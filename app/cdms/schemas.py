"""Webhook request schemas."""

from pydantic import AwareDatetime, BaseModel


class Category(BaseModel):
    categoryCode: str
    categoryName: str


class Unit(BaseModel):
    unitCode: str
    unitName: str | None = None


class WebhookProduct(BaseModel):
    productId: int
    sku: str | None = None
    partnerSKU: str | None = None
    productName: str | None = None
    assetType: str | None = None
    hasSerial: bool | None = None
    hasExpiration: bool | None = None
    color: str | None = None
    size: str | None = None
    description: str | None = None
    isActive: bool | None = None
    # Accept both list and detail endpoint formats.
    units: list[str | Unit] = []
    categories: list[Category] = []


class ProductWebhook(BaseModel):
    eventId: str
    observedAt: AwareDatetime
    product: WebhookProduct
