"""Base storage data models (Layer 3).

Standard base models and schemas shared across storage providers (Postgres, Valkey, etc.).
"""

from datetime import UTC, datetime
from typing import Any

from sqlmodel import Field, SQLModel


class BaseKVStoreModel(SQLModel, table=True):
    """Base SQLModel table for Key-Value & Secret storage.

    Compatible with both PostgreSQL table storage and Valkey/Redis KV structures.
    Provides exact parity with Valkey KV fields:
    - key: Unique primary key identifier
    - value: Raw, encrypted, or hashed payload
    - ttl_seconds: Optional TTL duration in seconds
    - expires_at: Optional absolute timestamp when key expires
    - created_at: Timestamp when record was inserted
    - updated_at: Timestamp when record was last updated or touched
    """

    __tablename__: Any = "base_kv_store"

    key: str = Field(primary_key=True)
    value: str = Field(nullable=False)
    ttl_seconds: int | None = Field(default=None, nullable=True)
    expires_at: datetime | None = Field(default=None, nullable=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        nullable=False,
    )
