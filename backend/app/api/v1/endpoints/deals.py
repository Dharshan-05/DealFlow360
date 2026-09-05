"""Commercial Deal Management Endpoints (DealFlow360 B11: Phases 206–215).

Provides tenant-isolated, RBAC-governed endpoints for deal creation from quotations,
product line-item linking, precision financial calculations, margins, stage transitions,
win probability scoring, forecasting, sales activities, unified timelines, and executive dashboards.
"""
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models.user import User
from app.schemas.deal import (
    DealActivityCreate,
    DealActivityResponse,
    DealCreateFromQuoteRequest,
    DealDashboardResponse,
    DealDetailResponse,
    DealForecastResponse,
    DealMarginResponse,
    DealProbabilityResponse,
    DealProductCreate,
    DealProductResponse,
    DealStageUpdateRequest,
    DealSummaryResponse,
    DealTimelineEventResponse,
    PipelineForecastSummary,
)
from app.schemas.response import ApiResponse
from app.services.deal import (
    DealActivityService,
    DealCreationService,
    DealDashboardService,
    DealForecastingService,
    DealMarginService,
    DealProbabilityService,
    DealProductService,
    DealService,
    DealStageManagementService,
    DealTimelineService,
)

router = APIRouter(prefix="/deals", tags=["Deal Management (B11: Phases 206–215)"])


# ==============================================================================
# Phase 215: Executive Deal Dashboard (placed before /{deal_id} to avoid collision)
# ==============================================================================

@router.get(
    "/dashboard",
    response_model=ApiResponse[DealDashboardResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("deals:read"))],
    summary="Get Deal Pipeline Dashboard (Phase 215)",
)
def get_deal_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve executive pipeline metrics, win rate, stage breakdown, and recent activity."""
    dashboard = DealDashboardService.get_dashboard_summary(
        db=db,
        company_id=current_user.company_id,
    )
    return ApiResponse(
        data=dashboard,
        message="Deal dashboard summary retrieved successfully",
    )


# ==============================================================================
# Phase 212: Pipeline Revenue Forecast (placed before /{deal_id} to avoid collision)
# ==============================================================================

@router.get(
    "/forecast/pipeline",
    response_model=ApiResponse[PipelineForecastSummary],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("deals:read"))],
    summary="Get Pipeline Revenue Forecast (Phase 212)",
)
def get_pipeline_forecast(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Aggregates expected revenue, weighted pipeline, and stage distributions."""
    forecast = DealForecastingService.get_pipeline_forecast(
        db=db,
        company_id=current_user.company_id,
    )
    return ApiResponse(
        data=forecast,
        message="Pipeline revenue forecast retrieved successfully",
    )


# ==============================================================================
# Phase 206: Deal Creation from Accepted Quotation
# ==============================================================================

