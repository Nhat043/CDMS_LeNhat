"""Fill the emulator with fake products."""

import random
import sys

from faker import Faker

from app.core.db import InventorySession
from app.inventory import service
from app.inventory.schemas import Category, ProductWrite, Unit

UNITS = [("CAI", "Cai"), ("HOP", "Hop"), ("THUNG", "Thung")]
CATEGORIES = [("CAT001", "Phone"), ("CAT002", "Laptop"), ("CAT003", "Accessory")]

fake = Faker()


def make_product(n: int) -> ProductWrite:
    unit_code, unit_name = random.choice(UNITS)
    category_code, category_name = random.choice(CATEGORIES)
    return ProductWrite(
        sku=f"SKU{n:05d}",
        partnerSKU=f"PARTNER{n:05d}",
        productName=fake.catch_phrase(),
        assetType=random.choice(["Single", "Bundle"]),
        serialType=random.choice([1, 2]),
        isExpiryDate=fake.boolean(),
        color=fake.color_name(),
        size=random.choice(["S", "M", "L", "XXL"]),
        description=fake.sentence(),
        units=[Unit(unitCode=unit_code, unitName=unit_name)],
        categories=[Category(categoryCode=category_code, categoryName=category_name)],
    )


count = int(sys.argv[1]) if len(sys.argv) > 1 else 20

with InventorySession() as db:
    start = service.count(db) + 1
    service.create(db, [make_product(start + i) for i in range(count)])

print(f"created {count} products")
