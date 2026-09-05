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
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models.customer import Customer
from app.models.product import Product
from app.models.user import User
from app.schemas.recommendations import (
    CustomerPurchasePattern,
    CustomerSegmentationResult,
    FrequentlyBoughtTogetherResponse,
    NextBestProductResponse,
    ProductAffinityMetric,
    RecommendationItem,
    RecommendationRankingResponse,
)
from app.schemas.response import ApiResponse
from app.services.recommendations import (
    AICrossSellService,
    AIUpsellService,
    CustomerSegmentationService,
    FrequentlyBoughtTogetherService,
    NextBestProductService,
    ProductAffinityService,
    PurchasePatternAnalysisService,
    RecommendationRankingEngine,
)

router = APIRouter(prefix="/recommendations", tags=["AI Upsell / Cross-Sell Engine (B07: Phases 166–175)"])


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
