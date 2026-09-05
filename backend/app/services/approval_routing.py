"""Approval Routing Services (DealFlow360 B05: Phases 146–155).

Implements the complete approval routing foundation:
- Phase 146: Approval Configuration (Tenant policy management & defaults)
- Phase 147: Approval Levels (Deterministic hierarchy & rank comparisons)
- Phase 148: Approval Chains (Chain topology, step sequencing, chain selection)
- Phase 149: Approval Thresholds (Boundary evaluation engine with safe comparison operators)
- Phase 150: Risk-Based Routing (ML Risk Engine inference evaluation)
- Phase 151: Discount-Based Routing (Sales rep authority, customer tier ceiling, category ceiling)
- Phase 152: Margin-Based Routing (Decimal gross margin & post-discount margin analysis)
- Phase 153: Customer-Based Routing (Payment reliability, delinquency risk, tenure evaluation)
- Phase 154: Deal-Value Routing (Monetary deal size threshold routing)
- Phase 155: Blended Risk Score (Composite scoring & strict preservation of maximum required level)

Strictly non-workflow-execution: outputs authoritative routing decisions and required chains.
"""
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import math
from typing import Any, Dict, List, Optional, Tuple
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ApplicationError
from app.models.approval_policy import ApprovalPolicy
from app.models.company import Company
from app.models.customer import Customer
from app.models.customer_payment_history import CustomerPaymentHistory
from app.models.customer_tier import CustomerTier
from app.models.customer_discount_ceiling import CustomerDiscountCeiling
from app.models.category_discount_ceiling import CategoryDiscountCeiling
from app.models.discount_configuration import DiscountConfiguration
from app.models.sales_rep_authority_limit import SalesRepAuthorityLimit
from app.models.user import User
from app.schemas.approval_routing import (
    ApprovalChainDefinition,
    ApprovalChainStep,
    ApprovalChainType,
    ApprovalLevel,
    ApprovalLevelDefinition,
    ApprovalPolicyCreate,
    ApprovalPolicyResponse,
    ApprovalPolicyUpdate,
    ApprovalThresholdRule,
    BlendedRiskComponentScore,
    BlendedRiskScoreResult,
    BlendedRiskWeights,
    ComparisonOperator,
    ComprehensiveApprovalEvaluationRequest,
    ComprehensiveApprovalEvaluationResponse,
    CustomerRoutingEvaluation,
    CustomerRoutingRequest,
    DealValueRoutingEvaluation,
    DealValueRoutingRequest,
    DiscountRoutingEvaluation,
    DiscountRoutingRequest,
    MarginRoutingEvaluation,
    MarginRoutingRequest,
    RiskRoutingEvaluation,
    RiskRoutingRequest,
    ThresholdDimension,
    ThresholdEvaluationResult,
)
from app.schemas.ml_risk import RiskPredictionRequest, RiskScoreCategory
from app.services.ml_risk import RiskPredictionInferenceService


# ==============================================================================
# Phase 147: Approval Levels Service
# ==============================================================================

class ApprovalLevelHierarchyService:
    """Service governing authority levels, rank ordering, and level comparisons (Phase 147)."""

    LEVEL_ORDER: Dict[ApprovalLevel, int] = {
        ApprovalLevel.NO_APPROVAL_REQUIRED: 0,
        ApprovalLevel.SALES_MANAGER: 1,
        ApprovalLevel.FINANCE: 2,
        ApprovalLevel.VP_SALES: 3,
        ApprovalLevel.EXECUTIVE: 4,
    }

    LEVEL_DEFINITIONS: List[ApprovalLevelDefinition] = [
        ApprovalLevelDefinition(
            level=ApprovalLevel.NO_APPROVAL_REQUIRED,
            rank=0,
            display_name="Direct Sale / Auto-Approval",
            description="Deals adhering strictly to pre-approved parameters with zero policy or margin infractions.",
            default_sla_hours=0,
        ),
        ApprovalLevelDefinition(
            level=ApprovalLevel.SALES_MANAGER,
            rank=1,
            display_name="Sales Management",
            description="First-line commercial authority for standard discretionary discounts and moderate deal sizes.",
            default_sla_hours=12,
        ),
        ApprovalLevelDefinition(
            level=ApprovalLevel.FINANCE,
            rank=2,
            display_name="Finance & Pricing Operations",
            description="Fiscal authority for margin compression, non-standard terms, or credit delinquency review.",
            default_sla_hours=24,
        ),
        ApprovalLevelDefinition(
            level=ApprovalLevel.VP_SALES,
            rank=3,
            display_name="Vice President of Sales",
            description="Executive commercial authority for high-value strategic deals and substantial discount exceptions.",
            default_sla_hours=36,
        ),
        ApprovalLevelDefinition(
            level=ApprovalLevel.EXECUTIVE,
            rank=4,
            display_name="Executive Leadership / Board",
            description="Highest governance tier for critical risk, negative margin, or enterprise commitments exceeding corporate limits.",
            default_sla_hours=48,
        ),
    ]

    @classmethod
    def get_rank(cls, level: ApprovalLevel) -> int:
        """Return the deterministic integer rank for an approval level."""
        return cls.LEVEL_ORDER.get(level, 0)

    @classmethod
    def get_strictest_level(cls, levels: List[ApprovalLevel]) -> ApprovalLevel:
        """Deterministically return the highest authority level required among a candidate list."""
        if not levels:
            return ApprovalLevel.NO_APPROVAL_REQUIRED
        return max(levels, key=lambda l: cls.get_rank(l))

    @classmethod
    def get_definitions(cls) -> List[ApprovalLevelDefinition]:
        """Return the standard hierarchy definitions."""
        return cls.LEVEL_DEFINITIONS


