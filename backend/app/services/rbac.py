"""Role-Based Access Control (RBAC) foundation service (Phases 032–035).
Provides reusable mechanisms for:
- Role retrieval and verification (has_role)
- Role assignment and removal with duplicate protection
- Permission retrieval through role associations
- Canonical role definitions for Sales Rep (033), Sales Manager (034), Finance & Operations (035)

Strictly authorization foundation — NO object-level authorization, NO permission middleware.
"""
import uuid
from typing import List, Optional, Set
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ApplicationError
from app.core.logging import logger
from app.models.audit_log import AuditLog
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User


class RBACRoleNames:
    """Canonical role names defined across DealFlow360."""
    ADMIN = "Admin"
    SALES_REPRESENTATIVE = "Sales Representative"
    SALES_MANAGER = "Sales Manager"
    FINANCE = "Finance"
    OPERATIONS = "Operations"
    CUSTOMER_PORTAL = "Customer Portal"


class RBACService:
    """Reusable RBAC service providing role and permission lookup/assignment primitives."""

    @staticmethod
    def get_role_by_name(db: Session, role_name: str) -> Optional[Role]:
        """Fetch role by canonical name."""
        return db.scalars(
            select(Role).where(Role.name == role_name)
        ).first()

    @staticmethod
    def get_role_by_id(db: Session, role_id: uuid.UUID) -> Optional[Role]:
        """Fetch role by primary key."""
        return db.get(Role, role_id)

    @staticmethod
    def get_user_roles(user: User, only_active: bool = True) -> List[Role]:
        """Retrieve roles assigned to a user, optionally filtering only active roles."""
        if not only_active:
            return list(user.roles)
        return [role for role in user.roles if role.is_active]

    @staticmethod
    def has_role(user: User, role_name: str, check_active: bool = True) -> bool:
        """Check if user is assigned a specific role by name."""
        for role in user.roles:
            if role.name == role_name:
                if check_active and not role.is_active:
                    return False
                return True
        return False

    @staticmethod
    def get_user_permissions(user: User, only_active: bool = True) -> List[Permission]:
        """Retrieve distinct active permissions accessible to the user through their roles."""
        active_roles = [r for r in user.roles if (not only_active or r.is_active)]
        seen_perm_ids: Set[uuid.UUID] = set()
        permissions: List[Permission] = []

        for role in active_roles:
            for perm in role.permissions:
                if perm.id not in seen_perm_ids:
                    seen_perm_ids.add(perm.id)
                    permissions.append(perm)
        return permissions

    @staticmethod
    def user_has_permission(user: User, permission_name: str, only_active: bool = True) -> bool:
        """Check if user has a specific permission via their assigned active roles."""
        for perm in RBACService.get_user_permissions(user, only_active=only_active):
            if perm.name == permission_name:
                return True
        return False

    @staticmethod
    def assign_role_to_user(
        db: Session,
        user: User,
        role: Role,
        assigned_by_user_id: Optional[uuid.UUID] = None,
    ) -> bool:
        """Assign a role to a user safely with duplicate assignment protection."""
        if not role.is_active:
            logger.warning(f"Attempted to assign inactive role: {role.name} to user: {user.id}")
            raise ApplicationError(
                message=f"Cannot assign inactive role '{role.name}'",
                code="ROLE_INACTIVE",
                status_code=400,
            )

        # Check if already assigned (prevent duplicate association rows)
        existing_role_ids = {r.id for r in user.roles}
        if role.id in existing_role_ids:
            logger.info(f"Role {role.name} already assigned to user {user.id}, skipping duplicate")
            return False

        user.roles.append(role)
        db.flush()

        # Audit log role assignment
        audit = AuditLog(
            user_id=assigned_by_user_id or user.id,
            company_id=user.company_id,
            action="rbac:role_assigned",
            resource_type="user_role",
            resource_id=f"{user.id}:{role.id}",
            details=f"Role '{role.name}' assigned to user '{user.email}'",
            context_metadata={"role_id": str(role.id), "role_name": role.name},
        )
        db.add(audit)
        db.commit()

        logger.info(f"Role {role.name} successfully assigned to user {user.id}")
        return True

    @staticmethod
    def remove_role_from_user(
        db: Session,
        user: User,
        role: Role,
        removed_by_user_id: Optional[uuid.UUID] = None,
    ) -> bool:
        """Remove a role assignment from a user."""
        existing_role_ids = {r.id for r in user.roles}
        if role.id not in existing_role_ids:
            logger.info(f"Role {role.name} not assigned to user {user.id}, skipping removal")
            return False

        user.roles = [r for r in user.roles if r.id != role.id]
        db.flush()

        # Audit log role removal
        audit = AuditLog(
            user_id=removed_by_user_id or user.id,
            company_id=user.company_id,
            action="rbac:role_removed",
            resource_type="user_role",
            resource_id=f"{user.id}:{role.id}",
            details=f"Role '{role.name}' removed from user '{user.email}'",
            context_metadata={"role_id": str(role.id), "role_name": role.name},
        )
        db.add(audit)
        db.commit()

        logger.info(f"Role {role.name} successfully removed from user {user.id}")
        return True
