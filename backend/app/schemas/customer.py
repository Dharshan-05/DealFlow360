import re
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


# ---------------------------------------------------------------------------
# Customer Tier Schemas (Phase 058)
# ---------------------------------------------------------------------------

class CustomerTierResponse(BaseModel):
    """Customer tier metadata representation."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    code: str
    description: Optional[str] = None
    discount_limit: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CustomerTierUpdate(BaseModel):
    """Schema for reassigning a customer's discount tier (Phase 058)."""
    tier_id: Optional[uuid.UUID] = Field(
        default=None,
        description="ID of the CustomerTier to assign, or null to unassign.",
    )


# ---------------------------------------------------------------------------
# Customer Purchase & Deal History Schemas (Phases 059 & 060)
# ---------------------------------------------------------------------------

class PurchaseHistoryCreate(BaseModel):
    """Schema for recording a purchase history entry (Phase 059)."""
    order_number: str = Field(..., min_length=1, max_length=50)
    purchase_date: datetime = Field(default_factory=datetime.utcnow)
    total_amount: Decimal = Field(..., ge=0)
    status: str = Field(default="COMPLETED", max_length=50)
    item_count: int = Field(default=1, ge=1)
    notes: Optional[str] = None


class PurchaseHistoryResponse(BaseModel):
    """Public representation of customer purchase history."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    customer_id: uuid.UUID
    order_number: str
    purchase_date: datetime
    total_amount: Decimal
    status: str
    item_count: int
    notes: Optional[str] = None
    created_at: datetime


class DealHistoryCreate(BaseModel):
    """Schema for recording a deal history entry (Phase 060)."""
    deal_code: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=200)
    deal_value: Decimal = Field(..., ge=0)
    status: str = Field(default="WON", max_length=50)
    sales_rep_name: Optional[str] = Field(default=None, max_length=100)
    closed_date: Optional[datetime] = None
    notes: Optional[str] = None


class DealHistoryResponse(BaseModel):
    """Public representation of customer deal history."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    customer_id: uuid.UUID
    deal_code: str
    title: str
    deal_value: Decimal
    status: str
    sales_rep_name: Optional[str] = None
    closed_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Customer CRUD Schemas (Phases 056 & 057)
# ---------------------------------------------------------------------------

class CustomerBase(BaseModel):
    customer_code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    email: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=50)
    address: Optional[str] = Field(default=None, max_length=255)
    city: Optional[str] = Field(default=None, max_length=100)
    state: Optional[str] = Field(default=None, max_length=100)
    country: Optional[str] = Field(default=None, max_length=100)
    postal_code: Optional[str] = Field(default=None, max_length=20)
    tier_id: Optional[uuid.UUID] = None
    is_active: bool = True

    @field_validator("email", mode="after")
    @classmethod
    def validate_email_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        normalized = v.lower().strip()
        if not EMAIL_REGEX.match(normalized):
            raise ValueError("Invalid email address format")
        return normalized

    @field_validator("customer_code", mode="after")
    @classmethod
    def normalize_code(cls, v: str) -> str:
        return v.strip().upper()


class CustomerCreate(CustomerBase):
    """Schema for creating a new customer account."""
    pass


class CustomerUpdate(BaseModel):
    """Schema for updating an existing customer account."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    email: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=50)
    address: Optional[str] = Field(default=None, max_length=255)
    city: Optional[str] = Field(default=None, max_length=100)
    state: Optional[str] = Field(default=None, max_length=100)
    country: Optional[str] = Field(default=None, max_length=100)
    postal_code: Optional[str] = Field(default=None, max_length=20)
    tier_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None

    @field_validator("email", mode="after")
    @classmethod
    def validate_email_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        normalized = v.lower().strip()
        if not EMAIL_REGEX.match(normalized):
            raise ValueError("Invalid email address format")
        return normalized


class CustomerResponse(BaseModel):
    """Detailed customer profile representation."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    customer_code: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    tier_id: Optional[uuid.UUID] = None
    tier: Optional[CustomerTierResponse] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CustomerListResponse(BaseModel):
    """Paginated customer query response."""
    items: List[CustomerResponse]
    total: int
    skip: int
    limit: int
