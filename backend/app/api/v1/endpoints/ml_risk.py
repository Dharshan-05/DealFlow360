"""ML Risk Dataset & Feature Engineering Endpoints (DealFlow360 B01: Phases 121–125).

Provides tenant-isolated, RBAC-protected API endpoints for:
- Phase 121: ML Dataset Preparation (GET /api/v1/ml/datasets/deals)
- Phase 122: Historical Deal Dataset Extraction (GET /api/v1/ml/datasets/deals/raw)
- Phase 123: Feature Engineering Vector Generation
- Phase 124: Discount Feature Inspection
- Phase 125: Margin Feature Inspection

Strictly non-ML-training: returns clean, normalized datasets and feature vectors.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.endpoints.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models.user import User
from app.schemas.ml_risk import (
    DatasetPreparationResponse,
    DiscountFeatures,
    EngineeredFeatureVector,
    MarginFeatures,
    RawDealRecord,
)
from app.services.ml_risk import (
    DiscountFeatureEngineer,
    HistoricalDealDatasetExtractor,
    MarginFeatureEngineer,
    MLDatasetPreparationService,
)

router = APIRouter(prefix="/ml", tags=["ML Risk Engine (Phases 121–125)"])


# ==============================================================================
# Phase 121: ML Dataset Preparation Endpoint
# ==============================================================================

@router.get(
    "/datasets/deals",
    response_model=DatasetPreparationResponse,
    summary="Prepare and extract ML-ready historical deal dataset (Phase 121–125)",
)
def prepare_deal_dataset(
    start_date: Optional[datetime] = Query(None, description="Filter deals from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter deals up to this date"),
    min_deal_value: Optional[Decimal] = Query(None, description="Minimum deal gross value"),
    status: Optional[str] = Query(None, description="Filter by deal status (WON, LOST, etc.)"),
    current_user: User = Depends(require_permission("discounts:read")),
    db: Session = Depends(get_db),
) -> DatasetPreparationResponse:
    """Prepare a deterministic, feature-engineered tabular dataset for ML risk analysis (Phase 121).
    Tenant-isolated by authenticated user's company_id.
    """
    return MLDatasetPreparationService.prepare_deal_risk_dataset(
        db=db,
        company_id=current_user.company_id,
        start_date=start_date,
        end_date=end_date,
        min_deal_value=min_deal_value,
        filter_status=status,
    )


# ==============================================================================
# Phase 122: Historical Deal Raw Dataset Extractor Endpoint
# ==============================================================================

@router.get(
    "/datasets/deals/raw",
    response_model=List[RawDealRecord],
    summary="Extract raw point-in-time historical deal records (Phase 122)",
)
def extract_raw_deal_dataset(
    start_date: Optional[datetime] = Query(None, description="Filter deals from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter deals up to this date"),
    current_user: User = Depends(require_permission("discounts:read")),
    db: Session = Depends(get_db),
) -> List[RawDealRecord]:
    """Extract normalized point-in-time deal records directly from verified business entities (Phase 122).
    Excludes sensitive user secrets and credentials.
    """
    return HistoricalDealDatasetExtractor.extract_records(
        db=db,
        company_id=current_user.company_id,
        start_date=start_date,
        end_date=end_date,
    )


# ==============================================================================
# Phase 124 & 125: Feature Calculation Utilities
# ==============================================================================

@router.get(
    "/features/discount",
    response_model=DiscountFeatures,
    summary="Compute discount features for a proposal (Phase 124)",
)
def compute_discount_features(
    requested_discount_pct: Decimal = Query(..., description="Requested discount percentage"),
    effective_ceiling_pct: Decimal = Query(Decimal("15.00"), description="Active policy ceiling percentage"),
    customer_historical_avg_pct: Decimal = Query(Decimal("0.00"), description="Customer lifetime discount avg %"),
    tier_discount_limit: Decimal = Query(Decimal("10.00"), description="Tier baseline discount limit"),
    deal_value: Decimal = Query(Decimal("1000.00"), description="Gross deal value"),
    has_prior_history: bool = Query(False, description="Whether customer has discount history"),
    current_user: User = Depends(require_permission("discounts:read")),
) -> DiscountFeatures:
    """Compute Phase 124 discount features."""
    return DiscountFeatureEngineer.compute(
        requested_discount_pct=requested_discount_pct,
        effective_ceiling_pct=effective_ceiling_pct,
        customer_historical_avg_pct=customer_historical_avg_pct,
        tier_discount_limit=tier_discount_limit,
        deal_value=deal_value,
        has_prior_history=has_prior_history,
    )


@router.get(
    "/features/margin",
    response_model=MarginFeatures,
    summary="Compute margin features for a proposal (Phase 125)",
)
def compute_margin_features(
    selling_price: Decimal = Query(..., description="Base selling price"),
    unit_cost: Decimal = Query(..., description="Product unit cost"),
    discount_pct: Decimal = Query(Decimal("0.00"), description="Proposed discount percentage"),
    current_user: User = Depends(require_permission("discounts:read")),
) -> MarginFeatures:
    """Compute Phase 125 margin features."""
    return MarginFeatureEngineer.compute(
        selling_price=selling_price,
        unit_cost=unit_cost,
        discount_pct=discount_pct,
    )
