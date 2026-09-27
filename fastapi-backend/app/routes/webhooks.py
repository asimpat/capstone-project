import json
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.lib.webhooks.security import verify_signature
from app.models.webhook_event import WebhookEvent


router = APIRouter(
    prefix="/webhooks",
    tags=["Webhooks"],
)


@router.post("/example")
async def receive_webhook(
    request: Request,
    x_webhook_signature: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    if not x_webhook_signature:
        raise HTTPException(
            status_code=401,
            detail="Missing signature header",
        )

    raw_body = await request.body()

    secret = os.getenv("WEBHOOK_SECRET")

    if not secret:
        raise HTTPException(
            status_code=500,
            detail="Webhook secret is not configured",
        )

    valid = verify_signature(
        raw_body,
        x_webhook_signature,
        secret,
    )

    if not valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid signature",
        )

    try:
        event = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON",
        )

    event_id = event.get("id")
    event_type = event.get("type")

    if not event_id or not event_type:
        raise HTTPException(
            status_code=400,
            detail="Invalid webhook event",
        )

    existing = db.get(
        WebhookEvent,
        event_id,
    )

    if existing and existing.processed_at:
        return {
            "received": True,
            "duplicate": True,
        }

    if not existing:
        webhook_event = WebhookEvent(
            id=event_id,
            provider="example",
            event_type=event_type,
            payload=raw_body.decode("utf-8"),
        )

        db.add(webhook_event)
        db.commit()

    # In the full production version, processing goes to a queue.
    # For this lesson, acknowledge the webhook quickly.

    return {
        "received": True,
    }
