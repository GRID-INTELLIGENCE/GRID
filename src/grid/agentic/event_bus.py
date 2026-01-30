"""Event bus for async event processing."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict, deque
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class EventBus:
    """Event bus for async event processing with Redis pub-sub support."""

    def __init__(
        self,
        use_redis: bool = False,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        max_history: int = 1000,
    ):
        """Initialize event bus.

        Args:
            use_redis: Whether to use Redis for distributed event bus
            redis_host: Redis hostname
            redis_port: Redis port
            redis_db: Redis database number
            max_history: Maximum number of events to keep in memory history
        """
        if max_history <= 0:
            raise ValueError(f"max_history must be positive, got {max_history}")

        self.use_redis = use_redis and REDIS_AVAILABLE
        self.redis_client: Any | None = None
        self.redis_pubsub: Any | None = None
        self.max_history = max_history

        # In-memory event queue (fallback)
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.handlers: dict[str, list[Callable]] = defaultdict(list)
        self.event_history: deque[dict[str, Any]] = deque(maxlen=max_history)

        # Initialize Redis if enabled
        if self.use_redis:
            self._init_redis(redis_host, redis_port, redis_db)

    def _init_redis(self, host: str, port: int, db: int) -> None:
        """Initialize Redis connection."""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available. Falling back to in-memory queue.")
            self.use_redis = False
            self.redis_client = None
            self.redis_pubsub = None
            return

        try:
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=True,
            )
            self.redis_pubsub = self.redis_client.pubsub()
            logger.info(f"Redis event bus initialized at {host}:{port}")
        except Exception as e:
            logger.warning(f"Failed to initialize Redis: {e}. Falling back to in-memory queue.")
            self.use_redis = False
            self.redis_client = None
            self.redis_pubsub = None

    async def publish(self, event: dict[str, Any]) -> None:
        """Publish an event to the bus.

        Args:
            event: Event dictionary with event_type and other fields
        """
        event_type = event.get("event_type", "unknown")
        event_data = {
            **event,
            "published_at": asyncio.get_event_loop().time(),
        }

        # Store in history (deque auto-pops oldest when at maxlen)
        self.event_history.append(event_data)

        # Publish to Redis if enabled
        if self.use_redis and self.redis_client:
            try:
                await self.redis_client.publish(f"events:{event_type}", str(event_data))
                await self.redis_client.publish("events:all", str(event_data))
            except Exception as e:
                logger.error(f"Failed to publish to Redis: {e}. Falling back to in-memory queue.")
                await self.event_queue.put(event_data)
        else:
            # Use in-memory queue
            await self.event_queue.put(event_data)

        # Trigger handlers synchronously
        await self._trigger_handlers(event_type, event_data)

    async def subscribe(self, event_type: str, handler: Callable) -> None:
        """Subscribe to events of a specific type.

        Args:
            event_type: Event type to subscribe to (e.g., "case.created")
            handler: Async handler function that takes event dict as argument
        """
        self.handlers[event_type].append(handler)
        logger.debug(f"Subscribed handler to {event_type}")

        # Subscribe to Redis if enabled
        if self.use_redis and self.redis_pubsub:
            try:
                await self.redis_pubsub.subscribe(f"events:{event_type}")
            except Exception as e:
                logger.warning(f"Failed to subscribe to Redis: {e}")

    async def subscribe_all(self, handler: Callable) -> None:
        """Subscribe to all events.

        Args:
            handler: Async handler function that takes event dict as argument
        """
        self.handlers["*"].append(handler)
        logger.debug("Subscribed handler to all events")

        # Subscribe to Redis if enabled
        if self.use_redis and self.redis_pubsub:
            try:
                await self.redis_pubsub.subscribe("events:all")
            except Exception as e:
                logger.warning(f"Failed to subscribe to Redis: {e}")

    async def _trigger_handlers(self, event_type: str, event_data: dict[str, Any]) -> None:
        """Trigger handlers for an event type.

        Args:
            event_type: Event type
            event_data: Event data dictionary
        """
        # Trigger specific handlers
        for handler in self.handlers.get(event_type, []):
            try:
                await handler(event_data)
            except Exception as e:
                logger.error(f"Error in handler for {event_type}: {e}")

        # Trigger universal handlers
        for handler in self.handlers.get("*", []):
            try:
                await handler(event_data)
            except Exception as e:
                logger.error(f"Error in universal handler: {e}")

    async def process_queue(self) -> None:
        """Process events from the in-memory queue."""
        while True:
            try:
                event = await self.event_queue.get()
                event_type = event.get("event_type", "unknown")
                await self._trigger_handlers(event_type, event)
            except Exception as e:
                logger.error(f"Error processing event queue: {e}")

    async def get_event_history(
        self,
        event_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get event history.

        Args:
            event_type: Filter by event type (optional)
            limit: Maximum number of events to return

        Returns:
            List of event dictionaries
        """
        events = list(self.event_history)
        if event_type:
            events = [e for e in events if e.get("event_type") == event_type]
        return events[-limit:]

    async def replay_events(
        self,
        event_type: str | None = None,
        limit: int = 100,
    ) -> None:
        """Replay events from history.

        Args:
            event_type: Filter by event type (optional)
            limit: Maximum number of events to replay
        """
        events = await self.get_event_history(event_type, limit)
        for event in events:
            await self.publish(event)

    async def close(self) -> None:
        """Close event bus and cleanup resources."""
        if self.use_redis and self.redis_pubsub and self.redis_client:
            try:
                await self.redis_pubsub.unsubscribe()
                await self.redis_client.close()
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}")


# Global event bus instance
_global_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """Get or create global event bus instance."""
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus


def set_event_bus(event_bus: EventBus) -> None:
    """Set global event bus instance."""
    global _global_event_bus
    _global_event_bus = event_bus
