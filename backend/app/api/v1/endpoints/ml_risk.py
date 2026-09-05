"""ML Risk Dataset & Feature Engineering Endpoints (DealFlow360 B01 & B02: Phases 121–130).

Provides tenant-isolated, RBAC-protected API endpoints for:
- Phase 121: ML Dataset Preparation (GET /api/v1/ml/datasets/deals)
- Phase 122: Historical Deal Dataset Extraction (GET /api/v1/ml/datasets/deals/raw)
- Phase 123: Feature Engineering Vector Generation
- Phase 124: Discount Feature Inspection
- Phase 125: Margin Feature Inspection
- Phase 126: Customer Features Inspection
- Phase 127: Deal Value Features Inspection
- Phase 128: Discount Behavior Features Inspection
- Phase 129: Margin Behavior Features Inspection
- Phase 130: Risk Target Inspection

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
    CustomerFeatures,
    DatasetPreparationResponse,
    DealValueFeatures,
    DiscountBehaviorFeatures,
    DiscountFeatures,
    EngineeredFeatureVector,
    MarginBehaviorFeatures,
    MarginFeatures,
    ModelArtifact,
    ModelComparisonReport,
    RawDealRecord,
    RiskDatasetPipelineResult,
    RiskTarget,
    AIRiskDashboardSummary,
    CalibrationMetadata,
    FeatureContribution,
    ModelEvaluationMetrics,
    ModelSelectionResult,
    ModelTrainingPipelineResult,
    RiskFactorDetail,
    RiskPredictionRequest,
    RiskPredictionResponse,
)
from app.services.ml_risk import (
    AIRiskDashboardService,
    CustomerFeatureEngineer,
    DealValueFeatureEngineer,
    DiscountBehaviorFeatureEngineer,
    DiscountFeatureEngineer,
    HistoricalDealDatasetExtractor,
    LightGBMRiskModelService,
    MarginBehaviorFeatureEngineer,
    MarginFeatureEngineer,
    MLDatasetPreparationService,
    ModelComparisonService,
    ModelMetricsEvaluator,
    ModelSelectionService,
    ModelTrainingPipelineService,
    ProbabilityCalibrationService,
    RandomForestRiskModelService,
    RiskDatasetPipelineService,
    RiskFactorExtractionService,
    RiskPredictionInferenceService,
    RiskTargetGenerator,
    TreeExplainabilityService,
    XGBoostRiskModelService,
)

router = APIRouter(prefix="/ml", tags=["AI/ML Risk Engine (Phases 121–145)"])


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


# ==============================================================================
# Phase 126: Customer Features Inspection Endpoint
# ==============================================================================

@router.get(
    "/features/customer",
    response_model=CustomerFeatures,
    summary="Compute customer features for a deal (Phase 126)",
)
def compute_customer_features(
    tenure_days: int = Query(0, description="Customer relationship age in days"),
    customer_tier: str = Query("STANDARD", description="Customer tier code"),
    tier_discount_limit: Decimal = Query(Decimal("10.00"), description="Tier discount limit %"),
    lifetime_orders: int = Query(0, description="Historical settled order count"),
    lifetime_revenue: Decimal = Query(Decimal("0.00"), description="Prior total settled gross revenue"),
    lifetime_settled: Decimal = Query(Decimal("0.00"), description="Prior total settled net amount"),
    failed_payments: int = Query(0, description="Historical failed/defaulted payment count"),
    total_payments: int = Query(0, description="Historical total payment count"),
    avg_discount_pct: Decimal = Query(Decimal("0.00"), description="Historical average discount %"),
    discount_count: int = Query(0, description="Historical discount count"),
    current_user: User = Depends(require_permission("discounts:read")),
) -> CustomerFeatures:
    """Compute Phase 126 Customer Features."""
    return CustomerFeatureEngineer.compute(
        tenure_days=tenure_days,
        customer_tier=customer_tier,
        tier_discount_limit=tier_discount_limit,
        lifetime_orders=lifetime_orders,
        lifetime_revenue=lifetime_revenue,
        lifetime_settled=lifetime_settled,
        failed_payments=failed_payments,
        total_payments=total_payments,
        avg_discount_pct=avg_discount_pct,
        discount_count=discount_count,
    )


# ==============================================================================
# Phase 127: Deal Value Features Inspection Endpoint
# ==============================================================================

@router.get(
    "/features/deal-value",
    response_model=DealValueFeatures,
    summary="Compute deal value features for a deal (Phase 127)",
)
def compute_deal_value_features(
    deal_value: Decimal = Query(..., description="Current deal nominal gross value"),
    customer_aov: Decimal = Query(Decimal("0.00"), description="Customer prior average order value"),
    has_prior_orders: bool = Query(False, description="Whether customer has prior orders"),
    current_user: User = Depends(require_permission("discounts:read")),
) -> DealValueFeatures:
    """Compute Phase 127 Deal Value Features."""
    return DealValueFeatureEngineer.compute(
        deal_value=deal_value,
        customer_aov=customer_aov,
        has_prior_orders=has_prior_orders,
    )


# ==============================================================================
# Phase 128: Discount Behavior Features Inspection Endpoint
# ==============================================================================

@router.get(
    "/features/discount-behavior",
    response_model=DiscountBehaviorFeatures,
    summary="Compute customer historical discount behavior features (Phase 128)",
)
def compute_discount_behavior_features(
    discount_history: List[Decimal] = Query(default=[], description="List of prior discount percentages"),
    total_prior_orders: int = Query(0, description="Total prior orders"),
    current_user: User = Depends(require_permission("discounts:read")),
) -> DiscountBehaviorFeatures:
    """Compute Phase 128 Discount Behavior Features."""
    return DiscountBehaviorFeatureEngineer.compute(
        prior_discounts=discount_history,
        total_prior_orders=total_prior_orders,
    )


# ==============================================================================
# Phase 129: Margin Behavior Features Inspection Endpoint
# ==============================================================================

@router.get(
    "/features/margin-behavior",
    response_model=MarginBehaviorFeatures,
    summary="Compute customer historical margin behavior features (Phase 129)",
)
def compute_margin_behavior_features(
    margin_history: List[Decimal] = Query(default=[], description="List of prior realized margin percentages"),
    current_user: User = Depends(require_permission("discounts:read")),
) -> MarginBehaviorFeatures:
    """Compute Phase 129 Margin Behavior Features."""
    return MarginBehaviorFeatureEngineer.compute(
        prior_applied_discounts=margin_history,
    )


# ==============================================================================
# Phase 130: Risk Target Inspection Endpoint
# ==============================================================================

@router.get(
    "/features/risk-target",
    response_model=RiskTarget,
    summary="Compute deterministic risk target classification (Phase 130)",
)
def compute_risk_target(
    effective_ceiling: Decimal = Query(Decimal("15.00"), description="Active policy ceiling percentage"),
    margin_pct: Decimal = Query(Decimal("25.00"), description="Discounted gross margin percentage"),
    requested_discount_pct: Decimal = Query(Decimal("10.00"), description="Requested discount %"),
    risk_level: str = Query("LOW", description="Risk level string"),
    decision_outcome: str = Query("APPROVED", description="Decision outcome"),
    deal_status: str = Query("WON", description="Deal outcome status"),
    reason_code: str = Query("OPTIMAL", description="Decision reason code"),
    prior_failed_payments_count: int = Query(0, description="Prior failed payments count"),
    current_user: User = Depends(require_permission("discounts:read")),
) -> RiskTarget:
    """Compute Phase 130 Deterministic Risk Target."""
    return RiskTargetGenerator.generate_target(
        record=None,
        effective_ceiling=effective_ceiling,
        margin_pct=margin_pct,
        requested_discount_pct=requested_discount_pct,
        risk_level=risk_level,
        decision_outcome=decision_outcome,
        deal_status=deal_status,
        reason_code=reason_code,
        prior_failed_payments_count=prior_failed_payments_count,
    )


# ==============================================================================
# Phase 131: Risk Dataset Pipeline Endpoint
# ==============================================================================

@router.post(
    "/pipeline/risk-dataset",
    response_model=RiskDatasetPipelineResult,
    summary="Execute Risk Dataset Pipeline with deterministic train/val/test split (Phase 131)",
)
def execute_risk_dataset_pipeline(
    train_ratio: float = Query(0.70, ge=0.5, le=0.9, description="Training split ratio"),
    val_ratio: float = Query(0.15, ge=0.05, le=0.3, description="Validation split ratio"),
    test_ratio: float = Query(0.15, ge=0.05, le=0.3, description="Test split ratio"),
    random_seed: int = Query(42, description="Deterministic random seed"),
    current_user: User = Depends(require_permission("discounts:read")),
    db: Session = Depends(get_db),
) -> RiskDatasetPipelineResult:
    """Execute the Phase 131 Risk Dataset Pipeline for authenticated company/tenant."""
    return RiskDatasetPipelineService.execute_pipeline(
        db=db,
        company_id=current_user.company_id,
        train_ratio=train_ratio,
        val_ratio=val_ratio,
        test_ratio=test_ratio,
        random_seed=random_seed,
    )


# ==============================================================================
# Phase 132: XGBoost Model Training Endpoint
# ==============================================================================

@router.post(
    "/models/xgboost/train",
    response_model=ModelArtifact,
    summary="Train XGBoost Risk Model on Phase 131 pipeline data (Phase 132)",
)
def train_xgboost_model(
    n_estimators: int = Query(15, ge=1, le=100, description="Boosting iterations"),
    max_depth: int = Query(4, ge=1, le=10, description="Maximum tree depth"),
    learning_rate: float = Query(0.1, ge=0.01, le=1.0, description="Shrinkage rate"),
    reg_lambda: float = Query(1.0, ge=0.0, le=10.0, description="L2 regularization"),
    random_seed: int = Query(42, description="Deterministic random seed"),
    current_user: User = Depends(require_permission("discounts:read")),
    db: Session = Depends(get_db),
) -> ModelArtifact:
    """Train an XGBoost Risk Model using the Phase 131 dataset pipeline."""
    pipeline_res = RiskDatasetPipelineService.execute_pipeline(
        db=db,
        company_id=current_user.company_id,
        random_seed=random_seed,
    )
    return XGBoostRiskModelService.train(
        pipeline_result=pipeline_res,
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
        reg_lambda=reg_lambda,
        random_seed=random_seed,
    )


# ==============================================================================
# Phase 133: LightGBM Model Training Endpoint
# ==============================================================================

@router.post(
    "/models/lightgbm/train",
    response_model=ModelArtifact,
    summary="Train LightGBM Risk Model on Phase 131 pipeline data (Phase 133)",
)
def train_lightgbm_model(
    n_estimators: int = Query(15, ge=1, le=100, description="Boosting iterations"),
    num_leaves: int = Query(16, ge=2, le=64, description="Max leaves per tree"),
    learning_rate: float = Query(0.1, ge=0.01, le=1.0, description="Shrinkage rate"),
    min_child_samples: int = Query(2, ge=1, le=50, description="Min samples per leaf"),
    random_seed: int = Query(42, description="Deterministic random seed"),
    current_user: User = Depends(require_permission("discounts:read")),
    db: Session = Depends(get_db),
) -> ModelArtifact:
    """Train a LightGBM Risk Model using the Phase 131 dataset pipeline."""
    pipeline_res = RiskDatasetPipelineService.execute_pipeline(
        db=db,
        company_id=current_user.company_id,
        random_seed=random_seed,
    )
    return LightGBMRiskModelService.train(
        pipeline_result=pipeline_res,
        n_estimators=n_estimators,
        num_leaves=num_leaves,
        learning_rate=learning_rate,
        min_child_samples=min_child_samples,
        random_seed=random_seed,
    )


# ==============================================================================
# Phase 134: Random Forest Baseline Training Endpoint
# ==============================================================================

@router.post(
    "/models/random-forest/train",
    response_model=ModelArtifact,
    summary="Train Random Forest Baseline Model on Phase 131 pipeline data (Phase 134)",
)
def train_random_forest_baseline(
    n_estimators: int = Query(15, ge=1, le=100, description="Forest tree count"),
    max_depth: int = Query(5, ge=1, le=12, description="Maximum tree depth"),
    max_features_ratio: float = Query(0.5, ge=0.1, le=1.0, description="Feature subsampling ratio"),
    min_samples_split: int = Query(2, ge=2, le=50, description="Min samples to split"),
    random_seed: int = Query(42, description="Deterministic random seed"),
    current_user: User = Depends(require_permission("discounts:read")),
    db: Session = Depends(get_db),
) -> ModelArtifact:
    """Train a Random Forest Baseline Model using the Phase 131 dataset pipeline."""
    pipeline_res = RiskDatasetPipelineService.execute_pipeline(
        db=db,
        company_id=current_user.company_id,
        random_seed=random_seed,
    )
    return RandomForestRiskModelService.train(
        pipeline_result=pipeline_res,
        n_estimators=n_estimators,
        max_depth=max_depth,
        max_features_ratio=max_features_ratio,
        min_samples_split=min_samples_split,
        random_seed=random_seed,
    )


# ==============================================================================
# Phase 135: Model Comparison Endpoint
# ==============================================================================

@router.post(
    "/models/compare",
    response_model=ModelComparisonReport,
    summary="Compare XGBoost, LightGBM, and Random Forest models on common test split (Phase 135)",
)
def compare_risk_models(
    random_seed: int = Query(42, description="Deterministic random seed"),
    current_user: User = Depends(require_permission("discounts:read")),
    db: Session = Depends(get_db),
) -> ModelComparisonReport:
    """Execute model comparison across XGBoost, LightGBM, and Random Forest on common test split (Phase 135)."""
    return ModelComparisonService.compare_models(
        db=db,
        company_id=current_user.company_id,
        random_seed=random_seed,
    )


# ==============================================================================
# Phase 136: Model Selection Endpoint
# ==============================================================================

@router.post(
    "/models/select",
    response_model=ModelSelectionResult,
    summary="Select Champion Risk Model deterministically (Phase 136)",
)
def select_champion_model(
    random_seed: int = Query(42, description="Deterministic random seed"),
    current_user: User = Depends(require_permission("discounts:read")),
    db: Session = Depends(get_db),
) -> ModelSelectionResult:
    """Execute model comparison across all candidates and deterministically select champion."""
    comparison_report = ModelComparisonService.compare_models(
        db=db,
        company_id=current_user.company_id,
        random_seed=random_seed,
    )
    return ModelSelectionService.select_champion(comparison_report)


# ==============================================================================
# Phase 137: Model Training Pipeline Endpoint
# ==============================================================================

@router.post(
    "/pipeline/train-and-select",
    response_model=ModelTrainingPipelineResult,
    summary="Execute end-to-end training pipeline, calibration, and caching (Phase 137)",
)
def train_and_select_pipeline(
    random_seed: int = Query(42, description="Deterministic random seed"),
    current_user: User = Depends(require_permission("discounts:read")),
    db: Session = Depends(get_db),
) -> ModelTrainingPipelineResult:
    """Execute full training pipeline: train candidates, select champion, calibrate, and cache."""
    return ModelTrainingPipelineService.train_pipeline(
        db=db,
        company_id=current_user.company_id,
        random_seed=random_seed,
    )


# ==============================================================================
# Phase 138: Model Evaluation Endpoint
# ==============================================================================

@router.post(
    "/models/evaluate",
    response_model=ModelEvaluationMetrics,
    summary="Evaluate held-out test split metrics for active champion model (Phase 138)",
)
def evaluate_champion_model(
    random_seed: int = Query(42, description="Deterministic random seed"),
    current_user: User = Depends(require_permission("discounts:read")),
    db: Session = Depends(get_db),
) -> ModelEvaluationMetrics:
    """Evaluate held-out test split performance of the champion model."""
    pipeline = ModelTrainingPipelineService.train_pipeline(
        db=db,
        company_id=current_user.company_id,
        random_seed=random_seed,
    )
    return pipeline.final_test_evaluation


# ==============================================================================
# Phase 139: Probability Calibration Endpoint
# ==============================================================================

@router.post(
    "/models/calibrate",
    response_model=CalibrationMetadata,
    summary="Fit Platt scaling calibration on validation data (Phase 139)",
)
def calibrate_model_probabilities(
    random_seed: int = Query(42, description="Deterministic random seed"),
    current_user: User = Depends(require_permission("discounts:read")),
    db: Session = Depends(get_db),
) -> CalibrationMetadata:
    """Fit probability calibration on validation split and return calibration metadata."""
    pipeline = ModelTrainingPipelineService.train_pipeline(
        db=db,
        company_id=current_user.company_id,
        random_seed=random_seed,
    )
    return pipeline.calibration


# ==============================================================================
# Phases 140–144: Risk Prediction & Explainability Endpoint
# ==============================================================================

@router.post(
    "/risk/predict",
    response_model=RiskPredictionResponse,
    summary="Execute deal risk inference with score, classification, and SHAP explainability (Phases 140–144)",
)
def predict_deal_risk(
    request: RiskPredictionRequest,
    current_user: User = Depends(require_permission("discounts:read")),
    db: Session = Depends(get_db),
) -> RiskPredictionResponse:
    """Perform real-time deal risk inference using cached champion model without retraining."""
    return RiskPredictionInferenceService.predict(
        db=db,
        company_id=current_user.company_id,
        request=request,
    )


# ==============================================================================
# Phase 145: AI Risk Dashboard Endpoint
# ==============================================================================

@router.get(
    "/risk/dashboard",
    response_model=AIRiskDashboardSummary,
    summary="Get aggregated AI Risk Dashboard overview, distributions, and model performance (Phase 145)",
)
def get_ai_risk_dashboard(
    current_user: User = Depends(require_permission("discounts:read")),
    db: Session = Depends(get_db),
) -> AIRiskDashboardSummary:
    """Aggregate tenant risk metrics, score distribution, and model status for the dashboard."""
    return AIRiskDashboardService.get_dashboard_summary(
        db=db,
        company_id=current_user.company_id,
    )




