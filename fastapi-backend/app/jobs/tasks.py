from rq import get_current_job
from sqlalchemy import delete

from app.database.session import SessionLocal
from app.models.document import Document
from app.models.chunk import Chunk
from app.utils.logger import logger


def update_progress(job, progress: int, step: str):
    """Store job progress in RQ job metadata."""
    if job:
        job.meta["progress"] = progress
        job.meta["step"] = step
        job.save_meta()


def chunk_text(content: str, chunk_size: int = 500):
    """Split document content into smaller chunks."""
    words = content.split()

    chunks = []

    for i in range(0, len(words), chunk_size):
        chunks.append(" ".join(words[i:i + chunk_size]))

    return chunks


def process_document(document_id: str):
    job = get_current_job()
    db = SessionLocal()

    try:
        # 1. Fetch document
        update_progress(job, 10, "Fetching document")

        document = db.get(Document, document_id)

        if not document:
            raise ValueError(f"Document {document_id} not found")
            

        # 2. Mark document as processing
        document.status = "processing"
        db.commit()

        update_progress(job, 25, "Document marked as processing")

        # 3. Chunk the document
        update_progress(job, 40, "Chunking document")

        chunks = chunk_text(document.content)

        # 4. Delete old chunks
        update_progress(job, 60, "Replacing document chunks")

        db.execute(
            delete(Chunk).where(
                Chunk.document_id == document.id
            )
        )

        # 5. Create new chunks
        for index, content in enumerate(chunks):
            chunk = Chunk(
                document_id=document.id,
                content=content,
                chunk_index=index,
            )

            db.add(chunk)

        # 6. Mark document as ready
        document.status = "ready"

        # Commit chunks + status together
        db.commit()

        # 7. Completed
        update_progress(job, 100, "Document processing completed")

        return {
            "document_id": document.id,
            "status": document.status,
            "chunks_created": len(chunks),
        }


    except Exception:
        db.rollback()

        if job:
            job.refresh()

            retries_left = job.retries_left

            if retries_left == 0:
                document = db.get(Document, document_id)

                if document:
                    document.status = "failed"
                    db.commit()

        raise

    finally:
        db.close()


def record_dead_letter(job_id: str, error: str):
    logger.error(
        "Dead-letter job permanently failed | job_id=%s error=%s",
        job_id,
        error,
    )

    return {
        "job_id": job_id,
        "error": error,
        "status": "dead-letter",
    }