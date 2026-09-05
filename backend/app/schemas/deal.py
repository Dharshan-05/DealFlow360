import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.deal import DealActivityType, DealStage


class DealMarginRisk(str, enum.Enum):
    """Classification of deal profitability health (Phase 209)."""
    HEALTHY = "HEALTHY"
    MODERATE = "MODERATE"
    THIN = "THIN"
    CRITICAL = "CRITICAL"


# ==============================================================================
# Phase 207: Deal Product Schemas
# ==============================================================================

class DealProductCreate(BaseModel):
    """Payload to add a product line item to a deal."""
    model_config = ConfigDict(from_attributes=True)

    product_id: uuid.UUID = Field(description="Catalog product identifier")
    quantity: Decimal = Field(description="Quantity to add", gt=Decimal("0.0"))
    unit_price: Optional[Decimal] = Field(default=None, description="Optional unit price override", ge=Decimal("0.0"))
    discount_percent: Optional[Decimal] = Field(default=Decimal("0.00"), description="Line discount percent", ge=Decimal("0.0"), le=Decimal("100.0"))
    tax_rate: Optional[Decimal] = Field(default=None, description="Optional applicable sales tax rate override", ge=Decimal("0.0"), le=Decimal("100.0"))
    notes: Optional[str] = Field(default=None, description="Line notes", max_length=255)


class DealProductResponse(BaseModel):
    """Response representation of a deal-linked product line item."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    deal_id: uuid.UUID
    product_id: uuid.UUID
    product_name: Optional[str] = None
    product_sku: Optional[str] = None
    quotation_line_item_id: Optional[uuid.UUID] = None
    quantity: Decimal
    unit_price: Decimal
    unit_cost: Decimal
    discount_percent: Decimal
    tax_rate: Decimal
    subtotal: Decimal
    discount_amount: Decimal
    taxable_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    total_cost: Decimal
    gross_profit: Decimal
    margin_percentage: Decimal
    notes: Optional[str] = None
    created_at: datetime


# ==============================================================================
# Phase 209: Deal Margin Schemas
# ==============================================================================

class DealMarginResponse(BaseModel):
    """Centralized deal margin calculation metrics (Phase 209)."""
    model_config = ConfigDict(from_attributes=True)

    deal_id: uuid.UUID
    deal_code: str
    total_revenue: Decimal
    total_cost: Decimal
    gross_profit: Decimal
    gross_margin_percentage: Decimal
    discounted_margin_percentage: Decimal
    margin_risk: DealMarginRisk
    is_negative_margin: bool


# ==============================================================================
# Phase 210: Deal Stage Schemas
# ==============================================================================

class DealStageUpdateRequest(BaseModel):
    """Payload to transition a deal stage."""
    model_config = ConfigDict(from_attributes=True)

    stage: DealStage = Field(description="Target deal stage")
    reason: Optional[str] = Field(default=None, description="Optional explanation for stage transition", max_length=255)


# ==============================================================================
# Phase 211: Deal Probability Schemas
# ==============================================================================

class DealProbabilityFactor(BaseModel):
    """Individual contributing signal factor to deal probability."""
    model_config = ConfigDict(from_attributes=True)

    factor: str
    impact_pct: int
    description: str


class DealProbabilityResponse(BaseModel):
    """Deterministic deal probability scoring breakdown (Phase 211)."""
    model_config = ConfigDict(from_attributes=True)

    deal_id: uuid.UUID
    probability: int = Field(ge=0, le=100)
    stage: str
    factors: List[DealProbabilityFactor]
    explanation: str


# ==============================================================================
# Phase 212: Deal Forecasting Schemas
# ==============================================================================

class DealForecastResponse(BaseModel):
    """Individual deal forecast value and weighted probability (Phase 212)."""
    model_config = ConfigDict(from_attributes=True)

    deal_id: uuid.UUID
    deal_code: str
    deal_value: Decimal
    probability: int
    weighted_value: Decimal
    stage: str
    status: str


class StageForecastItem(BaseModel):
    """Pipeline aggregation for an individual sales stage."""
    model_config = ConfigDict(from_attributes=True)

    stage: str
    deal_count: int
    total_value: Decimal
    weighted_value: Decimal


class PipelineForecastSummary(BaseModel):
    """Consolidated pipeline revenue forecast across all stages (Phase 212)."""
    model_config = ConfigDict(from_attributes=True)

    total_deals_count: int
    open_deals_count: int
    won_deals_count: int
    lost_deals_count: int
    pipeline_value: Decimal
    weighted_pipeline_value: Decimal
    expected_revenue: Decimal
    won_revenue: Decimal
    lost_value: Decimal
    stages: List[StageForecastItem]


# ==============================================================================
# Phase 213: Deal Activity Schemas
# ==============================================================================

class DealActivityCreate(BaseModel):
    """Payload to log a sales activity or note against a deal."""
    model_config = ConfigDict(from_attributes=True)

    activity_type: DealActivityType = Field(description="Type of activity")
    title: str = Field(description="Short title or summary", min_length=2, max_length=200)
    description: Optional[str] = Field(default=None, description="Detailed activity narrative")
    activity_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Structured contextual attributes")


class DealActivityResponse(BaseModel):
    """Persisted deal activity record."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    deal_id: uuid.UUID
    activity_type: str
    title: str
    description: Optional[str] = None
    actor_id: Optional[uuid.UUID] = None
    actor_name: Optional[str] = None
    activity_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime


