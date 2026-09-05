"""Pydantic schemas for standard API contracts"""
from app.schemas.auth import (
    LogoutRequest,
    TokenRefreshRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.schemas.customer import (
    CustomerCreate,
    CustomerListResponse,
    CustomerResponse,
    CustomerTierResponse,
    CustomerTierUpdate,
    CustomerUpdate,
    DealHistoryCreate,
    DealHistoryResponse,
    PurchaseHistoryCreate,
    PurchaseHistoryResponse,
)
from app.schemas.response import (
    ApiErrorDetail,
    ApiErrorResponse,
    ApiResponse,
    DatabaseHealth,
    HealthData,
)

__all__ = [
    "ApiResponse",
    "ApiErrorDetail",
    "ApiErrorResponse",
    "DatabaseHealth",
    "HealthData",
    "UserRegisterRequest",
    "UserLoginRequest",
    "TokenRefreshRequest",
    "LogoutRequest",
    "UserResponse",
    "TokenResponse",
    "CustomerCreate",
    "CustomerUpdate",
    "CustomerResponse",
    "CustomerListResponse",
    "CustomerTierResponse",
    "CustomerTierUpdate",
    "PurchaseHistoryCreate",
    "PurchaseHistoryResponse",
    "DealHistoryCreate",
    "DealHistoryResponse",
]
