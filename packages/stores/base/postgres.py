"""PostgreSQL Store implementations.

Layer 3: Stores & State.
Coordinates between domain logic/crypto (Core) and Postgres transport (Clients).

Contains:
- PostgresStore: Pure relational SQL query store.
- PostgresKVStore: Generic SQLModel-backed key-value / secret store accepting any KV model schema.
"""

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from sqlmodel import Session, SQLModel

from packages.core.crypto import (
    decrypt_value,
    derive_encryption_key,
    encrypt_value,
    hash_argon2,
    verify_argon2,
)
from packages.core.result import Result, err, ok

if TYPE_CHECKING:
    from packages.clients.postgres import PostgresClient


class PostgresStore:
    """Relational SQL query store backed by PostgreSQL."""

    def __init__(self, client: PostgresClient) -> None:
        self._client = client

    # --------------------------------------------------------------------------
    # Raw SQL Operations
    # --------------------------------------------------------------------------
    async def execute(
        self,
        query: str,
        params: tuple[object, ...] | dict[str, object] | None = None,
    ) -> Result[int, str]:
        """Execute a query and return affected row count."""
        try:
            async with self._client.connection() as conn, conn.cursor() as cur:
                await cur.execute(query, params)
                return ok(cur.rowcount)
        except Exception as e:
            return err(f"Postgres execution error: {e}")

    async def fetch_one(
        self,
        query: str,
        params: tuple[object, ...] | dict[str, object] | None = None,
    ) -> Result[dict[str, Any] | None, str]:
        """Fetch a single record as a dictionary."""
        try:
            async with self._client.connection() as conn, conn.cursor() as cur:
                await cur.execute(query, params)
                res = await cur.fetchone()
                return ok(dict(res) if res is not None else None)
        except Exception as e:
            return err(f"Postgres fetch_one error: {e}")

    async def fetch_all(
        self,
        query: str,
        params: tuple[object, ...] | dict[str, object] | None = None,
    ) -> Result[list[dict[str, Any]], str]:
        """Fetch all records matching query."""
        try:
            async with self._client.connection() as conn, conn.cursor() as cur:
                await cur.execute(query, params)
                rows = await cur.fetchall()
                return ok([dict(row) for row in rows])
        except Exception as e:
            return err(f"Postgres fetch_all error: {e}")

    async def fetch_val(
        self,
        query: str,
        params: tuple[object, ...] | dict[str, object] | None = None,
    ) -> Result[object | None, str]:
        """Fetch a single scalar value from the first column of the first row."""
        try:
            async with self._client.connection() as conn, conn.cursor() as cur:
                await cur.execute(query, params)
                row = await cur.fetchone()
                if row is None:
                    return ok(None)
                first_val = next(iter(row.values())) if row else None
                return ok(first_val)
        except Exception as e:
            return err(f"Postgres fetch_val error: {e}")


