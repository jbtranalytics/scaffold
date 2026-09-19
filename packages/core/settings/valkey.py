"""Valkey connection settings.

Layer 1: Core / Settings.
Pure configuration models backed by pydantic-settings.
"""

from functools import lru_cache

from packages.core.settings.base import BaseAppSettings


class ValkeySettings(BaseAppSettings):
    """Valkey / Redis configuration settings with dynamic layered environment variable loading."""

    url: str = "valkey://localhost:6379"


@lru_cache(maxsize=1)
def get_valkey_settings() -> ValkeySettings:
    """Return default overridable singleton for Valkey settings."""
    return ValkeySettings()
