import asyncio
import json
import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, status
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.schemas.realtime import ClientAction, ClientMessage, ServerMessage, ServerMessageType
from app.services.connection_manager import connection_manager
from app.services.realtime_auth import RealtimeAuthService

logger = logging.getLogger("dealflow360.websocket")

router = APIRouter()


@router.websocket("")
@router.websocket("/")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    """
    Production-ready WebSocket endpoint (Phase 337, Phase 338, Phase 339).
    Authenticates client via query param or initial auth frame,
    subscribes user to tenant channels, enforces RBAC, and handles heartbeat ping/pong.
    """
    db: Session = SessionLocal()
    user = None
    try:
        # Phase 339: Verify token
        if not token:
            # Check if client sends token in query or we wait for auth frame
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")
            return

        try:
            user = RealtimeAuthService.authenticate_token(db, token)
        except ValueError as auth_err:
            logger.warning(f"WebSocket auth failed: {auth_err}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=str(auth_err))
            return

        # Phase 338: Register connection
        metadata = await connection_manager.connect(websocket, user)

        # Send ACK connection established
        await connection_manager.send_to_socket(
            websocket,
            ServerMessage(
                type=ServerMessageType.ACK,
                payload={
                    "status": "connected",
                    "user_id": str(user.id),
                    "company_id": str(user.company_id),
                    "topics": list(metadata.topics),
                },
            ),
        )

        while True:
            # Await client frames
            data_text = await websocket.receive_text()
            try:
                raw_data = json.loads(data_text)
                action = raw_data.get("action")
                topic = raw_data.get("topic")
                correlation_id = raw_data.get("correlation_id")

                if action == ClientAction.PING.value or action == "ping":
                    await connection_manager.send_to_socket(
                        websocket,
                        ServerMessage(
                            type=ServerMessageType.PONG,
                            correlation_id=correlation_id,
                            payload={"status": "pong"},
                        ),
                    )

                elif action == ClientAction.SUBSCRIBE.value or action == "subscribe":
                    if topic:
                        success = connection_manager.subscribe_topic(websocket, topic)
                        if success:
                            await connection_manager.send_to_socket(
                                websocket,
                                ServerMessage(
                                    type=ServerMessageType.ACK,
                                    topic=topic,
                                    correlation_id=correlation_id,
                                    payload={"status": "subscribed", "topic": topic},
                                ),
                            )
                        else:
                            await connection_manager.send_to_socket(
                                websocket,
                                ServerMessage(
                                    type=ServerMessageType.ERROR,
                                    topic=topic,
                                    correlation_id=correlation_id,
                                    payload={"error": f"Unauthorized topic subscription: {topic}"},
                                ),
                            )

                elif action == ClientAction.UNSUBSCRIBE.value or action == "unsubscribe":
                    if topic:
                        connection_manager.unsubscribe_topic(websocket, topic)
                        await connection_manager.send_to_socket(
                            websocket,
                            ServerMessage(
                                type=ServerMessageType.ACK,
                                topic=topic,
                                correlation_id=correlation_id,
                                payload={"status": "unsubscribed", "topic": topic},
                            ),
                        )

            except json.JSONDecodeError:
                await connection_manager.send_to_socket(
                    websocket,
                    ServerMessage(
                        type=ServerMessageType.ERROR,
                        payload={"error": "Invalid JSON frame"},
                    ),
                )

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected normally: user={user.id if user else 'unknown'}")
    except Exception as e:
        logger.error(f"Unexpected WebSocket error: {e}", exc_info=True)
    finally:
        await connection_manager.disconnect(websocket)
        db.close()
