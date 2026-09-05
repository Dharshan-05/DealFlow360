"""Password hashing and verification utilities (Phase 029).
Uses Argon2id via argon2-cffi.
"""
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

from app.core.logging import logger

# Initialize Argon2id password hasher with secure production parameters
_ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,  # 64 MB
    parallelism=4,
    hash_len=32,
    salt_len=16,
)


def get_password_hash(password: str) -> str:
    """Hash a plaintext password using Argon2id.
    Never logs or persists plaintext password.
    """
    return _ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against an Argon2id hash in constant time."""
    try:
        return _ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False
    except Exception as exc:
        logger.warning(f"Unexpected error during password verification: {type(exc).__name__}")
        return False
