import asyncio
import json
import logging
import uuid
from typing import Any, Dict, List, Optional, Set
from fastapi import WebSocket

from app.models.user import User
from app.schemas.realtime import EventEnvelope, ServerMessage, ServerMessageType
from app.services.realtime_auth import RealtimeAuthService

logger = logging.getLogger("dealflow360.connection_manager")


class ConnectionMetadata:
    def __init__(self, websocket: WebSocket, user: User):
        self.websocket = websocket
        self.user = user
        self.company_id: uuid.UUID = user.company_id
        self.user_id: uuid.UUID = user.id
        # Subscribed topics (e.g. "transactions", "approvals", "inventory", "deal_health", "ai", "notifications")
        self.topics: Set[str] = {"notifications"}  # default always subscribed to notifications


class ConnectionManager:
    """
    Asynchronous Connection Manager (Phase 337, Phase 338).
    Tracks active WebSocket connections with strict multi-tenant isolation,
    topic-based subscription routing, and dead-connection pruning.
    """
    def __init__(self):
        # socket -> ConnectionMetadata
        self._connections: Dict[WebSocket, ConnectionMetadata] = {}
        # company_id -> Set[WebSocket]
        self._company_map: Dict[uuid.UUID, Set[WebSocket]] = {}
        # user_id -> Set[WebSocket]
        self._user_map: Dict[uuid.UUID, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user: User) -> ConnectionMetadata:
        """Accept WebSocket and register in tenant and user pools."""
        await websocket.accept()
        meta = ConnectionMetadata(websocket, user)

        async with self._lock:
            self._connections[websocket] = meta

            if meta.company_id not in self._company_map:
                self._company_map[meta.company_id] = set()
            self._company_map[meta.company_id].add(websocket)

            if meta.user_id not in self._user_map:
                self._user_map[meta.user_id] = set()
            self._user_map[meta.user_id].add(websocket)

        logger.info(
            f"WebSocket connected: user={user.id} ({user.email}), company={user.company_id}. "
            f"Active connections for tenant: {len(self._company_map[meta.company_id])}"
        )
        return meta

    async def disconnect(self, websocket: WebSocket) -> None:
        """Unregister connection and clean up collections."""
        async with self._lock:
            meta = self._connections.pop(websocket, None)
            if meta:
                if meta.company_id in self._company_map:
                    self._company_map[meta.company_id].discard(websocket)
                    if not self._company_map[meta.company_id]:
                        del self._company_map[meta.company_id]

                if meta.user_id in self._user_map:
                    self._user_map[meta.user_id].discard(websocket)
                    if not self._user_map[meta.user_id]:
                        del self._user_map[meta.user_id]

                logger.info(f"WebSocket disconnected: user={meta.user_id}, company={meta.company_id}")

    def subscribe_topic(self, websocket: WebSocket, topic: str) -> bool:
        """Add topic subscription after RBAC check."""
        meta = self._connections.get(websocket)
        if not meta:
            return False

        if RealtimeAuthService.authorize_topic(meta.user, topic):
            meta.topics.add(topic.strip().lower())
            return True
        return False

    def unsubscribe_topic(self, websocket: WebSocket, topic: str) -> bool:
        """Remove topic subscription."""
        meta = self._connections.get(websocket)
        if not meta:
            return False

        meta.topics.discard(topic.strip().lower())
        return True

    def get_user_topics(self, websocket: WebSocket) -> Set[str]:
        meta = self._connections.get(websocket)
        return set(meta.topics) if meta else set()

    async def send_to_socket(self, websocket: WebSocket, message: ServerMessage) -> bool:
        """Send message safely to a specific socket. Disconnects if socket is dead."""
        try:
            # Model dump json handles datetimes and UUIDs cleanly
            await websocket.send_text(message.model_dump_json())
            return True
        except Exception as e:
            logger.warning(f"Error sending message to socket: {e}. Pruning connection.")
            await self.disconnect(websocket)
            return False

    async def broadcast_to_company(
        self,
        company_id: uuid.UUID,
        topic: str,
        event: EventEnvelope[Any],
        target_user_id: Optional[uuid.UUID] = None,
        target_role: Optional[str] = None,
    ) -> int:
        """
        Broadcast an event to all authorized connections within a specific company.
        Guarantees:
        1. Multi-tenant isolation: Never broadcasts outside company_id.
        2. Topic authorization: Only dispatches if socket is subscribed to topic or '*'.
        3. Optional targeting: Filter by user_id or recipient_role.
        """
        sockets_to_send: List[WebSocket] = []

        async with self._lock:
            candidates = list(self._company_map.get(company_id, set()))

        msg = ServerMessage(
            type=ServerMessageType.EVENT,
            topic=topic,
            payload=event.model_dump(mode="json"),
        )

        for ws in candidates:
            meta = self._connections.get(ws)
            if not meta:
                continue

            # Check topic subscription
            if topic not in meta.topics and "*" not in meta.topics:
                continue

            # Check target user filter
            if target_user_id and meta.user_id != target_user_id:
                continue

            # Check target role filter
            if target_role:
                user_roles = {r.name.upper() for r in getattr(meta.user, "roles", [])}
                if target_role.upper() not in user_roles and "ADMIN" not in user_roles:
                    continue

            sockets_to_send.append(ws)

        sent_count = 0
        for ws in sockets_to_send:
            success = await self.send_to_socket(ws, msg)
            if success:
                sent_count += 1

        return sent_count

    async def broadcast_to_user(self, user_id: uuid.UUID, topic: str, payload: Any) -> int:
        """Send direct message to all open tabs/sockets of a specific user."""
        async with self._lock:
            sockets = list(self._user_map.get(user_id, set()))

        msg = ServerMessage(
            type=ServerMessageType.EVENT,
            topic=topic,
            payload=payload,
        )

        sent_count = 0
        for ws in sockets:
            if await self.send_to_socket(ws, msg):
                sent_count += 1
        return sent_count


# Global singleton connection manager
connection_manager = ConnectionManager()
