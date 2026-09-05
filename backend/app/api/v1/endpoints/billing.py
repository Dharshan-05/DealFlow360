
import uuid
from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.endpoints.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.billing import (
    SubscriptionPlanCreate, SubscriptionPlanResponse, SubscriptionCreate, SubscriptionResponse,
    UsageRecordCreate, UsageRecordResponse, BillingDashboardSummary, InvoiceResponse
)
from app.services.billing import (
    SubscriptionPlanService, SubscriptionCrudService, UsageBillingService, SubscriptionAnalyticsService,
    UpgradeDowngradeService, RenewalCancellationService, HybridBillingService
)
from app.models.billing import SubscriptionPlan

router = APIRouter()

@router.post("/plans", response_model=SubscriptionPlanResponse)
def create_plan(
    plan_in: SubscriptionPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    return SubscriptionPlanService.create_plan(db, current_user.company_id, plan_in)

@router.get("/plans", response_model=List[SubscriptionPlanResponse])
def list_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    return SubscriptionPlanService.list_plans(db, current_user.company_id)

@router.post("/subscriptions", response_model=SubscriptionResponse)
def create_subscription(
    sub_in: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    try:
        return SubscriptionCrudService.create_subscription(db, current_user.company_id, sub_in, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
def get_subscription(
    subscription_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    sub = SubscriptionCrudService.get_subscription(db, current_user.company_id, subscription_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return sub

@router.post("/subscriptions/{subscription_id}/change-plan", response_model=SubscriptionResponse)
def change_subscription_plan(
    subscription_id: uuid.UUID,
    new_plan_id: uuid.UUID,
    new_quantity: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    try:
        return UpgradeDowngradeService.change_plan(db, current_user.company_id, subscription_id, new_plan_id, new_quantity)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/subscriptions/{subscription_id}/renew", response_model=Any)
def renew_subscription(
    subscription_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    inv = RenewalCancellationService.process_renewal(db, current_user.company_id, subscription_id)
    return {"status": "success", "invoice_id": str(inv.id) if inv else None}

@router.post("/subscriptions/{subscription_id}/cancel", response_model=SubscriptionResponse)
def cancel_subscription(
    subscription_id: uuid.UUID,
    immediate: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    try:
        return RenewalCancellationService.cancel_subscription(db, current_user.company_id, subscription_id, immediate)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/subscriptions/{subscription_id}/usage", response_model=UsageRecordResponse)
def record_usage(
    subscription_id: uuid.UUID,
    usage_in: UsageRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    return UsageBillingService.ingest_usage(db, current_user.company_id, usage_in, subscription_id)

@router.post("/deals/{deal_id}/hybrid-invoice", response_model=InvoiceResponse)
def create_hybrid_invoice(
    deal_id: uuid.UUID,
    customer_id: uuid.UUID,
    lines: List[dict],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    return HybridBillingService.process_hybrid_deal(db, current_user.company_id, customer_id, deal_id, lines)

@router.get("/dashboard", response_model=BillingDashboardSummary)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    return SubscriptionAnalyticsService.get_dashboard_summary(db, current_user.company_id)

