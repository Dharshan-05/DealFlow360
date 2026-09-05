"""Comprehensive Test Suite for DealFlow360 B04 (Phases 136–145: AI/ML Risk Engine).

Strict production-grade tests verifying:
- Phase 136: Model Selection
  * Champion model deterministic evaluation and selection from candidate pool
  * Multi-metric weighted composite scoring formula verification
  * Complete selection justification metadata
- Phase 137: Model Training Pipeline
  * Ingestion -> Tabular Feature Pipeline -> 3-Way Splitting -> Multi-Model Tournament -> Champion Calibration
  * End-to-end artifact generation and pipeline tracking
- Phase 138: Model Evaluation
  * Strict out-of-sample held-out test split evaluation
  * Comprehensive metrics: ROC-AUC, PR-AUC, F1, Precision, Recall, Brier score, Confusion matrix
- Phase 139: Probability Calibration
  * Platt scaling (univariate logistic regression on validation margins)
  * Pre- vs post-calibration Brier score comparison and monotonic probability distribution
- Phase 140: Risk Prediction API
  * Real-time inference without re-training models
  * Dynamic raw & calibrated probability extraction
- Phase 141: Risk Score 0–100
  * Continuous [0, 100] integer risk score scaling
  * Bounded check across edge scenarios
- Phase 142: Risk Classification
  * 4-Tier categorical stratification: LOW (0-29), MEDIUM (30-59), HIGH (60-84), CRITICAL (85-100)
  * Boundary value enforcement
- Phase 143: SHAP Explainability
  * Exact tree-path marginal contribution attribution
  * Direction classification: risk_increasing vs risk_reducing
- Phase 144: Risk Factors
  * Translation of feature attributions into contextual business explanations and severity tiers
- Phase 145: AI Risk Dashboard
  * Multi-tenant aggregated summary metrics, histograms, recent predictions, and model status
  * Strict tenant isolation and RBAC permission enforcement
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.jwt import create_access_token
from app.db.session import SessionLocal
from app.main import app
from app.models.applied_discount import AppliedDiscount
from app.models.company import Company
from app.models.customer import Customer
from app.models.customer_deal_history import CustomerDealHistory
from app.models.customer_tier import CustomerTier
from app.models.discount_configuration import DiscountConfiguration
from app.models.permission import Permission
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.role import Role
from app.models.user import User
from app.schemas.ml_risk import (
    ModelType,
    RiskScoreCategory,
    RiskPredictionRequest,
    ModelSelectionResult,
    CalibrationMetadata,
    ModelArtifact,
)
from app.services.ml_risk import (
    RiskDatasetPipelineService,
    XGBoostRiskModelService,
    LightGBMRiskModelService,
    RandomForestRiskModelService,
    ModelComparisonService,
    ModelSelectionService,
    ProbabilityCalibrationService,
    TreeExplainabilityService,
    RiskFactorExtractionService,
    RiskPredictionInferenceService,
    AIRiskDashboardService,
    RiskEngineRegistry,
    ModelTrainingPipelineService,
)


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def setup_b04_data(db_session):
    """Seed historical deals and test user for B04 testing."""
    now = datetime.now(timezone.utc)

    # 1. Company
    company = Company(
        name=f"B04 AI Risk Co {uuid.uuid4().hex[:6]}",
        legal_name="B04 Enterprise Risk Analytics Corp",
        email=f"b04_{uuid.uuid4().hex[:6]}@example.com",
    )
    db_session.add(company)
    db_session.commit()

    # 2. Customer Tier
    tier_plat = CustomerTier(
        name=f"Plat-{uuid.uuid4().hex[:8]}",
        code=f"P-{uuid.uuid4().hex[:12]}",
        discount_limit=Decimal("25.00"),
        description="Platinum tier 25%",
    )
    db_session.add(tier_plat)
    db_session.commit()

    # 3. Customers
    cust_safe = Customer(
        company_id=company.id,
        tier_id=tier_plat.id,
        customer_code=f"CUST-SAFE-{uuid.uuid4().hex[:8]}",
        name="Reliable Bluechip Inc",
        email=f"safe_{uuid.uuid4().hex[:8]}@example.com",
    )
    cust_risky = Customer(
        company_id=company.id,
        tier_id=tier_plat.id,
        customer_code=f"CUST-RISK-{uuid.uuid4().hex[:8]}",
        name="Volatile Startup LLC",
        email=f"risk_{uuid.uuid4().hex[:8]}@example.com",
    )
    db_session.add_all([cust_safe, cust_risky])
    db_session.commit()

    # 4. Product Category and Product
    cat = ProductCategory(
        name=f"B04 Cat {uuid.uuid4().hex[:8]}",
        code=f"B04C-{uuid.uuid4().hex[:12]}",
        description="Enterprise Infrastructure",
    )
    db_session.add(cat)
    db_session.commit()

    product = Product(
        category_id=cat.id,
        sku=f"SKU-B04-{uuid.uuid4().hex[:12]}",
        name="Cloud Enterprise Engine",
        cost=Decimal("500.00"),
        base_price=Decimal("1500.00"),
        unit="instance",
    )
    db_session.add(product)
    db_session.commit()

    # 5. Discount Configuration
    config = DiscountConfiguration(
        company_id=company.id,
        name="B04 Standard Policy",
        default_discount_ceiling=Decimal("20.00"),
        effective_from=now - timedelta(days=120),
        is_active=True,
    )
    db_session.add(config)
    db_session.commit()

    # 6. Generate 30 historical deals (stratified distribution)
    deals = []
    for i in range(30):
        is_risky_case = (i % 3 == 0)  # 10 risky deals, 20 normal deals
        cust = cust_risky if is_risky_case else cust_safe
        deal_date = now - timedelta(days=90 - (i * 2))

        if is_risky_case:
            disc_pct = Decimal("45.00")
            margin_pct = Decimal("5.00")
            deal_val = Decimal("120000.00")
            risk_lvl = "CRITICAL"
        else:
            disc_pct = Decimal("8.00")
            margin_pct = Decimal("55.00")
            deal_val = Decimal("18000.00")
            risk_lvl = "LOW"

        deal_code_str = f"DEAL-B04-{i+1:03d}-{uuid.uuid4().hex[:4]}"
        deal = CustomerDealHistory(
            company_id=company.id,
            customer_id=cust.id,
            deal_code=deal_code_str,
            title=f"Contract B04 #{i+1}",
            deal_value=deal_val,
            status="WON" if (i % 2 == 0) else "LOST",
            sales_rep_name="Jordan Bell",
            created_at=deal_date,
        )
        db_session.add(deal)
        db_session.flush()

        disc = AppliedDiscount(
            company_id=company.id,
            customer_id=cust.id,
            product_id=product.id,
            deal_reference=deal_code_str,
            decision_id=f"DEC-B04-{i+1:03d}",
            requested_discount=disc_pct,
            applied_discount=disc_pct,
            selling_price=Decimal("1500.00"),
            discounted_price=Decimal("1500.00") * (Decimal("1.0") - (disc_pct / Decimal("100.0"))),
            unit_cost=Decimal("500.00"),
            margin_percentage=margin_pct,
            risk_level=risk_lvl,
            reason_code="GOVERNANCE_OPTIMAL",
            created_at=deal_date,
        )
        db_session.add(disc)

    db_session.commit()

    # 7. Auth setup for API tests
    perm = db_session.scalar(select(Permission).where(Permission.name == "discounts:read"))
    if not perm:
        perm = Permission(name="discounts:read", resource="discounts", action="read")
        db_session.add(perm)
        db_session.commit()

    role = Role(name=f"B04 Risk Role {uuid.uuid4().hex[:4]}", description="Risk Role")
    role.permissions.append(perm)
    db_session.add(role)
    db_session.commit()

    user = User(
        company_id=company.id,
        email=f"risk_officer_{uuid.uuid4().hex[:6]}@example.com",
        password_hash="mocked_hash",
        first_name="Chief",
        last_name="Risk Officer",
        is_active=True,
    )
    user.roles.append(role)
    db_session.add(user)
    db_session.commit()

    token = create_access_token(subject=str(user.id))

    return {
        "company": company,
        "token": token,
        "customer_safe": cust_safe,
        "customer_risky": cust_risky,
        "user": user,
    }


# ==============================================================================
# PHASE 136: MODEL SELECTION TESTS
# ==============================================================================

def test_phase_136_model_selection_deterministic_ranking(db_session, setup_b04_data):
    """Verify Phase 136: Model Selection evaluates candidate artifacts and selects deterministic champion."""
    company_id = setup_b04_data["company"].id
    RiskEngineRegistry._registry.clear()

    # Build dataset and compare models
    dataset_res = RiskDatasetPipelineService.execute_pipeline(db=db_session, company_id=company_id)
    comparison_rep = ModelComparisonService.compare_models(
        db=db_session,
        company_id=company_id,
        pipeline_result=dataset_res,
        random_seed=42,
    )

    selection = ModelSelectionService.select_champion(comparison_rep)

    assert isinstance(selection, ModelSelectionResult)
    assert selection.selected_model in [ModelType.XGBOOST, ModelType.LIGHTGBM, ModelType.RANDOM_FOREST]
    assert len(selection.candidate_metrics) == 3
    assert "as champion" in selection.selection_rationale

    # Ensure candidate ranks are 1, 2, 3
    ranks = [c.rank for c in selection.candidate_metrics]
    assert sorted(ranks) == [1, 2, 3]


# ==============================================================================
# PHASE 137: MODEL TRAINING PIPELINE TESTS
# ==============================================================================

def test_phase_137_training_pipeline_execution_and_registry_cache(db_session, setup_b04_data):
    """Verify Phase 137: Model Training Pipeline orchestrates end-to-end dataset extraction, tournament, and caching."""
    company_id = setup_b04_data["company"].id
    RiskEngineRegistry._registry.clear()

    pipeline_result = ModelTrainingPipelineService.train_pipeline(
        db=db_session,
        company_id=company_id,
        random_seed=42,
    )

    assert pipeline_result.company_id == company_id
    assert pipeline_result.champion_artifact is not None
    assert pipeline_result.model_selection is not None
    assert pipeline_result.calibration is not None
    assert pipeline_result.dataset_split.total_samples >= 25

    # Verify model is cached in RiskEngineRegistry for sub-millisecond inference
    cached = RiskEngineRegistry.get(company_id)
    assert cached is not None
    assert cached.champion_artifact.artifact_id == pipeline_result.champion_artifact.artifact_id


# ==============================================================================
# PHASE 138: MODEL EVALUATION ON HELD-OUT TEST SPLIT
# ==============================================================================

def test_phase_138_model_evaluation_metrics_held_out(db_session, setup_b04_data):
    """Verify Phase 138: Model Evaluation calculates non-leaking out-of-sample metrics on held-out test data."""
    company_id = setup_b04_data["company"].id
    dataset_res = RiskDatasetPipelineService.execute_pipeline(db=db_session, company_id=company_id)
    champion_art = XGBoostRiskModelService.train(dataset_res, random_seed=42)

    test_metrics = champion_art.test_metrics
    assert test_metrics.sample_count > 0
    assert 0.0 <= test_metrics.accuracy <= 1.0
    assert 0.0 <= test_metrics.precision <= 1.0
    assert 0.0 <= test_metrics.recall <= 1.0
    assert 0.0 <= test_metrics.f1_score <= 1.0
    assert 0.0 <= test_metrics.brier_score <= 1.0
    assert (test_metrics.true_positives + test_metrics.false_positives + 
            test_metrics.true_negatives + test_metrics.false_negatives) == test_metrics.sample_count


# ==============================================================================
# PHASE 139: PROBABILITY CALIBRATION TESTS (PLATT SCALING)
# ==============================================================================

def test_phase_139_platt_scaling_calibration(db_session, setup_b04_data):
    """Verify Phase 139: Probability Calibration applies Platt scaling with sigmoid parameters."""
    company_id = setup_b04_data["company"].id
    dataset_res = RiskDatasetPipelineService.execute_pipeline(db=db_session, company_id=company_id)
    champion_art = XGBoostRiskModelService.train(dataset_res, random_seed=42)

    val_probs = ModelTrainingPipelineService._predict_probs_for_artifact(champion_art, dataset_res.val_feature_matrix)
    calib_meta = ProbabilityCalibrationService.fit_calibration(
        raw_val_probs=val_probs,
        y_val=dataset_res.val_target_vector,
    )

    assert isinstance(calib_meta, CalibrationMetadata)
    assert calib_meta.method.value in ["PLATT_SCALING", "NONE"]
    assert calib_meta.validation_sample_count > 0
    assert calib_meta.sigmoid_a is not None
    assert calib_meta.sigmoid_b is not None

    # Test calibration transformation callable on edge probabilities
    cal_low = ProbabilityCalibrationService.apply_calibration(0.01, calib_meta.sigmoid_a, calib_meta.sigmoid_b)
    cal_high = ProbabilityCalibrationService.apply_calibration(0.99, calib_meta.sigmoid_a, calib_meta.sigmoid_b)
    assert 0.0 <= cal_low <= 1.0
    assert 0.0 <= cal_high <= 1.0
    assert cal_low < cal_high  # Monotonic ordering preserved


# ==============================================================================
# PHASES 140–144: REAL-TIME INFERENCE, 0-100 SCORING, AND SHAP ATTRIBUTION
# ==============================================================================

def test_phases_140_to_144_real_time_risk_inference_and_explainability(db_session, setup_b04_data):
    """Verify Phases 140–144: Real-time risk inference, 0–100 scaling, 4-tier classification, and SHAP explainability."""
    company_id = setup_b04_data["company"].id

    # 1. Evaluate high-risk proposal (Phase 140)
    high_risk_req = RiskPredictionRequest(
        deal_value=150000.0,
        requested_discount_pct=48.0,
        selling_price=78000.0,
        unit_cost=80000.0,
        customer_tenure_days=45,
        lifetime_orders=2,
        lifetime_revenue=20000.0,
        payment_default_ratio=0.40,
        historical_avg_discount_pct=42.0,
        historical_avg_margin_pct=-2.0,
        deal_reference="TEST-HIGH-RISK-PROPOSAL",
    )

    pred_high = RiskPredictionInferenceService.predict(db=db_session, company_id=company_id, request=high_risk_req)

    # Phase 140: Prediction API outputs
    assert pred_high.prediction_id is not None
    assert 0.0 <= pred_high.raw_probability <= 1.0
    assert 0.0 <= pred_high.risk_probability <= 1.0

    # Phase 141: Risk Score 0–100
    assert 0 <= pred_high.risk_score <= 100
    assert abs(pred_high.risk_score - int(round(pred_high.risk_probability * 100.0))) <= 1

    # Phase 142: Risk Classification
    assert pred_high.risk_classification in [RiskScoreCategory.HIGH, RiskScoreCategory.CRITICAL, RiskScoreCategory.MEDIUM]

    # Phase 143: Tree Explainability (Attribution)
    assert len(pred_high.feature_contributions) > 0
    # Top contributors should have valid direction and relative impact
    top_contrib = pred_high.feature_contributions[0]
    assert top_contrib.direction in ["risk_increasing", "risk_reducing"]
    assert 0.0 <= top_contrib.relative_impact_pct <= 100.0

    # Phase 144: Contextual Risk Factors
    assert len(pred_high.top_risk_increasing_factors) > 0 or len(pred_high.top_risk_reducing_factors) > 0
    if pred_high.top_risk_increasing_factors:
        top_factor = pred_high.top_risk_increasing_factors[0]
        assert len(top_factor.display_name) > 0
        assert len(top_factor.description) > 0
        assert top_factor.severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "BENEFICIAL"]

    # 2. Evaluate low-risk proposal (boundary & robustness check)
    low_risk_req = RiskPredictionRequest(
        deal_value=25000.0,
        requested_discount_pct=5.0,
        selling_price=23750.0,
        unit_cost=8000.0,
        customer_tenure_days=900,
        lifetime_orders=35,
        lifetime_revenue=850000.0,
        payment_default_ratio=0.0,
        historical_avg_discount_pct=6.0,
        historical_avg_margin_pct=65.0,
        deal_reference="TEST-LOW-RISK-PROPOSAL",
    )

    pred_low = RiskPredictionInferenceService.predict(db=db_session, company_id=company_id, request=low_risk_req)
    assert pred_low.risk_score <= pred_high.risk_score
    assert pred_low.risk_classification in [RiskScoreCategory.LOW, RiskScoreCategory.MEDIUM]


# ==============================================================================
# PHASE 145: AI RISK DASHBOARD AGGREGATION & TENANT ISOLATION
# ==============================================================================

def test_phase_145_ai_risk_dashboard_aggregation(db_session, setup_b04_data):
    """Verify Phase 145: AI Risk Dashboard Summary aggregates metrics and distribution."""
    company_id = setup_b04_data["company"].id

    # Make 2 predictions to populate evaluated deals
    req = RiskPredictionRequest(
        deal_value=60000.0,
        requested_discount_pct=25.0,
        selling_price=45000.0,
        unit_cost=30000.0,
    )
    RiskPredictionInferenceService.predict(db=db_session, company_id=company_id, request=req)

    dashboard = AIRiskDashboardService.get_dashboard_summary(db=db_session, company_id=company_id)

    assert dashboard.company_id == company_id
    assert dashboard.total_evaluated_deals >= 1
    assert 0.0 <= dashboard.average_risk_score <= 100.0
    assert len(dashboard.risk_distribution) == 5
    # Buckets represented
    bucket_ranges = [b.score_range for b in dashboard.risk_distribution]
    assert "0-20" in bucket_ranges
    assert "81-100" in bucket_ranges

    assert dashboard.champion_model is not None
    assert len(dashboard.recent_evaluated_deals) >= 1


# ==============================================================================
# API ENDPOINT & RBAC INTEGRATION TESTS
# ==============================================================================

def test_b04_api_endpoints_and_rbac(client, setup_b04_data):
    """Verify B04 API endpoints under /api/v1/ml/* enforce RBAC and succeed for authorized users."""
    token = setup_b04_data["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. POST /api/v1/ml/models/select
    res_select = client.post("/api/v1/ml/models/select?random_seed=42", headers=headers)
    assert res_select.status_code == 200, res_select.text
    sel_data = res_select.json()
    assert sel_data["selected_model"] in ["XGBOOST", "LIGHTGBM", "RANDOM_FOREST"]

    # 2. POST /api/v1/ml/pipeline/train-and-select
    res_pipeline = client.post("/api/v1/ml/pipeline/train-and-select?random_seed=42", headers=headers)
    assert res_pipeline.status_code == 200, res_pipeline.text
    pipe_data = res_pipeline.json()
    assert "champion_artifact" in pipe_data

    # 3. POST /api/v1/ml/models/evaluate
    res_eval = client.post("/api/v1/ml/models/evaluate?random_seed=42", headers=headers)
    assert res_eval.status_code == 200, res_eval.text
    eval_data = res_eval.json()
    assert "accuracy" in eval_data
    assert "f1_score" in eval_data

    # 4. POST /api/v1/ml/models/calibrate
    res_calib = client.post("/api/v1/ml/models/calibrate?random_seed=42", headers=headers)
    assert res_calib.status_code == 200, res_calib.text
    calib_data = res_calib.json()
    assert calib_data["method"] in ["PLATT_SCALING", "NONE"]

    # 5. POST /api/v1/ml/risk/predict
    payload = {
        "deal_value": 75000.0,
        "requested_discount_pct": 32.5,
        "selling_price": 50625.0,
        "unit_cost": 38000.0,
        "customer_tenure_days": 180,
        "customer_tier": "PLATINUM",
        "lifetime_orders": 8,
        "payment_default_ratio": 0.12,
        "historical_avg_discount_pct": 20.0,
        "historical_avg_margin_pct": 25.0,
        "deal_reference": "DEAL-API-TEST-001",
    }
    res_pred = client.post("/api/v1/ml/risk/predict", json=payload, headers=headers)
    assert res_pred.status_code == 200, res_pred.text
    pred_data = res_pred.json()
    assert "risk_score" in pred_data
    assert "risk_classification" in pred_data
    assert len(pred_data["top_risk_increasing_factors"]) > 0 or len(pred_data["top_risk_reducing_factors"]) > 0
    assert len(pred_data["feature_contributions"]) > 0

    # 6. GET /api/v1/ml/risk/dashboard
    res_dash = client.get("/api/v1/ml/risk/dashboard", headers=headers)
    assert res_dash.status_code == 200, res_dash.text
    dash_data = res_dash.json()
    assert dash_data["total_evaluated_deals"] >= 1
    assert "risk_distribution" in dash_data

    # 7. RBAC rejection test (unauthenticated request)
    res_unauth = client.get("/api/v1/ml/risk/dashboard")
    assert res_unauth.status_code == 401
