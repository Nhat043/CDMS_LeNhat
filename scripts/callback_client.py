"""Fetch a product and send it to the CDMS webhook

Usage: uv run python -m scripts.callback_client PARTNER00002 [eventId]
"""

import sys
import uuid
from datetime import datetime, timezone

import httpx

from app.core.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    partner_sku = sys.argv[1]
    event_id = sys.argv[2] if len(sys.argv) > 2 else str(uuid.uuid4())

    # Record when the product was read, not when the webhook was sent.
    observed_at = datetime.now(timezone.utc)
    product = (
        httpx.get(f"{settings.inventory_base_url}/api/v1/Products/{partner_sku}")
        .raise_for_status()
        .json()
    )

    response = httpx.post(
        f"{settings.cdms_base_url}/cdms/v1/webhooks/products",
        json={
            "eventId": event_id,
            "observedAt": observed_at.isoformat(),
            "product": product,
        },
    )
    print(response.status_code, response.json())
