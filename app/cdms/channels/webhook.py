"""Receive product webhooks"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.cdms.models import IngestEvent
from app.cdms.schemas import ProductWebhook
from app.core.db import get_cdms_db

router = APIRouter(prefix="/cdms/v1", tags=["Webhook"])


@router.post("/webhooks/products", status_code=202)
def receive_product(body: ProductWebhook, db: Session = Depends(get_cdms_db)):
    event = IngestEvent(
        event_id=uuid.uuid4(),
        channel="WEBHOOK",
        dedup_key=f"webhook:{body.eventId}",
        product_id=body.product.productId,
        observed_at=body.observedAt,
        raw_payload=body.product.model_dump(),
    )
    db.add(event)
    try:
        db.commit()
    except IntegrityError:
        # Ignore retries with an existing dedup_key.
        db.rollback()
        return {"status": "duplicate", "eventId": body.eventId}

    return {"status": "accepted", "eventId": body.eventId}
