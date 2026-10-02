import asyncio

from app.database.session import SessionLocal
from app.services.conversation_cache import (
    get_cached_conversations,
)


USER_ID = "mep9z3ta4rms8xbfas995544"


async def main():
    db = SessionLocal()

    try:
        print("\n--- FIRST REQUEST ---")

        result = await get_cached_conversations(
            user_id=USER_ID,
            page=1,
            limit=20,
            db=db,
        )

        print(result)

        print("\n--- SECOND REQUEST ---")

        result = await get_cached_conversations(
            user_id=USER_ID,
            page=1,
            limit=20,
            db=db,
        )

        print(result)

    finally:
        db.close()


asyncio.run(main())
