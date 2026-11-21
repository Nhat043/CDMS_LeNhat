"""Database operations for the inventory service"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.inventory.models import Product
from app.inventory.schemas import ProductWrite


def list_products(db: Session, page_index: int, page_size: int) -> list[Product]:
    return list(
        db.scalars(
            select(Product)
            .order_by(Product.product_id)
            .offset(page_index * page_size)
            .limit(page_size)
        )
    )


def get_by_partner_sku(db: Session, partner_sku: str) -> Product | None:
    return db.scalar(select(Product).where(Product.partner_sku == partner_sku))


def get_by_id(db: Session, product_id: int) -> Product | None:
    return db.get(Product, product_id)


def create(db: Session, items: list[ProductWrite]) -> list[Product]:
    products = [Product() for _ in items]

    for product, item in zip(products, items):
        _apply(product, item)

    db.add_all(products)
    db.commit()
    return products


def update(db: Session, product: Product, body: ProductWrite) -> Product:
    _apply(product, body)
    db.commit()
    return product


def set_active(db: Session, product: Product, active: bool) -> None:
    product.is_active = active
    db.commit()


def _apply(product: Product, body: ProductWrite) -> Product:
    product.sku = body.sku
    product.partner_sku = body.partnerSKU
    product.product_name = body.productName
    product.asset_type = body.assetType
    product.has_serial = body.serialType == 1
    product.has_expiration = body.isExpiryDate
    product.color = body.color
    product.size = body.size
    product.description = body.description
    product.units = [u.model_dump() for u in body.units]
    product.categories = [c.model_dump() for c in body.categories]
    return product


def count(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(Product)) or 0
