"""Storage contracts, protocols, and interfaces.

Layer 2: Protocols (schemas, procedure definitions, abstract contracts).
Depends solely on Layer 1 (Core).
"""

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from packages.core.result import Result


@runtime_checkable
class KeyValueStore(Protocol):
    """Protocol defining asynchronous Key-Value store operations (e.g. Valkey / Redis)."""

    async def get(self, key: str) -> Result[str | None, str]:
        """Retrieve a string value by key."""
        ...

    async def set(
        self,
        key: str,
        value: str,
        ttl_seconds: int | None = None,
    ) -> Result[bool, str]:
        """Store a string value with optional TTL in seconds."""
        ...

    async def delete(self, key: str) -> Result[bool, str]:
        """Delete a key."""
        ...

    async def exists(self, key: str) -> Result[bool, str]:
        """Check if a key exists."""
        ...

    async def touch(self, key: str, ttl_seconds: int) -> Result[bool, str]:
        """Update or refresh the time-to-live (TTL) expiration in seconds for an existing key."""
        ...

    async def ttl(self, key: str) -> Result[int | None, str]:
        """Return remaining time-to-live in seconds (-1 if no expiry, None if key does not exist)."""
        ...


@runtime_checkable
class EncryptedKeyValueStore(Protocol):
    """Protocol for storing and retrieving encrypted-at-rest secrets."""

    async def set_encrypted(
        self,
        key: str,
        secret_value: str,
        ttl_seconds: int | None = None,
        key_override: str | bytes | None = None,
    ) -> Result[bool, str]:
        """Encrypt secret value at rest and store it."""
        ...

    async def get_decrypted(
        self,
        key: str,
        key_override: str | bytes | None = None,
    ) -> Result[str | None, str]:
        """Retrieve and decrypt an encrypted-at-rest value."""
        ...


@runtime_checkable
class HashedKeyValueStore(Protocol):
    """Protocol for storing and verifying one-way hashed secrets (e.g. passwords, API tokens)."""

    async def set_hashed(
        self,
        key: str,
        secret: str,
        ttl_seconds: int | None = None,
    ) -> Result[str, str]:
        """Hash a secret with Argon2id, store the hash, and return the hash string."""
        ...

    async def verify_hashed(self, key: str, candidate_secret: str) -> Result[bool, str]:
        """Verify candidate secret against the stored Argon2id hash."""
        ...


@runtime_checkable
class RelationalStore(Protocol):
    """Protocol defining asynchronous Relational database operations (e.g. PostgreSQL)."""

    async def execute(
        self,
        query: str,
        params: tuple[object, ...] | dict[str, object] | None = None,
    ) -> Result[int, str]:
        """Execute a query returning number of affected rows."""
        ...

    async def fetch_one(
        self,
        query: str,
        params: tuple[object, ...] | dict[str, object] | None = None,
    ) -> Result[dict[str, object] | None, str]:
        """Fetch a single record as a dictionary."""
        ...

    async def fetch_all(
        self,
        query: str,
        params: tuple[object, ...] | dict[str, object] | None = None,
    ) -> Result[list[dict[str, object]], str]:
        """Fetch multiple records as dictionaries."""
        ...

    async def fetch_val(
        self,
        query: str,
        params: tuple[object, ...] | dict[str, object] | None = None,
    ) -> Result[object | None, str]:
        """Fetch a single scalar value from the first column of the first row."""
        ...
