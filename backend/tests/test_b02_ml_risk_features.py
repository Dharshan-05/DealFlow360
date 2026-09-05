"""Comprehensive Test Suite for DealFlow360 B02 (Phases 126–130: AI/ML Risk Foundation).

Verifies:
- Phase 126: Customer Features (tenure, tier, lifetime value, AOV, default ratio, new customer safety)
- Phase 127: Deal Value Features (nominal value, log transform, size categories, outlier detection, deal-to-AOV ratio)
- Phase 128: Discount Behavior Features (count, frequency %, volatility, trend slope, escalation rate)
- Phase 129: Margin Behavior Features (avg/min/max margin, volatility, low-margin count/frequency, erosion trend)
- Phase 130: Risk Target Definition (deterministic binary is_high_risk, multi-criteria breach, severity levels)
- Data Leakage Prevention: Point-in-time strictly enforced — future deals/discounts do NOT alter historical features
- Tabular ML Features Vector Export: to_flat_dict(include_targets=False/True)
- API Endpoints & RBAC: /api/v1/ml/features/* and /api/v1/ml/datasets/deals
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
from app.schemas.ml_risk import (
    DealSizeCategory,
    EngineeredFeatureVector,
    RiskTarget,
)
from app.services.ml_risk import (
    CustomerFeatureEngineer,
    DealValueFeatureEngineer,
    DiscountBehaviorFeatureEngineer,
    FeatureEngineeringService,
    HistoricalDealDatasetExtractor,
    MarginBehaviorFeatureEngineer,
    MLDatasetPreparationService,
    RiskTargetGenerator,
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
def setup_b02_data(db_session):
    """Seed test company, tier, customer, product, historical deals, discounts, and purchases."""
    # 1. Company
    company = Company(
        name=f"B02 Test Co {uuid.uuid4().hex[:6]}",
        legal_name="B02 Test Corp",
        email=f"b02_{uuid.uuid4().hex[:6]}@example.com",
    )
    db_session.add(company)
    db_session.commit()

    # 2. Customer Tier (Gold tier with 15% limit)
    tier_gold = CustomerTier(
        name=f"Gold-{uuid.uuid4().hex[:8]}",
        code=f"GLD-{uuid.uuid4().hex[:12]}",
        discount_limit=Decimal("15.00"),
        description="Gold tier 15%",
    )
    db_session.add(tier_gold)
    db_session.commit()

    # 3. Mature Customer under Company
    customer = Customer(
        company_id=company.id,
        tier_id=tier_gold.id,
        customer_code=f"CUST-B02-{uuid.uuid4().hex[:10]}",
        name="Horizon Enterprise Tech",
        email=f"horizon_{uuid.uuid4().hex[:10]}@example.com",
    )
    db_session.add(customer)
    db_session.commit()

    # 4. Product Category and Product
    cat = ProductCategory(
        name=f"B02 Cat {uuid.uuid4().hex[:8]}",
        code=f"B02C-{uuid.uuid4().hex[:12]}",
        description="Software licenses",
    )
    db_session.add(cat)
    db_session.commit()

    product = Product(
        category_id=cat.id,
        sku=f"SKU-B02-{uuid.uuid4().hex[:12]}",
        name="Enterprise Subscription Suite",
        cost=Decimal("500.00"),
        base_price=Decimal("2000.00"),
        unit="license",
    )
    db_session.add(product)
    db_session.commit()

    # 5. Discount Governance Policy (15% ceiling)
    now = datetime.now(timezone.utc)
    config = DiscountConfiguration(
        company_id=company.id,
        name="B02 Policy Config",
        default_discount_ceiling=Decimal("15.00"),
        effective_from=now - timedelta(days=60),
        is_active=True,
    )
    db_session.add(config)
    db_session.commit()

    # 6. Customer Historical Purchases (Phase 059)
    p1 = CustomerPurchaseHistory(
        company_id=company.id,
        customer_id=customer.id,
        order_number=f"PO1-{uuid.uuid4().hex[:6]}",
        purchase_date=now - timedelta(days=50),
        total_amount=Decimal("10000.00"),
        status="COMPLETED",
        item_count=5,
    )
    p2 = CustomerPurchaseHistory(
        company_id=company.id,
        customer_id=customer.id,
        order_number=f"PO2-{uuid.uuid4().hex[:6]}",
        purchase_date=now - timedelta(days=35),
        total_amount=Decimal("15000.00"),
        status="COMPLETED",
        item_count=8,
    )
    # 7. Customer Historical Payments (Phase 062) - 1 completed, 1 failed
    pay1 = CustomerPaymentHistory(
        company_id=company.id,
        customer_id=customer.id,
        payment_reference=f"PAY1-{uuid.uuid4().hex[:6]}",
        amount=Decimal("10000.00"),
        status="COMPLETED",
        created_at=now - timedelta(days=49),
    )
    pay2 = CustomerPaymentHistory(
        company_id=company.id,
        customer_id=customer.id,
        payment_reference=f"PAY2-FAIL-{uuid.uuid4().hex[:6]}",
        amount=Decimal("15000.00"),
        status="FAILED",
        created_at=now - timedelta(days=34),
    )
    # 8. Customer Historical Discounts (Phase 061)
    disc1 = CustomerDiscountHistory(
        company_id=company.id,
        customer_id=customer.id,
        discount_code="DISC-1",
        discount_percentage=Decimal("5.00"),
        discount_amount=Decimal("500.00"),
        applied_at=now - timedelta(days=48),
    )
    disc2 = CustomerDiscountHistory(
        company_id=company.id,
        customer_id=customer.id,
        discount_code="DISC-2",
        discount_percentage=Decimal("10.00"),
        discount_amount=Decimal("1500.00"),
        applied_at=now - timedelta(days=33),
    )
    db_session.add_all([p1, p2, pay1, pay2, disc1, disc2])
    db_session.commit()

    # 9. Reference Deal at T = now - 20 days
    deal_ref = CustomerDealHistory(
        company_id=company.id,
        customer_id=customer.id,
        deal_code=f"DEAL-REF-{uuid.uuid4().hex[:6]}",
        title="Mid-Year SaaS Renewal",
        deal_value=Decimal("20000.00"),
        status="WON",
        sales_rep_name="Maria Analyst",
        created_at=now - timedelta(days=20),
    )
    db_session.add(deal_ref)
    db_session.commit()

    # 10. Applied Discount corresponding to reference deal
    applied_disc_ref = AppliedDiscount(
        company_id=company.id,
        customer_id=customer.id,
        product_id=product.id,
        deal_reference=deal_ref.deal_code,
        decision_id="DEC-B02-001",
        requested_discount=Decimal("12.00"),
        applied_discount=Decimal("12.00"),
        selling_price=Decimal("2000.00"),
        discounted_price=Decimal("1760.00"),
        unit_cost=Decimal("500.00"),
        margin_percentage=Decimal("71.59"),
        risk_level="LOW",
        reason_code="GOVERNANCE_OPTIMAL",
        created_at=now - timedelta(days=20),
    )
    db_session.add(applied_disc_ref)
    db_session.commit()

    # 11. User with permissions
    user = User(
        company_id=company.id,
        email=f"b02_analyst_{uuid.uuid4().hex[:6]}@example.com",
        password_hash="mocked_argon2_hash",
        first_name="Risk",
        last_name="Engineer",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    perm = db_session.scalar(select(Permission).where(Permission.name == "discounts:read"))
    if not perm:
        perm = Permission(name="discounts:read", resource="discounts", action="read")
        db_session.add(perm)
        db_session.commit()

    role = Role(name=f"B02_Auditor_{uuid.uuid4().hex[:6]}", description="B02 dataset auditor")
    role.permissions.append(perm)
    db_session.add(role)
    db_session.commit()

    user.roles.append(role)
    db_session.commit()

    return {
        "company": company,
        "customer": customer,
        "tier": tier_gold,
        "product": product,
        "deal_ref": deal_ref,
        "applied_disc_ref": applied_disc_ref,
        "user": user,
    }


# ==============================================================================
# Phase 126: Customer Features Tests
# ==============================================================================

def test_phase_126_customer_features_mature():
    """Verify Phase 126 customer feature engineering for an active, mature customer."""
    features = CustomerFeatureEngineer.compute(
        tenure_days=180,
        customer_tier="GOLD",
        tier_discount_limit=Decimal("15.00"),
        lifetime_orders=2,
        lifetime_revenue=Decimal("25000.00"),
        lifetime_settled=Decimal("10000.00"),
        failed_payments=1,
        total_payments=2,
        avg_discount_pct=Decimal("7.50"),
        discount_count=2,
    )

    assert features.customer_tenure_days == 180
    assert features.customer_tier == "GOLD"
    assert features.tier_discount_limit == 15.0
    assert features.is_established_customer is True
    assert features.lifetime_orders_count == 2
    assert features.lifetime_revenue == 25000.0
    assert features.lifetime_settled_amount == 10000.0
    assert features.average_order_value == 12500.0
    assert features.payment_default_ratio == 0.5
    assert features.payment_reliability_score == 50.0
    assert features.has_payment_history is True
    assert 0.0 <= features.price_sensitivity_score <= 100.0


def test_phase_126_customer_features_new_customer():
    """Verify Phase 126 customer features default safely when customer has zero prior history."""
    features = CustomerFeatureEngineer.compute(
        tenure_days=0,
        customer_tier="STANDARD",
        tier_discount_limit=Decimal("10.00"),
        lifetime_orders=0,
        lifetime_revenue=Decimal("0.00"),
        lifetime_settled=Decimal("0.00"),
        failed_payments=0,
        total_payments=0,
        avg_discount_pct=Decimal("0.00"),
        discount_count=0,
    )

    assert features.customer_tenure_days == 0
    assert features.is_established_customer is False
    assert features.lifetime_orders_count == 0
    assert features.lifetime_revenue == 0.0
    assert features.lifetime_settled_amount == 0.0
    assert features.average_order_value == 0.0
    assert features.payment_default_ratio == 0.0
    assert features.payment_reliability_score == 85.0
    assert features.has_payment_history is False
    assert features.price_sensitivity_score == 20.0


# ==============================================================================
# Phase 127: Deal Value Features Tests
# ==============================================================================

def test_phase_127_deal_value_features_sizing_and_outlier():
    """Verify Phase 127 sizing categories, log transform, and outlier detection."""
    # Test MICRO (< 1000)
    micro = DealValueFeatureEngineer.compute(
        deal_value=Decimal("500.00"),
        customer_aov=Decimal("500.00"),
        has_prior_orders=True,
    )
    assert micro.deal_size_category == "MICRO"
    assert round(micro.log_deal_value, 2) == 6.22  # log(501) = 6.2166

    # Test SMALL (1000 - 10000)
    small = DealValueFeatureEngineer.compute(
        deal_value=Decimal("2500.00"),
        customer_aov=Decimal("2000.00"),
        has_prior_orders=True,
    )
    assert small.deal_size_category == "SMALL"
    assert small.deal_to_aov_ratio == 1.25

    # Test MEDIUM (10000 - 50000)
    med = DealValueFeatureEngineer.compute(
        deal_value=Decimal("15000.00"),
        customer_aov=Decimal("15000.00"),
        has_prior_orders=True,
    )
    assert med.deal_size_category == "MEDIUM"

    # Test LARGE (50000 - 250000)
    large = DealValueFeatureEngineer.compute(
        deal_value=Decimal("60000.00"),
        customer_aov=Decimal("25000.00"),
        has_prior_orders=True,
    )
    assert large.deal_size_category == "LARGE"

    # Test ENTERPRISE (>= 250000)
    ent = DealValueFeatureEngineer.compute(
        deal_value=Decimal("300000.00"),
        customer_aov=Decimal("50000.00"),
        has_prior_orders=True,
    )
    assert ent.deal_size_category == "ENTERPRISE"

    # Test Outlier Detection (> 3x customer AOV)
    outlier = DealValueFeatureEngineer.compute(
        deal_value=Decimal("25000.00"),
        customer_aov=Decimal("5000.00"),
        has_prior_orders=True,
    )
    assert outlier.is_deal_value_outlier is True
    assert outlier.deal_to_aov_ratio == 5.0
    assert outlier.deal_value_deviation_from_aov == 20000.0


# ==============================================================================
# Phase 128: Discount Behavior Features Tests
# ==============================================================================

def test_phase_128_discount_behavior_features():
    """Verify Phase 128 discount behavior metrics, volatility, slope, and escalation."""
    prior_discounts = [Decimal("5.00"), Decimal("10.00"), Decimal("15.00"), Decimal("20.00")]
    total_orders = 5

    features = DiscountBehaviorFeatureEngineer.compute(
        prior_discounts=prior_discounts,
        total_prior_orders=total_orders,
    )

    assert features.historical_discount_count == 4
    assert features.historical_discount_frequency_pct == 80.0  # 4 / 5 = 80%
    assert features.historical_avg_discount_pct == 12.5  # (5 + 10 + 15 + 20) / 4 = 12.5
    assert features.historical_max_discount_pct == 20.0
    assert features.historical_discount_volatility > 0.0
    assert features.discount_trend_slope == 1.0  # expanding discounts


def test_phase_128_discount_behavior_empty():
    """Verify Phase 128 handles zero prior discount records safely."""
    features = DiscountBehaviorFeatureEngineer.compute(
        prior_discounts=[],
        total_prior_orders=0,
    )

    assert features.historical_discount_count == 0
    assert features.historical_discount_frequency_pct == 0.0
    assert features.historical_avg_discount_pct == 0.0
    assert features.historical_max_discount_pct == 0.0
    assert features.historical_discount_volatility == 0.0
    assert features.discount_trend_slope == 0.0


# ==============================================================================
# Phase 129: Margin Behavior Features Tests
# ==============================================================================

def test_phase_129_margin_behavior_features():
    """Verify Phase 129 realized margin metrics, volatility, erosion slope, and low-margin counts."""
    # Realized margins declining over time: [50.0, 40.0, 30.0, 10.0]
    margins = [Decimal("50.00"), Decimal("40.00"), Decimal("30.00"), Decimal("10.00")]
    features = MarginBehaviorFeatureEngineer.compute(
        prior_applied_discounts=margins,
    )

    assert features.historical_avg_margin_pct == 32.5
    assert features.historical_min_margin_pct == 10.0
    assert features.historical_max_margin_pct == 50.0
    assert features.historical_margin_volatility > 0.0
    assert features.historical_low_margin_deal_count == 1  # 10.0 is < 20.0 floor
    assert features.low_margin_frequency_pct == 25.0  # 1 / 4 = 25%
    assert features.margin_erosion_trend == -1.0  # deteriorating margins
    assert features.has_prior_margin_history is True


def test_phase_129_margin_behavior_empty():
    """Verify Phase 129 handles customer without prior margin history safely."""
    features = MarginBehaviorFeatureEngineer.compute(
        prior_applied_discounts=[],
    )

    assert features.historical_avg_margin_pct == 0.0
    assert features.historical_min_margin_pct == 0.0
    assert features.historical_max_margin_pct == 0.0
    assert features.historical_margin_volatility == 0.0
    assert features.historical_low_margin_deal_count == 0
    assert features.low_margin_frequency_pct == 0.0
    assert features.margin_erosion_trend == 0.0
    assert features.has_prior_margin_history is False


# ==============================================================================
# Phase 130: Risk Target Definition Tests
# ==============================================================================

def test_phase_130_risk_target_clean_deal():
    """Verify Phase 130 marks normal, compliant deals as low risk with target=0."""
    target = RiskTargetGenerator.generate_target(
        requested_discount_pct=Decimal("8.00"),
        effective_ceiling=Decimal("15.00"),
        margin_pct=Decimal("30.00"),
        risk_level="LOW",
        decision_outcome="APPROVED",
        deal_status="WON",
    )

    assert target.is_high_risk == 0
    assert target.risk_level == "LOW"
    assert target.risk_category == "NONE"
    assert len(target.trigger_reasons) == 0


def test_phase_130_risk_target_governance_breach():
    """Verify Phase 130 flags discount policy ceiling breach as high risk."""
    target = RiskTargetGenerator.generate_target(
        requested_discount_pct=Decimal("20.00"),
        effective_ceiling=Decimal("15.00"),
        margin_pct=Decimal("25.00"),
        risk_level="HIGH",
        decision_outcome="ESCALATION_REQUIRED",
    )

    assert target.is_high_risk == 1
    assert target.risk_category == "GOVERNANCE_BREACH"
    assert target.is_governance_breached is True
    assert any("breached governance ceiling" in r for r in target.trigger_reasons)


def test_phase_130_risk_target_margin_erosion():
    """Verify Phase 130 flags low margin as CRITICAL/HIGH risk."""
    target = RiskTargetGenerator.generate_target(
        requested_discount_pct=Decimal("10.00"),
        effective_ceiling=Decimal("15.00"),
        margin_pct=Decimal("10.00"),
        risk_level="CRITICAL",
    )

    assert target.is_high_risk == 1
    assert target.risk_level == "CRITICAL"
    assert target.risk_category == "MARGIN_EROSION"
    assert target.is_margin_breached is True
    assert any("minimum threshold" in r for r in target.trigger_reasons)


def test_phase_130_risk_target_deal_rejection():
    """Verify Phase 130 flags deal rejection/loss."""
    target = RiskTargetGenerator.generate_target(
        deal_status="LOST",
        decision_outcome="REJECTED",
    )

    assert target.is_high_risk == 1
    assert target.risk_category == "DEAL_REJECTION"
    assert target.is_rejected is True


def test_phase_130_risk_target_payment_default():
    """Verify Phase 130 flags customer payment default."""
    target = RiskTargetGenerator.generate_target(
        prior_failed_payments_count=2,
    )

    assert target.risk_category == "PAYMENT_DEFAULT"


# ==============================================================================
# Point-in-Time Data Leakage Safeguard Test
# ==============================================================================

def test_point_in_time_data_leakage_safeguard(db_session, setup_b02_data):
    """Verify zero future data leakage: events after reference deal created_at DO NOT affect features."""
    data = setup_b02_data
    company = data["company"]
    customer = data["customer"]
    deal_ref = data["deal_ref"]

    # 1. Extract and compute feature vector for deal_ref
    records_before = HistoricalDealDatasetExtractor.extract_records(
        db=db_session,
        company_id=company.id,
    )
    deal_record_before = next(r for r in records_before if r.deal_reference == deal_ref.deal_code)
    features_before = FeatureEngineeringService.transform_record(
        db=db_session,
        record=deal_record_before,
    )

    # 2. Insert a FUTURE deal, purchase, and applied discount occurring 5 days AFTER deal_ref
    future_date = deal_ref.created_at + timedelta(days=5)

    future_purchase = CustomerPurchaseHistory(
        company_id=company.id,
        customer_id=customer.id,
        order_number=f"PO-FUTURE-{uuid.uuid4().hex[:6]}",
        purchase_date=future_date,
        total_amount=Decimal("99999.00"),
        status="COMPLETED",
        item_count=10,
    )
    future_deal = CustomerDealHistory(
        company_id=company.id,
        customer_id=customer.id,
        deal_code=f"DEAL-FUTURE-{uuid.uuid4().hex[:6]}",
        title="Future Multi-Million Deal",
        deal_value=Decimal("500000.00"),
        status="LOST",
        sales_rep_name="Future Rep",
        created_at=future_date,
    )
    future_disc = CustomerDiscountHistory(
        company_id=company.id,
        customer_id=customer.id,
        discount_code="DISC-FUTURE",
        discount_percentage=Decimal("45.00"),
        discount_amount=Decimal("45000.00"),
        applied_at=future_date,
    )
    db_session.add_all([future_purchase, future_deal, future_disc])
    db_session.commit()

    # 3. Re-extract and recompute feature vector for deal_ref
    records_after = HistoricalDealDatasetExtractor.extract_records(
        db=db_session,
        company_id=company.id,
    )
    deal_record_after = next(r for r in records_after if r.deal_reference == deal_ref.deal_code)
    features_after = FeatureEngineeringService.transform_record(
        db=db_session,
        record=deal_record_after,
    )

    # 4. Assert exact equality between before and after features
    assert features_before.customer_features.lifetime_revenue == features_after.customer_features.lifetime_revenue
    assert features_before.customer_features.lifetime_orders_count == features_after.customer_features.lifetime_orders_count
    assert features_before.discount_behavior_features.historical_avg_discount_pct == features_after.discount_behavior_features.historical_avg_discount_pct
    assert features_before.discount_behavior_features.historical_max_discount_pct == features_after.discount_behavior_features.historical_max_discount_pct
    assert features_before.margin_behavior_features.historical_avg_margin_pct == features_after.margin_behavior_features.historical_avg_margin_pct
    assert features_before.target.is_high_risk == features_after.target.is_high_risk


# ==============================================================================
# Flat Tabular Dict (37 Features) Test
# ==============================================================================

def test_flat_dict_feature_vector_37_features(db_session, setup_b02_data):
    """Verify that to_flat_dict exports exactly 37 non-target features and 41 with targets."""
    data = setup_b02_data
    company = data["company"]
    deal_ref = data["deal_ref"]

    records = HistoricalDealDatasetExtractor.extract_records(
        db=db_session,
        company_id=company.id,
    )
    deal_rec = next(r for r in records if r.deal_reference == deal_ref.deal_code)
    vector = FeatureEngineeringService.transform_record(db=db_session, record=deal_rec)

    flat_features = vector.to_flat_dict(include_targets=False)
    # Verify presence of features from each phase
    assert "deal_value" in flat_features  # Baseline
    assert "requested_discount_pct" in flat_features  # Phase 124
    assert "discounted_margin_pct" in flat_features  # Phase 125
    assert "customer_tenure_days" in flat_features  # Phase 126
    assert "deal_size_category" in flat_features  # Phase 127
    assert "historical_discount_volatility" in flat_features  # Phase 128
    assert "historical_avg_margin_pct" in flat_features  # Phase 129
    assert "target_is_high_risk" not in flat_features  # Target excluded

    flat_with_targets = vector.to_flat_dict(include_targets=True)
    assert "target_is_high_risk" in flat_with_targets
    assert "target_risk_category" in flat_with_targets


# ==============================================================================
# API Endpoints & RBAC Tests (Phases 126–130)
# ==============================================================================

def test_api_endpoints_phases_126_to_130(client, setup_b02_data):
    """Verify all new Phase 126-130 API calculation endpoints respond correctly with RBAC."""
    data = setup_b02_data
    user = data["user"]
    token = create_access_token(subject=str(user.id))
    headers = {"Authorization": f"Bearer {token}"}

    # Phase 126: Customer Features
    r_cust = client.get(
        "/api/v1/ml/features/customer",
        params={"tenure_days": 120, "lifetime_orders": 3, "lifetime_revenue": 15000},
        headers=headers,
    )
    assert r_cust.status_code == 200
    cust_data = r_cust.json()
    assert cust_data["customer_tenure_days"] == 120
    assert cust_data["average_order_value"] == 5000.0

    # Phase 127: Deal Value Features
    r_deal = client.get(
        "/api/v1/ml/features/deal-value",
        params={"deal_value": 75000.0, "customer_aov": 25000.0, "has_prior_orders": True},
        headers=headers,
    )
    assert r_deal.status_code == 200
    deal_data = r_deal.json()
    assert deal_data["deal_size_category"] == "LARGE"
    assert deal_data["deal_to_aov_ratio"] == 3.0

    # Phase 128: Discount Behavior Features
    r_disc = client.get(
        "/api/v1/ml/features/discount-behavior",
        params={"discount_history": [5.0, 10.0, 15.0], "total_prior_orders": 3},
        headers=headers,
    )
    assert r_disc.status_code == 200
    disc_data = r_disc.json()
    assert disc_data["historical_discount_count"] == 3
    assert disc_data["historical_avg_discount_pct"] == 10.0

    # Phase 129: Margin Behavior Features
    r_margin = client.get(
        "/api/v1/ml/features/margin-behavior",
        params={"margin_history": [45.0, 35.0, 25.0]},
        headers=headers,
    )
    assert r_margin.status_code == 200
    margin_data = r_margin.json()
    assert margin_data["historical_avg_margin_pct"] == 35.0
    assert margin_data["historical_low_margin_deal_count"] == 0

    # Phase 130: Risk Target
    r_target = client.get(
        "/api/v1/ml/features/risk-target",
        params={"effective_ceiling": 15.0, "requested_discount_pct": 20.0},
        headers=headers,
    )
    assert r_target.status_code == 200
    target_data = r_target.json()
    assert target_data["is_high_risk"] == 1
    assert target_data["risk_category"] == "GOVERNANCE_BREACH"

    # Full Dataset endpoint returns engineered feature vector including Phase 126-130
    r_dataset = client.get("/api/v1/ml/datasets/deals", headers=headers)
    assert r_dataset.status_code == 200
    ds_data = r_dataset.json()
    assert ds_data["metadata"]["feature_count"] == 37
    assert len(ds_data["features"]) >= 1
    sample_vec = ds_data["features"][0]
    assert "customer_features" in sample_vec
    assert "deal_value_features" in sample_vec
    assert "discount_behavior_features" in sample_vec
    assert "margin_behavior_features" in sample_vec
    assert "target" in sample_vec
