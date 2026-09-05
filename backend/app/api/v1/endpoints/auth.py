"""Authentication endpoints (Phases 026, 027, 028, 030).
Endpoints:
- POST /api/v1/auth/register (Phase 026)
- POST /api/v1/auth/login (Phase 027)
- POST /api/v1/auth/refresh (Phase 030)
- GET  /api/v1/auth/me (Phase 028: Protected authenticated resource)
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    TokenRefreshRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.schemas.response import ApiResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


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
        data=UserResponse.model_validate(user),
        message="User registered successfully",
    )


@router.post(
    "/login",
    response_model=ApiResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="Authenticate user login",
    description="Validates credentials and returns JWT access token and refresh token.",
)
def login(
    request: UserLoginRequest,
    db: Session = Depends(get_db),
) -> ApiResponse[TokenResponse]:
    _, token_response = AuthService.login_user(db, request)
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
    description="Rotates refresh token and issues a new access token.",
)
def refresh(
    request: TokenRefreshRequest,
    db: Session = Depends(get_db),
) -> ApiResponse[TokenResponse]:
    token_response = AuthService.refresh_tokens(db, request)
    return ApiResponse(
        success=True,
        data=token_response,
        message="Token refreshed successfully",
    )


@router.get(
    "/me",
    response_model=ApiResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Get current user context",
    description="Protected resource demonstrating JWT authentication dependency.",
)
def get_me(
    current_user: User = Depends(get_current_user),
) -> ApiResponse[UserResponse]:
    return ApiResponse(
        success=True,
        data=UserResponse.model_validate(current_user),
        message="Current user profile retrieved successfully",
    )
