
import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

# Base Models

class SubscriptionPlanBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    price: Decimal = Field(..., max_digits=14, decimal_places=2)
    currency: str = Field(default="INR", max_length=3)
    billing_interval: str = Field(..., max_length=50)
    interval_count: int = Field(default=1, ge=1)
    trial_days: int = Field(default=0, ge=0)
    is_active: bool = True
    metadata_json: Optional[dict] = None

class SubscriptionPlanCreate(SubscriptionPlanBase):
    pass

class SubscriptionPlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    is_active: Optional[bool] = None

class SubscriptionPlanResponse(SubscriptionPlanBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    company_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

class SubscriptionBase(BaseModel):
    customer_id: uuid.UUID
    plan_id: uuid.UUID
    auto_renew: bool = True
    quantity: int = Field(default=1, ge=1)

class SubscriptionCreate(SubscriptionBase):
    pass

class SubscriptionUpdate(BaseModel):
    auto_renew: Optional[bool] = None
    quantity: Optional[int] = Field(None, ge=1)

class SubscriptionResponse(SubscriptionBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    company_id: uuid.UUID
    status: str
    start_date: datetime
    current_period_start: datetime
    current_period_end: datetime
    next_billing_date: Optional[datetime]
    cancelled_at: Optional[datetime]
    cancel_at_period_end: bool
    created_at: datetime
    updated_at: datetime

class InvoiceLineItemBase(BaseModel):
    product_id: Optional[uuid.UUID] = None
    description: str
    quantity: Decimal = Field(default=Decimal("1.0000"), max_digits=12, decimal_places=4)
    unit_price: Decimal = Field(..., max_digits=14, decimal_places=2)
    discount_amount: Decimal = Field(default=Decimal("0.00"), max_digits=14, decimal_places=2)
    tax_amount: Decimal = Field(default=Decimal("0.00"), max_digits=14, decimal_places=2)
    billing_type: str = Field(default="ONE_TIME")
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

class InvoiceLineItemResponse(InvoiceLineItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    invoice_id: uuid.UUID
    subtotal: Decimal
    total: Decimal
    created_at: datetime

class InvoiceBase(BaseModel):
    customer_id: uuid.UUID
    subscription_id: Optional[uuid.UUID] = None
    deal_id: Optional[uuid.UUID] = None
    quotation_id: Optional[uuid.UUID] = None
    issue_date: date
    due_date: date
    currency: str = "INR"

class InvoiceResponse(InvoiceBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    company_id: uuid.UUID
    invoice_number: str
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    total_amount: Decimal
    amount_paid: Decimal
    amount_due: Decimal
    status: str
    payment_status: str
    billing_period_start: Optional[datetime]
    billing_period_end: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    line_items: List[InvoiceLineItemResponse] = []

class UsageRecordCreate(BaseModel):
    metric_name: str
    quantity: Decimal = Field(default=Decimal("0.0000"), max_digits=12, decimal_places=4)
    idempotency_key: str

class UsageRecordResponse(UsageRecordCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    company_id: uuid.UUID
    subscription_id: uuid.UUID
    timestamp: datetime
    created_at: datetime

class BillingDashboardSummary(BaseModel):
    mrr: Decimal
    arr: Decimal
    active_subscriptions: int
    pending_payments_count: int
    overdue_invoices_count: int
    recurring_revenue: Decimal
    one_time_revenue: Decimal
    hybrid_revenue: Decimal

