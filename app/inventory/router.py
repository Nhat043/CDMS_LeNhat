"""Vietful Products API emulator"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.core.db import get_inventory_db
from app.inventory import service
from app.inventory.models import Product
from app.inventory.schemas import ProductDetail, ProductListItem, ProductWrite

router = APIRouter(prefix="/api/v1/Products", tags=["Products"])


def _require(product: Product | None, key: str | int) -> Product:
    if product is None:
        raise HTTPException(404, f"Product {key} not found")
    return product


# The API returns a bare array, so clients page until they get fewer rows
@router.get("", response_model=list[ProductListItem])
def list_products(
    PageIndex: int = Query(0, ge=0),
    PageSize: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_inventory_db),
):
    products = service.list_products(db, PageIndex, PageSize)
    return [ProductListItem.from_product(p) for p in products]


@router.get("/{partnerSKU}", response_model=ProductDetail)
def get_product(partnerSKU: str, db: Session = Depends(get_inventory_db)):
    product = _require(service.get_by_partner_sku(db, partnerSKU), partnerSKU)
    return ProductDetail.from_product(product)


@router.post("", response_model=list[ProductDetail], status_code=201)
def create_products(body: list[ProductWrite], db: Session = Depends(get_inventory_db)):
    return [ProductDetail.from_product(p) for p in service.create(db, body)]


@router.put("/{product_id}", response_model=ProductDetail)
def update_product(
    product_id: int, body: ProductWrite, db: Session = Depends(get_inventory_db)
):
    product = _require(service.get_by_id(db, product_id), product_id)
    return ProductDetail.from_product(service.update(db, product, body))


# isActive can only be changed through these endpoints.
@router.put("/{product_id}/activate", status_code=204, response_class=Response)
def activate(product_id: int, db: Session = Depends(get_inventory_db)):
    service.set_active(
        db, _require(service.get_by_id(db, product_id), product_id), True
    )


@router.put("/{product_id}/de-activate", status_code=204, response_class=Response)
def deactivate(product_id: int, db: Session = Depends(get_inventory_db)):
    service.set_active(
        db, _require(service.get_by_id(db, product_id), product_id), False
    )
