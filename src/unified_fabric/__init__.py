"""
Unified Fabric - Async Event Bus
================================
Dynamic pub/sub event system eliminating synchronous blocking.

Key Features:
- Async publish/subscribe with Redis backend
- Domain-aware routing (safety, grid, coinbase)
- Request-reply pattern for synchronous needs
- Event versioning and schema validation
"""

import asyncio
import json
import logging
import time
import uuid
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Optional

from .domain_routing import expand_domains, infer_domain, normalize_domains, resolve_target_domains
from .event_schemas import validate_event

logger = logging.getLogger(__name__)


class EventDomain(Enum):
    """Event routing domains"""

    SAFETY = "safety"
    GRID = "grid"
    COINBASE = "coinbase"
    ALL = "all"


class EventPriority(Enum):
    """Event priority levels"""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class Event:
    """Base event structure for cross-system communication"""

    event_type: str
    payload: dict[str, Any]
    source_domain: str
    target_domains: list[str] = field(default_factory=lambda: ["all"])
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    priority: int = EventPriority.NORMAL.value
    version: str = "1.0"

    def __post_init__(self) -> None:
        self.source_domain = infer_domain(self.event_type, default=EventDomain.ALL.value)
        self.target_domains = resolve_target_domains(self.target_domains, self.event_type)

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "Event":
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> "Event":
        return cls.from_dict(json.loads(json_str))


@dataclass
class EventResponse:
    """Response to a request-reply event"""

    success: bool
    data: Any = None
    error: str | None = None
    event_id: str = ""
    response_time_ms: float = 0.0


EventHandler = Callable[[Event], Awaitable[EventResponse | None]]


