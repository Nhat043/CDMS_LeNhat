from datetime import datetime, timedelta

from app.cdms.changelog import Outcome, Snapshot, content_hash, decide, diff, normalise

T0 = datetime(2026, 11, 21, 10, 0, 0)
T1 = T0 + timedelta(minutes=5)


def snap(h: str, at: datetime) -> Snapshot:
    return Snapshot(content_hash=h, observed_at=at)


def test_first_sight_of_a_product_is_a_change():
    assert decide(None, snap("a", T0)) is Outcome.APPLIED


def test_older_observation_does_not_overwrite_newer_state():
    assert decide(snap("a", T1), snap("b", T0)) is Outcome.STALE


def test_same_content_seen_later_is_not_a_change():
    assert decide(snap("a", T0), snap("a", T1)) is Outcome.NO_CHANGE


def test_different_content_seen_later_is_a_change():
    assert decide(snap("a", T0), snap("b", T1)) is Outcome.APPLIED


def test_unit_codes_and_unit_objects_hash_the_same():
    from_list = {"units": ["CAI", "HOP"]}
    from_details = {
        "units": [
            {"unitCode": "HOP", "unitName": "Hop"},
            {"unitCode": "CAI", "unitName": "Cai"},
        ]
    }
    assert content_hash(normalise(from_list)) == content_hash(normalise(from_details))


def test_the_two_names_for_the_expiry_flag_agree():
    assert normalise({"hasExpiration": True}) == normalise({"isExpiryDate": True})


def test_diff_only_contains_fields_that_moved():
    old = normalise({"productName": "A", "color": "Red"})
    new = normalise({"productName": "B", "color": "Red"})
    assert diff(old, new) == {"productName": {"from": "A", "to": "B"}}


def test_false_expiry_flag_is_preserved():
    assert (
        normalise(
            {
                "hasExpiration": False,
                "isExpiryDate": True,
            }
        )["hasExpiration"]
        is False
    )


def test_category_order_does_not_affect_hash():
    first = {
        "categories": [
            {"categoryCode": "B", "categoryName": "B"},
            {"categoryCode": "A", "categoryName": "A"},
        ]
    }
    second = {
        "categories": [
            {"categoryCode": "A", "categoryName": "A"},
            {"categoryCode": "B", "categoryName": "B"},
        ]
    }

    assert content_hash(normalise(first)) == content_hash(normalise(second))


def test_first_snapshot_diff_contains_all_fields():
    new = normalise({"productName": "Phone", "color": "Black"})

    assert diff(None, new) == {
        "sku": {"from": None, "to": None},
        "partnerSKU": {"from": None, "to": None},
        "productName": {"from": None, "to": "Phone"},
        "assetType": {"from": None, "to": None},
        "hasSerial": {"from": None, "to": None},
        "hasExpiration": {"from": None, "to": None},
        "color": {"from": None, "to": "Black"},
        "size": {"from": None, "to": None},
        "description": {"from": None, "to": None},
        "isActive": {"from": None, "to": None},
        "units": {"from": None, "to": []},
        "categories": {"from": None, "to": []},
    }