# ==============================================================================
# Phase 214: Deal Timeline Schemas
# ==============================================================================

class DealTimelineEventResponse(BaseModel):
    """Unified chronological event entry in a deal timeline (Phase 214)."""
    model_config = ConfigDict(from_attributes=True)

    event_id: str
    source: str = Field(description="Originating subsystem (DEAL, QUOTATION, APPROVAL, ACTIVITY)")
    event_type: str
    title: str
    description: Optional[str] = None
    actor_name: Optional[str] = None
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


# ==============================================================================
# Phase 206 & 215: Deal Creation & Dashboard Schemas
# ==============================================================================

class DealCreateFromQuoteRequest(BaseModel):
    """Parameters to convert an accepted quotation to a deal (Phase 206)."""
    model_config = ConfigDict(from_attributes=True)

    title_override: Optional[str] = Field(default=None, max_length=200)
    notes: Optional[str] = Field(default=None)


class DealSummaryResponse(BaseModel):
    """Compact deal representation for listings and search."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    customer_id: uuid.UUID
    customer_name: Optional[str] = None
    deal_code: str
    title: str
    deal_value: Decimal
    status: str
    stage: str
    sales_rep_name: Optional[str] = None
    owner_id: Optional[uuid.UUID] = None
    quotation_id: Optional[uuid.UUID] = None
    quotation_number: Optional[str] = None
    quotation_version: Optional[int] = None
    probability: int
    expected_revenue: Decimal
    gross_profit: Decimal
    margin_percentage: Decimal
    closed_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class DealDetailResponse(DealSummaryResponse):
    """Full deal representation including financial breakdown and products."""
    subtotal: Decimal
    discount_amount: Decimal
    discount_percent: Decimal
    tax_amount: Decimal
    total_cost: Decimal
    notes: Optional[str] = None
    products: List[DealProductResponse] = Field(default_factory=list)
    recent_activities: List[DealActivityResponse] = Field(default_factory=list)


class DealDashboardResponse(BaseModel):
    """Executive KPI and pipeline aggregation response for deals (Phase 215)."""
    model_config = ConfigDict(from_attributes=True)

    total_deals: int
    open_deals: int
    won_deals: int
    lost_deals: int
    pipeline_value: Decimal
    weighted_pipeline: Decimal
    expected_revenue: Decimal
    average_deal_value: Decimal
    win_rate: float
    deals_by_stage: List[StageForecastItem]
    recent_activities: List[DealActivityResponse]
    top_deals: List[DealSummaryResponse]
