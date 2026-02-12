"""Event system for agentic coordination."""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4


@dataclass
class CaseCompletedEvent:
    """Event published when a case execution completes."""

    case_id: str
    outcome: str
    solution: str
    agent_experience: dict[str, Any] = field(default_factory=dict)
    execution_time_seconds: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class CaseExecutedEvent:
    """Event published when a case is executed."""

    case_id: str
    agent_role: str
    task: str
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = field(default_factory=lambda: str(uuid4()))


Event = dict[str, Any]
EventHandler = Callable[[Event], Any]


class EventBus:
    """Simple event bus for decoupled communication."""

    def __init__(self) -> None:
        self.subscribers: dict[str, list[EventHandler]] = {}

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe to an event type."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)

    def publish(self, event: Event) -> list[Any]:
        """Publish event to all subscribers."""
        event_type = event.get("type", "unknown")
        results = []

        if event_type in self.subscribers:
            for handler in self.subscribers[event_type]:
                try:
                    result = handler(event)
                    if result is not None:
                        results.append(result)
                except Exception as e:
                    print(f"Event handler error: {e}")

        return results

    def unsubscribe(self, event_type: str, handler: EventHandler) -> bool:
        """Unsubscribe from an event type."""
        if event_type in self.subscribers and handler in self.subscribers[event_type]:
            self.subscribers[event_type].remove(handler)
            return True
        return False
