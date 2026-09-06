import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field


T = TypeVar("T")


class RealtimeTopic(str, Enum):
    ALL = "*"
    TRANSACTIONS = "transactions"
    APPROVALS = "approvals"
    INVENTORY = "inventory"
    DEAL_HEALTH = "deal_health"
    AI = "ai"
    NOTIFICATIONS = "notifications"


class EventEnvelope(BaseModel, Generic[T]):
    """
    Standardized typed domain event envelope (Phase 336, Phase 342).
    Every event flowing through EventBus and WebSocket conforms to this contract.
    """
    event_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    event_type: str
    version: int = 1
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    company_id: uuid.UUID
    actor_id: Optional[uuid.UUID] = None
    entity_type: str
    entity_id: str
    correlation_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class ClientAction(str, Enum):
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    PING = "ping"


class ClientMessage(BaseModel):
    """Message received from WebSocket client."""
    action: ClientAction
    topic: Optional[str] = None
    correlation_id: Optional[str] = None


class ServerMessageType(str, Enum):
    EVENT = "event"
    ACK = "ack"
    PONG = "pong"
    ERROR = "error"


class ServerMessage(BaseModel):
    """Message pushed to WebSocket client."""
    type: ServerMessageType
    topic: Optional[str] = None
    correlation_id: Optional[str] = None
    payload: Any = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class NotificationResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    recipient_role: Optional[str] = None
    title: str
    message: str
    priority: str
    event_type: str
    entity_type: str
    entity_id: str
    payload: Optional[Dict[str, Any]] = None
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    items: List[NotificationResponse]
    total: int
    unread_count: int


class NotificationMarkReadRequest(BaseModel):
    notification_ids: Optional[List[uuid.UUID]] = None
