from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration read from .env."""

    inventory_database_url: str
    cdms_database_url: str

    inventory_base_url: str = "http://127.0.0.1:8001"
    cdms_base_url: str = "http://127.0.0.1:8002"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Read and validate .env once, then cache"""

    return Settings()
