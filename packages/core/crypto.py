"""Pure cryptographic primitives and transformation functions.

Layer 1: Core (deterministic functions, Result types, zero I/O, zero network/db side effects).
Provides:
- Argon2 password/token one-way hashing and timing-safe verification
- Key derivation from passwords (HKDF SHA-256) into 32-byte Fernet keys
- Fernet authenticated symmetric encryption and decryption
"""

import base64

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from packages.core.result import Result, err, ok

# Lazily initialized default argon2 hasher with secure parameters
_DEFAULT_HASHER = PasswordHasher()

# Default static public application salt for deterministic key derivation from STORE_PASSWORD
_DEFAULT_APP_SALT = b"public.store.salt.v1"


def hash_argon2(secret: str, hasher: PasswordHasher | None = None) -> str:
    """Hash a secret (password, API token, sensitive string) using Argon2id."""
    ph = hasher if hasher is not None else _DEFAULT_HASHER
    return ph.hash(secret)


def verify_argon2(secret: str, hash_str: str, hasher: PasswordHasher | None = None) -> bool:
    """Verify a secret against an Argon2id hash without raising exceptions."""
    ph = hasher if hasher is not None else _DEFAULT_HASHER
    try:
        return ph.verify(hash_str, secret)
    except VerifyMismatchError, Exception:
        return False


def derive_encryption_key(password: str | bytes, salt: bytes | None = None) -> str:
    """Derive a URL-safe base64-encoded 32-byte Fernet key from any password/passphrase using HKDF."""
    pw_bytes = password.encode("utf-8") if isinstance(password, str) else password
    effective_salt = salt or _DEFAULT_APP_SALT

    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=effective_salt,
        info=b"fernet-encryption-key",
    )
    derived_32_bytes = hkdf.derive(pw_bytes)
    return base64.urlsafe_b64encode(derived_32_bytes).decode("utf-8")


def generate_encryption_key() -> str:
    """Generate a fresh random URL-safe base64-encoded 32-byte Fernet key."""
    return Fernet.generate_key().decode("utf-8")


def encrypt_value(data: str | bytes, key: str | bytes) -> Result[str, str]:
    """Encrypt a string or bytes payload using Fernet symmetric encryption."""
    try:
        f = Fernet(key)
        payload = data.encode("utf-8") if isinstance(data, str) else data
        encrypted = f.encrypt(payload).decode("utf-8")
        return ok(encrypted)
    except Exception as e:
        return err(f"Encryption failed: {e}")


def decrypt_value(token: str | bytes, key: str | bytes) -> Result[str, str]:
    """Decrypt a Fernet token back to an unencrypted UTF-8 string."""
    try:
        f = Fernet(key)
        payload = token.encode("utf-8") if isinstance(token, str) else token
        decrypted = f.decrypt(payload).decode("utf-8")
        return ok(decrypted)
    except InvalidToken:
        return err("Invalid encryption token or mismatched encryption key")
    except Exception as e:
        return err(f"Decryption failed: {e}")
