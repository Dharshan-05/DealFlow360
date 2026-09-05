"""Customer Analytics, Search, Filtering, Segmentation & Dashboard Schemas (Phases 066–070).

Provides typed response models for:
- Phase 066: Customer Analytics (aggregates, distributions, revenue summaries)
- Phase 067: Customer Search parameters
- Phase 068: Customer Filtering parameters
- Phase 069: Customer Segmentation (deterministic rule-based customer segments)
- Phase 070: Customer Dashboard (consolidated KPIs, charts, and activity feeds)
"""
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Phase 066: Customer Analytics Schemas
# ---------------------------------------------------------------------------

class TierDistributionItem(BaseModel):
    tier_id: Optional[uuid.UUID] = None
    tier_name: str
    tier_code: str
    customer_count: int
    percentage_of_total: Decimal


class CustomerAnalyticsSummary(BaseModel):
    """Aggregate customer portfolio analytics metrics."""
    total_customers: int
    active_customers: int
    inactive_customers: int
    tiered_customers: int
    standard_customers: int
    
    # Financial and Transaction Totals
    total_purchases_count: int
    total_purchases_amount: Decimal
    total_deals_count: int
    total_deals_value: Decimal
    total_payments_count: int
    total_payments_amount: Decimal
    total_discounts_count: int
    total_discounts_amount: Decimal

    # Portfolio Averages
    average_customer_ltv: Decimal
    average_order_value: Decimal
    average_discount_percentage: Decimal

    # Tier Breakdown
    tier_distribution: List[TierDistributionItem]
    calculated_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Phase 069: Customer Segmentation Schemas
# ---------------------------------------------------------------------------

class CustomerSegmentType(str, Enum):
    CHAMPIONS = "CHAMPIONS"
    GROWTH_POTENTIAL = "GROWTH_POTENTIAL"
    DISCOUNT_DEPENDENT = "DISCOUNT_DEPENDENT"
    AT_RISK = "AT_RISK"
    UNCLASSIFIED = "UNCLASSIFIED"


class CustomerSegmentProfile(BaseModel):
    """Segment assignment for a single customer."""
    customer_id: uuid.UUID
    customer_code: str
    customer_name: str
    segment: CustomerSegmentType
    segment_label: str
    badge_variant: str
    rationale: str
    ltv_amount: Decimal
    risk_level: str
    discount_sensitivity_level: str
    assigned_at: datetime = Field(default_factory=datetime.utcnow)


class SegmentDistributionItem(BaseModel):
    segment: CustomerSegmentType
    label: str
    count: int
    percentage: Decimal
    description: str


class CustomerSegmentationSummary(BaseModel):
    """Portfolio segmentation summary with itemized details."""
    total_evaluated: int
    distribution: List[SegmentDistributionItem]
    customers: List[CustomerSegmentProfile]
    calculated_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Phase 070: Customer Dashboard Schemas
# ---------------------------------------------------------------------------

class DashboardKpiSummary(BaseModel):
    total_customers: int
    active_customers: int
    portfolio_ltv: Decimal
    high_risk_customers_count: int
    active_deals_count: int
    settled_revenue: Decimal


class ChartDataPointResponse(BaseModel):
    label: str
    value: float
    color: Optional[str] = None


class CustomerDashboardResponse(BaseModel):
    """Consolidated customer dashboard data envelope."""
    kpis: DashboardKpiSummary
    tier_chart_data: List[ChartDataPointResponse]
    risk_chart_data: List[ChartDataPointResponse]
    segment_chart_data: List[ChartDataPointResponse]
    recent_activity_summary: Dict[str, int]
    analytics: CustomerAnalyticsSummary
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
