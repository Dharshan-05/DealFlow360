from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field

from app.models.deal_health import (
    DealHealthAlertSeverity,
    DealHealthAlertStatus,
    DealHealthAlertType,
    DealHealthClassification,
    DealHealthEscalationStatus,
    DealHealthNudgeStatus,
)


# ==============================================================================
# Feature Engineering Schemas (Phases 211–217)
# ==============================================================================

class DealLifecycleFeatures(BaseModel):
    deal_age_days: int
    days_in_current_stage: int
    stage_transition_count: int
    current_stage: str
    previous_stage: Optional[str] = None
    stage_progression_velocity: float
    days_since_quote_creation: Optional[int] = None
    days_since_quote_update: Optional[int] = None
    days_since_last_activity: int
    customer_relationship_age_days: int
    quote_to_deal_duration_days: Optional[int] = None
    is_active: bool


class TimeToCloseFeatures(BaseModel):
    historical_avg_time_to_close_days: float
    customer_historical_close_duration_days: float
    stage_specific_historical_duration_days: float
    current_deal_age_days: int
    expected_remaining_duration_days: float
    close_time_deviation_days: float
    time_to_close_risk_indicator: float


class ApprovalDelayFeatures(BaseModel):
    approval_request_count: int
    approval_step_count: int
    completed_approval_steps: int
    pending_approval_steps: int
    approval_turnaround_hours: float
    average_approval_delay_hours: float
    maximum_approval_delay_hours: float
    escalation_count: int
    timeout_count: int
    approval_rejection_count: int
    approval_revision_count: int
    current_approval_pending_duration_hours: float
    approval_bottleneck_indicator: bool


class NegotiationFeatures(BaseModel):
    negotiation_activity_count: int
    customer_change_requests_count: int
    quote_revision_count: int
    discount_counter_proposals_count: int
    days_since_last_negotiation: Optional[int] = None
    negotiation_frequency_score: float
    negotiation_duration_days: int
    discount_change_direction: str  # INCREASING, DECREASING, STABLE, NONE
    negotiation_intensity_score: float
    negotiation_risk_indicator: bool


class DiscountAnomalyFeatures(BaseModel):
    current_discount_pct: float
    historical_avg_discount_pct: float
    historical_median_discount_pct: float
    discount_deviation_from_avg: float
    discount_percentile: float
    category_ceiling_utilization_ratio: float
    customer_ceiling_utilization_ratio: float
    rep_baseline_deviation: float
    discount_anomaly_score: float  # 0 to 100
    is_discount_anomaly: bool


class DeliveryDelayFeatures(BaseModel):
    promised_delivery_date: Optional[datetime] = None
    expected_delivery_date: Optional[datetime] = None
    actual_delivery_date: Optional[datetime] = None
    delivery_delay_days: int
    delivery_delay_frequency: float
    is_partial_delivery: bool
    is_backordered: bool
    fulfillment_risk_indicator: bool
    delivery_slippage_score: float


class DealHealthFeatureVector(BaseModel):
    deal_id: uuid.UUID
    company_id: uuid.UUID
    lifecycle: DealLifecycleFeatures
    time_to_close: TimeToCloseFeatures
    approval_delay: ApprovalDelayFeatures
    negotiation: NegotiationFeatures
    discount_anomaly: DiscountAnomalyFeatures
    delivery_delay: DeliveryDelayFeatures
    feature_vector_dict: Dict[str, float]


# ==============================================================================
# Model & Probability Schemas (Phases 218–225)
# ==============================================================================

class DealHealthPredictionRequest(BaseModel):
    deal_id: uuid.UUID


class DealHealthPredictionResponse(BaseModel):
    deal_id: uuid.UUID
    health_score: float
    classification: DealHealthClassification
    conversion_probability: float
    conversion_percentage: float
    stall_probability: float
    stall_percentage: float
    stall_risk_level: str
    delay_probability: float
    delay_percentage: float
    delay_risk_level: str
    anomaly_detected: bool
    anomaly_score: float
    primary_risk_factors: List[str]
    positive_factors: List[str]
    model_version: str


