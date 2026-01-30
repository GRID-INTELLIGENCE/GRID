"""
Core Event System for GRID Event-Driven I/O Architecture.

Provides the foundational components for event-driven communication
including the Event data structure, EventBus dispatcher, middleware
support, and event storage for sourcing and replay.

Features:
- Event correlation tracking for request tracing
- Priority-based event dispatch
- Middleware pipeline for cross-cutting concerns
- In-memory event store with query capabilities
- Async and sync event emission
- Subscription management with filtering

Example:
    >>> bus = EventBus()
    >>> bus.subscribe("input:cli:*", handler, priority=EventPriority.HIGH)
    >>> event = Event(type="input:cli:received", data={"command": "analyze"})
    >>> bus.emit(event)
"""

from __future__ import annotations

import asyncio
import logging
import threading
import uuid
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from typing import (
    Any,
    Protocol,
    runtime_checkable,
)

logger = logging.getLogger(__name__)


class EventPriority(IntEnum):
    """Priority levels for event handling."""

    LOWEST = 0
    LOW = 25
    NORMAL = 50
    HIGH = 75
    HIGHEST = 100
    CRITICAL = 200  # System-critical events


@dataclass
class Event:
    """
    Core event data structure with correlation tracking.

    Represents a single event in the GRID event-driven system,
    carrying data, metadata, and tracking information.

    Attributes:
        type: Event type string (e.g., "input:cli:received")
        data: Event payload data
        source: Identifier of the event source
        timestamp: When the event was created
        correlation_id: ID for tracking related events
        causation_id: ID of the event that caused this one
        metadata: Additional event metadata
        priority: Event priority level
        version: Event schema version
    """

    type: str
    data: dict[str, Any]
    source: str
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: str | None = None
    causation_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    priority: EventPriority = EventPriority.NORMAL
    version: str = "1.0"
    _event_id: str | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        """Generate correlation ID if not provided."""
        if self.correlation_id is None:
            self.correlation_id = str(uuid.uuid4())
        if self._event_id is None:
            self._event_id = f"evt-{uuid.uuid4().hex[:12]}"

    @property
    def event_id(self) -> str:
        """Get the unique event ID."""
        return self._event_id or f"evt-{uuid.uuid4().hex[:12]}"

    @property
    def age_ms(self) -> float:
        """Get the age of the event in milliseconds."""
        return (datetime.now() - self.timestamp).total_seconds() * 1000

    def with_causation(self, causation_id: str) -> Event:
        """Create a copy with causation ID set."""
        return Event(
            type=self.type,
            data=self.data.copy(),
            source=self.source,
            timestamp=self.timestamp,
            correlation_id=self.correlation_id,
            causation_id=causation_id,
            metadata=self.metadata.copy(),
            priority=self.priority,
            version=self.version,
        )

    def spawn_child(self, event_type: str, data: dict[str, Any], source: str) -> Event:
        """Create a child event with same correlation ID."""
        return Event(
            type=event_type,
            data=data,
            source=source,
            correlation_id=self.correlation_id,
            causation_id=self.event_id,
            priority=self.priority,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_id": self.event_id,
            "type": self.type,
            "data": self.data,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "metadata": self.metadata,
            "priority": self.priority.value,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Event:
        """Create event from dictionary."""
        return cls(
            type=data["type"],
            data=data.get("data", {}),
            source=data.get("source", "unknown"),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
            correlation_id=data.get("correlation_id"),
            causation_id=data.get("causation_id"),
            metadata=data.get("metadata", {}),
            priority=EventPriority(data.get("priority", EventPriority.NORMAL)),
            version=data.get("version", "1.0"),
        )

    def __hash__(self) -> int:
        """Hash based on event ID."""
        return hash(self.event_id)


@runtime_checkable
class EventMiddleware(Protocol):
    """Protocol for event middleware."""

    def __call__(self, event: Event, next_handler: Callable[[Event], Event]) -> Event:
        """Process event and call next handler."""
        ...


class BaseMiddleware(ABC):
    """Abstract base class for event middleware."""

    @abstractmethod
    def process(self, event: Event) -> Event:
        """Process and potentially transform the event."""
        pass

    def __call__(self, event: Event, next_handler: Callable[[Event], Event]) -> Event:
        """Process event and call next handler."""
        processed = self.process(event)
        return next_handler(processed)


class LoggingMiddleware(BaseMiddleware):
    """Middleware that logs all events."""

    def __init__(self, log_level: int = logging.DEBUG) -> None:
        self.log_level = log_level

    def process(self, event: Event) -> Event:
        """Log the event."""
        logger.log(
            self.log_level,
            "[Event] %s from %s (correlation=%s)",
            event.type,
            event.source,
            event.correlation_id,
        )
        return event


class TimingMiddleware(BaseMiddleware):
    """Middleware that adds timing metadata."""

    def process(self, event: Event) -> Event:
        """Add timing information to event metadata."""
        event.metadata["received_at"] = datetime.now().isoformat()
        event.metadata["event_age_ms"] = event.age_ms
        return event


class ValidationMiddleware(BaseMiddleware):
    """Middleware that validates events."""

    def process(self, event: Event) -> Event:
        """Validate event structure."""
        if not event.type:
            raise ValueError("Event type is required")
        if not event.source:
            raise ValueError("Event source is required")
        if not event.correlation_id:
            event.correlation_id = str(uuid.uuid4())
        return event


@dataclass
class EventSubscription:
    """Represents a subscription to events."""

    subscription_id: str
    event_pattern: str
    handler: Callable[[Event], None]
    priority: EventPriority = EventPriority.NORMAL
    once: bool = False
    filter_fn: Callable[[Event], bool] | None = None
    created_at: datetime = field(default_factory=datetime.now)
    call_count: int = 0

    def matches(self, event_type: str) -> bool:
        """Check if event type matches subscription pattern."""
        pattern = self.event_pattern

        # Exact match
        if pattern == event_type:
            return True

        # Wildcard matching
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            return event_type.startswith(prefix)

        # Category wildcard (e.g., "input:*:*")
        if "*" in pattern:
            pattern_parts = pattern.split(":")
            event_parts = event_type.split(":")

            if len(pattern_parts) != len(event_parts):
                return False

            for p_part, e_part in zip(pattern_parts, event_parts, strict=False):
                if p_part != "*" and p_part != e_part:
                    return False
            return True

        return False


class EventStore:
    """
    In-memory event store for event sourcing and replay.

    Stores events with query capabilities for correlation tracking,
    time-based queries, and event replay.
    """

    def __init__(self, max_events: int = 10000) -> None:
        """
        Initialize event store.

        Args:
            max_events: Maximum events to store (oldest are evicted)
        """
        self.max_events = max_events
        self._events: list[Event] = []
        self._correlation_index: dict[str, list[str]] = {}
        self._type_index: dict[str, list[str]] = {}
        self._lock = threading.Lock()

    def append(self, event: Event) -> None:
        """Add event to store."""
        with self._lock:
            # Evict old events if at capacity
            if len(self._events) >= self.max_events:
                evicted = self._events.pop(0)
                self._remove_from_indexes(evicted)

            self._events.append(event)
            self._add_to_indexes(event)

    def _add_to_indexes(self, event: Event) -> None:
        """Add event to indexes."""
        event_id = event.event_id

        # Correlation index
        if event.correlation_id:
            if event.correlation_id not in self._correlation_index:
                self._correlation_index[event.correlation_id] = []
            self._correlation_index[event.correlation_id].append(event_id)

        # Type index
        if event.type not in self._type_index:
            self._type_index[event.type] = []
        self._type_index[event.type].append(event_id)

    def _remove_from_indexes(self, event: Event) -> None:
        """Remove event from indexes."""
        event_id = event.event_id

        if event.correlation_id and event.correlation_id in self._correlation_index:
            try:
                self._correlation_index[event.correlation_id].remove(event_id)
            except ValueError:
                pass

        if event.type in self._type_index:
            try:
                self._type_index[event.type].remove(event_id)
            except ValueError:
                pass

    def get_by_correlation(self, correlation_id: str) -> list[Event]:
        """Get all events with a correlation ID."""
        with self._lock:
            event_ids = self._correlation_index.get(correlation_id, [])
            return [e for e in self._events if e.event_id in event_ids]

    def get_by_type(self, event_type: str) -> list[Event]:
        """Get all events of a specific type."""
        with self._lock:
            event_ids = self._type_index.get(event_type, [])
            return [e for e in self._events if e.event_id in event_ids]

    def get_by_time_range(
        self,
        start: datetime,
        end: datetime | None = None,
    ) -> list[Event]:
        """Get events within a time range."""
        end = end or datetime.now()
        with self._lock:
            return [e for e in self._events if start <= e.timestamp <= end]

    def get_recent(self, count: int = 100) -> list[Event]:
        """Get most recent events."""
        with self._lock:
            return self._events[-count:]

    def query(
        self,
        event_type: str | None = None,
        correlation_id: str | None = None,
        source: str | None = None,
        limit: int = 100,
    ) -> list[Event]:
        """Query events with filters."""
        with self._lock:
            results = self._events.copy()

            if event_type:
                results = [e for e in results if e.type == event_type]

            if correlation_id:
                results = [e for e in results if e.correlation_id == correlation_id]

            if source:
                results = [e for e in results if e.source == source]

            return results[-limit:]

    def clear(self) -> None:
        """Clear all stored events."""
        with self._lock:
            self._events.clear()
            self._correlation_index.clear()
            self._type_index.clear()

    def __len__(self) -> int:
        """Return number of stored events."""
        return len(self._events)


class EventBus:
    """
    Central event dispatcher with subscription management.

    Handles event routing, filtering, and delivery with support
    for priority-based processing and middleware pipelines.

    Features:
    - Pattern-based subscriptions (wildcards supported)
    - Priority-based handler execution
    - Middleware pipeline for cross-cutting concerns
    - Event store for sourcing and replay
    - Async and sync emission support
    """

    def __init__(
        self,
        store_events: bool = True,
        max_stored_events: int = 10000,
    ) -> None:
        """
        Initialize event bus.

        Args:
            store_events: Whether to store events for replay
            max_stored_events: Maximum events to store
        """
        self._subscriptions: dict[str, EventSubscription] = {}
        self._pattern_subscriptions: dict[str, set[str]] = {}
        self._middleware: list[BaseMiddleware] = []
        self._event_store = EventStore(max_stored_events) if store_events else None
        self._lock = threading.RLock()

        # Statistics
        self._stats = {
            "events_emitted": 0,
            "events_delivered": 0,
            "events_dropped": 0,
            "errors": 0,
        }

        logger.debug("EventBus initialized (store_events=%s)", store_events)

    def subscribe(
        self,
        event_pattern: str,
        handler: Callable[[Event], None],
        priority: EventPriority = EventPriority.NORMAL,
        once: bool = False,
        filter_fn: Callable[[Event], bool] | None = None,
    ) -> str:
        """
        Subscribe to events matching a pattern.

        Args:
            event_pattern: Pattern to match (supports wildcards)
            handler: Function to call when event matches
            priority: Handler priority (higher = called first)
            once: If True, unsubscribe after first delivery
            filter_fn: Optional additional filter function

        Returns:
            Subscription ID
        """
        subscription_id = f"sub-{uuid.uuid4().hex[:8]}"

        subscription = EventSubscription(
            subscription_id=subscription_id,
            event_pattern=event_pattern,
            handler=handler,
            priority=priority,
            once=once,
            filter_fn=filter_fn,
        )

        with self._lock:
            self._subscriptions[subscription_id] = subscription

            if event_pattern not in self._pattern_subscriptions:
                self._pattern_subscriptions[event_pattern] = set()
            self._pattern_subscriptions[event_pattern].add(subscription_id)

        logger.debug("Subscription created: %s -> %s", subscription_id, event_pattern)
        return subscription_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe by subscription ID.

        Args:
            subscription_id: ID returned from subscribe()

        Returns:
            True if unsubscribed successfully
        """
        with self._lock:
            if subscription_id not in self._subscriptions:
                return False

            subscription = self._subscriptions[subscription_id]
            pattern = subscription.event_pattern

            if pattern in self._pattern_subscriptions:
                self._pattern_subscriptions[pattern].discard(subscription_id)

            del self._subscriptions[subscription_id]

        logger.debug("Subscription removed: %s", subscription_id)
        return True

    def add_middleware(self, middleware: BaseMiddleware) -> None:
        """
        Add middleware to the processing pipeline.

        Args:
            middleware: Middleware instance
        """
        self._middleware.append(middleware)
        logger.debug("Middleware added: %s", type(middleware).__name__)

    def emit(self, event: Event) -> None:
        """
        Emit an event to all matching subscribers.

        Args:
            event: Event to emit
        """
        self._stats["events_emitted"] += 1

        # Apply middleware pipeline
        processed_event = self._apply_middleware(event)

        # Store event if enabled
        if self._event_store is not None:
            self._event_store.append(processed_event)

        # Get matching subscriptions
        matching = self._get_matching_subscriptions(processed_event)

        # Sort by priority (highest first)
        matching.sort(key=lambda s: s.priority, reverse=True)

        # Dispatch to handlers
        to_unsubscribe: list[str] = []

        for subscription in matching:
            try:
                # Apply subscription filter if present
                if subscription.filter_fn is not None:
                    if not subscription.filter_fn(processed_event):
                        continue

                subscription.handler(processed_event)
                subscription.call_count += 1
                self._stats["events_delivered"] += 1

                if subscription.once:
                    to_unsubscribe.append(subscription.subscription_id)

            except Exception as e:
                self._stats["errors"] += 1
                logger.error(
                    "Handler error for %s: %s",
                    subscription.subscription_id,
                    e,
                )
                # Emit error event
                self._emit_error_event(processed_event, e)

        # Clean up one-time subscriptions
        for sub_id in to_unsubscribe:
            self.unsubscribe(sub_id)

    async def emit_async(self, event: Event) -> None:
        """
        Emit an event asynchronously.

        Args:
            event: Event to emit
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.emit, event)

    def _apply_middleware(self, event: Event) -> Event:
        """Apply middleware pipeline to event."""
        result = event
        for middleware in self._middleware:
            result = middleware.process(result)
        return result

    def _get_matching_subscriptions(self, event: Event) -> list[EventSubscription]:
        """Get all subscriptions matching an event."""
        matching = []

        with self._lock:
            for _pattern, sub_ids in self._pattern_subscriptions.items():
                for sub_id in sub_ids:
                    subscription = self._subscriptions.get(sub_id)
                    if subscription and subscription.matches(event.type):
                        matching.append(subscription)

        return matching

    def _emit_error_event(self, original_event: Event, error: Exception) -> None:
        """Emit an error event for handler failures."""
        error_event = Event(
            type="system:error:handler_failed",
            data={
                "original_event_type": original_event.type,
                "error": str(error),
                "error_type": type(error).__name__,
            },
            source="event_bus",
            correlation_id=original_event.correlation_id,
            causation_id=original_event.event_id,
            priority=EventPriority.HIGH,
        )
        # Don't recursively emit to avoid infinite loops
        if self._event_store is not None:
            self._event_store.append(error_event)

    def on(
        self,
        event_pattern: str,
        priority: EventPriority = EventPriority.NORMAL,
    ) -> Callable[[Callable[[Event], None]], Callable[[Event], None]]:
        """
        Decorator for subscribing to events.

        Example:
            @bus.on("input:cli:*")
            def handle_cli(event):
                print(event.data)
        """

        def decorator(handler: Callable[[Event], None]) -> Callable[[Event], None]:
            self.subscribe(event_pattern, handler, priority=priority)
            return handler

        return decorator

    def once(
        self,
        event_pattern: str,
        priority: EventPriority = EventPriority.NORMAL,
    ) -> Callable[[Callable[[Event], None]], Callable[[Event], None]]:
        """Decorator for one-time event subscription."""

        def decorator(handler: Callable[[Event], None]) -> Callable[[Event], None]:
            self.subscribe(event_pattern, handler, priority=priority, once=True)
            return handler

        return decorator

    def get_event_store(self) -> EventStore | None:
        """Get the event store."""
        return self._event_store

    def get_stats(self) -> dict[str, Any]:
        """Get event bus statistics."""
        return {
            **self._stats,
            "subscriptions": len(self._subscriptions),
            "patterns": len(self._pattern_subscriptions),
            "stored_events": len(self._event_store) if self._event_store else 0,
            "middleware_count": len(self._middleware),
        }

    def replay_events(
        self,
        correlation_id: str | None = None,
        event_type: str | None = None,
    ) -> int:
        """
        Replay stored events.

        Args:
            correlation_id: Filter by correlation ID
            event_type: Filter by event type

        Returns:
            Number of events replayed
        """
        if self._event_store is None:
            return 0

        events = self._event_store.query(
            event_type=event_type,
            correlation_id=correlation_id,
        )

        for event in events:
            # Mark as replay in metadata
            event.metadata["is_replay"] = True
            self.emit(event)

        return len(events)

    def clear(self) -> None:
        """Clear all subscriptions and stored events."""
        with self._lock:
            self._subscriptions.clear()
            self._pattern_subscriptions.clear()

        if self._event_store is not None:
            self._event_store.clear()

        logger.info("EventBus cleared")

    def __repr__(self) -> str:
        """String representation."""
        return f"EventBus(subscriptions={len(self._subscriptions)}, middleware={len(self._middleware)})"


