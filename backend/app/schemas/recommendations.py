"""Schemas for DealFlow360 B07 & B08 Recommendation Intelligence Layer (Phases 166–185).

Defines deterministic data structures for:
- Phase 166: AI Upsell Engine
- Phase 167: AI Cross-Sell Engine
- Phase 168: Customer Purchase Pattern Analysis
- Phase 169: Product Affinity Analysis
- Phase 170: Frequently Bought Together
- Phase 171: Next Best Product
- Phase 172: Customer Segmentation
- Phase 173: Upsell Probability
- Phase 174: Cross-Sell Probability
- Phase 175: Recommendation Ranking
- Phase 176: Upsell Score (0–100)
- Phase 177: Cross-Sell Score (0–100)
- Phase 178: Extended Recommendation Ranking
- Phase 179: AI Next-Best-Product with telemetry
- Phase 180: Upsell Explanation
- Phase 181: Add-to-Quote Recommendation
- Phase 182: Real-Time Margin Update
- Phase 183: Upsell Acceptance Tracking
- Phase 184: Recommendation Analytics
- Phase 185: Upsell Dashboard
"""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field


class RecommendationType(str, Enum):
    """Categorization of recommendation strategy (Phase 171)."""
    UPSELL = "UPSELL"
    CROSS_SELL = "CROSS_SELL"
    REPEAT_PURCHASE = "REPEAT_PURCHASE"


class CustomerBehaviorSegment(str, Enum):
    """Deterministic customer behavioral segmentation (Phase 172)."""
    HIGH_VALUE = "HIGH_VALUE"
    LOYAL = "LOYAL"
    ACTIVE = "ACTIVE"
    GROWTH = "GROWTH"
    AT_RISK = "AT_RISK"
    NEW = "NEW"
    DORMANT = "DORMANT"


class RecommendationEventEnum(str, Enum):
    """Supported lifecycle tracking events (Phase 183)."""
    GENERATED = "GENERATED"
    VIEWED = "VIEWED"
    SELECTED = "SELECTED"
    ADDED_TO_QUOTE = "ADDED_TO_QUOTE"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    DISMISSED = "DISMISSED"


# ==============================================================================
# Phase 168: Customer Purchase Pattern Analysis
# ==============================================================================

class CustomerPurchasePattern(BaseModel):
    """Deterministic RFM and behavioral purchase pattern signals (Phase 168)."""
    model_config = ConfigDict(from_attributes=True)

    customer_id: uuid.UUID
    company_id: uuid.UUID
    total_orders_count: int
    total_spend: Decimal
    average_order_value: Decimal
    last_purchase_date: Optional[datetime] = None
    recency_days: int = Field(
        ...,
        description="Days since most recent purchase. 999 if no prior history."
    )
    purchase_frequency_monthly: float = Field(
        ...,
        description="Average number of completed orders per month across active tenure."
    )
    tenure_days: int
    top_purchased_categories: List[str] = Field(
        default_factory=list,
        description="Top product categories ordered by customer frequency."
    )
    distinct_products_count: int
    repeat_purchase_rate: float = Field(
        ...,
        description="Fraction of unique products purchased more than once (0.0 - 1.0)."
    )
    is_zero_history: bool = False
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


# ==============================================================================
# Phase 169: Product Affinity Analysis
# ==============================================================================

class ProductAffinityMetric(BaseModel):
    """Pairwise statistical association and affinity metrics (Phase 169)."""
    source_product_id: uuid.UUID
    target_product_id: uuid.UUID
    source_product_name: str
    target_product_name: str
    source_sku: str
    target_sku: str
    co_occurrence_count: int = Field(
        ...,
        description="Number of transactions/deals containing both products."
    )
    source_count: int = Field(
        ...,
        description="Total transactions containing source product."
    )
    target_count: int = Field(
        ...,
        description="Total transactions containing target product."
    )
    support: float = Field(
        ...,
        description="P(Source and Target) co-occurrence fraction relative to total company transactions."
    )
    confidence: float = Field(
        ...,
        description="P(Target | Source) conditional purchase probability."
    )
    lift: float = Field(
        ...,
        description="Ratio of observed co-occurrence to expected if independent: P(A,B) / (P(A) * P(B))."
    )
    affinity_score: float = Field(
        ...,
        description="Normalized composite affinity score clamped to [0.0, 1.0]."
    )


