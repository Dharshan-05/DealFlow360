"""Quotation Schemas (DealFlow360 B09: Phases 186–195).

Strict Pydantic v2 validation models for Quotation lifecycle, line items,
quantity management, multi-level discounts, tax calculations, and real-time margins.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.quotation import QuotationStatus


# ==============================================================================
# Line Item Schemas (Phases 189–193, 195)
# ==============================================================================

class QuotationLineItemBase(BaseModel):
    """Base schema for quotation line item."""
    product_id: uuid.UUID = Field(..., description="Target catalog product ID (Phase 189)")
    quantity: Decimal = Field(
        Decimal("1.00"),
        gt=Decimal("0.00"),
        description="Quantity of product (Phase 190, must be positive)",
    )
    unit_price: Optional[Decimal] = Field(
        None,
        ge=Decimal("0.00"),
        description="Optional selling unit price override (Phase 191). If omitted, catalog base price is used.",
    )
    discount_percent: Decimal = Field(
        Decimal("0.00"),
        ge=Decimal("0.00"),
        le=Decimal("100.00"),
        description="Line discount percentage (Phase 193)",
    )
    tax_rate: Decimal = Field(
        Decimal("0.00"),
        ge=Decimal("0.00"),
        le=Decimal("100.00"),
        description="Line tax rate percentage (Phase 192)",
    )
    notes: Optional[str] = Field(None, max_length=255, description="Itemized notes or specifications")


class QuotationLineItemCreate(QuotationLineItemBase):
    """Payload for creating a quotation line item."""
    pass


class QuotationLineItemResponse(BaseModel):
    """Detailed response for a persisted quotation line item."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    quotation_id: uuid.UUID
    product_id: uuid.UUID
    line_number: int
    quantity: Decimal
    unit_price: Decimal
    unit_cost: Decimal
    discount_percent: Decimal
    discount_amount: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    subtotal: Decimal
    net_amount: Decimal
    total_amount: Decimal
    line_cost: Decimal
    gross_profit: Decimal
    margin_percentage: Decimal
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Denormalized product details
    product_sku: Optional[str] = None
    product_name: Optional[str] = None


# ==============================================================================
# Quotation Schemas (Phases 186–188, 194, 195)
# ==============================================================================

class QuotationCreate(BaseModel):
    """Creation payload for a new commercial quotation (Phase 186)."""
    customer_id: uuid.UUID = Field(..., description="Target customer account ID (Phase 188)")
    valid_until: Optional[datetime] = Field(None, description="Expiration/validity timestamp")
    notes: Optional[str] = Field(None, description="Internal quotation notes")
    terms_conditions: Optional[str] = Field(None, description="Commercial terms and conditions")
    overall_discount_percent: Decimal = Field(
        Decimal("0.00"),
        ge=Decimal("0.00"),
        le=Decimal("100.00"),
        description="Overall quotation-level discount percentage (Phase 194)",
    )
    line_items: List[QuotationLineItemCreate] = Field(
        default_factory=list,
        description="Initial itemized product line items (Phase 189)",
    )


class QuotationUpdate(BaseModel):
    """Update payload for modifying an existing quotation (Phase 186)."""
    customer_id: Optional[uuid.UUID] = Field(None, description="Customer reassignment")
    valid_until: Optional[datetime] = Field(None, description="Updated validity timestamp")
    notes: Optional[str] = Field(None, description="Updated notes")
    terms_conditions: Optional[str] = Field(None, description="Updated terms and conditions")
    overall_discount_percent: Optional[Decimal] = Field(
        None,
        ge=Decimal("0.00"),
        le=Decimal("100.00"),
        description="Updated overall discount percentage (Phase 194)",
    )
    line_items: Optional[List[QuotationLineItemCreate]] = Field(
        None,
        description="Replaced line item set. If provided, replaces all existing line items.",
    )


class QuotationStatusUpdate(BaseModel):
    """Payload for transitioning quotation lifecycle status."""
    status: QuotationStatus = Field(..., description="Target quotation status")
    reason: Optional[str] = Field(None, max_length=255, description="Reason for transition")


