import asyncio

from app.cache import (
    cache_get,
    cache_set,
    cache_delete,
    CACHE_TTL,
)


async def main():
    key = "permissions:user123"

    print("1. Saving permissions...")

    await cache_set(
        key,
        ["documents:read"],
        CACHE_TTL["PERMISSIONS"],
    )

    print("2. Getting permissions...")

    result = await cache_get(key)

    print("Cached:", result)

    print("3. Invalidating permissions...")

    await cache_delete(key)

    print("4. Getting permissions again...")

    result = await cache_get(key)

    print("After invalidation:", result)


asyncio.run(main())
