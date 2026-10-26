import time

from sqlalchemy import select

from app.database.session import SessionLocal
from app.models.chunk import Chunk
from app.models.document import Document
from app.services.embedding import generate_embedding_cached
from app.services.chunking import estimate_tokens
from app.utils.logger import logger


async def semantic_search(
    query: str,
    user_id: str,
    document_id: str | None = None,
    top_k: int = 10,
    min_score: float = 0.3,
    correlation_id: str | None = None,
):
    start_time = time.perf_counter()

    query_embedding = await generate_embedding_cached(query)

    db = SessionLocal()

    try:
        distance = Chunk.embedding.cosine_distance(
            query_embedding
        )

        score = 1 - distance

        statement = (
            select(
                Chunk.id.label("chunk_id"),
                Chunk.document_id,
                Document.title.label("document_title"),
                Chunk.content,
                Chunk.chunk_index,
                score.label("score"),
            )
            .join(
                Document,
                Document.id == Chunk.document_id,
            )
            .where(
                Document.user_id == user_id,
                Document.deleted_at.is_(None),
                Document.status == "ready",
                Chunk.embedding.is_not(None),
            )
            .order_by(distance)
            .limit(top_k)
        )

        if document_id:
            statement = statement.where(
                Document.id == document_id
            )

        rows = db.execute(statement).all()

        results = []

        for row in rows:
            result_score = float(row.score)

            results.append({
                "chunkId": row.chunk_id,
                "documentId": row.document_id,
                "documentTitle": row.document_title,
                "content": row.content,
                "chunkIndex": row.chunk_index,
                "score": result_score,
                "tokenCount": estimate_tokens(row.content),
            })

        filtered = [
            result
            for result in results
            if result["score"] >= min_score
        ]

        duration = int(
            (time.perf_counter() - start_time) * 1000
        )

        logger.info(
            "Semantic search completed | "
            "query=%s total_results=%s "
            "filtered_results=%s top_score=%s "
            "duration_ms=%s correlation_id=%s",
            query[:100],
            len(results),
            len(filtered),
            (
                f"{filtered[0]['score']:.4f}"
                if filtered
                else None
            ),
            duration,
            correlation_id,
        )

        return filtered

    finally:
        db.close()
