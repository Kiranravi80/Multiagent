"""WebSocket endpoint to monitor agent status and events in real-time."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.application.dependencies.container import get_container
from app.core.logging import get_logger
from app.domain.events.base import DomainEvent

logger = get_logger(__name__)

router = APIRouter(prefix="/ws", tags=["WebSockets"])


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accept connection and add to active list."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("websocket_connected", count=len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove connection from active list."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info("websocket_disconnected", count=len(self.active_connections))

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast JSON message to all active connections."""
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception as exc:
                logger.error("websocket_send_failed", error=str(exc))
                if connection in self.active_connections:
                    self.active_connections.remove(connection)


manager = ConnectionManager()


async def event_bus_listener(event: DomainEvent) -> None:
    """Listens to domain events and broadcasts them to WebSocket clients."""
    payload = {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "timestamp": event.timestamp.isoformat(),
        "source_agent": event.source_agent,
        "payload": event.payload,
        "correlation_id": event.correlation_id,
    }
    await manager.broadcast(payload)


@router.websocket("/agents")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for agent monitoring."""
    container = get_container()
    await manager.connect(websocket)

    # Send current status on connect
    try:
        status = await container.agent_orchestration_service.get_system_status()
        await websocket.send_json({
            "event_type": "INITIAL_STATUS",
            "payload": status,
        })
    except Exception as exc:
        logger.error("websocket_initial_status_failed", error=str(exc))

    try:
        while True:
            # Keep connection open. Respond to client messages if needed.
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as exc:
        logger.error("websocket_error", error=str(exc))
        manager.disconnect(websocket)


async def register_ws_listener() -> None:
    """Register the WebSocket listener to the event bus."""
    container = get_container()
    
    # We subscribe to system events and career events that are interesting for the dashboard
    from app.core.constants import EventType
    events_to_monitor = [
        EventType.SYSTEM_STARTED,
        EventType.SYSTEM_SHUTDOWN,
        EventType.AGENT_REGISTERED,
        EventType.AGENT_STARTED,
        EventType.AGENT_STOPPED,
        EventType.AGENT_ERROR,
        EventType.JOB_COLLECTED,
        EventType.JOB_CLASSIFIED,
        EventType.JOB_MATCHED,
        EventType.APPLICATION_READY,
        EventType.APPLICATION_UPDATED,
    ]
    
    for event_type in events_to_monitor:
        await container.event_bus.subscribe(event_type, event_bus_listener)
    
    logger.info("websocket_listener_registered", events_monitored=len(events_to_monitor))
