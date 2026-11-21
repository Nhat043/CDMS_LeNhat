"""Process pending inbox events"""

from sqlalchemy import select

from app.cdms.models import IngestEvent
from app.cdms.processor import process
from app.core.db import CdmsSession

if __name__ == "__main__":
    with CdmsSession() as db:
        events = db.scalars(
            select(IngestEvent)
            .where(IngestEvent.status == "PENDING")
            .order_by(IngestEvent.received_at)
        ).all()
        for event in events:
            print(event.event_id, process(db, event))
        print(f"processed {len(events)}")
