"""Valkey Store implementation with optional encryption at rest (Fernet) and hashing (Argon2).

Layer 3: Stores & State.
Coordinates between domain logic/crypto (Core) and Valkey transport (Clients).
"""

from typing import TYPE_CHECKING

from packages.core.crypto import (
    decrypt_value,
    derive_encryption_key,
    encrypt_value,
    hash_argon2,
    verify_argon2,
)
from packages.core.result import Result, err, ok

if TYPE_CHECKING:
    from packages.clients.valkey import ValkeyClient


class ValkeyStore:
    """Generic Key-Value store backed by Valkey.

    Supports:
    - Pass in either a raw 32-byte Fernet key or any passphrase/password (auto-derived via HKDF)
    - Optional automatic transparent encryption on get/set (auto_encrypt=True)
    - Explicit encrypted operations (get_decrypted, set_encrypted)
    - One-way password/token hashing & timing-safe verification (Argon2id)
    """

    def __init__(
        self,
        client: ValkeyClient,
        encryption_key: str | bytes | None = None,
        password: str | bytes | None = None,
        auto_encrypt: bool = False,
    ) -> None:
        self._client = client
        self._auto_encrypt = auto_encrypt

        # Resolve encryption key: either provided directly or derived from password
        if encryption_key is not None:
            self._encryption_key: str | bytes | None = encryption_key
        elif password is not None:
            self._encryption_key = derive_encryption_key(password)
        else:
            self._encryption_key = None

    # --------------------------------------------------------------------------
    # Raw / Plaintext Operations (transparently encrypted if auto_encrypt=True)
    # --------------------------------------------------------------------------
    async def get(self, key: str) -> Result[str | None, str]:
        """Retrieve a value by key (automatically decrypted if auto_encrypt=True)."""
        if self._auto_encrypt:
            return await self.get_decrypted(key)

        return await self._raw_get(key)

    async def set(
        self,
        key: str,
        value: str,
        ttl_seconds: int | None = None,
    ) -> Result[bool, str]:
        """Set a value by key with optional TTL (automatically encrypted if auto_encrypt=True)."""
        if self._auto_encrypt:
            return await self.set_encrypted(key=key, secret_value=value, ttl_seconds=ttl_seconds)

        return await self._raw_set(key=key, value=value, ttl_seconds=ttl_seconds)

    async def _raw_get(self, key: str) -> Result[str | None, str]:
        try:
            val = await self._client.client.get(key)
            if val is None:
                return ok(None)
            if isinstance(val, bytes):
                return ok(val.decode("utf-8"))
            return ok(str(val))
        except Exception as e:
            return err(f"Valkey get error: {e}")

    async def _raw_set(
        self,
        key: str,
        value: str,
        ttl_seconds: int | None = None,
    ) -> Result[bool, str]:
        try:
            res = await self._client.client.set(name=key, value=value, ex=ttl_seconds)
            return ok(bool(res))
        except Exception as e:
            return err(f"Valkey set error: {e}")

    async def delete(self, key: str) -> Result[bool, str]:
        """Delete a key."""
        try:
            res = await self._client.client.delete(key)
            return ok(bool(res > 0))
        except Exception as e:
            return err(f"Valkey delete error: {e}")

    async def exists(self, key: str) -> Result[bool, str]:
        """Check key existence."""
        try:
            res = await self._client.client.exists(key)
            return ok(bool(res > 0))
        except Exception as e:
            return err(f"Valkey exists error: {e}")

    async def touch(self, key: str, ttl_seconds: int) -> Result[bool, str]:
        """Update or refresh the time-to-live (TTL) expiration in seconds for an existing key."""
        try:
            res = await self._client.client.expire(name=key, time=ttl_seconds)
            return ok(bool(res))
        except Exception as e:
            return err(f"Valkey expire error: {e}")

    async def ttl(self, key: str) -> Result[int | None, str]:
        """Return remaining time-to-live in seconds (-1 if no expiry, None if key does not exist)."""
        try:
            res = await self._client.client.ttl(key)
            # Valkey/Redis returns -2 if the key does not exist, -1 if no TTL is set
            if res == -2:
                return ok(None)
            return ok(int(res))
        except Exception as e:
            return err(f"Valkey ttl error: {e}")

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
        """Encrypt value at rest using Fernet and store it."""
        enc_key = key_override or self._encryption_key
        if not enc_key:
            return err("Encryption key or password must be provided to set_encrypted")

        encrypt_res = encrypt_value(secret_value, enc_key)
        if not encrypt_res.ok or encrypt_res.data is None:
            return err(encrypt_res.error or "Failed to encrypt value")

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

        raw_res = await self._raw_get(key)
        if not raw_res.ok:
            return err(str(raw_res.error))
        if raw_res.data is None:
            return ok(None)

        decrypt_res = decrypt_value(raw_res.data, enc_key)
        if not decrypt_res.ok:
            return err(str(decrypt_res.error))

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
        """Hash a secret with Argon2id, store the hash, and return the hash string."""
        try:
            hash_str = hash_argon2(secret)
            set_res = await self._raw_set(key=key, value=hash_str, ttl_seconds=ttl_seconds)
            if not set_res.ok:
                return err(set_res.error or "Failed to store hash")
            return ok(hash_str)
        except Exception as e:
            return err(f"Argon2 hashing error: {e}")

    async def verify_hashed(self, key: str, candidate_secret: str) -> Result[bool, str]:
        """Verify candidate secret against stored Argon2id hash."""
        raw_res = await self._raw_get(key)
        if not raw_res.ok:
            return err(raw_res.error or "Failed to retrieve hash")
        if raw_res.data is None:
            return ok(False)

        matches = verify_argon2(candidate_secret, raw_res.data)
        return ok(matches)
