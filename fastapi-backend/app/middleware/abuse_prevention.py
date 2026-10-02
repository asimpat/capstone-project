import logging
from app.cache import cache_redis
import hashlib

from fastapi import Request


def get_request_fingerprint(request: Request) -> str:
    ip = request.client.host if request.client else ""

    user_agent = request.headers.get(
        "user-agent",
        "",
    )

    accept_language = request.headers.get(
        "accept-language",
        "",
    )

    accept_encoding = request.headers.get(
        "accept-encoding",
        "",
    )

    raw = "|".join(
        [
            ip,
            user_agent,
            accept_language,
            accept_encoding,
        ]
    )

    fingerprint = hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()

    return fingerprint[:16]


logger = logging.getLogger(__name__)


async def track_document_access(
    user_id: str,
    document_id: str,
):
    key = f"docuchat:access-pattern:{user_id}"

    await cache_redis.sadd(
        key,
        document_id,
    )

    await cache_redis.expire(
        key,
        300,
    )

    unique_documents = await cache_redis.scard(key)

    if unique_documents > 50:
        logger.warning(
            "Suspicious document access: "
            "user_id=%s unique_documents=%s",
            user_id,
            unique_documents,
        )

    return unique_documents