# ─────────────────────────────────────────────────────────────
# Factory Functions
# ─────────────────────────────────────────────────────────────

_default_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """
    Get the default event bus instance.

    Returns:
        Shared EventBus instance
    """
    global _default_event_bus
    if _default_event_bus is None:
        _default_event_bus = EventBus()
        # Add default middleware
        _default_event_bus.add_middleware(ValidationMiddleware())
        _default_event_bus.add_middleware(TimingMiddleware())
        _default_event_bus.add_middleware(LoggingMiddleware())
    return _default_event_bus


def set_event_bus(bus: EventBus) -> None:
    """
    Set the default event bus instance.

    Args:
        bus: EventBus to use as default
    """
    global _default_event_bus
    _default_event_bus = bus


def emit(event: Event) -> None:
    """
    Emit event using the default bus.

    Args:
        event: Event to emit
    """
    get_event_bus().emit(event)


def subscribe(
    event_pattern: str,
    handler: Callable[[Event], None],
    priority: EventPriority = EventPriority.NORMAL,
) -> str:
    """
    Subscribe to events using the default bus.

    Args:
        event_pattern: Pattern to match
        handler: Handler function
        priority: Handler priority

    Returns:
        Subscription ID
    """
    return get_event_bus().subscribe(event_pattern, handler, priority=priority)
