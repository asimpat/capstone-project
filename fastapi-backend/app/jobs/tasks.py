import asyncio
import time

from rq import get_current_job
from sqlalchemy import delete, select

from app.database.session import SessionLocal
from app.models.document import Document
from app.models.chunk import Chunk
from app.services.chunking import chunk_document
from app.services.embedding import generate_embeddings_cached
from app.utils.logger import logger
from app.events.ingestion import handle_document_processed
from app.utils.metrics import (
    ingestion_duration,
    chunks_per_document,
)

def update_progress(job, progress: int, step: str):
    if job:
        job.meta["progress"] = progress
        job.meta["step"] = step
        job.save_meta()


def process_document(document_id: str):
    job = get_current_job()
    db = SessionLocal()
    start_time = time.perf_counter()

    try:
        update_progress(job, 5, "Fetching document")

        document = db.get(Document, document_id)

        if not document:
            raise ValueError(
                f"Document {document_id} not found"
            )

        document.status = "processing"
        db.commit()

        update_progress(
            job,
            15,
            "Document marked as processing",
        )

        text = document.content

        logger.info(
            "Text extracted | document_id=%s text_length=%s",
            document_id,
            len(text),
        )

        update_progress(
            job,
            30,
            "Chunking document",
        )

        chunks = chunk_document(
            text,
            max_tokens=500,
            overlap_tokens=50,
            min_chunk_tokens=50,
        )

        logger.info(
            "Document chunked | document_id=%s chunk_count=%s",
            document_id,
            len(chunks),
        )

        db.execute(
            delete(Chunk).where(
                Chunk.document_id == document_id
            )
        )

        for chunk in chunks:
            db.add(
                Chunk(
                    document_id=document_id,
                    content=chunk["text"],
                    chunk_index=chunk["index"],
                )
            )

        db.commit()

        update_progress(
            job,
            50,
            "Chunks stored",
        )

        chunk_texts = [
            chunk["text"]
            for chunk in chunks
        ]

        embeddings = asyncio.run(
            generate_embeddings_cached(
                chunk_texts
            )
        )

        update_progress(
            job,
            85,
            "Embeddings generated",
        )

        stored_chunks = db.scalars(
            select(Chunk)
            .where(
                Chunk.document_id == document_id
            )
            .order_by(Chunk.chunk_index)
        ).all()

        for chunk, embedding in zip(
            stored_chunks,
            embeddings,
        ):
            chunk.embedding = embedding

        db.commit()

        update_progress(
            job,
            95,
            "Embeddings stored",
        )

        document.status = "ready"
        db.commit()

        update_progress(
            job,
            100,
            "Document processing completed",
        )

        duration_ms = int(
            (time.perf_counter() - start_time) * 1000
        )

        logger.info(
            "Document processing complete | "
            "document_id=%s chunk_count=%s duration_ms=%s",
            document_id,
            len(chunks),
            duration_ms,
        )

        return {
            "success": True,
            "document_id": document_id,
            "chunks": len(chunks),
            "duration_ms": duration_ms,
        }

    except Exception as error:
        db.rollback()

        if job:
            job.refresh()

            if job.retries_left == 0:
                document = db.get(
                    Document,
                    document_id,
                )

                if document:
                    document.status = "failed"
                    db.commit()

        logger.error(
            "Document processing failed | "
            "document_id=%s error=%s",
            document_id,
            str(error),
        )

        raise

    finally:
        db.close()


def record_dead_letter(
    job_id: str,
    error: str,
):
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
