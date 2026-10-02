from sqlalchemy import func
from sqlalchemy.orm import Session

from app.cache import (
    CACHE_TTL,
    cache_get_or_set,
    hash_key,
)
from app.models.conversation import Conversation
from app.models.message import Message


async def get_cached_conversations(
    user_id: str,
    page: int,
    limit: int,
    db: Session,
):
    cache_key = (
        f"conversations:"
        f"{hash_key(user_id)}:"
        f"page:{page}:"
        f"limit:{limit}"
    )

    async def fetch_conversations():
        message_count_subquery = (
            db.query(
                Message.conversation_id,
                func.count(Message.id).label("message_count"),
            )
            .group_by(Message.conversation_id)
            .subquery()
        )

        latest_message_subquery = (
            db.query(
                Message.conversation_id,
                func.max(Message.created_at).label(
                    "latest_created_at"
                ),
            )
            .group_by(Message.conversation_id)
            .subquery()
        )

        query = (
            db.query(
                Conversation,
                func.coalesce(
                    message_count_subquery.c.message_count,
                    0,
                ).label("message_count"),
                Message,
            )
            .outerjoin(
                message_count_subquery,
                message_count_subquery.c.conversation_id
                == Conversation.id,
            )
            .outerjoin(
                latest_message_subquery,
                latest_message_subquery.c.conversation_id
                == Conversation.id,
            )
            .outerjoin(
                Message,
                (
                    Message.conversation_id
                    == Conversation.id
                )
                & (
                    Message.created_at
                    == latest_message_subquery.c.latest_created_at
                ),
            )
            .filter(
                Conversation.user_id == user_id
            )
            .order_by(
                Conversation.updated_at.desc()
            )
        )

        total = (
            db.query(func.count(Conversation.id))
            .filter(
                Conversation.user_id == user_id
            )
            .scalar()
        )

        offset = (page - 1) * limit

        rows = (
            query
            .offset(offset)
            .limit(limit)
            .all()
        )

        data = []

        for conversation, message_count, latest_message in rows:
            data.append(
                {
                    "id": conversation.id,
                    "title": conversation.title,
                    "message_count": message_count,
                    "last_message": (
                        {
                            "id": latest_message.id,
                            "content": latest_message.content,
                            "role": latest_message.role,
                            "created_at": latest_message.created_at.isoformat(),
                        }
                        if latest_message
                        else None
                    ),
                    "updated_at": conversation.updated_at.isoformat(),
                }
            )

        return {
            "data": data,
            "meta": {
                "page": page,
                "limit": limit,
                "total": total,
            },
        }

    return await cache_get_or_set(
        key=cache_key,
        ttl_seconds=CACHE_TTL["CONVERSATIONS"],
        fetch_fn=fetch_conversations,
    )