# ==============================================================================
# Phase 148: Approval Chains Service
# ==============================================================================

class ApprovalChainService:
    """Service governing named approval chains, step sequencing, and chain selection (Phase 148)."""

    DEFAULT_CHAINS: Dict[ApprovalChainType, ApprovalChainDefinition] = {
        ApprovalChainType.AUTO_APPROVE: ApprovalChainDefinition(
            chain_type=ApprovalChainType.AUTO_APPROVE,
            name="Instant Auto-Approval Pathway",
            description="Direct execution path for low-risk, compliant deals requiring no manual intervention.",
            highest_level=ApprovalLevel.NO_APPROVAL_REQUIRED,
            steps=[],
        ),
        ApprovalChainType.STANDARD_SALES: ApprovalChainDefinition(
            chain_type=ApprovalChainType.STANDARD_SALES,
            name="Standard Sales Management Chain",
            description="Single-step escalation to Sales Manager for routine discount or medium size approvals.",
            highest_level=ApprovalLevel.SALES_MANAGER,
            steps=[
                ApprovalChainStep(
                    step_number=1,
                    level=ApprovalLevel.SALES_MANAGER,
                    step_name="Sales Manager Commercial Review",
                    required=True,
                    sla_hours=12,
                )
            ],
        ),
        ApprovalChainType.FINANCE_REVIEW: ApprovalChainDefinition(
            chain_type=ApprovalChainType.FINANCE_REVIEW,
            name="Financial Governance & Margin Review Chain",
            description="Two-step sequential review: Sales Manager commercial endorsement followed by Finance fiscal sign-off.",
            highest_level=ApprovalLevel.FINANCE,
            steps=[
                ApprovalChainStep(
                    step_number=1,
                    level=ApprovalLevel.SALES_MANAGER,
                    step_name="Sales Manager Endorsement",
                    required=True,
                    sla_hours=12,
                ),
                ApprovalChainStep(
                    step_number=2,
                    level=ApprovalLevel.FINANCE,
                    step_name="Finance Fiscal & Margin Verification",
                    required=True,
                    sla_hours=24,
                ),
            ],
        ),
        ApprovalChainType.EXECUTIVE_EXCEPTION: ApprovalChainDefinition(
            chain_type=ApprovalChainType.EXECUTIVE_EXCEPTION,
            name="Executive Leadership Strategic Review Chain",
            description="Accelerated executive review for critical risk, negative margin, or enterprise commitments.",
            highest_level=ApprovalLevel.EXECUTIVE,
            steps=[
                ApprovalChainStep(
                    step_number=1,
                    level=ApprovalLevel.FINANCE,
                    step_name="Finance Controller Audit",
                    required=True,
                    sla_hours=12,
                ),
                ApprovalChainStep(
                    step_number=2,
                    level=ApprovalLevel.EXECUTIVE,
                    step_name="Executive / CFO Sign-Off",
                    required=True,
                    sla_hours=24,
                ),
            ],
        ),
        ApprovalChainType.COMPREHENSIVE_MULTI_TIER: ApprovalChainDefinition(
            chain_type=ApprovalChainType.COMPREHENSIVE_MULTI_TIER,
            name="Comprehensive Multi-Tier Governance Chain",
            description="Full sequential audit traversing Sales Manager -> Finance -> VP Sales -> Executive.",
            highest_level=ApprovalLevel.EXECUTIVE,
            steps=[
                ApprovalChainStep(
                    step_number=1,
                    level=ApprovalLevel.SALES_MANAGER,
                    step_name="Sales Manager Validation",
                    required=True,
                    sla_hours=12,
                ),
                ApprovalChainStep(
                    step_number=2,
                    level=ApprovalLevel.FINANCE,
                    step_name="Finance Risk Assessment",
                    required=True,
                    sla_hours=24,
                ),
                ApprovalChainStep(
                    step_number=3,
                    level=ApprovalLevel.VP_SALES,
                    step_name="VP Sales Commercial Concurrence",
                    required=True,
                    sla_hours=24,
                ),
                ApprovalChainStep(
                    step_number=4,
                    level=ApprovalLevel.EXECUTIVE,
                    step_name="Executive Leadership Authorization",
                    required=True,
                    sla_hours=24,
                ),
            ],
        ),
    }

    @classmethod
    def get_chain_for_level(cls, target_level: ApprovalLevel) -> ApprovalChainDefinition:
        """Select the appropriate standard chain capable of fulfilling the required authority level."""
        if target_level == ApprovalLevel.NO_APPROVAL_REQUIRED:
            return cls.DEFAULT_CHAINS[ApprovalChainType.AUTO_APPROVE]
        elif target_level == ApprovalLevel.SALES_MANAGER:
            return cls.DEFAULT_CHAINS[ApprovalChainType.STANDARD_SALES]
        elif target_level == ApprovalLevel.FINANCE:
            return cls.DEFAULT_CHAINS[ApprovalChainType.FINANCE_REVIEW]
        elif target_level == ApprovalLevel.VP_SALES:
            return cls.DEFAULT_CHAINS[ApprovalChainType.COMPREHENSIVE_MULTI_TIER]
        elif target_level == ApprovalLevel.EXECUTIVE:
            return cls.DEFAULT_CHAINS[ApprovalChainType.EXECUTIVE_EXCEPTION]
        return cls.DEFAULT_CHAINS[ApprovalChainType.STANDARD_SALES]

    @classmethod
    def get_all_chains(cls) -> List[ApprovalChainDefinition]:
        """Return all standard registered approval chains."""
        return list(cls.DEFAULT_CHAINS.values())


