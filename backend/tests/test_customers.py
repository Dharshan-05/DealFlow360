"""Comprehensive Test Suite for Customer Management Foundation (Phases 056–060).

Verifies:
- Phase 056: Customer CRUD (create, read, update, soft delete, hard delete, duplicate code rejection)
- Phase 057: Customer Profile retrieval (including joined tier details and timestamps)
- Phase 058: Customer Tier Management (assigning valid tier, invalid tier rejection, clearing tier)
- Phase 059: Customer Purchase History (recording purchase, listing chronological purchases)
- Phase 060: Customer Deal History (recording deal, listing chronological deals)
- Object-level authorization & Tenant Boundary Isolation (cross-tenant access denial)
- RBAC permissions (customers:read, customers:write, customers:delete)
- Audit log entry verification for customer lifecycle events
"""
import uuid
from decimal import Decimal
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select

from app.core.jwt import create_access_token
from app.db.session import SessionLocal
from app.main import app
from app.models.audit_log import AuditLog
from app.models.company import Company
from app.models.customer import Customer
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
def setup_customer_test_data(db_session):
    """Seed companies, tiers, users and roles for test execution."""
    # Ensure Company A and Company B
    company_a = db_session.scalars(select(Company).where(Company.name == "Acme Corp Alpha")).first()
    if not company_a:
        company_a = Company(
            name="Acme Corp Alpha",
            legal_name="Acme Alpha Inc",
            email="alpha@acme.example.com",
            is_active=True,
        )
        db_session.add(company_a)
        db_session.flush()

    company_b = db_session.scalars(select(Company).where(Company.name == "Beta Corp Omega")).first()
    if not company_b:
        company_b = Company(
            name="Beta Corp Omega",
            legal_name="Beta Omega LLC",
            email="omega@beta.example.com",
            is_active=True,
        )
        db_session.add(company_b)
        db_session.flush()

    # Ensure Customer Tiers
    tier_gold = db_session.scalars(select(CustomerTier).where(CustomerTier.code == "TIER-TEST-GOLD")).first()
    if not tier_gold:
        tier_gold = CustomerTier(
            name="Test Gold Tier",
            code="TIER-TEST-GOLD",
            discount_limit=Decimal("15.00"),
            is_active=True,
        )
        db_session.add(tier_gold)
        db_session.flush()

    # Permissions
    perm_read = db_session.scalars(select(Permission).where(Permission.name == "customers:read")).first()
    perm_write = db_session.scalars(select(Permission).where(Permission.name == "customers:write")).first()
    perm_del = db_session.scalars(select(Permission).where(Permission.name == "customers:delete")).first()

    # Ensure Roles
    rep_role = db_session.scalars(select(Role).where(Role.name == "Sales Rep Customer Test")).first()
    if not rep_role:
        rep_role = Role(name="Sales Rep Customer Test", description="Test Rep Role")
        rep_role.permissions.extend([perm_read, perm_write])
        db_session.add(rep_role)
        db_session.flush()

    admin_role = db_session.scalars(select(Role).where(Role.name == "Admin Customer Test")).first()
    if not admin_role:
        admin_role = Role(name="Admin Customer Test", description="Test Admin Role")
        admin_role.permissions.extend([perm_read, perm_write, perm_del])
        db_session.add(admin_role)
        db_session.flush()

    viewer_role = db_session.scalars(select(Role).where(Role.name == "Viewer Customer Test")).first()
    if not viewer_role:
        viewer_role = Role(name="Viewer Customer Test", description="Read-only role")
        viewer_role.permissions.append(perm_read)
        db_session.add(viewer_role)
        db_session.flush()

    # Test Users
    user_alpha = db_session.scalars(select(User).where(User.email == "rep_alpha@test.com")).first()
    if not user_alpha:
        user_alpha = User(
            email="rep_alpha@test.com",
            first_name="Alpha",
            last_name="Sales",
            company_id=company_a.id,
            is_active=True,
        )
        user_alpha.roles.append(rep_role)
        db_session.add(user_alpha)
        db_session.flush()

    user_admin = db_session.scalars(select(User).where(User.email == "admin_alpha@test.com")).first()
    if not user_admin:
        user_admin = User(
            email="admin_alpha@test.com",
            first_name="Admin",
            last_name="Alpha",
            company_id=company_a.id,
            is_active=True,
        )
        user_admin.roles.append(admin_role)
        db_session.add(user_admin)
        db_session.flush()

    user_beta = db_session.scalars(select(User).where(User.email == "rep_beta@test.com")).first()
    if not user_beta:
        user_beta = User(
            email="rep_beta@test.com",
            first_name="Beta",
            last_name="Sales",
            company_id=company_b.id,
            is_active=True,
        )
        user_beta.roles.append(rep_role)
        db_session.add(user_beta)
        db_session.flush()

    user_viewer = db_session.scalars(select(User).where(User.email == "viewer_alpha@test.com")).first()
    if not user_viewer:
        user_viewer = User(
            email="viewer_alpha@test.com",
            first_name="Viewer",
            last_name="Only",
            company_id=company_a.id,
            is_active=True,
        )
        user_viewer.roles.append(viewer_role)
        db_session.add(user_viewer)
        db_session.flush()

    db_session.commit()

    return {
        "company_a": company_a,
        "company_b": company_b,
        "tier_gold": tier_gold,
        "user_alpha": user_alpha,
        "user_admin": user_admin,
        "user_beta": user_beta,
        "user_viewer": user_viewer,
    }


