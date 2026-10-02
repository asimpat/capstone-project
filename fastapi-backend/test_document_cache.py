import asyncio

from app.database.session import SessionLocal
from app.services.document_cache import get_cached_document


DOCUMENT_ID = "elxvmkuulunja1y4razg4f64"
USER_ID = "vn4b3xk3kwpvsd9oax49jkb3"


async def main():
    db = SessionLocal()

    try:
        print("\n--- FIRST CALL ---")

        document = await get_cached_document(
            DOCUMENT_ID,
            USER_ID,
            db,
        )

        print("Document:", document)

        print("\n--- SECOND CALL ---")

        document = await get_cached_document(
            DOCUMENT_ID,
            USER_ID,
            db,
        )

        print("Document:", document)

    finally:
        db.close()


asyncio.run(main())