# ==============================================================================
# Phase 149: Approval Thresholds Service
# ==============================================================================

class ApprovalThresholdService:
    """Service evaluating numeric boundary limits and mapping infractions to required levels (Phase 149)."""

    DEFAULT_RULES: List[ApprovalThresholdRule] = [
        ApprovalThresholdRule(
            rule_id="RULE-RISK-CRITICAL",
            dimension=ThresholdDimension.AI_RISK_SCORE,
            operator=ComparisonOperator.GREATER_THAN_OR_EQUAL,
            threshold_value=85.0,
            required_level=ApprovalLevel.EXECUTIVE,
            description="AI Risk Score >= 85 warrants Executive sign-off.",
        ),
        ApprovalThresholdRule(
            rule_id="RULE-RISK-HIGH",
            dimension=ThresholdDimension.AI_RISK_SCORE,
            operator=ComparisonOperator.GREATER_THAN_OR_EQUAL,
            threshold_value=60.0,
            required_level=ApprovalLevel.FINANCE,
            description="AI Risk Score >= 60 warrants Finance review.",
        ),
        ApprovalThresholdRule(
            rule_id="RULE-RISK-MEDIUM",
            dimension=ThresholdDimension.AI_RISK_SCORE,
            operator=ComparisonOperator.GREATER_THAN_OR_EQUAL,
            threshold_value=30.0,
            required_level=ApprovalLevel.SALES_MANAGER,
            description="AI Risk Score >= 30 warrants Sales Manager approval.",
        ),
        ApprovalThresholdRule(
            rule_id="RULE-DISC-EXEC",
            dimension=ThresholdDimension.DISCOUNT_PERCENT,
            operator=ComparisonOperator.GREATER_THAN,
            threshold_value=30.0,
            required_level=ApprovalLevel.EXECUTIVE,
            description="Discounts > 30% require Executive authorization.",
        ),
        ApprovalThresholdRule(
            rule_id="RULE-DISC-VP",
            dimension=ThresholdDimension.DISCOUNT_PERCENT,
            operator=ComparisonOperator.GREATER_THAN,
            threshold_value=20.0,
            required_level=ApprovalLevel.VP_SALES,
            description="Discounts > 20% require VP of Sales sign-off.",
        ),
        ApprovalThresholdRule(
            rule_id="RULE-DISC-MGR",
            dimension=ThresholdDimension.DISCOUNT_PERCENT,
            operator=ComparisonOperator.GREATER_THAN,
            threshold_value=10.0,
            required_level=ApprovalLevel.SALES_MANAGER,
            description="Discounts > 10% require Sales Manager review.",
        ),
        ApprovalThresholdRule(
            rule_id="RULE-MARGIN-NEG",
            dimension=ThresholdDimension.MARGIN_PERCENT,
            operator=ComparisonOperator.LESS_THAN_OR_EQUAL,
            threshold_value=0.0,
            required_level=ApprovalLevel.EXECUTIVE,
            description="Negative or break-even margin requires Executive approval.",
        ),
        ApprovalThresholdRule(
            rule_id="RULE-MARGIN-LOW",
            dimension=ThresholdDimension.MARGIN_PERCENT,
            operator=ComparisonOperator.LESS_THAN,
            threshold_value=15.0,
            required_level=ApprovalLevel.FINANCE,
            description="Gross margins under 15% require Finance pricing sign-off.",
        ),
        ApprovalThresholdRule(
            rule_id="RULE-VAL-ENT",
            dimension=ThresholdDimension.DEAL_VALUE,
            operator=ComparisonOperator.GREATER_THAN_OR_EQUAL,
            threshold_value=250000.0,
            required_level=ApprovalLevel.EXECUTIVE,
            description="Enterprise commitments >= $250,000 require Executive authorization.",
        ),
        ApprovalThresholdRule(
            rule_id="RULE-VAL-LARGE",
            dimension=ThresholdDimension.DEAL_VALUE,
            operator=ComparisonOperator.GREATER_THAN_OR_EQUAL,
            threshold_value=50000.0,
            required_level=ApprovalLevel.VP_SALES,
            description="Large deals >= $50,000 require VP of Sales sign-off.",
        ),
        ApprovalThresholdRule(
            rule_id="RULE-VAL-MED",
            dimension=ThresholdDimension.DEAL_VALUE,
            operator=ComparisonOperator.GREATER_THAN_OR_EQUAL,
            threshold_value=10000.0,
            required_level=ApprovalLevel.SALES_MANAGER,
            description="Mid-market deals >= $10,000 require Sales Manager approval.",
        ),
        ApprovalThresholdRule(
            rule_id="RULE-DEFAULT-HIGH",
            dimension=ThresholdDimension.PAYMENT_DEFAULT_RATIO,
            operator=ComparisonOperator.GREATER_THAN,
            threshold_value=0.25,
            required_level=ApprovalLevel.FINANCE,
            description="Customer payment default ratio > 25% requires Finance review.",
        ),
    ]

    @classmethod
    def evaluate_dimension(
        cls,
        dimension: ThresholdDimension,
        value: float,
        rules: Optional[List[ApprovalThresholdRule]] = None,
    ) -> ThresholdEvaluationResult:
        """Evaluate a scalar value against threshold rules for the dimension."""
        active_rules = rules or cls.DEFAULT_RULES
        matched_rules: List[ApprovalThresholdRule] = []

        for rule in active_rules:
            if rule.dimension != dimension:
                continue

            v = float(value)
            tv = float(rule.threshold_value)
            triggered = False

            if rule.operator == ComparisonOperator.GREATER_THAN and v > tv:
                triggered = True
            elif rule.operator == ComparisonOperator.GREATER_THAN_OR_EQUAL and v >= tv:
                triggered = True
            elif rule.operator == ComparisonOperator.LESS_THAN and v < tv:
                triggered = True
            elif rule.operator == ComparisonOperator.LESS_THAN_OR_EQUAL and v <= tv:
                triggered = True
            elif rule.operator == ComparisonOperator.EQUAL and math.isclose(v, tv, rel_tol=1e-5):
                triggered = True

            if triggered:
                matched_rules.append(rule)

        if not matched_rules:
            return ThresholdEvaluationResult(
                dimension=dimension,
                metric_value=value,
                triggered=False,
                matched_rule_id=None,
                required_level=ApprovalLevel.NO_APPROVAL_REQUIRED,
                explanation=f"Value {value} is within normal thresholds for {dimension.value}.",
            )

        # Choose the strictest matched rule
        strictest = max(
            matched_rules,
            key=lambda r: ApprovalLevelHierarchyService.get_rank(r.required_level),
        )

        return ThresholdEvaluationResult(
            dimension=dimension,
            metric_value=value,
            triggered=True,
            matched_rule_id=strictest.rule_id,
            required_level=strictest.required_level,
            explanation=f"Triggered {strictest.rule_id}: {strictest.description}",
        )


