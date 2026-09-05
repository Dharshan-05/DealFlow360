"""Approval Routing Schemas (DealFlow360 B05: Phases 146–155).

Defines strongly-typed schemas for:
- Phase 146: Approval Configuration (Tenant policy, hierarchy settings, active flags)
- Phase 147: Approval Levels (Tiered authority levels and definitions)
- Phase 148: Approval Chains (Sequential approval pathways and chains)
- Phase 149: Approval Thresholds (Boundary metrics and condition rules)
- Phase 150: Risk-Based Routing (AI risk probability and classification routing)
- Phase 151: Discount-Based Routing (Discount threshold and ceiling violation routing)
- Phase 152: Margin-Based Routing (Gross and post-discount margin profitability routing)
- Phase 153: Customer-Based Routing (Tenure, default ratio, and payment reliability routing)
- Phase 154: Deal-Value Routing (Deal size and monetary threshold routing)
- Phase 155: Blended Risk Score (Unified multi-dimensional risk synthesis and strict level preservation)

Zero sensitive credentials/tokens; Decimal-safe financial arithmetic.
Strict multi-tenant isolation.
"""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


# ==============================================================================
# Phase 147: Approval Levels
# ==============================================================================

class ApprovalLevel(str, Enum):
    """Deterministic hierarchy of approval authority levels (Phase 147).
    Rank order from lowest to highest:
    NO_APPROVAL_REQUIRED (0) < SALES_MANAGER (1) < FINANCE (2) < VP_SALES (3) < EXECUTIVE (4)
    """
    NO_APPROVAL_REQUIRED = "NO_APPROVAL_REQUIRED"
    SALES_MANAGER = "SALES_MANAGER"
    FINANCE = "FINANCE"
    VP_SALES = "VP_SALES"
    EXECUTIVE = "EXECUTIVE"


class ApprovalLevelDefinition(BaseModel):
    """Metadata describing an authority tier in the organization (Phase 147)."""
    model_config = ConfigDict(from_attributes=True)

    level: ApprovalLevel = Field(description="Authority level enum")
    rank: int = Field(description="Deterministic integer rank (higher = stricter authority)")
    display_name: str = Field(description="Human-readable title")
    description: str = Field(description="Scope of responsibility and typical sign-off domain")
    default_sla_hours: int = Field(default=24, description="Target decision SLA in hours")


# ==============================================================================
# Phase 148: Approval Chains
# ==============================================================================

class ApprovalChainType(str, Enum):
    """Named approval pathway types (Phase 148)."""
    AUTO_APPROVE = "AUTO_APPROVE"
    STANDARD_SALES = "STANDARD_SALES"
    FINANCE_REVIEW = "FINANCE_REVIEW"
    EXECUTIVE_EXCEPTION = "EXECUTIVE_EXCEPTION"
    COMPREHENSIVE_MULTI_TIER = "COMPREHENSIVE_MULTI_TIER"


class ApprovalChainStep(BaseModel):
    """Individual sequential step within an approval chain (Phase 148)."""
    model_config = ConfigDict(from_attributes=True)

    step_number: int = Field(description="Sequence position (1-indexed)", ge=1)
    level: ApprovalLevel = Field(description="Required approval level for this step")
    step_name: str = Field(description="Descriptive step name")
    required: bool = Field(default=True, description="Whether this step is mandatory in sequence")
    sla_hours: int = Field(default=24, description="SLA for this step in hours")


class ApprovalChainDefinition(BaseModel):
    """Complete structured definition of an approval chain (Phase 148)."""
    model_config = ConfigDict(from_attributes=True)

    chain_type: ApprovalChainType = Field(description="Unique chain type identifier")
    name: str = Field(description="Human-readable chain name")
    description: str = Field(description="Business scenario for which this chain is utilized")
    highest_level: ApprovalLevel = Field(description="Maximum authority level in this chain")
    steps: List[ApprovalChainStep] = Field(description="Ordered sequence of approval steps")


# ==============================================================================
# Phase 149: Approval Thresholds
# ==============================================================================

