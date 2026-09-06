import uuid
from typing import Dict, List, Optional, Set
from sqlalchemy.orm import Session

from app.core.jwt import decode_token
from app.models.user import User
from app.schemas.realtime import RealtimeTopic


TOPIC_ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    RealtimeTopic.ALL.value: {"ADMIN", "SUPERADMIN"},
    RealtimeTopic.TRANSACTIONS.value: {"ADMIN", "SUPERADMIN", "FINANCE", "MANAGER", "ACCOUNTING"},
    RealtimeTopic.APPROVALS.value: {"ADMIN", "SUPERADMIN", "MANAGER", "FINANCE", "SALES_REP", "APPROVER"},
    RealtimeTopic.INVENTORY.value: {"ADMIN", "SUPERADMIN", "MANAGER", "INVENTORY_MANAGER", "WAREHOUSE_MANAGER", "SALES_REP"},
    RealtimeTopic.DEAL_HEALTH.value: {"ADMIN", "SUPERADMIN", "MANAGER", "SALES_REP", "FINANCE"},
    RealtimeTopic.AI.value: {"ADMIN", "SUPERADMIN", "MANAGER", "SALES_REP", "FINANCE", "USER"},
    RealtimeTopic.NOTIFICATIONS.value: {"*"},  # All authenticated users receive their own notifications
}


class RealtimeAuthService:
    """
    Real-Time Authentication and Topic-Level Authorization (Phase 339, Phase 340).
    Ensures zero client-supplied tenant trust: all credentials and scopes
    are derived from validated JWT tokens and database queries.
    """

    @staticmethod
    def authenticate_token(db: Session, token: str) -> User:
        """
        Authenticate a JWT token. Raises ValueError on expired/invalid/revoked token or missing user.
        """
        if not token:
            raise ValueError("Missing authentication token")

        try:
            payload = decode_token(token)
        except Exception as e:
            raise ValueError(f"Invalid or expired authentication token: {e}")

        if not payload:
            raise ValueError("Invalid or expired authentication token")

        if payload.get("type") != "access":
            raise ValueError("Token is not an access token")

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise ValueError("Missing subject in token payload")

        try:
            user_uuid = uuid.UUID(user_id_str)
        except (ValueError, TypeError):
            raise ValueError("Invalid user ID format in token")

        user = db.get(User, user_uuid)
        if not user or not user.is_active:
            raise ValueError("User not found or account inactive")

        if not user.company_id:
            raise ValueError("User is not associated with any company")

        return user

    @staticmethod
    def authorize_topic(user: User, topic: str) -> bool:
        """
        Determine if the user is authorized to subscribe to the given topic.
        Strict multi-tenant security: role-based topic filtering.
        """
        if not topic:
            return False

        topic_clean = topic.strip().lower()

        # Everyone gets notifications scoped to their tenant/user
        if topic_clean == RealtimeTopic.NOTIFICATIONS.value:
            return True

        # Resolve user role names
        user_roles: Set[str] = set()
        if hasattr(user, "roles") and user.roles:
            user_roles = {r.name.upper() for r in user.roles}

        # Check if user has ADMIN / SUPERADMIN
        if "ADMIN" in user_roles or "SUPERADMIN" in user_roles:
            return True

        # Check allowed roles for specific topic
        allowed = TOPIC_ROLE_PERMISSIONS.get(topic_clean, set())
        if "*" in allowed:
            return True

        return bool(user_roles.intersection(allowed))