class QuotationSummaryResponse(BaseModel):
    """Summary representation of a quotation for paginated lists."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    customer_id: uuid.UUID
    customer_name: Optional[str] = None
    customer_code: Optional[str] = None
    user_id: uuid.UUID
    author_name: Optional[str] = None
    quotation_number: str
    status: str
    version_number: int = 1
    subtotal: Decimal
    total_discount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    gross_profit: Decimal
    margin_percentage: Decimal
    is_negative_margin: bool
    line_items_count: int
    approval_request_id: Optional[uuid.UUID] = None
    converted_deal_id: Optional[uuid.UUID] = None
    sent_at: Optional[datetime] = None
    viewed_at: Optional[datetime] = None
    accepted_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class QuotationDetailResponse(QuotationSummaryResponse):
    """Full detail representation of a quotation including line items and margins."""
    notes: Optional[str] = None
    terms_conditions: Optional[str] = None
    line_discount_total: Decimal
    overall_discount_percent: Decimal
    overall_discount_amount: Decimal
    taxable_amount: Decimal
    total_cost: Decimal
    accepted_by_id: Optional[uuid.UUID] = None
    acceptance_notes: Optional[str] = None
    rejected_by_id: Optional[uuid.UUID] = None
    rejection_reason: Optional[str] = None
    converted_at: Optional[datetime] = None
    line_items: List[QuotationLineItemResponse] = Field(default_factory=list)


# ==============================================================================
# Calculation Schemas (Transient Real-Time Pricing & Margins, Phase 192–195)
# ==============================================================================

class QuotationCalculationRequest(BaseModel):
    """Request payload for dry-run real-time price, tax, and margin calculation."""
    overall_discount_percent: Decimal = Field(
        Decimal("0.00"),
        ge=Decimal("0.00"),
        le=Decimal("100.00"),
    )
    line_items: List[QuotationLineItemCreate] = Field(
        default_factory=list,
    )


class QuotationCalculationResponse(BaseModel):
    """Response payload for dry-run real-time quote margin and tax computation."""
    subtotal: Decimal
    line_discount_total: Decimal
    overall_discount_percent: Decimal
    overall_discount_amount: Decimal
    total_discount: Decimal
    taxable_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    total_cost: Decimal
    gross_profit: Decimal
    margin_percentage: Decimal
    is_negative_margin: bool
    lines: List[QuotationLineItemResponse] = Field(default_factory=list)


# ==============================================================================
# B10 Lifecycle, Versioning, Approval, Send & Conversion Schemas (Phases 196–205)
# ==============================================================================

class QuotationVersionCreate(BaseModel):
    """Request to create a new revision/version for a quotation (Phase 197)."""
    change_reason: Optional[str] = Field(
        None,
        max_length=255,
        description="Business rationale for the new version revision",
    )


class QuotationVersionResponse(BaseModel):
    """Immutable snapshot representation of a historical quotation version (Phase 197)."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    quotation_id: uuid.UUID
    company_id: uuid.UUID
    version_number: int
    created_by_id: Optional[uuid.UUID] = None
    change_reason: Optional[str] = None
    snapshot_data: dict
    created_at: datetime


class QuotationExpireRequest(BaseModel):
    """Manual/explicit expiration trigger request (Phase 198)."""
    reason: Optional[str] = Field(None, description="Optional explanation for expiration")


class QuotationExpirationEvaluationResponse(BaseModel):
    """Result of deterministic expiration check (Phase 198)."""
    quotation_id: uuid.UUID
    is_expired: bool
    valid_until: Optional[datetime] = None
    previous_status: str
    current_status: str
    message: str


class QuotationApprovalSubmitRequest(BaseModel):
    """Payload for submitting quotation into B05/B06 approval engine (Phase 199)."""
    notes: Optional[str] = Field(None, description="Contextual note for approvers")


class QuotationApprovalSubmitResponse(BaseModel):
    """Result of quotation approval submission (Phase 199)."""
    quotation_id: uuid.UUID
    approval_request_id: Optional[uuid.UUID] = None
    status: str
    required_level: str
    auto_approved: bool
    message: str


class QuotationEmailRequest(BaseModel):
    """Payload for dispatching quotation via email with attached PDF (Phase 201)."""
    recipient_email: str = Field(..., description="Target recipient email address")
    subject: Optional[str] = Field(None, max_length=255, description="Custom email subject")
    notes: Optional[str] = Field(None, description="Accompanying email note")


class QuotationEmailResponse(BaseModel):
    """Status result of quotation email dispatch (Phase 201)."""
    quotation_id: uuid.UUID
    recipient_email: str
    delivery_status: str = Field(..., description="'SENT', 'FAILED', or 'UNAVAILABLE_CONFIGURATION'")
    tracking_token: str
    message: str


class QuotationSendLogResponse(BaseModel):
    """Audit log entry of quotation dispatch and view tracking (Phase 202)."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    quotation_id: uuid.UUID
    version_number: int
    sender_id: Optional[uuid.UUID] = None
    recipient_email: str
    delivery_status: str
    email_subject: Optional[str] = None
    tracking_token: str
    sent_at: datetime
    viewed_at: Optional[datetime] = None


class QuotationAcceptRequest(BaseModel):
    """Payload for customer accepting quotation (Phase 203)."""
    acceptance_notes: Optional[str] = Field(None, description="Acceptance commentary or PO number")


class QuotationAcceptResponse(BaseModel):
    """Confirmation of quotation acceptance (Phase 203)."""
    quotation_id: uuid.UUID
    version_number: int
    status: str
    accepted_at: datetime
    accepted_by_id: Optional[uuid.UUID] = None
    message: str


class QuotationRejectRequest(BaseModel):
    """Payload for rejecting quotation (Phase 204)."""
    reason: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="Mandatory reason for quotation rejection",
    )


class QuotationRejectResponse(BaseModel):
    """Confirmation of quotation rejection (Phase 204)."""
    quotation_id: uuid.UUID
    version_number: int
    status: str
    rejected_at: datetime
    rejected_by_id: Optional[uuid.UUID] = None
    reason: str
    message: str


class QuotationConvertDealRequest(BaseModel):
    """Payload for converting accepted quotation into deal entity (Phase 205)."""
    title_override: Optional[str] = Field(None, max_length=200, description="Custom deal title")
    notes: Optional[str] = Field(None, description="Additional commercial notes on the deal")


class QuotationConvertDealResponse(BaseModel):
    """Result of converting quotation to customer deal (Phase 205)."""
    quotation_id: uuid.UUID
    deal_id: uuid.UUID
    deal_code: str
    deal_value: Decimal
    status: str
    converted_at: datetime
    message: str
