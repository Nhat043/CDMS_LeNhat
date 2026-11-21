"""Apply an inbox event to the product state and change log"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.cdms.changelog import Outcome, Snapshot, content_hash, decide, diff, normalise
from app.cdms.models import IngestEvent, ProductChange, ProductState


def process(db: Session, event: IngestEvent) -> Outcome:
    payload = normalise(event.raw_payload)
    event.payload = payload
    event.content_hash = content_hash(payload)

    # Serialise everything touching this product. A row lock is not enough:
    # for a product seen for the first time there is no row to lock yet, so
    # two workers would both insert and one would fail on the primary key.
    db.execute(text("SELECT pg_advisory_xact_lock(:pid)"), {"pid": event.product_id})

    state = db.scalar(
        select(ProductState).where(ProductState.product_id == event.product_id)
    )
    current = Snapshot(state.content_hash, state.observed_at) if state else None
    outcome = decide(current, Snapshot(event.content_hash, event.observed_at))

    if outcome is Outcome.APPLIED:
        db.add(
            ProductChange(
                change_id=uuid.uuid4(),
                product_id=event.product_id,
                event_id=event.event_id,
                kind="UPDATED" if state else "CREATED",
                diff=diff(state.payload if state else None, payload),
                observed_at=event.observed_at,
            )
        )
        if state is None:
            state = ProductState(product_id=event.product_id)
            db.add(state)
        state.payload = payload
        state.content_hash = event.content_hash
        state.observed_at = event.observed_at
        state.last_event_id = event.event_id

    elif outcome is Outcome.NO_CHANGE:
        # Content is the same but we have seen it more recently, so move the
        # watermark forward. Otherwise a later stale event would be accepted.
        state.observed_at = event.observed_at
        state.last_event_id = event.event_id

    event.status = outcome.value
    event.processed_at = datetime.now(timezone.utc)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return outcome