class ThresholdDimension(str, Enum):
    """Evaluation dimensions for threshold checking (Phase 149)."""
    AI_RISK_SCORE = "AI_RISK_SCORE"
    DISCOUNT_PERCENT = "DISCOUNT_PERCENT"
    MARGIN_PERCENT = "MARGIN_PERCENT"
    DEAL_VALUE = "DEAL_VALUE"
    PAYMENT_DEFAULT_RATIO = "PAYMENT_DEFAULT_RATIO"


class ComparisonOperator(str, Enum):
    """Safe comparison operators (Phase 149)."""
    GREATER_THAN = ">"
    GREATER_THAN_OR_EQUAL = ">="
    LESS_THAN = "<"
    LESS_THAN_OR_EQUAL = "<="
    EQUAL = "=="


class ApprovalThresholdRule(BaseModel):
    """Single boundary threshold rule mapping a dimension limit to a required level (Phase 149)."""
    model_config = ConfigDict(from_attributes=True)

    rule_id: str = Field(description="Unique rule identifier")
    dimension: ThresholdDimension = Field(description="Dimension being tested")
    operator: ComparisonOperator = Field(description="Comparison operator")
    threshold_value: float = Field(description="Boundary value")
    required_level: ApprovalLevel = Field(description="Minimum approval level required if triggered")
    description: str = Field(description="Human explanation of this threshold rule")


class ThresholdEvaluationResult(BaseModel):
    """Result of evaluating a specific metric against threshold rules (Phase 149)."""
    model_config = ConfigDict(from_attributes=True)

    dimension: ThresholdDimension = Field(description="Evaluated dimension")
    metric_value: float = Field(description="Observed input value")
    triggered: bool = Field(description="Whether a threshold condition was triggered")
    matched_rule_id: Optional[str] = Field(default=None, description="Triggered rule ID if any")
    required_level: ApprovalLevel = Field(default=ApprovalLevel.NO_APPROVAL_REQUIRED)
    explanation: str = Field(description="Deterministic explanation of threshold result")


# ==============================================================================
# Phase 150: Risk-Based Routing
# ==============================================================================

class RiskRoutingRequest(BaseModel):
    """Input payload for risk-based routing evaluation (Phase 150)."""
    model_config = ConfigDict(from_attributes=True)

    risk_score: float = Field(description="Calibrated AI Risk Score (0.0 - 100.0)", ge=0.0, le=100.0)
    risk_classification: str = Field(description="LOW, MEDIUM, HIGH, or CRITICAL")
    raw_probability: Optional[float] = Field(default=None, description="Calibrated risk probability [0.0, 1.0]", ge=0.0, le=1.0)
    primary_risk_factors: List[str] = Field(default_factory=list, description="Top risk-increasing factors")


class RiskRoutingEvaluation(BaseModel):
    """Outcome of risk-based routing evaluation (Phase 150)."""
    model_config = ConfigDict(from_attributes=True)

    dimension: str = Field(default="RISK_BASED")
    risk_score: float = Field(description="Observed risk score")
    risk_classification: str = Field(description="Classification tier")
    required_level: ApprovalLevel = Field(description="Level required by risk")
    recommended_chain: ApprovalChainType = Field(description="Recommended chain for risk")
    escalation_reason: str = Field(description="Business reason for risk routing decision")


# ==============================================================================
# Phase 151: Discount-Based Routing
# ==============================================================================

class DiscountRoutingRequest(BaseModel):
    """Input payload for discount-based routing evaluation (Phase 151)."""
    model_config = ConfigDict(from_attributes=True)

    requested_discount_pct: Decimal = Field(description="Proposed discount percentage", ge=Decimal("0.0"), le=Decimal("100.0"))
    rep_authorized_limit: Optional[Decimal] = Field(default=Decimal("10.0"), description="Sales rep max authorized discount %")
    customer_tier_ceiling: Optional[Decimal] = Field(default=Decimal("20.0"), description="Customer tier discount ceiling %")
    category_ceiling: Optional[Decimal] = Field(default=Decimal("25.0"), description="Product category discount ceiling %")
    company_max_ceiling: Optional[Decimal] = Field(default=Decimal("40.0"), description="Company-wide maximum discount %")


