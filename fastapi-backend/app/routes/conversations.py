from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.schemas import (
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
)
from app.security.authorization import require_permission
from app.security.dependencies import get_current_user
from datetime import datetime, timezone

from sqlalchemy import func, select

from app.models.document import Document
from app.models.usage_log import UsageLog
from app.exceptions import APIException
from app.middleware.rate_limiter import chat_rate_limit

from app.middleware.conversation_cache import get_cached_conversations


router = APIRouter(
    prefix="/api/v1/conversations",
    tags=["Conversations"],
)


# ============================================================
# CREATE CONVERSATION
# ============================================================

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(chat_rate_limit), Depends(
        require_permission("conversations:create"))],
)
def create_conversation(
    data: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = Conversation(
        user_id=current_user.id,
        title=data.title,
        document_id=data.document_id,
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return {
        "success": True,
        "data": ConversationResponse.model_validate(conversation),
    }


# ============================================================
# LIST CONVERSATIONS
# ============================================================

# @router.get(
#     "",
#     dependencies=[Depends(require_permission("conversations:read"))],
# )
# async def list_conversations(
#     page: int = Query(1, ge=1),
#     limit: int = Query(20, ge=1, le=100),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     message_count_subquery = (
#         db.query(
#             Message.conversation_id,
#             func.count(Message.id).label("message_count"),
#         )
#         .group_by(Message.conversation_id)
#         .subquery()
#     )

#     latest_message_subquery = (
#         db.query(
#             Message.conversation_id,
#             func.max(Message.created_at).label("latest_created_at"),
#         )
#         .group_by(Message.conversation_id)
#         .subquery()
#     )

#     query = (
#         db.query(
#             Conversation,
#             func.coalesce(
#                 message_count_subquery.c.message_count,
#                 0,
#             ).label("message_count"),
#             Message,
#         )
#         .outerjoin(
#             message_count_subquery,
#             message_count_subquery.c.conversation_id
#             == Conversation.id,
#         )
#         .outerjoin(
#             latest_message_subquery,
#             latest_message_subquery.c.conversation_id
#             == Conversation.id,
#         )
#         .outerjoin(
#             Message,
#             (
#                 Message.conversation_id == Conversation.id
#             )
#             & (
#                 Message.created_at
#                 == latest_message_subquery.c.latest_created_at
#             ),
#         )
#         .filter(
#             Conversation.user_id == current_user.id
#         )
#         .order_by(
#             Conversation.updated_at.desc()
#         )
#     )

#     total = (
#         db.query(func.count(Conversation.id))
#         .filter(
#             Conversation.user_id == current_user.id
#         )
#         .scalar()
#     )

#     offset = (page - 1) * limit

#     rows = (
#         query
#         .offset(offset)
#         .limit(limit)
#         .all()
#     )

#     data = []

#     for conversation, message_count, latest_message in rows:
#         data.append({
#             "id": conversation.id,
#             "title": conversation.title,
#             "message_count": message_count,
#             "last_message": (
#                 {
#                     "id": latest_message.id,
#                     "content": latest_message.content,
#                     "role": latest_message.role,
#                     "created_at": latest_message.created_at,
#                 }
#                 if latest_message
#                 else None
#             ),
#             "updated_at": conversation.updated_at,
#         })

#     return {
#         "success": True,
#         "data": data,
#         "meta": {
#             "page": page,
#             "limit": limit,
#             "total": total,
#         },
#     }

@router.get(
    "",
    dependencies=[Depends(require_permission("conversations:read"))],
)
async def list_conversations(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await get_cached_conversations(
        user_id=current_user.id,
        page=page,
        limit=limit,
        db=db,
    )

    return {
        "success": True,
        "data": result["data"],
        "meta": result["meta"],
    }


@router.post(
    "/{conversation_id}/messages",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("conversations:create"))],
)
@router.post(
    "/{conversation_id}/messages",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("conversations:create"))],
)
def send_message(
    conversation_id: str,
    data: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        # 1. Verify conversation belongs to current user
        conversation = db.scalar(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == current_user.id,
            )
        )

        if not conversation:
            raise APIException(
                status_code=404,
                code="CONVERSATION_NOT_FOUND",
                message="Conversation not found",
            )

        # 2. Verify document if provided
        if data.document_id:
            document = db.scalar(
                select(Document).where(
                    Document.id == data.document_id,
                    Document.user_id == current_user.id,
                    Document.deleted_at.is_(None),
                )
            )

            if not document:
                raise APIException(
                    status_code=404,
                    code="DOCUMENT_NOT_FOUND",
                    message="Document not found",
                )

        # 3. Create user message
        user_message = Message(
            conversation_id=conversation.id,
            user_id=current_user.id,
            document_id=data.document_id,
            content=data.content,
            role="user",
        )

        db.add(user_message)

        # 4. Update conversation
        conversation.updated_at = datetime.now(timezone.utc)

        # 5. Create assistant placeholder
        assistant_message = Message(
            conversation_id=conversation.id,
            user_id=current_user.id,
            document_id=data.document_id,
            content="Assistant response pending.",
            role="assistant",
        )

        db.add(assistant_message)

        # 6. Create usage log
        usage_log = UsageLog(
            user_id=current_user.id,
            conversation_id=conversation.id,
            document_id=data.document_id,
            event="message:sent",
            tokens=0,
        )

        db.add(usage_log)

        # Generate IDs and validate the pending changes
        db.flush()

        # Commit EVERYTHING together
        db.commit()

        # Refresh objects after commit
        db.refresh(user_message)
        db.refresh(assistant_message)

    except APIException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise

    return {
        "success": True,
        "data": {
            "user_message": MessageResponse.model_validate(user_message),
            "assistant_message": MessageResponse.model_validate(assistant_message),
        },
    }
