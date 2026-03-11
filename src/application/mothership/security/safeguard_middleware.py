"""
Safeguard ASGI middleware: enforces security hooks on request/WebSocket lifecycle.

- WebSocket: runs WebSocketAuthHook.validate_connection() before accepting;
  rejects with 4401 if auth missing or per-IP throttle exceeded (TM-002).
- HTTP: no per-request policy run here; startup and auth-path hooks are used instead.
"""

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from .safeguard_hooks import PolicyVerdict, WebSocketAuthHook

logger = logging.getLogger(__name__)


def _get_auth_token_from_scope(scope: dict[str, Any]) -> str | None:
    """Extract Bearer token from scope headers or query string."""
    # ASGI headers are list of (lowercase_name, value) bytes
    headers = scope.get("headers") or []
    for name, value in headers:
        if name == b"authorization" and value.startswith(b"bearer "):
            return value[7:].decode("utf-8", errors="replace").strip()
    # Query string: ?token=xxx
    qs = scope.get("query_string") or b""
    if not qs:
        return None
    for part in qs.decode("utf-8", errors="replace").split("&"):
        if "=" in part:
            k, v = part.split("=", 1)
            if k.strip().lower() == "token":
                return v.strip()
    return None


def _get_client_ip(scope: dict[str, Any]) -> str | None:
    """Get client IP from scope (direct or X-Forwarded-For)."""
    # Headers: x-forwarded-for may be first client
    headers = scope.get("headers") or []
    for name, value in headers:
        if name == b"x-forwarded-for":
            return value.decode("utf-8", errors="replace").strip().split(",")[0].strip()
    client = scope.get("client")
    if client:
        return client[0] if isinstance(client, (list, tuple)) else str(client)
    return None


class SafeguardMiddleware:
    """
    ASGI middleware that runs security safeguard hooks.

    - On WebSocket connect: validates auth and per-IP throttle via WebSocketAuthHook.
      Rejects with close code 4401 and reason when verdict is DENY.
    """

    def __init__(self, app: Callable[..., Awaitable[None]]) -> None:
        self.app = app

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable[[], Awaitable[dict[str, Any]]],
        send: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> None:
        if scope.get("type") != "websocket":
            await self.app(scope, receive, send)
            return

        path = scope.get("path") or ""
        auth_token = _get_auth_token_from_scope(scope)
        client_ip = _get_client_ip(scope)

        result = WebSocketAuthHook.validate_connection(
            auth_token=auth_token,
            client_ip=client_ip,
            path=path,
        )

        if result.verdict == PolicyVerdict.DENY:
            logger.warning(
                "WebSocket connection denied: policy=%s reason=%s path=%s client_ip=%s",
                result.policy_id,
                result.reason,
                path,
                client_ip,
            )
            await send({"type": "websocket.close", "code": 4401, "reason": result.reason[:120]})
            return

        await self.app(scope, receive, send)
