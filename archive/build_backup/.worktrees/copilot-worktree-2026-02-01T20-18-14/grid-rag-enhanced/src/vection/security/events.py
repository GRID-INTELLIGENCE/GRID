"""Security Events Module - Structured security event handling.

Provides a structured event system for security-related events in VECTION.
Enables publish/subscribe patterns for security monitoring and integration
with external systems (SIEM, alerting, etc.).

Features:
- Structured SecurityEvent dataclass
- Event emitter with callback support
- Event filtering and routing
- Event serialization for external systems
- Integration with audit logging
- Thread-safe implementation

Usage:
    from vection.security.events import SecurityEvent, SecurityEventEmitter

    # Create emitter
    emitter = SecurityEventEmitter()

    # Subscribe to events
    emitter.on("rate_limit.*", lambda event: handle_rate_limit(event))

    # Emit events
    emitter.emit(SecurityEvent(
        category="rate_limit",
        action="exceeded",
        session_id="ses_123",
        details={"operation": "reinforce"}
    ))
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class EventCategory(str, Enum):
    """Categories of security events."""

    # Rate limiting events
    RATE_LIMIT = "rate_limit"

    # Validation events
    VALIDATION = "validation"

    # Session events
    SESSION = "session"

    # Access control events
    ACCESS = "access"

    # Anomaly events
    ANOMALY = "anomaly"

    # Audit events
    AUDIT = "audit"

    # System events
    SYSTEM = "system"

    # Alert events
    ALERT = "alert"

    # Custom events
    CUSTOM = "custom"


class EventAction(str, Enum):
    """Common event actions."""

    # Generic actions
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    ACCESSED = "accessed"

    # Rate limit actions
    CHECKED = "checked"
    EXCEEDED = "exceeded"
    RESET = "reset"

    # Validation actions
    PASSED = "passed"
    FAILED = "failed"
    SANITIZED = "sanitized"

    # Access actions
    GRANTED = "granted"
    DENIED = "denied"
    REVOKED = "revoked"

    # Anomaly actions
    DETECTED = "detected"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"

    # System actions
    STARTED = "started"
    STOPPED = "stopped"
    ERROR = "error"

    # Alert actions
    TRIGGERED = "triggered"
    ESCALATED = "escalated"
    SUPPRESSED = "suppressed"


class EventPriority(str, Enum):
    """Priority levels for events."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityEvent:
    """A structured security event.

    Attributes:
        event_id: Unique identifier for this event.
        category: Event category.
        action: Event action.
        timestamp: When the event occurred (ISO 8601).
        session_id: Associated session (if any).
        user_id: Associated user (if any).
        source: Source component that generated the event.
        priority: Event priority level.
        details: Additional event-specific details.
        tags: Tags for filtering and categorization.
        correlation_id: ID for correlating related events.
        metadata: Additional metadata.
    """

    category: str
    action: str
    event_id: str = ""
    timestamp: str = ""
    session_id: str | None = None
    user_id: str | None = None
    source: str = "vection.security"
    priority: EventPriority = EventPriority.NORMAL
    details: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    correlation_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize computed fields."""
        if not self.event_id:
            self.event_id = self._generate_event_id()
        if not self.timestamp:
            self.timestamp = datetime.now(UTC).isoformat()

    def _generate_event_id(self) -> str:
        """Generate a unique event ID."""
        timestamp = int(time.time() * 1000000)
        hash_input = f"{self.category}:{self.action}:{timestamp}:{id(self)}"
        return f"evt_{hashlib.sha256(hash_input.encode()).hexdigest()[:16]}"

    @property
    def event_type(self) -> str:
        """Get the full event type (category.action)."""
        return f"{self.category}.{self.action}"

    @property
    def is_high_priority(self) -> bool:
        """Check if event is high priority."""
        return self.priority in (EventPriority.HIGH, EventPriority.CRITICAL)

    def add_tag(self, tag: str) -> SecurityEvent:
        """Add a tag to the event.

        Args:
            tag: Tag to add.

        Returns:
            Self for chaining.
        """
        if tag not in self.tags:
            self.tags.append(tag)
        return self

    def add_detail(self, key: str, value: Any) -> SecurityEvent:
        """Add a detail to the event.

        Args:
            key: Detail key.
            value: Detail value.

        Returns:
            Self for chaining.
        """
        self.details[key] = value
        return self

    def with_correlation(self, correlation_id: str) -> SecurityEvent:
        """Set correlation ID.

        Args:
            correlation_id: Correlation identifier.

        Returns:
            Self for chaining.
        """
        self.correlation_id = correlation_id
        return self

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "category": self.category,
            "action": self.action,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "source": self.source,
            "priority": self.priority.value if isinstance(self.priority, EventPriority) else self.priority,
            "details": self.details,
            "tags": self.tags,
            "correlation_id": self.correlation_id,
            "metadata": self.metadata,
        }

    def to_json(self, indent: int | None = None) -> str:
        """Convert to JSON string.

        Args:
            indent: JSON indentation.

        Returns:
            JSON string.
        """
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SecurityEvent:
        """Create event from dictionary.

        Args:
            data: Dictionary with event data.

        Returns:
            SecurityEvent instance.
        """
        priority = data.get("priority", "normal")
        if isinstance(priority, str):
            try:
                priority = EventPriority(priority)
            except ValueError:
                priority = EventPriority.NORMAL

        return cls(
            event_id=data.get("event_id", ""),
            category=data.get("category", "custom"),
            action=data.get("action", "unknown"),
            timestamp=data.get("timestamp", ""),
            session_id=data.get("session_id"),
            user_id=data.get("user_id"),
            source=data.get("source", "vection.security"),
            priority=priority,
            details=data.get("details", {}),
            tags=data.get("tags", []),
            correlation_id=data.get("correlation_id"),
            metadata=data.get("metadata", {}),
        )

    # Factory methods for common events

    @classmethod
    def rate_limit_exceeded(
        cls,
        session_id: str,
        operation: str,
        current_count: int,
        limit: int,
    ) -> SecurityEvent:
        """Create a rate limit exceeded event."""
        return cls(
            category=EventCategory.RATE_LIMIT.value,
            action=EventAction.EXCEEDED.value,
            session_id=session_id,
            priority=EventPriority.HIGH,
            details={
                "operation": operation,
                "current_count": current_count,
                "limit": limit,
            },
            tags=["rate_limit", "security"],
        )

    @classmethod
    def validation_failed(
        cls,
        session_id: str | None,
        field_name: str,
        reason: str,
    ) -> SecurityEvent:
        """Create a validation failed event."""
        return cls(
            category=EventCategory.VALIDATION.value,
            action=EventAction.FAILED.value,
            session_id=session_id,
            priority=EventPriority.NORMAL,
            details={
                "field_name": field_name,
                "reason": reason,
            },
            tags=["validation", "security"],
        )

    @classmethod
    def access_denied(
        cls,
        source_session: str,
        target_session: str,
        resource_type: str,
        reason: str,
    ) -> SecurityEvent:
        """Create an access denied event."""
        return cls(
            category=EventCategory.ACCESS.value,
            action=EventAction.DENIED.value,
            session_id=source_session,
            priority=EventPriority.HIGH,
            details={
                "target_session": target_session,
                "resource_type": resource_type,
                "reason": reason,
            },
            tags=["access_control", "security"],
        )

    @classmethod
    def anomaly_detected(
        cls,
        session_id: str,
        anomaly_type: str,
        description: str,
        severity: str = "medium",
    ) -> SecurityEvent:
        """Create an anomaly detected event."""
        priority = (
            EventPriority.CRITICAL
            if severity == "critical"
            else (EventPriority.HIGH if severity == "high" else EventPriority.NORMAL)
        )
        return cls(
            category=EventCategory.ANOMALY.value,
            action=EventAction.DETECTED.value,
            session_id=session_id,
            priority=priority,
            details={
                "anomaly_type": anomaly_type,
                "description": description,
                "severity": severity,
            },
            tags=["anomaly", "security", severity],
        )

    @classmethod
    def security_alert(
        cls,
        alert_type: str,
        description: str,
        session_id: str | None = None,
        severity: str = "high",
    ) -> SecurityEvent:
        """Create a security alert event."""
        priority = EventPriority.CRITICAL if severity == "critical" else EventPriority.HIGH
        return cls(
            category=EventCategory.ALERT.value,
            action=EventAction.TRIGGERED.value,
            session_id=session_id,
            priority=priority,
            details={
                "alert_type": alert_type,
                "description": description,
                "severity": severity,
            },
            tags=["alert", "security", severity],
        )


class SecurityEventEmitter:
    """Event emitter for security events.

    Provides publish/subscribe functionality for security events
    with pattern-based subscription support.

    Thread-safe and suitable for concurrent use.

    Usage:
        emitter = SecurityEventEmitter()

        # Subscribe to specific event types
        emitter.on("rate_limit.exceeded", handler)

        # Subscribe with pattern
        emitter.on("anomaly.*", anomaly_handler)

        # Subscribe to all events
        emitter.on("*", log_all_events)

        # Emit event
        emitter.emit(event)
    """

    def __init__(self, max_history: int = 1000) -> None:
        """Initialize the event emitter.

        Args:
            max_history: Maximum events to retain in history.
        """
        self._lock = threading.Lock()
        self._subscribers: dict[str, list[Callable[[SecurityEvent], None]]] = {}
        self._history: list[SecurityEvent] = []
        self._max_history = max_history
        self._total_events = 0
        self._total_delivered = 0

    def on(
        self,
        event_pattern: str,
        callback: Callable[[SecurityEvent], None],
    ) -> Callable[[], None]:
        """Subscribe to events matching a pattern.

        Patterns support wildcards:
        - "rate_limit.exceeded" - exact match
        - "rate_limit.*" - all rate_limit events
        - "*.exceeded" - all exceeded events
        - "*" - all events

        Args:
            event_pattern: Pattern to match event types.
            callback: Function to call with matching events.

        Returns:
            Unsubscribe function.
        """
        with self._lock:
            if event_pattern not in self._subscribers:
                self._subscribers[event_pattern] = []
            self._subscribers[event_pattern].append(callback)

        def unsubscribe() -> None:
            with self._lock:
                if event_pattern in self._subscribers:
                    if callback in self._subscribers[event_pattern]:
                        self._subscribers[event_pattern].remove(callback)

        return unsubscribe

    def off(
        self,
        event_pattern: str,
        callback: Callable[[SecurityEvent], None] | None = None,
    ) -> None:
        """Unsubscribe from events.

        Args:
            event_pattern: Pattern to unsubscribe from.
            callback: Specific callback to remove (None for all).
        """
        with self._lock:
            if event_pattern in self._subscribers:
                if callback is None:
                    del self._subscribers[event_pattern]
                elif callback in self._subscribers[event_pattern]:
                    self._subscribers[event_pattern].remove(callback)

    def emit(self, event: SecurityEvent) -> int:
        """Emit a security event.

        Args:
            event: Event to emit.

        Returns:
            Number of callbacks that received the event.
        """
        with self._lock:
            self._total_events += 1

            # Add to history
            self._history.append(event)
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history :]

            # Find matching subscribers
            callbacks_to_call: list[Callable[[SecurityEvent], None]] = []
            event_type = event.event_type

            for pattern, callbacks in self._subscribers.items():
                if self._matches_pattern(event_type, pattern):
                    callbacks_to_call.extend(callbacks)

        # Call callbacks outside lock
        delivered = 0
        for callback in callbacks_to_call:
            try:
                callback(event)
                delivered += 1
            except Exception as e:
                logger.warning(f"Event callback error for {event.event_type}: {e}")

        with self._lock:
            self._total_delivered += delivered

        return delivered

    def emit_rate_limit_exceeded(
        self,
        session_id: str,
        operation: str,
        current_count: int,
        limit: int,
    ) -> SecurityEvent:
        """Emit a rate limit exceeded event.

        Args:
            session_id: Session identifier.
            operation: Operation that was rate limited.
            current_count: Current request count.
            limit: Maximum allowed requests.

        Returns:
            The emitted event.
        """
        event = SecurityEvent.rate_limit_exceeded(session_id, operation, current_count, limit)
        self.emit(event)
        return event

    def emit_validation_failed(
        self,
        session_id: str | None,
        field_name: str,
        reason: str,
    ) -> SecurityEvent:
        """Emit a validation failed event.

        Args:
            session_id: Session identifier.
            field_name: Field that failed validation.
            reason: Failure reason.

        Returns:
            The emitted event.
        """
        event = SecurityEvent.validation_failed(session_id, field_name, reason)
        self.emit(event)
        return event

    def emit_access_denied(
        self,
        source_session: str,
        target_session: str,
        resource_type: str,
        reason: str,
    ) -> SecurityEvent:
        """Emit an access denied event.

        Args:
            source_session: Session that was denied.
            target_session: Session that was targeted.
            resource_type: Type of resource.
            reason: Denial reason.

        Returns:
            The emitted event.
        """
        event = SecurityEvent.access_denied(source_session, target_session, resource_type, reason)
        self.emit(event)
        return event

    def emit_anomaly_detected(
        self,
        session_id: str,
        anomaly_type: str,
        description: str,
        severity: str = "medium",
    ) -> SecurityEvent:
        """Emit an anomaly detected event.

        Args:
            session_id: Session identifier.
            anomaly_type: Type of anomaly.
            description: Anomaly description.
            severity: Anomaly severity.

        Returns:
            The emitted event.
        """
        event = SecurityEvent.anomaly_detected(session_id, anomaly_type, description, severity)
        self.emit(event)
        return event

    def emit_security_alert(
        self,
        alert_type: str,
        description: str,
        session_id: str | None = None,
        severity: str = "high",
    ) -> SecurityEvent:
        """Emit a security alert event.

        Args:
            alert_type: Type of alert.
            description: Alert description.
            session_id: Associated session.
            severity: Alert severity.

        Returns:
            The emitted event.
        """
        event = SecurityEvent.security_alert(alert_type, description, session_id, severity)
        self.emit(event)
        return event

    def get_history(
        self,
        event_type: str | None = None,
        session_id: str | None = None,
        limit: int = 100,
    ) -> list[SecurityEvent]:
        """Get event history with optional filtering.

        Args:
            event_type: Filter by event type pattern.
            session_id: Filter by session.
            limit: Maximum events to return.

        Returns:
            List of matching events.
        """
        with self._lock:
            events = self._history.copy()

        # Apply filters
        if event_type is not None:
            events = [e for e in events if self._matches_pattern(e.event_type, event_type)]

        if session_id is not None:
            events = [e for e in events if e.session_id == session_id]

        return events[-limit:]

    def get_stats(self) -> dict[str, Any]:
        """Get emitter statistics.

        Returns:
            Dictionary with statistics.
        """
        with self._lock:
            return {
                "total_events": self._total_events,
                "total_delivered": self._total_delivered,
                "history_size": len(self._history),
                "subscriber_patterns": len(self._subscribers),
                "total_subscribers": sum(len(cbs) for cbs in self._subscribers.values()),
            }

    def clear_history(self) -> None:
        """Clear event history."""
        with self._lock:
            self._history.clear()

    def _matches_pattern(self, event_type: str, pattern: str) -> bool:
        """Check if event type matches pattern.

        Args:
            event_type: Event type to check.
            pattern: Pattern to match against.

        Returns:
            True if matches.
        """
        if pattern == "*":
            return True
        return fnmatch.fnmatch(event_type, pattern)


# Module-level singleton
_event_emitter: SecurityEventEmitter | None = None


def get_event_emitter() -> SecurityEventEmitter:
    """Get the global security event emitter.

    Returns:
        SecurityEventEmitter singleton.
    """
    global _event_emitter
    if _event_emitter is None:
        _event_emitter = SecurityEventEmitter()
    return _event_emitter


def emit_security_event(event: SecurityEvent) -> int:
    """Convenience function to emit a security event.

    Args:
        event: Event to emit.

    Returns:
        Number of callbacks that received the event.
    """
    return get_event_emitter().emit(event)