# ==============================================================================
# Phase 150: Risk-Based Routing Service
# ==============================================================================

class RiskBasedRoutingService:
    """Service evaluating deals against AI Risk predictions (Phase 150)."""

    @classmethod
    def evaluate(cls, request: RiskRoutingRequest) -> RiskRoutingEvaluation:
        score = float(request.risk_score)
        classification = request.risk_classification.upper()

        if classification == "CRITICAL" or score >= 85.0:
            level = ApprovalLevel.EXECUTIVE
            chain = ApprovalChainType.EXECUTIVE_EXCEPTION
            reason = f"CRITICAL AI Risk Score ({score:.1f}/100) requires Executive authorization."
        elif classification == "HIGH" or score >= 60.0:
            level = ApprovalLevel.FINANCE
            chain = ApprovalChainType.FINANCE_REVIEW
            reason = f"HIGH AI Risk Score ({score:.1f}/100) requires Finance fiscal assessment."
        elif classification == "MEDIUM" or score >= 30.0:
            level = ApprovalLevel.SALES_MANAGER
            chain = ApprovalChainType.STANDARD_SALES
            reason = f"MEDIUM AI Risk Score ({score:.1f}/100) requires Sales Manager approval."
        else:
            level = ApprovalLevel.NO_APPROVAL_REQUIRED
            chain = ApprovalChainType.AUTO_APPROVE
            reason = f"LOW AI Risk Score ({score:.1f}/100) qualifies for automated routing."

        return RiskRoutingEvaluation(
            dimension="RISK_BASED",
            risk_score=score,
            risk_classification=classification,
            required_level=level,
            recommended_chain=chain,
            escalation_reason=reason,
        )


# ==============================================================================
# Phase 151: Discount-Based Routing Service
# ==============================================================================

class DiscountBasedRoutingService:
    """Service evaluating discount limits, authority ceilings, and escalation paths (Phase 151)."""

    @classmethod
    def evaluate(
        cls,
        request: DiscountRoutingRequest,
        db: Optional[Session] = None,
        company_id: Optional[uuid.UUID] = None,
    ) -> DiscountRoutingEvaluation:
        disc = request.requested_discount_pct
        rep_limit = request.rep_authorized_limit or Decimal("10.0")
        tier_ceiling = request.customer_tier_ceiling or Decimal("20.0")
        cat_ceiling = request.category_ceiling or Decimal("25.0")
        company_max = request.company_max_ceiling or Decimal("40.0")

        exceeds_rep = disc > rep_limit
        exceeds_tier = disc > tier_ceiling
        exceeds_cat = disc > cat_ceiling
        exceeds_company = disc > company_max

        if exceeds_company or disc > Decimal("30.0"):
            level = ApprovalLevel.EXECUTIVE
            chain = ApprovalChainType.EXECUTIVE_EXCEPTION
            reason = f"Requested discount {disc:.2f}% exceeds executive threshold or company ceiling ({company_max:.2f}%)."
        elif exceeds_cat or disc > Decimal("20.0"):
            level = ApprovalLevel.VP_SALES
            chain = ApprovalChainType.COMPREHENSIVE_MULTI_TIER
            reason = f"Requested discount {disc:.2f}% exceeds VP/category threshold ({cat_ceiling:.2f}%)."
        elif exceeds_tier or disc > Decimal("15.0"):
            level = ApprovalLevel.FINANCE
            chain = ApprovalChainType.FINANCE_REVIEW
            reason = f"Requested discount {disc:.2f}% exceeds customer tier ceiling ({tier_ceiling:.2f}%)."
        elif exceeds_rep:
            level = ApprovalLevel.SALES_MANAGER
            chain = ApprovalChainType.STANDARD_SALES
            reason = f"Requested discount {disc:.2f}% exceeds Sales Rep authorized limit ({rep_limit:.2f}%)."
        else:
            level = ApprovalLevel.NO_APPROVAL_REQUIRED
            chain = ApprovalChainType.AUTO_APPROVE
            reason = f"Requested discount {disc:.2f}% is within Sales Rep authorized threshold ({rep_limit:.2f}%)."

        return DiscountRoutingEvaluation(
            dimension="DISCOUNT_BASED",
            requested_discount_pct=disc,
            exceeds_rep_authority=exceeds_rep,
            exceeds_tier_ceiling=exceeds_tier,
            exceeds_category_ceiling=exceeds_cat,
            exceeds_company_ceiling=exceeds_company,
            required_level=level,
            recommended_chain=chain,
            escalation_reason=reason,
        )


