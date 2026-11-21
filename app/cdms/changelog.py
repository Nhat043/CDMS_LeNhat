"""Compare product snapshots.

All three channels use the same comparison logic
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class Outcome(StrEnum):
    APPLIED = "APPLIED"
    NO_CHANGE = "NO_CHANGE"
    STALE = "STALE"


@dataclass(frozen=True)
class Snapshot:
    content_hash: str
    observed_at: datetime


def normalise(raw: dict) -> dict:
    """Convert payloads from different channels into a consistent shape."""
    return {
        "sku": raw.get("sku"),
        "partnerSKU": raw.get("partnerSKU"),
        "productName": raw.get("productName"),
        "assetType": raw.get("assetType"),
        "hasSerial": raw.get("hasSerial"),
        "hasExpiration": raw.get("hasExpiration", raw.get("isExpiryDate")),
        "color": raw.get("color"),
        "size": raw.get("size"),
        "description": raw.get("description"),
        "isActive": raw.get("isActive"),
        "units": sorted(_unit_codes(raw.get("units") or [])),
        "categories": sorted(
            (
                {"categoryCode": c["categoryCode"], "categoryName": c["categoryName"]}
                for c in raw.get("categories") or []
            ),
            key=lambda c: c["categoryCode"],
        ),
    }


def _unit_codes(units: list) -> list[str]:
    return [u if isinstance(u, str) else u["unitCode"] for u in units]


def content_hash(normalised: dict) -> str:
    blob = json.dumps(
        normalised, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(blob.encode()).hexdigest()


def decide(current: Snapshot | None, incoming: Snapshot) -> Outcome:
    if current is None:
        return Outcome.APPLIED
    if incoming.observed_at < current.observed_at:
        return Outcome.STALE
    if incoming.content_hash == current.content_hash:
        return Outcome.NO_CHANGE
    return Outcome.APPLIED


def diff(old: dict | None, new: dict) -> dict:
    """Only the fields that moved, as {field: {from, to}}"""
    if old is None:
        return {key: {"from": None, "to": value} for key, value in new.items()}
    return {
        key: {"from": old.get(key), "to": value}
        for key, value in new.items()
        if old.get(key) != value
    }
