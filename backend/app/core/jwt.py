"""JWT token generation, decoding, and validation infrastructure (Phases 028 & 030).
"""
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from app.core.config import settings
from app.core.logging import logger


def generate_jti() -> str:
    """Generate a unique JTI (JWT ID) for token uniqueness and replay protection."""
    return str(uuid.uuid4())


def hash_token(token: str) -> str:
    """Produce a secure SHA-256 hash of a raw token for safe database indexing."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Create a signed JWT access token.
    Claims: sub (user_id), type ('access'), iat, exp.
    Strictly avoids personal secrets, passwords, or permission lists in payload.
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: Dict[str, Any] = {
        "sub": str(subject),
        "type": "access",
        "jti": generate_jti(),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)

    encoded_jwt = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def create_refresh_token(
    subject: str,
    jti: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT refresh token.
    Claims: sub (user_id), type ('refresh'), jti, iat, exp.
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    token_jti = jti or generate_jti()
    payload: Dict[str, Any] = {
        "sub": str(subject),
        "type": "refresh",
        "jti": token_jti,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    encoded_jwt = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and verify a JWT signature and expiration.
    Raises jwt.ExpiredSignatureError or jwt.InvalidTokenError on failure.
    """
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
