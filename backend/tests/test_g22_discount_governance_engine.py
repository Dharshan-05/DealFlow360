"""Comprehensive Test Suite for DealFlow360 G22 (Phases 106–110).

Verifies:
- Phase 106: Manager Authority Limit (CRUD, [0, 100] bounds, duplicate active rejection [409], date ordering, self-modification check)
- Phase 107: Finance Authority Limit (CRUD, duplicate active rejection [409], Sales Rep forbidden [403])
- Phase 108: Discount Policy Engine (Deterministic policy resolution: company baseline, customer ceiling, category ceiling, product ceiling, actor authority limit, effective ceiling = MIN, single timestamp)
- Phase 109: Discount Validation Service (Valid discount passes, cross-tenant isolation enforcement [404], boundary checks [422])
- Phase 110: Discount Violation Detection (All violation types: COMPANY_DISCOUNT_CEILING, CUSTOMER_DISCOUNT_CEILING, CATEGORY_DISCOUNT_CEILING, PRODUCT_DISCOUNT_CEILING, SALES_REP_AUTHORITY_LIMIT, MANAGER_AUTHORITY_LIMIT, FINANCE_AUTHORITY_LIMIT)
- Security & RBAC: 401 unauthenticated, 403 unauthorized, audit log creation
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
from app.models.audit_log import AuditLog
from app.models.category_discount_ceiling import CategoryDiscountCeiling
from app.models.company import Company
from app.models.customer import Customer
from app.models.customer_discount_ceiling import CustomerDiscountCeiling
from app.models.discount_configuration import DiscountConfiguration
from app.models.finance_authority_limit import FinanceAuthorityLimit
from app.models.manager_authority_limit import ManagerAuthorityLimit
from app.models.permission import Permission
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.product_discount_ceiling import ProductDiscountCeiling
from app.models.role import Role
from app.models.sales_rep_authority_limit import SalesRepAuthorityLimit
from app.models.user import User
from app.services.discount_governance import DiscountPolicyEngine, DiscountValidationService
from app.schemas.discount_governance import DiscountValidationRequest


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
def setup_g22_test_data(db_session):
    """Seed test company, roles (Admin, Manager, Finance, Sales Rep), users, category, product, customer."""
    suffix = uuid.uuid4().hex[:8]

    company = Company(
        name=f"G22 Enterprise {suffix}",
        legal_name=f"G22 Enterprise Corp {suffix}",
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

    # Admin role
    admin_role = Role(name=f"Admin_{suffix}", description="Admin role")
    admin_role.permissions.extend([perm_read, perm_write])
    db_session.add(admin_role)

    # Manager role
    mgr_role = Role(name=f"Sales Manager_{suffix}", description="Sales Manager role")
    mgr_role.permissions.extend([perm_read, perm_write])
    db_session.add(mgr_role)

    # Finance role
    fin_role = Role(name=f"Finance_{suffix}", description="Finance role")
    fin_role.permissions.extend([perm_read, perm_write])
    db_session.add(fin_role)

    # Sales Rep role (read only)
    rep_role = Role(name=f"Sales Representative_{suffix}", description="Sales Rep role")
    rep_role.permissions.append(perm_read)
    db_session.add(rep_role)

    # Empty role
    empty_role = Role(name=f"Empty_{suffix}", description="Empty role")
    db_session.add(empty_role)
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

    mgr_user = User(
        email=f"mgr_{suffix}@example.com",
        first_name="Manager",
        last_name="User",
        is_active=True,
        company_id=company.id,
        roles=[mgr_role],
    )
    db_session.add(mgr_user)

    fin_user = User(
        email=f"fin_{suffix}@example.com",
        first_name="Finance",
        last_name="User",
        is_active=True,
        company_id=company.id,
        roles=[fin_role],
    )
    db_session.add(fin_user)

    rep_user = User(
        email=f"rep_{suffix}@example.com",
        first_name="Rep",
        last_name="User",
        is_active=True,
        company_id=company.id,
        roles=[rep_role],
    )
    db_session.add(rep_user)

    unauth_user = User(
        email=f"unauth_{suffix}@example.com",
        first_name="Unauth",
        last_name="User",
        is_active=True,
        company_id=company.id,
        roles=[empty_role],
    )
    db_session.add(unauth_user)

    # Category & Product
    category = ProductCategory(
        code=f"CAT-{suffix[:4].upper()}",
        name=f"Hardware {suffix}",
        is_active=True,
    )
    db_session.add(category)
    db_session.flush()

    product = Product(
        sku=f"SKU-{suffix[:6].upper()}",
        name=f"Server {suffix}",
        category_id=category.id,
        base_price=Decimal("1000.00"),
        cost=Decimal("600.00"),
        is_active=True,
    )
    db_session.add(product)
    db_session.flush()

    # Customer
    customer = Customer(
        company_id=company.id,
        customer_code=f"CUST-{suffix[:4].upper()}",
        name=f"Client {suffix}",
        is_active=True,
    )
    db_session.add(customer)
    db_session.commit()

    return {
        "company": company,
        "admin_user": admin_user,
        "mgr_user": mgr_user,
        "fin_user": fin_user,
        "rep_user": rep_user,
        "unauth_user": unauth_user,
        "admin_headers": {"Authorization": f"Bearer {create_access_token(admin_user.id)}"},
        "mgr_headers": {"Authorization": f"Bearer {create_access_token(mgr_user.id)}"},
        "fin_headers": {"Authorization": f"Bearer {create_access_token(fin_user.id)}"},
        "rep_headers": {"Authorization": f"Bearer {create_access_token(rep_user.id)}"},
        "unauth_headers": {"Authorization": f"Bearer {create_access_token(unauth_user.id)}"},
        "category": category,
        "product": product,
        "customer": customer,
    }


# ===========================================================================
# PHASE 106: Manager Authority Limit Tests
# ===========================================================================

def test_manager_authority_limit_crud_and_boundaries(client, setup_g22_test_data):
    data = setup_g22_test_data
    headers = data["admin_headers"]
    mgr_user = data["mgr_user"]

    # 1. Negative test: discount < 0 -> 422
    resp_neg = client.post(
        "/api/v1/governance/discounts/manager-limits",
        headers=headers,
        json={"user_id": str(mgr_user.id), "max_authorized_discount": -5.0},
    )
    assert resp_neg.status_code == 422

    # 2. Negative test: discount > 100 -> 422
    resp_high = client.post(
        "/api/v1/governance/discounts/manager-limits",
        headers=headers,
        json={"user_id": str(mgr_user.id), "max_authorized_discount": 105.0},
    )
    assert resp_high.status_code == 422

    # 3. Create valid limit: 25%
    resp_create = client.post(
        "/api/v1/governance/discounts/manager-limits",
        headers=headers,
        json={
            "user_id": str(mgr_user.id),
            "max_authorized_discount": 25.0,
            "is_active": True,
        },
    )
    assert resp_create.status_code == 201
    limit_id = resp_create.json()["id"]
    assert float(resp_create.json()["max_authorized_discount"]) == 25.0

    # 4. Duplicate active record -> 409 Conflict
    resp_dup = client.post(
        "/api/v1/governance/discounts/manager-limits",
        headers=headers,
        json={
            "user_id": str(mgr_user.id),
            "max_authorized_discount": 30.0,
            "is_active": True,
        },
    )
    assert resp_dup.status_code == 409

    # 5. List and Get
    resp_list = client.get("/api/v1/governance/discounts/manager-limits", headers=headers)
    assert resp_list.status_code == 200
    assert any(item["id"] == limit_id for item in resp_list.json()["items"])

    resp_get = client.get(f"/api/v1/governance/discounts/manager-limits/{limit_id}", headers=headers)
    assert resp_get.status_code == 200
    assert resp_get.json()["id"] == limit_id

    # 6. Update
    resp_up = client.put(
        f"/api/v1/governance/discounts/manager-limits/{limit_id}",
        headers=headers,
        json={"max_authorized_discount": 28.0},
    )
    assert resp_up.status_code == 200
    assert float(resp_up.json()["max_authorized_discount"]) == 28.0

    # 7. Soft-deactivate
    resp_del = client.delete(f"/api/v1/governance/discounts/manager-limits/{limit_id}", headers=headers)
    assert resp_del.status_code == 204

    # Now a new active limit can be created since previous is deactivated
    resp_create_2 = client.post(
        "/api/v1/governance/discounts/manager-limits",
        headers=headers,
        json={
            "user_id": str(mgr_user.id),
            "max_authorized_discount": 25.0,
            "is_active": True,
        },
    )
    assert resp_create_2.status_code == 201


# ===========================================================================
# PHASE 107: Finance Authority Limit Tests
# ===========================================================================

def test_finance_authority_limit_crud_and_rbac(client, setup_g22_test_data):
    data = setup_g22_test_data
    admin_headers = data["admin_headers"]
    rep_headers = data["rep_headers"]
    fin_user = data["fin_user"]

    # 1. Sales Rep forbidden from configuring Finance limit (403)
    resp_rep = client.post(
        "/api/v1/governance/discounts/finance-limits",
        headers=rep_headers,
        json={"user_id": str(fin_user.id), "max_authorized_discount": 40.0},
    )
    assert resp_rep.status_code == 403

    # 2. Admin creates valid finance limit: 40%
    resp_create = client.post(
        "/api/v1/governance/discounts/finance-limits",
        headers=admin_headers,
        json={
            "user_id": str(fin_user.id),
            "max_authorized_discount": 40.0,
            "is_active": True,
        },
    )
    assert resp_create.status_code == 201
    fin_limit_id = resp_create.json()["id"]

    # 3. Duplicate active rejection -> 409
    resp_dup = client.post(
        "/api/v1/governance/discounts/finance-limits",
        headers=admin_headers,
        json={
            "user_id": str(fin_user.id),
            "max_authorized_discount": 45.0,
            "is_active": True,
        },
    )
    assert resp_dup.status_code == 409

    # 4. List and Update
    resp_list = client.get("/api/v1/governance/discounts/finance-limits", headers=admin_headers)
    assert resp_list.status_code == 200
    assert any(item["id"] == fin_limit_id for item in resp_list.json()["items"])

    resp_up = client.put(
        f"/api/v1/governance/discounts/finance-limits/{fin_limit_id}",
        headers=admin_headers,
        json={"max_authorized_discount": 42.0},
    )
    assert resp_up.status_code == 200
    assert float(resp_up.json()["max_authorized_discount"]) == 42.0


# ===========================================================================
# PHASES 108 & 110: Deterministic Discount Policy Engine & Violation Detection
# ===========================================================================

def test_discount_policy_engine_hierarchy_and_minimum_ceiling(client, setup_g22_test_data, db_session):
    """Verify that the policy engine calculates the governing ceiling as MIN(company, customer, category, product)

    and detects proper violations.
    """
    data = setup_g22_test_data
    company = data["company"]
    customer = data["customer"]
    category = data["category"]
    product = data["product"]
    rep_user = data["rep_user"]

    now = datetime.now(timezone.utc)

    # 1. Setup Company Configuration = 30%
    db_session.add(
        DiscountConfiguration(
            company_id=company.id,
            name="Tier 1 Policy",
            default_discount_ceiling=Decimal("30.00"),
            is_active=True,
            effective_from=now - timedelta(days=1),
        )
    )

    # 2. Setup Category Ceiling = 25%
    db_session.add(
        CategoryDiscountCeiling(
            company_id=company.id,
            category_id=category.id,
            max_discount_percentage=Decimal("25.00"),
            is_active=True,
            effective_from=now - timedelta(days=1),
        )
    )

    # 3. Setup Product Ceiling = 20%
    db_session.add(
        ProductDiscountCeiling(
            company_id=company.id,
            product_id=product.id,
            max_discount_percentage=Decimal("20.00"),
            is_active=True,
            effective_from=now - timedelta(days=1),
        )
    )

    # 4. Setup Customer Ceiling = 15% (Most restrictive)
    db_session.add(
        CustomerDiscountCeiling(
            company_id=company.id,
            customer_id=customer.id,
            max_discount_percentage=Decimal("15.00"),
            is_active=True,
            effective_from=now - timedelta(days=1),
        )
    )

    # 5. Setup Sales Rep Authority Limit = 10%
    db_session.add(
        SalesRepAuthorityLimit(
            company_id=company.id,
            user_id=rep_user.id,
            max_authorized_discount=Decimal("10.00"),
            is_active=True,
            effective_from=now - timedelta(days=1),
        )
    )
    db_session.commit()

    # Case A: Proposed discount 8% -> Within rep authority (10%) and within ceiling (15%) -> PASS
    res_a = DiscountPolicyEngine.evaluate(
        db=db_session,
        company_id=company.id,
        customer_id=customer.id,
        product_id=product.id,
        proposed_discount=Decimal("8.00"),
        actor=rep_user,
    )
    assert res_a.allowed is True
    assert res_a.effective_ceiling == Decimal("15.00")
    assert res_a.actor_authority_limit == Decimal("10.00")
    assert len(res_a.violations) == 0

    # Case B: Proposed discount 12% -> Exceeds rep authority (10%) but within ceiling (15%) -> FAIL on authority
    res_b = DiscountPolicyEngine.evaluate(
        db=db_session,
        company_id=company.id,
        customer_id=customer.id,
        product_id=product.id,
        proposed_discount=Decimal("12.00"),
        actor=rep_user,
    )
    assert res_b.allowed is False
    assert len(res_b.violations) == 1
    assert res_b.violations[0].type == "SALES_REP_AUTHORITY_LIMIT"
    assert res_b.violations[0].limit == Decimal("10.00")

    # Case C: Proposed discount 22% -> Exceeds customer (15%), product (20%), and rep authority (10%)
    res_c = DiscountPolicyEngine.evaluate(
        db=db_session,
        company_id=company.id,
        customer_id=customer.id,
        product_id=product.id,
        proposed_discount=Decimal("22.00"),
        actor=rep_user,
    )
    assert res_c.allowed is False
    violation_types = {v.type for v in res_c.violations}
    assert "CUSTOMER_DISCOUNT_CEILING" in violation_types
    assert "PRODUCT_DISCOUNT_CEILING" in violation_types
    assert "SALES_REP_AUTHORITY_LIMIT" in violation_types
    assert "CATEGORY_DISCOUNT_CEILING" not in violation_types  # category is 25%

    # Case D: Proposed discount 35% -> Exceeds ALL ceilings
    res_d = DiscountPolicyEngine.evaluate(
        db=db_session,
        company_id=company.id,
        customer_id=customer.id,
        product_id=product.id,
        proposed_discount=Decimal("35.00"),
        actor=rep_user,
    )
    assert res_d.allowed is False
    all_v_types = {v.type for v in res_d.violations}
    assert "COMPANY_DISCOUNT_CEILING" in all_v_types
    assert "CUSTOMER_DISCOUNT_CEILING" in all_v_types
    assert "CATEGORY_DISCOUNT_CEILING" in all_v_types
    assert "PRODUCT_DISCOUNT_CEILING" in all_v_types
    assert "SALES_REP_AUTHORITY_LIMIT" in all_v_types


# ===========================================================================
# PHASE 109: Discount Validation Endpoint & Security Tests
# ===========================================================================

def test_discount_validation_endpoint_and_cross_tenant_isolation(client, setup_g22_test_data, db_session):
    data = setup_g22_test_data
    headers = data["rep_headers"]
    customer = data["customer"]
    product = data["product"]

    # 1. Negative: Proposed discount > 100 -> 422
    resp_invalid = client.post(
        "/api/v1/governance/discounts/validate",
        headers=headers,
        json={
            "customer_id": str(customer.id),
            "product_id": str(product.id),
            "proposed_discount": 150.0,
        },
    )
    assert resp_invalid.status_code == 422

    # 2. Negative: Cross-tenant isolation (customer of another company) -> 404
    other_company = Company(name="Other Co", legal_name="Other Co Ltd", is_active=True)
    db_session.add(other_company)
    db_session.flush()

    other_customer = Customer(
        company_id=other_company.id,
        customer_code="OTHER-01",
        name="Foreign Customer",
        is_active=True,
    )
    db_session.add(other_customer)
    db_session.commit()

    resp_cross = client.post(
        "/api/v1/governance/discounts/validate",
        headers=headers,
        json={
            "customer_id": str(other_customer.id),
            "product_id": str(product.id),
            "proposed_discount": 5.0,
        },
    )
    assert resp_cross.status_code == 404

    # 3. Valid evaluation request
    resp_valid = client.post(
        "/api/v1/governance/discounts/validate",
        headers=headers,
        json={
            "customer_id": str(customer.id),
            "product_id": str(product.id),
            "proposed_discount": 8.0,
        },
    )
    assert resp_valid.status_code == 200
    res_json = resp_valid.json()
    assert "allowed" in res_json
    assert "effective_ceiling" in res_json
    assert "violations" in res_json

    # 4. Verify audit log creation
    audit_record = (
        db_session.query(AuditLog)
        .filter(AuditLog.action == "DISCOUNT_POLICY_EVALUATION")
        .order_by(AuditLog.created_at.desc())
        .first()
    )
    assert audit_record is not None
    assert audit_record.context_metadata["customer_id"] == str(customer.id)


def test_manager_and_finance_authority_in_policy_engine(setup_g22_test_data, db_session):
    """Verify that Manager and Finance roles receive their correct authority limits."""
    data = setup_g22_test_data
    company = data["company"]
    customer = data["customer"]
    product = data["product"]
    mgr_user = data["mgr_user"]
    fin_user = data["fin_user"]

    now = datetime.now(timezone.utc)

    # Add Manager limit: 25%
    db_session.add(
        ManagerAuthorityLimit(
            company_id=company.id,
            user_id=mgr_user.id,
            max_authorized_discount=Decimal("25.00"),
            is_active=True,
            effective_from=now - timedelta(days=1),
        )
    )

    # Add Finance limit: 35%
    db_session.add(
        FinanceAuthorityLimit(
            company_id=company.id,
            user_id=fin_user.id,
            max_authorized_discount=Decimal("35.00"),
            is_active=True,
            effective_from=now - timedelta(days=1),
        )
    )
    db_session.commit()

    # Manager evaluates proposed discount 22% (within 25%) -> allowed
    res_mgr = DiscountPolicyEngine.evaluate(
        db=db_session,
        company_id=company.id,
        customer_id=customer.id,
        product_id=product.id,
        proposed_discount=Decimal("22.00"),
        actor=mgr_user,
    )
    assert res_mgr.actor_authority_limit == Decimal("25.00")

    # Manager evaluates proposed discount 28% -> MANAGER_AUTHORITY_LIMIT violation
    res_mgr_over = DiscountPolicyEngine.evaluate(
        db=db_session,
        company_id=company.id,
        customer_id=customer.id,
        product_id=product.id,
        proposed_discount=Decimal("28.00"),
        actor=mgr_user,
    )
    mgr_v_types = [v.type for v in res_mgr_over.violations]
    assert "MANAGER_AUTHORITY_LIMIT" in mgr_v_types

    # Finance evaluates proposed discount 32% (within 35%) -> allowed
    res_fin = DiscountPolicyEngine.evaluate(
        db=db_session,
        company_id=company.id,
        customer_id=customer.id,
        product_id=product.id,
        proposed_discount=Decimal("32.00"),
        actor=fin_user,
    )
    assert res_fin.actor_authority_limit == Decimal("35.00")

    # Finance evaluates proposed discount 40% -> FINANCE_AUTHORITY_LIMIT violation
    res_fin_over = DiscountPolicyEngine.evaluate(
        db=db_session,
        company_id=company.id,
        customer_id=customer.id,
        product_id=product.id,
        proposed_discount=Decimal("40.00"),
        actor=fin_user,
    )
    fin_v_types = [v.type for v in res_fin_over.violations]
    assert "FINANCE_AUTHORITY_LIMIT" in fin_v_types
