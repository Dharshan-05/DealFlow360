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
    subtotal: Decimal
    total_discount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    gross_profit: Decimal
    margin_percentage: Decimal
    is_negative_margin: bool
    line_items_count: int
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
