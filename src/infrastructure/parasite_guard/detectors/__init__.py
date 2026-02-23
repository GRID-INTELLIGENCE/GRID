"""
Detector implementations for parasitic call patterns.

Detectors follow Protocol interface and implement Chain of Responsibility
for efficient, prioritized detection.
"""

from __future__ import annotations

import asyncio
import logging
import traceback
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Callable
from datetime import UTC, datetime, timezone
from typing import Any, Awaitable, Dict, List, Optional
from weakref import WeakSet

from ..config import GuardMode, ParasiteGuardConfig
from ..models import (
    DetectionResult,
    ParasiteContext,
    ParasiteSeverity,
    SourceMap,
)

logger = logging.getLogger(__name__)


class Detector(ABC):
    """
    Protocol interface for parasite detectors.

    Each detector:
    - Inspects a request/message/component state
    - Returns DetectionResult with ParasiteContext if detected
    - Provides metadata for profiling/tracing
    """

    name: str = "base_detector"
    component: str = "unknown"

    @abstractmethod
    async def __call__(self, request: Any, **kwargs) -> DetectionResult:
        """
        Detect if request/component exhibits parasitic behavior.

        Returns:
            DetectionResult with context if detected, or empty result.
        """
        pass

    def get_source_map(self) -> SourceMap:
        """Capture current call stack location."""
        stack = traceback.extract_stack()
        for frame in reversed(stack):
            if "site-packages" not in frame.filename:
                return SourceMap(
                    module=frame.name,
                    function=frame.name,
                    line=frame.lineno,
                    file=frame.filename,
                )
        return SourceMap(
            module="unknown",
            function="unknown",
            line=0,
            file="unknown",
        )


class DetectorChain:
    """
    Chain of Responsibility for running multiple detectors.

    Detectors run in priority order; stops at first detection.
    """

    def __init__(self, detectors: list[Detector], config: ParasiteGuardConfig):
        self.detectors = detectors
        self.config = config
        self._detection_stats: dict[str, int] = defaultdict(int)

    async def detect(self, request: Any, **kwargs) -> DetectionResult | None:
        """
        Run all detectors in order, return first detection.

        Returns None if no parasites detected.
        """
        if self.config.disabled:
            return None

        for detector in self.detectors:
            # Skip if component not enabled
            if not self.config.is_component_enabled(detector.component):
                continue

            # Skip if mode is DISABLED
            mode = self.config.get_component_mode(detector.component)
            if mode == GuardMode.DISABLED:
                continue

            try:
                start_time = datetime.now(UTC)
                result = await detector(request, **kwargs)
                end_time = datetime.now(UTC)

                # Track detection stats
                if result.detected:
                    self._detection_stats[detector.name] += 1
                    logger.debug(
                        f"Parasite detected by {detector.name}: {result.reason}",
                        extra={
                            "parasite_id": str(result.context.id) if result.context else None,
                            "detector": detector.name,
                            "component": detector.component,
                            "duration_ms": (end_time - start_time).total_seconds() * 1000,
                        },
                    )

                return result

            except Exception as e:
                logger.error(
                    f"Detector {detector.name} failed: {e}",
                    exc_info=True,
                    extra={"detector": detector.name},
                )
                continue

        return DetectionResult(detected=False)

    def get_stats(self) -> dict[str, int]:
        """Get detection statistics."""
        return dict(self._detection_stats)


class WebSocketNoAckDetector(Detector):
    """
    C1: WebSocket No-Ack Detector.

    Detects when websocket.send_text() is called but acknowledgment
    is not awaited within configured timeout, indicating potential
    message loss and state desynchronization.
    """

    name = "websocket_no_ack"
    component = "websocket"

    def __init__(self, config: ParasiteGuardConfig):
        self.config = config
        self._pending_messages: dict[str, datetime] = {}  # message_id → timestamp
        self._ack_timeout_seconds = config.get_component_threshold("websocket", "ack_timeout", default=3)

    async def __call__(self, request: Any, **kwargs) -> DetectionResult:
        """
        Check for unacknowledged WebSocket messages.

        Expected request structure (from WebSocket wrapper):
        - request.state.websocket: WebSocket connection
        - request.state.last_send_id: Last message ID sent
        - request.state.last_ack_id: Last message ID acknowledged
        """
        # Get WebSocket from request state
        websocket = getattr(getattr(request, "state", None), "websocket", None)
        if not websocket:
            return DetectionResult(detected=False)

        # Check for pending message tracking
        last_send_id = kwargs.get("last_send_id")
        last_ack_id = kwargs.get("last_ack_id")

        if last_send_id and last_ack_id is None:
            # Message sent, not yet acknowledged
            send_time = kwargs.get("send_time")
            if send_time:
                elapsed = (datetime.now(UTC) - send_time).total_seconds()

                if elapsed > self._ack_timeout_seconds:
                    # No-ack detected
                    context = ParasiteContext(
                        id=kwargs.get("message_id"),
                        component=self.component,
                        pattern="no_ack",
                        rule=self.name,
                        severity=ParasiteSeverity.CRITICAL,
                        source=self.get_source_map(),
                        detection_metadata={
                            "connection_id": kwargs.get("connection_id"),
                            "message_id": last_send_id,
                            "timeout_seconds": self._ack_timeout_seconds,
                            "elapsed_seconds": elapsed,
                            "send_time": send_time.isoformat(),
                        },
                    )

                    return DetectionResult(
                        detected=True,
                        context=context,
                        reason=f"WebSocket message {last_send_id} not acknowledged after {elapsed:.2f}s (timeout: {self._ack_timeout_seconds}s)",
                        confidence=0.95,
                    )

        # Track message if sent
        if last_send_id:
            self._pending_messages[last_send_id] = kwargs.get("send_time", datetime.now(UTC))

        # Cleanup acknowledged messages
        if last_ack_id:
            self._pending_messages.pop(last_ack_id, None)

        return DetectionResult(detected=False)

    def cleanup_connection(self, connection_id: str):
        """Cleanup pending messages for disconnected WebSocket."""
        # In production, this would filter by connection_id
        pass


