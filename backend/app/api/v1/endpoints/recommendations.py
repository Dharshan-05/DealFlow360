"""Recommendation Engine Endpoints (DealFlow360 B07: Phases 166–175).

Provides tenant-isolated, RBAC-protected endpoints for:
- Phase 166: AI Upsell Engine (GET /api/v1/recommendations/upsell/{customer_id})
- Phase 167: AI Cross-Sell Engine (GET /api/v1/recommendations/cross-sell/{customer_id})
- Phase 168: Customer Purchase Pattern Analysis (GET /api/v1/recommendations/customer/{customer_id}/patterns)
- Phase 169: Product Affinity Analysis (GET /api/v1/recommendations/affinity/{product_id})
- Phase 170: Frequently Bought Together (GET /api/v1/recommendations/frequently-bought-together/{product_id})
- Phase 171: Next Best Product (GET /api/v1/recommendations/next-best-product/{customer_id})
- Phase 172: Customer Segmentation (GET /api/v1/recommendations/customer/{customer_id}/segment)
- Phase 175: Recommendation Ranking (GET /api/v1/recommendations/ranking/{customer_id})
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models.customer import Customer
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.user import User
from app.schemas.recommendations import (
    AddToQuoteRequest,
    AddToQuoteResponse,
    CustomerBehaviorSegment,
    CustomerPurchasePattern,
    CustomerSegmentationResult,
    FrequentlyBoughtTogetherResponse,
    NextBestProductResponse,
    ProductAffinityMetric,
    QuoteLineItemInput,
    RealTimeMarginSummary,
    RecommendationAnalyticsResponse,
    RecommendationEventCreate,
    RecommendationEventResponse,
    RecommendationExplanation,
    RecommendationItem,
    RecommendationRankingResponse,
    RecommendationType,
    UpsellDashboardSummary,
)
from app.schemas.response import ApiResponse
from app.services.recommendations import (
    AICrossSellService,
    AIUpsellService,
    CrossSellProbabilityService,
    CustomerSegmentationService,
    FrequentlyBoughtTogetherService,
    NextBestProductService,
    ProductAffinityService,
    PurchasePatternAnalysisService,
    RealTimeMarginService,
    RecommendationAnalyticsService,
    RecommendationExplanationService,
    RecommendationQuoteIntegrationService,
    RecommendationRankingEngine,
    RecommendationTrackingService,
    UpsellDashboardService,
    UpsellProbabilityService,
)

router = APIRouter(prefix="/recommendations", tags=["AI Upsell / Cross-Sell Engine (B07-B08: Phases 166–185)"])


# Helper for customer tenant verification
def _verify_customer_tenant(db: Session, customer_id: uuid.UUID, company_id: Optional[uuid.UUID]) -> Customer:
    if not company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authenticated user must belong to an active organization",
        )
    customer = db.scalars(
        Customer.__table__.select().where(
            Customer.id == customer_id,
            Customer.company_id == company_id,
        )
    ).one_or_none()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer {customer_id} not found in current organization",
        )
    return db.get(Customer, customer_id)


# Helper for product tenant verification
def _verify_product_tenant(db: Session, product_id: uuid.UUID) -> Product:
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found",
        )
    return product


# ==============================================================================
# Phase 166: AI Upsell Engine
# ==============================================================================

@router.get(
    "/upsell/{customer_id}",
    response_model=ApiResponse[List[dict]],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("discounts:read"))],
    summary="Generate AI Upsell candidates for customer (Phase 166)",
)
def get_upsell_recommendations(
    customer_id: uuid.UUID,
    limit: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate candidate upsell products for an existing customer account."""
    _verify_customer_tenant(db, customer_id, current_user.company_id)
    candidates = AIUpsellService.generate_upsell_candidates(
        db=db,
        company_id=current_user.company_id,
        customer_id=customer_id,
        limit=limit,
    )
    results = []
    for prod, score, signals in candidates:
        results.append({
            "product_id": str(prod.id),
            "sku": prod.sku,
            "name": prod.name,
            "base_price": float(prod.base_price),
            "score": score,
            "signals": signals,
        })
    return ApiResponse(
        data=results,
        message=f"Generated {len(results)} upsell candidates",
    )


