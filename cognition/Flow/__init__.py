"""
Flow Module

Manages cognitive event flows and state transitions.
Provides basic flow management with extensibility for advanced features.
"""

import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class FlowState(Enum):
    """States in cognitive flow processing."""
    IDLE = "idle"
    ACTIVE = "active"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class FlowEvent:
    """Represents an event in the cognitive flow."""
    event_id: str
    event_type: str
    timestamp: float
    data: dict[str, Any] = field(default_factory=dict)
    source: str | None = None
    priority: int = 0  # Higher numbers = higher priority


@dataclass
class CognitiveFlow:
    """A cognitive flow with events and state management."""
    flow_id: str
    name: str
    events: list[FlowEvent] = field(default_factory=list)
    current_state: FlowState = FlowState.IDLE
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def add_event(self, event: FlowEvent) -> None:
        """Add an event to the flow."""
        self.events.append(event)
        self.updated_at = time.time()
        logger.debug(f"Added event {event.event_id} to flow {self.flow_id}")

    def get_events_by_type(self, event_type: str) -> list[FlowEvent]:
        """Get all events of a specific type."""
        return [e for e in self.events if e.event_type == event_type]

    def get_recent_events(self, count: int = 10) -> list[FlowEvent]:
        """Get the most recent events."""
        return sorted(self.events, key=lambda e: e.timestamp, reverse=True)[:count]


class FlowProcessor(ABC):
    """Abstract base class for flow processors."""

    @abstractmethod
    def process_event(self, event: FlowEvent, flow: CognitiveFlow) -> bool:
        """Process a single event. Return True if successful."""
        pass

    @abstractmethod
    def can_process(self, event: FlowEvent) -> bool:
        """Check if this processor can handle the event."""
        pass


class FlowManager:
    """Manages multiple cognitive flows and event processing."""

    def __init__(self):
        self.flows: dict[str, CognitiveFlow] = {}
        self.processors: list[FlowProcessor] = []
        self.event_handlers: dict[str, Callable] = {}
        self.logger = logging.getLogger(f"{__name__}.FlowManager")

    def create_flow(self, flow_id: str, name: str, **metadata) -> CognitiveFlow:
        """Create a new cognitive flow."""
        if flow_id in self.flows:
            raise ValueError(f"Flow {flow_id} already exists")

        flow = CognitiveFlow(flow_id=flow_id, name=name, metadata=metadata)
        self.flows[flow_id] = flow
        self.logger.info(f"Created flow {flow_id}: {name}")
        return flow

    def get_flow(self, flow_id: str) -> CognitiveFlow | None:
        """Get a flow by ID."""
        return self.flows.get(flow_id)

    def add_processor(self, processor: FlowProcessor) -> None:
        """Add a flow processor."""
        self.processors.append(processor)
        self.logger.debug(f"Added processor: {processor.__class__.__name__}")

    def register_event_handler(self, event_type: str, handler: Callable) -> None:
        """Register a custom event handler."""
        self.event_handlers[event_type] = handler

    def process_event(self, flow_id: str, event: FlowEvent) -> bool:
        """Process an event in a specific flow."""
        flow = self.get_flow(flow_id)
        if not flow:
            self.logger.error(f"Flow {flow_id} not found")
            return False

        # Add event to flow
        flow.add_event(event)

        # Try custom handler first
        if event.event_type in self.event_handlers:
            try:
                self.event_handlers[event.event_type](event, flow)
                self.logger.debug(f"Processed {event.event_type} with custom handler")
                return True
            except Exception as e:
                self.logger.error(f"Custom handler failed: {e}")

        # Try registered processors
        for processor in self.processors:
            if processor.can_process(event):
                try:
                    success = processor.process_event(event, flow)
                    if success:
                        self.logger.debug(f"Processed {event.event_type} with {processor.__class__.__name__}")
                        return True
                except Exception as e:
                    self.logger.error(f"Processor {processor.__class__.__name__} failed: {e}")

        # Default processing
        flow.current_state = FlowState.ACTIVE
        self.logger.debug(f"Default processing for {event.event_type}")
        return True

    def get_flow_statistics(self, flow_id: str) -> dict[str, Any]:
        """Get statistics for a flow."""
        flow = self.get_flow(flow_id)
        if not flow:
            return {}

        event_types: dict[str, int] = {}
        for event in flow.events:
            event_types[event.event_type] = event_types.get(event.event_type, 0) + 1

        return {
            "flow_id": flow.flow_id,
            "name": flow.name,
            "state": flow.current_state.value,
            "event_count": len(flow.events),
            "event_types": event_types,
            "created_at": flow.created_at,
            "updated_at": flow.updated_at,
            "duration": flow.updated_at - flow.created_at,
        }

    def list_flows(self) -> list[str]:
        """List all flow IDs."""
        return list(self.flows.keys())

    def delete_flow(self, flow_id: str) -> bool:
        """Delete a flow."""
        if flow_id in self.flows:
            del self.flows[flow_id]
            self.logger.info(f"Deleted flow {flow_id}")
            return True
        return False


# Basic processor implementations
class PerceptionProcessor(FlowProcessor):
    """Processes perception events."""

    def can_process(self, event: FlowEvent) -> bool:
        return event.event_type == "perception"

    def process_event(self, event: FlowEvent, flow: CognitiveFlow) -> bool:
        """Process perception event."""
        # Basic perception processing logic
        flow.metadata["last_perception"] = event.timestamp
        return True


class AttentionProcessor(FlowProcessor):
    """Processes attention shift events."""

    def can_process(self, event: FlowEvent) -> bool:
        return event.event_type == "attention_shift"

    def process_event(self, event: FlowEvent, flow: CognitiveFlow) -> bool:
        """Process attention shift event."""
        # Basic attention processing logic
        flow.metadata["attention_target"] = event.data.get("target")
        flow.metadata["last_attention_shift"] = event.timestamp
        return True


# Future extension points
class AdvancedFlowManager(FlowManager):
    """Advanced flow manager with additional capabilities."""

    def __init__(self):
        super().__init__()
        self.flow_dependencies: dict[str, list[str]] = {}
        self.flow_priorities: dict[str, int] = {}

    def add_dependency(self, flow_id: str, depends_on: str) -> None:
        """Add a flow dependency."""
        if flow_id not in self.flow_dependencies:
            self.flow_dependencies[flow_id] = []
        self.flow_dependencies[flow_id].append(depends_on)

    def set_priority(self, flow_id: str, priority: int) -> None:
        """Set flow priority."""
        self.flow_priorities[flow_id] = priority

    # Placeholder for advanced features
    def optimize_flow_order(self) -> list[str]:
        """Optimize flow processing order based on dependencies and priorities."""
        # TODO: Implement topological sort with priority weighting
        return list(self.flows.keys())
