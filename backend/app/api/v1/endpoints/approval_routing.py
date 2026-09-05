"""Approval Routing API Endpoints (DealFlow360 B05: Phases 146–155).

Provides tenant-isolated, RBAC-protected API endpoints for:
- Phase 146: Approval Configuration (GET /api/v1/approvals/policies, POST /api/v1/approvals/policies)
- Phase 147: Approval Levels (GET /api/v1/approvals/levels)
- Phase 148: Approval Chains (GET /api/v1/approvals/chains)
- Phase 149: Approval Thresholds (POST /api/v1/approvals/evaluate/thresholds)
- Phase 150: Risk-Based Routing (POST /api/v1/approvals/evaluate/risk)
- Phase 151: Discount-Based Routing (POST /api/v1/approvals/evaluate/discount)
- Phase 152: Margin-Based Routing (POST /api/v1/approvals/evaluate/margin)
- Phase 153: Customer-Based Routing (POST /api/v1/approvals/evaluate/customer)
- Phase 154: Deal-Value Routing (POST /api/v1/approvals/evaluate/deal-value)
- Phase 155: Blended Risk Score & Comprehensive Evaluation (POST /api/v1/approvals/evaluate/comprehensive)
"""
from typing import List
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models.user import User
from app.schemas.response import ApiResponse
from app.schemas.approval_routing import (
    ApprovalChainDefinition,
    ApprovalLevelDefinition,
    ApprovalPolicyCreate,
    ApprovalPolicyResponse,
    ApprovalThresholdRule,
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
from app.services.approval_routing import (
    ApprovalChainService,
    ApprovalLevelHierarchyService,
    ApprovalPolicyService,
    ApprovalThresholdService,
    BlendedRiskScoreService,
    CustomerBasedRoutingService,
    DealValueRoutingService,
    DiscountBasedRoutingService,
    MarginBasedRoutingService,
    RiskBasedRoutingService,
)

router = APIRouter(prefix="/approvals", tags=["Approval Routing Foundation (B05: Phases 146–155)"])


# ==============================================================================
# Phase 146: Approval Configuration Endpoints
# ==============================================================================

@router.get(
    "/policies",
    response_model=ApiResponse[List[ApprovalPolicyResponse]],
    dependencies=[Depends(require_permission("discounts:read"))],
    summary="List tenant approval policies (Phase 146)",
)
def list_approval_policies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all approval policies defined for the authenticated company tenant."""
    policies = ApprovalPolicyService.list_policies(db=db, company_id=current_user.company_id)
    return ApiResponse(
        success=True,
        data=[ApprovalPolicyResponse.model_validate(p) for p in policies],
    )


@router.post(
    "/policies",
    response_model=ApiResponse[ApprovalPolicyResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("discounts:create"))],
    summary="Create tenant approval policy (Phase 146)",
)
def create_approval_policy(
    payload: ApprovalPolicyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new tenant-isolated approval policy specifying levels, chains, and threshold rules."""
    policy = ApprovalPolicyService.create_policy(
        db=db,
        company_id=current_user.company_id,
        data=payload,
        user_id=current_user.id,
    )
    return ApiResponse(
        success=True,
        data=ApprovalPolicyResponse.model_validate(policy),
    )


# ==============================================================================
# Phase 147: Approval Levels Endpoints
# ==============================================================================

@router.get(
    "/levels",
    response_model=ApiResponse[List[ApprovalLevelDefinition]],
    dependencies=[Depends(require_permission("discounts:read"))],
    summary="Get approval levels hierarchy (Phase 147)",
)
def get_approval_levels(
    current_user: User = Depends(get_current_user),
):
    """Retrieve the deterministic authority levels hierarchy with rank ordering and SLA parameters."""
    definitions = ApprovalLevelHierarchyService.get_definitions()
    return ApiResponse(
        success=True,
        data=definitions,
    )


# ==============================================================================
# Phase 148: Approval Chains Endpoints
# ==============================================================================

@router.get(
    "/chains",
    response_model=ApiResponse[List[ApprovalChainDefinition]],
    dependencies=[Depends(require_permission("discounts:read"))],
    summary="Get registered approval chains (Phase 148)",
)
def get_approval_chains(
    current_user: User = Depends(get_current_user),
):
    """Retrieve standard registered sequential approval chains and their steps."""
    chains = ApprovalChainService.get_all_chains()
    return ApiResponse(
        success=True,
        data=chains,
    )


# ==============================================================================
# Phase 149: Approval Thresholds Evaluation
# ==============================================================================

@router.post(
    "/evaluate/thresholds",
    response_model=ApiResponse[ThresholdEvaluationResult],
    dependencies=[Depends(require_permission("discounts:read"))],
    summary="Evaluate value against approval thresholds (Phase 149)",
)
def evaluate_threshold(
    dimension: ThresholdDimension,
    value: float = Query(description="Numerical metric value to evaluate"),
    current_user: User = Depends(get_current_user),
):
    """Evaluate an observed metric value against boundary threshold rules for a dimension."""
    res = ApprovalThresholdService.evaluate_dimension(dimension=dimension, value=value)
    return ApiResponse(
        success=True,
        data=res,
    )


# ==============================================================================
# Phase 150: Risk-Based Routing
# ==============================================================================

@router.post(
    "/evaluate/risk",
    response_model=ApiResponse[RiskRoutingEvaluation],
    dependencies=[Depends(require_permission("discounts:read"))],
    summary="Evaluate risk-based routing (Phase 150)",
)
def evaluate_risk_routing(
    request: RiskRoutingRequest,
    current_user: User = Depends(get_current_user),
):
    """Determine required approval level and chain driven by AI Risk model classification."""
    res = RiskBasedRoutingService.evaluate(request)
    return ApiResponse(
        success=True,
        data=res,
    )


# ==============================================================================
# Phase 151: Discount-Based Routing
# ==============================================================================

@router.post(
    "/evaluate/discount",
    response_model=ApiResponse[DiscountRoutingEvaluation],
    dependencies=[Depends(require_permission("discounts:read"))],
    summary="Evaluate discount-based routing (Phase 151)",
)
def evaluate_discount_routing(
    request: DiscountRoutingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Determine required approval level and chain based on discount ceilings and authority limits."""
    res = DiscountBasedRoutingService.evaluate(
        request=request,
        db=db,
        company_id=current_user.company_id,
    )
    return ApiResponse(
        success=True,
        data=res,
    )


# ==============================================================================
# Phase 152: Margin-Based Routing
# ==============================================================================

@router.post(
    "/evaluate/margin",
    response_model=ApiResponse[MarginRoutingEvaluation],
    dependencies=[Depends(require_permission("discounts:read"))],
    summary="Evaluate margin-based routing (Phase 152)",
)
def evaluate_margin_routing(
    request: MarginRoutingRequest,
    current_user: User = Depends(get_current_user),
):
    """Determine required approval level and chain based on gross and post-discount margin profitability."""
    res = MarginBasedRoutingService.evaluate(request)
    return ApiResponse(
        success=True,
        data=res,
    )


# ==============================================================================
# Phase 153: Customer-Based Routing
# ==============================================================================

@router.post(
    "/evaluate/customer",
    response_model=ApiResponse[CustomerRoutingEvaluation],
    dependencies=[Depends(require_permission("discounts:read"))],
    summary="Evaluate customer-based routing (Phase 153)",
)
def evaluate_customer_routing(
    request: CustomerRoutingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Determine required approval level and chain based on customer tier, tenure, and payment default history."""
    res = CustomerBasedRoutingService.evaluate(
        request=request,
        db=db,
        company_id=current_user.company_id,
    )
    return ApiResponse(
        success=True,
        data=res,
    )


# ==============================================================================
# Phase 154: Deal-Value Routing
# ==============================================================================

@router.post(
    "/evaluate/deal-value",
    response_model=ApiResponse[DealValueRoutingEvaluation],
    dependencies=[Depends(require_permission("discounts:read"))],
    summary="Evaluate deal-value routing (Phase 154)",
)
def evaluate_deal_value_routing(
    request: DealValueRoutingRequest,
    current_user: User = Depends(get_current_user),
):
    """Determine required approval level and chain based on monetary deal sizing tiers."""
    res = DealValueRoutingService.evaluate(request)
    return ApiResponse(
        success=True,
        data=res,
    )


# ==============================================================================
# Phase 155: Blended Risk Score & Comprehensive Routing
# ==============================================================================

@router.post(
    "/evaluate/comprehensive",
    response_model=ApiResponse[ComprehensiveApprovalEvaluationResponse],
    dependencies=[Depends(require_permission("discounts:read"))],
    summary="Execute comprehensive multi-dimensional approval evaluation (Phase 155)",
)
def evaluate_comprehensive_routing(
    request: ComprehensiveApprovalEvaluationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Synthesize Risk, Discount, Margin, Customer, and Deal Value metrics into a Blended Risk Score,
    preserving the strictest required approval level across all dimensions.
    """
    res = BlendedRiskScoreService.evaluate_comprehensive(
        db=db,
        company_id=current_user.company_id,
        request=request,
    )
    return ApiResponse(
        success=True,
        data=res,
    )
