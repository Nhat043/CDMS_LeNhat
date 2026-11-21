"""Vietful API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.inventory.models import Product


class Category(BaseModel):
    categoryCode: str
    categoryName: str


class Unit(BaseModel):
    unitCode: str
    unitName: str
    length: float | None = None
    width: float | None = None
    height: float | None = None
    weight: float | None = None


class ProductListItem(BaseModel):
    """List response. units only contains unit codes."""

    productId: int
    sku: str
    partnerSKU: str
    productName: str
    assetType: str | None
    hasSerial: bool
    hasExpiration: bool
    color: str | None
    size: str | None
    description: str | None
    isActive: bool
    units: list[str]
    categories: list[Category]

    @classmethod
    def from_product(cls, p: Product) -> ProductListItem:
        return cls(
            productId=p.product_id,
            sku=p.sku,
            partnerSKU=p.partner_sku,
            productName=p.product_name,
            assetType=p.asset_type,
            hasSerial=p.has_serial,
            hasExpiration=p.has_expiration,
            color=p.color,
            size=p.size,
            description=p.description,
            isActive=p.is_active,
            units=[u["unitCode"] for u in p.units],
            categories=p.categories,
        )


class ProductDetail(BaseModel):
    """Detail response with full unit objects."""

    productId: int
    sku: str
    partnerSKU: str
    productName: str
    assetType: str | None
    hasSerial: bool
    isExpiryDate: bool
    color: str | None
    size: str | None
    description: str | None
    isActive: bool
    units: list[Unit]
    categories: list[Category]

    @classmethod
    def from_product(cls, p: Product) -> ProductDetail:
        return cls(
            productId=p.product_id,
            sku=p.sku,
            partnerSKU=p.partner_sku,
            productName=p.product_name,
            assetType=p.asset_type,
            hasSerial=p.has_serial,
            isExpiryDate=p.has_expiration,
            color=p.color,
            size=p.size,
            description=p.description,
            isActive=p.is_active,
            units=p.units,
            categories=p.categories,
        )


class ProductWrite(BaseModel):
    """Fields used by POST and PUT."""

    sku: str
    partnerSKU: str
    productName: str
    assetType: str | None = None
    serialType: int = 2  # 1 = Serial, 2 = NonSerial
    isExpiryDate: bool = False
    color: str | None = None
    size: str | None = None
    description: str | None = None
    units: list[Unit] = Field(default_factory=list)
    categories: list[Category] = Field(default_factory=list)
