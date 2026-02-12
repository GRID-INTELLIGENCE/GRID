"""
Event-Driven I/O Core Module for GRID.

Provides the foundational event system for decoupled, scalable processing
with event sourcing, middleware support, and correlation tracking.

Key Components:
- Event: Core event data structure with correlation tracking
- EventBus: Central event dispatcher with subscription management
- EventType: Enumeration of standard event types
- EventMiddleware: Protocol for event middleware
- EventStore: In-memory event storage with query support

Features:
- Decoupled architecture through event-driven communication
- Correlation ID tracking for request tracing
- Middleware pipeline for cross-cutting concerns
- Event sourcing with queryable event store
- Async and sync event emission support
- Priority-based event handling

Example:
    >>> from grid.events import EventBus, Event, EventType
    >>> bus = EventBus()
    >>> bus.subscribe(EventType.CLI_INPUT, lambda e: print(f"Received: {e.data}"))
    >>> bus.emit(Event(type=EventType.CLI_INPUT, data={"command": "analyze"}))
"""

from __future__ import annotations

__version__ = "0.1.0"
__author__ = "GRID Team"

from .core import (
    Event,
    EventBus,
    EventMiddleware,
    EventPriority,
    EventStore,
    EventSubscription,
)
from .types import EventCategory, EventType
from .unified import UnifiedEventBus, get_unified_bus, set_unified_bus

__all__ = [
    # Core classes
    "Event",
    "EventBus",
    "EventMiddleware",
    "EventPriority",
    "EventStore",
    "EventSubscription",
    # Unified facade
    "UnifiedEventBus",
    "get_unified_bus",
    "set_unified_bus",
    # Event types
    "EventType",
    "EventCategory",
]
