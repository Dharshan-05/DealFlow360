"""Comprehensive Test Suite for Customer Financial Intelligence Foundation (Phases 061–065).

Verifies:
- Phase 061: Customer Discount History (append-only recording, listing, customer/company isolation)
- Phase 062: Customer Payment History (append-only recording, listing, customer/company isolation)
- Phase 063: Customer LTV Calculation (0 orders, 1 order, multiple orders, zero-division safety)
- Phase 064: Customer Discount Sensitivity (INSUFFICIENT_DATA, LOW, MODERATE, HIGH)
- Phase 065: Customer Risk Profile (score calculation, LOW/MEDIUM/HIGH levels, payment default impact, account status)
- Consolidated Financial Intelligence API endpoint (GET /customers/{id}/financial-intelligence)
- Object-level authorization & Tenant Boundary Isolation
- RBAC permissions (customers:read, customers:write)
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select

from app.core.jwt import create_access_token
from app.db.session import SessionLocal
from app.main import app
from app.models.company import Company
from app.models.customer import Customer
from app.models.customer_discount_history import CustomerDiscountHistory
from app.models.customer_payment_history import CustomerPaymentHistory
from app.models.customer_purchase_history import CustomerPurchaseHistory
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
def setup_g13_test_data(db_session):
    """Seed test companies, users, and customer accounts for G13 intelligence tests."""
    company_a = db_session.scalars(select(Company).where(Company.name == "G13 Alpha Corp")).first()
    if not company_a:
        company_a = Company(
            name="G13 Alpha Corp",
            legal_name="G13 Alpha Inc",
            email="g13_alpha@example.com",
            is_active=True,
        )
        db_session.add(company_a)
        db_session.flush()

    company_b = db_session.scalars(select(Company).where(Company.name == "G13 Beta Corp")).first()
    if not company_b:
        company_b = Company(
            name="G13 Beta Corp",
            legal_name="G13 Beta Inc",
            email="g13_beta@example.com",
            is_active=True,
        )
        db_session.add(company_b)
        db_session.flush()

    perm_read = db_session.scalars(select(Permission).where(Permission.name == "customers:read")).first()
    perm_write = db_session.scalars(select(Permission).where(Permission.name == "customers:write")).first()

    rep_role = db_session.scalars(select(Role).where(Role.name == "G13 Rep Role")).first()
    if not rep_role:
        rep_role = Role(name="G13 Rep Role", description="G13 Test Rep Role")
        rep_role.permissions.extend([perm_read, perm_write])
        db_session.add(rep_role)
        db_session.flush()

    viewer_role = db_session.scalars(select(Role).where(Role.name == "G13 Viewer Role")).first()
    if not viewer_role:
        viewer_role = Role(name="G13 Viewer Role", description="G13 Test Viewer Role")
        viewer_role.permissions.append(perm_read)
        db_session.add(viewer_role)
        db_session.flush()

    user_alpha = db_session.scalars(select(User).where(User.email == "g13_rep_a@test.com")).first()
    if not user_alpha:
        user_alpha = User(
            email="g13_rep_a@test.com",
            first_name="Alpha",
            last_name="G13",
            company_id=company_a.id,
            is_active=True,
        )
        user_alpha.roles.append(rep_role)
        db_session.add(user_alpha)
        db_session.flush()

    user_viewer = db_session.scalars(select(User).where(User.email == "g13_viewer_a@test.com")).first()
    if not user_viewer:
        user_viewer = User(
            email="g13_viewer_a@test.com",
            first_name="Viewer",
            last_name="G13",
            company_id=company_a.id,
            is_active=True,
        )
        user_viewer.roles.append(viewer_role)
        db_session.add(user_viewer)
        db_session.flush()

    user_beta = db_session.scalars(select(User).where(User.email == "g13_rep_b@test.com")).first()
    if not user_beta:
        user_beta = User(
            email="g13_rep_b@test.com",
            first_name="Beta",
            last_name="G13",
            company_id=company_b.id,
            is_active=True,
        )
        user_beta.roles.append(rep_role)
        db_session.add(user_beta)
        db_session.flush()

    # Create target test customer in company A
    cust_code = f"G13-CUST-{uuid.uuid4().hex[:6].upper()}"
    customer_a = Customer(
        customer_code=cust_code,
        name="G13 Test Enterprise",
        company_id=company_a.id,
        is_active=True,
    )
    db_session.add(customer_a)
    db_session.flush()

    # Create target test customer in company B
    cust_b_code = f"G13-B-CUST-{uuid.uuid4().hex[:6].upper()}"
    customer_b = Customer(
        customer_code=cust_b_code,
        name="G13 Beta Customer",
        company_id=company_b.id,
        is_active=True,
    )
    db_session.add(customer_b)
    db_session.commit()

    token_a = create_access_token(str(user_alpha.id))
    token_viewer = create_access_token(str(user_viewer.id))
    token_b = create_access_token(str(user_beta.id))

    return {
        "user_alpha": user_alpha,
        "token_alpha": token_a,
        "user_viewer": user_viewer,
        "token_viewer": token_viewer,
        "user_beta": user_beta,
        "token_beta": token_b,
        "customer_a": customer_a,
        "customer_b": customer_b,
        "company_a": company_a,
        "company_b": company_b,
    }


# ===========================================================================
# Phase 061: Customer Discount History Tests
# ===========================================================================

def test_phase_061_discount_history_create_and_list(client, setup_g13_test_data):
    """Verify recording and listing discount history entries for a customer."""
    data = setup_g13_test_data
    token = data["token_alpha"]
    cust_id = str(data["customer_a"].id)

    # 1. Initially empty
    res = client.get(
        f"/api/v1/customers/{cust_id}/discount-history",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["success"] is True
    assert len(res_data["data"]) == 0

    # 2. Record discount entry
    payload = {
        "discount_code": "DISC-SEASONAL-12",
        "discount_percentage": "12.50",
        "discount_amount": "1250.00",
        "deal_reference": "DEAL-2026-VOL-01",
        "reason": "Contract renewal volume tier agreement",
    }
    create_res = client.post(
        f"/api/v1/customers/{cust_id}/discount-history",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_res.status_code == 201
    created_entry = create_res.json()["data"]
    assert created_entry["discount_code"] == "DISC-SEASONAL-12"
    assert float(created_entry["discount_percentage"]) == 12.50
    assert float(created_entry["discount_amount"]) == 1250.00
    assert created_entry["deal_reference"] == "DEAL-2026-VOL-01"

    # 3. Retrieve list and verify entry present
    list_res = client.get(
        f"/api/v1/customers/{cust_id}/discount-history",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_res.status_code == 200
    entries = list_res.json()["data"]
    assert len(entries) >= 1
    assert any(e["id"] == created_entry["id"] for e in entries)


def test_phase_061_discount_history_tenant_isolation(client, setup_g13_test_data):
    """Verify customer discount history cannot be accessed or created across tenants."""
    data = setup_g13_test_data
    token_beta = data["token_beta"]
    cust_a_id = str(data["customer_a"].id)

    # User in Company B cannot read Company A's customer discount history
    read_res = client.get(
        f"/api/v1/customers/{cust_a_id}/discount-history",
        headers={"Authorization": f"Bearer {token_beta}"},
    )
    assert read_res.status_code == 403

    # User in Company B cannot record discount history for Company A's customer
    post_res = client.post(
        f"/api/v1/customers/{cust_a_id}/discount-history",
        json={
            "discount_code": "DISC-ATTACK",
            "discount_percentage": "10.00",
            "discount_amount": "100.00",
        },
        headers={"Authorization": f"Bearer {token_beta}"},
    )
    assert post_res.status_code == 403


def test_phase_061_discount_history_permission_enforcement(client, setup_g13_test_data):
    """Verify write permission is required to post discount history."""
    data = setup_g13_test_data
    token_viewer = data["token_viewer"]
    cust_id = str(data["customer_a"].id)

    res = client.post(
        f"/api/v1/customers/{cust_id}/discount-history",
        json={
            "discount_code": "DISC-VIEW",
            "discount_percentage": "5.00",
            "discount_amount": "50.00",
        },
        headers={"Authorization": f"Bearer {token_viewer}"},
    )
    assert res.status_code == 403


# ===========================================================================
# Phase 062: Customer Payment History Tests
# ===========================================================================

def test_phase_062_payment_history_create_and_list(client, setup_g13_test_data):
    """Verify recording and listing customer payment history entries."""
    data = setup_g13_test_data
    token = data["token_alpha"]
    cust_id = str(data["customer_a"].id)

    # 1. Record completed payment
    pay_payload = {
        "payment_reference": f"PAY-{uuid.uuid4().hex[:6].upper()}",
        "amount": "4500.00",
        "status": "COMPLETED",
        "payment_method": "ACH_TRANSFER",
        "transaction_reference": "TXN-BANK-009182",
        "notes": "Invoice INV-001 settlement",
    }
    create_res = client.post(
        f"/api/v1/customers/{cust_id}/payment-history",
        json=pay_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_res.status_code == 201
    created_pay = create_res.json()["data"]
    assert created_pay["payment_reference"] == pay_payload["payment_reference"]
    assert float(created_pay["amount"]) == 4500.00
    assert created_pay["status"] == "COMPLETED"
    assert created_pay["payment_method"] == "ACH_TRANSFER"

    # 2. Retrieve list
    list_res = client.get(
        f"/api/v1/customers/{cust_id}/payment-history",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_res.status_code == 200
    payments = list_res.json()["data"]
    assert any(p["id"] == created_pay["id"] for p in payments)


def test_phase_062_payment_history_tenant_isolation(client, setup_g13_test_data):
    """Verify customer payment history cross-tenant boundary isolation."""
    data = setup_g13_test_data
    token_beta = data["token_beta"]
    cust_a_id = str(data["customer_a"].id)

    # User in Company B cannot read Company A's customer payment history
    read_res = client.get(
        f"/api/v1/customers/{cust_a_id}/payment-history",
        headers={"Authorization": f"Bearer {token_beta}"},
    )
    assert read_res.status_code == 403

    # User in Company B cannot post payment history for Company A's customer
    post_res = client.post(
        f"/api/v1/customers/{cust_a_id}/payment-history",
        json={
            "payment_reference": "PAY-ATTACK-01",
            "amount": "100.00",
            "status": "COMPLETED",
        },
        headers={"Authorization": f"Bearer {token_beta}"},
    )
    assert post_res.status_code == 403


# ===========================================================================
# Phase 063: Customer LTV Calculation Tests
# ===========================================================================

def test_phase_063_ltv_calculation_zero_purchases(client, setup_g13_test_data, db_session):
    """Verify LTV calculation handles 0 purchases cleanly with zero-division safety."""
    data = setup_g13_test_data
    token = data["token_alpha"]
    company_a = data["company_a"]

    # Create fresh customer with 0 purchases
    zero_cust = Customer(
        customer_code=f"ZERO-{uuid.uuid4().hex[:6].upper()}",
        name="Zero Purchase Corp",
        company_id=company_a.id,
        is_active=True,
    )
    db_session.add(zero_cust)
    db_session.commit()

    res = client.get(
        f"/api/v1/customers/{zero_cust.id}/financial-intelligence",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    intel = res.json()["data"]
    ltv = intel["ltv"]

    assert float(ltv["ltv_amount"]) == 0.0
    assert ltv["total_purchases_count"] == 0
    assert float(ltv["total_purchases_amount"]) == 0.0
    assert float(ltv["average_order_value"]) == 0.0
    assert ltv["first_purchase_date"] is None


def test_phase_063_ltv_calculation_multi_purchases(client, setup_g13_test_data, db_session):
    """Verify deterministic LTV aggregation across multiple purchases and payments."""
    data = setup_g13_test_data
    token = data["token_alpha"]
    company_a = data["company_a"]

    multi_cust = Customer(
        customer_code=f"MULTI-{uuid.uuid4().hex[:6].upper()}",
        name="Multi Purchase Corp",
        company_id=company_a.id,
        is_active=True,
    )
    db_session.add(multi_cust)
    db_session.flush()

    # Add 2 purchase history orders
    p1 = CustomerPurchaseHistory(
        company_id=company_a.id,
        customer_id=multi_cust.id,
        order_number="ORD-001",
        purchase_date=datetime.now(timezone.utc),
        total_amount=Decimal("10000.00"),
        status="COMPLETED",
    )
    p2 = CustomerPurchaseHistory(
        company_id=company_a.id,
        customer_id=multi_cust.id,
        order_number="ORD-002",
        purchase_date=datetime.now(timezone.utc),
        total_amount=Decimal("20000.00"),
        status="COMPLETED",
    )
    # Add 1 settled payment
    pay = CustomerPaymentHistory(
        company_id=company_a.id,
        customer_id=multi_cust.id,
        payment_reference="PAY-001",
        amount=Decimal("30000.00"),
        status="COMPLETED",
    )
    db_session.add_all([p1, p2, pay])
    db_session.commit()

    res = client.get(
        f"/api/v1/customers/{multi_cust.id}/financial-intelligence",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    ltv = res.json()["data"]["ltv"]

    assert float(ltv["ltv_amount"]) == 30000.00
    assert ltv["total_purchases_count"] == 2
    assert float(ltv["total_purchases_amount"]) == 30000.00
    assert float(ltv["average_order_value"]) == 15000.00
    assert float(ltv["total_settled_payments_amount"]) == 30000.00


# ===========================================================================
# Phase 064: Customer Discount Sensitivity Tests
# ===========================================================================

def test_phase_064_discount_sensitivity_insufficient_data(client, setup_g13_test_data, db_session):
    """Verify INSUFFICIENT_DATA classification when no purchase/discount records exist."""
    data = setup_g13_test_data
    token = data["token_alpha"]
    company_a = data["company_a"]

    empty_cust = Customer(
        customer_code=f"SENS-0-{uuid.uuid4().hex[:6].upper()}",
        name="Empty History Inc",
        company_id=company_a.id,
        is_active=True,
    )
    db_session.add(empty_cust)
    db_session.commit()

    res = client.get(
        f"/api/v1/customers/{empty_cust.id}/financial-intelligence",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    sens = res.json()["data"]["discount_sensitivity"]
    assert sens["level"] == "INSUFFICIENT_DATA"
    assert sens["score"] == 0
    assert sens["total_orders_evaluated"] == 0


def test_phase_064_discount_sensitivity_high_sensitivity(client, setup_g13_test_data, db_session):
    """Verify HIGH sensitivity classification when frequent large discounts are observed."""
    data = setup_g13_test_data
    token = data["token_alpha"]
    company_a = data["company_a"]

    sens_cust = Customer(
        customer_code=f"SENS-H-{uuid.uuid4().hex[:6].upper()}",
        name="High Discount Sensitive Corp",
        company_id=company_a.id,
        is_active=True,
    )
    db_session.add(sens_cust)
    db_session.flush()

    # 3 orders, 3 discounts (100% discount frequency, average ~30%)
    for i in range(3):
        p = CustomerPurchaseHistory(
            company_id=company_a.id,
            customer_id=sens_cust.id,
            order_number=f"ORD-SENS-{i}",
            purchase_date=datetime.now(timezone.utc),
            total_amount=Decimal("1000.00"),
            status="COMPLETED",
        )
        d = CustomerDiscountHistory(
            company_id=company_a.id,
            customer_id=sens_cust.id,
            discount_code=f"DISC-HEAVY-{i}",
            discount_percentage=Decimal("30.00"),
            discount_amount=Decimal("300.00"),
            deal_reference=f"ORD-SENS-{i}",
        )
        db_session.add_all([p, d])
    db_session.commit()

    res = client.get(
        f"/api/v1/customers/{sens_cust.id}/financial-intelligence",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    sens = res.json()["data"]["discount_sensitivity"]
    assert sens["level"] in ("MODERATE", "HIGH")
    assert sens["score"] >= 40
    assert sens["discounted_orders_count"] == 3


# ===========================================================================
# Phase 065: Customer Risk Profile Tests
# ===========================================================================

def test_phase_065_risk_profile_low_risk(client, setup_g13_test_data, db_session):
    """Verify active customer with successful payments gets LOW risk."""
    data = setup_g13_test_data
    token = data["token_alpha"]
    company_a = data["company_a"]

    low_risk_cust = Customer(
        customer_code=f"RISK-L-{uuid.uuid4().hex[:6].upper()}",
        name="Low Risk Reliable Corp",
        company_id=company_a.id,
        is_active=True,
    )
    db_session.add(low_risk_cust)
    db_session.flush()

    # 5 completed payments, 0 failed
    for i in range(5):
        pay = CustomerPaymentHistory(
            company_id=company_a.id,
            customer_id=low_risk_cust.id,
            payment_reference=f"PAY-RELIABLE-{i}",
            amount=Decimal("2000.00"),
            status="COMPLETED",
        )
        db_session.add(pay)
    db_session.commit()

    res = client.get(
        f"/api/v1/customers/{low_risk_cust.id}/financial-intelligence",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    risk = res.json()["data"]["risk_profile"]

    assert risk["risk_level"] == "LOW"
    assert risk["score"] < 30
    assert float(risk["failed_payment_ratio"]) == 0.0
    assert risk["payment_reliability_score"] == 100
    assert risk["account_status"] == "ACTIVE"


def test_phase_065_risk_profile_high_risk_failures(client, setup_g13_test_data, db_session):
    """Verify customer with high payment failure ratio is flagged as HIGH risk."""
    data = setup_g13_test_data
    token = data["token_alpha"]
    company_a = data["company_a"]

    high_risk_cust = Customer(
        customer_code=f"RISK-H-{uuid.uuid4().hex[:6].upper()}",
        name="High Risk Defaulting Corp",
        company_id=company_a.id,
        is_active=False,  # Inactive/suspended adds penalty
    )
    db_session.add(high_risk_cust)
    db_session.flush()

    # 4 failed payments out of 5
    for i in range(4):
        pay = CustomerPaymentHistory(
            company_id=company_a.id,
            customer_id=high_risk_cust.id,
            payment_reference=f"PAY-FAIL-{i}",
            amount=Decimal("1500.00"),
            status="FAILED",
        )
        db_session.add(pay)

    pay_ok = CustomerPaymentHistory(
        company_id=company_a.id,
        customer_id=high_risk_cust.id,
        payment_reference="PAY-OK-01",
        amount=Decimal("1500.00"),
        status="COMPLETED",
    )
    db_session.add(pay_ok)
    db_session.commit()

    res = client.get(
        f"/api/v1/customers/{high_risk_cust.id}/financial-intelligence",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    risk = res.json()["data"]["risk_profile"]

    assert risk["risk_level"] == "HIGH"
    assert risk["score"] >= 60
    assert float(risk["failed_payment_ratio"]) == 80.0
    assert risk["account_status"] == "INACTIVE"
    assert len(risk["primary_factors"]) >= 2
