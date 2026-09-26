from datetime import datetime, timezone
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.document import Document
from app.models.user import User
from app.schemas import DocumentCreate, DocumentResponse, DocumentUpdate
from app.security.authorization import require_permission
from app.security.dependencies import get_current_user
from app.models.chunk import Chunk
from app.events.document_events import log_document_created
from app.events.document_events import log_document_deleted


router = APIRouter(
    prefix="/api/v1/documents",
    tags=["Documents"],
)


class DocumentStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    ready = "ready"
    failed = "failed"


class SortBy(str, Enum):
    created_at = "createdAt"
    title = "title"
    chunk_count = "chunkCount"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


# ============================================================
# CREATE DOCUMENT
# ============================================================

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("documents:create"))],
)
def create_document(
    data: DocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = Document(
        user_id=current_user.id,
        title=data.title,
        content=data.content,
        status="pending",
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    log_document_created(
        db,
        current_user.id,
        document.id,
    )

    return {
        "success": True,
        "data": DocumentResponse.model_validate(document),
    }


# ============================================================
# LIST DOCUMENTS
# ============================================================

@router.get(
    "",
    dependencies=[Depends(require_permission("documents:read"))],
)
def list_documents(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status_filter: DocumentStatus | None = Query(
        default=None,
        alias="status",
    ),
    search: str | None = Query(
        default=None,
        max_length=200,
    ),
    sort_by: SortBy = Query(
        default=SortBy.created_at,
        alias="sortBy",
    ),
    sort_order: SortOrder = Query(
        default=SortOrder.desc,
        alias="sortOrder",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # --------------------------------------------------------
    # Chunk count
    # --------------------------------------------------------

    chunk_count = func.count(Chunk.id).label("chunk_count")

    # --------------------------------------------------------
    # Base query
    # --------------------------------------------------------

    query = (
        db.query(
            Document,
            chunk_count,
        )
        .outerjoin(
            Chunk,
            Chunk.document_id == Document.id,
        )
        .filter(
            Document.user_id == current_user.id,
            Document.deleted_at.is_(None),
        )
        .group_by(Document.id)
    )

    # --------------------------------------------------------
    # Status filter
    # --------------------------------------------------------

    if status_filter:
        query = query.filter(
            Document.status == status_filter.value
        )

    # --------------------------------------------------------
    # Search
    # --------------------------------------------------------

    if search:
        search_pattern = f"%{search}%"

        query = query.filter(
            Document.title.ilike(search_pattern)
        )

    # --------------------------------------------------------
    # Sorting
    # --------------------------------------------------------

    if sort_by == SortBy.title:
        sort_column = Document.title

    elif sort_by == SortBy.chunk_count:
        sort_column = chunk_count

    else:
        sort_column = Document.created_at

    if sort_order == SortOrder.asc:
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # --------------------------------------------------------
    # Count total records
    # --------------------------------------------------------

    count_query = (
        db.query(func.count(Document.id))
        .filter(
            Document.user_id == current_user.id,
            Document.deleted_at.is_(None),
        )
    )

    if status_filter:
        count_query = count_query.filter(
            Document.status == status_filter.value
        )

    if search:
        search_pattern = f"%{search}%"

        count_query = count_query.filter(
            Document.title.ilike(search_pattern)
        )

    total = count_query.scalar()

    # --------------------------------------------------------
    # Pagination
    # --------------------------------------------------------

    offset = (page - 1) * limit

    rows = (
        query
        .offset(offset)
        .limit(limit)
        .all()
    )

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    data = []

    for document, count in rows:
        document_data = DocumentResponse.model_validate(document)

        document_data = document_data.model_dump()

        document_data["chunk_count"] = count

        data.append(document_data)

    return {
        "success": True,
        "data": data,
        "meta": {
            "page": page,
            "limit": limit,
            "total": total,
        },
    }


def list_documents(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status_filter: DocumentStatus | None = Query(
        default=None,
        alias="status",
    ),
    search: str | None = Query(
        default=None,
        max_length=200,
    ),
    sort_by: SortBy = Query(
        default=SortBy.created_at,
        alias="sortBy",
    ),
    sort_order: SortOrder = Query(
        default=SortOrder.desc,
        alias="sortOrder",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # --------------------------------------------------------
    # Base query
    # --------------------------------------------------------

    query = select(Document).where(
        Document.user_id == current_user.id,
        Document.deleted_at.is_(None),
    )

    # --------------------------------------------------------
    # Status filter
    # --------------------------------------------------------

    if status_filter:
        query = query.where(
            Document.status == status_filter.value
        )

    # --------------------------------------------------------
    # Search
    # --------------------------------------------------------

    if search:
        search_pattern = f"%{search}%"

        query = query.where(
            Document.title.ilike(search_pattern)
        )

    # --------------------------------------------------------
    # Sorting
    # --------------------------------------------------------

    if sort_by == SortBy.title:
        sort_column = Document.title
    elif sort_by == "chunkCount":
        query = query.order_by(
        chunk_count.asc()
        if sort_order == "asc"
        else chunk_count.desc()
    )
    else:
        sort_column = Document.created_at

    if sort_order == SortOrder.asc:
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # --------------------------------------------------------
    # Count total records
    # --------------------------------------------------------

    count_query = select(
        func.count()
    ).select_from(Document).where(
        Document.user_id == current_user.id,
        Document.deleted_at.is_(None),
    )

    if status_filter:
        count_query = count_query.where(
            Document.status == status_filter.value
        )

    if search:
        search_pattern = f"%{search}%"

        count_query = count_query.where(
            Document.title.ilike(search_pattern)
        )

    total = db.scalar(count_query)

    # --------------------------------------------------------
    # Pagination
    # --------------------------------------------------------

    offset = (page - 1) * limit

    query = query.offset(offset).limit(limit)

    documents = db.scalars(query).all()

    chunk_count = func.count(Chunk.id).label("chunk_count")

    query = (
        db.query(
            Document,
            chunk_count
        )
        .outerjoin(
            Chunk,
            Chunk.document_id == Document.id
        )
        .filter(
            Document.user_id == current_user.id,
            Document.deleted_at.is_(None)
        )
        .group_by(Document.id)
    )

    return {
        "success": True,
        "data": [
            DocumentResponse.model_validate(document)
            for document in documents
        ],
        "meta": {
            "page": page,
            "limit": limit,
            "total": total,
        },
    }


# ============================================================
# GET SINGLE DOCUMENT
# ============================================================

@router.get(
    "/{document_id}",
    dependencies=[Depends(require_permission("documents:read"))],
)
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = db.scalar(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id,
            Document.deleted_at.is_(None),
        )
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "DOCUMENT_NOT_FOUND",
                "message": "Document not found",
            },
        )

    return {
        "success": True,
        "data": DocumentResponse.model_validate(document),
    }


# ============================================================
# UPDATE DOCUMENT
# ============================================================

@router.patch(
    "/{document_id}",
    dependencies=[Depends(require_permission("documents:update"))],
)
def update_document(
    document_id: str,
    data: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = db.scalar(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id,
            Document.deleted_at.is_(None),
        )
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "DOCUMENT_NOT_FOUND",
                "message": "Document not found",
            },
        )

    document.title = data.title

    db.commit()
    db.refresh(document)

    return {
        "success": True,
        "data": DocumentResponse.model_validate(document),
    }


# ============================================================
# SOFT DELETE DOCUMENT
# ============================================================

@router.delete(
    "/{document_id}",
    dependencies=[Depends(require_permission("documents:delete"))],
)
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = db.scalar(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id,
            Document.deleted_at.is_(None),
        )
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "DOCUMENT_NOT_FOUND",
                "message": "Document not found",
            },
        )

    # IMPORTANT:
    # We are NOT doing db.delete(document)
    # We are marking the document as deleted.

    document.deleted_at = datetime.now(timezone.utc)
    document.deleted_by = current_user.id

    db.commit()
    db.refresh(document)

    log_document_deleted(
        db,
        current_user.id,
        document.id,
    )

    return {
        "success": True,
        "data": {
            "message": "Document deleted successfully",
            "document_id": document.id,
        },
    }