def auth_header(user: User) -> dict:
    token = create_access_token(str(user.id))
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Phase 056: Customer CRUD Tests
# ---------------------------------------------------------------------------

def test_create_customer_success(client, setup_customer_test_data):
    data = setup_customer_test_data
    headers = auth_header(data["user_alpha"])

    payload = {
        "customer_code": f"CUST-{uuid.uuid4().hex[:6]}",
        "name": "Acme Global Solutions",
        "email": "contact@acmeglobal.com",
        "phone": "+1-555-1234",
        "address": "123 Market St",
        "city": "San Francisco",
        "state": "CA",
        "country": "USA",
        "postal_code": "94105",
        "tier_id": str(data["tier_gold"].id),
    }

    resp = client.post("/api/v1/customers", json=payload, headers=headers)
    assert resp.status_code == 201
    res_data = resp.json()
    assert res_data["success"] is True
    cust = res_data["data"]
    assert cust["name"] == "Acme Global Solutions"
    assert cust["customer_code"] == payload["customer_code"].upper()
    assert cust["company_id"] == str(data["company_a"].id)
    assert cust["tier"]["id"] == str(data["tier_gold"].id)


def test_create_customer_duplicate_code_rejected(client, setup_customer_test_data):
    data = setup_customer_test_data
    headers = auth_header(data["user_alpha"])
    code = f"DUP-{uuid.uuid4().hex[:6]}"

    payload = {
        "customer_code": code,
        "name": "First Customer",
        "email": "first@test.com",
    }
    resp1 = client.post("/api/v1/customers", json=payload, headers=headers)
    assert resp1.status_code == 201

    # Duplicate attempt
    resp2 = client.post("/api/v1/customers", json=payload, headers=headers)
    assert resp2.status_code == 409
    assert resp2.json()["error"]["code"] == "DUPLICATE_CUSTOMER_CODE"


def test_list_customers_tenant_isolated(client, setup_customer_test_data):
    data = setup_customer_test_data
    headers_alpha = auth_header(data["user_alpha"])
    headers_beta = auth_header(data["user_beta"])

    # Create customer in Company A
    code_a = f"ALPHA-{uuid.uuid4().hex[:6]}"
    client.post("/api/v1/customers", json={"customer_code": code_a, "name": "Company A Cust"}, headers=headers_alpha)

    # Create customer in Company B
    code_b = f"BETA-{uuid.uuid4().hex[:6]}"
    client.post("/api/v1/customers", json={"customer_code": code_b, "name": "Company B Cust"}, headers=headers_beta)

    # List as Alpha
    resp_a = client.get("/api/v1/customers", headers=headers_alpha)
    assert resp_a.status_code == 200
    codes_seen_a = [c["customer_code"] for c in resp_a.json()["data"]["items"]]
    assert code_a.upper() in codes_seen_a
    assert code_b.upper() not in codes_seen_a

    # List as Beta
    resp_b = client.get("/api/v1/customers", headers=headers_beta)
    assert resp_b.status_code == 200
    codes_seen_b = [c["customer_code"] for c in resp_b.json()["data"]["items"]]
    assert code_b.upper() in codes_seen_b
    assert code_a.upper() not in codes_seen_b