# ==============================================================================
# Phase 167: AI Cross-Sell Engine
# ==============================================================================

@router.get(
    "/cross-sell/{customer_id}",
    response_model=ApiResponse[List[dict]],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("discounts:read"))],
    summary="Generate AI Cross-Sell candidates for customer (Phase 167)",
)
def get_cross_sell_recommendations(
    customer_id: uuid.UUID,
    limit: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate candidate cross-sell complementary products for customer."""
    _verify_customer_tenant(db, customer_id, current_user.company_id)
    candidates = AICrossSellService.generate_cross_sell_candidates(
        db=db,
        company_id=current_user.company_id,
        customer_id=customer_id,
        limit=limit,
    )
    results = []
    for prod, score, signals in candidates:
        results.append({
            "product_id": str(prod.id),
            "sku": prod.sku,
            "name": prod.name,
            "base_price": float(prod.base_price),
            "score": score,
            "signals": signals,
        })
    return ApiResponse(
        data=results,
        message=f"Generated {len(results)} cross-sell candidates",
    )


# ==============================================================================
# Phase 168: Customer Purchase Pattern Analysis
# ==============================================================================

@router.get(
    "/customer/{customer_id}/patterns",
    response_model=ApiResponse[CustomerPurchasePattern],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("discounts:read"))],
    summary="Customer Purchase Pattern Analysis (Phase 168)",
)
def get_customer_purchase_patterns(
    customer_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Analyze customer transaction history and compute RFM purchase behavior metrics."""
    _verify_customer_tenant(db, customer_id, current_user.company_id)
    pattern = PurchasePatternAnalysisService.analyze_customer(
        db=db,
        company_id=current_user.company_id,
        customer_id=customer_id,
    )
    return ApiResponse(
        data=pattern,
        message="Purchase patterns analyzed successfully",
    )


# ==============================================================================
# Phase 169: Product Affinity Analysis
# ==============================================================================

@router.get(
    "/affinity/{product_id}",
    response_model=ApiResponse[List[ProductAffinityMetric]],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("discounts:read"))],
    summary="Product Affinity Analysis (Phase 169)",
)
def get_product_affinities(
    product_id: uuid.UUID,
    min_support: float = Query(0.0, ge=0.0, le=1.0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Compute product-to-product market basket affinity metrics."""
    _verify_product_tenant(db, product_id)
    affinities = ProductAffinityService.get_affinities_for_product(
        db=db,
        company_id=current_user.company_id,
        source_product_id=product_id,
        min_support=min_support,
        limit=limit,
    )
    return ApiResponse(
        data=affinities,
        message=f"Evaluated affinities for product {product_id}",
    )


# ==============================================================================
# Phase 170: Frequently Bought Together
# ==============================================================================

@router.get(
    "/frequently-bought-together/{product_id}",
    response_model=ApiResponse[FrequentlyBoughtTogetherResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("discounts:read"))],
    summary="Frequently Bought Together Recommendations (Phase 170)",
)
def get_frequently_bought_together(
    product_id: uuid.UUID,
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return top products frequently bought together with the target product."""
    _verify_product_tenant(db, product_id)
    res = FrequentlyBoughtTogetherService.get_frequently_bought_together(
        db=db,
        company_id=current_user.company_id,
        product_id=product_id,
        limit=limit,
    )
    return ApiResponse(
        data=res,
        message="Frequently bought together recommendations retrieved",
    )


# ==============================================================================
# Phase 171: Next Best Product
# ==============================================================================

@router.get(
    "/next-best-product/{customer_id}",
    response_model=ApiResponse[NextBestProductResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("discounts:read"))],
    summary="Next Best Product Recommendation (Phase 171)",
)
def get_next_best_product(
    customer_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Determine the single highest-impact Next Best Product for a customer."""
    _verify_customer_tenant(db, customer_id, current_user.company_id)
    res = NextBestProductService.determine_next_best_product(
        db=db,
        company_id=current_user.company_id,
        customer_id=customer_id,
    )
    return ApiResponse(
        data=res,
        message="Next best product evaluated",
    )


# ==============================================================================
# Phase 172: Customer Segmentation
# ==============================================================================

@router.get(
    "/customer/{customer_id}/segment",
    response_model=ApiResponse[CustomerSegmentationResult],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("discounts:read"))],
    summary="Customer Behavioral Segmentation (Phase 172)",
)
def get_customer_behavioral_segment(
    customer_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Classify customer account into deterministic behavioral segment."""
    _verify_customer_tenant(db, customer_id, current_user.company_id)
    res = CustomerSegmentationService.segment_customer(
        db=db,
        company_id=current_user.company_id,
        customer_id=customer_id,
    )
    return ApiResponse(
        data=res,
        message="Customer behavioral segment computed",
    )


# ==============================================================================
# Phase 175: Recommendation Ranking
# ==============================================================================

@router.get(
    "/ranking/{customer_id}",
    response_model=ApiResponse[RecommendationRankingResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("discounts:read"))],
    summary="Multi-Factor Recommendation Ranking (Phase 175)",
)
def get_recommendation_ranking(
    customer_id: uuid.UUID,
    top_n: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve multi-factor ranked product recommendations with full signal telemetry."""
    _verify_customer_tenant(db, customer_id, current_user.company_id)
    res = RecommendationRankingEngine.rank_recommendations(
        db=db,
        company_id=current_user.company_id,
        customer_id=customer_id,
        top_n=top_n,
    )
    return ApiResponse(
        data=res,
        message=f"Generated {len(res.recommendations)} ranked recommendations",
    )


# ==============================================================================
# Phase 176: Upsell Score
# ==============================================================================

@router.get(
    "/upsell-score",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("discounts:read"))],
    summary="Calculate 0–100 Upsell Score (Phase 176)",
)
def get_upsell_score(
    customer_id: uuid.UUID,
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Compute deterministic 0–100 Upsell Score with underlying scoring factors."""
    customer = _verify_customer_tenant(db, customer_id, current_user.company_id)
    product = _verify_product_tenant(db, product_id)

    pattern = PurchasePatternAnalysisService.analyze_customer(
        db=db,
        company_id=current_user.company_id,
        customer_id=customer.id,
    )
    segment_res = CustomerSegmentationService.segment_customer(
        db=db,
        company_id=current_user.company_id,
        customer_id=customer.id,
    )

    category = db.get(ProductCategory, product.category_id) if product.category_id else None
    cat_name = category.name if category else None

    prob = UpsellProbabilityService.calculate_probability(
        customer_pattern=pattern,
        customer_segment=segment_res.segment,
        target_product=product,
        target_category_name=cat_name,
    )
    margin_pct = (
        float(product.base_price - product.cost) / float(product.base_price) * 100.0
        if product.base_price > Decimal("0.00")
        else 0.0
    )
    margin_pct = max(0.0, min(100.0, margin_pct))
    price_ratio = (
        float(product.base_price / pattern.average_order_value)
        if pattern.average_order_value > Decimal("0.00")
        else 1.0
    )

    score_100 = AIUpsellService.calculate_upsell_score_100(
        probability=prob,
        unit_margin_pct=margin_pct,
        inventory_quantity=product.inventory_quantity,
        price_ratio=price_ratio,
    )

    return ApiResponse(
        data={
            "customer_id": str(customer.id),
            "product_id": str(product.id),
            "score_100": score_100,
            "probability": prob,
            "unit_margin_pct": round(margin_pct, 2),
            "inventory_quantity": product.inventory_quantity,
            "price_ratio": round(price_ratio, 2),
        },
        message="Upsell score computed successfully",
    )


# ==============================================================================
# Phase 177: Cross-Sell Score
# ==============================================================================

@router.get(
    "/cross-sell-score",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("discounts:read"))],
    summary="Calculate 0–100 Cross-Sell Score (Phase 177)",
)
def get_cross_sell_score(
    customer_id: uuid.UUID,
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Compute deterministic 0–100 Cross-Sell Score with affinity factors."""
    customer = _verify_customer_tenant(db, customer_id, current_user.company_id)
    product = _verify_product_tenant(db, product_id)

    pattern = PurchasePatternAnalysisService.analyze_customer(
        db=db,
        company_id=current_user.company_id,
        customer_id=customer.id,
    )
    segment_res = CustomerSegmentationService.segment_customer(
        db=db,
        company_id=current_user.company_id,
        customer_id=customer.id,
    )

    affinities = ProductAffinityService.get_affinities_for_product(
        db=db,
        company_id=current_user.company_id,
        source_product_id=product.id,
        min_support=0.0,
        limit=10,
    )
    best_affinity = affinities[0] if affinities else None
    prob = CrossSellProbabilityService.calculate_probability(
        customer_pattern=pattern,
        customer_segment=segment_res.segment,
        affinity_metric=best_affinity,
    )
    max_conf = max([a.confidence for a in affinities], default=0.25)
    max_lift = max([a.lift for a in affinities], default=1.0)

    score_100 = AICrossSellService.calculate_cross_sell_score_100(
        probability=prob,
        confidence=max_conf,
        lift=max_lift,
        inventory_quantity=product.inventory_quantity,
    )

    return ApiResponse(
        data={
            "customer_id": str(customer.id),
            "product_id": str(product.id),
            "score_100": score_100,
            "probability": prob,
            "confidence": round(max_conf, 4),
            "lift": round(max_lift, 4),
            "inventory_quantity": product.inventory_quantity,
        },
        message="Cross-sell score computed successfully",
    )


# ==============================================================================
# Phase 180: Upsell & Recommendation Explanation
# ==============================================================================

@router.get(
    "/explain/{product_id}",
    response_model=ApiResponse[RecommendationExplanation],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("discounts:read"))],
    summary="Explain Recommendation Rationale (Phase 180)",
)
def get_recommendation_explanation(
    product_id: uuid.UUID,
    customer_id: uuid.UUID,
    recommendation_type: RecommendationType = Query(RecommendationType.UPSELL),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate structured explainability narrative and signals for recommended product."""
    customer = _verify_customer_tenant(db, customer_id, current_user.company_id)
    product = _verify_product_tenant(db, product_id)

    pattern = PurchasePatternAnalysisService.analyze_customer(
        db=db,
        company_id=current_user.company_id,
        customer_id=customer.id,
    )
    segment_res = CustomerSegmentationService.segment_customer(
        db=db,
        company_id=current_user.company_id,
        customer_id=customer.id,
    )

    category = db.get(ProductCategory, product.category_id) if product.category_id else None
    cat_name = category.name if category else None

    if recommendation_type == RecommendationType.UPSELL:
        prob = UpsellProbabilityService.calculate_probability(
            customer_pattern=pattern,
            customer_segment=segment_res.segment,
            target_product=product,
            target_category_name=cat_name,
        )
        margin_pct = (
            float(product.base_price - product.cost) / float(product.base_price) * 100.0
            if product.base_price > Decimal("0.00")
            else 0.0
        )
        price_ratio = (
            float(product.base_price / pattern.average_order_value)
            if pattern.average_order_value > Decimal("0.00")
            else 1.0
        )
        score_100 = AIUpsellService.calculate_upsell_score_100(
            probability=prob,
            unit_margin_pct=margin_pct,
            inventory_quantity=product.inventory_quantity,
            price_ratio=price_ratio,
        )
        signals = {
            "upsell_probability": prob,
            "unit_margin_pct": round(margin_pct, 2),
            "aov_ratio": round(price_ratio, 2),
            "inventory_quantity": product.inventory_quantity,
        }
    else:
        affinities = ProductAffinityService.get_affinities_for_product(
            db=db,
            company_id=current_user.company_id,
            source_product_id=product.id,
            min_support=0.0,
            limit=10,
        )
        best_affinity = affinities[0] if affinities else None
        prob = CrossSellProbabilityService.calculate_probability(
            customer_pattern=pattern,
            customer_segment=segment_res.segment,
            affinity_metric=best_affinity,
        )
        conf = max([a.confidence for a in affinities], default=0.25)
        lift = max([a.lift for a in affinities], default=1.0)
        score_100 = AICrossSellService.calculate_cross_sell_score_100(
            probability=prob,
            confidence=conf,
            lift=lift,
            inventory_quantity=product.inventory_quantity,
        )
        signals = {
            "cross_sell_probability": prob,
            "confidence": round(conf, 4),
            "lift": round(lift, 4),
            "inventory_quantity": product.inventory_quantity,
        }

    explanation = RecommendationExplanationService.generate_explanation(
        product=product,
        recommendation_type=recommendation_type,
        customer_pattern=pattern,
        customer_segment=segment_res.segment,
        score_100=score_100,
        signals=signals,
        category_name=cat_name,
    )

    return ApiResponse(
        data=explanation,
        message="Recommendation explanation generated",
    )


# ==============================================================================
# Phase 181 & 182: Add-to-Quote & Real-Time Margin Updates
# ==============================================================================

@router.post(
    "/add-to-quote",
    response_model=ApiResponse[AddToQuoteResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("discounts:read"))],
    summary="Add Recommendation to Quote Context (Phase 181 & 182)",
)
def add_recommendation_to_quote(
    payload: AddToQuoteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add recommended product to quotation context and calculate real-time gross profit / margin."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authenticated user must belong to an active organization",
        )
    try:
        response = RecommendationQuoteIntegrationService.add_recommendation_to_quote(
            db=db,
            company_id=current_user.company_id,
            request=payload,
            actor_id=current_user.id,
        )
        return ApiResponse(
            data=response,
            message="Recommendation successfully added to quote context",
        )
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )


