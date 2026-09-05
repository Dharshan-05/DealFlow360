"""Object-Level Authorization Service (Phase 038).
Enforces multi-tenant company isolation and object-level resource ownership:
- Tenant boundary enforcement between companies
- System administrator cross-tenant bypass
- Resource-specific access verification (e.g. Customer read/write/delete)
- Explicit 403 Forbidden denial on violation
"""
import uuid
from typing import Optional

from app.core.errors import ApplicationError
from app.core.logging import logger
from app.models.customer import Customer
from app.models.user import User
from app.services.rbac import RBACRoleNames, RBACService


class AuthorizationService:
    """Centralized service for evaluating object-level permissions and tenant boundaries."""

    @staticmethod
    def can_access_company_resource(
        user: User,
        resource_company_id: Optional[uuid.UUID],
    ) -> bool:
        """Evaluate if the user has access to a company-scoped resource.
        Admin users have system-wide access. Regular users must match resource company_id.
        """
        if not user.is_active:
            return False

        # System administrators have global cross-tenant access
        if RBACService.has_role(user, RBACRoleNames.ADMIN):
            return True

        # Non-admin users must have an assigned company matching the resource
        if user.company_id is None or resource_company_id is None:
            return False

        return user.company_id == resource_company_id

    @classmethod
    def assert_company_access(
        cls,
        user: User,
        resource_company_id: Optional[uuid.UUID],
    ) -> None:
        """Enforce tenant isolation. Raises 403 ApplicationError if unauthorized."""
        if not cls.can_access_company_resource(user, resource_company_id):
            logger.warning(
                f"Unauthorized company access attempt: user={user.id} "
                f"(company={user.company_id}) to resource_company={resource_company_id}"
            )
            raise ApplicationError(
                message="Access denied: Cross-company resource access is forbidden",
                code="FORBIDDEN_TENANT_ACCESS",
                status_code=403,
            )

    @classmethod
    def can_access_customer(cls, user: User, customer: Customer) -> bool:
        """Check if user can view a specific customer.
        Requires tenant boundary match AND 'customers:read' permission.
        """
        if not cls.can_access_company_resource(user, customer.company_id):
            return False
        return RBACService.user_has_permission(user, "customers:read")

    @classmethod
    def can_modify_customer(cls, user: User, customer: Customer) -> bool:
        """Check if user can modify a specific customer.
        Requires tenant boundary match AND 'customers:write' permission.
        """
        if not cls.can_access_company_resource(user, customer.company_id):
            return False
        return RBACService.user_has_permission(user, "customers:write")

    @classmethod
    def assert_customer_access(
        cls,
        user: User,
        customer: Customer,
        action: str = "read",
    ) -> None:
        """Assert access to a specific Customer instance, raising 403 on denial."""
        cls.assert_company_access(user, customer.company_id)

        if action == "read":
            if not RBACService.user_has_permission(user, "customers:read"):
                raise ApplicationError(
                    message=f"Permission denied: missing 'customers:read' to access customer '{customer.customer_code}'",
                    code="PERMISSION_DENIED",
                    status_code=403,
                )
        elif action in ("write", "update"):
            if not RBACService.user_has_permission(user, "customers:write"):
                raise ApplicationError(
                    message=f"Permission denied: missing 'customers:write' to modify customer '{customer.customer_code}'",
                    code="PERMISSION_DENIED",
                    status_code=403,
                )
        elif action == "delete":
            if not RBACService.user_has_permission(user, "customers:delete"):
                raise ApplicationError(
                    message=f"Permission denied: missing 'customers:delete' to delete customer '{customer.customer_code}'",
                    code="PERMISSION_DENIED",
                    status_code=403,
                )
        else:
            raise ApplicationError(
                message=f"Unsupported customer action: '{action}'",
                code="INVALID_ACTION",
                status_code=400,
            )
