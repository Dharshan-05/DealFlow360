import asyncio
import pytest
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from fastapi.testclient import TestClient

from app.main import app
from app.core.jwt import create_access_token
from app.db.session import SessionLocal
from app.models.company import Company
from app.models.user import User
from app.models.role import Role
from app.models.notification import Notification, NotificationPriority
from app.schemas.realtime import EventEnvelope, RealtimeTopic, ClientAction
from app.services.event_bus import EventBus
from app.services.connection_manager import ConnectionManager
from app.services.realtime_auth import RealtimeAuthService
from app.services.notification import NotificationService


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_tenants(db_session):
    # Setup company A and user A
    comp_a = Company(
        id=uuid.uuid4(),
        name=f"Tenant A {uuid.uuid4().hex[:6]}",
    )
    comp_b = Company(
        id=uuid.uuid4(),
        name=f"Tenant B {uuid.uuid4().hex[:6]}",
    )
    db_session.add_all([comp_a, comp_b])
    db_session.commit()

    role_admin = db_session.query(Role).filter_by(name="ADMIN").first()
    if not role_admin:
        role_admin = Role(id=uuid.uuid4(), name="ADMIN")
        db_session.add(role_admin)
        db_session.commit()

    user_a = User(
        id=uuid.uuid4(),
        company_id=comp_a.id,
        email=f"user_a_{uuid.uuid4().hex[:6]}@example.com",
        first_name="Alice",
        last_name="Admin",
        password_hash="fakehash",
        is_active=True,
    )
    user_a.roles.append(role_admin)

    user_b = User(
        id=uuid.uuid4(),
        company_id=comp_b.id,
        email=f"user_b_{uuid.uuid4().hex[:6]}@example.com",
        first_name="Bob",
        last_name="Manager",
        password_hash="fakehash",
        is_active=True,
    )
    user_b.roles.append(role_admin)

    db_session.add_all([user_a, user_b])
    db_session.commit()

    token_a = create_access_token(subject=str(user_a.id))
    token_b = create_access_token(subject=str(user_b.id))

    return {
        "comp_a": comp_a,
        "comp_b": comp_b,
        "user_a": user_a,
        "user_b": user_b,
        "token_a": token_a,
        "token_b": token_b,
    }


def test_phase_336_342_domain_events_schema(test_tenants):
    """Phase 336 & 342: EventEnvelope schema conformity and tenant binding."""
    comp_id = test_tenants["comp_a"].id
    envelope = EventEnvelope(
        event_type="transaction.created",
        company_id=comp_id,
        entity_type="invoice",
        entity_id="inv-123",
        payload={"total": "100.00"},
    )
    assert envelope.company_id == comp_id
    assert envelope.event_type == "transaction.created"
    assert envelope.version == 1
    assert envelope.event_id is not None
    assert isinstance(envelope.timestamp, datetime)


def test_phase_341_event_bus():
    """Phase 341: Event bus pub/sub, pattern matching, error isolation."""
    bus = EventBus()
    received = []

    async def handler_all(event):
        received.append(("all", event.event_type))

    async def handler_tx(event):
        received.append(("tx", event.event_type))

    async def faulty_handler(event):
        raise RuntimeError("Isolated handler failure")

    bus.subscribe("*", handler_all)
    bus.subscribe("transaction.*", handler_tx)
    bus.subscribe("transaction.*", faulty_handler)

    test_event = EventEnvelope(
        event_type="transaction.completed",
        company_id=uuid.uuid4(),
        entity_type="payment",
        entity_id="p-1",
        payload={},
    )

    asyncio.run(bus.publish(test_event))

    # Faulty handler did not break execution, both handlers received the event
    assert ("all", "transaction.completed") in received
    assert ("tx", "transaction.completed") in received


