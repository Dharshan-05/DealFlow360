"""Discount Intelligence Endpoints (DealFlow360 G23: Phases 111–115).

Provides REST APIs for:
- Phase 111: Recommended Discount Engine (POST /governance/discounts/intelligence/recommend)
- Phase 112: Maximum Safe Discount (POST /governance/discounts/intelligence/maximum-safe)
- Phase 113: Margin Protection Engine (POST /governance/discounts/intelligence/margin-protection)
- Phase 114: Historical Discount Analysis (GET /governance/discounts/intelligence/history)
- Phase 115: Customer Discount Analysis (GET /governance/discounts/intelligence/customer/{customer_id})
"""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models.user import User
from app.schemas.discount_intelligence import (
    CustomerDiscountAnalysisResponse,
    DiscountRecommendationRequest,
    DiscountRecommendationResponse,
    HistoricalDiscountAnalysisResponse,
    MarginProtectionRequest,
    MarginProtectionResponse,
    MaximumSafeDiscountRequest,
    MaximumSafeDiscountResponse,
)
from app.services.discount_intelligence import (
    CustomerDiscountAnalysisService,
    DiscountHistoryAnalysisService,
    DiscountRecommendationEngine,
    MarginProtectionEngine,
    MaximumSafeDiscountEngine,
)

router = APIRouter(prefix="/governance/discounts/intelligence", tags=["Discount Intelligence"])


# ==============================================================================
# Phase 113: Margin Protection Endpoint
# ==============================================================================

@router.post("/margin-protection", response_model=MarginProtectionResponse)
def evaluate_margin_protection(
    payload: MarginProtectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("discounts:read")),
):
    """Calculates gross margin erosion and computes the maximum discount allowed

    without breaching the required minimum profit margin.
    Uses strict Decimal arithmetic.
    """
    return MarginProtectionEngine.evaluate(
        db=db,
        company_id=current_user.company_id,
        product_id=payload.product_id,
        selling_price_override=payload.selling_price,
        min_margin_percentage=payload.min_margin_percentage,
    )


# ==============================================================================
# Phase 112: Maximum Safe Discount Endpoint
# ==============================================================================

@router.post("/maximum-safe", response_model=MaximumSafeDiscountResponse)
def calculate_maximum_safe_discount(
    payload: MaximumSafeDiscountRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("discounts:read")),
):
    """Calculates the absolute upper bound of a safe discount by intersecting

    governance policy ceilings, actor authority limits, and product economics.
    """
    return MaximumSafeDiscountEngine.evaluate(
        db=db,
        company_id=current_user.company_id,
        customer_id=payload.customer_id,
        product_id=payload.product_id,
        actor=current_user,
        selling_price_override=payload.selling_price,
        min_margin_percentage=payload.min_margin_percentage,
    )


# ==============================================================================
# Phase 114: Historical Discount Analysis Endpoint
# ==============================================================================

@router.get("/history", response_model=HistoricalDiscountAnalysisResponse)
def get_historical_discount_analysis(
    customer_id: Optional[uuid.UUID] = Query(None, description="Optional customer filter"),
    product_id: Optional[uuid.UUID] = Query(None, description="Optional product filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("discounts:read")),
):
    """Aggregates and analyzes historical discount performance for a company,

    customer, and/or product across historical transaction records.
    Strictly isolated by company_id.
    """
    return DiscountHistoryAnalysisService.analyze_history(
        db=db,
        company_id=current_user.company_id,
        customer_id=customer_id,
        product_id=product_id,
    )


# ==============================================================================
# Phase 115: Customer Discount Analysis Endpoint
# ==============================================================================

@router.get("/customer/{customer_id}", response_model=CustomerDiscountAnalysisResponse)
def get_customer_discount_analysis(
    customer_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("discounts:read")),
):
    """Deep customer-centric financial intelligence linking historical behavior

    with active governance ceilings and relationship profile.
    """
    return CustomerDiscountAnalysisService.analyze_customer(
        db=db,
        company_id=current_user.company_id,
        customer_id=customer_id,
    )


# ==============================================================================
# Phase 111: Recommended Discount Engine Endpoint
# ==============================================================================

@router.post("/recommend", response_model=DiscountRecommendationResponse)
def get_recommended_discount(
    payload: DiscountRecommendationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("discounts:read")),
):
    """Generates a deterministic, explainable discount recommendation that

    maximizes deal closing potential while preserving margin and obeying governance.
    """
    return DiscountRecommendationEngine.recommend(
        db=db,
        company_id=current_user.company_id,
        customer_id=payload.customer_id,
        product_id=payload.product_id,
        actor=current_user,
        selling_price_override=payload.selling_price,
        min_margin_percentage=payload.min_margin_percentage,
        benchmark_discount=payload.benchmark_discount,
    )