# ==============================================================================
# Phase 170: Frequently Bought Together
# ==============================================================================

class FrequentlyBoughtTogetherItem(BaseModel):
    """Complementary product frequently bought alongside a reference item (Phase 170)."""
    product_id: uuid.UUID
    sku: str
    name: str
    category_id: Optional[uuid.UUID] = None
    category_name: Optional[str] = None
    base_price: Decimal
    inventory_quantity: int
    is_active: bool
    confidence: float
    lift: float
    co_occurrence_count: int
    rank: int


class FrequentlyBoughtTogetherResponse(BaseModel):
    """Response payload for frequently bought together recommendations (Phase 170)."""
    source_product_id: uuid.UUID
    source_sku: str
    source_name: str
    total_associations_evaluated: int
    items: List[FrequentlyBoughtTogetherItem]
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ==============================================================================
# Phase 172: Customer Segmentation
# ==============================================================================

class CustomerSegmentationResult(BaseModel):
    """Behavioral segmentation evaluation result for a customer (Phase 172)."""
    customer_id: uuid.UUID
    segment: CustomerBehaviorSegment
    segment_label: str
    rationale: str
    recency_days: int
    frequency_count: int
    monetary_total: Decimal
    average_order_value: Decimal
    tenure_days: int
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)


# ==============================================================================
# Phase 180: Recommendation Explanation Schema
# ==============================================================================

class RecommendationExplanation(BaseModel):
    """Structured human-readable explanation data (Phase 180)."""
    summary: str = Field(..., description="High-level narrative justification.")
    reasons: List[str] = Field(default_factory=list, description="Explicit bulleted business reasons.")
    signals: Dict[str, Any] = Field(default_factory=dict, description="Underlying numerical signals.")


# ==============================================================================
# Recommendation Candidate & Item Schema (Phases 166, 167, 171, 175, 176, 177, 178, 179)
# ==============================================================================

class RecommendationItem(BaseModel):
    """Ranked product recommendation item with multi-factor attribution (Phase 175 & 178)."""
    product_id: uuid.UUID
    sku: str
    name: str
    category_id: Optional[uuid.UUID] = None
    category_name: Optional[str] = None
    base_price: Decimal
    cost: Decimal
    unit_margin_pct: Decimal
    inventory_status: str
    inventory_quantity: int

    # Scored dimensions
    recommendation_type: RecommendationType
    score: float = Field(
        ...,
        description="Final deterministic weighted composite score (0.0 - 1.0 or 0 - 100)."
    )
    rank: int = Field(
        ...,
        description="Deterministic position rank (1-indexed)."
    )
    upsell_score_100: int = Field(
        default=0,
        description="Deterministic 0-100 integer score (Phase 176)."
    )
    cross_sell_score_100: int = Field(
        default=0,
        description="Deterministic 0-100 integer score (Phase 177)."
    )
    upsell_probability: float = Field(
        ...,
        description="Calibrated upsell likelihood (Phase 173)."
    )
    cross_sell_probability: float = Field(
        ...,
        description="Calibrated cross-sell likelihood (Phase 174)."
    )
    affinity_score: float = Field(
        ...,
        description="Product-to-product or basket association strength (Phase 169)."
    )
    segment_relevance: float = Field(
        ...,
        description="Behavioral alignment with customer segment (Phase 172)."
    )
    supporting_signals: Dict[str, float] = Field(
        default_factory=dict,
        description="Structured numerical signal components supporting the recommendation."
    )
    explanation: Optional[RecommendationExplanation] = Field(
        default=None,
        description="Explainability metadata payload (Phase 180)."
    )


class RecommendationRankingResponse(BaseModel):
    """Unified response containing ranked product recommendations for a customer (Phase 175 & 178)."""
    customer_id: uuid.UUID
    customer_code: str
    customer_name: str
    customer_segment: CustomerBehaviorSegment
    total_candidates_evaluated: int
    recommendations: List[RecommendationItem]
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class NextBestProductResponse(BaseModel):
    """Optimal single next best product recommendation (Phase 171 & 179)."""
    customer_id: uuid.UUID
    has_recommendation: bool
    best_product: Optional[RecommendationItem] = None
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)


# ==============================================================================
# Phase 181 & 182: Add-to-Quote & Real-Time Margin Schemas
# ==============================================================================

