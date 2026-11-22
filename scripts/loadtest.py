"""Spike and concurrency check against a running stack.

Run it inside the stack so it sees the same database:
    docker compose exec cdms python -m scripts.loadtest
"""

import asyncio
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import func, select

from app.cdms.models import IngestEvent, ProductChange, ProductState
from app.core.config import get_settings
from app.core.db import CdmsSession

BURST = int(sys.argv[1]) if len(sys.argv) > 1 else 200
PRODUCT_ID = 990001  # outside anything the emulator creates
RUN = uuid.uuid4().hex[:8]


def payload(event_id: str, observed_at: datetime, name: str) -> dict:
    return {
        "eventId": event_id,
        "observedAt": observed_at.isoformat(),
        "product": {
            "productId": PRODUCT_ID,
            "sku": "SPIKE",
            "productName": name,
            "isActive": True,
            "units": ["CAI"],
            "categories": [],
        },
    }


async def fire(url: str, bodies: list[dict]) -> list[str]:
    limits = httpx.Limits(max_connections=50)
    async with httpx.AsyncClient(timeout=30, limits=limits) as client:
        responses = await asyncio.gather(
            *(client.post(url, json=body) for body in bodies)
        )
    return [r.json().get("status", str(r.status_code)) for r in responses]


def wait_for_drain(timeout: float = 180) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with CdmsSession() as db:
            if not db.query(IngestEvent).filter_by(status="PENDING").count():
                return True
        time.sleep(0.5)
    return False


def count_events(dedup_key: str) -> int:
    with CdmsSession() as db:
        return db.query(IngestEvent).filter_by(dedup_key=dedup_key).count()


def count_changes(product_id: int) -> int:
    with CdmsSession() as db:
        return db.query(ProductChange).filter_by(product_id=product_id).count()


def check_no_lost_updates() -> list[str]:
    """Check that product states haven't lost any updates"""
    problems = []
    with CdmsSession() as db:
        for state in db.scalars(select(ProductState)):
            source = db.get(IngestEvent, state.last_event_id)
            if source.content_hash != state.content_hash:
                problems.append(
                    f"product {state.product_id}: state hash != last event hash"
                )

            newer = db.scalar(
                select(IngestEvent)
                .where(
                    IngestEvent.product_id == state.product_id,
                    IngestEvent.status == "APPLIED",
                    IngestEvent.observed_at > state.observed_at,
                )
                .limit(1)
            )
            if newer is not None:
                problems.append(
                    f"product {state.product_id}: an applied event is newer than the state"
                )
    return problems


def main() -> None:
    url = f"{get_settings().cdms_base_url}/cdms/v1/webhooks/products"
    now = datetime.now(timezone.utc)

    print(f"burst size: {BURST}\n")

    # A - the same callback arriving many times at once
    repeated = f"spike-same-{uuid.uuid4()}"
    started = time.monotonic()
    statuses = asyncio.run(
        fire(
            url, [payload(repeated, now, f"same callback {RUN}") for _ in range(BURST)]
        )
    )
    elapsed = time.monotonic() - started
    stored = count_events(f"webhook:{repeated}")
    print(f"A  {BURST} concurrent posts of one eventId in {elapsed:.2f}s")
    print(
        f"   accepted={statuses.count('accepted')} duplicate={statuses.count('duplicate')}"
    )
    print(f"   rows stored: {stored}  -> {'ok' if stored == 1 else 'FAIL'}\n")

    # B - distinct events carrying identical content
    before = count_changes(PRODUCT_ID)
    bodies = [
        payload(
            f"spike-{uuid.uuid4()}", now + timedelta(seconds=i), f"one content {RUN}"
        )
        for i in range(BURST)
    ]
    started = time.monotonic()
    statuses = asyncio.run(fire(url, bodies))
    elapsed = time.monotonic() - started
    print(f"B  {BURST} concurrent posts, distinct ids, same content in {elapsed:.2f}s")
    print(f"   accepted={statuses.count('accepted')}")

    if not wait_for_drain():
        print("   FAIL inbox did not drain")
        return
    produced = count_changes(PRODUCT_ID) - before
    print(f"   changes produced: {produced}  -> {'ok' if produced == 1 else 'FAIL'}\n")

    # C - the whole picture, with polling running throughout
    problems = check_no_lost_updates()
    print("C  no lost updates across every product")
    for problem in problems:
        print("   FAIL", problem)
    if not problems:
        print("   ok\n")

    with CdmsSession() as db:
        print("spike product:")
        for status, n in db.execute(
            select(IngestEvent.status, func.count())
            .where(IngestEvent.product_id == PRODUCT_ID)
            .group_by(IngestEvent.status)
        ).all():
            print(f"   {status:10} {n}")
        print(
            f"\ntotals: {db.query(IngestEvent).count()} events, "
            f"{db.query(ProductChange).count()} changes, "
            f"{db.query(ProductState).count()} states"
        )


if __name__ == "__main__":
    main()
