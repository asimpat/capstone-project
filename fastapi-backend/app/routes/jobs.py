from fastapi import APIRouter
from app.jobs.tasks import process_document

from app.queue import queue
from app.jobs.tasks import process_document

router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])


@router.post("/documents/{document_id}")
def create_document_job(document_id: str):
    job = queue.enqueue(
        process_document,
        document_id,
    )

    return {
        "message": "Document processing job added to queue",
        "job_id": job.id,
        "document_id": document_id,
    }
