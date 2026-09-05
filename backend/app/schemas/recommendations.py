"""Schemas for DealFlow360 B07 Recommendation Intelligence Layer (Phases 166–175).

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
"""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional
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
# Recommendation Candidate & Item Schema (Phases 166, 167, 171, 173, 174, 175)
# ==============================================================================

class RecommendationItem(BaseModel):
    """Ranked product recommendation item with multi-factor attribution (Phase 175)."""
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
        description="Final deterministic weighted composite score (0.0 - 1.0)."
    )
    rank: int = Field(
        ...,
        description="Deterministic position rank (1-indexed)."
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


class RecommendationRankingResponse(BaseModel):
    """Unified response containing ranked product recommendations for a customer (Phase 175)."""
    customer_id: uuid.UUID
    customer_code: str
    customer_name: str
    customer_segment: CustomerBehaviorSegment
    total_candidates_evaluated: int
    recommendations: List[RecommendationItem]
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class NextBestProductResponse(BaseModel):
    """Optimal single next best product recommendation (Phase 171)."""
    customer_id: uuid.UUID
    has_recommendation: bool
    best_product: Optional[RecommendationItem] = None
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
