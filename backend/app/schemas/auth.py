import re
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class UserRegisterRequest(BaseModel):
    """Registration request schema with normalization and policy validation (Phase 026)."""
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=8, max_length=128, description="Minimum 8 characters")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    company_id: Optional[uuid.UUID] = None

    @field_validator("email", mode="after")
    @classmethod
    def validate_and_normalize_email(cls, v: str) -> str:
        normalized = v.lower().strip()
        if not EMAIL_REGEX.match(normalized):
            raise ValueError("Invalid email address format")
        return normalized

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        v_stripped = v.strip()
        if len(v_stripped) < 8:
            raise ValueError("Password must be at least 8 characters long and cannot consist only of whitespace")
        return v


class UserLoginRequest(BaseModel):
    """Login credential request schema (Phase 027)."""
    email: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1, max_length=128)

    @field_validator("email", mode="after")
    @classmethod
    def validate_and_normalize_email(cls, v: str) -> str:
        normalized = v.lower().strip()
        if not EMAIL_REGEX.match(normalized):
            raise ValueError("Invalid email address format")
        return normalized


class TokenRefreshRequest(BaseModel):
    """Refresh token request schema (Phase 030).
    Optional in body when provided via HttpOnly cookie.
    """
    refresh_token: Optional[str] = Field(default=None)


class LogoutRequest(BaseModel):
    """Logout request schema (Phase 031).
    Optional in body when provided via HttpOnly cookie.
    """
    refresh_token: Optional[str] = Field(default=None)


class UserResponse(BaseModel):
    """Safe public user representation.
    Strictly excludes password_hash and internal security secrets.
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    is_active: bool
    company_id: Optional[uuid.UUID] = None
    roles: List[str] = Field(default_factory=list, description="Assigned role names")
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseModel):
    """Authentication response returning access and refresh tokens."""
    access_token: str
    refresh_token: Optional[str] = Field(default=None, description="Refresh token value (also transported via HttpOnly cookie)")
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token expiration in seconds")
