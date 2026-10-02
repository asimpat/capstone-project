from sqlalchemy import select
from sqlalchemy.orm import Session

from app.cache import (
    CACHE_TTL,
    cache_get_or_set,
    hash_key,
)
from app.models.document import Document


async def get_cached_document(
    document_id: str,
    user_id: str,
    db: Session,
):
    key = f"doc:{hash_key(document_id, user_id)}"

    async def fetch_document():
        document = db.scalar(
            select(Document).where(
                Document.id == document_id,
                Document.user_id == user_id,
                Document.deleted_at.is_(None),
            )
        )

        if not document:
            return None

        return {
            "id": document.id,
            "user_id": document.user_id,
            "title": document.title,
            "content": document.content,
            "status": document.status,
            "created_at": document.created_at.isoformat(),
            "updated_at": document.updated_at.isoformat(),
        }

    return await cache_get_or_set(
        key=key,
        ttl_seconds=CACHE_TTL["DOCUMENT"],
        fetch_fn=fetch_document,
    )
