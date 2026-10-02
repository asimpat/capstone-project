import math
import time


from app.models.user import User
from app.security.dependencies import get_current_user

from fastapi import HTTPException, Request, status, Depends, Response

from app.cache import cache_redis


TIER_LIMITS = {
    "free": {
        "api": (100, 900),
        "upload": (5, 3600),
        "chat": (10, 60),
    },
    "pro": {
        "api": (500, 900),
        "upload": (50, 3600),
        "chat": (30, 60),
    },
    "enterprise": {
        "api": (2000, 900),
        "upload": (500, 3600),
        "chat": (100, 60),
    },
}


AUTH_LIMIT = 10
AUTH_WINDOW = 900


async def sliding_window_limit(
    key: str,
    limit: int,
    window_seconds: int,
):

    now = time.time()

    current_window = int(now // window_seconds)
    previous_window = current_window - 1

    current_key = f"docuchat:rate:{key}:{current_window}"
    previous_key = f"docuchat:rate:{key}:{previous_window}"

    current_count = await cache_redis.incr(current_key)

    if current_count == 1:
        await cache_redis.expire(current_key, window_seconds * 2)

    previous_count_raw = await cache_redis.get(previous_key)
    previous_count = int(previous_count_raw or 0)

    elapsed = now % window_seconds
    previous_weight = 1 - (elapsed / window_seconds)

    estimated_count = (
        current_count
        + previous_count * previous_weight
    )

    allowed = estimated_count <= limit

    remaining = max(
        0,
        math.floor(limit - estimated_count),
    )

    reset = int(
        window_seconds - elapsed
    )

    return {
        "allowed": allowed,
        "limit": limit,
        "remaining": remaining,
        "reset": reset,
    }


async def enforce_rate_limit(
    key: str,
    limit: int,
    window_seconds: int,
):
    result = await sliding_window_limit(
        key=key,
        limit=limit,
        window_seconds=window_seconds,
    )

    if not result["allowed"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "success": False,
                "error": {
                    "code": "RATE_LIMITED",
                    "message": "Too many requests. Please try again later.",
                },
            },
            headers={
                "Retry-After": str(result["reset"]),
            },
        )

    return result


async def api_rate_limit(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
):
    tier = current_user.tier or "free"

    if tier not in TIER_LIMITS:
        tier = "free"

    limit, window = TIER_LIMITS[tier]["api"]

    result = await enforce_rate_limit(
        key=f"api:user:{current_user.id}",
        limit=limit,
        window_seconds=window,
    )

    response.headers["RateLimit-Limit"] = str(
        result["limit"]
    )

    response.headers["RateLimit-Remaining"] = str(
        result["remaining"]
    )

    response.headers["RateLimit-Reset"] = str(
        result["reset"]
    )

    return result


async def upload_rate_limit(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
):
    tier = current_user.tier or "free"

    if tier not in TIER_LIMITS:
        tier = "free"

    limit, window = TIER_LIMITS[tier]["upload"]

    return await enforce_rate_limit(
        key=f"upload:user:{current_user.id}",
        limit=limit,
        window_seconds=window,
    )


async def chat_rate_limit(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
):
    tier = current_user.tier or "free"

    if tier not in TIER_LIMITS:
        tier = "free"

    limit, window = TIER_LIMITS[tier]["chat"]

    return await enforce_rate_limit(
        key=f"chat:user:{current_user.id}",
        limit=limit,
        window_seconds=window,
    )


async def auth_rate_limit(request: Request, response: Response,):
    client_ip = request.client.host if request.client else "unknown"

    key = f"auth:ip:{client_ip}"

    return await enforce_rate_limit(
        key=key,
        limit=AUTH_LIMIT,
        window_seconds=AUTH_WINDOW,
    )
