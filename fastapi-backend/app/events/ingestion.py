import json

from app.utils.logger import logger
from app.utils.metrics import documents_processed


def handle_document_processed(data: dict):
    try:
        from app.database.session import SessionLocal
        from app.models.usage_log import UsageLog

        db = SessionLocal()

        try:
            usage_log = UsageLog(
                user_id=data["user_id"],
                action="document_ingested",
                tokens=0,
                cost_usd=0,
                metadata=json.dumps({
                    "documentId": data["document_id"],
                    "chunkCount": data["chunk_count"],
                    "durationMs": data["duration_ms"],
                    "format": data.get("format"),
                    "pageCount": data.get("page_count"),
                }),
            )

            db.add(usage_log)
            db.commit()

            documents_processed.labels(
                status="success"
            ).inc()

            logger.info(
                "Ingestion logged | "
                "document_id=%s chunk_count=%s",
                data["document_id"],
                data["chunk_count"],
            )

        finally:
            db.close()

    except Exception as error:
        logger.error(
            "Failed to log ingestion | error=%s",
            str(error),
        )
