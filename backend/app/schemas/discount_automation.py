"""Pydantic schemas for Discount Automation & Decision Engine (DealFlow360 G24: Phases 116–120).

Covers:
- Phase 116: Inventory-Aware Discount
- Phase 117: Deal-Value-Aware Discount
- Phase 118: Discount Risk Calculation
- Phase 119: Discount Decision Engine
- Phase 120: Automated Discount Application
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ==============================================================================
# Phase 116: Inventory-Aware Discount Schemas
# ==============================================================================

class InventoryDiscountSignalRequest(BaseModel):
    product_id: uuid.UUID
    base_target_discount: Decimal = Field(..., ge=0, le=100, description="Baseline target discount percentage")


class InventoryDiscountSignalResponse(BaseModel):
    product_id: uuid.UUID
    total_physical_stock: int
    total_reserved_stock: int
    total_available_to_promise: int
    open_backorders_count: int
    inventory_signal: str = Field(..., description="EXCESS_AVAILABLE, HEALTHY_STOCK, LOW_STOCK, OUT_OF_STOCK, or BACKORDERED")
    adjustment_factor: Decimal = Field(..., description="Multiplier applied to target discount (e.g. 1.20, 1.00, 0.75, 0.50, 0.00)")
    suggested_discount: Decimal = Field(..., description="Inventory-modulated discount percentage")
    reason_code: str
    explanation: str
    evaluated_at: datetime


# ==============================================================================
# Phase 117: Deal-Value-Aware Discount Schemas
# ==============================================================================

class DealValueDiscountSignalRequest(BaseModel):
    product_id: uuid.UUID
    deal_value: Optional[Decimal] = Field(None, ge=0, description="Direct deal transaction value, or computed via quantity * price")
    quantity: int = Field(1, ge=1, description="Quantity being purchased if deal_value is not directly supplied")
    selling_price_override: Optional[Decimal] = Field(None, ge=0, description="Optional override price per unit")
    base_target_discount: Decimal = Field(..., ge=0, le=100, description="Baseline target discount percentage")


class DealValueDiscountSignalResponse(BaseModel):
    product_id: uuid.UUID
    effective_deal_value: Decimal
    value_tier: str = Field(..., description="LOW_VALUE, STANDARD_VALUE, HIGH_VALUE, or ENTERPRISE_TIER")
    value_incentive_multiplier: Decimal
    suggested_discount: Decimal
    reason_code: str
    explanation: str
    evaluated_at: datetime


# ==============================================================================
# Phase 118: Discount Risk Calculation Schemas
# ==============================================================================

class DiscountRiskCalculationRequest(BaseModel):
    customer_id: uuid.UUID
    product_id: uuid.UUID
    requested_discount: Decimal = Field(..., ge=0, le=100, description="Discount percentage proposed by sales rep")
    deal_value: Optional[Decimal] = Field(None, ge=0, description="Optional total transaction value")
    selling_price_override: Optional[Decimal] = Field(None, ge=0, description="Optional override selling price")
    min_margin_percentage: Decimal = Field(Decimal("15.00"), ge=0, le=100, description="Required minimum gross margin")


class RiskDimensionScore(BaseModel):
    dimension: str
    score: int = Field(..., ge=0, le=100)
    weight: Decimal
    weighted_score: Decimal
    details: str


class DiscountRiskCalculationResponse(BaseModel):
    customer_id: uuid.UUID
    product_id: uuid.UUID
    requested_discount: Decimal
    overall_risk_score: int = Field(..., ge=0, le=100, description="Aggregated risk score 0 to 100")
    risk_level: str = Field(..., description="LOW, MEDIUM, HIGH, or CRITICAL")
    primary_risk_factors: List[str]
    dimensions: List[RiskDimensionScore]
    is_acceptable_risk: bool
    risk_summary: str
    evaluated_at: datetime


# ==============================================================================
# Phase 119: Discount Decision Engine Schemas
# ==============================================================================

class DiscountDecisionRequest(BaseModel):
    customer_id: uuid.UUID
    product_id: uuid.UUID
    requested_discount: Decimal = Field(..., ge=0, le=100, description="Requested discount percentage")
    deal_reference: Optional[str] = Field(None, max_length=100, description="Optional deal / order tracking reference")
    deal_value: Optional[Decimal] = Field(None, ge=0, description="Optional total deal value")
    selling_price_override: Optional[Decimal] = Field(None, ge=0, description="Optional unit price override")
    min_margin_percentage: Decimal = Field(Decimal("15.00"), ge=0, le=100, description="Required gross profit margin")


class DiscountDecisionResponse(BaseModel):
    decision_id: str
    customer_id: uuid.UUID
    product_id: uuid.UUID
    requested_discount: Decimal
    decision: str = Field(..., description="APPROVED, ADJUSTED, ESCALATION_REQUIRED, or REJECTED")
    permitted_discount: Decimal = Field(..., description="Final allowable discount percentage under this decision")
    effective_ceiling: Decimal
    actor_authority_limit: Optional[Decimal] = None
    margin_ceiling: Decimal
    max_safe_discount: Decimal
    inventory_signal: str
    deal_value_tier: str
    risk_level: str
    limiting_factors: List[str]
    is_executable: bool = Field(..., description="True if decision is APPROVED or ADJUSTED and can be immediately applied")
    requires_escalation: bool
    escalation_role_needed: Optional[str] = None
    decision_summary: str
    evaluated_at: datetime


# ==============================================================================
# Phase 120: Automated Discount Application Schemas
# ==============================================================================

class ApplyDiscountRequest(BaseModel):
    customer_id: uuid.UUID
    product_id: uuid.UUID
    requested_discount: Decimal = Field(..., ge=0, le=100, description="Discount to apply")
    deal_reference: str = Field(..., min_length=1, max_length=100, description="Canonical deal reference identifier")
    deal_value: Optional[Decimal] = Field(None, ge=0, description="Optional total transaction value")
    selling_price_override: Optional[Decimal] = Field(None, ge=0, description="Optional unit selling price")
    min_margin_percentage: Decimal = Field(Decimal("15.00"), ge=0, le=100, description="Required gross margin percentage")
    notes: Optional[str] = Field(None, max_length=255, description="Optional domain justification notes")


class AppliedDiscountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    customer_id: uuid.UUID
    product_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    deal_reference: Optional[str] = None
    decision_id: Optional[str] = None
    requested_discount: Decimal
    applied_discount: Decimal
    selling_price: Decimal
    discounted_price: Decimal
    unit_cost: Decimal
    margin_percentage: Decimal
    risk_level: str
    reason_code: str
    decision_summary: Optional[str] = None
    context_metadata: Optional[Dict[str, Any]] = None
    applied_at: datetime
    created_at: datetime


class AppliedDiscountListResponse(BaseModel):
    items: List[AppliedDiscountResponse]
    total: int
