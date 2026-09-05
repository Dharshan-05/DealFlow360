"""Unit and integration test suite for G07 RBAC Foundation and Roles (Phases 032–035):
- Phase 032: Role-Based Access Control primitives (lookup, assignment, removal, permission lookup)
- Phase 033: Sales Representative role
- Phase 034: Sales Manager role
- Phase 035: Finance and Operations roles
"""
import uuid
import pytest
from sqlalchemy import select

from app.core.errors import ApplicationError
from app.db.session import SessionLocal
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User
from app.services.rbac import RBACRoleNames, RBACService


# ===========================================================================
# PHASE 032: RBAC FOUNDATION SERVICE TESTS
# ===========================================================================

def test_user_with_no_roles():
    """Verify user initially has no roles and no permissions."""
    session = SessionLocal()
    suffix = uuid.uuid4().hex[:6]
    user = User(
        email=f"noroles_{suffix}@example.com",
        first_name="No",
        last_name="Roles",
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    try:
        roles = RBACService.get_user_roles(user)
        assert len(roles) == 0
        assert RBACService.has_role(user, "Admin") is False
        assert RBACService.has_role(user, "Sales Representative") is False

        perms = RBACService.get_user_permissions(user)
        assert len(perms) == 0
        assert RBACService.user_has_permission(user, "customers:read") is False
    finally:
        session.delete(user)
        session.commit()
        session.close()


def test_role_assignment_and_removal():
    """Verify role assignment, duplicate prevention, and role removal."""
    session = SessionLocal()
    suffix = uuid.uuid4().hex[:6]

    user = User(
        email=f"rbac_user_{suffix}@example.com",
        first_name="RBAC",
        last_name="User",
    )
    role = Role(
        name=f"TEST_ROLE_{suffix}",
        description="Temporary RBAC test role",
    )
    session.add_all([user, role])
    session.commit()
    session.refresh(user)
    session.refresh(role)

    try:
        # Initial: no roles
        assert RBACService.has_role(user, role.name) is False

        # 1. Assign role
        assigned = RBACService.assign_role_to_user(session, user, role)
        assert assigned is True
        assert RBACService.has_role(user, role.name) is True
        assert len(RBACService.get_user_roles(user)) == 1

        # 2. Duplicate assignment prevention (idempotent; returns False, no duplicate row)
        dup_assigned = RBACService.assign_role_to_user(session, user, role)
        assert dup_assigned is False
        assert len(RBACService.get_user_roles(user)) == 1

        # 3. Remove role
        removed = RBACService.remove_role_from_user(session, user, role)
        assert removed is True
        assert RBACService.has_role(user, role.name) is False
        assert len(RBACService.get_user_roles(user)) == 0

        # 4. Remove unassigned role (safe, returns False)
        dup_removed = RBACService.remove_role_from_user(session, user, role)
        assert dup_removed is False

    finally:
        session.delete(user)
        session.delete(role)
        session.commit()
        session.close()


def test_assign_inactive_role_rejected():
    """Verify attempting to assign an inactive role raises ApplicationError."""
    session = SessionLocal()
    suffix = uuid.uuid4().hex[:6]

    user = User(email=f"inactive_test_{suffix}@example.com", first_name="Inact", last_name="Role")
    inactive_role = Role(name=f"INACTIVE_{suffix}", is_active=False)
    session.add_all([user, inactive_role])
    session.commit()
    session.refresh(user)
    session.refresh(inactive_role)

    try:
        with pytest.raises(ApplicationError) as exc_info:
            RBACService.assign_role_to_user(session, user, inactive_role)
        assert exc_info.value.code == "ROLE_INACTIVE"
    finally:
        session.delete(user)
        session.delete(inactive_role)
        session.commit()
        session.close()


def test_permission_lookup_through_roles():
    """Verify user permissions are resolved transitively across assigned active roles."""
    session = SessionLocal()
    suffix = uuid.uuid4().hex[:6]

    user = User(email=f"perm_user_{suffix}@example.com", first_name="Perm", last_name="Tester")
    perm1 = Permission(name=f"res_a:read_{suffix}", resource="res_a", action=f"read_{suffix}")
    perm2 = Permission(name=f"res_b:write_{suffix}", resource="res_b", action=f"write_{suffix}")

    role1 = Role(name=f"ROLE_A_{suffix}")
    role2 = Role(name=f"ROLE_B_{suffix}")

    role1.permissions.append(perm1)
    role2.permissions.append(perm2)

    session.add_all([user, perm1, perm2, role1, role2])
    session.commit()
    session.refresh(user)
    session.refresh(role1)
    session.refresh(role2)

    try:
        # Assign role1
        RBACService.assign_role_to_user(session, user, role1)
        assert RBACService.user_has_permission(user, f"res_a:read_{suffix}") is True
        assert RBACService.user_has_permission(user, f"res_b:write_{suffix}") is False

        # Assign role2
        RBACService.assign_role_to_user(session, user, role2)
        assert RBACService.user_has_permission(user, f"res_a:read_{suffix}") is True
        assert RBACService.user_has_permission(user, f"res_b:write_{suffix}") is True

        user_perms = RBACService.get_user_permissions(user)
        perm_names = {p.name for p in user_perms}
        assert f"res_a:read_{suffix}" in perm_names
        assert f"res_b:write_{suffix}" in perm_names
        assert len(user_perms) == 2

    finally:
        session.delete(user)
        session.delete(role1)
        session.delete(role2)
        session.delete(perm1)
        session.delete(perm2)
        session.commit()
        session.close()


# ===========================================================================
# PHASES 033, 034, 035: BUSINESS ROLES VERIFICATION
# ===========================================================================

def test_sales_representative_role_exists_and_assignable():
    """Phase 033: Verify Sales Representative canonical role exists, is active, and assignable."""
    session = SessionLocal()
    suffix = uuid.uuid4().hex[:6]

    role = RBACService.get_role_by_name(session, RBACRoleNames.SALES_REPRESENTATIVE)
    assert role is not None
    assert role.name == "Sales Representative"
    assert role.is_active is True
    assert "sales" in role.description.lower() or "deal" in role.description.lower()

    # Verify assignable to a user
    user = User(email=f"sales_rep_{suffix}@example.com", first_name="Sales", last_name="Rep")
    session.add(user)
    session.commit()
    session.refresh(user)

    try:
        assigned = RBACService.assign_role_to_user(session, user, role)
        assert assigned is True
        assert RBACService.has_role(user, RBACRoleNames.SALES_REPRESENTATIVE) is True
        assert RBACService.user_has_permission(user, "quotations:write") is True
    finally:
        session.delete(user)
        session.commit()
        session.close()


def test_sales_manager_role_exists_and_assignable():
    """Phase 034: Verify Sales Manager canonical role exists, is active, and assignable."""
    session = SessionLocal()
    suffix = uuid.uuid4().hex[:6]

    role = RBACService.get_role_by_name(session, RBACRoleNames.SALES_MANAGER)
    assert role is not None
    assert role.name == "Sales Manager"
    assert role.is_active is True

    # Verify assignable to a user
    user = User(email=f"sales_mgr_{suffix}@example.com", first_name="Sales", last_name="Manager")
    session.add(user)
    session.commit()
    session.refresh(user)

    try:
        assigned = RBACService.assign_role_to_user(session, user, role)
        assert assigned is True
        assert RBACService.has_role(user, RBACRoleNames.SALES_MANAGER) is True
        assert RBACService.user_has_permission(user, "quotations:approve") is True
    finally:
        session.delete(user)
        session.commit()
        session.close()


def test_finance_and_operations_roles_exist_and_assignable():
    """Phase 035: Verify Finance and Operations canonical roles exist, are active, and assignable."""
    session = SessionLocal()
    suffix = uuid.uuid4().hex[:6]

    finance_role = RBACService.get_role_by_name(session, RBACRoleNames.FINANCE)
    ops_role = RBACService.get_role_by_name(session, RBACRoleNames.OPERATIONS)

    assert finance_role is not None
    assert finance_role.name == "Finance"
    assert finance_role.is_active is True

    assert ops_role is not None
    assert ops_role.name == "Operations"
    assert ops_role.is_active is True

    user = User(email=f"fin_ops_{suffix}@example.com", first_name="Fin", last_name="Ops")
    session.add(user)
    session.commit()
    session.refresh(user)

    try:
        # Assign Finance
        RBACService.assign_role_to_user(session, user, finance_role)
        assert RBACService.has_role(user, RBACRoleNames.FINANCE) is True
        assert RBACService.user_has_permission(user, "quotations:approve") is True

        # Assign Operations
        RBACService.assign_role_to_user(session, user, ops_role)
        assert RBACService.has_role(user, RBACRoleNames.OPERATIONS) is True
        assert RBACService.user_has_permission(user, "warehouses:write") is True

        # User now holds both roles
        roles = RBACService.get_user_roles(user)
        role_names = {r.name for r in roles}
        assert RBACRoleNames.FINANCE in role_names
        assert RBACRoleNames.OPERATIONS in role_names
        assert len(roles) == 2
    finally:
        session.delete(user)
        session.commit()
        session.close()
