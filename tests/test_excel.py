import pytest
from datetime import datetime, timezone
from io import BytesIO

from openpyxl import Workbook

from app.cdms.excel import HEADER, parse


def build(*rows) -> bytes:
    workbook = Workbook()
    workbook.active.append(HEADER)
    for row in rows:
        workbook.active.append(row)
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


GOOD = (
    7,
    "S7",
    "P7",
    "Name",
    "Single",
    True,
    False,
    "Red",
    "M",
    "d",
    True,
    "CAI,HOP",
    "CAT001|Phone;CAT002|Laptop",
    datetime(2026, 11, 21, 10, 0),
)


def test_a_good_row_parses():
    row = parse(build(GOOD), max_rows=10)[0]
    assert row.error is None
    assert row.product_id == 7
    assert row.payload["units"] == ["CAI", "HOP"]
    assert row.payload["categories"][0] == {
        "categoryCode": "CAT001",
        "categoryName": "Phone",
    }


def test_observed_at_is_read_as_utc():
    row = parse(build(GOOD), max_rows=10)[0]
    assert row.observed_at == datetime(2026, 11, 21, 10, 0, tzinfo=timezone.utc)


def test_a_bad_product_id_is_rejected_without_losing_the_row():
    row = parse(build(("abc",) + GOOD[1:]), max_rows=10)[0]
    assert row.error is not None
    assert row.product_id is None
    assert row.payload["sku"] == "S7"


def test_a_missing_observed_at_is_rejected():
    assert parse(build(GOOD[:13] + (None,)), max_rows=10)[0].error is not None


def test_one_bad_row_does_not_affect_the_others():
    rows = parse(
        build(GOOD, ("abc",) + GOOD[1:], GOOD[:1] + ("S8",) + GOOD[2:]), max_rows=10
    )
    assert [r.error is None for r in rows] == [True, False, True]


def test_too_many_rows_are_rejected():
    with pytest.raises(ValueError, match="more than 2 data rows"):
        parse(build(GOOD, GOOD, GOOD), max_rows=2)
