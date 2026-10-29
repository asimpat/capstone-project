import asyncio
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

from app.services.search import semantic_search
from app.services.rag import assemble_context, generate_rag_response
from app.services.embedding import EmbeddingServiceError

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
@router.post(
    "/{conversation_id}/messages",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("conversations:create"))],
)
async def send_message(
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

        # 3. Save user message

        user_message = Message(
            conversation_id=conversation.id,
            user_id=current_user.id,
            document_id=data.document_id,
            content=data.content,
            role="user",
        )

        db.add(user_message)

        conversation.updated_at = datetime.now(timezone.utc)

        db.flush()
        db.commit()
        db.refresh(user_message)

    except APIException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise

    # ============================================================
    # RAG PIPELINE
    # ============================================================

    try:
        # 4. Load recent conversation history

        history_rows = db.scalars(
            select(Message)
            .where(
                Message.conversation_id == conversation.id,
                Message.user_id == current_user.id,
            )
            .order_by(Message.created_at.desc())
            .limit(10)
        ).all()

        history_rows.reverse()

        conversation_history = [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in history_rows
        ]

        # 5. Semantic search

        search_results = await semantic_search(
            query=data.content,
            user_id=current_user.id,
            document_id=data.document_id,
            top_k=10,
            min_score=0.3,
        )

        # 6. Assemble context

        context = assemble_context(search_results)

        # 7. Generate RAG response

        rag_response = generate_rag_response(
            question=data.content,
            context=context,
            conversation_history=conversation_history,
            user_id=current_user.id,
            conversation_id=conversation.id,
        )

    except EmbeddingServiceError as exc:
        raise APIException(
            status_code=503,
            code="EMBEDDING_SERVICE_ERROR",
            message=str(exc),
            details=[{"service": "ollama"}],
        ) from exc

    except Exception:
        raise

    # ============================================================
    # SAVE ASSISTANT RESPONSE
    # ============================================================

    try:
        # 8. Save assistant message

        assistant_message = Message(
            conversation_id=conversation.id,
            user_id=current_user.id,
            document_id=data.document_id,
            content=rag_response["answer"],
            role="assistant",
            prompt_tokens=rag_response["tokensUsed"]["prompt"],
            completion_tokens=rag_response["tokensUsed"]["completion"],
            cost_usd=rag_response["costUsd"],
            message_metadata={
                "model": rag_response["model"],
                "citations": rag_response["citations"],
                "contextChunks": len(context["chunks"]),
            },
        )

        db.add(assistant_message)

        # 9. Save usage log

        usage_log = UsageLog(
            user_id=current_user.id,
            conversation_id=conversation.id,
            document_id=data.document_id,
            event="message:sent",
            tokens=rag_response["tokensUsed"]["total"],
        )

        db.add(usage_log)

        # 10. Update conversation

        conversation.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(assistant_message)

    except Exception:
        db.rollback()
        raise

    return {
        "success": True,
        "data": {
            "user_message": MessageResponse.model_validate(
                user_message
            ),
            "assistant_message": MessageResponse.model_validate(
                assistant_message
            ),
            "citations": rag_response["citations"],
        },
    }