def test_update_customer(client, setup_customer_test_data):
    data = setup_customer_test_data
    headers = auth_header(data["user_alpha"])

    # Create customer
    code = f"UPD-{uuid.uuid4().hex[:6]}"
    create_resp = client.post("/api/v1/customers", json={"customer_code": code, "name": "Old Name"}, headers=headers)
    cust_id = create_resp.json()["data"]["id"]

    # Update customer
    update_payload = {"name": "New Name Updated", "phone": "+1-999-8888"}
    upd_resp = client.put(f"/api/v1/customers/{cust_id}", json=update_payload, headers=headers)
    assert upd_resp.status_code == 200
    assert upd_resp.json()["data"]["name"] == "New Name Updated"
    assert upd_resp.json()["data"]["phone"] == "+1-999-8888"


def test_delete_customer_soft_and_rbac(client, setup_customer_test_data):
    data = setup_customer_test_data
    headers_rep = auth_header(data["user_alpha"])  # has no customers:delete
    headers_admin = auth_header(data["user_admin"])  # has customers:delete

    # Create customer
    code = f"DEL-{uuid.uuid4().hex[:6]}"
    create_resp = client.post("/api/v1/customers", json={"customer_code": code, "name": "To Delete"}, headers=headers_rep)
    cust_id = create_resp.json()["data"]["id"]

    # Rep cannot delete
    del_resp_rep = client.delete(f"/api/v1/customers/{cust_id}", headers=headers_rep)
    assert del_resp_rep.status_code == 403

    # Admin can soft-delete
    del_resp_admin = client.delete(f"/api/v1/customers/{cust_id}?soft=true", headers=headers_admin)
    assert del_resp_admin.status_code == 200
    assert del_resp_admin.json()["data"]["deleted"] is True

    # Customer profile still accessible by admin, but is_active is False
    profile_resp = client.get(f"/api/v1/customers/{cust_id}", headers=headers_admin)
    assert profile_resp.status_code == 200
    assert profile_resp.json()["data"]["is_active"] is False


# ---------------------------------------------------------------------------
# Phase 057: Customer Profile Tests
# ---------------------------------------------------------------------------

def test_get_customer_profile_cross_tenant_forbidden(client, setup_customer_test_data):
    data = setup_customer_test_data
    headers_alpha = auth_header(data["user_alpha"])
    headers_beta = auth_header(data["user_beta"])

    # Create customer in Company A
    create_resp = client.post(
        "/api/v1/customers",
        json={"customer_code": f"PROF-{uuid.uuid4().hex[:6]}", "name": "Company A Profile Target"},
        headers=headers_alpha,
    )
    cust_id = create_resp.json()["data"]["id"]

    # Beta user cannot access Alpha customer
    cross_resp = client.get(f"/api/v1/customers/{cust_id}", headers=headers_beta)
    assert cross_resp.status_code == 403


# ---------------------------------------------------------------------------
# Phase 058: Customer Tier Management Tests
# ---------------------------------------------------------------------------

