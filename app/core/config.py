from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration read from .env."""

    inventory_database_url: str
    cdms_database_url: str

    inventory_base_url: str = "http://127.0.0.1:8001"
    cdms_base_url: str = "http://127.0.0.1:8002"
    poll_page_size: int = 50
    poll_enabled: bool = True
    poll_interval_seconds: float = 30
    worker_batch_size: int = 200
    worker_idle_sleep_seconds: float = 1.0

    excel_max_bytes: int = 5 * 1024 * 1024
    excel_max_rows: int = 10_000

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
