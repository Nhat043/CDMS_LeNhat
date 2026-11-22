"""Upload a spreadsheet to CDMS

    python -m scripts.upload_excel [path]
"""

import sys

import httpx

from app.core.config import get_settings

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "sample-import.xlsx"
    with open(path, "rb") as handle:
        response = httpx.post(
            f"{get_settings().cdms_base_url}/cdms/v1/imports/products",
            files={"file": (path, handle)},
        )
    print(response.status_code, response.json())