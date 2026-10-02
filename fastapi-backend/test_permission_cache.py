import asyncio

from app.database.session import SessionLocal
from app.services.permission_cache import get_user_permissions


USER_ID = "mvdmt6ja7kgrg887y7v9igit"


async def main():
    db = SessionLocal()

    try:
        print("\n--- FIRST CALL ---")

        permissions = await get_user_permissions(
            USER_ID,
            db,
        )

        print("Permissions:", permissions)

        print("\n--- SECOND CALL ---")

        permissions = await get_user_permissions(
            USER_ID,
            db,
        )

        print("Permissions:", permissions)

    finally:
        db.close()


asyncio.run(main())
