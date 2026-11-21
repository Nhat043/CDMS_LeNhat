"""Poll the inventory API for product updates.

The API has no date filter or total count, so each run scans all pages
"""

import uuid
from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from app.cdms.models import IngestBatch, IngestEvent
from app.core.config import get_settings


def poll_once(db: Session) -> int:
    settings = get_settings()
    batch_id = uuid.uuid4()
    db.add(IngestBatch(batch_id=batch_id, channel="POLLING"))

    count = 0
    page = 0
    with httpx.Client(base_url=settings.inventory_base_url, timeout=10) as client:
        while True:
            # Timestamp each page when it's read, not once per polling cycle
            observed_at = datetime.now(timezone.utc)
            products = (
                client.get(
                    "/api/v1/Products",
                    params={"PageIndex": page, "PageSize": settings.poll_page_size},
                )
                .raise_for_status()
                .json()
            )

            for product in products:
                db.add(
                    IngestEvent(
                        event_id=uuid.uuid4(),
                        batch_id=batch_id,
                        channel="POLLING",
                        dedup_key=f"poll:{batch_id}:{product['productId']}",
                        product_id=product["productId"],
                        observed_at=observed_at,
                        raw_payload=product,
                    )
                )
                count += 1

            if len(products) < settings.poll_page_size:
                break
            page += 1

    db.commit()
    return count