class DiscountRoutingEvaluation(BaseModel):
    """Outcome of discount-based routing evaluation (Phase 151)."""
    model_config = ConfigDict(from_attributes=True)

    dimension: str = Field(default="DISCOUNT_BASED")
    requested_discount_pct: Decimal = Field(description="Evaluated discount %")
    exceeds_rep_authority: bool = Field(description="Whether discount exceeds sales rep authority")
    exceeds_tier_ceiling: bool = Field(description="Whether discount exceeds customer tier ceiling")
    exceeds_category_ceiling: bool = Field(description="Whether discount exceeds product category ceiling")
    exceeds_company_ceiling: bool = Field(description="Whether discount exceeds company max ceiling")
    required_level: ApprovalLevel = Field(description="Level required by discount checks")
    recommended_chain: ApprovalChainType = Field(description="Recommended chain for discount")
    escalation_reason: str = Field(description="Business reason for discount routing decision")


# ==============================================================================
# Phase 152: Margin-Based Routing
# ==============================================================================

class MarginRoutingRequest(BaseModel):
    """Input payload for margin-based routing evaluation (Phase 152)."""
    model_config = ConfigDict(from_attributes=True)

    selling_price: Decimal = Field(description="Proposed unit selling price", ge=Decimal("0.0"))
    unit_cost: Decimal = Field(description="Unit cost of goods", ge=Decimal("0.0"))
    requested_discount_pct: Decimal = Field(default=Decimal("0.0"), description="Discount percentage", ge=Decimal("0.0"), le=Decimal("100.0"))
    min_acceptable_margin_pct: Decimal = Field(default=Decimal("20.0"), description="Company minimum target gross margin %")


class MarginRoutingEvaluation(BaseModel):
    """Outcome of margin-based routing evaluation (Phase 152)."""
    model_config = ConfigDict(from_attributes=True)

    dimension: str = Field(default="MARGIN_BASED")
    gross_margin_pct: Decimal = Field(description="Base gross margin percentage")
    discounted_margin_pct: Decimal = Field(description="Post-discount gross margin percentage")
    discounted_unit_price: Decimal = Field(description="Final unit price after discount")
    is_negative_margin: bool = Field(description="True if discounted price < unit cost")
    is_below_minimum_margin: bool = Field(description="True if margin < minimum acceptable target")
    required_level: ApprovalLevel = Field(description="Level required by margin health")
    recommended_chain: ApprovalChainType = Field(description="Recommended chain for margin")
    escalation_reason: str = Field(description="Business reason for margin routing decision")


# ==============================================================================
# Phase 153: Customer-Based Routing
# ==============================================================================

class CustomerRoutingRequest(BaseModel):
    """Input payload for customer-based routing evaluation (Phase 153)."""
    model_config = ConfigDict(from_attributes=True)

    customer_id: Optional[uuid.UUID] = Field(default=None, description="Optional customer ID for DB lookup")
    customer_tier: str = Field(default="STANDARD", description="Customer tier: BRONZE, SILVER, GOLD, PLATINUM, ENTERPRISE, STANDARD")
    tenure_days: int = Field(default=90, description="Customer relationship tenure in days", ge=0)
    payment_default_ratio: float = Field(default=0.0, description="Customer historical payment default ratio [0.0, 1.0]", ge=0.0, le=1.0)
    failed_payment_count: int = Field(default=0, description="Total recorded failed/overdue payments", ge=0)
    lifetime_deal_count: int = Field(default=3, description="Prior completed deal count", ge=0)


class CustomerRoutingEvaluation(BaseModel):
    """Outcome of customer-based routing evaluation (Phase 153)."""
    model_config = ConfigDict(from_attributes=True)

    dimension: str = Field(default="CUSTOMER_BASED")
    customer_tier: str = Field(description="Customer tier")
    payment_reliability_score: float = Field(description="Computed payment reliability score [0.0, 100.0]")
    is_delinquent_risk: bool = Field(description="True if payment default ratio or failed payments exceed risk thresholds")
    required_level: ApprovalLevel = Field(description="Level required by customer status")
    recommended_chain: ApprovalChainType = Field(description="Recommended chain for customer")
    escalation_reason: str = Field(description="Business reason for customer routing decision")