@router.post(
    "/from-quote/{quotation_id}",
    response_model=ApiResponse[DealDetailResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("deals:write"))],
    summary="Create Deal from Quotation (Phase 206)",
)
def create_deal_from_quote(
    quotation_id: uuid.UUID,
    payload: Optional[DealCreateFromQuoteRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Transactionally creates a WON deal from an ACCEPTED quotation, copying line items and preserving terms."""
    title_override = payload.title_override if payload else None
    notes = payload.notes if payload else None

    deal = DealCreationService.create_from_quote(
        db=db,
        company_id=current_user.company_id,
        quotation_id=quotation_id,
        actor=current_user,
        title_override=title_override,
        notes=notes,
    )
    db.commit()

    detail = DealService.to_deal_detail(deal)
    return ApiResponse(
        data=detail,
        message=f"Deal {deal.deal_code} created successfully from quotation",
    )


# ==============================================================================
# Deal Listing & Retrieval
# ==============================================================================

@router.get(
    "",
    response_model=ApiResponse[List[DealSummaryResponse]],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("deals:read"))],
    summary="List Deals (Phases 206–210)",
)
def list_deals(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    stage: Optional[str] = Query(None, description="Filter by stage (e.g., QUALIFIED, PROPOSAL)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (e.g., OPEN, WON, LOST)"),
    customer_id: Optional[uuid.UUID] = Query(None, description="Filter by customer identifier"),
    search: Optional[str] = Query(None, description="Search deal code or title"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve paginated, tenant-isolated list of commercial deals with filters."""
    items, total = DealService.list_deals(
        db=db,
        company_id=current_user.company_id,
        skip=skip,
        limit=limit,
        stage=stage,
        status=status_filter,
        customer_id=customer_id,
        search=search,
    )
    return ApiResponse(
        data=items,
        message=f"Retrieved {len(items)} deals (total {total})",
    )


@router.get(
    "/{deal_id}",
    response_model=ApiResponse[DealDetailResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("deals:read"))],
    summary="Get Deal Detail (Phases 206–208)",
)
def get_deal(
    deal_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve full details of a deal including products, financials, and recent activities."""
    deal = DealService.get_deal_by_id(
        db=db,
        company_id=current_user.company_id,
        deal_id=deal_id,
    )
    detail = DealService.to_deal_detail(deal)
    return ApiResponse(
        data=detail,
        message=f"Deal {deal.deal_code} retrieved successfully",
    )


# ==============================================================================
# Phase 207: Deal Product Linking
# ==============================================================================

@router.post(
    "/{deal_id}/products",
    response_model=ApiResponse[DealProductResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("deals:write"))],
    summary="Add Product to Deal (Phase 207)",
)
def add_product_to_deal(
    deal_id: uuid.UUID,
    payload: DealProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Links a product to a deal with pricing, discount, tax, cost, and margin calculation."""
    deal_product = DealProductService.add_product_to_deal(
        db=db,
        company_id=current_user.company_id,
        deal_id=deal_id,
        payload=payload,
        actor=current_user,
    )
    db.commit()

    res = DealProductResponse(
        id=deal_product.id,
        deal_id=deal_product.deal_id,
        product_id=deal_product.product_id,
        product_name=deal_product.product.name if deal_product.product else None,
        product_sku=deal_product.product.sku if deal_product.product else None,
        quotation_line_item_id=deal_product.quotation_line_item_id,
        quantity=deal_product.quantity,
        unit_price=deal_product.unit_price,
        unit_cost=deal_product.unit_cost,
        discount_percent=deal_product.discount_percent,
        tax_rate=deal_product.tax_rate,
        subtotal=deal_product.subtotal,
        discount_amount=deal_product.discount_amount,
        taxable_amount=deal_product.taxable_amount,
        tax_amount=deal_product.tax_amount,
        total_amount=deal_product.total_amount,
        total_cost=deal_product.total_cost,
        gross_profit=deal_product.gross_profit,
        margin_percentage=deal_product.margin_percentage,
        notes=deal_product.notes,
        created_at=deal_product.created_at,
    )
    return ApiResponse(
        data=res,
        message="Product linked to deal successfully",
    )


@router.get(
    "/{deal_id}/products",
    response_model=ApiResponse[List[DealProductResponse]],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("deals:read"))],
    summary="List Deal Products (Phase 207)",
)
def list_deal_products(
    deal_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all product line items associated with a deal."""
    deal = DealService.get_deal_by_id(
        db=db,
        company_id=current_user.company_id,
        deal_id=deal_id,
    )
    items = [
        DealProductResponse(
            id=p.id,
            deal_id=p.deal_id,
            product_id=p.product_id,
            product_name=p.product.name if p.product else None,
            product_sku=p.product.sku if p.product else None,
            quotation_line_item_id=p.quotation_line_item_id,
            quantity=p.quantity,
            unit_price=p.unit_price,
            unit_cost=p.unit_cost,
            discount_percent=p.discount_percent,
            tax_rate=p.tax_rate,
            subtotal=p.subtotal,
            discount_amount=p.discount_amount,
            taxable_amount=p.taxable_amount,
            tax_amount=p.tax_amount,
            total_amount=p.total_amount,
            total_cost=p.total_cost,
            gross_profit=p.gross_profit,
            margin_percentage=p.margin_percentage,
            notes=p.notes,
            created_at=p.created_at,
        )
        for p in deal.products
    ]
    return ApiResponse(
        data=items,
        message=f"Retrieved {len(items)} deal products",
    )


# ==============================================================================
# Phase 208: Deal Recalculation
# ==============================================================================

@router.post(
    "/{deal_id}/recalculate",
    response_model=ApiResponse[DealDetailResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("deals:write"))],
    summary="Recalculate Deal Totals (Phase 208)",
)
def recalculate_deal(
    deal_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Recomputes subtotal, discounts, taxes, costs, margins, and expected revenue."""
    deal = DealService.recalculate_and_save(
        db=db,
        company_id=current_user.company_id,
        deal_id=deal_id,
    )
    db.commit()
    detail = DealService.to_deal_detail(deal)
    return ApiResponse(
        data=detail,
        message=f"Deal {deal.deal_code} totals recalculated successfully",
    )


# ==============================================================================
# Phase 209: Deal Margin Evaluation
# ==============================================================================

@router.get(
    "/{deal_id}/margin",
    response_model=ApiResponse[DealMarginResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("deals:read"))],
    summary="Get Deal Margin & Risk Analysis (Phase 209)",
)
def get_deal_margin(
    deal_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Calculates gross margin, discounted margin, and risk classification."""
    deal = DealService.get_deal_by_id(
        db=db,
        company_id=current_user.company_id,
        deal_id=deal_id,
    )
    margin_metrics = DealMarginService.evaluate_margin(deal)
    return ApiResponse(
        data=margin_metrics,
        message="Deal margin metrics evaluated successfully",
    )


# ==============================================================================
# Phase 210: Deal Stage Management
# ==============================================================================

@router.patch(
    "/{deal_id}/stage",
    response_model=ApiResponse[DealDetailResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("deals:write"))],
    summary="Update Deal Stage (Phase 210)",
)
def update_deal_stage(
    deal_id: uuid.UUID,
    payload: DealStageUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Transitions a deal stage with state validation, probability adjustment, and activity audit logging."""
    deal = DealService.get_deal_by_id(
        db=db,
        company_id=current_user.company_id,
        deal_id=deal_id,
    )
    updated_deal = DealStageManagementService.update_stage(
        db=db,
        deal=deal,
        target_stage=payload.stage,
        actor=current_user,
        reason=payload.reason,
    )
    db.commit()
    detail = DealService.to_deal_detail(updated_deal)
    return ApiResponse(
        data=detail,
        message=f"Deal transitioned to stage {updated_deal.stage} successfully",
    )


# ==============================================================================
# Phase 211: Deal Probability Engine
# ==============================================================================

@router.get(
    "/{deal_id}/probability",
    response_model=ApiResponse[DealProbabilityResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("deals:read"))],
    summary="Calculate Deal Win Probability (Phase 211)",
)
def get_deal_probability(
    deal_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Determines win probability (0–100%) with contributing factors."""
    deal = DealService.get_deal_by_id(
        db=db,
        company_id=current_user.company_id,
        deal_id=deal_id,
    )
    prob, factors, explanation = DealProbabilityService.calculate_probability(db=db, deal=deal)
    res = DealProbabilityResponse(
        deal_id=deal.id,
        probability=prob,
        stage=deal.stage,
        factors=factors,
        explanation=explanation,
    )
    return ApiResponse(
        data=res,
        message="Deal probability calculated successfully",
    )


# ==============================================================================
# Phase 212: Deal Forecasting
# ==============================================================================

@router.get(
    "/{deal_id}/forecast",
    response_model=ApiResponse[DealForecastResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("deals:read"))],
    summary="Get Deal Revenue Forecast (Phase 212)",
)
def get_deal_forecast(
    deal_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns single deal forecast and probability-weighted value."""
    deal = DealService.get_deal_by_id(
        db=db,
        company_id=current_user.company_id,
        deal_id=deal_id,
    )
    forecast = DealForecastingService.get_deal_forecast(deal)
    return ApiResponse(
        data=forecast,
        message="Deal revenue forecast retrieved successfully",
    )


# ==============================================================================
# Phase 213: Deal Activity Tracking
# ==============================================================================

@router.post(
    "/{deal_id}/activities",
    response_model=ApiResponse[DealActivityResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("deals:write"))],
    summary="Log Deal Activity (Phase 213)",
)
def log_deal_activity(
    deal_id: uuid.UUID,
    payload: DealActivityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Records an activity (note, call, meeting, task, etc.) against a deal."""
    activity = DealActivityService.record_activity(
        db=db,
        company_id=current_user.company_id,
        deal_id=deal_id,
        payload=payload,
        actor=current_user,
    )
    db.commit()

    actor_name = f"{current_user.first_name} {current_user.last_name}".strip() if current_user.first_name else current_user.email
    res = DealActivityResponse(
        id=activity.id,
        deal_id=activity.deal_id,
        activity_type=activity.activity_type,
        title=activity.title,
        description=activity.description,
        actor_id=activity.actor_id,
        actor_name=actor_name,
        activity_metadata=activity.activity_metadata,
        created_at=activity.created_at,
    )
    return ApiResponse(
        data=res,
        message="Deal activity logged successfully",
    )


@router.get(
    "/{deal_id}/activities",
    response_model=ApiResponse[List[DealActivityResponse]],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("deals:read"))],
    summary="List Deal Activities (Phase 213)",
)
def list_deal_activities(
    deal_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve paginated activity records for a deal in reverse chronological order."""
    acts = DealActivityService.list_activities(
        db=db,
        company_id=current_user.company_id,
        deal_id=deal_id,
        limit=limit,
        offset=offset,
    )
    items = [
        DealActivityResponse(
            id=a.id,
            deal_id=a.deal_id,
            activity_type=a.activity_type,
            title=a.title,
            description=a.description,
            actor_id=a.actor_id,
            actor_name=f"{a.actor.first_name} {a.actor.last_name}".strip() if a.actor else "System",
            activity_metadata=a.activity_metadata,
            created_at=a.created_at,
        )
        for a in acts
    ]
    return ApiResponse(
        data=items,
        message=f"Retrieved {len(items)} deal activities",
    )


# ==============================================================================
# Phase 214: Unified Chronological Deal Timeline
# ==============================================================================

@router.get(
    "/{deal_id}/timeline",
    response_model=ApiResponse[List[DealTimelineEventResponse]],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("deals:read"))],
    summary="Get Deal Timeline (Phase 214)",
)
def get_deal_timeline(
    deal_id: uuid.UUID,
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Aggregates deal creation, activities, quotation events, and approvals into a unified timeline."""
    events = DealTimelineService.get_timeline(
        db=db,
        company_id=current_user.company_id,
        deal_id=deal_id,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(
        data=events,
        message=f"Retrieved {len(events)} deal timeline events",
    )