def test_phase_339_340_realtime_auth(test_tenants, db_session):
    """Phase 339 & 340: Real-time authentication and topic authorization."""
    token_a = test_tenants["token_a"]
    user = RealtimeAuthService.authenticate_token(db_session, token_a)
    assert user.id == test_tenants["user_a"].id
    assert user.company_id == test_tenants["comp_a"].id

    # Admin is authorized to all topics
    assert RealtimeAuthService.authorize_topic(user, "transactions") is True
    assert RealtimeAuthService.authorize_topic(user, "approvals") is True
    assert RealtimeAuthService.authorize_topic(user, "inventory") is True
    assert RealtimeAuthService.authorize_topic(user, "deal_health") is True
    assert RealtimeAuthService.authorize_topic(user, "ai") is True
    assert RealtimeAuthService.authorize_topic(user, "notifications") is True

    # Invalid token raises error
    with pytest.raises(ValueError):
        RealtimeAuthService.authenticate_token(db_session, "invalid.token.here")


def test_phase_337_338_websocket_endpoint_and_ping(test_tenants):
    """Phase 337 & 338: WebSocket endpoint connection, auth handshake, and ping/pong."""
    client = TestClient(app)
    token_a = test_tenants["token_a"]

    with client.websocket_connect(f"/api/v1/ws?token={token_a}") as websocket:
        # Handshake ack
        ack = websocket.receive_json()
        assert ack["type"] == "ack"
        assert ack["payload"]["status"] == "connected"
        assert ack["payload"]["user_id"] == str(test_tenants["user_a"].id)

        # Ping
        websocket.send_json({"action": "ping", "correlation_id": "test-ping-1"})
        pong = websocket.receive_json()
        assert pong["type"] == "pong"
        assert pong["correlation_id"] == "test-ping-1"

        # Subscribe
        websocket.send_json({"action": "subscribe", "topic": "transactions", "correlation_id": "sub-1"})
        sub_ack = websocket.receive_json()
        assert sub_ack["type"] == "ack"
        assert sub_ack["payload"]["status"] == "subscribed"


def test_phase_337_websocket_unauthorized_rejection():
    """Phase 337 & 339: Rejection on missing or invalid token."""
    client = TestClient(app)
    with pytest.raises(Exception):
        with client.websocket_connect("/api/v1/ws"):
            pass


def test_phase_347_notification_crud_and_endpoints(test_tenants, db_session):
    """Phase 347: Unified Notification Service persistence, listing, mark as read."""
    comp_a = test_tenants["comp_a"]
    user_a = test_tenants["user_a"]

    notif = NotificationService.create_notification(
        db=db_session,
        company_id=comp_a.id,
        user_id=user_a.id,
        title="Test Alert",
        message="This is a test notification",
        priority=NotificationPriority.HIGH,
        event_type="deal.health.critical",
        entity_type="deal",
        entity_id="deal-999",
        payload={"score": "45"},
    )
    assert notif.id is not None
    assert notif.is_read is False

    # List notifications
    items, total, unread = NotificationService.list_notifications(db_session, user_a)
    assert total >= 1
    assert unread >= 1
    assert any(i.id == notif.id for i in items)

    # Mark as read
    updated = NotificationService.mark_as_read(db_session, user_a, [notif.id])
    assert updated == 1
    db_session.refresh(notif)
    assert notif.is_read is True
    assert notif.read_at is not None

    # Test via REST API endpoint
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {test_tenants['token_a']}"}
    resp = client.get("/api/v1/notifications", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert "unread_count" in data


def test_phase_343_346_349_domain_events_handling(test_tenants, db_session):
    """Phases 343-346 & 349: Verify domain event dispatch triggers notification handler."""
    comp_id = test_tenants["comp_a"].id
    actor_id = test_tenants["user_a"].id

    event = EventEnvelope(
        event_type="deal.health.critical",
        company_id=comp_id,
        actor_id=actor_id,
        entity_type="deal",
        entity_id="deal-critical-1",
        payload={"score": 30.5},
    )

    # Fire event handler directly
    asyncio.run(NotificationService.handle_domain_event(event))

    # Check notification persisted
    notifs = db_session.query(Notification).filter(
        Notification.company_id == comp_id,
        Notification.event_type == "deal.health.critical",
    ).all()
    assert len(notifs) >= 1
    assert notifs[-1].priority == NotificationPriority.URGENT.value
