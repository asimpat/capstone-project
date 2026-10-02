import logging

from app.cache import cache_redis

logger = logging.getLogger(__name__)


async def track_login_failure(device_info: str):
    key = f"docuchat:login-failures:{device_info}"

    failures = await cache_redis.incr(key)

    if failures == 1:
        await cache_redis.expire(
            key,
            900,
        )

    if failures >= 5:
        logger.warning(
            "Suspicious login activity detected: "
            "device=%s failures=%s",
            device_info,
            failures,
        )

    return failures
