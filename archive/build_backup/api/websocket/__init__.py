"""WebSocket package for real-time rights-preserving communication."""

from api.websocket.rights_gateway import (
    RightsPreservingWebSocketManager,
    WebSocketEndpoint,
    websocket_endpoint,
    websocket_manager,
)

__all__ = [
    "RightsPreservingWebSocketManager",
    "WebSocketEndpoint",
    "websocket_endpoint",
    "websocket_manager",
]
