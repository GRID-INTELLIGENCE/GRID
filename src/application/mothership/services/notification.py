"""
Notification Dispatcher Service.

Centralised alert notification layer. Decouples alert creation
(mothership models/AlertService) from delivery channels (log, webhook, email).

Design:
- Handlers are registered per channel; multiple handlers can coexist.
- Each handler receives a normalised NotificationPayload.
- Delivery is best-effort: handler failures are logged but do not propagate.
- Channel filtering: each alert severity maps to a minimum channel threshold.

TDC-20260314-0007: Refactor notification service
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import IntEnum
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Severity threshold mapping
# ---------------------------------------------------------------------------


class ChannelThreshold(IntEnum):
    """Minimum alert severity required to fire a channel."""

    CRITICAL = 4
    HIGH = 3
    MEDIUM = 2
    LOW = 1
    ALL = 0


_SEVERITY_RANK: dict[str, int] = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
    "info": 0,
}


# ---------------------------------------------------------------------------
# Payload
# ---------------------------------------------------------------------------


@dataclass
class NotificationPayload:
    """Normalised notification passed to every handler."""

    alert_id: str
    title: str
    message: str
    severity: str
    source: str = "mothership"
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def severity_rank(self) -> int:
        return _SEVERITY_RANK.get(self.severity.lower(), 0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "title": self.title,
            "message": self.message,
            "severity": self.severity,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Handler interface
# ---------------------------------------------------------------------------


class NotificationHandler(ABC):
    """Abstract notification delivery handler."""

    @property
    @abstractmethod
    def channel(self) -> str:
        """Unique channel identifier (e.g. 'log', 'webhook', 'email')."""

    @property
    def threshold(self) -> ChannelThreshold:
        """Minimum severity rank to trigger this handler."""
        return ChannelThreshold.ALL

    @abstractmethod
    async def send(self, payload: NotificationPayload) -> bool:
        """Deliver the notification. Returns True on success."""


# ---------------------------------------------------------------------------
# Built-in handlers
# ---------------------------------------------------------------------------


class LogHandler(NotificationHandler):
    """Delivers notifications to the Python logging system."""

    @property
    def channel(self) -> str:
        return "log"

    @property
    def threshold(self) -> ChannelThreshold:
        return ChannelThreshold.ALL

    async def send(self, payload: NotificationPayload) -> bool:
        level = {
            "critical": logging.CRITICAL,
            "high": logging.ERROR,
            "medium": logging.WARNING,
            "low": logging.INFO,
        }.get(payload.severity.lower(), logging.INFO)

        logger.log(
            level,
            "[ALERT/%s] %s — %s (id=%s, source=%s)",
            payload.severity.upper(),
            payload.title,
            payload.message,
            payload.alert_id,
            payload.source,
        )
        return True


class WebhookHandler(NotificationHandler):
    """Delivers notifications to an HTTP webhook endpoint."""

    def __init__(
        self,
        url: str,
        threshold: ChannelThreshold = ChannelThreshold.HIGH,
        timeout: float = 10.0,
        headers: dict[str, str] | None = None,
    ):
        self._url = url
        self._threshold = threshold
        self._timeout = timeout
        self._headers = headers or {"Content-Type": "application/json"}

    @property
    def channel(self) -> str:
        return "webhook"

    @property
    def threshold(self) -> ChannelThreshold:
        return self._threshold

    async def send(self, payload: NotificationPayload) -> bool:
        try:
            import httpx

            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    self._url,
                    json=payload.to_dict(),
                    headers=self._headers,
                )
                return resp.status_code < 400
        except Exception as exc:
            logger.warning("WebhookHandler delivery failed to %s: %s", self._url, exc)
            return False


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------


class NotificationDispatcher:
    """
    Centralised notification dispatcher.

    Usage:
        dispatcher = NotificationDispatcher()
        dispatcher.register(LogHandler())
        dispatcher.register(WebhookHandler("https://hooks.example.com/grid"))
        await dispatcher.dispatch(payload)
    """

    def __init__(self) -> None:
        self._handlers: list[NotificationHandler] = []

    def register(self, handler: NotificationHandler) -> None:
        """Register a delivery handler."""
        self._handlers.append(handler)
        logger.debug("NotificationDispatcher: registered channel '%s'", handler.channel)

    def unregister(self, channel: str) -> None:
        """Remove all handlers for a channel."""
        before = len(self._handlers)
        self._handlers = [h for h in self._handlers if h.channel != channel]
        removed = before - len(self._handlers)
        if removed:
            logger.debug("NotificationDispatcher: removed %d handler(s) for channel '%s'", removed, channel)

    async def dispatch(self, payload: NotificationPayload) -> dict[str, bool]:
        """
        Fan-out delivery to all eligible handlers.

        A handler fires only when payload.severity_rank >= handler.threshold.
        Handler failures are caught individually — one failure does not block others.

        Returns:
            Dict mapping channel name to delivery success.
        """
        results: dict[str, bool] = {}

        for handler in self._handlers:
            if payload.severity_rank < handler.threshold:
                continue
            try:
                ok = await handler.send(payload)
            except Exception as exc:
                logger.error(
                    "NotificationDispatcher: unhandled error in channel '%s': %s",
                    handler.channel,
                    exc,
                )
                ok = False
            results[handler.channel] = ok

        if not results:
            logger.debug("NotificationDispatcher: no handlers fired for severity='%s'", payload.severity)

        return results

    async def dispatch_alert(
        self,
        alert_id: str,
        title: str,
        message: str,
        severity: str,
        source: str = "mothership",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, bool]:
        """Convenience method: build payload and dispatch."""
        payload = NotificationPayload(
            alert_id=alert_id,
            title=title,
            message=message,
            severity=severity,
            source=source,
            metadata=metadata or {},
        )
        return await self.dispatch(payload)

    @property
    def registered_channels(self) -> list[str]:
        """Return list of registered channel names."""
        return [h.channel for h in self._handlers]


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------

_dispatcher: NotificationDispatcher | None = None


def get_notification_dispatcher() -> NotificationDispatcher:
    """Get or create the global notification dispatcher with default handlers."""
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = NotificationDispatcher()
        _dispatcher.register(LogHandler())
        logger.info("NotificationDispatcher initialised with LogHandler")
    return _dispatcher


def reset_notification_dispatcher() -> None:
    """Reset the global dispatcher (for testing)."""
    global _dispatcher
    _dispatcher = None
