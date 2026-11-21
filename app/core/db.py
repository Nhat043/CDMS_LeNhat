"""Database engines for the two services."""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class InventoryBase(DeclarativeBase):
    """Base for the emulated inventory service tables."""


class CdmsBase(DeclarativeBase):
    """Base for the CDMS tables."""


_settings = get_settings()

inventory_engine = create_engine(_settings.inventory_database_url)
cdms_engine = create_engine(_settings.cdms_database_url)

InventorySession = sessionmaker(bind=inventory_engine, expire_on_commit=False)


def get_inventory_db() -> Iterator[Session]:
    with InventorySession() as db:
        yield db
