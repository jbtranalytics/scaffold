"""PostgreSQL connection and pool settings.

Layer 1: Core / Settings.
Pure configuration models backed by pydantic-settings.
"""

from functools import lru_cache

from packages.core.settings.base import BaseAppSettings


class PostgresSettings(BaseAppSettings):
    """PostgreSQL configuration settings with dynamic layered environment variable loading."""

    url: str = "postgresql://postgres:postgres@localhost:5432/scaffold_dev"
    min_size: int = 1
    max_size: int = 10


@lru_cache(maxsize=1)
def get_postgres_settings() -> PostgresSettings:
    """Return default overridable singleton for Postgres settings."""
    return PostgresSettings()
