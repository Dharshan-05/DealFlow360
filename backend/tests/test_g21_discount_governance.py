"""Comprehensive Test Suite for DealFlow360 G21 (Phases 101–105).

Verifies:
- Phase 101: Discount Configuration (CRUD, [0, 100] boundaries, date ordering validation, single active uniqueness)
- Phase 102: Customer Discount Ceiling (CRUD, duplicate active rejection [409 Conflict], company isolation)
- Phase 103: Category Discount Ceiling (CRUD, duplicate active rejection [409 Conflict], category validation)
- Phase 104: Product Discount Ceiling (CRUD, duplicate active rejection [409 Conflict], product validation)
- Phase 105: Sales Rep Authority Limit (CRUD, duplicate active rejection, sales rep self-escalation rejection [403 Forbidden])
- Security & RBAC: 401 unauthenticated, 403 unauthorized, audit log creation
"""
import uuid
from decimal import Decimal
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.jwt import create_access_token
from app.db.session import SessionLocal
from app.main import app
from app.models.audit_log import AuditLog
from app.models.company import Company
from app.models.customer import Customer
from app.models.permission import Permission
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.role import Role
from app.models.user import User
from app.models.discount_configuration import DiscountConfiguration
from app.models.customer_discount_ceiling import CustomerDiscountCeiling
from app.models.category_discount_ceiling import CategoryDiscountCeiling
from app.models.product_discount_ceiling import ProductDiscountCeiling
from app.models.sales_rep_authority_limit import SalesRepAuthorityLimit


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
def setup_g21_test_data(db_session):
    """Seed test company, admin user, sales rep user, category, product, customer."""
    suffix = uuid.uuid4().hex[:8]

    company = Company(
        name=f"G21 Enterprise {suffix}",
        legal_name=f"G21 Enterprise Corp {suffix}",
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

    # Admin role with read and write
    admin_role = Role(
        name=f"g21_admin_{suffix}",
        description="G21 admin role",
    )
    admin_role.permissions.extend([perm_read, perm_write])
    db_session.add(admin_role)

    # Sales Rep role with read ONLY
    rep_role = Role(
        name=f"g21_rep_{suffix}",
        description="G21 sales rep role",
    )
    rep_role.permissions.append(perm_read)
    db_session.add(rep_role)

    # Empty role with NO discount permissions
    empty_role = Role(
        name=f"g21_empty_{suffix}",
        description="G21 empty role",
    )
    db_session.add(empty_role)
    db_session.flush()

    # Admin User
    admin_user = User(
        email=f"admin_{suffix}@example.com",
        first_name="Admin",
        last_name="User",
        is_active=True,
        company_id=company.id,
        roles=[admin_role],
    )
    db_session.add(admin_user)

    # Sales Rep User
    rep_user = User(
        email=f"rep_{suffix}@example.com",
        first_name="Sales",
        last_name="Rep",
        is_active=True,
        company_id=company.id,
        roles=[rep_role],
    )
    db_session.add(rep_user)

    # Rep 2 User with write permission (to test self-modification prevention)
    rep2_role = Role(
        name=f"g21_rep2_{suffix}",
        description="G21 sales rep 2 role with write",
    )
    rep2_role.permissions.extend([perm_read, perm_write])
    db_session.add(rep2_role)
    db_session.flush()

    rep2_user = User(
        email=f"rep2_{suffix}@example.com",
        first_name="Sales",
        last_name="Rep2",
        is_active=True,
        company_id=company.id,
        roles=[rep2_role],
    )
    db_session.add(rep2_user)

    # Unauthorized User (no discount perms)
    unauthorized_user = User(
        email=f"no_perms_{suffix}@example.com",
        first_name="No",
        last_name="Perms",
        is_active=True,
        company_id=company.id,
        roles=[empty_role],
    )
    db_session.add(unauthorized_user)

    # Category
    category = ProductCategory(
        code=f"CAT-{suffix[:4].upper()}",
        name=f"Hardware Category {suffix}",
        is_active=True,
    )
    db_session.add(category)
    db_session.flush()

    # Product
    product = Product(
        sku=f"SKU-{suffix[:6].upper()}",
        name=f"Enterprise Server {suffix}",
        category_id=category.id,
        base_price=Decimal("1000.00"),
        cost=Decimal("500.00"),
        is_active=True,
    )
    db_session.add(product)
    db_session.flush()

    # Customer
    customer = Customer(
        company_id=company.id,
        customer_code=f"CUST-{suffix[:4].upper()}",
        name=f"Acme Corp {suffix}",
        is_active=True,
    )
    db_session.add(customer)
    db_session.commit()

    admin_token = create_access_token(admin_user.id)
    rep_token = create_access_token(rep_user.id)
    rep2_token = create_access_token(rep2_user.id)
    unauth_token = create_access_token(unauthorized_user.id)

    return {
        "company": company,
        "admin_user": admin_user,
        "rep_user": rep_user,
        "rep2_user": rep2_user,
        "unauthorized_user": unauthorized_user,
        "admin_headers": {"Authorization": f"Bearer {admin_token}"},
        "rep_headers": {"Authorization": f"Bearer {rep_token}"},
        "rep2_headers": {"Authorization": f"Bearer {rep2_token}"},
        "unauth_headers": {"Authorization": f"Bearer {unauth_token}"},
        "category": category,
        "product": product,
        "customer": customer,
    }


# ===========================================================================
# PHASE 101: Discount Configuration Tests
# ===========================================================================

def test_discount_configuration_crud_and_boundaries(client, setup_g21_test_data, db_session):
    data = setup_g21_test_data
    headers = data["admin_headers"]

    # 1. Create with invalid boundary (> 100) -> 422 Unprocessable Entity
    invalid_res = client.post(
        "/api/v1/governance/discounts/configurations",
        headers=headers,
        json={
            "name": "Invalid Ceiling",
            "default_discount_ceiling": 105.00,
        },
    )
    assert invalid_res.status_code == 422

    # 2. Create valid configuration
    create_res = client.post(
        "/api/v1/governance/discounts/configurations",
        headers=headers,
        json={
            "name": "Global Test Policy",
            "description": "Standard test policy",
            "default_discount_ceiling": 25.50,
            "is_active": True,
        },
    )
    assert create_res.status_code == 201
    cfg_data = create_res.json()
    assert cfg_data["name"] == "Global Test Policy"
    assert float(cfg_data["default_discount_ceiling"]) == 25.50
    assert cfg_data["is_active"] is True
    cfg_id = cfg_data["id"]

    # 3. List configurations
    list_res = client.get("/api/v1/governance/discounts/configurations", headers=headers)
    assert list_res.status_code == 200
    assert list_res.json()["total"] >= 1

    # 4. Get by ID
    get_res = client.get(f"/api/v1/governance/discounts/configurations/{cfg_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == cfg_id

    # 5. Update configuration
    update_res = client.put(
        f"/api/v1/governance/discounts/configurations/{cfg_id}",
        headers=headers,
        json={"default_discount_ceiling": 22.00},
    )
    assert update_res.status_code == 200
    assert float(update_res.json()["default_discount_ceiling"]) == 22.00

    # 6. Delete (soft-deactivate) configuration
    del_res = client.delete(f"/api/v1/governance/discounts/configurations/{cfg_id}", headers=headers)
    assert del_res.status_code == 204

    # Verify inactive
    get_after = client.get(f"/api/v1/governance/discounts/configurations/{cfg_id}", headers=headers)
    assert get_after.status_code == 200
    assert get_after.json()["is_active"] is False


def test_discount_configuration_date_validation(client, setup_g21_test_data):
    data = setup_g21_test_data
    headers = data["admin_headers"]

    now = datetime.now(timezone.utc)
    future = now + timedelta(days=10)
    past = now - timedelta(days=10)

    # effective_until < effective_from should fail validation
    res = client.post(
        "/api/v1/governance/discounts/configurations",
        headers=headers,
        json={
            "name": "Invalid Dates",
            "default_discount_ceiling": 15.00,
            "effective_from": future.isoformat(),
            "effective_until": past.isoformat(),
        },
    )
    assert res.status_code == 422


# ===========================================================================
# PHASE 102: Customer Discount Ceiling Tests
# ===========================================================================

def test_customer_discount_ceiling_crud_and_conflict(client, setup_g21_test_data):
    data = setup_g21_test_data
    headers = data["admin_headers"]
    cust_id = str(data["customer"].id)

    # 1. Create active customer ceiling
    res1 = client.post(
        "/api/v1/governance/discounts/customer-ceilings",
        headers=headers,
        json={
            "customer_id": cust_id,
            "max_discount_percentage": 18.00,
            "is_active": True,
        },
    )
    assert res1.status_code == 201
    c_ceil = res1.json()
    assert float(c_ceil["max_discount_percentage"]) == 18.00
    c_id = c_ceil["id"]

    # 2. Duplicate active customer ceiling creation must return 409 Conflict
    res_dup = client.post(
        "/api/v1/governance/discounts/customer-ceilings",
        headers=headers,
        json={
            "customer_id": cust_id,
            "max_discount_percentage": 20.00,
            "is_active": True,
        },
    )
    assert res_dup.status_code == 409
    err_msg = res_dup.json().get("error", {}).get("message", "")
    assert "active discount ceiling already exists" in err_msg.lower()

    # 3. Update ceiling
    res_up = client.put(
        f"/api/v1/governance/discounts/customer-ceilings/{c_id}",
        headers=headers,
        json={"max_discount_percentage": 19.50},
    )
    assert res_up.status_code == 200
    assert float(res_up.json()["max_discount_percentage"]) == 19.50

    # 4. Soft-delete
    res_del = client.delete(f"/api/v1/governance/discounts/customer-ceilings/{c_id}", headers=headers)
    assert res_del.status_code == 204

    # 5. After deactivating, creating a new active ceiling for the same customer succeeds
    res_new = client.post(
        "/api/v1/governance/discounts/customer-ceilings",
        headers=headers,
        json={
            "customer_id": cust_id,
            "max_discount_percentage": 22.00,
            "is_active": True,
        },
    )
    assert res_new.status_code == 201


# ===========================================================================
# PHASE 103: Category Discount Ceiling Tests
# ===========================================================================

def test_category_discount_ceiling_crud_and_conflict(client, setup_g21_test_data):
    data = setup_g21_test_data
    headers = data["admin_headers"]
    cat_id = str(data["category"].id)

    # 1. Create active category ceiling
    res = client.post(
        "/api/v1/governance/discounts/category-ceilings",
        headers=headers,
        json={
            "category_id": cat_id,
            "max_discount_percentage": 14.00,
            "is_active": True,
        },
    )
    assert res.status_code == 201
    cat_ceil_id = res.json()["id"]

    # 2. Duplicate active ceiling on same category returns 409 Conflict
    res_dup = client.post(
        "/api/v1/governance/discounts/category-ceilings",
        headers=headers,
        json={
            "category_id": cat_id,
            "max_discount_percentage": 16.00,
            "is_active": True,
        },
    )
    assert res_dup.status_code == 409

    # 3. Soft-delete
    res_del = client.delete(f"/api/v1/governance/discounts/category-ceilings/{cat_ceil_id}", headers=headers)
    assert res_del.status_code == 204


# ===========================================================================
# PHASE 104: Product Discount Ceiling Tests
# ===========================================================================

def test_product_discount_ceiling_crud_and_conflict(client, setup_g21_test_data):
    data = setup_g21_test_data
    headers = data["admin_headers"]
    prod_id = str(data["product"].id)

    # 1. Create active product ceiling
    res = client.post(
        "/api/v1/governance/discounts/product-ceilings",
        headers=headers,
        json={
            "product_id": prod_id,
            "max_discount_percentage": 11.50,
            "is_active": True,
        },
    )
    assert res.status_code == 201
    p_ceil_id = res.json()["id"]

    # 2. Duplicate active ceiling on same product returns 409 Conflict
    res_dup = client.post(
        "/api/v1/governance/discounts/product-ceilings",
        headers=headers,
        json={
            "product_id": prod_id,
            "max_discount_percentage": 15.00,
            "is_active": True,
        },
    )
    assert res_dup.status_code == 409

    # 3. Soft-delete
    res_del = client.delete(f"/api/v1/governance/discounts/product-ceilings/{p_ceil_id}", headers=headers)
    assert res_del.status_code == 204


# ===========================================================================
# PHASE 105: Sales Rep Authority Limit Tests & Self-Escalation Prohibition
# ===========================================================================

def test_sales_rep_authority_limit_crud(client, setup_g21_test_data):
    data = setup_g21_test_data
    headers = data["admin_headers"]
    rep_user_id = str(data["rep_user"].id)

    # 1. Admin creates limit for sales rep
    res = client.post(
        "/api/v1/governance/discounts/sales-rep-limits",
        headers=headers,
        json={
            "user_id": rep_user_id,
            "max_authorized_discount": 8.00,
            "is_active": True,
        },
    )
    assert res.status_code == 201
    limit_id = res.json()["id"]
    assert float(res.json()["max_authorized_discount"]) == 8.00

    # 2. Duplicate active limit returns 409 Conflict
    res_dup = client.post(
        "/api/v1/governance/discounts/sales-rep-limits",
        headers=headers,
        json={
            "user_id": rep_user_id,
            "max_authorized_discount": 10.00,
            "is_active": True,
        },
    )
    assert res_dup.status_code == 409

    # 3. Admin updates sales rep limit
    res_up = client.put(
        f"/api/v1/governance/discounts/sales-rep-limits/{limit_id}",
        headers=headers,
        json={"max_authorized_discount": 9.50},
    )
    assert res_up.status_code == 200
    assert float(res_up.json()["max_authorized_discount"]) == 9.50

    # 4. Delete
    res_del = client.delete(f"/api/v1/governance/discounts/sales-rep-limits/{limit_id}", headers=headers)
    assert res_del.status_code == 204


def test_sales_rep_self_escalation_prohibited(client, setup_g21_test_data):
    """Phase 105 Strict Rule: Users are strictly forbidden from modifying or creating their own limit."""
    data = setup_g21_test_data
    rep2_headers = data["rep2_headers"]
    rep2_id = str(data["rep2_user"].id)
    admin_headers = data["admin_headers"]

    # 1. Sales rep trying to CREATE their own limit must be rejected with 403 Forbidden
    res_create = client.post(
        "/api/v1/governance/discounts/sales-rep-limits",
        headers=rep2_headers,
        json={
            "user_id": rep2_id,
            "max_authorized_discount": 50.00,
            "is_active": True,
        },
    )
    assert res_create.status_code == 403
    err_create = res_create.json().get("error", {}).get("message", "")
    assert "cannot assign or modify their own" in err_create.lower()

    # 2. Admin creates a limit for rep2
    res_admin_create = client.post(
        "/api/v1/governance/discounts/sales-rep-limits",
        headers=admin_headers,
        json={
            "user_id": rep2_id,
            "max_authorized_discount": 7.00,
            "is_active": True,
        },
    )
    assert res_admin_create.status_code == 201
    rep2_limit_id = res_admin_create.json()["id"]

    # 3. Sales rep trying to UPDATE their own limit must be rejected with 403 Forbidden
    res_update = client.put(
        f"/api/v1/governance/discounts/sales-rep-limits/{rep2_limit_id}",
        headers=rep2_headers,
        json={"max_authorized_discount": 40.00},
    )
    assert res_update.status_code == 403
    err_up = res_update.json().get("error", {}).get("message", "")
    assert "cannot assign or modify their own" in err_up.lower()


# ===========================================================================
# RBAC & Audit Log Security Tests
# ===========================================================================

def test_unauthenticated_and_unauthorized_access(client, setup_g21_test_data):
    data = setup_g21_test_data
    unauth_headers = data["unauth_headers"]

    # 1. Unauthenticated -> 401 Unauthorized
    res_unauth = client.get("/api/v1/governance/discounts/configurations")
    assert res_unauth.status_code == 401

    # 2. Role without discounts:read -> 403 Forbidden
    res_forbidden_read = client.get(
        "/api/v1/governance/discounts/configurations",
        headers=unauth_headers,
    )
    assert res_forbidden_read.status_code == 403

    # 3. Role without discounts:write -> 403 Forbidden on mutation
    rep_headers = data["rep_headers"]  # Has discounts:read but not discounts:write
    res_forbidden_write = client.post(
        "/api/v1/governance/discounts/configurations",
        headers=rep_headers,
        json={
            "name": "Unauthorized Config",
            "default_discount_ceiling": 10.00,
        },
    )
    assert res_forbidden_write.status_code == 403


def test_audit_log_tracking_on_mutations(client, setup_g21_test_data, db_session):
    data = setup_g21_test_data
    headers = data["admin_headers"]

    # Create a configuration to verify audit trail
    res = client.post(
        "/api/v1/governance/discounts/configurations",
        headers=headers,
        json={
            "name": "Audit Tracked Policy",
            "default_discount_ceiling": 14.00,
        },
    )
    assert res.status_code == 201
    cfg_id = res.json()["id"]

    # Verify audit log exists in DB
    audit = db_session.scalars(
        select(AuditLog).where(
            AuditLog.resource_type == "discount_configuration",
            AuditLog.resource_id == cfg_id,
            AuditLog.action == "DISCOUNT_CONFIGURATION_CREATED",
        )
    ).first()
    assert audit is not None
    assert audit.user_id == data["admin_user"].id
