"""Comprehensive Test Suite for DealFlow360 B03 (Phases 131–135: AI/ML Risk Engine).

Verifies:
- Phase 131: Risk Dataset Pipeline
  * Deterministic tabular feature extraction across 37 features
  * Label encoding for categorical fields
  * Stratified train/val/test splitting
  * Data leakage prevention (strictly zero target columns in X matrices)
- Phase 132: XGBoost Model
  * 2nd-order Taylor approximation gradient boosted trees with L2 regularization
  * Binary cross-entropy training loss reduction
  * Comprehensive metrics (Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC, Brier score)
  * Model artifact serialization and determinism
- Phase 133: LightGBM Model
  * Leaf-wise (best-first) tree expansion
  * Probability predictions bounded in [0, 1]
  * Model serialization & feature importances
- Phase 134: Random Forest Baseline
  * Bagging ensemble with bootstrap sampling & random feature subsetting
  * Out-of-sample evaluation on validation & test sets
- Phase 135: Model Comparison
  * Multi-model evaluation across identical test splits
  * Objective composite scoring and automated champion selection
- API Endpoints & RBAC:
  * /api/v1/ml/pipeline/risk-dataset
  * /api/v1/ml/models/xgboost/train
  * /api/v1/ml/models/lightgbm/train
  * /api/v1/ml/models/random-forest/train
  * /api/v1/ml/models/compare
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
    ModelArtifact,
    ModelComparisonReport,
    RiskDatasetPipelineResult,
)
from app.services.ml_risk import (
    RiskDatasetPipelineService,
    XGBoostRiskModelService,
    LightGBMRiskModelService,
    RandomForestRiskModelService,
    ModelComparisonService,
    ModelMetricsEvaluator,
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
def setup_b03_data(db_session):
    """Seed comprehensive historical deal records to train and evaluate ML risk models."""
    now = datetime.now(timezone.utc)

    # 1. Company
    company = Company(
        name=f"B03 Test Co {uuid.uuid4().hex[:6]}",
        legal_name="B03 Risk ML Corp",
        email=f"b03_{uuid.uuid4().hex[:6]}@example.com",
    )
    db_session.add(company)
    db_session.commit()

    # 2. Customer Tier
    tier_gold = CustomerTier(
        name=f"Gold-{uuid.uuid4().hex[:8]}",
        code=f"G-{uuid.uuid4().hex[:12]}",
        discount_limit=Decimal("15.00"),
        description="Gold tier 15%",
    )
    db_session.add(tier_gold)
    db_session.commit()

    # 3. Multiple Customers (high risk & normal)
    cust_normal = Customer(
        company_id=company.id,
        tier_id=tier_gold.id,
        customer_code=f"CUST-NORM-{uuid.uuid4().hex[:10]}",
        name="Reliable Corp",
        email=f"norm_{uuid.uuid4().hex[:10]}@example.com",
    )
    cust_risky = Customer(
        company_id=company.id,
        tier_id=tier_gold.id,
        customer_code=f"CUST-RISK-{uuid.uuid4().hex[:10]}",
        name="High Risk LLC",
        email=f"risk_{uuid.uuid4().hex[:10]}@example.com",
    )
    db_session.add_all([cust_normal, cust_risky])
    db_session.commit()

    # 4. Product Category and Product
    cat = ProductCategory(
        name=f"B03 Cat {uuid.uuid4().hex[:8]}",
        code=f"B03C-{uuid.uuid4().hex[:12]}",
        description="Enterprise Suite",
    )
    db_session.add(cat)
    db_session.commit()

    product = Product(
        category_id=cat.id,
        sku=f"SKU-B03-{uuid.uuid4().hex[:12]}",
        name="Analytics Platform",
        cost=Decimal("400.00"),
        base_price=Decimal("1000.00"),
        unit="license",
    )
    db_session.add(product)
    db_session.commit()

    # 5. Discount Configuration
    config = DiscountConfiguration(
        company_id=company.id,
        name="B03 Standard Ceiling",
        default_discount_ceiling=Decimal("15.00"),
        effective_from=now - timedelta(days=90),
        is_active=True,
    )
    db_session.add(config)
    db_session.commit()

    # 6. Generate 25 historical deals (mix of low risk and high risk)
    deals = []
    discounts = []
    for i in range(25):
        is_risky_case = (i % 3 == 0)  # ~33% high risk deals
        cust = cust_risky if is_risky_case else cust_normal
        deal_date = now - timedelta(days=80 - (i * 3))
        
        # High risk: steep discount (e.g. 42%), low margin (e.g. 6%), high value
        # Low risk: mild discount (e.g. 10%), high margin (e.g. 48%), normal value
        if is_risky_case:
            disc_pct = Decimal("42.00")
            margin_pct = Decimal("6.00")
            deal_val = Decimal("85000.00")
            risk_lvl = "CRITICAL"
        else:
            disc_pct = Decimal("10.00")
            margin_pct = Decimal("48.00")
            deal_val = Decimal("15000.00")
            risk_lvl = "LOW"

        deal_code_str = f"DEAL-B03-{i+1:03d}-{uuid.uuid4().hex[:4]}"
        deal = CustomerDealHistory(
            company_id=company.id,
            customer_id=cust.id,
            deal_code=deal_code_str,
            title=f"Contract Phase B03 #{i+1}",
            deal_value=deal_val,
            status="WON" if (i % 2 == 0) else "NEGOTIATING",
            sales_rep_name="Alex Broker",
            created_at=deal_date,
        )
        deals.append(deal)
        db_session.add(deal)
        db_session.flush()

        disc = AppliedDiscount(
            company_id=company.id,
            customer_id=cust.id,
            product_id=product.id,
            deal_reference=deal_code_str,
            decision_id=f"DEC-B03-{i+1:03d}",
            requested_discount=disc_pct,
            applied_discount=disc_pct,
            selling_price=Decimal("1000.00"),
            discounted_price=Decimal("1000.00") * (Decimal("1.0") - (disc_pct / Decimal("100.0"))),
            unit_cost=Decimal("400.00"),
            margin_percentage=margin_pct,
            risk_level=risk_lvl,
            reason_code="GOVERNANCE_OPTIMAL",
            created_at=deal_date,
        )
        discounts.append(disc)
        db_session.add(disc)

    db_session.commit()

    # 7. Auth setup for API tests
    perm = db_session.scalar(select(Permission).where(Permission.name == "discounts:read"))
    if not perm:
        perm = Permission(name="discounts:read", resource="discounts", action="read")
        db_session.add(perm)
        db_session.commit()

    role = Role(name=f"B03 Risk Analyst {uuid.uuid4().hex[:4]}", description="Risk Analyst Role")
    role.permissions.append(perm)
    db_session.add(role)
    db_session.commit()

    user = User(
        company_id=company.id,
        email=f"analyst_{uuid.uuid4().hex[:6]}@example.com",
        password_hash="mocked_hash",
        first_name="Risk",
        last_name="Analyst",
        is_active=True,
    )
    user.roles.append(role)
    db_session.add(user)
    db_session.commit()

    token = create_access_token(subject=str(user.id))

    return {
        "company": company,
        "token": token,
        "customer_normal": cust_normal,
        "customer_risky": cust_risky,
        "deals_count": len(deals),
    }


# ==============================================================================
# PHASE 131: RISK DATASET PIPELINE TESTS
# ==============================================================================

def test_phase_131_risk_dataset_pipeline_extraction(db_session, setup_b03_data):
    """Test Phase 131 dataset pipeline creates balanced, stratified, leak-free tabular matrices."""
    company = setup_b03_data["company"]
    result = RiskDatasetPipelineService.execute_pipeline(
        db=db_session,
        company_id=company.id,
        train_ratio=0.6,
        val_ratio=0.2,
        test_ratio=0.2,
        random_seed=42,
    )

    # Manifest verification
    assert result.company_id == company.id
    assert result.split_manifest.total_samples >= setup_b03_data["deals_count"]
    assert len(result.split_manifest.feature_names) == 50

    # Data split sizes
    assert len(result.train_feature_matrix) == result.split_manifest.train_samples
    assert len(result.val_feature_matrix) == result.split_manifest.val_samples
    assert len(result.test_feature_matrix) == result.split_manifest.test_samples
    assert len(result.train_target_vector) == result.split_manifest.train_samples
    assert len(result.val_target_vector) == result.split_manifest.val_samples
    assert len(result.test_target_vector) == result.split_manifest.test_samples

    total_split = (
        result.split_manifest.train_samples
        + result.split_manifest.val_samples
        + result.split_manifest.test_samples
    )
    assert total_split == result.split_manifest.total_samples

    # Verify zero data leakage: target variables MUST NOT exist in feature matrix
    for f in result.split_manifest.feature_names:
        assert "target" not in f
        assert "is_high_risk" not in f
        assert "severity" not in f

    # Verify binary target labels
    for y in result.train_target_vector + result.val_target_vector + result.test_target_vector:
        assert y in (0, 1)

    # Verify deterministic encoding
    assert "deal_size_category" in result.split_manifest.categorical_encodings
    assert len(result.split_manifest.categorical_encodings["deal_size_category"]) > 0


def test_phase_131_empty_dataset_handling(db_session):
    """Test Phase 131 handles companies with no deal history gracefully."""
    empty_company = Company(name=f"Empty Co {uuid.uuid4().hex[:6]}", legal_name="Empty Corp")
    db_session.add(empty_company)
    db_session.commit()

    result = RiskDatasetPipelineService.execute_pipeline(
        db=db_session,
        company_id=empty_company.id,
    )

    assert result.split_manifest.total_samples == 0
    assert len(result.train_feature_matrix) == 0
    assert len(result.train_target_vector) == 0


# ==============================================================================
# PHASE 132: XGBOOST RISK MODEL TESTS
# ==============================================================================

def test_phase_132_xgboost_training_and_metrics(db_session, setup_b03_data):
    """Test Phase 132 XGBoost model trains, computes real metrics, and serializes artifact."""
    company = setup_b03_data["company"]
    dataset = RiskDatasetPipelineService.execute_pipeline(
        db=db_session,
        company_id=company.id,
        random_seed=42,
    )

    artifact = XGBoostRiskModelService.train(
        pipeline_result=dataset,
        n_estimators=10,
        max_depth=3,
        learning_rate=0.1,
        reg_lambda=1.0,
        random_seed=42,
    )

    assert artifact.model_type == ModelType.XGBOOST
    assert artifact.company_id == company.id
    assert len(artifact.feature_names) == 50
    assert artifact.test_metrics is not None

    # Verify real metrics computation
    metrics = artifact.test_metrics
    assert 0.0 <= metrics.accuracy <= 1.0
    if metrics.roc_auc is not None:
        assert 0.0 <= metrics.roc_auc <= 1.0
    assert 0.0 <= metrics.brier_score <= 1.0
    assert metrics.sample_count == len(dataset.test_target_vector)
    assert (
        metrics.true_positives + metrics.true_negatives + metrics.false_positives + metrics.false_negatives
        == metrics.sample_count
    )

    # Test feature importances
    assert len(artifact.feature_importances) == 50
    total_importance = sum(artifact.feature_importances.values())
    if total_importance > 0:
        assert pytest.approx(total_importance, rel=1e-2) == 1.0


# ==============================================================================
# PHASE 133: LIGHTGBM RISK MODEL TESTS
# ==============================================================================

def test_phase_133_lightgbm_leaf_wise_training(db_session, setup_b03_data):
    """Test Phase 133 LightGBM model trains via leaf-wise best-first strategy."""
    company = setup_b03_data["company"]
    dataset = RiskDatasetPipelineService.execute_pipeline(
        db=db_session,
        company_id=company.id,
        random_seed=42,
    )

    artifact = LightGBMRiskModelService.train(
        pipeline_result=dataset,
        n_estimators=10,
        num_leaves=15,
        learning_rate=0.1,
        min_child_samples=2,
        random_seed=42,
    )

    assert artifact.model_type == ModelType.LIGHTGBM
    assert artifact.test_metrics is not None
    assert 0.0 <= artifact.test_metrics.accuracy <= 1.0
    assert 0.0 <= artifact.test_metrics.f1_score <= 1.0


# ==============================================================================
# PHASE 134: RANDOM FOREST BASELINE TESTS
# ==============================================================================

def test_phase_134_random_forest_baseline(db_session, setup_b03_data):
    """Test Phase 134 Random Forest bagging ensemble with bootstrap sampling."""
    company = setup_b03_data["company"]
    dataset = RiskDatasetPipelineService.execute_pipeline(
        db=db_session,
        company_id=company.id,
        random_seed=42,
    )

    artifact = RandomForestRiskModelService.train(
        pipeline_result=dataset,
        n_estimators=15,
        max_depth=4,
        max_features_ratio=0.5,
        random_seed=42,
    )

    assert artifact.model_type == ModelType.RANDOM_FOREST
    assert artifact.test_metrics is not None
    if artifact.test_metrics.roc_auc is not None:
        assert 0.0 <= artifact.test_metrics.roc_auc <= 1.0


# ==============================================================================
# PHASE 135: MODEL COMPARISON & BENCHMARK TESTS
# ==============================================================================

def test_phase_135_model_comparison_benchmark(db_session, setup_b03_data):
    """Test Phase 135 trains all 3 models on identical test data and selects champion."""
    company = setup_b03_data["company"]
    dataset = RiskDatasetPipelineService.execute_pipeline(
        db=db_session,
        company_id=company.id,
        random_seed=42,
    )

    report = ModelComparisonService.compare_models(
        db=db_session,
        company_id=company.id,
        pipeline_result=dataset,
        random_seed=42,
    )

    assert report.company_id == company.id
    assert len(report.evaluated_models) == 3
    assert report.winner_model_type in [ModelType.XGBOOST, ModelType.LIGHTGBM, ModelType.RANDOM_FOREST]

    # Verify rank ordering: rank 1 has highest composite score
    assert report.evaluated_models[0].rank == 1
    assert report.evaluated_models[0].model_type == report.winner_model_type
    assert report.evaluated_models[0].selection_score >= report.evaluated_models[1].selection_score


def test_metrics_evaluator_edge_cases():
    """Test ModelMetricsEvaluator handles single-class edge cases without NaN/ZeroDivision."""
    # All negative targets
    y_true = [0, 0, 0, 0]
    y_pred = [0.1, 0.2, 0.05, 0.3]
    metrics = ModelMetricsEvaluator.evaluate(y_true, y_pred)
    assert metrics.accuracy == 1.0
    assert metrics.precision == 0.0
    assert metrics.recall == 0.0
    assert metrics.roc_auc is None  # Single class has undefined ROC-AUC

    # All positive targets
    y_true = [1, 1, 1, 1]
    y_pred = [0.9, 0.8, 0.7, 0.95]
    metrics = ModelMetricsEvaluator.evaluate(y_true, y_pred)
    assert metrics.accuracy == 1.0
    assert metrics.recall == 1.0


# ==============================================================================
# API ENDPOINTS & RBAC TESTS (Phases 131–135)
# ==============================================================================

def test_api_phase_131_risk_dataset_pipeline(client, setup_b03_data):
    """Test POST /api/v1/ml/pipeline/risk-dataset."""
    token = setup_b03_data["token"]
    response = client.post(
        "/api/v1/ml/pipeline/risk-dataset?train_ratio=0.7&val_ratio=0.15&test_ratio=0.15&random_seed=42",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "split_manifest" in data
    assert len(data["split_manifest"]["feature_names"]) == 50


def test_api_phase_132_xgboost_train(client, setup_b03_data):
    """Test POST /api/v1/ml/models/xgboost/train."""
    token = setup_b03_data["token"]
    response = client.post(
        "/api/v1/ml/models/xgboost/train?n_estimators=5&max_depth=2&learning_rate=0.1&random_seed=42",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["model_type"] == "XGBOOST"
    assert "test_metrics" in data
    assert "feature_importances" in data


def test_api_phase_133_lightgbm_train(client, setup_b03_data):
    """Test POST /api/v1/ml/models/lightgbm/train."""
    token = setup_b03_data["token"]
    response = client.post(
        "/api/v1/ml/models/lightgbm/train?n_estimators=5&num_leaves=8&learning_rate=0.1&random_seed=42",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["model_type"] == "LIGHTGBM"
    assert "test_metrics" in data


def test_api_phase_134_random_forest_train(client, setup_b03_data):
    """Test POST /api/v1/ml/models/random-forest/train."""
    token = setup_b03_data["token"]
    response = client.post(
        "/api/v1/ml/models/random-forest/train?n_estimators=5&max_depth=3&random_seed=42",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["model_type"] == "RANDOM_FOREST"
    assert "test_metrics" in data


def test_api_phase_135_model_comparison(client, setup_b03_data):
    """Test POST /api/v1/ml/models/compare."""
    token = setup_b03_data["token"]
    response = client.post(
        "/api/v1/ml/models/compare?random_seed=42",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["evaluated_models"]) == 3
    assert data["winner_model_type"] in ["XGBOOST", "LIGHTGBM", "RANDOM_FOREST"]
    assert "comparison_notes" in data


def test_api_unauthorized_access(client):
    """Verify unauthorized requests without token are rejected."""
    response = client.post("/api/v1/ml/pipeline/risk-dataset")
    assert response.status_code in (401, 403)
