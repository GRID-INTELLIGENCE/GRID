"""
Event-Driven Architecture System for Arena Modernization
======================================================

Transforms the dial-up-like synchronous architecture into an asynchronous,
event-driven system with proper separation of concerns and dynamic integration.
"""

import asyncio
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, TypeVar

import aio_pika  # type: ignore[import-not-found]
import aiofiles  # type: ignore[import-not-found,import-untyped]
import redis.asyncio as redis
from aio_pika import DeliveryMode, ExchangeType, Message

try:
    from prometheus_client import REGISTRY, Counter, Gauge

    def get_or_create_counter(name, documentation, **kwargs):
        if name in REGISTRY._names_to_collectors:
            return REGISTRY._names_to_collectors[name]
        return Counter(name, documentation, **kwargs)

    def get_or_create_gauge(name, documentation, **kwargs):
        if name in REGISTRY._names_to_collectors:
            return REGISTRY._names_to_collectors[name]
        return Gauge(name, documentation, **kwargs)

    _subscriptions_created = get_or_create_counter("eventbus_subscriptions_created_total", "Total subscriptions created")
    _subscriptions_removed = get_or_create_counter("eventbus_subscriptions_removed_total", "Total subscriptions removed")
    _active_subscriptions = get_or_create_gauge("eventbus_active_subscriptions", "Active subscriptions", labelnames=["event_type"])
    METRICS_ENABLED = True
except ImportError:
    METRICS_ENABLED = False
except Exception:
    METRICS_ENABLED = False

T = TypeVar("T")


