import time
import hashlib


from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models.chunk import Chunk

from app.lib.http.openai_client import openai_post_with_retry
from app.utils.logger import logger
from app.cache import CACHE_TTL, cache_get, cache_set


EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536
EMBEDDING_BATCH_SIZE = 100

def content_hash(text: str) -> str:
    """
    Generate a deterministic SHA-256 hash for text.
    """

    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()

def generate_embedding(text: str) -> list[float]:
    """
    Generate a single embedding for a piece of text.
    """

    if not text or not text.strip():
        raise ValueError("Text cannot be empty")

    start_time = time.perf_counter()

    response = openai_post_with_retry(
        "/embeddings",
        {
            "input": text,
            "model": EMBEDDING_MODEL,
        },
    )

    data = response.json()

    embedding = data["data"][0]["embedding"]

    duration_ms = int(
        (time.perf_counter() - start_time) * 1000
    )

    dimensions = len(embedding)

    if dimensions != EMBEDDING_DIMENSIONS:
        raise ValueError(
            f"Expected {EMBEDDING_DIMENSIONS} dimensions, "
            f"got {dimensions}"
        )

    logger.info(
        "Embedding generated | model=%s input_length=%s "
        "dimensions=%s duration_ms=%s tokens_used=%s",
        EMBEDDING_MODEL,
        len(text),
        dimensions,
        duration_ms,
        data.get("usage", {}).get("total_tokens"),
    )

    return embedding


def generate_embeddings(
    texts: list[str],
) -> list[list[float]]:
    """
    Generate embeddings for multiple pieces of text.

    Texts are processed in batches and the returned embeddings
    preserve the same order as the input texts.
    """

    if not texts:
        return []

    results: list[list[float] | None] = [None] * len(texts)

    for batch_start in range(
        0,
        len(texts),
        EMBEDDING_BATCH_SIZE,
    ):
        batch = texts[
            batch_start:
            batch_start + EMBEDDING_BATCH_SIZE
        ]

        if any(not text or not text.strip() for text in batch):
            raise ValueError(
                "Text cannot be empty"
            )

        start_time = time.perf_counter()

        response = openai_post_with_retry(
            "/embeddings",
            {
                "input": batch,
                "model": EMBEDDING_MODEL,
            },
        )

        data = response.json()

        embedding_data = sorted(
            data["data"],
            key=lambda item: item["index"],
        )

        for offset, item in enumerate(embedding_data):
            embedding = item["embedding"]

            if len(embedding) != EMBEDDING_DIMENSIONS:
                raise ValueError(
                    f"Expected {EMBEDDING_DIMENSIONS} dimensions, "
                    f"got {len(embedding)}"
                )

            original_index = batch_start + offset

            results[original_index] = embedding

        duration_ms = int(
            (time.perf_counter() - start_time) * 1000
        )

        logger.info(
            "Embedding batch processed | "
            "batch_index=%s batch_size=%s total_texts=%s "
            "duration_ms=%s tokens_used=%s",
            batch_start // EMBEDDING_BATCH_SIZE,
            len(batch),
            len(texts),
            duration_ms,
            data.get("usage", {}).get("total_tokens"),
        )

    return [
        embedding
        for embedding in results
        if embedding is not None
    ]

def store_chunk_embedding(
        db: Session,
        chunk_id: str,
        embedding: list[float],
    ) -> None:
    """
    Store an embedding for a single chunk.
    """

    if len(embedding) != EMBEDDING_DIMENSIONS:
        raise ValueError(
            f"Expected {EMBEDDING_DIMENSIONS} dimensions, "
            f"got {len(embedding)}"
        )

    result = db.execute(
        update(Chunk)
        .where(Chunk.id == chunk_id)
        .values(embedding=embedding)
    )

    if result.rowcount == 0:
        raise ValueError(
            f"Chunk not found: {chunk_id}"
        )

    db.commit()

    logger.info(
        "Chunk embedding stored | chunk_id=%s dimensions=%s",
        chunk_id,
        len(embedding),
    )


