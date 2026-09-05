"""Authentication dependency providing get_current_user context (Phase 028).
Validates Bearer token, signature, expiration, and active account status.
Strictly authentication only — NO RBAC, role checks, or permission middleware.
"""
import uuid
from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.jwt import decode_token
from app.core.logging import logger
from app.db.session import get_db
from app.models.user import User
from app.services.rbac import RBACService


def get_current_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency extracting and verifying the authenticated User from the Bearer token.
    Raises standardized HTTP 401/403 errors on failure.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization scheme must be Bearer",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]
    try:
        payload = decode_token(token)
    except Exception as exc:
        logger.warning(f"Access token validation failed: {type(exc).__name__}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        logger.warning("Token type mismatch in get_current_user: expected access token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type: access token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject identifier",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user identifier in token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.get(User, user_uuid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


def require_permission(permission_name: str):
    """FastAPI dependency factory enforcing that the authenticated user possesses the specified permission (Phase 039).
    Verifies that the user is active and has an active role granting this permission.
    """
    def _dependency(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )
        if not RBACService.user_has_permission(current_user, permission_name, only_active=True):
            logger.warning(
                f"Permission denied: user {current_user.id} ({current_user.email}) lacks permission '{permission_name}'"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: missing required permission '{permission_name}'",
            )
        return current_user

    return _dependency


def require_role(role_name: str):
    """FastAPI dependency factory enforcing that the authenticated user possesses the specified role (Phase 039).
    Verifies that the user is active and has the specified active role.
    """
    def _dependency(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )
        if not RBACService.has_role(current_user, role_name, check_active=True):
            logger.warning(
                f"Role check failed: user {current_user.id} ({current_user.email}) lacks required role '{role_name}'"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: missing required role '{role_name}'",
            )
        return current_user

    return _dependency