class EventPriority(Enum):
    """Event priority levels."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class EventStatus(Enum):
    """Event processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class Event:
    """Base event structure."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""
    source: str = ""
    timestamp: float = field(default_factory=time.time)
    data: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    priority: EventPriority = EventPriority.NORMAL
    correlation_id: str | None = None
    causation_id: str | None = None  # Event that caused this event
    retry_count: int = 0
    max_retries: int = 3
    timeout: float = 30.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["priority"] = self.priority.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Event":
        """Create from dictionary."""
        data["priority"] = EventPriority(data["priority"])
        return cls(**data)


@dataclass
class EventResult:
    """Event processing result."""

    event_id: str
    status: EventStatus
    result: dict[str, Any] | None = None
    error: str | None = None
    processing_time: float = 0.0
    timestamp: float = field(default_factory=time.time)


@dataclass(frozen=True)
class Subscription:
    """
    Immutable handle representing a subscription.

    Provides a convenient interface for managing subscription lifecycle.

    Attributes:
        event_type: The event type this subscription listens to.
        handler: The callback function to invoke.
        id: Unique subscription identifier.
        created_at: When the subscription was created.
    """

    event_type: str = field(compare=False)
    handler: Callable[..., Any] = field(compare=False)
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: float = field(default_factory=time.time, compare=False)

    async def unsubscribe(self) -> bool:
        """Unsubscribe this subscription."""
        return await unsubscribe(self)

    def to_dict(self) -> dict[str, Any]:
        """Serialize subscription to dictionary (excluding handler)."""
        return {
            "id": str(self.id),
            "event_type": self.event_type,
            "created_at": self.created_at,
            "handler_name": getattr(self.handler, "__name__", str(self.handler)),
        }


class EventHandler[T](ABC):
    """Abstract event handler."""

    @abstractmethod
    async def handle(self, event: Event) -> EventResult:
        """Handle an event."""
        pass

    @property
    @abstractmethod
    def event_types(self) -> list[str]:
        """List of event types this handler can process."""
        pass

    @property
    def name(self) -> str:
        """Handler name."""
        return self.__class__.__name__


class EventStore:
    """Event store for persistence and replay."""

    def __init__(self, storage_path: str = "events"):
        self.storage_path = storage_path
        self.events: dict[str, Event] = {}
        self.results: dict[str, EventResult] = {}
        self._lock = asyncio.Lock()

    async def store_event(self, event: Event) -> bool:
        """Store an event."""
        async with self._lock:
            self.events[event.id] = event
            await self._persist_event(event)
            return True

    async def store_result(self, result: EventResult) -> bool:
        """Store event result."""
        async with self._lock:
            self.results[result.event_id] = result
            await self._persist_result(result)
            return True

    async def get_event(self, event_id: str) -> Event | None:
        """Get an event by ID."""
        return self.events.get(event_id)

    async def get_result(self, event_id: str) -> EventResult | None:
        """Get event result by ID."""
        return self.results.get(event_id)

    async def get_events_by_type(self, event_type: str, limit: int = 100) -> list[Event]:
        """Get events by type."""
        events = [event for event in self.events.values() if event.type == event_type]
        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events[:limit]

    async def get_events_by_source(self, source: str, limit: int = 100) -> list[Event]:
        """Get events by source."""
        events = [event for event in self.events.values() if event.source == source]
        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events[:limit]

    async def replay_events(self, event_type: str | None = None) -> list[Event]:
        """Replay events for recovery."""
        events = list(self.events.values())

        if event_type:
            events = [e for e in events if e.type == event_type]

        events.sort(key=lambda e: e.timestamp)
        return events

    async def _persist_event(self, event: Event):
        """Persist event to disk."""
        try:
            filename = f"{self.storage_path}/events/{event.id}.json"
            async with aiofiles.open(filename, "w") as f:
                await f.write(json.dumps(event.to_dict(), indent=2))
        except Exception as e:
            logging.error(f"Failed to persist event: {e}")

    async def _persist_result(self, result: EventResult):
        """Persist result to disk."""
        try:
            filename = f"{self.storage_path}/results/{result.event_id}.json"
            async with aiofiles.open(filename, "w") as f:
                await f.write(json.dumps(asdict(result), indent=2))
        except Exception as e:
            logging.error(f"Failed to persist result: {e}")


class EventRouter:
    """Event router for dispatching events to handlers."""

    def __init__(self):
        self.handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self.global_handlers: list[EventHandler] = []
        self.middleware: list[Callable] = []

    def register_handler(self, handler: EventHandler):
        """Register an event handler."""
        for event_type in handler.event_types:
            self.handlers[event_type].append(handler)

        logging.info(f"Registered handler: {handler.name} for {handler.event_types}")

    def register_global_handler(self, handler: EventHandler):
        """Register a global handler for all events."""
        self.global_handlers.append(handler)
        logging.info(f"Registered global handler: {handler.name}")

    def add_middleware(self, middleware: Callable):
        """Add middleware for event processing."""
        self.middleware.append(middleware)

    async def route_event(self, event: Event) -> list[EventResult]:
        """Route event to appropriate handlers."""
        results = []

        # Apply middleware
        for middleware in self.middleware:
            event = await middleware(event)

        # Get handlers for this event type
        handlers = self.handlers.get(event.type, [])

        # Add global handlers
        handlers.extend(self.global_handlers)

        # Process event with all handlers
        tasks = []
        for handler in handlers:
            task = asyncio.create_task(self._handle_with_error(handler, event))
            tasks.append(task)

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and convert to EventResult
        final_results = []
        for result in results:
            if isinstance(result, Exception):
                final_results.append(EventResult(event_id=event.id, status=EventStatus.FAILED, error=str(result)))
            elif isinstance(result, EventResult):
                final_results.append(result)

        return final_results

    async def _handle_with_error(self, handler: EventHandler, event: Event) -> EventResult:
        """Handle event with error catching."""
        try:
            return await handler.handle(event)
        except Exception as e:
            logging.error(f"Handler {handler.name} failed for event {event.id}: {e}")
            return EventResult(event_id=event.id, status=EventStatus.FAILED, error=str(e))


class EventBus:
    """
    Main event bus for the event-driven architecture.

    Singleton pattern with thread-safe operations for parasitic leak prevention.
    """

    _instance: "EventBus | None" = None
    _lock: asyncio.Lock = asyncio.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "EventBus":
        """Prevent direct instantiation - use get_eventbus() instead."""
        raise RuntimeError("Use get_eventbus() to get EventBus instance")

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        rabbitmq_url: str = "amqp://localhost:5672",
        storage_path: str = "events",
    ):
        self.redis_client: redis.Redis | None = None
        self.rabbitmq_connection: aio_pika.Connection | None = None
        self.channel: aio_pika.Channel | None = None
        self.exchange: aio_pika.Exchange | None = None

        self.event_store = EventStore(storage_path)
        self.event_router = EventRouter()

        self.redis_url = redis_url
        self.rabbitmq_url = rabbitmq_url

        # Thread-safe subscription storage
        self._subscribers: dict[str, list[Subscription]] = defaultdict(list)
        self._index: dict[uuid.UUID, tuple[str, int]] = {}  # O(1) removal index
        self._state_lock = asyncio.Lock()

        self.running = False

        # Metrics
        self.events_processed = 0
        self.events_failed = 0
        self.processing_times: list[float] = []

    @classmethod
    async def get_eventbus(cls, *args: Any, **kwargs: Any) -> "EventBus":
        """Get singleton EventBus instance."""
        async with cls._lock:
            if cls._instance is None:
                # Bypass __new__ by calling object.__new__
                instance = object.__new__(cls)
                instance.__init__(*args, **kwargs)
                cls._instance = instance
            return cls._instance

    async def start(self):
        """Start the event bus."""
        # Initialize Redis
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logging.info("Redis connected to event bus")
        except Exception as e:
            logging.error(f"Failed to connect to Redis: {e}")

        # Initialize RabbitMQ
        try:
            self.rabbitmq_connection = await aio_pika.connect_robust(self.rabbitmq_url)
            self.channel = await self.rabbitmq_connection.channel()

            # Declare exchange
            self.exchange = await self.channel.declare_exchange("arena_events", ExchangeType.TOPIC, durable=True)

            logging.info("RabbitMQ connected to event bus")
        except Exception as e:
            logging.error(f"Failed to connect to RabbitMQ: {e}")

        # Create storage directories
        import os

        os.makedirs(f"{self.event_store.storage_path}/events", exist_ok=True)
        os.makedirs(f"{self.event_store.storage_path}/results", exist_ok=True)

        self.running = True
        logging.info("Event bus started")

    async def stop(self):
        """Stop the event bus."""
        self.running = False

        if self.rabbitmq_connection:
            await self.rabbitmq_connection.close()

        if self.redis_client:
            await self.redis_client.close()

        logging.info("Event bus stopped")

    async def publish(
        self,
        event_type: str,
        data: dict[str, Any],
        source: str = "unknown",
        priority: EventPriority = EventPriority.NORMAL,
        correlation_id: str | None = None,
        routing_key: str | None = None,
    ) -> str:
        """Publish an event."""
        event = Event(
            type=event_type,
            source=source,
            data=data,
            priority=priority,
            correlation_id=correlation_id,
            metadata={"routing_key": routing_key or event_type},
        )

        # Store event
        await self.event_store.store_event(event)

        # Route to local handlers
        results = await self.event_router.route_event(event)

        # Store results
        for result in results:
            await self.event_store.store_result(result)
            if result.status == EventStatus.COMPLETED:
                self.events_processed += 1
            else:
                self.events_failed += 1

        # Publish to RabbitMQ
        if self.exchange:
            try:
                message = Message(
                    json.dumps(event.to_dict()).encode(),
                    content_type="application/json",
                    delivery_mode=DeliveryMode.PERSISTENT,
                    headers={"priority": event.priority.value},
                )

                routing_key = routing_key or event_type
                await self.exchange.publish(message, routing_key=routing_key)

                logging.debug(f"Published event {event.id} to RabbitMQ")
            except Exception as e:
                logging.error(f"Failed to publish to RabbitMQ: {e}")

        # Publish to Redis for real-time subscribers
        if self.redis_client:
            try:
                await self.redis_client.publish(f"events:{event_type}", json.dumps(event.to_dict()))
            except Exception as e:
                logging.error(f"Failed to publish to Redis: {e}")

        return event.id

    async def subscribe(self, event_type: str, handler: Callable) -> Subscription:
        """
        Subscribe to events with thread-safe operations.

        Returns a Subscription handle for unsubscription.
        """
        sub = Subscription(event_type=event_type, handler=handler)

        # Async-safe modification with lock
        async with self._state_lock:
            # Add to subscribers list
            self._subscribers[event_type].append(sub)

            # Add to index for O(1) removal
            self._index[sub.id] = (event_type, len(self._subscribers[event_type]) - 1)

            # Update metrics
            if METRICS_ENABLED:
                _subscriptions_created.inc()
                _active_subscriptions.labels(event_type=event_type).inc()

        logging.info(f"Subscribed to {event_type} (id={sub.id})")
        return sub

    async def unsubscribe(self, subscription: Subscription | uuid.UUID) -> bool:
        """
        Unsubscribe a handler with O(1) index lookup.

        Returns True if successful, False if subscription not found.
        """
        sub_id = subscription.id if isinstance(subscription, Subscription) else subscription

        async with self._state_lock:
            if sub_id not in self._index:
                logging.warning(f"Attempted to unsubscribe unknown subscription {sub_id}")
                return False

            event_type, index = self._index[sub_id]

            # Remove from subscribers list
            if index < len(self._subscribers[event_type]):
                self._subscribers[event_type].pop(index)

                # Rebuild index for remaining subscriptions
                for i, sub in enumerate(self._subscribers[event_type]):
                    self._index[sub.id] = (event_type, i)

            # Clean up index
            del self._index[sub_id]

            # Update metrics
            if METRICS_ENABLED:
                _subscriptions_removed.inc()
                _active_subscriptions.labels(event_type=event_type).dec()

        logging.info(f"Unsubscribed {sub_id}")
        return True

    async def subscribe_to_pattern(self, pattern: str, handler: Callable):
        """Subscribe to event patterns (Redis pub/sub)."""
        if self.redis_client:
            pubsub = self.redis_client.pubsub()
            await pubsub.psubscribe(f"events:{pattern}")

            async def listener():
                async for message in pubsub.listen():
                    if message["type"] == "pmessage":
                        try:
                            event_data = json.loads(message["data"])
                            event = Event.from_dict(event_data)
                            await handler(event)
                        except Exception as e:
                            logging.error(f"Pattern subscriber error: {e}")

            asyncio.create_task(listener())

    def register_handler(self, handler: EventHandler):
        """Register an event handler."""
        self.event_router.register_handler(handler)

    def register_global_handler(self, handler: EventHandler):
        """Register a global handler."""
        self.event_router.register_global_handler(handler)

    async def get_metrics(self) -> dict[str, Any]:
        """Get event bus metrics."""
        async with self._state_lock:
            total_subs = sum(len(subs) for subs in self._subscribers.values())
            subs_by_type = {k: len(v) for k, v in self._subscribers.items()}

        return {
            "events_processed": self.events_processed,
            "events_failed": self.events_failed,
            "success_rate": (
                self.events_processed / (self.events_processed + self.events_failed)
                if (self.events_processed + self.events_failed) > 0
                else 0
            ),
            "average_processing_time": (
                sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0
            ),
            "handlers_registered": len(self.event_router.handlers),
            "total_subscriptions": total_subs,
            "subscriptions_by_type": subs_by_type,
        }

    async def get_subscription_count(self, event_type: str | None = None) -> int:
        """Get count of active subscriptions.

        Args:
            event_type: Optional event type to filter by.

        Returns:
            Number of active subscriptions.
        """
        async with self._state_lock:
            if event_type:
                return len(self._subscribers.get(event_type, []))
            return sum(len(subs) for subs in self._subscribers.values())

    async def get_subscriptions(self, event_type: str | None = None) -> list[Subscription]:
        """Get list of active subscriptions.

        Args:
            event_type: Optional event type to filter by.

        Returns:
            List of Subscription objects.
        """
        async with self._state_lock:
            if event_type:
                return list(self._subscribers.get(event_type, []))
            all_subs = []
            for subs in self._subscribers.values():
                all_subs.extend(subs)
            return all_subs

    async def clear_all(self) -> int:
        """Clear all subscriptions.

        Returns:
            Number of subscriptions cleared.
        """
        async with self._state_lock:
            total = sum(len(subs) for subs in self._subscribers.values())
            self._subscribers.clear()
            self._index.clear()

            if METRICS_ENABLED:
                _subscriptions_removed.inc(total)

            logging.info(f"Cleared {total} subscriptions")
            return total

    async def clear_stale_subscriptions(self, max_age_seconds: float = 3600) -> int:
        """Clear subscriptions older than max_age_seconds.

        Args:
            max_age_seconds: Maximum age in seconds (default: 1 hour).

        Returns:
            Number of stale subscriptions cleared.
        """
        now = time.time()
        stale_ids: list[uuid.UUID] = []

        async with self._state_lock:
            for event_type, subs in self._subscribers.items():
                for sub in subs:
                    if now - sub.created_at > max_age_seconds:
                        stale_ids.append(sub.id)

        # Unsubscribe stale subscriptions outside the lock
        cleared = 0
        for sub_id in stale_ids:
            if await self.unsubscribe(sub_id):
                cleared += 1

        if cleared > 0:
            logging.warning(f"Cleared {cleared} stale subscriptions (older than {max_age_seconds}s)")

        return cleared


# ============================================================================
# Example Event Handlers
# ============================================================================


class PortfolioUpdateHandler(EventHandler):
    """Handler for portfolio update events."""

    @property
    def event_types(self) -> list[str]:
        return ["portfolio.updated", "portfolio.created"]

    async def handle(self, event: Event) -> EventResult:
        """Handle portfolio update."""
        start_time = time.time()

        try:
            # Process portfolio update

            # Update analytics
            # Send notifications
            # Update caches

            processing_time = time.time() - start_time

            return EventResult(
                event_id=event.id,
                status=EventStatus.COMPLETED,
                result={"processed": True},
                processing_time=processing_time,
            )

        except Exception as e:
            return EventResult(
                event_id=event.id, status=EventStatus.FAILED, error=str(e), processing_time=time.time() - start_time
            )


class TradingSignalHandler(EventHandler):
    """Handler for trading signal events."""

    @property
    def event_types(self) -> list[str]:
        return ["trading.signal.generated", "trading.signal.executed"]

    async def handle(self, event: Event) -> EventResult:
        """Handle trading signal."""
        start_time = time.time()

        try:
            # Validate signal
            # Check risk limits
            # Execute trade if approved

            processing_time = time.time() - start_time

            return EventResult(
                event_id=event.id,
                status=EventStatus.COMPLETED,
                result={"signal_processed": True},
                processing_time=processing_time,
            )

        except Exception as e:
            return EventResult(
                event_id=event.id, status=EventStatus.FAILED, error=str(e), processing_time=time.time() - start_time
            )


# ============================================================================
# Module-level API
# ============================================================================

_eventbus_instance: EventBus | None = None
_eventbus_lock = asyncio.Lock()


async def get_eventbus(*args: Any, **kwargs: Any) -> EventBus:
    """Get or create the singleton EventBus instance."""
    global _eventbus_instance
    async with _eventbus_lock:
        if _eventbus_instance is None:
            _eventbus_instance = await EventBus.get_eventbus(*args, **kwargs)
        return _eventbus_instance


async def subscribe(event_type: str, handler: Callable) -> Subscription:
    """Subscribe to events using the singleton EventBus."""
    bus = await get_eventbus()
    return await bus.subscribe(event_type, handler)


async def unsubscribe(subscription: Subscription | uuid.UUID) -> bool:
    """Unsubscribe using the singleton EventBus."""
    bus = await get_eventbus()
    return await bus.unsubscribe(subscription)


async def publish(
    event_type: str,
    data: dict[str, Any],
    source: str = "unknown",
    priority: EventPriority = EventPriority.NORMAL,
    correlation_id: str | None = None,
    routing_key: str | None = None,
) -> str:
    """Publish an event using the singleton EventBus."""
    bus = await get_eventbus()
    return await bus.publish(event_type, data, source, priority, correlation_id, routing_key)


async def clear_all() -> None:
    """Clear all subscriptions using the singleton EventBus."""
    bus = await get_eventbus()
    await bus.clear_all()


__all__ = [
    "EventBus",
    "Event",
    "EventResult",
    "EventPriority",
    "EventStatus",
    "Subscription",
    "EventHandler",
    "EventStore",
    "EventRouter",
    "get_eventbus",
    "subscribe",
    "unsubscribe",
    "publish",
    "clear_all",
]


# ============================================================================
# Example Usage
# ============================================================================


async def example_event_bus_setup():
    """Example setup of event bus."""
    event_bus = EventBus()
    await event_bus.start()

    # Register handlers
    event_bus.register_handler(PortfolioUpdateHandler())
    event_bus.register_handler(TradingSignalHandler())

    # Publish events
    await event_bus.publish("portfolio.updated", {"user_id": "user123", "value": 25000.0}, source="portfolio_service")

    await event_bus.publish(
        "trading.signal.generated",
        {"symbol": "BTC", "signal": "BUY", "confidence": 0.85},
        source="trading_service",
        priority=EventPriority.HIGH,
    )

    # Get metrics
    metrics = await event_bus.get_metrics()
    print(f"Event bus metrics: {metrics}")

    return event_bus


if __name__ == "__main__":

    async def main():
        event_bus = await example_event_bus_setup()

        try:
            # Keep running
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await event_bus.stop()

    asyncio.run(main())