class DynamicEventBus:
    """
    Async event bus for cross-system communication.

    Eliminates dial-up-like blocking by using pub/sub pattern.
    Each component subscribes to relevant events and processes asynchronously.
    """

    def __init__(self, bus_id: str = "unified"):
        self.bus_id = bus_id
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._domain_handlers: dict[str, dict[str, list[EventHandler]]] = defaultdict(lambda: defaultdict(list))
        self._pending_replies: dict[str, asyncio.Future] = {}
        self._event_history: list[Event] = []
        self._max_history = 1000
        self._running = False
        self._queue: asyncio.Queue = asyncio.Queue()
        self._worker_task: asyncio.Task | None = None

        logger.info(f"DynamicEventBus '{bus_id}' initialized")

    async def start(self):
        """Start the event bus worker"""
        if self._running:
            return
        self._running = True
        self._worker_task = asyncio.create_task(self._process_events())
        logger.info(f"EventBus '{self.bus_id}' started")

    async def stop(self):
        """Stop the event bus worker"""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info(f"EventBus '{self.bus_id}' stopped")

    def subscribe(self, event_type: str, handler: EventHandler, domain: str = "all") -> None:
        """
        Subscribe to events of a specific type.

        Args:
            event_type: Event type pattern (supports wildcards: "safety.*")
            handler: Async function to handle events
            domain: Only receive events from this domain
        """
        normalized_domain = (domain or "all").lower()
        if normalized_domain == "all":
            self._handlers[event_type].append(handler)
        else:
            self._domain_handlers[normalized_domain][event_type].append(handler)

        logger.debug(f"Subscribed to '{event_type}' in domain '{domain}'")

    def unsubscribe(self, event_type: str, handler: EventHandler, domain: str = "all") -> None:
        """Unsubscribe from event type"""
        normalized_domain = (domain or "all").lower()
        if normalized_domain == "all":
            if handler in self._handlers[event_type]:
                self._handlers[event_type].remove(handler)
        else:
            if handler in self._domain_handlers[normalized_domain][event_type]:
                self._domain_handlers[normalized_domain][event_type].remove(handler)

    async def publish(self, event: Event, wait_for_handlers: bool = False) -> None:
        """
        Publish event to all subscribers.

        Args:
            event: Event to publish
            wait_for_handlers: If True, wait for all handlers to complete
        """
        event.target_domains = resolve_target_domains(event.target_domains, event.event_type)
        validation = validate_event(event.event_type, event.payload)
        if not validation.is_valid:
            logger.warning(
                "Rejected event '%s': %s",
                event.event_type,
                validation.message,
            )
            return

        # Add to history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)

        if wait_for_handlers:
            await self._dispatch_event(event)
        else:
            await self._queue.put(event)

    async def request_reply(self, event: Event, timeout: float = 5.0) -> EventResponse:
        """
        Send event and wait for response (request-reply pattern).

        Args:
            event: Event to send
            timeout: Max time to wait for response

        Returns:
            EventResponse from handler
        """
        start_time = time.perf_counter()

        # Create future for response
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending_replies[event.event_id] = future

        try:
            # Publish event
            await self.publish(event, wait_for_handlers=True)

            # Wait for response
            response = await asyncio.wait_for(future, timeout=timeout)
            response.response_time_ms = (time.perf_counter() - start_time) * 1000
            return response

        except TimeoutError:
            return EventResponse(
                success=False,
                error=f"Timeout waiting for response after {timeout}s",
                event_id=event.event_id,
                response_time_ms=(time.perf_counter() - start_time) * 1000,
            )
        finally:
            self._pending_replies.pop(event.event_id, None)

    def reply(self, event_id: str, response: EventResponse) -> None:
        """Send reply to a request-reply event"""
        if event_id in self._pending_replies:
            future = self._pending_replies[event_id]
            if not future.done():
                future.set_result(response)

    async def _process_events(self):
        """Background worker to process queued events"""
        while self._running:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=0.1)
                await self._dispatch_event(event)
            except TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Event processing error: {e}")

    async def _dispatch_event(self, event: Event):
        """Dispatch event to matching handlers"""
        handlers_called = 0

        # Get handlers for this event type
        handlers = self._get_matching_handlers(event)

        # Execute handlers concurrently
        tasks = [asyncio.create_task(h(event)) for h in handlers]

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Handler error for {event.event_type}: {result}")
                elif isinstance(result, EventResponse):
                    # If handler returns a response, send reply
                    self.reply(event.event_id, result)

                handlers_called += 1

        logger.debug(f"Event '{event.event_type}' dispatched to {handlers_called} handlers")

    @staticmethod
    def _pattern_match(event_type: str, pattern: str) -> bool:
        if pattern == "*":
            return True
        if pattern.endswith(".*"):
            return event_type.startswith(pattern[:-2])
        return event_type == pattern

    def _get_matching_handlers(self, event: Event) -> list[EventHandler]:
        """Get all handlers matching event type and domain"""
        handlers = []

        # Global handlers (all domains)
        for pattern, pattern_handlers in self._handlers.items():
            if self._pattern_match(event.event_type, pattern):
                handlers.extend(pattern_handlers)

        # Domain-specific handlers
        for domain in expand_domains(event.target_domains):
            domain_handlers = self._domain_handlers[domain]
            for pattern, pattern_handlers in domain_handlers.items():
                if self._pattern_match(event.event_type, pattern):
                    handlers.extend(pattern_handlers)

        return handlers

    def get_event_history(self, limit: int | None = None) -> list[Event]:
        """Return recent event history for replay/debug."""
        if limit:
            return list(self._event_history[-limit:])
        return list(self._event_history)

    async def replay_events(
        self,
        handler: EventHandler,
        event_type: str = "*",
        domain: str = "all",
        limit: int | None = None,
    ) -> int:
        """Replay historical events to a handler for bootstrapping."""
        matched = 0
        history = self.get_event_history(limit)
        normalized_domains = expand_domains(normalize_domains([domain])) if domain != "all" else None
        for event in history:
            if not self._pattern_match(event.event_type, event_type):
                continue
            if normalized_domains and not set(expand_domains(event.target_domains)).intersection(normalized_domains):
                continue
            await handler(event)
            matched += 1
        return matched

    def get_stats(self) -> dict[str, Any]:
        """Get event bus statistics"""
        return {
            "bus_id": self.bus_id,
            "running": self._running,
            "total_handlers": sum(len(h) for h in self._handlers.values()),
            "event_history_size": len(self._event_history),
            "pending_replies": len(self._pending_replies),
            "queue_size": self._queue.qsize(),
        }


# Singleton instance
_event_bus: DynamicEventBus | None = None


def get_event_bus() -> DynamicEventBus:
    """Get the singleton event bus instance"""
    global _event_bus
    if _event_bus is None:
        _event_bus = DynamicEventBus()
    return _event_bus


async def init_event_bus() -> DynamicEventBus:
    """Initialize and start the event bus"""
    bus = get_event_bus()
    await bus.start()
    return bus
