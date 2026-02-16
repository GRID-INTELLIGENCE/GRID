"""
WebSocket server for persistent boundary/consent/guardrail event streaming.
Subscribers receive real-time log events; events are also persisted via BoundaryEventLogger.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

try:
    import websockets

    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False

from boundaries.logger_ws import BoundaryEventLogger, set_global_logger


class BoundaryWebSocketServer:
    """
    Broadcasts boundary/consent/guardrail events to WebSocket clients.
    Run in background; logger persists to file and pushes each event to all connected clients.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 8765, log_dir: str = "logs/boundaries"):
        self.host = host
        self.port = port
        self.log_dir = log_dir
        self._clients: set[Any] = set()
        self._server = None
        self._logger: BoundaryEventLogger | None = None

    def _broadcast(self, event: dict[str, Any]) -> None:
        if not self._clients:
            return
        msg = json.dumps(event, default=str)
        for ws in list(self._clients):
            try:
                asyncio.create_task(ws.send(msg))
            except Exception:
                self._clients.discard(ws)

    async def _handler(self, websocket: Any) -> None:
        self._clients.add(websocket)
        try:
            await websocket.wait_closed()
        finally:
            self._clients.discard(websocket)

    async def start(self) -> None:
        if not HAS_WEBSOCKETS:
            raise RuntimeError("Install websockets to run the WebSocket server: pip install websockets")
        self._logger = BoundaryEventLogger(
            enabled=True,
            persist_to_file=True,
            log_dir=self.log_dir,
            ws_broadcast=self._broadcast,
        )
        set_global_logger(self._logger)
        self._server = await websockets.serve(self._handler, self.host, self.port, ping_interval=20, ping_timeout=20)
        return self._server  # type: ignore[return-value]

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        if self._logger:
            self._logger.close()


async def run_boundary_ws_server(
    host: str = "127.0.0.1",
    port: int = 8765,
    log_dir: str = "logs/boundaries",
) -> BoundaryWebSocketServer:
    """Run the boundary WebSocket server (blocking until stopped)."""
    s = BoundaryWebSocketServer(host=host, port=port, log_dir=log_dir)
    await s.start()
    return s