class EventSubscriptionLeakDetector(Detector):
    """
    C2: Event Bus Subscription Leak Detector.

    Detects when event subscriptions accumulate beyond threshold,
    indicating potential memory leak from unmanaged subscriptions.
    """

    name = "event_subscription_leak"
    component = "eventbus"

    def __init__(self, config: ParasiteGuardConfig):
        self.config = config
        self._leak_threshold = config.get_component_threshold("eventbus", "leak_threshold", default=1000)
        self._event_bus = None  # Will be set via set_event_bus()

    def set_event_bus(self, event_bus: Any):
        """Set reference to event bus for inspection."""
        self._event_bus = event_bus

    async def __call__(self, request: Any, **kwargs) -> DetectionResult:
        """
        Check event bus for subscription leak.

        Expected event_bus structure:
        - event_bus._subscribers: Dict[str, List[Subscription]]
        - event_bus._active_subscriptions: Counter
        """
        if not self._event_bus:
            return DetectionResult(detected=False)

        try:
            # Get total subscription count
            total_subs = 0

            # Check WeakSet-based subscribers (event_system_fixed.py)
            if hasattr(self._event_bus, "_subscribers"):
                for subscribers in self._event_bus._subscribers.values():
                    total_subs += len(subscribers)

            # Check active subscriptions gauge
            elif hasattr(self._event_bus, "_active_subscriptions"):
                total_subs = sum(
                    self._event_bus._active_subscriptions.labels(event_type=et)._value.get()
                    for et in ["*"] or list(self._event_bus._active_subscriptions._metrics)
                )

            # Check if leak detected
            if total_subs > self._leak_threshold:
                context = ParasiteContext(
                    component=self.component,
                    pattern="subscription_leak",
                    rule=self.name,
                    severity=ParasiteSeverity.CRITICAL,
                    source=self.get_source_map(),
                    detection_metadata={
                        "total_subscriptions": total_subs,
                        "leak_threshold": self._leak_threshold,
                        "excess": total_subs - self._leak_threshold,
                        "top_events": self._get_top_event_types(),
                    },
                )

                return DetectionResult(
                    detected=True,
                    context=context,
                    reason=f"Event bus subscription leak: {total_subs} active subscriptions (threshold: {self._leak_threshold})",
                    confidence=0.90,
                )

        except Exception as e:
            logger.warning(f"Event bus inspection failed: {e}", exc_info=True)

        return DetectionResult(detected=False)

    def _get_top_event_types(self) -> list[dict[str, int]]:
        """Get event types with most subscriptions."""
        if not self._event_bus or not hasattr(self._event_bus, "_subscribers"):
            return []

        sorted_events = sorted(
            [{"event_type": et, "count": len(subs)} for et, subs in self._event_bus._subscribers.items()],
            key=lambda x: x["count"],
            reverse=True,
        )
        return sorted_events[:5]


class DBConnectionOrphanDetector(Detector):
    """
    C3: DB Connection Orphan Detector.

    Detects when DB connection pool size exceeds expected maximum,
    indicating orphaned connections not properly disposed.
    """

    name = "db_connection_orphan"
    component = "db"

    def __init__(self, config: ParasiteGuardConfig):
        self.config = config
        self._max_pool_size = config.get_component_threshold("db", "max_pool_size", default=30)
        self._db_engine = None  # Will be set via set_db_engine()

    def set_db_engine(self, engine: Any):
        """Set reference to DB engine for inspection."""
        self._db_engine = engine

    async def __call__(self, request: Any, **kwargs) -> DetectionResult:
        """
        Check DB connection pool for orphaned connections.

        Expected engine structure:
        - engine.pool.size(): Current pool size
        - engine.pool.checkedout(): Number of checked out connections
        """
        if not self._db_engine:
            return DetectionResult(detected=False)

        try:
            pool = getattr(self._db_engine, "pool", None)
            if not pool:
                return DetectionResult(detected=False)

            pool_size = getattr(pool, "size", lambda: 0)()
            checked_out = getattr(pool, "checkedout", lambda: 0)()

            # Check if orphan detected
            if pool_size > self._max_pool_size:
                context = ParasiteContext(
                    component=self.component,
                    pattern="connection_orphan",
                    rule=self.name,
                    severity=ParasiteSeverity.CRITICAL,
                    source=self.get_source_map(),
                    detection_metadata={
                        "pool_size": pool_size,
                        "checked_out": checked_out,
                        "max_pool_size": self._max_pool_size,
                        "excess": pool_size - self._max_pool_size,
                    },
                )

                return DetectionResult(
                    detected=True,
                    context=context,
                    reason=f"DB connection orphan: pool size {pool_size} exceeds maximum {self._max_pool_size}",
                    confidence=0.85,
                )

        except Exception as e:
            logger.warning(f"DB engine inspection failed: {e}", exc_info=True)

        return DetectionResult(detected=False)