class PostgresKVStore[M: SQLModel]:
    """Generic Key-Value & Secret store accepting any SQLModel KV model class.

    Supports:
    - Standard get/set/delete/exists/touch/ttl operations using SQLModel
    - Optional automatic transparent Fernet encryption (auto_encrypt=True)
    - Pass in either a raw 32-byte Fernet key or passphrase/password (auto-derived via HKDF)
    - Argon2id password/token hashing via set_hashed / verify_hashed
    """

    def __init__(
        self,
        client: PostgresClient,
        model_cls: type[M],
        encryption_key: str | bytes | None = None,
        password: str | bytes | None = None,
        auto_encrypt: bool = False,
    ) -> None:
        self._client = client
        self._model_cls = model_cls
        self._auto_encrypt = auto_encrypt

        # Resolve encryption key: either provided directly or derived from password
        if encryption_key is not None:
            self._encryption_key: str | bytes | None = encryption_key
        elif password is not None:
            self._encryption_key = derive_encryption_key(password)
        else:
            self._encryption_key = None

    async def init_table(self) -> Result[bool, str]:
        """Ensure the target model database table exists via SQLModel metadata."""
        try:
            async with self._client.connection() as conn:
                with Session(conn) as session:
                    self._model_cls.metadata.create_all(session.get_bind())
            return ok(True)
        except Exception as e:
            return err(f"Failed to init KV table via SQLModel: {e}")

    # --------------------------------------------------------------------------
    # Key-Value Operations
    # --------------------------------------------------------------------------
    async def get(self, key: str) -> Result[str | None, str]:
        """Retrieve a value by key (automatically decrypted if auto_encrypt=True)."""
        if self._auto_encrypt:
            return await self.get_decrypted(key=key)
        return await self._raw_get(key=key)

    async def set(
        self,
        key: str,
        value: str,
        ttl_seconds: int | None = None,
    ) -> Result[bool, str]:
        """Upsert a key-value pair (automatically encrypted if auto_encrypt=True)."""
        if self._auto_encrypt:
            return await self.set_encrypted(key=key, secret_value=value, ttl_seconds=ttl_seconds)
        return await self._raw_set(key=key, value=value, ttl_seconds=ttl_seconds)

    async def delete(self, key: str) -> Result[bool, str]:
        """Delete a key."""
        try:
            async with self._client.connection() as conn:
                with Session(conn) as session:
                    item = session.get(self._model_cls, key)
                    if item:
                        session.delete(item)
                        session.commit()
            return ok(True)
        except Exception as e:
            return err(f"PostgresKVStore delete error: {e}")

    async def exists(self, key: str) -> Result[bool, str]:
        """Check if a non-expired key exists."""
        try:
            async with self._client.connection() as conn:
                with Session(conn) as session:
                    item = session.get(self._model_cls, key)
                    if not item:
                        return ok(False)
                    expires_at = getattr(item, "expires_at", None)
                    if expires_at and datetime.now(UTC) > expires_at:
                        return ok(False)
            return ok(True)
        except Exception as e:
            return err(f"PostgresKVStore exists error: {e}")

    async def touch(self, key: str, ttl_seconds: int) -> Result[bool, str]:
        """Refresh TTL expiration in seconds for an existing key."""
        try:
            async with self._client.connection() as conn:
                with Session(conn) as session:
                    item = session.get(self._model_cls, key)
                    if not item:
                        return ok(False)
                    now = datetime.now(UTC)
                    expires_at = getattr(item, "expires_at", None)
                    if expires_at and now > expires_at:
                        return ok(False)
                    item.ttl_seconds = ttl_seconds
                    item.expires_at = now + timedelta(seconds=ttl_seconds)
                    item.updated_at = now
                    session.add(item)
                    session.commit()
            return ok(True)
        except Exception as e:
            return err(f"PostgresKVStore touch error: {e}")

    async def ttl(self, key: str) -> Result[int | None, str]:
        """Return remaining time-to-live in seconds (-1 if no expiry, None if key does not exist)."""
        try:
            async with self._client.connection() as conn:
                with Session(conn) as session:
                    item = session.get(self._model_cls, key)
                    if not item:
                        return ok(None)
                    expires_at = getattr(item, "expires_at", None)
                    if not expires_at:
                        return ok(-1)
                    now = datetime.now(UTC)
                    remaining = int((expires_at - now).total_seconds())
                    return ok(max(0, remaining) if remaining >= 0 else None)
        except Exception as e:
            return err(f"PostgresKVStore ttl error: {e}")

    async def _raw_set(
        self,
        key: str,
        value: str,
        ttl_seconds: int | None = None,
    ) -> Result[bool, str]:
        try:
            async with self._client.connection() as conn:
                with Session(conn) as session:
                    item = session.get(self._model_cls, key)
                    now = datetime.now(UTC)
                    expires_at = now + timedelta(seconds=ttl_seconds) if ttl_seconds else None

                    if item:
                        item.value = value
                        if hasattr(item, "updated_at"):
                            item.updated_at = now
                        if hasattr(item, "ttl_seconds"):
                            item.ttl_seconds = ttl_seconds
                        if hasattr(item, "expires_at"):
                            item.expires_at = expires_at
                    else:
                        kwargs: dict[str, Any] = {"key": key, "value": value, "updated_at": now}
                        if hasattr(self._model_cls, "created_at"):
                            kwargs["created_at"] = now
                        if hasattr(self._model_cls, "ttl_seconds"):
                            kwargs["ttl_seconds"] = ttl_seconds
                        if hasattr(self._model_cls, "expires_at"):
                            kwargs["expires_at"] = expires_at
                        item = self._model_cls(**kwargs)

                    session.add(item)
                    session.commit()
            return ok(True)
        except Exception as e:
            return err(f"PostgresKVStore set error: {e}")

    async def _raw_get(self, key: str) -> Result[str | None, str]:
        try:
            async with self._client.connection() as conn:
                with Session(conn) as session:
                    item = session.get(self._model_cls, key)
                    if not item:
                        return ok(None)
                    expires_at = getattr(item, "expires_at", None)
                    if expires_at and datetime.now(UTC) > expires_at:
                        return ok(None)
            val = getattr(item, "value", None) if item else None
            return ok(str(val) if val is not None else None)
        except Exception as e:
            return err(f"PostgresKVStore get error: {e}")

    # --------------------------------------------------------------------------
    # Encrypted At Rest Operations (Fernet)
    # --------------------------------------------------------------------------
    async def set_encrypted(
        self,
        key: str,
        secret_value: str,
        ttl_seconds: int | None = None,
        key_override: str | bytes | None = None,
    ) -> Result[bool, str]:
        """Encrypt secret value at rest with Fernet and upsert into database."""
        enc_key = key_override or self._encryption_key
        if not enc_key:
            return err("Encryption key or password must be provided to set_encrypted")

        encrypt_res = encrypt_value(secret_value, enc_key)
        if not encrypt_res.ok or encrypt_res.data is None:
            return err(encrypt_res.error or "Encryption failed")

        return await self._raw_set(key=key, value=encrypt_res.data, ttl_seconds=ttl_seconds)

    async def get_decrypted(
        self,
        key: str,
        key_override: str | bytes | None = None,
    ) -> Result[str | None, str]:
        """Retrieve and decrypt an encrypted-at-rest value."""
        enc_key = key_override or self._encryption_key
        if not enc_key:
            return err("Encryption key or password must be provided to get_decrypted")

        raw_res = await self._raw_get(key=key)
        if not raw_res.ok:
            return err(raw_res.error or "Failed to fetch encrypted value")
        if raw_res.data is None:
            return ok(None)

        decrypt_res = decrypt_value(raw_res.data, enc_key)
        if not decrypt_res.ok:
            return err(decrypt_res.error or "Decryption failed")

        return ok(decrypt_res.data)

    # --------------------------------------------------------------------------
    # Hashing Operations (Argon2)
    # --------------------------------------------------------------------------
    async def set_hashed(
        self,
        key: str,
        secret: str,
        ttl_seconds: int | None = None,
    ) -> Result[str, str]:
        """Hash a secret with Argon2id, store the hash, and return hash."""
        try:
            hash_str = hash_argon2(secret)
            set_res = await self._raw_set(key=key, value=hash_str, ttl_seconds=ttl_seconds)
            if not set_res.ok:
                return err(set_res.error or "Failed to store hash")
            return ok(hash_str)
        except Exception as e:
            return err(f"Argon2 hashing error: {e}")

    async def verify_hashed(
        self,
        key: str,
        candidate_secret: str,
    ) -> Result[bool, str]:
        """Verify candidate secret against stored Argon2id hash."""
        raw_res = await self._raw_get(key=key)
        if not raw_res.ok:
            return err(raw_res.error or "Failed to retrieve hash")
        if raw_res.data is None:
            return ok(False)

        matches = verify_argon2(candidate_secret, raw_res.data)
        return ok(matches)
