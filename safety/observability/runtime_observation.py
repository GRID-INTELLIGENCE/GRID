"""
Runtime Observation Service.
Unified observation framework for safety and security modules.
"""

from __future__ import annotations

import asyncio
import logging
import queue as stdlib_queue
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from safety.observability.metrics import EVENT_BUS_DROPS_TOTAL, OBSERVATION_PENDING_DEPTH
from safety.observability.risk_score import risk_manager
from safety.observability.security_monitoring import (
    SecurityEvent,
    security_logger,
)

logger = logging.getLogger(__name__)


@dataclass
class RuntimeObservationEvent:
    """Unified event schema for all observation data."""

    # Identification
    event_id: str
    trace_id: str
    timestamp: str
    event_type: str  # String to allow for broader categories than SecurityEventType
    severity: str

    # Context
    source: str
    user_id: str | None = None
    ip_address: str | None = None
    session_id: str | None = None
    request_id: str | None = None

    # Details
    decision: str = "unknown"
    reason: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    risk_score: float = 0.0

    # Metrics
    latency_ms: float = 0.0

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)

    @classmethod
    def from_security_event(cls, event: SecurityEvent, trace_id: str = "unknown") -> RuntimeObservationEvent:
        """Convert from legacy SecurityEvent."""
        return cls(
            event_id=event.event_id,
            trace_id=trace_id,
            timestamp=event.timestamp,
            event_type=event.event_type.value,
            severity=event.severity.value,
            source=event.source,
            user_id=event.user_id,
            ip_address=event.ip_address,
            session_id=event.session_id,
            details=event.details,
            request_id=event.details.get("request_id"),
            decision=event.details.get("decision", "unknown"),
            reason=event.details.get("reason"),
            risk_score=event.risk_score,
        )


_SUBSCRIBER_STALE_SECONDS = 300.0  # 5 minutes


class EventBus:
    """In-memory event bus for streaming with subscriber lifecycle management."""

    def __init__(self):
        # Each subscriber is (queue, last_active_timestamp)
        self._subscribers: list[tuple[asyncio.Queue, float]] = []

    async def publish(self, event: RuntimeObservationEvent):
        """Publish event to all subscribers, reaping stale ones."""
        now = time.monotonic()
        active: list[tuple[asyncio.Queue, float]] = []

        for queue, last_active in self._subscribers:
            if now - last_active > _SUBSCRIBER_STALE_SECONDS:
                logger.info(
                    "event_bus_subscriber_reaped",
                    extra={"age_seconds": round(now - last_active, 1)},
                )
                continue
            try:
                queue.put_nowait(event)
                active.append((queue, now))
            except asyncio.QueueFull:
                EVENT_BUS_DROPS_TOTAL.labels(stage="subscriber").inc()
                logger.warning(
                    "event_bus_subscriber_slow",
                    extra={
                        "event_id": event.event_id,
                        "subscribers": len(self._subscribers),
                    },
                )
                # Keep subscriber but don't refresh its timestamp
                active.append((queue, last_active))

        self._subscribers = active

    async def subscribe(self) -> asyncio.Queue:
        """Subscribe to events. Returns a bounded queue."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self._subscribers.append((queue, time.monotonic()))
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        """Unsubscribe from events."""
        self._subscribers = [(q, t) for q, t in self._subscribers if q is not queue]

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)


class RuntimeObservationService:
    """Unified runtime observation for all safety/security modules.

    Uses a thread-safe stdlib queue to bridge sync security logger callbacks
    into the async event bus and risk score manager, avoiding the broken
    asyncio.get_running_loop() + create_task pattern.
    """

    _PENDING_QUEUE_MAX = 10_000

    def __init__(self):
        self.event_bus = EventBus()
        self._pending_events: stdlib_queue.Queue[SecurityEvent] = stdlib_queue.Queue(maxsize=self._PENDING_QUEUE_MAX)
        self._drain_task: asyncio.Task | None = None
        # Hook into existing security logger
        security_logger.add_listener(self._on_security_event_sync)

    def _on_security_event_sync(self, event: SecurityEvent):
        """Bridge sync logger to async processing via thread-safe queue.

        This is called from sync code (security_logger listeners).
        Instead of gambling on asyncio.get_running_loop(), we put the event
        into a stdlib queue that the async drain loop consumes safely.
        """
        try:
            self._pending_events.put_nowait(event)
        except stdlib_queue.Full:
            EVENT_BUS_DROPS_TOTAL.labels(stage="bridge").inc()
            logger.warning(
                "observation_event_dropped",
                extra={"event_id": event.event_id, "reason": "queue_full"},
            )

    async def start(self):
        """Start the async drain loop. Call from FastAPI lifespan startup."""
        if self._drain_task is None or self._drain_task.done():
            self._drain_task = asyncio.create_task(self._drain_loop())
            logger.info("observation_service_started")

    async def stop(self):
        """Graceful shutdown. Call from FastAPI lifespan shutdown."""
        if self._drain_task and not self._drain_task.done():
            self._drain_task.cancel()
            try:
                await self._drain_task
            except asyncio.CancelledError:
                pass

        # Count and log remaining undrained events
        remaining = 0
        while not self._pending_events.empty():
            try:
                self._pending_events.get_nowait()
                remaining += 1
            except stdlib_queue.Empty:
                break
        if remaining:
            logger.warning("observation_events_dropped_at_shutdown", extra={"count": remaining})
        logger.info("observation_service_stopped")

    async def _drain_loop(self):
        """Async loop that drains the thread-safe queue into the event bus."""
        loop = asyncio.get_running_loop()
        while True:
            try:
                # Block in executor to avoid busy-spinning
                event = await loop.run_in_executor(None, self._pending_events.get, True, 0.5)
            except stdlib_queue.Empty:
                # Timeout — no events, update gauge and loop back
                OBSERVATION_PENDING_DEPTH.set(self._pending_events.qsize())
                continue

            OBSERVATION_PENDING_DEPTH.set(self._pending_events.qsize())
            try:
                obs_event = RuntimeObservationEvent.from_security_event(event)
                await self.event_bus.publish(obs_event)
                await risk_manager.record_violation(event)
            except Exception:
                logger.exception(
                    "observation_processing_error",
                    extra={"event_id": event.event_id},
                )

    async def log_observation(self, event: RuntimeObservationEvent):
        """Log a new observation event."""
        await self.event_bus.publish(event)

    async def get_system_health(self) -> dict[str, Any]:
        """Get health status."""
        return {
            "status": "healthy",
            "subscribers": self.event_bus.subscriber_count,
            "pending_events": self._pending_events.qsize(),
            "drain_active": self._drain_task is not None and not self._drain_task.done(),
            "backend": "redis_streams_and_memory",
        }


# Global Instance
observation_service = RuntimeObservationService()
