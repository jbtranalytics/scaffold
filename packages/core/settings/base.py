"""Base Settings class for scaffold applications.

Layer 1: Core / Settings.
Ensures layered .env files (.env -> .env.dev/.env.prod -> .env.local) are loaded
and ${env:VAR} / ${VAR:-fallback} patterns are expanded into os.environ before pydantic-settings initialization.
"""

from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict

from packages.core.env import load_workspace_env


class BaseAppSettings(BaseSettings):
    """Base settings model with automatic ${env:VAR} pattern expansion and layered os.environ loading."""

    model_config = SettingsConfigDict(
        env_prefix="",
        extra="ignore",
    )

    def __init__(self, **kwargs: Any) -> None:
        # Pre-pass: Load layered .env files and expand ${env:VAR} patterns into os.environ
        load_workspace_env()
        super().__init__(**kwargs)
