"""Discount Automation & Decision Engine Endpoints (DealFlow360 G24: Phases 116–120).

Provides REST APIs for:
- Phase 116: Inventory-Aware Discount Signal (POST /governance/discounts/automation/inventory-signal)
- Phase 117: Deal-Value-Aware Discount Signal (POST /governance/discounts/automation/deal-value-signal)
- Phase 118: Discount Risk Calculation (POST /governance/discounts/automation/calculate-risk)
- Phase 119: Discount Decision Engine (POST /governance/discounts/automation/evaluate-decision)
- Phase 120: Automated Discount Application (POST /governance/discounts/automation/apply & GET /governance/discounts/automation/applied)
"""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models.user import User
from app.schemas.discount_automation import (
    AppliedDiscountListResponse,
    AppliedDiscountResponse,
    ApplyDiscountRequest,
    DealValueDiscountSignalRequest,
    DealValueDiscountSignalResponse,
    DiscountDecisionRequest,
    DiscountDecisionResponse,
    DiscountRiskCalculationRequest,
    DiscountRiskCalculationResponse,
    InventoryDiscountSignalRequest,
    InventoryDiscountSignalResponse,
)
from app.services.discount_automation import (
    AutomatedDiscountApplicationService,
    DealValueAwareDiscountService,
    DiscountDecisionEngine,
    DiscountRiskCalculationService,
    InventoryAwareDiscountService,
)

router = APIRouter(prefix="/governance/discounts/automation", tags=["Discount Automation & Decision Engine"])


# ==============================================================================
# Phase 116: Inventory-Aware Discount Signal Endpoint
# ==============================================================================

@router.post("/inventory-signal", response_model=InventoryDiscountSignalResponse)
def get_inventory_discount_signal(
    payload: InventoryDiscountSignalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("discounts:read")),
):
    """Calculates inventory-aware discount modulation based on real-time multi-warehouse

    ATP, stock levels, and open backorder states.
    """
    return InventoryAwareDiscountService.evaluate_inventory_signal(
        db=db,
        company_id=current_user.company_id,
        product_id=payload.product_id,
        base_target_discount=payload.base_target_discount,
    )


# ==============================================================================
# Phase 117: Deal-Value-Aware Discount Signal Endpoint
# ==============================================================================

@router.post("/deal-value-signal", response_model=DealValueDiscountSignalResponse)
def get_deal_value_discount_signal(
    payload: DealValueDiscountSignalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("discounts:read")),
):
    """Calculates deal-value-aware discount modulation based on transaction sizing

    using strict Decimal financial calculations.
    """
    return DealValueAwareDiscountService.evaluate_deal_value_signal(
        db=db,
        company_id=current_user.company_id,
        product_id=payload.product_id,
        base_target_discount=payload.base_target_discount,
        deal_value=payload.deal_value,
        quantity=payload.quantity,
        selling_price_override=payload.selling_price_override,
    )


# ==============================================================================
# Phase 118: Discount Risk Calculation Endpoint
# ==============================================================================

@router.post("/calculate-risk", response_model=DiscountRiskCalculationResponse)
def calculate_discount_risk(
    payload: DiscountRiskCalculationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("discounts:read")),
):
    """Evaluates multi-factor risk associated with applying a requested discount."""
    return DiscountRiskCalculationService.calculate_risk(
        db=db,
        company_id=current_user.company_id,
        customer_id=payload.customer_id,
        product_id=payload.product_id,
        requested_discount=payload.requested_discount,
        actor=current_user,
        deal_value=payload.deal_value,
        selling_price_override=payload.selling_price_override,
        min_margin_percentage=payload.min_margin_percentage,
    )


# ==============================================================================
# Phase 119: Discount Decision Engine Endpoint
# ==============================================================================

@router.post("/evaluate-decision", response_model=DiscountDecisionResponse)
def evaluate_discount_decision(
    payload: DiscountDecisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("discounts:read")),
):
    """Master orchestration engine evaluating governance, margins, actor limits,

    inventory, deal value, and risk to produce a final deterministic decision.
    """
    return DiscountDecisionEngine.evaluate_decision(
        db=db,
        company_id=current_user.company_id,
        customer_id=payload.customer_id,
        product_id=payload.product_id,
        requested_discount=payload.requested_discount,
        actor=current_user,
        deal_value=payload.deal_value,
        deal_reference=payload.deal_reference,
        selling_price_override=payload.selling_price_override,
        min_margin_percentage=payload.min_margin_percentage,
    )


# ==============================================================================
# Phase 120: Automated Discount Application Endpoints
# ==============================================================================

@router.post("/apply", response_model=AppliedDiscountResponse, status_code=status.HTTP_201_CREATED)
def apply_discount(
    payload: ApplyDiscountRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("discounts:write")),
):
    """Controlled automated discount application.

    Re-verifies decision server-side, prevents unauthorized/rejected applications,
    guarantees idempotency, updates discount history, and creates audit logs.
    Requires `discounts:write` permission.
    """
    return AutomatedDiscountApplicationService.apply_discount(
        db=db,
        company_id=current_user.company_id,
        payload=payload,
        actor=current_user,
    )


@router.get("/applied", response_model=AppliedDiscountListResponse)
def list_applied_discounts(
    customer_id: Optional[uuid.UUID] = Query(None, description="Filter by customer ID"),
    product_id: Optional[uuid.UUID] = Query(None, description="Filter by product ID"),
    deal_reference: Optional[str] = Query(None, description="Search by deal reference"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("discounts:read")),
):
    """List audit-trailed applied discount records within current company tenant."""
    items = AutomatedDiscountApplicationService.list_applied_discounts(
        db=db,
        company_id=current_user.company_id,
        customer_id=customer_id,
        product_id=product_id,
        deal_reference=deal_reference,
        skip=skip,
        limit=limit,
    )
    total = AutomatedDiscountApplicationService.count_applied_discounts(
        db=db,
        company_id=current_user.company_id,
        customer_id=customer_id,
        product_id=product_id,
        deal_reference=deal_reference,
    )
    return AppliedDiscountListResponse(items=items, total=total)
