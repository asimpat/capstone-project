import hashlib
import json
import os

import asyncio
import redis.asyncio as redis


REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

CACHE_PREFIX = "docuchat:"

cache_redis = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True,
)


CACHE_TTL = {
    "PERMISSIONS": 300,
    "DOCUMENT": 600,
    "CONVERSATION_LIST": 120,
    "CONVERSATIONS": 300,
    "EMBEDDING": 604800,
    "RAG_RESULT": 3600,
}


async def cache_get(key: str):
    full_key = f"{CACHE_PREFIX}{key}"

    raw = await cache_redis.get(full_key)

    if raw is None:
        return None

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


async def cache_set(
    key: str,
    value,
    ttl_seconds: int,
) -> None:
    full_key = f"{CACHE_PREFIX}{key}"

    await cache_redis.set(
        full_key,
        json.dumps(value),
        ex=ttl_seconds,
    )


async def cache_delete(key: str) -> None:
    full_key = f"{CACHE_PREFIX}{key}"

    await cache_redis.delete(full_key)


async def cache_delete_pattern(pattern: str) -> None:
    full_pattern = f"{CACHE_PREFIX}{pattern}"

    async for key in cache_redis.scan_iter(match=full_pattern):
        await cache_redis.delete(key)


def hash_key(*parts: str) -> str:
    data = ":".join(parts)

    return hashlib.sha256(
        data.encode("utf-8")
    ).hexdigest()[:16]


async def cache_get_or_set(
    key: str,
    ttl_seconds: int,
    fetch_fn,
):
    # 1. Check cache first
    cached = await cache_get(key)

    if cached is not None:
        return cached

    # 2. Create lock key
    lock_key = f"{CACHE_PREFIX}lock:{key}"

    # 3. Try to acquire lock
    acquired = await cache_redis.set(
        lock_key,
        "1",
        ex=5,
        nx=True,
    )

    if acquired:
        try:
            # 4. We own the lock
            value = await fetch_fn()

            # 5. Store result in cache
            await cache_set(
                key,
                value,
                ttl_seconds,
            )

            return value

        finally:
            # 6. Release lock
            await cache_redis.delete(lock_key)

    # 7. Another request is fetching the data.
    # Keep checking the cache.
    for _ in range(20):
        await asyncio.sleep(0.1)

        cached = await cache_get(key)

        if cached is not None:
            return cached

    # 8. If the cache still isn't available,
    # fetch as a final fallback.
    return await fetch_fn()


async def get_user_permissions(
    user_id: str,
    db,
):
    cache_key = f"permissions:{user_id}"

    async def fetch_permissions():
        return await load_permissions_from_database(
            user_id,
            db,
        )

    permissions = await cache_get_or_set(
        cache_key,
        CACHE_TTL["PERMISSIONS"],
        fetch_permissions,
    )

    return set(permissions)


async def get_document(
    document_id: str,
    db,
):
    cache_key = f"doc:{document_id}"

    async def fetch_document():
        # SQLAlchemy query
        ...

    return await cache_get_or_set(
        cache_key,
        CACHE_TTL["DOCUMENT"],
        fetch_document,
    )


def generate_etag(data) -> str:
    content = json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
    )

    digest = hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()

    return f'"{digest}"'
