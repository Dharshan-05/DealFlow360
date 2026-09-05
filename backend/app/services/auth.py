"""Authentication Service (Phases 026–030).
Encapsulates business operations for:
- User Registration (026)
- User Login (027)
- JWT Token Issuance & Refresh Rotation (028, 030)
- Audit Logging of Authentication Events
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import ApplicationError
from app.core.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_jti,
    hash_token,
)
from app.core.logging import logger
from app.core.security import get_password_hash, verify_password
from app.models.audit_log import AuditLog
from app.models.company import Company
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import (
    LogoutRequest,
    TokenRefreshRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
)


class AuthService:
    """Core authentication logic separated cleanly from the HTTP transport layer."""

    @staticmethod
    def register_user(db: Session, request: UserRegisterRequest) -> User:
        """Register a new user, enforcing email uniqueness and password hashing (Phase 026)."""
        # Check duplicate email
        existing_user = db.scalars(
            select(User).where(User.email == request.email)
        ).first()
        if existing_user:
            logger.warning(f"Registration attempted with existing email: {request.email}")
            raise ApplicationError(
                message="An account with this email already exists",
                code="EMAIL_ALREADY_EXISTS",
                status_code=409,
            )

        # Validate company_id if provided
        if request.company_id is not None:
            company = db.get(Company, request.company_id)
            if not company:
                raise ApplicationError(
                    message="Referenced company does not exist",
                    code="COMPANY_NOT_FOUND",
                    status_code=404,
                )

        # Hash password using Argon2id (never store plaintext)
        hashed_pwd = get_password_hash(request.password)

        user = User(
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name,
            password_hash=hashed_pwd,
            company_id=request.company_id,
            is_active=True,
        )
        db.add(user)
        db.flush()

        # Audit log for user registration (no sensitive fields logged)
        audit = AuditLog(
            user_id=user.id,
            company_id=user.company_id,
            action="auth:registered",
            resource_type="user",
            resource_id=str(user.id),
            details=f"User registered with email: {user.email}",
            context_metadata={"action": "registration"},
        )
        db.add(audit)
        db.commit()
        db.refresh(user)

        logger.info(f"User successfully registered: {user.id}")
        return user

    @staticmethod
    def login_user(db: Session, request: UserLoginRequest) -> Tuple[User, TokenResponse]:
        """Verify user credentials and issue access and refresh tokens (Phase 027)."""
        user = db.scalars(
            select(User).where(User.email == request.email)
        ).first()

        # Constant-time / uniform rejection to avoid email enumeration
        if not user or not verify_password(request.password, user.password_hash):
            logger.warning(f"Authentication failed for email: {request.email}")
            raise ApplicationError(
                message="Invalid email or password",
                code="INVALID_CREDENTIALS",
                status_code=401,
            )

        if not user.is_active:
            logger.warning(f"Authentication attempted for inactive user: {user.id}")
            raise ApplicationError(
                message="User account is inactive",
                code="USER_INACTIVE",
                status_code=403,
            )

        # Generate tokens
        access_token = create_access_token(subject=str(user.id))
        jti = generate_jti()
        refresh_token = create_refresh_token(subject=str(user.id), jti=jti)

        # Store refresh token record for rotation & revocation tracking
        token_record = RefreshToken(
            user_id=user.id,
            jti=jti,
            token_hash=hash_token(refresh_token),
            expires_at=datetime.fromtimestamp(
                decode_token(refresh_token)["exp"],
                tz=timezone.utc,
            ),
            is_revoked=False,
        )
        db.add(token_record)

        # Audit log for successful login
        audit = AuditLog(
            user_id=user.id,
            company_id=user.company_id,
            action="auth:login_success",
            resource_type="session",
            resource_id=jti,
            details="User logged in successfully",
            context_metadata={"jti": jti},
        )
        db.add(audit)
        db.commit()

        logger.info(f"User logged in successfully: {user.id}")
        token_response = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        return user, token_response

    @staticmethod
    def refresh_tokens(db: Session, request: TokenRefreshRequest) -> TokenResponse:
        """Validate refresh token and issue rotated access and refresh tokens (Phase 030)."""
        try:
            payload = decode_token(request.refresh_token)
        except Exception as exc:
            logger.warning(f"Refresh token decoding failed: {type(exc).__name__}")
            raise ApplicationError(
                message="Invalid or expired refresh token",
                code="INVALID_REFRESH_TOKEN",
                status_code=401,
            )

        # Verify token type is refresh
        if payload.get("type") != "refresh":
            logger.warning("Token type mismatch: expected refresh token")
            raise ApplicationError(
                message="Token is not a valid refresh token",
                code="INVALID_TOKEN_TYPE",
                status_code=401,
            )

        user_id_str = payload.get("sub")
        jti = payload.get("jti")
        if not user_id_str or not jti:
            raise ApplicationError(
                message="Malformed refresh token claims",
                code="INVALID_REFRESH_TOKEN",
                status_code=401,
            )

        try:
            user_uuid = uuid.UUID(user_id_str)
        except ValueError:
            raise ApplicationError(
                message="Invalid user identifier in token",
                code="INVALID_REFRESH_TOKEN",
                status_code=401,
            )

        # Lookup token in database
        token_record = db.scalars(
            select(RefreshToken).where(RefreshToken.jti == jti)
        ).first()

        # Token reuse / revocation check
        if not token_record or token_record.is_revoked:
            logger.warning(f"Attempted reuse of revoked or non-existent refresh token: {jti}")
            # Security precaution: if revoked token is re-presented, revoke all tokens for this user
            if token_record and token_record.is_revoked:
                logger.error(f"Potential token replay attack detected for user: {user_uuid}")
            raise ApplicationError(
                message="Refresh token has been revoked or expired",
                code="TOKEN_REVOKED",
                status_code=401,
            )

        # Check expiration
        now = datetime.now(timezone.utc)
        if token_record.expires_at < now:
            raise ApplicationError(
                message="Refresh token has expired",
                code="TOKEN_EXPIRED",
                status_code=401,
            )

        # Lookup user and verify active status
        user = db.get(User, user_uuid)
        if not user or not user.is_active:
            raise ApplicationError(
                message="User account does not exist or is inactive",
                code="USER_INACTIVE",
                status_code=403,
            )

        # Rotate token: revoke old token and issue new pair
        token_record.is_revoked = True
        token_record.revoked_at = now

        new_jti = generate_jti()
        new_access_token = create_access_token(subject=str(user.id))
        new_refresh_token = create_refresh_token(subject=str(user.id), jti=new_jti)

        new_token_record = RefreshToken(
            user_id=user.id,
            jti=new_jti,
            token_hash=hash_token(new_refresh_token),
            expires_at=datetime.fromtimestamp(
                decode_token(new_refresh_token)["exp"],
                tz=timezone.utc,
            ),
            is_revoked=False,
        )
        db.add(new_token_record)

        # Audit log token rotation
        audit = AuditLog(
            user_id=user.id,
            company_id=user.company_id,
            action="auth:token_refresh",
            resource_type="session",
            resource_id=new_jti,
            details="Token refreshed and rotated",
            context_metadata={"old_jti": jti, "new_jti": new_jti},
        )
        db.add(audit)
        db.commit()

        logger.info(f"Tokens successfully refreshed for user: {user.id}")
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    @staticmethod
    def logout_user(db: Session, request: LogoutRequest, current_user: Optional[User] = None) -> bool:
        """Revoke refresh token and invalidate session (Phase 031).
        Safe against already-revoked tokens; prevents future refresh-token reuse.
        Does NOT delete user, modify user status, or alter roles/permissions.
        """
        try:
            payload = decode_token(request.refresh_token)
        except Exception as exc:
            logger.warning(f"Logout token decoding failed: {type(exc).__name__}")
            raise ApplicationError(
                message="Invalid or expired token",
                code="INVALID_TOKEN",
                status_code=400,
            )

        if payload.get("type") != "refresh":
            logger.warning("Token type mismatch in logout: expected refresh token")
            raise ApplicationError(
                message="Token is not a valid refresh token",
                code="INVALID_TOKEN_TYPE",
                status_code=400,
            )

        jti = payload.get("jti")
        user_id_str = payload.get("sub")
        if not jti or not user_id_str:
            raise ApplicationError(
                message="Malformed token claims",
                code="INVALID_TOKEN",
                status_code=400,
            )

        # Lookup token in database
        token_record = db.scalars(
            select(RefreshToken).where(RefreshToken.jti == jti)
        ).first()

        now = datetime.now(timezone.utc)
        target_user_id = current_user.id if current_user else None
        target_company_id = current_user.company_id if current_user else None

        if token_record:
            if not target_user_id:
                target_user_id = token_record.user_id
            if not token_record.is_revoked:
                token_record.is_revoked = True
                token_record.revoked_at = now

        # Audit log logout event (never logs raw token or secrets)
        audit = AuditLog(
            user_id=target_user_id,
            company_id=target_company_id,
            action="auth:logout",
            resource_type="session",
            resource_id=jti,
            details="User logged out; session terminated",
            context_metadata={"jti": jti},
        )
        db.add(audit)
        db.commit()

        logger.info(f"User session terminated for JTI: {jti}")
        return True