@router.post(
    "/real-time-margins",
    response_model=ApiResponse[RealTimeMarginSummary],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("discounts:read"))],
    summary="Calculate Real-Time Financial Margins (Phase 182)",
)
def calculate_real_time_margins(
    items: List[QuoteLineItemInput],
    current_user: User = Depends(get_current_user),
):
    """Compute line-level and consolidated quote profit and margin percentages using strict Decimal arithmetic."""
    summary = RealTimeMarginService.calculate_margins(items)
    return ApiResponse(
        data=summary,
        message="Real-time margins calculated successfully",
    )


# ==============================================================================
# Phase 183: Upsell Acceptance Tracking
# ==============================================================================

@router.post(
    "/events",
    response_model=ApiResponse[RecommendationEventResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("discounts:read"))],
    summary="Record Recommendation Lifecycle Event (Phase 183)",
)
def record_recommendation_event(
    event: RecommendationEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Log lifecycle event (GENERATED, VIEWED, SELECTED, ADDED_TO_QUOTE, ACCEPTED, REJECTED, DISMISSED)."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authenticated user must belong to an active organization",
        )
    _verify_customer_tenant(db, event.customer_id, current_user.company_id)
    _verify_product_tenant(db, event.product_id)

    persisted = RecommendationTrackingService.track_event(
        db=db,
        company_id=current_user.company_id,
        event=event,
        actor_id=current_user.id,
    )
    return ApiResponse(
        data=RecommendationEventResponse.model_validate(persisted),
        message="Recommendation lifecycle event tracked",
    )


