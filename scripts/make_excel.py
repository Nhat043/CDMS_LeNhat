"""Write a sample upload: some good rows, some broken ones."""

from datetime import datetime, timezone

from openpyxl import Workbook

from app.cdms.excel import HEADER

NOW = datetime.now(timezone.utc).replace(tzinfo=None)

ROWS = [
    (
        1,
        "S1",
        "P1",
        "Renamed by spreadsheet",
        "Single",
        True,
        False,
        "Blue",
        "L",
        "updated",
        True,
        "CAI",
        "CAT001|Phone",
        NOW,
    ),
    (
        2,
        "S2",
        "P2",
        "Also renamed",
        "Single",
        False,
        True,
        "Red",
        "M",
        "updated",
        True,
        "CAI,HOP",
        "CAT002|Laptop",
        NOW,
    ),
    (
        "abc",
        "S3",
        "P3",
        "Bad id",
        None,
        None,
        None,
        None,
        None,
        None,
        True,
        "",
        "",
        NOW,
    ),
    (
        4,
        "S4",
        "P4",
        "No timestamp",
        None,
        None,
        None,
        None,
        None,
        None,
        True,
        "",
        "",
        None,
    ),
]

if __name__ == "__main__":
    workbook = Workbook()
    workbook.active.append(HEADER)
    for row in ROWS:
        workbook.active.append(row)
    workbook.save("sample-import.xlsx")
    print("wrote sample-import.xlsx")
