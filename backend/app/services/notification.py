import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import select, update, func, desc, and_
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.notification import Notification, NotificationPriority
from app.models.user import User
from app.schemas.realtime import EventEnvelope, RealtimeTopic
from app.services.connection_manager import connection_manager
from app.services.event_bus import event_bus

logger = logging.getLogger("dealflow360.notification_service")


class NotificationService:
    """
    Unified Notification Service (Phase 347).
    Translates high-value domain events into persistent notifications,
    manages read/unread states, and dispatches real-time WebSocket alerts.
    """

    @staticmethod
    def create_notification(
        db: Session,
        company_id: uuid.UUID,
        title: str,
        message: str,
        event_type: str,
        entity_type: str,
        entity_id: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        user_id: Optional[uuid.UUID] = None,
        recipient_role: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Notification:
        """Create and persist a notification record."""
        notification = Notification(
            company_id=company_id,
            user_id=user_id,
            recipient_role=recipient_role,
            title=title,
            message=message,
            priority=priority.value,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
            is_read=False,
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification

    @staticmethod
    def list_notifications(
        db: Session,
        user: User,
        skip: int = 0,
        limit: int = 50,
        unread_only: bool = False,
    ) -> Tuple[List[Notification], int, int]:
        """
        Fetch notifications for a user within their company.
        Includes notifications addressed directly to user, or addressed to one of user's roles, or company-wide.
        """
        user_roles = [r.name.upper() for r in getattr(user, "roles", [])]

        conditions = [
            Notification.company_id == user.company_id,
            (
                (Notification.user_id == user.id)
                | (Notification.recipient_role.in_(user_roles))
                | ((Notification.user_id == None) & (Notification.recipient_role == None))
            )
        ]

        if unread_only:
            conditions.append(Notification.is_read == False)

        stmt = select(Notification).where(and_(*conditions)).order_by(desc(Notification.created_at))
        total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        items = list(db.scalars(stmt.offset(skip).limit(limit)))

        # Unread count
        unread_stmt = select(func.count(Notification.id)).where(
            Notification.company_id == user.company_id,
            Notification.is_read == False,
            (
                (Notification.user_id == user.id)
                | (Notification.recipient_role.in_(user_roles))
                | ((Notification.user_id == None) & (Notification.recipient_role == None))
            )
        )
        unread_count = db.scalar(unread_stmt) or 0

        return items, total, unread_count

    @staticmethod
    def mark_as_read(db: Session, user: User, notification_ids: Optional[List[uuid.UUID]] = None) -> int:
        """Mark specific notifications or all notifications as read for the user."""
        now = datetime.now(timezone.utc)
        user_roles = [r.name.upper() for r in getattr(user, "roles", [])]

        conditions = [
            Notification.company_id == user.company_id,
            Notification.is_read == False,
            (
                (Notification.user_id == user.id)
                | (Notification.recipient_role.in_(user_roles))
                | ((Notification.user_id == None) & (Notification.recipient_role == None))
            )
        ]

        if notification_ids:
            conditions.append(Notification.id.in_(notification_ids))

        result = db.execute(
            update(Notification)
            .where(and_(*conditions))
            .values(is_read=True, read_at=now)
        )
        db.commit()
        return result.rowcount

    @classmethod
    async def handle_domain_event(cls, event: EventEnvelope[Any]) -> None:
        """
        Global event bus handler that maps domain events to persistent notifications
        and triggers real-time WebSocket broadcasts.
        """
        # Determine topic and target audience based on event_type
        event_type = event.event_type
        company_id = event.company_id

        topic = RealtimeTopic.NOTIFICATIONS.value
        if event_type.startswith("transaction."):
            topic = RealtimeTopic.TRANSACTIONS.value
        elif event_type.startswith("approval."):
            topic = RealtimeTopic.APPROVALS.value
        elif event_type.startswith("inventory."):
            topic = RealtimeTopic.INVENTORY.value
        elif event_type.startswith("deal.health."):
            topic = RealtimeTopic.DEAL_HEALTH.value
        elif event_type.startswith("ai."):
            topic = RealtimeTopic.AI.value

        # High priority events get persisted as Notification records
        should_persist = False
        priority = NotificationPriority.NORMAL
        title = ""
        message = ""
        target_role: Optional[str] = None
        target_user: Optional[uuid.UUID] = None

        if event_type == "transaction.failed":
            should_persist = True
            priority = NotificationPriority.URGENT
            title = "Payment Transaction Failed"
            message = f"Transaction {event.entity_id} failed: {event.payload.get('reason', 'Processing error')}"
            target_role = "FINANCE"
        elif event_type == "approval.created":
            should_persist = True
            priority = NotificationPriority.HIGH
            title = "New Approval Request"
            message = f"Deal {event.payload.get('deal_reference', event.entity_id)} requires approval."
            target_role = "MANAGER"
        elif event_type == "approval.approved":
            should_persist = True
            priority = NotificationPriority.NORMAL
            title = "Approval Request Approved"
            message = f"Deal {event.payload.get('deal_reference', event.entity_id)} was approved."
            target_user = event.actor_id
        elif event_type == "approval.rejected":
            should_persist = True
            priority = NotificationPriority.HIGH
            title = "Approval Request Rejected"
            message = f"Deal {event.payload.get('deal_reference', event.entity_id)} was rejected."
            target_user = event.actor_id
        elif event_type == "inventory.low_stock":
            should_persist = True
            priority = NotificationPriority.HIGH
            title = "Low Inventory Alert"
            message = f"Product {event.payload.get('product_name', event.entity_id)} has reached low stock."
            target_role = "INVENTORY_MANAGER"
        elif event_type == "deal.health.critical":
            should_persist = True
            priority = NotificationPriority.URGENT
            title = "Critical Deal Risk Alert"
            message = f"Deal {event.entity_id} health dropped into critical threshold."
            target_role = "MANAGER"

        if should_persist:
            db = SessionLocal()
            try:
                cls.create_notification(
                    db=db,
                    company_id=company_id,
                    title=title,
                    message=message,
                    event_type=event_type,
                    entity_type=event.entity_type,
                    entity_id=event.entity_id,
                    priority=priority,
                    user_id=target_user,
                    recipient_role=target_role,
                    payload=event.payload,
                )
            except Exception as e:
                logger.error(f"Failed to persist notification for event {event_type}: {e}")
            finally:
                db.close()

        # Broadcast event across company sockets subscribed to topic
        await connection_manager.broadcast_to_company(
            company_id=company_id,
            topic=topic,
            event=event,
            target_user_id=target_user,
            target_role=target_role,
        )


# Register global handler to EventBus wildcard
event_bus.subscribe("*", NotificationService.handle_domain_event)