class DealHealthTrainRequest(BaseModel):
    model_version: Optional[str] = "v1.0"
    random_state: int = 42


class DealHealthTrainResponse(BaseModel):
    model_version: str
    trained_at: datetime
    metrics: Dict[str, Any]
    feature_names: List[str]
    sample_count: int


class DealAnomalyDetailResponse(BaseModel):
    deal_id: uuid.UUID
    anomaly_detected: bool
    anomaly_score: float
    isolation_forest_score: float
    anomaly_type: Optional[str] = None
    anomalous_features: List[str]
    explanation: str


# ==============================================================================
# Alert, Recommendation, Nudge, Escalation Schemas (Phases 226–229)
# ==============================================================================

class DealHealthAlertCreate(BaseModel):
    deal_id: uuid.UUID
    alert_type: DealHealthAlertType
    severity: DealHealthAlertSeverity = DealHealthAlertSeverity.HIGH
    title: str
    description: str
    health_score: Decimal
    anomaly_score: Optional[Decimal] = None
    recommended_action: Optional[str] = None


class DealHealthAlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    deal_id: uuid.UUID
    alert_type: str
    severity: str
    title: str
    description: str
    health_score: float
    anomaly_score: Optional[float] = None
    recommended_action: Optional[str] = None
    status: str
    actor_id: Optional[uuid.UUID] = None
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


class DealHealthRecommendationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    deal_id: uuid.UUID
    recommendation_type: str
    priority: str
    title: str
    explanation: str
    triggering_signal: str
    suggested_action: str
    status: str
    created_at: datetime


class DealHealthNudgeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    deal_id: uuid.UUID
    nudge_type: str
    reason: str
    recipient_id: Optional[uuid.UUID] = None
    status: str
    actor_id: Optional[uuid.UUID] = None
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    dismissed_at: Optional[datetime] = None


class DealHealthEscalationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    deal_id: uuid.UUID
    current_health: str
    escalation_reason: str
    source_signal: str
    previous_authority_id: Optional[uuid.UUID] = None
    next_authority_id: Optional[uuid.UUID] = None
    status: str
    sla_expires_at: Optional[datetime] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None


# ==============================================================================
# Dashboard Schemas (Phase 230)
# ==============================================================================

class DealHealthSummaryCard(BaseModel):
    total_active_deals: int
    healthy_deals_count: int
    watch_deals_count: int
    at_risk_deals_count: int
    critical_deals_count: int
    avg_health_score: float
    avg_conversion_probability: float
    avg_stall_probability: float
    avg_delay_probability: float
    total_anomalies_count: int
    open_alerts_count: int
    unresolved_critical_alerts_count: int
    pending_nudges_count: int
    pending_escalations_count: int


class RankedDealHealthItem(BaseModel):
    deal_id: uuid.UUID
    deal_code: str
    title: str
    customer_name: str
    customer_tier: str
    sales_rep_name: Optional[str] = None
    deal_value: float
    stage: str
    health_score: float
    classification: str
    conversion_pct: float
    stall_pct: float
    delay_pct: float
    primary_risk: str
    created_at: datetime


class DealHealthDashboardResponse(BaseModel):
    summary: DealHealthSummaryCard
    health_distribution: Dict[str, int]
    trend_series: List[Dict[str, Any]]
    critical_deals: List[RankedDealHealthItem]
    at_risk_deals: List[RankedDealHealthItem]
    stalled_deals: List[RankedDealHealthItem]
    discount_anomalies: List[RankedDealHealthItem]
    approval_bottlenecks: List[RankedDealHealthItem]
    delivery_risks: List[RankedDealHealthItem]
    recommendations: List[DealHealthRecommendationResponse]
    open_alerts: List[DealHealthAlertResponse]