class QuoteLineItemInput(BaseModel):
    """Line item in quote context."""
    product_id: uuid.UUID
    quantity: int = Field(1, ge=1)
    selling_price: Decimal = Field(..., ge=Decimal("0.00"))
    unit_cost: Decimal = Field(..., ge=Decimal("0.00"))


class AddToQuoteRequest(BaseModel):
    """Request payload to add a recommended product to quote context (Phase 181)."""
    customer_id: uuid.UUID
    product_id: uuid.UUID
    recommendation_id: Optional[str] = None
    recommendation_type: RecommendationType = RecommendationType.UPSELL
    quantity: int = Field(1, ge=1)
    quote_reference: Optional[str] = None
    existing_items: List[QuoteLineItemInput] = Field(default_factory=list)


class LineMarginDetail(BaseModel):
    """Individual line item margin detail (Phase 182)."""
    product_id: uuid.UUID
    quantity: int
    unit_price: Decimal
    unit_cost: Decimal
    line_revenue: Decimal
    line_cost: Decimal
    line_gross_profit: Decimal
    line_margin_pct: Decimal


class RealTimeMarginSummary(BaseModel):
    """Consolidated quote margin analysis (Phase 182)."""
    total_revenue: Decimal
    total_cost: Decimal
    total_gross_profit: Decimal
    total_margin_pct: Decimal
    lines: List[LineMarginDetail]


class AddToQuoteResponse(BaseModel):
    """Response returned upon adding a recommendation to quote context (Phase 181)."""
    customer_id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    product_sku: str
    quote_reference: Optional[str]
    added_quantity: int
    margin_summary: RealTimeMarginSummary
    event_id: Optional[str] = None
    status: str = "SUCCESS"


# ==============================================================================
# Phase 183: Upsell Acceptance Tracking Schemas
# ==============================================================================

class RecommendationEventCreate(BaseModel):
    """Event submission payload for lifecycle tracking (Phase 183)."""
    recommendation_id: str
    customer_id: uuid.UUID
    product_id: uuid.UUID
    recommendation_type: RecommendationType
    event_type: RecommendationEventEnum
    score: Decimal = Field(Decimal("0.00"), ge=Decimal("0.00"), le=Decimal("100.00"))
    quote_reference: Optional[str] = None
    context_metadata: Optional[Dict[str, Any]] = None


class RecommendationEventResponse(BaseModel):
    """Event confirmation response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    recommendation_id: str
    customer_id: uuid.UUID
    product_id: uuid.UUID
    recommendation_type: str
    event_type: str
    score: Decimal
    quote_reference: Optional[str] = None
    created_at: datetime


# ==============================================================================
# Phase 184: Recommendation Analytics Schemas
# ==============================================================================

class ProductPerformanceItem(BaseModel):
    """Product performance in recommendations."""
    product_id: uuid.UUID
    sku: str
    name: str
    recommendation_count: int
    acceptance_count: int
    conversion_rate: float


class RecommendationAnalyticsResponse(BaseModel):
    """Aggregated recommendation analytics (Phase 184)."""
    total_recommendations_generated: int
    total_viewed: int
    total_selected: int
    total_added_to_quote: int
    total_accepted: int
    total_rejected: int
    total_dismissed: int
    view_rate: float
    selection_rate: float
    add_to_quote_rate: float
    acceptance_rate: float
    average_recommendation_score: float
    upsell_events_count: int
    cross_sell_events_count: int
    top_recommended_products: List[ProductPerformanceItem]
    top_accepted_products: List[ProductPerformanceItem]
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


# ==============================================================================
# Phase 185: Upsell Dashboard Schemas
# ==============================================================================

class FunnelStageMetric(BaseModel):
    """Funnel stage metric."""
    stage: str
    count: int
    conversion_rate_from_top: float


class RecentActivityItem(BaseModel):
    """Item in recent activity stream."""
    event_id: uuid.UUID
    event_type: str
    recommendation_type: str
    customer_id: uuid.UUID
    product_id: uuid.UUID
    score: float
    timestamp: datetime


class UpsellDashboardSummary(BaseModel):
    """Consolidated Upsell & Recommendation Dashboard summary (Phase 185)."""
    kpis: Dict[str, Any]
    conversion_funnel: List[FunnelStageMetric]
    category_distribution: Dict[str, int]
    analytics: RecommendationAnalyticsResponse
    recent_activity: List[RecentActivityItem]
    generated_at: datetime = Field(default_factory=datetime.utcnow)
