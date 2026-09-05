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
# Phase 061: Customer Discount History Schemas
# ---------------------------------------------------------------------------

class DiscountHistoryCreate(BaseModel):
    """Schema for recording a customer discount history entry (Phase 061)."""
    discount_code: str = Field(..., min_length=1, max_length=50)
    discount_percentage: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    discount_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    deal_reference: Optional[str] = Field(default=None, max_length=100)
    reason: Optional[str] = None
    applied_at: datetime = Field(default_factory=datetime.utcnow)


class DiscountHistoryResponse(BaseModel):
    """Public representation of customer discount history."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    customer_id: uuid.UUID
    discount_code: str
    discount_percentage: Decimal
    discount_amount: Decimal
    deal_reference: Optional[str] = None
    reason: Optional[str] = None
    applied_at: datetime
    created_at: datetime


# ---------------------------------------------------------------------------
# Phase 062: Customer Payment History Schemas
# ---------------------------------------------------------------------------

class PaymentHistoryCreate(BaseModel):
    """Schema for recording a customer payment transaction (Phase 062)."""
    payment_reference: str = Field(..., min_length=1, max_length=100)
    amount: Decimal = Field(..., ge=0)
    status: str = Field(default="COMPLETED", max_length=50)
    payment_method: Optional[str] = Field(default=None, max_length=50)
    transaction_reference: Optional[str] = Field(default=None, max_length=100)
    payment_date: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None


class PaymentHistoryResponse(BaseModel):
    """Public representation of customer payment history."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    customer_id: uuid.UUID
    payment_reference: str
    amount: Decimal
    status: str
    payment_method: Optional[str] = None
    transaction_reference: Optional[str] = None
    payment_date: datetime
    notes: Optional[str] = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Phase 063: Customer LTV Schemas
# ---------------------------------------------------------------------------

class CustomerLtvResponse(BaseModel):
    """Customer Lifetime Value calculation result (Phase 063)."""
    customer_id: uuid.UUID
    ltv_amount: Decimal
    total_purchases_count: int
    total_purchases_amount: Decimal
    total_settled_payments_amount: Decimal
    average_order_value: Decimal
    first_purchase_date: Optional[datetime] = None
    latest_purchase_date: Optional[datetime] = None
    calculated_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Phase 064: Customer Discount Sensitivity Schemas
# ---------------------------------------------------------------------------

class DiscountSensitivityResponse(BaseModel):
    """Customer discount sensitivity analysis result (Phase 064)."""
    customer_id: uuid.UUID
    score: int = Field(..., ge=0, le=100, description="0=Least sensitive, 100=Most sensitive")
    level: str = Field(..., description="LOW, MODERATE, HIGH, or INSUFFICIENT_DATA")
    average_discount_percent: Decimal
    discount_frequency_percent: Decimal
    total_orders_evaluated: int
    discounted_orders_count: int
    explanation: str
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Phase 065: Customer Risk Profile Schemas
# ---------------------------------------------------------------------------

class CustomerRiskProfileResponse(BaseModel):
    """Customer-level risk profiling result (Phase 065)."""
    customer_id: uuid.UUID
    score: int = Field(..., ge=0, le=100, description="0=Lowest risk, 100=Highest risk")
    risk_level: str = Field(..., description="LOW, MEDIUM, or HIGH")
    failed_payment_ratio: Decimal
    payment_reliability_score: int
    account_status: str
    primary_factors: List[str]
    explanation: str
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Customer Financial Intelligence Combined Envelope (Phases 063-065)
# ---------------------------------------------------------------------------

class CustomerFinancialIntelligenceResponse(BaseModel):
    """Consolidated financial intelligence indicators for customer profile."""
    customer_id: uuid.UUID
    ltv: CustomerLtvResponse
    discount_sensitivity: DiscountSensitivityResponse
    risk_profile: CustomerRiskProfileResponse


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