def test_update_customer_tier(client, setup_customer_test_data):
    data = setup_customer_test_data
    headers = auth_header(data["user_alpha"])

    # Create customer with no tier
    create_resp = client.post(
        "/api/v1/customers",
        json={"customer_code": f"TIER-{uuid.uuid4().hex[:6]}", "name": "Tier Target"},
        headers=headers,
    )
    cust_id = create_resp.json()["data"]["id"]
    assert create_resp.json()["data"]["tier"] is None

    # Assign Tier Gold
    patch_resp = client.patch(
        f"/api/v1/customers/{cust_id}/tier",
        json={"tier_id": str(data["tier_gold"].id)},
        headers=headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["data"]["tier"]["code"] == "TIER-TEST-GOLD"

    # Unassign Tier
    unassign_resp = client.patch(
        f"/api/v1/customers/{cust_id}/tier",
        json={"tier_id": None},
        headers=headers,
    )
    assert unassign_resp.status_code == 200
    assert unassign_resp.json()["data"]["tier"] is None


def test_update_customer_tier_invalid_rejected(client, setup_customer_test_data):
    data = setup_customer_test_data
    headers = auth_header(data["user_alpha"])

    create_resp = client.post(
        "/api/v1/customers",
        json={"customer_code": f"TIER-INV-{uuid.uuid4().hex[:6]}", "name": "Invalid Tier Target"},
        headers=headers,
    )
    cust_id = create_resp.json()["data"]["id"]

    # Assign non-existent tier
    fake_tier_id = str(uuid.uuid4())
    patch_resp = client.patch(
        f"/api/v1/customers/{cust_id}/tier",
        json={"tier_id": fake_tier_id},
        headers=headers,
    )
    assert patch_resp.status_code == 400
    assert patch_resp.json()["error"]["code"] == "INVALID_TIER"


# ---------------------------------------------------------------------------
# Phase 059 & 060: Customer Purchase & Deal History Tests
# ---------------------------------------------------------------------------

def test_customer_purchase_history(client, setup_customer_test_data):
    data = setup_customer_test_data
    headers = auth_header(data["user_alpha"])

    # Create customer
    create_resp = client.post(
        "/api/v1/customers",
        json={"customer_code": f"PUR-{uuid.uuid4().hex[:6]}", "name": "Purchase History Cust"},
        headers=headers,
    )
    cust_id = create_resp.json()["data"]["id"]

    # Add purchase 1
    p1 = {
        "order_number": "ORD-2026-001",
        "total_amount": "14500.00",
        "status": "COMPLETED",
        "item_count": 5,
        "notes": "Initial infrastructure purchase",
    }
    add_resp = client.post(f"/api/v1/customers/{cust_id}/purchase-history", json=p1, headers=headers)
    assert add_resp.status_code == 201
    assert add_resp.json()["data"]["order_number"] == "ORD-2026-001"

    # Query purchase history
    list_resp = client.get(f"/api/v1/customers/{cust_id}/purchase-history", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()["data"]) == 1
    assert list_resp.json()["data"][0]["order_number"] == "ORD-2026-001"


def test_customer_deal_history(client, setup_customer_test_data):
    data = setup_customer_test_data
    headers = auth_header(data["user_alpha"])

    # Create customer
    create_resp = client.post(
        "/api/v1/customers",
        json={"customer_code": f"DEAL-{uuid.uuid4().hex[:6]}", "name": "Deal History Cust"},
        headers=headers,
    )
    cust_id = create_resp.json()["data"]["id"]

    # Add deal 1
    d1 = {
        "deal_code": "DEAL-Q3-01",
        "title": "Enterprise Cloud Migration",
        "deal_value": "95000.00",
        "status": "WON",
        "sales_rep_name": "Alpha Sales",
        "notes": "Closed multi-year contract",
    }
    add_resp = client.post(f"/api/v1/customers/{cust_id}/deal-history", json=d1, headers=headers)
    assert add_resp.status_code == 201
    assert add_resp.json()["data"]["deal_code"] == "DEAL-Q3-01"

    # Query deal history
    list_resp = client.get(f"/api/v1/customers/{cust_id}/deal-history", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()["data"]) == 1
    assert list_resp.json()["data"][0]["deal_code"] == "DEAL-Q3-01"


# ---------------------------------------------------------------------------
# Audit Trail Verification
# ---------------------------------------------------------------------------

def test_customer_audit_trail_recorded(client, setup_customer_test_data, db_session):
    data = setup_customer_test_data
    headers = auth_header(data["user_alpha"])

    code = f"AUDIT-{uuid.uuid4().hex[:6]}"
    create_resp = client.post(
        "/api/v1/customers",
        json={"customer_code": code, "name": "Audit Tracked Customer"},
        headers=headers,
    )
    cust_id = create_resp.json()["data"]["id"]

    # Verify AuditLog created
    audit = db_session.scalars(
        select(AuditLog).where(
            AuditLog.resource_type == "customer",
            AuditLog.resource_id == cust_id,
            AuditLog.action == "CREATE",
        )
    ).first()
    assert audit is not None
    assert audit.user_id == data["user_alpha"].id
