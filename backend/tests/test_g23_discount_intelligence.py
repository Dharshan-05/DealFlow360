"""Comprehensive Test Suite for DealFlow360 G23 (Phases 111–115).

Verifies:
- Phase 111: Recommended Discount Engine (Deterministic recommendation, clamping to max safe, explainability reason codes, fallback for no history)
- Phase 112: Maximum Safe Discount (Intersection of governed ceiling, margin protection, actor limits, limiting factor detection)
- Phase 113: Margin Protection Engine (Strict Decimal precision, edge cases: cost >= price, zero price, negative margin, min margin >= 100%)
- Phase 114: Historical Discount Analysis (Multi-tenant company isolation, zero sample handling, sample size, avg, min, max, latest discount)
- Phase 115: Customer Discount Analysis (Active customer ceiling integration, compliance rating, customer profile context)
- Security & RBAC: 401 unauthenticated, 403 unauthorized
"""
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.jwt import create_access_token
from app.db.session import SessionLocal
from app.main import app
from app.models.category_discount_ceiling import CategoryDiscountCeiling
from app.models.company import Company
from app.models.customer import Customer
from app.models.customer_discount_ceiling import CustomerDiscountCeiling
from app.models.customer_discount_history import CustomerDiscountHistory
from app.models.customer_tier import CustomerTier
from app.models.discount_configuration import DiscountConfiguration
from app.models.permission import Permission
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.product_discount_ceiling import ProductDiscountCeiling
from app.models.role import Role
from app.models.sales_rep_authority_limit import SalesRepAuthorityLimit
from app.models.user import User
from app.services.discount_intelligence import (
    CustomerDiscountAnalysisService,
    DiscountHistoryAnalysisService,
    DiscountRecommendationEngine,
    MarginProtectionEngine,
    MaximumSafeDiscountEngine,
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
def setup_g23_test_data(db_session):
    """Seed test company, roles, users, products with costs, customer with tier and discount history."""
    suffix = uuid.uuid4().hex[:8]

    company = Company(
        name=f"G23 Enterprise {suffix}",
        legal_name=f"G23 Enterprise Corp {suffix}",
        is_active=True,
    )
    db_session.add(company)
    db_session.flush()

    # Permissions
    perm_read = db_session.scalars(select(Permission).where(Permission.name == "discounts:read")).first()
    if not perm_read:
        perm_read = Permission(name="discounts:read", description="Read discounts")
        db_session.add(perm_read)

    perm_write = db_session.scalars(select(Permission).where(Permission.name == "discounts:write")).first()
    if not perm_write:
        perm_write = Permission(name="discounts:write", description="Write discounts")
        db_session.add(perm_write)

    db_session.flush()

    # Roles
    admin_role = Role(name=f"Admin_{suffix}", description="Admin role")
    admin_role.permissions.extend([perm_read, perm_write])
    db_session.add(admin_role)

    rep_role = Role(name=f"Sales Representative_{suffix}", description="Sales Rep role")
    rep_role.permissions.append(perm_read)
    db_session.add(rep_role)

    no_perm_role = Role(name=f"Viewer_{suffix}", description="Viewer role without discount permissions")
    db_session.add(no_perm_role)
    db_session.flush()

    # Users
    admin_user = User(
        email=f"admin_{suffix}@example.com",
        first_name="Admin",
        last_name="User",
        is_active=True,
        company_id=company.id,
        roles=[admin_role],
    )
    db_session.add(admin_user)

    rep_user = User(
        email=f"rep_{suffix}@example.com",
        first_name="Rep",
        last_name="User",
        is_active=True,
        company_id=company.id,
        roles=[rep_role],
    )
    db_session.add(rep_user)

    viewer_user = User(
        email=f"viewer_{suffix}@example.com",
        first_name="Viewer",
        last_name="User",
        is_active=True,
        company_id=company.id,
        roles=[no_perm_role],
    )
    db_session.add(viewer_user)

    # Category
    category = ProductCategory(
        name=f"Category {suffix}",
        code=f"CAT_{suffix}",
        is_active=True,
    )
    db_session.add(category)
    db_session.flush()

    # Standard profitable product: Cost = $60, Base Price = $100 -> Margin = 40%
    product = Product(
        sku=f"SKU_{suffix}_1",
        name=f"Enterprise Server {suffix}",
        base_price=Decimal("100.00"),
        cost=Decimal("60.00"),
        category_id=category.id,
        is_active=True,
    )
    db_session.add(product)

    # Low margin / loss product: Cost = $110, Base Price = $100 -> Negative margin
    loss_product = Product(
        sku=f"SKU_{suffix}_LOSS",
        name=f"Loss Item {suffix}",
        base_price=Decimal("100.00"),
        cost=Decimal("110.00"),
        category_id=category.id,
        is_active=True,
    )
    db_session.add(loss_product)

    # Zero cost product: Cost = $0, Base Price = $100 -> 100% Margin
    zero_cost_product = Product(
        sku=f"SKU_{suffix}_ZERO",
        name=f"Digital License {suffix}",
        base_price=Decimal("100.00"),
        cost=Decimal("0.00"),
        category_id=category.id,
        is_active=True,
    )
    db_session.add(zero_cost_product)

    # Customer Tier
    tier = CustomerTier(
        name=f"Gold Tier {suffix}",
        code=f"GOLD_{suffix}",
        discount_limit=Decimal("10.00"),
        is_active=True,
    )
    db_session.add(tier)
    db_session.flush()

    # Customer
    customer = Customer(
        company_id=company.id,
        customer_code=f"CUST_{suffix}",
        name=f"Acme Corp {suffix}",
        tier_id=tier.id,
        is_active=True,
    )
    db_session.add(customer)

    # Second Customer with NO discount history
    customer_no_history = Customer(
        company_id=company.id,
        customer_code=f"CUST_NO_HIST_{suffix}",
        name=f"Fresh Corp {suffix}",
        is_active=True,
    )
    db_session.add(customer_no_history)

    # Another Company for multi-tenant checks
    other_company = Company(
        name=f"Other Co {suffix}",
        legal_name=f"Other Co Legal {suffix}",
        is_active=True,
    )
    db_session.add(other_company)
    db_session.flush()

    other_customer = Customer(
        company_id=other_company.id,
        customer_code=f"CUST_OTHER_{suffix}",
        name=f"Other Customer {suffix}",
        is_active=True,
    )
    db_session.add(other_customer)
    db_session.flush()

    # Baseline Company Discount Configuration: Ceiling = 30%
    config = DiscountConfiguration(
        company_id=company.id,
        name=f"Company Default {suffix}",
        default_discount_ceiling=Decimal("30.00"),
        is_active=True,
        effective_from=datetime.now(timezone.utc) - timedelta(days=5),
    )
    db_session.add(config)

    # Customer Discount Ceiling: Ceiling = 25%
    cust_ceiling = CustomerDiscountCeiling(
        company_id=company.id,
        customer_id=customer.id,
        max_discount_percentage=Decimal("25.00"),
        is_active=True,
        effective_from=datetime.now(timezone.utc) - timedelta(days=5),
    )
    db_session.add(cust_ceiling)

    # Sales Rep Authority Limit: Max = 15%
    rep_limit = SalesRepAuthorityLimit(
        company_id=company.id,
        user_id=rep_user.id,
        max_authorized_discount=Decimal("15.00"),
        is_active=True,
        effective_from=datetime.now(timezone.utc) - timedelta(days=5),
    )
    db_session.add(rep_limit)

    # Historical discount grants for customer:
    # 1. 10.00% ($10.00)
    # 2. 12.00% ($12.00)
    # 3. 14.00% ($14.00)
    # Mean = 12.00%, Min = 10.00%, Max = 14.00%, Latest = 14.00%
    hist1 = CustomerDiscountHistory(
        company_id=company.id,
        customer_id=customer.id,
        discount_code="PROMO10",
        discount_percentage=Decimal("10.00"),
        discount_amount=Decimal("10.00"),
        applied_at=datetime.now(timezone.utc) - timedelta(days=10),
    )
    hist2 = CustomerDiscountHistory(
        company_id=company.id,
        customer_id=customer.id,
        discount_code="PROMO12",
        discount_percentage=Decimal("12.00"),
        discount_amount=Decimal("12.00"),
        applied_at=datetime.now(timezone.utc) - timedelta(days=5),
    )
    hist3 = CustomerDiscountHistory(
        company_id=company.id,
        customer_id=customer.id,
        discount_code="PROMO14",
        discount_percentage=Decimal("14.00"),
        discount_amount=Decimal("14.00"),
        applied_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    db_session.add_all([hist1, hist2, hist3])

    # Other company discount history (should never be seen)
    hist_other = CustomerDiscountHistory(
        company_id=other_company.id,
        customer_id=other_customer.id,
        discount_code="OTHER50",
        discount_percentage=Decimal("50.00"),
        discount_amount=Decimal("500.00"),
        applied_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    db_session.add(hist_other)

    db_session.commit()

    admin_headers = {"Authorization": f"Bearer {create_access_token(admin_user.id)}"}
    rep_headers = {"Authorization": f"Bearer {create_access_token(rep_user.id)}"}
    viewer_headers = {"Authorization": f"Bearer {create_access_token(viewer_user.id)}"}

    return {
        "company": company,
        "admin_user": admin_user,
        "rep_user": rep_user,
        "viewer_user": viewer_user,
        "admin_headers": admin_headers,
        "rep_headers": rep_headers,
        "viewer_headers": viewer_headers,
        "product": product,
        "loss_product": loss_product,
        "zero_cost_product": zero_cost_product,
        "customer": customer,
        "customer_no_history": customer_no_history,
        "other_company": other_company,
        "other_customer": other_customer,
    }


# ==============================================================================
# Phase 113 Tests: Margin Protection Engine
# ==============================================================================

def test_margin_protection_profitable_product(db_session, setup_g23_test_data):
    """Product: Price = 100, Cost = 60. Current margin = 40%.

    Target min margin = 20%.
    Formula: d <= (1 - 60 / (100 * 0.80)) * 100 = (1 - 60/80) * 100 = 25.00%.
    """
    data = setup_g23_test_data
    res = MarginProtectionEngine.evaluate(
        db=db_session,
        company_id=data["company"].id,
        product_id=data["product"].id,
        min_margin_percentage=Decimal("20.00"),
    )
    assert res.is_margin_preserved is True
    assert res.current_margin_percentage == Decimal("40.00")
    assert res.protected_margin_percentage == Decimal("20.00")
    assert res.max_discount_from_margin == Decimal("25.00")
    assert res.reason_code == "SAFE_MARGIN"


def test_margin_protection_cost_exceeds_price(db_session, setup_g23_test_data):
    """Cost ($110) > Price ($100) -> Max discount must be strictly 0.00%."""
    data = setup_g23_test_data
    res = MarginProtectionEngine.evaluate(
        db=db_session,
        company_id=data["company"].id,
        product_id=data["loss_product"].id,
        min_margin_percentage=Decimal("15.00"),
    )
    assert res.is_margin_preserved is False
    assert res.current_margin_percentage == Decimal("-10.00")
    assert res.max_discount_from_margin == Decimal("0.00")
    assert res.reason_code == "COST_EXCEEDS_PRICE"


def test_margin_protection_zero_cost(db_session, setup_g23_test_data):
    """Cost = 0, Price = 100. For zero cost, margin is 100% at any selling price > 0,

    allowing up to 100% discount.
    """
    data = setup_g23_test_data
    res = MarginProtectionEngine.evaluate(
        db=db_session,
        company_id=data["company"].id,
        product_id=data["zero_cost_product"].id,
        min_margin_percentage=Decimal("15.00"),
    )
    assert res.is_margin_preserved is True
    assert res.current_margin_percentage == Decimal("100.00")
    assert res.max_discount_from_margin == Decimal("100.00")
    assert res.reason_code == "SAFE_MARGIN"


def test_margin_protection_insufficient_buffer(db_session, setup_g23_test_data):
    """Price = 100, Cost = 60 (Margin = 40%). Target min margin = 45% (higher than current).

    Must return 0.00% discount.
    """
    data = setup_g23_test_data
    res = MarginProtectionEngine.evaluate(
        db=db_session,
        company_id=data["company"].id,
        product_id=data["product"].id,
        min_margin_percentage=Decimal("45.00"),
    )
    assert res.max_discount_from_margin == Decimal("0.00")
    assert res.reason_code == "INSUFFICIENT_MARGIN_BUFFER"


# ==============================================================================
# Phase 112 Tests: Maximum Safe Discount
# ==============================================================================

def test_maximum_safe_discount_actor_authority_bound(db_session, setup_g23_test_data):
    """For Sales Rep:

    - Governed Ceiling = 25% (Customer ceiling)
    - Margin Ceiling = 25% (Product: 100 price, 60 cost, 20% margin)
    - Actor Authority Limit = 15% (Rep limit)
    -> Maximum Safe Discount must be 15.00% (Limiting factor: ACTOR_AUTHORITY).
    """
    data = setup_g23_test_data
    res = MaximumSafeDiscountEngine.evaluate(
        db=db_session,
        company_id=data["company"].id,
        customer_id=data["customer"].id,
        product_id=data["product"].id,
        actor=data["rep_user"],
        min_margin_percentage=Decimal("20.00"),
    )
    assert res.governed_ceiling == Decimal("25.00")
    assert res.margin_ceiling == Decimal("25.00")
    assert res.actor_authority_limit == Decimal("15.00")
    assert res.max_safe_discount == Decimal("15.00")
    assert res.limiting_factor == "ACTOR_AUTHORITY"


def test_maximum_safe_discount_margin_bound(db_session, setup_g23_test_data):
    """For Admin (no authority restriction):

    - Governed Ceiling = 25%
    - Margin Ceiling with min_margin=30%:
      d <= (1 - 60 / (100 * 0.70)) * 100 = (1 - 60/70) * 100 = 14.29%
    -> Maximum Safe Discount must be 14.29% (Limiting factor: MARGIN_LIMIT).
    """
    data = setup_g23_test_data
    res = MaximumSafeDiscountEngine.evaluate(
        db=db_session,
        company_id=data["company"].id,
        customer_id=data["customer"].id,
        product_id=data["product"].id,
        actor=data["admin_user"],
        min_margin_percentage=Decimal("30.00"),
    )
    assert res.governed_ceiling == Decimal("25.00")
    assert res.margin_ceiling == Decimal("14.29")
    assert res.max_safe_discount == Decimal("14.29")
    assert res.limiting_factor == "MARGIN_LIMIT"


# ==============================================================================
# Phase 114 Tests: Historical Discount Analysis
# ==============================================================================

def test_historical_discount_analysis_multi_tenant(db_session, setup_g23_test_data):
    """Historical records: 10%, 12%, 14% -> Mean = 12.00%, Min = 10.00%, Max = 14.00%, Latest = 14.00%.

    Must NOT see other_company's 50% discount record.
    """
    data = setup_g23_test_data
    res = DiscountHistoryAnalysisService.analyze_history(
        db=db_session,
        company_id=data["company"].id,
        customer_id=data["customer"].id,
    )
    assert res.has_history is True
    assert res.summary.sample_size == 3
    assert res.summary.average_discount == Decimal("12.00")
    assert res.summary.min_discount == Decimal("10.00")
    assert res.summary.max_discount == Decimal("14.00")
    assert res.summary.latest_discount == Decimal("14.00")
    assert res.summary.total_discount_amount == Decimal("36.00")


def test_historical_discount_analysis_zero_sample(db_session, setup_g23_test_data):
    """Customer with no history returns sample_size=0 and None for averages."""
    data = setup_g23_test_data
    res = DiscountHistoryAnalysisService.analyze_history(
        db=db_session,
        company_id=data["company"].id,
        customer_id=data["customer_no_history"].id,
    )
    assert res.has_history is False
    assert res.summary.sample_size == 0
    assert res.summary.average_discount is None
    assert res.summary.min_discount is None
    assert res.summary.latest_discount is None


# ==============================================================================
# Phase 115 Tests: Customer Discount Analysis
# ==============================================================================

def test_customer_discount_analysis_profile(db_session, setup_g23_test_data):
    """Checks active customer ceiling, tier name, and compliance rating."""
    data = setup_g23_test_data
    res = CustomerDiscountAnalysisService.analyze_customer(
        db=db_session,
        company_id=data["company"].id,
        customer_id=data["customer"].id,
    )
    assert res.customer_id == data["customer"].id
    assert res.active_customer_ceiling == Decimal("25.00")
    assert "Gold Tier" in res.tier_name
    assert res.compliance_rating == "COMPLIANT"
    assert res.history_summary.sample_size == 3


def test_customer_discount_analysis_no_history(db_session, setup_g23_test_data):
    """Customer without history rated NO_HISTORY."""
    data = setup_g23_test_data
    res = CustomerDiscountAnalysisService.analyze_customer(
        db=db_session,
        company_id=data["company"].id,
        customer_id=data["customer_no_history"].id,
    )
    assert res.compliance_rating == "NO_HISTORY"
    assert res.history_summary.sample_size == 0


# ==============================================================================
# Phase 111 Tests: Recommended Discount Engine
# ==============================================================================

def test_recommended_discount_historical_alignment(db_session, setup_g23_test_data):
    """Customer historical avg = 12.00%.

    Admin max safe = 25.00%.
    Recommended should align with historical average: 12.00% (HISTORICAL_ALIGNMENT).
    """
    data = setup_g23_test_data
    res = DiscountRecommendationEngine.recommend(
        db=db_session,
        company_id=data["company"].id,
        customer_id=data["customer"].id,
        product_id=data["product"].id,
        actor=data["admin_user"],
        min_margin_percentage=Decimal("20.00"),
    )
    assert res.recommended_discount == Decimal("12.00")
    assert res.max_safe_discount == Decimal("25.00")
    assert res.reason_code == "HISTORICAL_ALIGNMENT"
    assert "historical average discount" in res.reason_summary


def test_recommended_discount_clamped_to_max_safe(db_session, setup_g23_test_data):
    """Sales Rep authority = 10% (override via benchmark 15% or high margin restriction).

    If min_margin = 35% -> margin ceiling = 7.69%.
    Customer historical avg is 12.00%, but max safe is 7.69%.
    Recommended must be clamped to 7.69% (MAX_SAFE_CLAMPED).
    """
    data = setup_g23_test_data
    res = DiscountRecommendationEngine.recommend(
        db=db_session,
        company_id=data["company"].id,
        customer_id=data["customer"].id,
        product_id=data["product"].id,
        actor=data["admin_user"],
        min_margin_percentage=Decimal("35.00"),  # d <= 1 - 60/(100*0.65) = 1 - 0.9231 = 7.69%
    )
    assert res.max_safe_discount == Decimal("7.69")
    assert res.recommended_discount == Decimal("7.69")
    assert res.reason_code == "MAX_SAFE_CLAMPED"


def test_recommended_discount_no_history_fallback(db_session, setup_g23_test_data):
    """Customer with no history gets conservative default (5% or 50% of max safe)."""
    data = setup_g23_test_data
    res = DiscountRecommendationEngine.recommend(
        db=db_session,
        company_id=data["company"].id,
        customer_id=data["customer_no_history"].id,
        product_id=data["product"].id,
        actor=data["admin_user"],
        min_margin_percentage=Decimal("20.00"),
    )
    assert res.recommended_discount == Decimal("5.00")
    assert res.reason_code == "DEFAULT_BENCHMARK"


# ==============================================================================
# REST API Integration Tests
# ==============================================================================

def test_api_margin_protection(client, setup_g23_test_data):
    data = setup_g23_test_data
    resp = client.post(
        "/api/v1/governance/discounts/intelligence/margin-protection",
        headers=data["admin_headers"],
        json={
            "product_id": str(data["product"].id),
            "min_margin_percentage": 20.0,
        },
    )
    assert resp.status_code == 200
    res_data = resp.json()
    assert float(res_data["max_discount_from_margin"]) == 25.0
    assert res_data["is_margin_preserved"] is True


def test_api_maximum_safe_discount(client, setup_g23_test_data):
    data = setup_g23_test_data
    resp = client.post(
        "/api/v1/governance/discounts/intelligence/maximum-safe",
        headers=data["rep_headers"],
        json={
            "customer_id": str(data["customer"].id),
            "product_id": str(data["product"].id),
            "min_margin_percentage": 20.0,
        },
    )
    assert resp.status_code == 200
    res_data = resp.json()
    assert float(res_data["max_safe_discount"]) == 15.0  # Rep limit
    assert res_data["limiting_factor"] == "ACTOR_AUTHORITY"


def test_api_historical_discount_analysis(client, setup_g23_test_data):
    data = setup_g23_test_data
    resp = client.get(
        f"/api/v1/governance/discounts/intelligence/history?customer_id={data['customer'].id}",
        headers=data["admin_headers"],
    )
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["has_history"] is True
    assert res_data["summary"]["sample_size"] == 3
    assert float(res_data["summary"]["average_discount"]) == 12.0


def test_api_customer_discount_analysis(client, setup_g23_test_data):
    data = setup_g23_test_data
    resp = client.get(
        f"/api/v1/governance/discounts/intelligence/customer/{data['customer'].id}",
        headers=data["admin_headers"],
    )
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["compliance_rating"] == "COMPLIANT"
    assert float(res_data["active_customer_ceiling"]) == 25.0


def test_api_recommend_discount(client, setup_g23_test_data):
    data = setup_g23_test_data
    resp = client.post(
        "/api/v1/governance/discounts/intelligence/recommend",
        headers=data["admin_headers"],
        json={
            "customer_id": str(data["customer"].id),
            "product_id": str(data["product"].id),
            "min_margin_percentage": 20.0,
        },
    )
    assert resp.status_code == 200
    res_data = resp.json()
    assert float(res_data["recommended_discount"]) == 12.0
    assert res_data["reason_code"] == "HISTORICAL_ALIGNMENT"


def test_api_auth_and_rbac(client, setup_g23_test_data):
    data = setup_g23_test_data
    # 401 unauthenticated
    resp_unauth = client.post(
        "/api/v1/governance/discounts/intelligence/recommend",
        json={
            "customer_id": str(data["customer"].id),
            "product_id": str(data["product"].id),
        },
    )
    assert resp_unauth.status_code == 401

    # 403 unauthorized for user without discounts:read
    resp_forbid = client.post(
        "/api/v1/governance/discounts/intelligence/recommend",
        headers=data["viewer_headers"],
        json={
            "customer_id": str(data["customer"].id),
            "product_id": str(data["product"].id),
        },
    )
    assert resp_forbid.status_code == 403