# ==============================================================================
# Phase 152: Margin-Based Routing Service
# ==============================================================================

class MarginBasedRoutingService:
    """Service evaluating deal profitability, gross margin, and margin compression (Phase 152)."""

    @classmethod
    def evaluate(cls, request: MarginRoutingRequest) -> MarginRoutingEvaluation:
        price = request.selling_price
        cost = request.unit_cost
        disc = request.requested_discount_pct
        min_margin = request.min_acceptable_margin_pct

        # Calculate discounted unit price
        discount_factor = Decimal("1.0") - (disc / Decimal("100.0"))
        discounted_price = (price * discount_factor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Handle zero selling price or negative margin
        if price <= Decimal("0.0") or discounted_price < cost:
            gross_margin = Decimal("0.0") if price <= Decimal("0.0") else ((price - cost) / price * Decimal("100.0")).quantize(Decimal("0.01"))
            discounted_margin = Decimal("-100.0") if discounted_price <= Decimal("0.0") else (((discounted_price - cost) / discounted_price) * Decimal("100.0")).quantize(Decimal("0.01"))
            return MarginRoutingEvaluation(
                dimension="MARGIN_BASED",
                gross_margin_pct=gross_margin,
                discounted_margin_pct=discounted_margin,
                discounted_unit_price=discounted_price,
                is_negative_margin=True,
                is_below_minimum_margin=True,
                required_level=ApprovalLevel.EXECUTIVE,
                recommended_chain=ApprovalChainType.EXECUTIVE_EXCEPTION,
                escalation_reason=f"CRITICAL: Proposed terms yield negative margin (price: {discounted_price:.2f}, cost: {cost:.2f}).",
            )

        # Standard margin calculations
        gross_margin = ((price - cost) / price * Decimal("100.0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        discounted_margin = ((discounted_price - cost) / discounted_price * Decimal("100.0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        is_below_min = discounted_margin < min_margin

        if discounted_margin <= Decimal("5.0"):
            level = ApprovalLevel.EXECUTIVE
            chain = ApprovalChainType.EXECUTIVE_EXCEPTION
            reason = f"Extreme margin compression: post-discount margin {discounted_margin:.2f}% is at or below 5%."
        elif discounted_margin < Decimal("15.0") or is_below_min:
            level = ApprovalLevel.FINANCE
            chain = ApprovalChainType.FINANCE_REVIEW
            reason = f"Thin margin: post-discount margin {discounted_margin:.2f}% is below minimum target ({min_margin:.2f}%)."
        elif discounted_margin < Decimal("25.0"):
            level = ApprovalLevel.SALES_MANAGER
            chain = ApprovalChainType.STANDARD_SALES
            reason = f"Moderate margin compression: post-discount margin {discounted_margin:.2f}% requires Sales Manager review."
        else:
            level = ApprovalLevel.NO_APPROVAL_REQUIRED
            chain = ApprovalChainType.AUTO_APPROVE
            reason = f"Healthy margin: post-discount margin {discounted_margin:.2f}% exceeds target threshold."

        return MarginRoutingEvaluation(
            dimension="MARGIN_BASED",
            gross_margin_pct=gross_margin,
            discounted_margin_pct=discounted_margin,
            discounted_unit_price=discounted_price,
            is_negative_margin=False,
            is_below_minimum_margin=is_below_min,
            required_level=level,
            recommended_chain=chain,
            escalation_reason=reason,
        )


# ==============================================================================
# Phase 153: Customer-Based Routing Service
# ==============================================================================

class CustomerBasedRoutingService:
    """Service evaluating customer profile, payment reliability, and credit risk (Phase 153)."""

    @classmethod
    def evaluate(
        cls,
        request: CustomerRoutingRequest,
        db: Optional[Session] = None,
        company_id: Optional[uuid.UUID] = None,
    ) -> CustomerRoutingEvaluation:
        tier = request.customer_tier.upper()
        tenure = request.tenure_days
        default_ratio = request.payment_default_ratio
        failed_count = request.failed_payment_count

        # If customer_id provided and db available, query real customer profile
        if request.customer_id and db and company_id:
            cust = db.execute(
                select(Customer).where(
                    Customer.id == request.customer_id,
                    Customer.company_id == company_id,
                )
            ).scalar_one_or_none()
            if cust and cust.tier:
                tier = cust.tier.name.upper()

            # Query payment history for defaults
            payments = db.execute(
                select(CustomerPaymentHistory).where(
                    CustomerPaymentHistory.customer_id == request.customer_id
                )
            ).scalars().all()
            if payments:
                total_p = len(payments)
                failed_p = sum(1 for p in payments if p.payment_status in ("FAILED", "OVERDUE"))
                failed_count = failed_p
                default_ratio = (failed_p / total_p) if total_p > 0 else 0.0

        # Compute Payment Reliability Score [0.0 - 100.0]
        # 100 = perfect, drops with default ratio and failed count
        base_score = 100.0 - (default_ratio * 70.0) - (min(failed_count, 6) * 5.0)
        if tenure < 30:
            base_score -= 10.0  # New customer penalty
        reliability_score = max(0.0, min(100.0, round(base_score, 1)))

        is_delinquent = default_ratio >= 0.20 or failed_count >= 2

        if default_ratio >= 0.35 or failed_count >= 4:
            level = ApprovalLevel.EXECUTIVE
            chain = ApprovalChainType.EXECUTIVE_EXCEPTION
            reason = f"High credit risk: customer default ratio {default_ratio:.1%} with {failed_count} payment failures."
        elif is_delinquent or reliability_score < 60.0:
            level = ApprovalLevel.FINANCE
            chain = ApprovalChainType.FINANCE_REVIEW
            reason = f"Delinquency risk: customer reliability score ({reliability_score:.1f}) requires Finance review."
        elif tenure < 60 or tier in ("BRONZE", "STANDARD"):
            level = ApprovalLevel.SALES_MANAGER
            chain = ApprovalChainType.STANDARD_SALES
            reason = f"Customer profile ({tier}, tenure {tenure}d) requires Sales Manager validation."
        else:
            level = ApprovalLevel.NO_APPROVAL_REQUIRED
            chain = ApprovalChainType.AUTO_APPROVE
            reason = f"Trusted customer ({tier}, tenure {tenure}d, reliability {reliability_score:.1f})."

        return CustomerRoutingEvaluation(
            dimension="CUSTOMER_BASED",
            customer_tier=tier,
            payment_reliability_score=reliability_score,
            is_delinquent_risk=is_delinquent,
            required_level=level,
            recommended_chain=chain,
            escalation_reason=reason,
        )


# ==============================================================================
# Phase 154: Deal-Value Routing Service
# ==============================================================================

class DealValueRoutingService:
    """Service evaluating transaction sizing and authority limits (Phase 154)."""

    @classmethod
    def evaluate(cls, request: DealValueRoutingRequest) -> DealValueRoutingEvaluation:
        val = request.deal_value

        if val >= Decimal("250000.00"):
            band = "ENTERPRISE"
            level = ApprovalLevel.EXECUTIVE
            chain = ApprovalChainType.EXECUTIVE_EXCEPTION
            reason = f"Enterprise commitment of ${val:,.2f} exceeds $250,000 corporate threshold."
        elif val >= Decimal("50000.00"):
            band = "LARGE"
            level = ApprovalLevel.VP_SALES
            chain = ApprovalChainType.COMPREHENSIVE_MULTI_TIER
            reason = f"Large deal sizing of ${val:,.2f} requires VP of Sales authorization."
        elif val >= Decimal("10000.00"):
            band = "MEDIUM"
            level = ApprovalLevel.SALES_MANAGER
            chain = ApprovalChainType.STANDARD_SALES
            reason = f"Mid-market deal sizing of ${val:,.2f} requires Sales Manager approval."
        elif val >= Decimal("1000.00"):
            band = "SMALL"
            level = ApprovalLevel.NO_APPROVAL_REQUIRED
            chain = ApprovalChainType.AUTO_APPROVE
            reason = f"Standard deal sizing of ${val:,.2f} is pre-authorized."
        else:
            band = "MICRO"
            level = ApprovalLevel.NO_APPROVAL_REQUIRED
            chain = ApprovalChainType.AUTO_APPROVE
            reason = f"Micro deal sizing of ${val:,.2f} qualifies for instant auto-approval."

        return DealValueRoutingEvaluation(
            dimension="DEAL_VALUE_BASED",
            deal_value=val,
            value_band=band,
            required_level=level,
            recommended_chain=chain,
            escalation_reason=reason,
        )


# ==============================================================================
# Phase 155: Blended Risk Score & Unified Routing Service
# ==============================================================================

class BlendedRiskScoreService:
    """Service orchestrating multi-dimensional evaluation, computing blended risk scores,
    and deterministically preserving the strictest required approval level (Phase 155).
    """

    @classmethod
    def evaluate_comprehensive(
        cls,
        db: Session,
        company_id: uuid.UUID,
        request: ComprehensiveApprovalEvaluationRequest,
        weights: Optional[BlendedRiskWeights] = None,
    ) -> ComprehensiveApprovalEvaluationResponse:
        """Execute full multi-dimensional evaluation and synthesize blended decision."""
        w = weights or BlendedRiskWeights()

        # 1. AI Risk Dimension (Phase 150)
        if request.ai_risk_score is not None:
            risk_score = float(request.ai_risk_score)
            risk_class = request.ai_risk_classification or (
                "CRITICAL" if risk_score >= 85 else "HIGH" if risk_score >= 60 else "MEDIUM" if risk_score >= 30 else "LOW"
            )
            risk_req = RiskRoutingRequest(
                risk_score=risk_score,
                risk_classification=risk_class,
            )
        else:
            # Auto-infer via B04 RiskPredictionInferenceService
            infer_req = RiskPredictionRequest(
                deal_value=float(request.deal_value),
                requested_discount_pct=float(request.requested_discount_pct),
                selling_price=float(request.selling_price),
                unit_cost=float(request.unit_cost),
                customer_tenure_days=request.customer_tenure_days,
                customer_tier=request.customer_tier,
                deal_reference=request.deal_reference,
            )
            infer_resp = RiskPredictionInferenceService.predict(
                db=db,
                company_id=company_id,
                request=infer_req,
            )
            risk_req = RiskRoutingRequest(
                risk_score=float(infer_resp.risk_score),
                risk_classification=infer_resp.risk_classification.value,
                raw_probability=infer_resp.calibrated_probability,
            )

        risk_eval = RiskBasedRoutingService.evaluate(risk_req)

        # 2. Discount Dimension (Phase 151)
        discount_eval = DiscountBasedRoutingService.evaluate(
            request=DiscountRoutingRequest(
                requested_discount_pct=request.requested_discount_pct,
            ),
            db=db,
            company_id=company_id,
        )

        # 3. Margin Dimension (Phase 152)
        margin_eval = MarginBasedRoutingService.evaluate(
            request=MarginRoutingRequest(
                selling_price=request.selling_price,
                unit_cost=request.unit_cost,
                requested_discount_pct=request.requested_discount_pct,
            )
        )

        # 4. Customer Dimension (Phase 153)
        customer_eval = CustomerBasedRoutingService.evaluate(
            request=CustomerRoutingRequest(
                customer_id=request.customer_id,
                customer_tier=request.customer_tier,
                tenure_days=request.customer_tenure_days,
                payment_default_ratio=request.payment_default_ratio,
                failed_payment_count=request.failed_payment_count,
            ),
            db=db,
            company_id=company_id,
        )

        # 5. Deal Value Dimension (Phase 154)
        deal_val_eval = DealValueRoutingService.evaluate(
            request=DealValueRoutingRequest(
                deal_value=request.deal_value,
            )
        )

        # ======================================================================
        # Phase 155: Synthesis, Blended Risk Score & Strictest Preservation
        # ======================================================================

        # Normalize component scores to [0.0 - 100.0]
        # Risk: already 0-100
        norm_risk = min(100.0, max(0.0, float(risk_eval.risk_score)))

        # Discount: scale requested discount (e.g. 0% = 0, 40%+ = 100)
        norm_disc = min(100.0, max(0.0, float(request.requested_discount_pct) * 2.5))

        # Margin: inverted (negative or 0% margin = 100 risk, 50%+ margin = 0 risk)
        discounted_margin_flt = float(margin_eval.discounted_margin_pct)
        if margin_eval.is_negative_margin or discounted_margin_flt <= 0.0:
            norm_margin = 100.0
        else:
            norm_margin = min(100.0, max(0.0, (50.0 - discounted_margin_flt) * 2.0))

        # Customer: inverted reliability score (reliability 100 = risk 0, reliability 0 = risk 100)
        norm_cust = min(100.0, max(0.0, 100.0 - customer_eval.payment_reliability_score))

        # Deal value: logarithmic scale ($1k = 0, $250k+ = 100)
        val_flt = float(request.deal_value)
        if val_flt <= 1000.0:
            norm_val = 10.0
        elif val_flt >= 250000.0:
            norm_val = 100.0
        else:
            norm_val = min(100.0, max(10.0, (math.log10(val_flt) - 3.0) / (math.log10(250000.0) - 3.0) * 90.0 + 10.0))

        # Components with individual contributions
        components = [
            BlendedRiskComponentScore(
                dimension="AI_RISK",
                raw_metric=f"Score: {risk_eval.risk_score:.1f} ({risk_eval.risk_classification})",
                normalized_score=round(norm_risk, 1),
                weight=w.ai_risk_weight,
                weighted_contribution=round(norm_risk * w.ai_risk_weight, 2),
                triggered_level=risk_eval.required_level,
            ),
            BlendedRiskComponentScore(
                dimension="DISCOUNT",
                raw_metric=f"Discount: {request.requested_discount_pct:.1f}%",
                normalized_score=round(norm_disc, 1),
                weight=w.discount_weight,
                weighted_contribution=round(norm_disc * w.discount_weight, 2),
                triggered_level=discount_eval.required_level,
            ),
            BlendedRiskComponentScore(
                dimension="MARGIN",
                raw_metric=f"Post-discount Margin: {margin_eval.discounted_margin_pct:.1f}%",
                normalized_score=round(norm_margin, 1),
                weight=w.margin_weight,
                weighted_contribution=round(norm_margin * w.margin_weight, 2),
                triggered_level=margin_eval.required_level,
            ),
            BlendedRiskComponentScore(
                dimension="CUSTOMER",
                raw_metric=f"Reliability: {customer_eval.payment_reliability_score:.1f} (Tier: {customer_eval.customer_tier})",
                normalized_score=round(norm_cust, 1),
                weight=w.customer_weight,
                weighted_contribution=round(norm_cust * w.customer_weight, 2),
                triggered_level=customer_eval.required_level,
            ),
            BlendedRiskComponentScore(
                dimension="DEAL_VALUE",
                raw_metric=f"Value: ${request.deal_value:,.2f} ({deal_val_eval.value_band})",
                normalized_score=round(norm_val, 1),
                weight=w.deal_value_weight,
                weighted_contribution=round(norm_val * w.deal_value_weight, 2),
                triggered_level=deal_val_eval.required_level,
            ),
        ]

        total_blended_score = round(sum(c.weighted_contribution for c in components), 1)

        # Classification based on blended score
        if total_blended_score >= 85.0:
            blended_class = "CRITICAL"
        elif total_blended_score >= 60.0:
            blended_class = "HIGH"
        elif total_blended_score >= 30.0:
            blended_class = "MEDIUM"
        else:
            blended_class = "LOW"

        # STRICT PRESERVATION RULE: Find the strictest level among all individual dimensions
        all_levels = [
            risk_eval.required_level,
            discount_eval.required_level,
            margin_eval.required_level,
            customer_eval.required_level,
            deal_val_eval.required_level,
        ]
        strictest_level = ApprovalLevelHierarchyService.get_strictest_level(all_levels)
        strictest_rank = ApprovalLevelHierarchyService.get_rank(strictest_level)

        # Identify primary driver
        drivers = [
            c for c in components
            if ApprovalLevelHierarchyService.get_rank(c.triggered_level) == strictest_rank
        ]
        primary_driver = drivers[0].dimension if drivers else "BLENDED_SYNTHESIS"

        # Resolve final binding chain
        final_chain = ApprovalChainService.get_chain_for_level(strictest_level)

        summary_text = (
            f"Deal evaluated with Blended Risk Score {total_blended_score}/100 ({blended_class}). "
            f"Preserved strictest required authority: {strictest_level.value} (Rank {strictest_rank}) "
            f"driven by {primary_driver}. Routed to chain: {final_chain.name}."
        )

        blended_result = BlendedRiskScoreResult(
            blended_risk_score=total_blended_score,
            blended_risk_classification=blended_class,
            strictest_required_level=strictest_level,
            strictest_level_rank=strictest_rank,
            selected_approval_chain=final_chain.chain_type,
            component_breakdown=components,
            primary_escalation_driver=primary_driver,
            evaluation_summary=summary_text,
        )

        return ComprehensiveApprovalEvaluationResponse(
            evaluation_id=f"EVAL-{uuid.uuid4().hex[:12].upper()}",
            company_id=company_id,
            deal_reference=request.deal_reference,
            evaluated_at=datetime.now(timezone.utc),
            risk_evaluation=risk_eval,
            discount_evaluation=discount_eval,
            margin_evaluation=margin_eval,
            customer_evaluation=customer_eval,
            deal_value_evaluation=deal_val_eval,
            blended_result=blended_result,
            final_required_level=strictest_level,
            final_approval_chain=final_chain,
        )


# ==============================================================================
# Phase 146: Approval Policy Configuration Service
# ==============================================================================

class ApprovalPolicyService:
    """Service managing tenant-isolated approval policy configurations (Phase 146)."""

    @classmethod
    def get_active_policy(cls, db: Session, company_id: uuid.UUID) -> Optional[ApprovalPolicy]:
        """Fetch the default or first active approval policy for a tenant."""
        policy = db.execute(
            select(ApprovalPolicy).where(
                ApprovalPolicy.company_id == company_id,
                ApprovalPolicy.is_active == True,
                ApprovalPolicy.is_default == True,
            )
        ).scalar_one_or_none()

        if not policy:
            policy = db.execute(
                select(ApprovalPolicy).where(
                    ApprovalPolicy.company_id == company_id,
                    ApprovalPolicy.is_active == True,
                ).order_by(ApprovalPolicy.created_at.desc())
            ).scalars().first()

        return policy

    @classmethod
    def create_policy(
        cls,
        db: Session,
        company_id: uuid.UUID,
        data: ApprovalPolicyCreate,
        user_id: Optional[uuid.UUID] = None,
    ) -> ApprovalPolicy:
        """Create a new approval policy for a tenant."""
        # Check if default needs unsetting on others
        if data.is_default:
            existing_defaults = db.execute(
                select(ApprovalPolicy).where(
                    ApprovalPolicy.company_id == company_id,
                    ApprovalPolicy.is_default == True,
                )
            ).scalars().all()
            for p in existing_defaults:
                p.is_default = False

        levels_data = [l.model_dump() for l in data.levels_config] if data.levels_config else [l.model_dump() for l in ApprovalLevelHierarchyService.get_definitions()]
        chains_data = [c.model_dump() for c in data.chains_config] if data.chains_config else [c.model_dump() for c in ApprovalChainService.get_all_chains()]
        thresholds_data = {"rules": [r.model_dump() for r in data.thresholds_config]} if data.thresholds_config else {"rules": [r.model_dump() for r in ApprovalThresholdService.DEFAULT_RULES]}

        policy = ApprovalPolicy(
            company_id=company_id,
            name=data.name,
            description=data.description,
            is_active=data.is_active,
            is_default=data.is_default,
            levels_config=levels_data,
            chains_config=chains_data,
            thresholds_config=thresholds_data,
            created_by_id=user_id,
        )
        db.add(policy)
        db.commit()
        db.refresh(policy)
        return policy

    @classmethod
    def list_policies(cls, db: Session, company_id: uuid.UUID) -> List[ApprovalPolicy]:
        """List all approval policies for a tenant."""
        return list(db.execute(
            select(ApprovalPolicy).where(
                ApprovalPolicy.company_id == company_id
            ).order_by(ApprovalPolicy.created_at.desc())
        ).scalars().all())
