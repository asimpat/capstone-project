from enum import Enum

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.exceptions import APIException
from app.models.document import Document

from app.models.user import User
from app.schemas import (
    DocumentCreate,
    DocumentResponse,
    DocumentUpdate
)
from app.security.authorization import require_permission


router = APIRouter(
    prefix="/api/v1/documents",
    tags=["Documents"]
)


class DocumentStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    ready = "ready"
    failed = "failed"


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=DocumentResponse
)
def create_document(
    document_data: DocumentCreate,
    current_user: User = Depends(
        require_permission("documents:create")
    ),
    db: Session = Depends(get_db)
):
    document = Document(
        user_id=current_user.id,
        title=document_data.title,
        content=document_data.content,
        status=DocumentStatus.pending.value
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return document


@router.get("")
def list_documents(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    document_status: DocumentStatus | None = Query(
        None,
        alias="status"
    ),
    current_user: User = Depends(
        require_permission("documents:read")
    ),
    db: Session = Depends(get_db)
):
    query = select(Document).where(
        Document.user_id == current_user.id
    )

    if document_status:
        query = query.where(
            Document.status == document_status.value
        )

    count_query = select(
        func.count()
    ).select_from(
        query.subquery()
    )

    total = db.execute(count_query).scalar() or 0

    offset = (page - 1) * limit

    query = (
        query
        .order_by(Document.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    documents = db.execute(query).scalars().all()

    return {
        "success": True,
        "data": documents,
        "meta": {
            "page": page,
            "limit": limit,
            "total": total
        }
    }


@router.get(
    "/{document_id}",
    response_model=DocumentResponse
)
def get_document(
    document_id: str,
    current_user: User = Depends(
        require_permission("documents:read")
    ),
    db: Session = Depends(get_db)
):
    document = db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id
        )
    ).scalar_one_or_none()

    if not document:

        raise APIException(
            status_code=404,
            code="DOCUMENT_NOT_FOUND",
            message="Document not found"
        )

    return document


@router.patch(
    "/{document_id}",
    response_model=DocumentResponse
)
def update_document(
    document_id: str,
    document_data: DocumentUpdate,
    current_user: User = Depends(
        require_permission("documents:update")
    ),
    db: Session = Depends(get_db)
):
    document = db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id
        )
    ).scalar_one_or_none()

    if not document:

        raise APIException(
            status_code=404,
            code="DOCUMENT_NOT_FOUND",
            message="Document not found"
        )

    document.title = document_data.title
    # document.content = document_data.content

    db.commit()
    db.refresh(document)

    return document


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_200_OK
)
def delete_document(
    document_id: str,
    current_user: User = Depends(
        require_permission("documents:delete")
    ),
    db: Session = Depends(get_db)
):
    document = db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id
        )
    ).scalar_one_or_none()

    if not document:

        raise APIException(
            status_code=404,
            code="DOCUMENT_NOT_FOUND",
            message="Document not found"
        )

    db.delete(document)
    db.commit()

    return {
        "success": True,
        "data": {
            "message": "Document deleted successfully"
        }
    }
