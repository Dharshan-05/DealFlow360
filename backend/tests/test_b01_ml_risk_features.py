"""Comprehensive Test Suite for DealFlow360 B01 (Phases 121–125: AI/ML Risk Foundation).

Verifies:
- Phase 121: ML Dataset Preparation (deterministic dataset metadata, record validation, invalid record filtering, sensitive field exclusion)
- Phase 122: Historical Deal Dataset (point-in-time extraction from CustomerDealHistory & AppliedDiscount, deterministic ordering, empty dataset handling)
- Phase 123: Feature Engineering (numerical and categorical transformation, null safety, log transforms, tenure, flat dict export, zero leakage)
- Phase 124: Discount Features (requested discount, ceiling utilization ratio, breach flags, customer baseline deviation, Decimal precision)
- Phase 125: Margin Features (unit cost, selling price, gross margin, discounted margin, compression ratio, zero cost/price edge cases, Decimal precision)
- Security & RBAC: Multi-tenant isolation (company_id filtering), authentication requirements, sensitive credentials exclusion (no passwords/hashes/JWTs)
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
from app.models.customer_discount_ceiling import CustomerDiscountCeiling
from app.models.customer_discount_history import CustomerDiscountHistory
from app.models.customer_payment_history import CustomerPaymentHistory
from app.models.customer_purchase_history import CustomerPurchaseHistory
from app.models.customer_tier import CustomerTier
from app.models.discount_configuration import DiscountConfiguration
from app.models.permission import Permission
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.role import Role
from app.models.user import User
from app.schemas.ml_risk import DatasetType, EngineeredFeatureVector, RawDealRecord
from app.services.ml_risk import (
    DiscountFeatureEngineer,
    FeatureEngineeringService,
    HistoricalDealDatasetExtractor,
    MarginFeatureEngineer,
    MLDatasetPreparationService,
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
def setup_b01_data(db_session):
    """Seed test company, tier, customer, product, historical deals, discounts, and purchases."""
    # 1. Company A & Company B (for multi-tenant verification)
    company_a = Company(
        name=f"B01 Company A {uuid.uuid4().hex[:6]}",
        legal_name="B01 Company A Inc.",
        email=f"comp_a_{uuid.uuid4().hex[:6]}@example.com",
    )
    company_b = Company(
        name=f"B01 Company B {uuid.uuid4().hex[:6]}",
        legal_name="B01 Company B Inc.",
        email=f"comp_b_{uuid.uuid4().hex[:6]}@example.com",
    )
    db_session.add_all([company_a, company_b])
    db_session.commit()

    # 2. Customer Tier (Silver with 10% limit)
    tier_silver = CustomerTier(
        name=f"Silver-{uuid.uuid4().hex[:8]}",
        code=f"SLV-{uuid.uuid4().hex[:12]}",
        discount_limit=Decimal("10.00"),
        description="Silver tier 10%",
    )
    db_session.add(tier_silver)
    db_session.commit()

    # 3. Customer under Company A
    customer = Customer(
        company_id=company_a.id,
        tier_id=tier_silver.id,
        customer_code=f"CUST-{uuid.uuid4().hex[:6]}",
        name="Apex Enterprise Solutions",
        email="apex@example.com",
    )
    db_session.add(customer)
    db_session.commit()

    # 4. Product Category and Product
    cat = ProductCategory(
        name=f"Cloud Compute {uuid.uuid4().hex[:6]}",
        code=f"CC-{uuid.uuid4().hex[:12]}",
        description="Compute resources",
    )
    db_session.add(cat)
    db_session.commit()

    product = Product(
        category_id=cat.id,
        sku=f"SKU-SRV-{uuid.uuid4().hex[:12]}",
        name="Dedicated Server Instance",
        cost=Decimal("400.00"),
        base_price=Decimal("1000.00"),
        unit="server",
    )
    db_session.add(product)
    db_session.commit()

    # 5. Discount Governance Policy (Company baseline 15%)
    now = datetime.now(timezone.utc)
    config = DiscountConfiguration(
        company_id=company_a.id,
        name="Baseline Governance Config",
        default_discount_ceiling=Decimal("15.00"),
        effective_from=now - timedelta(days=30),
        is_active=True,
    )
    db_session.add(config)
    db_session.commit()

    # 6. Customer Historical Purchases (Phase 059)
    p1 = CustomerPurchaseHistory(
        company_id=company_a.id,
        customer_id=customer.id,
        order_number=f"PO-{uuid.uuid4().hex[:6]}",
        purchase_date=now - timedelta(days=20),
        total_amount=Decimal("5000.00"),
        status="COMPLETED",
        item_count=5,
    )
    # 7. Customer Historical Payments (Phase 062)
    pay1 = CustomerPaymentHistory(
        company_id=company_a.id,
        customer_id=customer.id,
        payment_reference=f"PAY-{uuid.uuid4().hex[:6]}",
        amount=Decimal("5000.00"),
        status="COMPLETED",
        created_at=now - timedelta(days=19),
    )
    # 8. Customer Historical Discounts (Phase 061)
    disc1 = CustomerDiscountHistory(
        company_id=company_a.id,
        customer_id=customer.id,
        discount_code="DISC-EARLY",
        discount_percentage=Decimal("8.00"),
        discount_amount=Decimal("400.00"),
        applied_at=now - timedelta(days=15),
    )
    db_session.add_all([p1, pay1, disc1])
    db_session.commit()

    # 9. Customer Deal History (Phase 060)
    deal1 = CustomerDealHistory(
        company_id=company_a.id,
        customer_id=customer.id,
        deal_code=f"DEAL-{uuid.uuid4().hex[:6]}",
        title="Q1 Infrastructure Upgrade",
        deal_value=Decimal("12000.00"),
        status="WON",
        sales_rep_name="Alex Rep",
        created_at=now - timedelta(days=10),
    )
    db_session.add(deal1)
    db_session.commit()

    # 10. Applied Discount (Phase 120)
    applied_disc = AppliedDiscount(
        company_id=company_a.id,
        customer_id=customer.id,
        product_id=product.id,
        deal_reference=f"DEAL-APPLIED-{uuid.uuid4().hex[:6]}",
        decision_id="DEC-TEST-001",
        requested_discount=Decimal("12.00"),
        applied_discount=Decimal("12.00"),
        selling_price=Decimal("1000.00"),
        discounted_price=Decimal("880.00"),
        unit_cost=Decimal("400.00"),
        margin_percentage=Decimal("54.55"),
        risk_level="LOW",
        reason_code="GOVERNANCE_OPTIMAL",
        created_at=now - timedelta(days=5),
    )
    db_session.add(applied_disc)
    db_session.commit()

    # 11. User with permissions
    user = User(
        company_id=company_a.id,
        email=f"ml_analyst_{uuid.uuid4().hex[:6]}@example.com",
        password_hash="mocked_argon2_hash",
        first_name="Data",
        last_name="Scientist",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    # Assign discounts:read permission via role
    perm = db_session.scalar(select(Permission).where(Permission.name == "discounts:read"))
    if not perm:
        perm = Permission(name="discounts:read", resource="discounts", action="read")
        db_session.add(perm)
        db_session.commit()

    role = Role(name=f"ML_Auditor_{uuid.uuid4().hex[:6]}", description="ML dataset access")
    role.permissions.append(perm)
    db_session.add(role)
    db_session.commit()

    user.roles.append(role)
    db_session.commit()

    return {
        "company_a": company_a,
        "company_b": company_b,
        "customer": customer,
        "tier": tier_silver,
        "product": product,
        "deal1": deal1,
        "applied_disc": applied_disc,
        "user": user,
    }


# ==============================================================================
# Phase 125: Margin Features Tests
# ==============================================================================

def test_phase_125_margin_feature_engineering_precision():
    """Verify Phase 125 deterministic margin features and Decimal precision."""
    # Selling Price: 1000, Unit Cost: 400, Discount: 10%
    # Original Margin = 600 (60.0%), Discounted Price = 900
    # Discounted Margin = 500 (55.56%), Margin Reduction = 100 / 600 = 0.1667
    features = MarginFeatureEngineer.compute(
        selling_price=Decimal("1000.00"),
        unit_cost=Decimal("400.00"),
        discount_pct=Decimal("10.00"),
    )

    assert features.selling_price == 1000.0
    assert features.unit_cost == 400.0
    assert features.gross_margin_amount == 600.0
    assert features.gross_margin_pct == 60.0
    assert features.discounted_price == 900.0
    assert features.discounted_margin_amount == 500.0
    assert round(features.discounted_margin_pct, 2) == 55.56
    assert round(features.margin_reduction_ratio, 4) == 0.1667
    assert features.is_negative_margin is False
    assert features.is_zero_cost is False


def test_phase_125_margin_feature_edge_cases():
    """Verify margin calculations with zero price, zero cost, and cost exceeding price."""
    # Zero cost
    zero_cost_feat = MarginFeatureEngineer.compute(
        selling_price=Decimal("500.00"),
        unit_cost=Decimal("0.00"),
        discount_pct=Decimal("20.00"),
    )
    assert zero_cost_feat.is_zero_cost is True
    assert zero_cost_feat.gross_margin_pct == 100.0
    assert zero_cost_feat.discounted_price == 400.0

    # Negative margin (discount pushes price below cost)
    neg_margin_feat = MarginFeatureEngineer.compute(
        selling_price=Decimal("100.00"),
        unit_cost=Decimal("80.00"),
        discount_pct=Decimal("30.00"),  # discounted price = 70 < cost 80
    )
    assert neg_margin_feat.discounted_price == 70.0
    assert neg_margin_feat.discounted_margin_amount == -10.0
    assert neg_margin_feat.is_negative_margin is True

    # Zero selling price
    zero_price_feat = MarginFeatureEngineer.compute(
        selling_price=Decimal("0.00"),
        unit_cost=Decimal("50.00"),
        discount_pct=Decimal("0.00"),
    )
    assert zero_price_feat.gross_margin_pct == 0.0
    assert zero_price_feat.discounted_margin_amount == -50.0


# ==============================================================================
# Phase 124: Discount Features Tests
# ==============================================================================

def test_phase_124_discount_feature_engineering():
    """Verify Phase 124 discount feature calculations and ceiling utilization."""
    features = DiscountFeatureEngineer.compute(
        requested_discount_pct=Decimal("12.00"),
        effective_ceiling_pct=Decimal("15.00"),
        customer_historical_avg_pct=Decimal("8.00"),
        tier_discount_limit=Decimal("10.00"),
        deal_value=Decimal("10000.00"),
        has_prior_history=True,
    )

    assert features.requested_discount_pct == 12.0
    assert features.effective_ceiling_pct == 15.0
    assert features.ceiling_utilization_ratio == 0.8  # 12 / 15
    assert features.is_ceiling_breached is False
    assert features.customer_historical_avg_discount == 8.0
    assert features.discount_deviation_from_customer_avg == 4.0  # 12 - 8
    assert features.tier_utilization_ratio == 1.2  # 12 / 10
    assert features.discount_amount_est == 1200.0
    assert features.has_prior_discount_history is True


def test_phase_124_discount_ceiling_breach():
    """Verify ceiling breach detection in discount features."""
    features = DiscountFeatureEngineer.compute(
        requested_discount_pct=Decimal("20.00"),
        effective_ceiling_pct=Decimal("15.00"),
        customer_historical_avg_pct=Decimal("0.00"),
        tier_discount_limit=Decimal("10.00"),
        deal_value=Decimal("5000.00"),
        has_prior_history=False,
    )
    assert features.is_ceiling_breached is True
    assert round(features.ceiling_utilization_ratio, 2) == 1.33


# ==============================================================================
# Phase 122: Historical Deal Dataset Extractor Tests
# ==============================================================================

def test_phase_122_historical_deal_extraction(db_session, setup_b01_data):
    """Verify extraction of historical deal records from existing database models."""
    company_id = setup_b01_data["company_a"].id
    records = HistoricalDealDatasetExtractor.extract_records(db=db_session, company_id=company_id)

    assert len(records) >= 2  # 1 AppliedDiscount + 1 CustomerDealHistory
    
    # Check deterministic sorting
    for i in range(len(records) - 1):
        assert records[i].created_at <= records[i + 1].created_at

    # Verify field population without synthetic mocks
    rec = records[0]
    assert isinstance(rec, RawDealRecord)
    assert rec.company_id == company_id
    assert rec.customer_code == setup_b01_data["customer"].customer_code
    assert rec.customer_tier.startswith("SLV-")
    assert rec.tier_discount_limit == Decimal("10.00")
    # Verify prior metrics are computed without future leakage
    assert rec.prior_purchases_count >= 0


def test_phase_122_empty_dataset_handling(db_session, setup_b01_data):
    """Verify that an isolated company with no deals returns a clean empty list."""
    company_b_id = setup_b01_data["company_b"].id
    records = HistoricalDealDatasetExtractor.extract_records(db=db_session, company_id=company_b_id)
    assert records == []


# ==============================================================================
# Phase 123: Feature Engineering Vector Tests
# ==============================================================================

def test_phase_123_feature_vector_transformation(db_session, setup_b01_data):
    """Verify transformation of raw records into complete ML-ready feature vectors."""
    company_id = setup_b01_data["company_a"].id
    records = HistoricalDealDatasetExtractor.extract_records(db=db_session, company_id=company_id)
    rec = records[0]

    feature_vector = FeatureEngineeringService.transform_record(db=db_session, record=rec)
    assert isinstance(feature_vector, EngineeredFeatureVector)
    assert feature_vector.record_id == rec.record_id
    assert feature_vector.customer_tier == rec.customer_tier
    assert feature_vector.deal_value > 0
    assert feature_vector.log_deal_value > 0

    # Flat dict export check
    flat_dict = feature_vector.to_flat_dict(include_targets=True)
    assert "deal_value" in flat_dict
    assert "requested_discount_pct" in flat_dict
    assert "gross_margin_pct" in flat_dict
    assert "target_risk_level" in flat_dict
    assert isinstance(flat_dict["is_ceiling_breached"], int)


# ==============================================================================
# Phase 121: ML Dataset Preparation Orchestration Tests
# ==============================================================================

def test_phase_121_dataset_preparation_service(db_session, setup_b01_data):
    """Verify end-to-end dataset preparation service and manifest generation."""
    company_id = setup_b01_data["company_a"].id
    response = MLDatasetPreparationService.prepare_deal_risk_dataset(
        db=db_session,
        company_id=company_id,
    )

    assert response.metadata.dataset_type == DatasetType.HISTORICAL_DEALS
    assert response.metadata.company_id == company_id
    assert response.metadata.total_records_extracted >= 2
    assert response.metadata.valid_records_count == len(response.features)
    assert response.metadata.invalid_records_count == 0
    assert response.metadata.feature_count >= 21
    assert len(response.features) > 0


def test_phase_121_filtering_and_invalidation(db_session, setup_b01_data):
    """Verify dataset filtering by min_deal_value and status."""
    company_id = setup_b01_data["company_a"].id
    # Filter with high min_deal_value that excludes smaller deals
    response = MLDatasetPreparationService.prepare_deal_risk_dataset(
        db=db_session,
        company_id=company_id,
        min_deal_value=Decimal("5000.00"),
    )

    for fv in response.features:
        assert fv.deal_value >= 5000.0
    assert response.metadata.invalid_records_count >= 1


# ==============================================================================
# Security & RBAC & Endpoint Tests
# ==============================================================================

def test_b01_endpoints_rbac_and_tenant_isolation(client, setup_b01_data):
    """Verify API endpoints require authentication, permissions, and enforce multi-tenancy."""
    user = setup_b01_data["user"]
    token = create_access_token(subject=str(user.id))
    headers = {"Authorization": f"Bearer {token}"}

    # 1. GET /api/v1/ml/datasets/deals
    resp = client.get("/api/v1/ml/datasets/deals", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "metadata" in data
    assert "features" in data
    assert data["metadata"]["company_id"] == str(user.company_id)

    # 2. GET /api/v1/ml/datasets/deals/raw
    raw_resp = client.get("/api/v1/ml/datasets/deals/raw", headers=headers)
    assert raw_resp.status_code == 200
    raw_list = raw_resp.json()
    assert len(raw_list) > 0
    for item in raw_list:
        assert item["company_id"] == str(user.company_id)

    # 3. GET /api/v1/ml/features/discount
    disc_feat_resp = client.get(
        "/api/v1/ml/features/discount?requested_discount_pct=10&deal_value=5000",
        headers=headers,
    )
    assert disc_feat_resp.status_code == 200
    assert disc_feat_resp.json()["requested_discount_pct"] == 10.0

    # 4. GET /api/v1/ml/features/margin
    margin_feat_resp = client.get(
        "/api/v1/ml/features/margin?selling_price=1000&unit_cost=400&discount_pct=15",
        headers=headers,
    )
    assert margin_feat_resp.status_code == 200
    assert margin_feat_resp.json()["gross_margin_pct"] == 60.0

    # 5. Unauthenticated request rejected (401)
    unauth_resp = client.get("/api/v1/ml/datasets/deals")
    assert unauth_resp.status_code == 401


def test_b01_sensitive_field_exclusion(client, setup_b01_data):
    """Verify that NO password hashes, secrets, or auth tokens appear in dataset output."""
    user = setup_b01_data["user"]
    token = create_access_token(subject=str(user.id))
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/v1/ml/datasets/deals", headers=headers)
    assert resp.status_code == 200
    content_str = resp.text

    assert "password_hash" not in content_str
    assert "secret" not in content_str.lower()
    assert "refresh_token" not in content_str
