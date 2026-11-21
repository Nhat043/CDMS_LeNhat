import uuid
from datetime import datetime, timedelta, timezone


from app.cdms.changelog import Outcome
from app.cdms.models import IngestEvent, ProductChange, ProductState
from app.cdms.processor import process

T0 = datetime(2026, 11, 21, 10, 0, tzinfo=timezone.utc)
T1 = T0 + timedelta(minutes=5)

PRODUCT = {"productId": 9001, "sku": "S1", "productName": "First", "isActive": True}


def add_event(db, payload, observed_at):
    event = IngestEvent(
        event_id=uuid.uuid4(),
        channel="WEBHOOK",
        dedup_key=f"test:{uuid.uuid4()}",
        product_id=9001,
        observed_at=observed_at,
        raw_payload=payload,
    )
    db.add(event)
    db.flush()
    return event


def test_new_product_creates_one_change(db):
    assert process(db, add_event(db, PRODUCT, T0)) is Outcome.APPLIED
    assert db.query(ProductChange).filter_by(product_id=9001).count() == 1


def test_same_payload_twice_creates_one_change(db):
    process(db, add_event(db, PRODUCT, T0))
    assert process(db, add_event(db, PRODUCT, T1)) is Outcome.NO_CHANGE
    assert db.query(ProductChange).filter_by(product_id=9001).count() == 1


def test_older_event_is_rejected(db):
    process(db, add_event(db, PRODUCT, T1))
    changed = PRODUCT | {"productName": "Second"}
    assert process(db, add_event(db, changed, T0)) is Outcome.STALE
    assert db.query(ProductChange).filter_by(product_id=9001).count() == 1


def test_changed_payload_adds_a_second_change(db):
    process(db, add_event(db, PRODUCT, T0))
    changed = PRODUCT | {"productName": "Second"}
    process(db, add_event(db, changed, T1))
    changes = db.query(ProductChange).filter_by(product_id=9001).all()
    assert len(changes) == 2
    assert changes[1].diff["productName"] == {"from": "First", "to": "Second"}


def test_no_change_advances_watermark(db):
    process(db, add_event(db, PRODUCT, T0))

    assert process(db, add_event(db, PRODUCT, T1)) is Outcome.NO_CHANGE

    changed = PRODUCT | {"productName": "Second"}
    assert (
        process(db, add_event(db, changed, T0 + timedelta(minutes=2))) is Outcome.STALE
    )

    state = db.get(ProductState, 9001)
    assert state.observed_at == T1
    assert db.query(ProductChange).filter_by(product_id=9001).count() == 1
