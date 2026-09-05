from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Standard success envelope for API responses."""
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None


class ApiErrorDetail(BaseModel):
    """Detailed error object matching client expectations."""
    code: str
    message: str
    details: Optional[Any] = None


class ApiErrorResponse(BaseModel):
    """Standard failure envelope for API error responses."""
    success: bool = False
    error: ApiErrorDetail


class DatabaseHealth(BaseModel):
    """Infrastructure-level database status, distinct from application status."""
    connected: bool
    dialect: str = "postgresql"


class HealthData(BaseModel):
    """Payload schema for health checks."""
    status: str
    service: str
    phase: str
    version: str
    environment: str
    database: Optional[DatabaseHealth] = None