# ==============================================================================
# Phase 154: Deal-Value Routing
# ==============================================================================

class DealValueRoutingRequest(BaseModel):
    """Input payload for deal-value routing evaluation (Phase 154)."""
    model_config = ConfigDict(from_attributes=True)

    deal_value: Decimal = Field(description="Total proposed monetary deal value", ge=Decimal("0.0"))


class DealValueRoutingEvaluation(BaseModel):
    """Outcome of deal-value routing evaluation (Phase 154)."""
    model_config = ConfigDict(from_attributes=True)

    dimension: str = Field(default="DEAL_VALUE_BASED")
    deal_value: Decimal = Field(description="Evaluated total deal value")
    value_band: str = Field(description="Size category: MICRO, SMALL, MEDIUM, LARGE, ENTERPRISE")
    required_level: ApprovalLevel = Field(description="Level required by deal value")
    recommended_chain: ApprovalChainType = Field(description="Recommended chain for deal value")
    escalation_reason: str = Field(description="Business reason for deal value routing decision")


# ==============================================================================
# Phase 155: Blended Risk Score & Unified Routing
# ==============================================================================

class BlendedRiskWeights(BaseModel):
    """Configurable weights for the multi-dimensional blended risk score (Phase 155).
    Sum of weights equals 1.0.
    """
    model_config = ConfigDict(from_attributes=True)

    ai_risk_weight: float = Field(default=0.35, ge=0.0, le=1.0)
    discount_weight: float = Field(default=0.25, ge=0.0, le=1.0)
    margin_weight: float = Field(default=0.20, ge=0.0, le=1.0)
    customer_weight: float = Field(default=0.10, ge=0.0, le=1.0)
    deal_value_weight: float = Field(default=0.10, ge=0.0, le=1.0)


class BlendedRiskComponentScore(BaseModel):
    """Normalized sub-score for each evaluation dimension (Phase 155)."""
    model_config = ConfigDict(from_attributes=True)

    dimension: str = Field(description="Dimension name")
    raw_metric: str = Field(description="Raw human-readable metric string")
    normalized_score: float = Field(description="Normalized component score [0.0, 100.0]", ge=0.0, le=100.0)
    weight: float = Field(description="Weight assigned to this dimension")
    weighted_contribution: float = Field(description="Calculated score contribution to total blended score")
    triggered_level: ApprovalLevel = Field(description="Level triggered specifically by this dimension")


class BlendedRiskScoreResult(BaseModel):
    """Synthesized blended risk score and strict preserved approval authority (Phase 155)."""
    model_config = ConfigDict(from_attributes=True)

    blended_risk_score: float = Field(description="Consolidated scalar risk score [0.0, 100.0]", ge=0.0, le=100.0)
    blended_risk_classification: str = Field(description="LOW, MEDIUM, HIGH, or CRITICAL")
    strictest_required_level: ApprovalLevel = Field(description="Strictest approval level preserved across all dimensions")
    strictest_level_rank: int = Field(description="Deterministic integer rank of strictest level")
    selected_approval_chain: ApprovalChainType = Field(description="Approval chain corresponding to strictest level")
    component_breakdown: List[BlendedRiskComponentScore] = Field(description="Detailed dimension-by-dimension breakdown")
    primary_escalation_driver: str = Field(description="The single most authoritative dimension driving the escalation")
    evaluation_summary: str = Field(description="Executive summary of the routing determination")


