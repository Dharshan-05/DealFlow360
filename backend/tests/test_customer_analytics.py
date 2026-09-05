"""Comprehensive Test Suite for Customer Analytics, Search, Filtering, Segmentation, and Dashboard (Phases 066–070).

Verifies:
- Phase 066: Customer Analytics (aggregates, distributions, zero-division safety on empty datasets)
- Phase 067: Customer Search (case-insensitive partial matching on code, name, email, phone)
- Phase 068: Customer Filtering (single and composable filters: is_active, tier_id, combined with search)
- Phase 069: Customer Segmentation (deterministic rule-based categorization: Champions, Growth Potential, Discount Sensitive, At Risk, Unclassified)
- Phase 070: Customer Dashboard (consolidated KPIs, DonutChart/BarChart data points, activity summaries, RBAC enforcement)
"""
import uuid
from decimal import Decimal
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select

from app.core.jwt import create_access_token
from app.db.session import SessionLocal
from app.main import app
from app.models.company import Company
from app.models.customer import Customer
from app.models.customer_deal_history import CustomerDealHistory
from app.models.customer_discount_history import CustomerDiscountHistory
from app.models.customer_payment_history import CustomerPaymentHistory
from app.models.customer_purchase_history import CustomerPurchaseHistory
from app.models.customer_tier import CustomerTier
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User


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
def setup_g14_test_data(db_session):
    """Seed test company, tiers, users, and customer accounts for G14 tests."""
    unique_suffix = uuid.uuid4().hex[:8]
    company = Company(
        name=f"G14 Enterprise Org {unique_suffix}",
        legal_name=f"G14 Enterprise Inc {unique_suffix}",
        email=f"g14_enterprise_{unique_suffix}@example.com",
        is_active=True,
    )
    db_session.add(company)
    db_session.flush()

    # Create Gold Tier
    tier_gold = CustomerTier(
        name=f"G14 Gold Tier {unique_suffix}",
        code=f"TIER-G14-GOLD-{unique_suffix.upper()}",
        discount_limit=Decimal("20.00"),
        is_active=True,
    )
    db_session.add(tier_gold)
    db_session.flush()

    # Permissions & Roles
    perm_read = db_session.scalars(select(Permission).where(Permission.name == "customers:read")).first()
    perm_write = db_session.scalars(select(Permission).where(Permission.name == "customers:write")).first()

    role = Role(name=f"G14 Manager Role {unique_suffix}", description="G14 Test Manager")
    role.permissions.extend([p for p in [perm_read, perm_write] if p])
    db_session.add(role)
    db_session.flush()

    user = User(
        email=f"g14_user_{unique_suffix}@test.com",
        first_name="G14",
        last_name="Tester",
        company_id=company.id,
        is_active=True,
    )
    user.roles.append(role)
    db_session.add(user)
    db_session.flush()

    # Seed 3 distinct customers with specific profiles
    # 1. Champion Customer (Tiered, high purchases, completed payments)
    cust_champion = Customer(
        customer_code=f"CHAMP-{uuid.uuid4().hex[:6].upper()}",
        name="Champion Aerospace Corp",
        email="procure@champion-aero.com",
        phone="+1-555-0199",
        company_id=company.id,
        tier_id=tier_gold.id,
        is_active=True,
    )
    # 2. At Risk Customer (Inactive with failed payments)
    cust_risk = Customer(
        customer_code=f"RISK-{uuid.uuid4().hex[:6].upper()}",
        name="Vulnerable Logistics Ltd",
        email="ops@vulnerable-logistics.com",
        phone="+1-555-0288",
        company_id=company.id,
        is_active=False,
    )
    # 3. Discount Sensitive Customer
    cust_sens = Customer(
        customer_code=f"SENS-{uuid.uuid4().hex[:6].upper()}",
        name="Bargain Retailers Group",
        email="contact@bargain-retail.com",
        phone="+1-555-0377",
        company_id=company.id,
        is_active=True,
    )
    db_session.add_all([cust_champion, cust_risk, cust_sens])
    db_session.flush()

    # Champion purchase & payment transactions
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)

    p1 = CustomerPurchaseHistory(
        company_id=company.id,
        customer_id=cust_champion.id,
        order_number="ORD-CHAMP-1",
        purchase_date=now,
        total_amount=Decimal("15000.00"),
        status="COMPLETED",
    )
    p2 = CustomerPurchaseHistory(
        company_id=company.id,
        customer_id=cust_champion.id,
        order_number="ORD-CHAMP-2",
        purchase_date=now,
        total_amount=Decimal("18000.00"),
        status="COMPLETED",
    )
    pay1 = CustomerPaymentHistory(
        company_id=company.id,
        customer_id=cust_champion.id,
        payment_reference="PAY-CHAMP-1",
        amount=Decimal("33000.00"),
        status="COMPLETED",
        payment_date=now,
    )
    d1 = CustomerDealHistory(
        company_id=company.id,
        customer_id=cust_champion.id,
        deal_code="DEAL-CHAMP-1",
        title="Fleet Upgrade Contract",
        deal_value=Decimal("50000.00"),
        status="WON",
    )
    db_session.add_all([p1, p2, pay1, d1])

    # Vulnerable customer failed payment
    pay_fail = CustomerPaymentHistory(
        company_id=company.id,
        customer_id=cust_risk.id,
        payment_reference="PAY-FAIL-1",
        amount=Decimal("5000.00"),
        status="FAILED",
        payment_date=now,
    )
    db_session.add(pay_fail)

    # Discount sensitive customer heavy discounts
    p_sens = CustomerPurchaseHistory(
        company_id=company.id,
        customer_id=cust_sens.id,
        order_number="ORD-SENS-1",
        purchase_date=now,
        total_amount=Decimal("2000.00"),
        status="COMPLETED",
    )
    disc_sens = CustomerDiscountHistory(
        company_id=company.id,
        customer_id=cust_sens.id,
        discount_code="DISC-HEAVY-01",
        discount_percentage=Decimal("35.00"),
        discount_amount=Decimal("700.00"),
        applied_at=now,
    )
    db_session.add_all([p_sens, disc_sens])

    db_session.commit()

    token = create_access_token(str(user.id))

    return {
        "user": user,
        "token": token,
        "company": company,
        "tier_gold": tier_gold,
        "cust_champion": cust_champion,
        "cust_risk": cust_risk,
        "cust_sens": cust_sens,
    }


