"""Test suite for G08: Phases 036–039:
- Phase 036: Customer Portal Role
- Phase 037: Admin Role
- Phase 038: Object-Level Authorization (AuthorizationService)
- Phase 039: Permission Middleware (require_permission, require_role)
"""
import uuid
from decimal import Decimal
import pytest
from fastapi import APIRouter, Depends, FastAPI, status
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api.v1.endpoints.deps import get_current_user, require_permission, require_role
from app.core.errors import ApplicationError
from app.core.jwt import create_access_token
from app.db.session import SessionLocal, get_db
from app.models.company import Company
from app.models.customer import Customer
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User
from app.services.authorization import AuthorizationService
from app.services.rbac import RBACRoleNames, RBACService


# ===========================================================================
# PHASE 036: CUSTOMER PORTAL ROLE TESTS
# ===========================================================================

def test_customer_portal_role_exists_and_assignable():
    """Verify Customer Portal role is present in DB and grants exact canonical permissions."""
    session = SessionLocal()
    try:
        portal_role = session.scalars(
            select(Role).where(Role.name == RBACRoleNames.CUSTOMER_PORTAL)
        ).first()
        assert portal_role is not None, "Customer Portal role must be seeded"
        assert portal_role.is_active is True

        # Check permissions attached to Customer Portal
        perm_names = {p.name for p in portal_role.permissions}
        assert "customers:read" in perm_names
        assert "quotations:read" in perm_names
        assert "products:read" in perm_names

        # Customer Portal must NOT have mutation or administrative permissions
        assert "customers:write" not in perm_names
        assert "customers:delete" not in perm_names
        assert "quotations:write" not in perm_names
        assert "quotations:approve" not in perm_names
        assert "audit_logs:read" not in perm_names

        # Test assignment to user
        suffix = uuid.uuid4().hex[:6]
        user = User(
            email=f"portal_user_{suffix}@example.com",
            first_name="Portal",
            last_name="Customer",
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        RBACService.assign_role_to_user(session, user, portal_role)

        assert RBACService.has_role(user, RBACRoleNames.CUSTOMER_PORTAL) is True
        assert RBACService.user_has_permission(user, "customers:read") is True
        assert RBACService.user_has_permission(user, "quotations:read") is True
        assert RBACService.user_has_permission(user, "products:read") is True
        assert RBACService.user_has_permission(user, "customers:write") is False
        assert RBACService.user_has_permission(user, "quotations:approve") is False
    finally:
        if "user" in locals():
            session.delete(user)
            session.commit()
        session.close()


# ===========================================================================
# PHASE 037: ADMIN ROLE TESTS
# ===========================================================================

def test_admin_role_exists_and_has_full_permissions():
    """Verify Admin role exists and contains comprehensive system permissions."""
    session = SessionLocal()
    try:
        admin_role = session.scalars(
            select(Role).where(Role.name == RBACRoleNames.ADMIN)
        ).first()
        assert admin_role is not None, "Admin role must be seeded"
        assert admin_role.is_active is True

        perm_names = {p.name for p in admin_role.permissions}
        required_admin_perms = [
            "customers:read", "customers:write", "customers:delete",
            "products:read", "products:write",
            "warehouses:read", "warehouses:write",
            "quotations:read", "quotations:write", "quotations:approve",
            "audit_logs:read",
        ]
        for perm in required_admin_perms:
            assert perm in perm_names, f"Admin role missing permission '{perm}'"

        # Verify assignment to user
        suffix = uuid.uuid4().hex[:6]
        user = User(
            email=f"admin_test_{suffix}@example.com",
            first_name="System",
            last_name="Admin",
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        RBACService.assign_role_to_user(session, user, admin_role)
        assert RBACService.has_role(user, RBACRoleNames.ADMIN) is True
        assert RBACService.user_has_permission(user, "customers:delete") is True
        assert RBACService.user_has_permission(user, "quotations:approve") is True
        assert RBACService.user_has_permission(user, "audit_logs:read") is True
    finally:
        if "user" in locals():
            session.delete(user)
            session.commit()
        session.close()


# ===========================================================================
# PHASE 038: OBJECT-LEVEL AUTHORIZATION TESTS
# ===========================================================================

def test_object_level_tenant_isolation():
    """Verify multi-tenant isolation prevents cross-company access, except for Admin."""
    session = SessionLocal()
    suffix = uuid.uuid4().hex[:6]
    company_a = Company(name=f"Company A {suffix}")
    company_b = Company(name=f"Company B {suffix}")
    session.add_all([company_a, company_b])
    session.commit()
    session.refresh(company_a)
    session.refresh(company_b)

    user_a = User(email=f"usera_{suffix}@example.com", first_name="A", last_name="User", company_id=company_a.id)
    user_b = User(email=f"userb_{suffix}@example.com", first_name="B", last_name="User", company_id=company_b.id)
    user_no_company = User(email=f"nocomp_{suffix}@example.com", first_name="No", last_name="Comp")
    admin_user = User(email=f"admin_tenant_{suffix}@example.com", first_name="Admin", last_name="User", company_id=company_a.id)
    admin_role = session.scalars(select(Role).where(Role.name == RBACRoleNames.ADMIN)).first()

    session.add_all([user_a, user_b, user_no_company, admin_user])
    session.commit()
    session.refresh(user_a)
    session.refresh(user_b)
    session.refresh(user_no_company)
    session.refresh(admin_user)

    RBACService.assign_role_to_user(session, admin_user, admin_role)

    try:
        # User A accessing Company A resource -> allowed
        assert AuthorizationService.can_access_company_resource(user_a, company_a.id) is True
        AuthorizationService.assert_company_access(user_a, company_a.id)

        # User A accessing Company B resource -> forbidden
        assert AuthorizationService.can_access_company_resource(user_a, company_b.id) is False
        with pytest.raises(ApplicationError) as exc_info:
            AuthorizationService.assert_company_access(user_a, company_b.id)
        assert exc_info.value.status_code == 403
        assert exc_info.value.code == "FORBIDDEN_TENANT_ACCESS"

        # User with no company cannot access any company resource
        assert AuthorizationService.can_access_company_resource(user_no_company, company_a.id) is False

        # Inactive user cannot access company resource
        user_a.is_active = False
        assert AuthorizationService.can_access_company_resource(user_a, company_a.id) is False
        user_a.is_active = True

        # Admin user can access resources in Company A AND Company B
        assert AuthorizationService.can_access_company_resource(admin_user, company_a.id) is True
        assert AuthorizationService.can_access_company_resource(admin_user, company_b.id) is True
        AuthorizationService.assert_company_access(admin_user, company_b.id)
    finally:
        for entity in [user_a, user_b, user_no_company, admin_user, company_a, company_b]:
            session.delete(entity)
        session.commit()
        session.close()


def test_object_level_customer_authorization():
    """Verify customer read/modify authorization enforces both company isolation and action permissions."""
    session = SessionLocal()
    suffix = uuid.uuid4().hex[:6]
    company_1 = Company(name=f"Org 1 {suffix}")
    company_2 = Company(name=f"Org 2 {suffix}")
    session.add_all([company_1, company_2])
    session.commit()
    session.refresh(company_1)
    session.refresh(company_2)

    customer_org1 = Customer(
        company_id=company_1.id,
        customer_code=f"CUST1-{suffix}",
        name="Org 1 Client",
    )
    customer_org2 = Customer(
        company_id=company_2.id,
        customer_code=f"CUST2-{suffix}",
        name="Org 2 Client",
    )
    session.add_all([customer_org1, customer_org2])
    session.commit()
    session.refresh(customer_org1)
    session.refresh(customer_org2)

    # User in Org 1 with Sales Representative role (has customers:read and customers:write)
    user_sales = User(email=f"sales_{suffix}@example.com", first_name="Sales", last_name="Rep", company_id=company_1.id)
    # User in Org 1 with Customer Portal role (has customers:read, NO customers:write)
    user_portal = User(email=f"custportal_{suffix}@example.com", first_name="Portal", last_name="User", company_id=company_1.id)

    sales_role = session.scalars(select(Role).where(Role.name == RBACRoleNames.SALES_REPRESENTATIVE)).first()
    portal_role = session.scalars(select(Role).where(Role.name == RBACRoleNames.CUSTOMER_PORTAL)).first()

    session.add_all([user_sales, user_portal])
    session.commit()
    session.refresh(user_sales)
    session.refresh(user_portal)

    RBACService.assign_role_to_user(session, user_sales, sales_role)
    RBACService.assign_role_to_user(session, user_portal, portal_role)

    try:
        # Sales Rep in Org 1:
        # - Can read Org 1 customer
        assert AuthorizationService.can_access_customer(user_sales, customer_org1) is True
        AuthorizationService.assert_customer_access(user_sales, customer_org1, action="read")
        # - Can modify Org 1 customer
        assert AuthorizationService.can_modify_customer(user_sales, customer_org1) is True
        AuthorizationService.assert_customer_access(user_sales, customer_org1, action="write")
        # - Cannot access Org 2 customer (cross-tenant violation)
        assert AuthorizationService.can_access_customer(user_sales, customer_org2) is False
        with pytest.raises(ApplicationError) as exc_cross:
            AuthorizationService.assert_customer_access(user_sales, customer_org2, action="read")
        assert exc_cross.value.status_code == 403

        # Customer Portal user in Org 1:
        # - Can read Org 1 customer
        assert AuthorizationService.can_access_customer(user_portal, customer_org1) is True
        AuthorizationService.assert_customer_access(user_portal, customer_org1, action="read")
        # - Cannot modify Org 1 customer (missing customers:write permission)
        assert AuthorizationService.can_modify_customer(user_portal, customer_org1) is False
        with pytest.raises(ApplicationError) as exc_perm:
            AuthorizationService.assert_customer_access(user_portal, customer_org1, action="write")
        assert exc_perm.value.status_code == 403
        assert "customers:write" in exc_perm.value.message
    finally:
        for item in [user_sales, user_portal, customer_org1, customer_org2, company_1, company_2]:
            session.delete(item)
        session.commit()
        session.close()


# ===========================================================================
# PHASE 039: PERMISSION MIDDLEWARE TESTS
# ===========================================================================

def test_permission_middleware_enforcement():
    """Verify require_permission and require_role dependencies enforce active roles and permissions."""
    session = SessionLocal()
    suffix = uuid.uuid4().hex[:6]

    # Set up test users
    user_sales = User(email=f"mid_sales_{suffix}@example.com", first_name="Mid", last_name="Sales")
    user_portal = User(email=f"mid_portal_{suffix}@example.com", first_name="Mid", last_name="Portal")
    user_inactive = User(email=f"mid_inact_{suffix}@example.com", first_name="Mid", last_name="Inactive", is_active=False)

    sales_role = session.scalars(select(Role).where(Role.name == RBACRoleNames.SALES_REPRESENTATIVE)).first()
    portal_role = session.scalars(select(Role).where(Role.name == RBACRoleNames.CUSTOMER_PORTAL)).first()

    session.add_all([user_sales, user_portal, user_inactive])
    session.commit()
    session.refresh(user_sales)
    session.refresh(user_portal)
    session.refresh(user_inactive)

    RBACService.assign_role_to_user(session, user_sales, sales_role)
    RBACService.assign_role_to_user(session, user_portal, portal_role)
    RBACService.assign_role_to_user(session, user_inactive, sales_role)

    # Build isolated test FastAPI app with protected test routes
    test_app = FastAPI()

    # Route requiring 'customers:read'
    @test_app.get("/test/customers-read")
    def read_customers_route(user: User = Depends(require_permission("customers:read"))):
        return {"authorized": True, "email": user.email}

    # Route requiring 'customers:write'
    @test_app.post("/test/customers-write")
    def write_customers_route(user: User = Depends(require_permission("customers:write"))):
        return {"authorized": True, "email": user.email}

    # Route requiring 'Admin' role
    @test_app.get("/test/admin-only")
    def admin_only_route(user: User = Depends(require_role(RBACRoleNames.ADMIN))):
        return {"authorized": True, "email": user.email}

    # Override get_db in test_app
    test_app.dependency_overrides[get_db] = lambda: session
    client = TestClient(test_app)

    token_sales = create_access_token(str(user_sales.id))
    token_portal = create_access_token(str(user_portal.id))
    token_inactive = create_access_token(str(user_inactive.id))

    headers_sales = {"Authorization": f"Bearer {token_sales}"}
    headers_portal = {"Authorization": f"Bearer {token_portal}"}
    headers_inactive = {"Authorization": f"Bearer {token_inactive}"}

    try:
        # 1. Unauthenticated request -> 401 Unauthorized
        res = client.get("/test/customers-read")
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

        # 2. Inactive user -> 403 Forbidden
        res = client.get("/test/customers-read", headers=headers_inactive)
        assert res.status_code == status.HTTP_403_FORBIDDEN
        assert "inactive" in res.json()["detail"].lower()

        # 3. customers:read: Both Sales Rep and Customer Portal have it -> 200 OK
        res = client.get("/test/customers-read", headers=headers_sales)
        assert res.status_code == status.HTTP_200_OK
        assert res.json()["authorized"] is True

        res = client.get("/test/customers-read", headers=headers_portal)
        assert res.status_code == status.HTTP_200_OK
        assert res.json()["authorized"] is True

        # 4. customers:write: Sales Rep has it -> 200 OK
        res = client.post("/test/customers-write", headers=headers_sales)
        assert res.status_code == status.HTTP_200_OK
        assert res.json()["authorized"] is True

        # 5. customers:write: Customer Portal does NOT have it -> 403 Forbidden
        res = client.post("/test/customers-write", headers=headers_portal)
        assert res.status_code == status.HTTP_403_FORBIDDEN
        assert "customers:write" in res.json()["detail"]

        # 6. Admin-only route: Neither Sales Rep nor Customer Portal has Admin role -> 403 Forbidden
        res = client.get("/test/admin-only", headers=headers_sales)
        assert res.status_code == status.HTTP_403_FORBIDDEN
        assert "Admin" in res.json()["detail"]
    finally:
        for u in [user_sales, user_portal, user_inactive]:
            session.delete(u)
        session.commit()
        session.close()