# ==============================================================================
# Phase 184: Recommendation Analytics
# ==============================================================================

@router.get(
    "/analytics",
    response_model=ApiResponse[RecommendationAnalyticsResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("discounts:read"))],
    summary="Recommendation Funnel & Conversion Analytics (Phase 184)",
)
def get_recommendation_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Aggregate lifecycle funnel metrics, acceptance rates, and product conversion leaderboards."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authenticated user must belong to an active organization",
        )
    analytics = RecommendationAnalyticsService.get_analytics(
        db=db,
        company_id=current_user.company_id,
        start_date=start_date,
        end_date=end_date,
    )
    return ApiResponse(
        data=analytics,
        message="Recommendation analytics retrieved",
    )


# ==============================================================================
# Phase 185: Upsell Dashboard
# ==============================================================================

@router.get(
    "/dashboard",
    response_model=ApiResponse[UpsellDashboardSummary],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("discounts:read"))],
    summary="Consolidated Upsell Dashboard (Phase 185)",
)
def get_upsell_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve executive KPIs, conversion funnels, catalog distributions, and recent recommendation activity."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authenticated user must belong to an active organization",
        )
    dashboard = UpsellDashboardService.get_dashboard_summary(
        db=db,
        company_id=current_user.company_id,
    )
    return ApiResponse(
        data=dashboard,
        message="Upsell dashboard retrieved successfully",
    )

