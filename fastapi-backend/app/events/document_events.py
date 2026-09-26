from app.models.usage_log import UsageLog


def log_document_created(db, user_id: str, document_id: str):
    try:
        usage_log = UsageLog(
            user_id=user_id,
            document_id=document_id,
            event="doc:created",
            tokens=0,
        )

        db.add(usage_log)
        db.commit()

    except Exception:
        db.rollback()


def log_document_deleted(db, user_id: str, document_id: str):
    try:
        usage_log = UsageLog(
            user_id=user_id,
            document_id=document_id,
            event="doc:deleted",
            tokens=0,
        )

        db.add(usage_log)
        db.commit()

    except Exception:
        db.rollback()
