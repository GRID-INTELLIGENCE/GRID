"""
Runtime Observation Service.
Unified observation framework for safety and security modules.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

from safety.observability.risk_score import risk_manager
from safety.observability.security_monitoring import (
    SecurityEvent,
    SecurityEventSeverity,
    SecurityEventType,
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
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None

    # Details
    decision: str = "unknown"
    reason: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    risk_score: float = 0.0

    # Metrics
    latency_ms: float = 0.0
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)

    @classmethod
    def from_security_event(cls, event: SecurityEvent, trace_id: str = "unknown") -> "RuntimeObservationEvent":
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
            risk_score=event.risk_score
        )


class EventBus:
    """Simple in-memory event bus for streaming."""

    def __init__(self):
        self._subscribers: List[asyncio.Queue] = []

    async def publish(self, event: RuntimeObservationEvent):
        """Publish event to all subscribers."""
        for queue in self._subscribers:
            try:
                # Don't block publisher
                queue.put_nowait(event)
            except asyncio.QueueFull:
                pass  # Drop event if subscriber is slow

    async def subscribe(self) -> asyncio.Queue:
        """Subscribe to events."""
        queue = asyncio.Queue(maxsize=1000)
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        """Unsubscribe from events."""
        if queue in self._subscribers:
            self._subscribers.remove(queue)


class RuntimeObservationService:
    """Unified runtime observation for all safety/security modules."""

    def __init__(self):
        self.event_bus = EventBus()
        # Hook into existing security logger
        security_logger.add_listener(self._on_security_event_sync)

    def _on_security_event_sync(self, event: SecurityEvent):
        """Bridge sync logger to async bus and risk manager."""
        # This runs in the sync listener loop, so we need to schedule the async tasks
        try:
            loop = asyncio.get_running_loop()
            
            # 1. Publish to stream
            obs_event = RuntimeObservationEvent.from_security_event(event)
            loop.create_task(self.event_bus.publish(obs_event))
            
            # 2. Update Risk Score (Project GUARDIAN Phase 2)
            loop.create_task(risk_manager.record_violation(event))
            
        except RuntimeError:
            # No event loop (e.g. testing or shutdown), ignore
            pass

    async def log_observation(self, event: RuntimeObservationEvent):
        """Log a new observation event."""
        # Convert back to legacy for persistence if needed, or just publish
        await self.event_bus.publish(event)
        
    async def get_system_health(self) -> Dict[str, Any]:
        """Get health status."""
        return {
            "status": "healthy",
            "subscribers": len(self.event_bus._subscribers),
            "backend": "redis_streams_and_memory"
        }

# Global Instance
observation_service = RuntimeObservationService()