def store_chunk_embeddings_batch(
    db: Session,
    chunks: list[dict],
) -> None:
    """
    Store embeddings for multiple chunks in one transaction.

    Each item in chunks must contain:
        {
            "id": str,
            "embedding": list[float]
        }
    """

    if not chunks:
        return

    for chunk in chunks:
        embedding = chunk["embedding"]

        if len(embedding) != EMBEDDING_DIMENSIONS:
            raise ValueError(
                f"Expected {EMBEDDING_DIMENSIONS} dimensions, "
                f"got {len(embedding)} "
                f"for chunk {chunk['id']}"
            )

    try:
        for chunk in chunks:
            result = db.execute(
                update(Chunk)
                .where(Chunk.id == chunk["id"])
                .values(embedding=chunk["embedding"])
            )

            if result.rowcount == 0:
                raise ValueError(
                    f"Chunk not found: {chunk['id']}"
                )

        db.commit()

        logger.info(
            "Chunk embeddings stored in batch | count=%s",
            len(chunks),
        )

    except Exception:
        db.rollback()
        raise


async def generate_embedding_cached(
    text: str,
) -> list[float]:
    """
    Generate an embedding using Redis caching.

    If an embedding already exists in the cache,
    return it without calling OpenAI.
    """

    if not text or not text.strip():
        raise ValueError("Text cannot be empty")

    hash_value = content_hash(text)

    cache_key = f"embed:{hash_value}"

    cached = await cache_get(cache_key)

    if cached is not None:
        logger.debug(
            "Embedding cache hit | hash=%s",
            hash_value[:12],
        )

        return cached

    logger.debug(
        "Embedding cache miss | hash=%s",
        hash_value[:12],
    )

    embedding = generate_embedding(text)

    await cache_set(
        cache_key,
        embedding,
        CACHE_TTL["EMBEDDING"],
    )

    logger.debug(
        "Embedding cached | hash=%s ttl=%s",
        hash_value[:12],
        CACHE_TTL["EMBEDDING"],
    )

    return embedding


async def generate_embeddings_cached(
    texts: list[str],
) -> list[list[float]]:
    """
    Generate embeddings using Redis caching.

    Cached texts are returned immediately.
    Only uncached texts are sent to OpenAI.
    The returned embeddings preserve the original
    order of the input texts.
    """

    if not texts:
        return []

    results: list[list[float] | None] = [
        None
    ] * len(texts)

    uncached_texts: list[str] = []
    uncached_indexes: list[int] = []

    # --------------------------------------------------
    # 1. Check Redis for every text
    # --------------------------------------------------

    for index, text in enumerate(texts):

        if not text or not text.strip():
            raise ValueError(
                f"Text at index {index} cannot be empty"
            )

        hash_value = content_hash(text)

        cache_key = f"embed:{hash_value}"

        cached = await cache_get(cache_key)

        if cached is not None:
            results[index] = cached

            logger.debug(
                "Embedding cache hit | hash=%s index=%s",
                hash_value[:12],
                index,
            )

        else:
            uncached_texts.append(text)
            uncached_indexes.append(index)

            logger.debug(
                "Embedding cache miss | hash=%s index=%s",
                hash_value[:12],
                index,
            )

    # --------------------------------------------------
    # 2. Generate only missing embeddings
    # --------------------------------------------------

    if uncached_texts:

        generated_embeddings = generate_embeddings(
            uncached_texts
        )

        # --------------------------------------------------
        # 3. Cache the newly generated embeddings
        # --------------------------------------------------

        for index, text, embedding in zip(
            uncached_indexes,
            uncached_texts,
            generated_embeddings,
        ):
            hash_value = content_hash(text)

            cache_key = f"embed:{hash_value}"

            await cache_set(
                cache_key,
                embedding,
                CACHE_TTL["EMBEDDING"],
            )

            results[index] = embedding

            logger.debug(
                "Embedding cached | hash=%s index=%s ttl=%s",
                hash_value[:12],
                index,
                CACHE_TTL["EMBEDDING"],
            )

    # --------------------------------------------------
    # 4. Return everything in original order
    # --------------------------------------------------

    return [
        embedding
        for embedding in results
        if embedding is not None
    ]
