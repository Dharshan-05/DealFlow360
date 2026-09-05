"""Pydantic schemas for Discount Intelligence Foundation (Phases 111–115).

Covers:
- Phase 111: Recommended Discount Engine
- Phase 112: Maximum Safe Discount
- Phase 113: Margin Protection Engine
- Phase 114: Historical Discount Analysis
- Phase 115: Customer Discount Analysis
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ==============================================================================
# Phase 113: Margin Protection Schemas
# ==============================================================================

class MarginProtectionRequest(BaseModel):
    product_id: uuid.UUID = Field(..., description="Target product ID")
    selling_price: Optional[Decimal] = Field(None, ge=0, description="Override selling price, or defaults to product base_price")
    min_margin_percentage: Decimal = Field(Decimal("15.00"), ge=0, le=100, description="Minimum required gross profit margin (0-100%)")


class MarginProtectionResponse(BaseModel):
    product_id: uuid.UUID
    selling_price: Decimal
    unit_cost: Decimal
    current_margin_percentage: Decimal
    protected_margin_percentage: Decimal
    max_discount_from_margin: Decimal
    is_margin_preserved: bool
    reason_code: str = Field(..., description="Explanation code: SAFE_MARGIN, COST_EXCEEDS_PRICE, ZERO_PRICE, ZERO_MARGIN_BUFFER")
    reason_description: str


# ==============================================================================
# Phase 112: Maximum Safe Discount Schemas
# ==============================================================================

class MaximumSafeDiscountRequest(BaseModel):
    customer_id: uuid.UUID
    product_id: uuid.UUID
    selling_price: Optional[Decimal] = Field(None, ge=0, description="Optional override selling price")
    min_margin_percentage: Decimal = Field(Decimal("15.00"), ge=0, le=100, description="Target minimum gross margin")


class MaximumSafeDiscountResponse(BaseModel):
    customer_id: uuid.UUID
    product_id: uuid.UUID
    max_safe_discount: Decimal = Field(..., description="Deterministic maximum safe discount percentage")
    governed_ceiling: Decimal = Field(..., description="Minimum effective ceiling from active policies")
    margin_ceiling: Decimal = Field(..., description="Maximum discount allowable under margin protection")
    actor_authority_limit: Optional[Decimal] = Field(None, description="Authorized limit for the evaluating actor")
    limiting_factor: str = Field(..., description="MARGIN_LIMIT, GOVERNANCE_CEILING, ACTOR_AUTHORITY, or NONE")
    evaluation_breakdown: Dict[str, Any]
    evaluated_at: datetime


# ==============================================================================
# Phase 114: Historical Discount Analysis Schemas
# ==============================================================================

class HistoricalDiscountSummary(BaseModel):
    sample_size: int = Field(..., ge=0, description="Total discount events analyzed")
    average_discount: Optional[Decimal] = Field(None, description="Mean discount percentage")
    min_discount: Optional[Decimal] = Field(None, description="Minimum discount percentage")
    max_discount: Optional[Decimal] = Field(None, description="Maximum discount percentage")
    latest_discount: Optional[Decimal] = Field(None, description="Most recent discount percentage")
    latest_applied_at: Optional[datetime] = Field(None, description="Timestamp of most recent discount")
    total_discount_amount: Decimal = Field(Decimal("0.00"), description="Total monetary discount awarded")


class HistoricalDiscountAnalysisResponse(BaseModel):
    company_id: uuid.UUID
    customer_id: Optional[uuid.UUID] = None
    product_id: Optional[uuid.UUID] = None
    summary: HistoricalDiscountSummary
    has_history: bool
    evaluated_at: datetime


# ==============================================================================
# Phase 115: Customer Discount Analysis Schemas
# ==============================================================================

class CustomerDiscountAnalysisResponse(BaseModel):
    customer_id: uuid.UUID
    customer_name: str
    customer_code: str
    tier_name: Optional[str] = None
    active_customer_ceiling: Optional[Decimal] = None
    history_summary: HistoricalDiscountSummary
    compliance_rating: str = Field(..., description="COMPLIANT, HIGH_DISCOUNT_CUSTOMER, or NO_HISTORY")
    insight_summary: str
    evaluated_at: datetime


# ==============================================================================
# Phase 111: Recommended Discount Engine Schemas
# ==============================================================================

class DiscountRecommendationRequest(BaseModel):
    customer_id: uuid.UUID
    product_id: uuid.UUID
    selling_price: Optional[Decimal] = Field(None, ge=0, description="Optional override selling price")
    min_margin_percentage: Decimal = Field(Decimal("15.00"), ge=0, le=100, description="Target minimum gross margin")
    benchmark_discount: Optional[Decimal] = Field(None, ge=0, le=100, description="Optional baseline benchmark discount target")


class DiscountRecommendationResponse(BaseModel):
    customer_id: uuid.UUID
    product_id: uuid.UUID
    recommended_discount: Decimal = Field(..., description="Deterministic recommended discount percentage")
    max_safe_discount: Decimal = Field(..., description="Calculated maximum safe discount boundary")
    governed_ceiling: Decimal = Field(..., description="Effective governance ceiling")
    margin_ceiling: Decimal = Field(..., description="Margin-preserving maximum discount")
    customer_historical_avg: Optional[Decimal] = None
    reason_code: str = Field(..., description="HISTORICAL_ALIGNMENT, MAX_SAFE_CLAMPED, MARGIN_CONSTRAINED, CEILING_CONSTRAINED, or DEFAULT_BENCHMARK")
    reason_summary: str
    evaluation_details: Dict[str, Any]
    evaluated_at: datetime
