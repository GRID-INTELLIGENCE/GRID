from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import WebSocket
from starlette.types import ASGIApp
from starlette.websockets import WebSocketState

from ..services.movement_monitor import movement_monitor

logger = logging.getLogger(__name__)


class MonitoredWebSocket:
    """Wrapper around WebSocket that monitors message flow."""

    def __init__(self, websocket: WebSocket, connection_id: str):
        self.websocket = websocket
        self.connection_id = connection_id
        self.client = websocket.client if hasattr(websocket, "client") else None
        self.client_ip = self.client.host if self.client and hasattr(self.client, "host") else "unknown"

    async def accept(self, *args, **kwargs) -> None:
        """Accept the WebSocket connection and record it."""
        await self.websocket.accept(*args, **kwargs)

        # Record the connection
        movement_monitor.record_websocket_connection(
            connection_id=self.connection_id,
            path=self.websocket.url.path,
            client_ip=self.client_ip,
            user_id=getattr(self.websocket, "user", {}).get("sub") if hasattr(self.websocket, "user") else None,
        )

    async def receive(self, *args, **kwargs) -> Any:
        """Receive a message and record it."""
        try:
            message = await self.websocket.receive(*args, **kwargs)

            # Record the inbound message
            if "text" in message:
                movement_monitor.record_websocket_message(
                    connection_id=self.connection_id,
                    message_type="text",
                    message_size=len(message["text"]),
                    direction="inbound",
                )
            elif "bytes" in message:
                movement_monitor.record_websocket_message(
                    connection_id=self.connection_id,
                    message_type="binary",
                    message_size=len(message["bytes"]),
                    direction="inbound",
                )

            return message
        except Exception as e:
            # Record disconnection on error
            movement_monitor.record_websocket_disconnection(
                connection_id=self.connection_id,
                reason="error",
                error=str(e),
            )
            raise

    async def send_text(self, data: str) -> None:
        """Send text data and record the outbound message."""
        await self.websocket.send_text(data)

        movement_monitor.record_websocket_message(
            connection_id=self.connection_id,
            message_type="text",
            message_size=len(data),
            direction="outbound",
        )

    async def send_json(self, data: Any) -> None:
        """Send JSON data and record the outbound message."""
        text = json.dumps(data)
        await self.send_text(text)

    async def close(self, code: int = 1000, reason: str = None) -> None:
        """Close the WebSocket connection and record it."""
        if self.websocket.client_state != WebSocketState.DISCONNECTED:
            await self.websocket.close(code=code, reason=reason)

        movement_monitor.record_websocket_disconnection(
            connection_id=self.connection_id,
            reason=reason or "normal",
        )

    def __getattr__(self, name: str) -> Any:
        """Delegate other attributes to the underlying WebSocket."""
        return getattr(self.websocket, name)


class WebSocketMonitoringMiddleware:
    """Middleware for monitoring WebSocket connections."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "websocket":
            await self.app(scope, receive, send)
            return

        # Create a connection ID
        connection_id = f"ws_{id(scope):x}"

        # Wrap the send function to monitor outbound messages
        original_send = send

        async def monitored_send(message):
            if message["type"] == "websocket.accept":
                # The WebSocket is being accepted
                scope["_monitored_websocket"] = MonitoredWebSocket(
                    websocket=WebSocket(scope, receive=receive, send=send),
                    connection_id=connection_id,
                )

            await original_send(message)

        try:
            await self.app(scope, receive, monitored_send)
        except Exception as e:
            # Ensure we record disconnection on error
            movement_monitor.record_websocket_disconnection(
                connection_id=connection_id,
                reason="error",
                error=str(e),
            )
            raise
        finally:
            # Ensure we record disconnection when the connection ends
            if "_monitored_websocket" in scope:
                movement_monitor.record_websocket_disconnection(
                    connection_id=connection_id,
                    reason="closed",
                )
