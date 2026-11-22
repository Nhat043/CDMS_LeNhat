"""Parse Excel uploads into inbox events"""

from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO

from openpyxl import load_workbook

HEADER = (
    "productId",
    "sku",
    "partnerSKU",
    "productName",
    "assetType",
    "hasSerial",
    "hasExpiration",
    "color",
    "size",
    "description",
    "isActive",
    "units",
    "categories",
    "observedAt",
)


@dataclass(frozen=True)
class ParsedRow:
    row_number: int
    product_id: int | None
    observed_at: datetime | None
    payload: dict
    error: str | None


def parse(contents: bytes, max_rows: int) -> list[ParsedRow]:
    workbook = load_workbook(BytesIO(contents), read_only=True, data_only=True)
    try:
        sheet = workbook.active
        rows = sheet.iter_rows(values_only=True)

        header = tuple(next(rows, ()))[: len(HEADER)]
        if header != HEADER:
            raise ValueError(f"header must be: {', '.join(HEADER)}")

        parsed = []
        for number, cells in enumerate(rows, start=2):
            if number - 1 > max_rows:
                raise ValueError(f"sheet has more than {max_rows} data rows")
            parsed.append(_row(number, cells))
        return parsed
    finally:
        workbook.close()


def _row(number: int, cells: tuple) -> ParsedRow:
    values = dict(zip(HEADER, cells + (None,) * (len(HEADER) - len(cells))))
    payload = {
        "productId": values["productId"],
        "sku": _text(values["sku"]),
        "partnerSKU": _text(values["partnerSKU"]),
        "productName": _text(values["productName"]),
        "assetType": _text(values["assetType"]),
        "hasSerial": _flag(values["hasSerial"]),
        "hasExpiration": _flag(values["hasExpiration"]),
        "color": _text(values["color"]),
        "size": _text(values["size"]),
        "description": _text(values["description"]),
        "isActive": _flag(values["isActive"]),
        "units": _units(values["units"]),
        "categories": _categories(values["categories"]),
    }

    error = None
    if not isinstance(values["productId"], int) or values["productId"] < 1:
        error = "productId must be a positive whole number"
    observed_at = _observed_at(values["observedAt"])
    if error is None and observed_at is None:
        error = "observedAt must be a date and time"

    return ParsedRow(
        row_number=number,
        product_id=values["productId"] if error is None else None,
        observed_at=observed_at,
        payload=payload,
        error=error,
    )


def _text(cell) -> str | None:
    if cell is None:
        return None
    text = str(cell).strip()
    return text or None


def _flag(cell) -> bool | None:
    if isinstance(cell, bool):
        return cell
    if cell is None:
        return None
    return str(cell).strip().upper() in {"TRUE", "1", "YES", "Y"}


def _units(cell) -> list[str]:
    return [code.strip() for code in str(cell or "").split(",") if code.strip()]


def _categories(cell) -> list[dict]:
    out = []
    for pair in str(cell or "").split(";"):
        code, _, name = pair.strip().partition("|")
        if code.strip():
            out.append({"categoryCode": code.strip(), "categoryName": name.strip()})
    return out


def _observed_at(cell) -> datetime | None:
    if not isinstance(cell, datetime):
        return None
    # Excel has no timezone, so treat values as UTC
    return cell if cell.tzinfo else cell.replace(tzinfo=timezone.utc)