class ComprehensiveApprovalEvaluationRequest(BaseModel):
    """Complete deal payload for multi-dimensional approval routing evaluation (Phases 146–155)."""
    model_config = ConfigDict(from_attributes=True)

    deal_reference: Optional[str] = Field(default=None, description="Deal reference code")
    deal_value: Decimal = Field(description="Total deal monetary value", ge=Decimal("0.0"))
    selling_price: Decimal = Field(description="Unit selling price", ge=Decimal("0.0"))
    unit_cost: Decimal = Field(description="Unit cost", ge=Decimal("0.0"))
    requested_discount_pct: Decimal = Field(description="Proposed discount percentage", ge=Decimal("0.0"), le=Decimal("100.0"))
    customer_id: Optional[uuid.UUID] = Field(default=None, description="Customer ID")
    customer_tier: str = Field(default="STANDARD", description="Customer tier")
    customer_tenure_days: int = Field(default=90, description="Customer tenure in days", ge=0)
    payment_default_ratio: float = Field(default=0.0, description="Payment default ratio", ge=0.0, le=1.0)
    failed_payment_count: int = Field(default=0, description="Failed payment count", ge=0)
    ai_risk_score: Optional[float] = Field(default=None, description="Pre-computed AI Risk Score [0-100], or auto-inferred if omitted")
    ai_risk_classification: Optional[str] = Field(default=None, description="Pre-computed risk classification")


class ComprehensiveApprovalEvaluationResponse(BaseModel):
    """Complete evaluation response containing all dimension evaluations and the blended resolution (Phase 155)."""
    model_config = ConfigDict(from_attributes=True)

    evaluation_id: str = Field(description="Unique evaluation execution identifier")
    company_id: uuid.UUID = Field(description="Tenant ID")
    deal_reference: Optional[str] = Field(default=None, description="Deal reference")
    evaluated_at: datetime = Field(description="Evaluation timestamp")
    risk_evaluation: RiskRoutingEvaluation = Field(description="Phase 150 Risk-based evaluation")
    discount_evaluation: DiscountRoutingEvaluation = Field(description="Phase 151 Discount-based evaluation")
    margin_evaluation: MarginRoutingEvaluation = Field(description="Phase 152 Margin-based evaluation")
    customer_evaluation: CustomerRoutingEvaluation = Field(description="Phase 153 Customer-based evaluation")
    deal_value_evaluation: DealValueRoutingEvaluation = Field(description="Phase 154 Deal-value evaluation")
    blended_result: BlendedRiskScoreResult = Field(description="Phase 155 Blended synthesis and final preserved chain")
    final_required_level: ApprovalLevel = Field(description="Final binding authority required")
    final_approval_chain: ApprovalChainDefinition = Field(description="Binding approval chain with concrete steps")


# ==============================================================================
# Phase 146: Approval Policy Configuration Schemas
# ==============================================================================

class ApprovalPolicyCreate(BaseModel):
    """Payload for creating or updating an approval policy (Phase 146)."""
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(description="Policy name", max_length=100)
    description: Optional[str] = Field(default=None, description="Policy description", max_length=255)
    is_active: bool = Field(default=True, description="Whether policy is active")
    is_default: bool = Field(default=False, description="Whether policy is the company default")
    levels_config: Optional[List[ApprovalLevelDefinition]] = Field(default=None, description="Custom levels configuration")
    chains_config: Optional[List[ApprovalChainDefinition]] = Field(default=None, description="Custom chains configuration")
    thresholds_config: Optional[List[ApprovalThresholdRule]] = Field(default=None, description="Custom thresholds configuration")


class ApprovalPolicyUpdate(BaseModel):
    """Payload for updating an existing approval policy (Phase 146)."""
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, max_length=255)
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    levels_config: Optional[List[ApprovalLevelDefinition]] = None
    chains_config: Optional[List[ApprovalChainDefinition]] = None
    thresholds_config: Optional[List[ApprovalThresholdRule]] = None


class ApprovalPolicyResponse(BaseModel):
    """Response model for approval policy metadata (Phase 146)."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Policy identifier")
    company_id: uuid.UUID = Field(description="Tenant identifier")
    name: str = Field(description="Policy name")
    description: Optional[str] = Field(default=None, description="Policy description")
    is_active: bool = Field(description="Active status")
    is_default: bool = Field(description="Default status")
    levels_config: List[Dict[str, Any]] = Field(description="Configured levels")
    chains_config: List[Dict[str, Any]] = Field(description="Configured chains")
    thresholds_config: Dict[str, Any] = Field(description="Configured thresholds")
    effective_from: datetime = Field(description="Effective start timestamp")
    effective_until: Optional[datetime] = Field(default=None, description="Effective end timestamp")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Update timestamp")
