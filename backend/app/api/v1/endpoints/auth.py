"""Authentication endpoints (Phases 026, 027, 028, 030).
Endpoints:
- POST /api/v1/auth/register (Phase 026)
- POST /api/v1/auth/login (Phase 027)
- POST /api/v1/auth/refresh (Phase 030)
- GET  /api/v1/auth/me (Phase 028: Protected authenticated resource)
"""
from typing import Optional
from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    LogoutRequest,
    TokenRefreshRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.schemas.response import ApiResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])

REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_PATH = f"{settings.API_V1_STR}/auth"


def _serialize_user(user: User) -> UserResponse:
    """Serialize User model into public UserResponse, populating assigned role names."""
    role_names = [role.name for role in user.roles if role.is_active]
    return UserResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        company_id=user.company_id,
        roles=role_names,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.post(
    "/register",
    response_model=ApiResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Registers a new user account with hashed password and returns safe public user profile.",
)
def register(
    request: UserRegisterRequest,
    db: Session = Depends(get_db),
) -> ApiResponse[UserResponse]:
    user = AuthService.register_user(db, request)
    return ApiResponse(
        success=True,
        data=_serialize_user(user),
        message="User registered successfully",
    )


@router.post(
    "/login",
    response_model=ApiResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="Authenticate user login",
    description="Validates credentials, sets HttpOnly refresh cookie, and returns JWT access token.",
)
def login(
    request: UserLoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> ApiResponse[TokenResponse]:
    _, token_response = AuthService.login_user(db, request)
    if token_response.refresh_token:
        response.set_cookie(
            key=REFRESH_COOKIE_NAME,
            value=token_response.refresh_token,
            httponly=True,
            secure=(settings.ENVIRONMENT == "production"),
            samesite="lax",
            path=REFRESH_COOKIE_PATH,
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        )
    return ApiResponse(
        success=True,
        data=token_response,
        message="Authentication successful",
    )


@router.post(
    "/refresh",
    response_model=ApiResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Rotates refresh token and issues a new access token via HttpOnly cookie or request body.",
)
def refresh(
    raw_request: Request,
    response: Response,
    request: Optional[TokenRefreshRequest] = Body(None),
    db: Session = Depends(get_db),
) -> ApiResponse[TokenResponse]:
    token_val = (request.refresh_token if request and request.refresh_token else None) or raw_request.cookies.get(REFRESH_COOKIE_NAME)
    if not token_val:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing from request body or cookie",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token_response = AuthService.refresh_tokens(db, TokenRefreshRequest(refresh_token=token_val))
    if token_response.refresh_token:
        response.set_cookie(
            key=REFRESH_COOKIE_NAME,
            value=token_response.refresh_token,
            httponly=True,
            secure=(settings.ENVIRONMENT == "production"),
            samesite="lax",
            path=REFRESH_COOKIE_PATH,
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        )
    return ApiResponse(
        success=True,
        data=token_response,
        message="Token refreshed successfully",
    )


@router.post(
    "/logout",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Logout user",
    description="Revokes the refresh token and clears the HttpOnly cookie (Phase 031).",
)
def logout(
    raw_request: Request,
    response: Response,
    request: Optional[LogoutRequest] = Body(None),
    db: Session = Depends(get_db),
) -> ApiResponse[dict]:
    token_val = (request.refresh_token if request and request.refresh_token else None) or raw_request.cookies.get(REFRESH_COOKIE_NAME)
    if token_val:
        AuthService.logout_user(db, LogoutRequest(refresh_token=token_val))

    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path=REFRESH_COOKIE_PATH,
        httponly=True,
        secure=(settings.ENVIRONMENT == "production"),
        samesite="lax",
    )
    return ApiResponse(
        success=True,
        data={"logged_out": True},
        message="Successfully logged out",
    )


@router.get(
    "/me",
    response_model=ApiResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Get current user context",
    description="Protected resource demonstrating JWT authentication dependency with assigned roles.",
)
def get_me(
    current_user: User = Depends(get_current_user),
) -> ApiResponse[UserResponse]:
    return ApiResponse(
        success=True,
        data=_serialize_user(current_user),
        message="Current user profile retrieved successfully",
    )

