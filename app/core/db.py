"""Database engines for the two services."""

from sqlalchemy import create_engine
from app.core.config import get_settings

_settings = get_settings()

inventory_engine = create_engine(_settings.inventory_database_url)
cdms_engine = create_engine(_settings.cdms_database_url)