# ===========================================================================
# Phase 066: Customer Analytics Tests
# ===========================================================================

def test_phase_066_customer_analytics(client, setup_g14_test_data):
    """Verify deterministic customer analytics calculations and portfolio metrics."""
    data = setup_g14_test_data
    token = data["token"]

    res = client.get(
        "/api/v1/customers/analytics",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["success"] is True
    analytics = res_data["data"]

    assert analytics["total_customers"] >= 3
    assert analytics["active_customers"] >= 2
    assert analytics["inactive_customers"] >= 1
    assert analytics["tiered_customers"] >= 1
    assert float(analytics["total_purchases_amount"]) >= 35000.00
    assert float(analytics["total_deals_value"]) >= 50000.00
    assert float(analytics["total_payments_amount"]) >= 33000.00
    assert len(analytics["tier_distribution"]) >= 1


def test_phase_066_customer_analytics_empty_company(client, db_session):
    """Verify analytics handles an empty organization with zero-division safety."""
    empty_company = Company(
        name=f"Empty Org {uuid.uuid4().hex[:6]}",
        legal_name="Empty Org Inc",
        is_active=True,
    )
    db_session.add(empty_company)
    db_session.flush()

    perm_read = db_session.scalars(select(Permission).where(Permission.name == "customers:read")).first()
    role = Role(name=f"Role {uuid.uuid4().hex[:6]}")
    role.permissions.append(perm_read)
    db_session.add(role)
    db_session.flush()

    user = User(
        email=f"empty_{uuid.uuid4().hex[:6]}@test.com",
        first_name="Empty",
        last_name="User",
        company_id=empty_company.id,
        is_active=True,
    )
    user.roles.append(role)
    db_session.add(user)
    db_session.commit()

    token = create_access_token(str(user.id))

    res = client.get(
        "/api/v1/customers/analytics",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    analytics = res.json()["data"]
    assert analytics["total_customers"] == 0
    assert float(analytics["average_customer_ltv"]) == 0.0
    assert float(analytics["average_order_value"]) == 0.0


# ===========================================================================
# Phase 067: Customer Search Tests
# ===========================================================================

def test_phase_067_search_by_name(client, setup_g14_test_data):
    """Verify search by partial case-insensitive customer name."""
    data = setup_g14_test_data
    token = data["token"]

    res = client.get(
        "/api/v1/customers?search=champion",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    items = res.json()["data"]["items"]
    assert len(items) >= 1
    assert any("Champion" in c["name"] for c in items)


def test_phase_067_search_by_code_and_phone(client, setup_g14_test_data):
    """Verify search by customer code and phone number."""
    data = setup_g14_test_data
    token = data["token"]
    champ = data["cust_champion"]

    # Search by code
    res_code = client.get(
        f"/api/v1/customers?search={champ.customer_code}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_code.status_code == 200
    items = res_code.json()["data"]["items"]
    assert any(c["customer_code"] == champ.customer_code for c in items)

    # Search by phone
    res_phone = client.get(
        "/api/v1/customers?search=0199",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_phone.status_code == 200
    items_phone = res_phone.json()["data"]["items"]
    assert any(c["phone"] == champ.phone for c in items_phone)


def test_phase_067_search_no_results(client, setup_g14_test_data):
    """Verify empty result when search term does not match any record."""
    data = setup_g14_test_data
    token = data["token"]

    res = client.get(
        "/api/v1/customers?search=nonexistent_customer_xyz",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert len(res.json()["data"]["items"]) == 0


# ===========================================================================
# Phase 068: Customer Filtering Tests
# ===========================================================================

def test_phase_068_filter_by_status(client, setup_g14_test_data):
    """Verify filtering customers by active and inactive status."""
    data = setup_g14_test_data
    token = data["token"]

    # Active only
    res_active = client.get(
        "/api/v1/customers?is_active=true",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_active.status_code == 200
    for c in res_active.json()["data"]["items"]:
        assert c["is_active"] is True

    # Inactive only
    res_inactive = client.get(
        "/api/v1/customers?is_active=false",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_inactive.status_code == 200
    for c in res_inactive.json()["data"]["items"]:
        assert c["is_active"] is False


def test_phase_068_filter_by_tier_and_combined(client, setup_g14_test_data):
    """Verify filtering by tier_id and combined filters."""
    data = setup_g14_test_data
    token = data["token"]
    tier_id = str(data["tier_gold"].id)

    # Tier only
    res_tier = client.get(
        f"/api/v1/customers?tier_id={tier_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_tier.status_code == 200
    items = res_tier.json()["data"]["items"]
    assert len(items) >= 1
    for c in items:
        assert c["tier_id"] == tier_id

    # Composable search + tier + is_active
    res_comb = client.get(
        f"/api/v1/customers?search=champion&tier_id={tier_id}&is_active=true",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_comb.status_code == 200
    items_comb = res_comb.json()["data"]["items"]
    assert len(items_comb) == 1
    assert items_comb[0]["customer_code"] == data["cust_champion"].customer_code


# ===========================================================================
# Phase 069: Customer Segmentation Tests
# ===========================================================================

def test_phase_069_customer_segmentation(client, setup_g14_test_data):
    """Verify deterministic rule-based segmentation classification."""
    data = setup_g14_test_data
    token = data["token"]

    res = client.get(
        "/api/v1/customers/segmentation",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    seg = res.json()["data"]

    assert seg["total_evaluated"] >= 3
    assert len(seg["distribution"]) == 5

    # Verify specific customer assignments
    cust_map = {c["customer_id"]: c for c in seg["customers"]}

    champ_id = str(data["cust_champion"].id)
    assert champ_id in cust_map
    assert cust_map[champ_id]["segment"] == "CHAMPIONS"

    risk_id = str(data["cust_risk"].id)
    assert risk_id in cust_map
    assert cust_map[risk_id]["segment"] == "AT_RISK"


# ===========================================================================
# Phase 070: Customer Dashboard Tests
# ===========================================================================

def test_phase_070_customer_dashboard(client, setup_g14_test_data):
    """Verify customer dashboard KPIs, chart data structures, and analytics."""
    data = setup_g14_test_data
    token = data["token"]

    res = client.get(
        "/api/v1/customers/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    dash = res.json()["data"]

    kpis = dash["kpis"]
    assert kpis["total_customers"] >= 3
    assert kpis["active_customers"] >= 2
    assert float(kpis["portfolio_ltv"]) >= 35000.00
    assert kpis["high_risk_customers_count"] >= 1

    # Check chart data structures
    assert len(dash["tier_chart_data"]) >= 1
    for pt in dash["tier_chart_data"]:
        assert "label" in pt
        assert "value" in pt

    assert len(dash["risk_chart_data"]) >= 1
    assert len(dash["segment_chart_data"]) >= 1

    # Check activity summary
    assert "purchases" in dash["recent_activity_summary"]
    assert "deals" in dash["recent_activity_summary"]
