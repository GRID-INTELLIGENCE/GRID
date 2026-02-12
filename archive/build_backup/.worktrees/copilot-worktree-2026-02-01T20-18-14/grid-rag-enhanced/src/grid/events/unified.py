"""
Unified Event Bus — facade composing sync core and async agentic buses.

Provides a single API surface that:
- Accepts both sync and async handlers
- Routes through the middleware pipeline (core bus)
- Optionally distributes via Redis pub-sub (agentic bus)
- Maintains an EventStore for correlation/type queries (core)
- Keeps a deque-based fast history for replay (agentic)
- Supports pattern-based subscriptions with wildcards

Usage:
    >>> from grid.events.unified import get_unified_bus
    >>> bus = get_unified_bus()
    >>> bus.subscribe("cognitive:*", my_handler)
    >>> bus.emit(Event(type="cognitive:route", data={"query": "..."}))
    >>> await bus.emit_async(event)
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import threading
import uuid
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from grid.events.core import (
    Event,
    EventBus as CoreEventBus,
    EventMiddleware,
    EventPriority,
    EventStore,
    EventSubscription,
)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Optional Redis import
# ─────────────────────────────────────────────────────────────

try:
    import redis.asyncio as aioredis

    _REDIS_AVAILABLE = True
except ImportError:
    _REDIS_AVAILABLE = False
    aioredis = None  # type: ignore[assignment]


# ─────────────────────────────────────────────────────────────
# Handler Wrapper
# ─────────────────────────────────────────────────────────────

class HandlerKind(Enum):
    """Whether a registered handler is sync or async."""

    SYNC = "sync"
    ASYNC = "async"


@dataclass(frozen=True)
class UnifiedSubscription:
    """Tracks a unified subscription spanning both buses."""

    subscription_id: str
    pattern: str
    handler: Callable[..., Any]
    kind: HandlerKind
    priority: EventPriority = EventPriority.NORMAL
    core_subscription_id: str | None = None


# ─────────────────────────────────────────────────────────────
# Bridge Adapters
# ─────────────────────────────────────────────────────────────

def _wrap_async_as_sync(
    async_handler: Callable[[Event], Any],
) -> Callable[[Event], None]:
    """Wrap an async handler so it can be called from the sync core bus."""

    def wrapper(event: Event) -> None:
        try:
            loop = asyncio.get_running_loop()
            # Already in an event loop — schedule as task
            loop.create_task(async_handler(event))
        except RuntimeError:
            # No running loop — run to completion
            asyncio.run(async_handler(event))

    wrapper.__wrapped__ = async_handler  # type: ignore[attr-defined]
    wrapper.__qualname__ = f"async_bridge({async_handler.__qualname__})"
    return wrapper


def _event_to_dict(event: Event) -> dict[str, Any]:
    """Convert a core Event to a dict for the agentic bus."""
    return {
        "event_type": event.type,
        "event_id": event.event_id,
        "source": event.source,
        "data": event.data,
        "correlation_id": event.correlation_id,
        "causation_id": event.causation_id,
        "priority": event.priority.value if isinstance(event.priority, EventPriority) else event.priority,
        "metadata": event.metadata,
    }


def _dict_to_event(d: dict[str, Any]) -> Event:
    """Best-effort conversion from agentic dict to core Event."""
    priority_val = d.get("priority", EventPriority.NORMAL.value)
    try:
        priority = EventPriority(priority_val)
    except (ValueError, KeyError):
        priority = EventPriority.NORMAL

    return Event(
        type=d.get("event_type", d.get("type", "unknown")),
        data=d.get("data", {}),
        source=d.get("source", "unknown"),
        correlation_id=d.get("correlation_id"),
        causation_id=d.get("causation_id"),
        priority=priority,
        metadata=d.get("metadata", {}),
    )


# ─────────────────────────────────────────────────────────────
# Unified Event Bus
# ─────────────────────────────────────────────────────────────

class UnifiedEventBus:
    """
    Unified facade over the sync core EventBus and async agentic EventBus.

    Design principles:
    - **Core bus** handles middleware, priority dispatch, and EventStore.
    - **Redis** distribution is optional and managed directly here (no
      separate agentic bus instance) to avoid double-dispatch.
    - Async handlers are bridged into the sync dispatch path; pure-async
      callers should use ``emit_async`` for full await semantics.
    """

    def __init__(
        self,
        *,
        enable_store: bool = True,
        store_max_events: int = 10_000,
        enable_redis: bool = False,
        redis_url: str = "redis://localhost:6379/0",
        history_size: int = 1_000,
    ) -> None:
        # Core sync bus (middleware + store + priority)
        self._core = CoreEventBus(
            store_events=enable_store,
            max_stored_events=store_max_events,
        )

        # Fast deque history (mirrors agentic bus pattern)
        self._history: deque[dict[str, Any]] = deque(maxlen=history_size)

        # Unified subscription registry
        self._subscriptions: dict[str, UnifiedSubscription] = {}
        self._lock = threading.RLock()

        # Redis distribution (optional)
        self._redis_enabled = enable_redis and _REDIS_AVAILABLE
        self._redis_client: Any | None = None
        self._redis_pubsub: Any | None = None
        if self._redis_enabled:
            self._init_redis(redis_url)

        # Stats
        self._stats: dict[str, int] = {
            "unified_emit_sync": 0,
            "unified_emit_async": 0,
            "redis_published": 0,
            "redis_errors": 0,
            "bridge_async_to_sync": 0,
        }

    # ── Redis ────────────────────────────────────────────────

    def _init_redis(self, redis_url: str) -> None:
        """Initialize async Redis for distributed pub-sub."""
        if not _REDIS_AVAILABLE:
            logger.warning("redis.asyncio not available — Redis distribution disabled.")
            self._redis_enabled = False
            return
        try:
            self._redis_client = aioredis.from_url(redis_url, decode_responses=True)
            self._redis_pubsub = self._redis_client.pubsub()
            logger.info("UnifiedEventBus: Redis pub-sub initialized (%s)", redis_url)
        except Exception as exc:
            logger.warning("UnifiedEventBus: Redis init failed (%s) — falling back to local.", exc)
            self._redis_enabled = False
            self._redis_client = None
            self._redis_pubsub = None

    async def _redis_publish(self, event: Event) -> None:
        """Publish event to Redis channels."""
        if not self._redis_enabled or self._redis_client is None:
            return
        try:
            payload = str(_event_to_dict(event))
            await self._redis_client.publish(f"events:{event.type}", payload)
            await self._redis_client.publish("events:all", payload)
            self._stats["redis_published"] += 1
        except Exception as exc:
            self._stats["redis_errors"] += 1
            logger.error("Redis publish failed: %s", exc)

    # ── Subscribe ────────────────────────────────────────────

    def subscribe(
        self,
        event_pattern: str,
        handler: Callable[..., Any],
        *,
        priority: EventPriority = EventPriority.NORMAL,
        once: bool = False,
    ) -> str:
        """
        Subscribe to events matching *event_pattern*.

        Accepts both sync and async handlers — async handlers are bridged
        into the core bus via ``create_task`` / ``asyncio.run`` adapters.

        Args:
            event_pattern: Glob-style pattern (e.g. ``"cognitive:*"``).
            handler: Sync or async callable receiving an ``Event``.
            priority: Dispatch priority.
            once: If ``True``, automatically unsubscribe after first delivery.

        Returns:
            Subscription ID (UUID).
        """
        kind = HandlerKind.ASYNC if inspect.iscoroutinefunction(handler) else HandlerKind.SYNC

        # Determine the handler that the core bus will call
        if kind is HandlerKind.ASYNC:
            core_handler = _wrap_async_as_sync(handler)
            self._stats["bridge_async_to_sync"] += 1
        else:
            core_handler = handler

        core_sub_id = self._core.subscribe(
            event_pattern,
            core_handler,
            priority=priority,
            once=once,
        )

        unified_id = str(uuid.uuid4())
        sub = UnifiedSubscription(
            subscription_id=unified_id,
            pattern=event_pattern,
            handler=handler,
            kind=kind,
            priority=priority,
            core_subscription_id=core_sub_id,
        )

        with self._lock:
            self._subscriptions[unified_id] = sub

        logger.debug(
            "UnifiedEventBus: subscribed [%s] pattern=%s kind=%s",
            unified_id[:8],
            event_pattern,
            kind.value,
        )
        return unified_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Remove a subscription by its unified ID."""
        with self._lock:
            sub = self._subscriptions.pop(subscription_id, None)
        if sub is None:
            return False
        if sub.core_subscription_id:
            self._core.unsubscribe(sub.core_subscription_id)
        return True

    # ── Decorators ───────────────────────────────────────────

    def on(
        self,
        event_pattern: str,
        priority: EventPriority = EventPriority.NORMAL,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """
        Decorator for subscribing to events.

        Example::

            @bus.on("cognitive:route:*")
            def handle_route(event: Event) -> None:
                ...

            @bus.on("rag:query:completed")
            async def handle_rag(event: Event) -> None:
                ...
        """

        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            self.subscribe(event_pattern, fn, priority=priority)
            return fn

        return decorator

    def once(
        self,
        event_pattern: str,
        priority: EventPriority = EventPriority.NORMAL,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator for one-time event subscription."""

        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            self.subscribe(event_pattern, fn, priority=priority, once=True)
            return fn

        return decorator

    # ── Emit ─────────────────────────────────────────────────

    def emit(self, event: Event) -> None:
        """
        Synchronous emit — runs the middleware pipeline, stores the event,
        dispatches to all matching handlers (async handlers fire-and-forget
        via ``create_task``), and appends to the fast history deque.
        """
        self._stats["unified_emit_sync"] += 1
        self._core.emit(event)
        self._history.append(_event_to_dict(event))

    async def emit_async(self, event: Event) -> None:
        """
        Async emit — full middleware pipeline + Redis distribution.

        Preferred when calling from async code; ensures Redis publish
        is properly awaited and async handlers run in the current loop.
        """
        self._stats["unified_emit_async"] += 1

        # Run sync core dispatch in executor to avoid blocking the loop
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._core.emit, event)

        # Distribute via Redis
        await self._redis_publish(event)

        # Append to fast history
        self._history.append(_event_to_dict(event))

    async def publish(self, event_dict: dict[str, Any]) -> None:
        """
        Agentic-compatible async publish — accepts a raw dict.

        Converts to a core ``Event``, runs through the unified pipeline,
        then distributes via Redis. This method provides backward
        compatibility with code written against ``grid.agentic.event_bus``.
        """
        event = _dict_to_event(event_dict)
        await self.emit_async(event)

    # ── Middleware ────────────────────────────────────────────

    def add_middleware(self, middleware: EventMiddleware) -> None:
        """Add middleware to the core processing pipeline."""
        self._core.add_middleware(middleware)

    # ── History & Replay ─────────────────────────────────────

    def get_history(
        self,
        event_type: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Return recent events from the fast history deque.

        Args:
            event_type: Optional filter.
            limit: Max results (default: all).
        """
        events = list(self._history)
        if event_type is not None:
            events = [e for e in events if e.get("event_type") == event_type]
        if limit is not None:
            events = events[-limit:]
        return events

    def replay(
        self,
        *,
        correlation_id: str | None = None,
        event_type: str | None = None,
    ) -> int:
        """
        Replay events from the EventStore through the core bus.

        Delegates to ``CoreEventBus.replay_events`` which marks replayed
        events with ``metadata["is_replay"] = True``.

        Returns:
            Number of events replayed.
        """
        return self._core.replay_events(
            correlation_id=correlation_id,
            event_type=event_type,
        )

    def get_event_store(self) -> EventStore | None:
        """Access the core EventStore for advanced queries."""
        return self._core.get_event_store()

    # ── Stats ────────────────────────────────────────────────

    def get_stats(self) -> dict[str, Any]:
        """Merged statistics from unified layer + core bus."""
        core_stats = self._core.get_stats()
        return {
            **core_stats,
            **self._stats,
            "history_size": len(self._history),
            "unified_subscriptions": len(self._subscriptions),
            "redis_enabled": self._redis_enabled,
        }

    # ── Lifecycle ────────────────────────────────────────────

    async def close(self) -> None:
        """Shut down Redis connections and clear state."""
        if self._redis_pubsub is not None:
            await self._redis_pubsub.unsubscribe()
            await self._redis_pubsub.close()
        if self._redis_client is not None:
            await self._redis_client.close()
        self._core.clear()
        self._history.clear()
        logger.info("UnifiedEventBus closed.")

    def clear(self) -> None:
        """Clear all subscriptions, stores, and history."""
        with self._lock:
            self._subscriptions.clear()
        self._core.clear()
        self._history.clear()

    def __repr__(self) -> str:
        return (
            f"UnifiedEventBus("
            f"subscriptions={len(self._subscriptions)}, "
            f"history={len(self._history)}, "
            f"redis={'on' if self._redis_enabled else 'off'}"
            f")"
        )


# ─────────────────────────────────────────────────────────────
# Singleton access
# ─────────────────────────────────────────────────────────────

_unified_bus: UnifiedEventBus | None = None
_unified_lock = threading.Lock()


def get_unified_bus(**kwargs: Any) -> UnifiedEventBus:
    """
    Get or create the singleton UnifiedEventBus.

    Keyword arguments are forwarded to the constructor *only* on first
    call. Subsequent calls return the cached instance.

    Returns:
        The shared UnifiedEventBus.
    """
    global _unified_bus
    if _unified_bus is None:
        with _unified_lock:
            if _unified_bus is None:
                _unified_bus = UnifiedEventBus(**kwargs)
    return _unified_bus


def set_unified_bus(bus: UnifiedEventBus) -> None:
    """Replace the singleton (useful in tests)."""
    global _unified_bus
    with _unified_lock:
        _unified_bus = bus


def reset_unified_bus() -> None:
    """Clear the singleton (useful in tests)."""
    global _unified_bus
    with _unified_lock:
        _unified_bus = None
