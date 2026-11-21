"""Schedule polls and process pending inbox events

All channels use the same processor to update product state
"""

import logging
import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.cdms.channels.polling import poll_once
from app.cdms.models import IngestEvent
from app.cdms.processor import process
from app.core.config import get_settings
from app.core.db import CdmsSession

log = logging.getLogger("worker")


def drain(db: Session, limit: int) -> int:
    events = db.scalars(
        select(IngestEvent)
        .where(IngestEvent.status == "PENDING")
        .order_by(IngestEvent.received_at)
        .limit(limit)
    ).all()

    for event in events:
        try:
            process(db, event)
        except Exception:
            # Keep processing even if one event fails.
            # The raw payload is kept for debugging
            log.exception("event %s failed", event.event_id)
            db.rollback()
            failed = db.get(IngestEvent, event.event_id)
            failed.status = "FAILED"
            failed.attempts += 1
            db.commit()

    return len(events)


def run() -> None:
    settings = get_settings()
    next_poll = time.monotonic()

    while True:
        worked = 0
        with CdmsSession() as db:
            if settings.poll_enabled and time.monotonic() >= next_poll:
                try:
                    queued = poll_once(db)
                    log.info("polled %s products", queued)
                except Exception:
                    # A failed poll shouldn't stop inbox processing
                    log.exception("poll failed")
                    db.rollback()
                next_poll = time.monotonic() + settings.poll_interval_seconds

            worked = drain(db, settings.worker_batch_size)
            if worked:
                log.info("processed %s events", worked)

        if not worked:
            time.sleep(settings.worker_idle_sleep_seconds)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    run()
