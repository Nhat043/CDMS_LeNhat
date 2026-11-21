"""Vietful inventory emulator."""

from fastapi import FastAPI

from app.core.db import InventoryBase, inventory_engine
from app.inventory import models  # noqa: F401
from app.inventory.router import router

# Create the emulator tables on startup. No migrations needed.
InventoryBase.metadata.create_all(inventory_engine)

app = FastAPI(title="Vietful inventory emulator")
app.include_router(router)
