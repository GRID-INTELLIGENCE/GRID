"""Audit Logger - Comprehensive security event logging.

Provides transparent, tamper-evident audit logging for all security-relevant
events in the VECTION system. All logs are explicit, structured, and suitable
for SIEM integration and compliance requirements.

Features:
- Structured JSON logging for machine parsing
- Human-readable console output
- Tamper-evident log chain (hash chaining)
- Configurable log levels and destinations
- Automatic log rotation
- Session context tracking
- Compliance-ready audit trails

Usage:
    from vection.security.audit_logger import AuditLogger, SecurityEventType

    logger = AuditLogger()
    logger.log_event(
        event_type=SecurityEventType.SESSION_CREATED,
        session_id="ses_abc123",
        details={"user_agent": "..."}
    )
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any


class SecurityEventType(StrEnum):
    """Types of security events that are logged.

    All security-relevant events are categorized for easy filtering
    and analysis in SIEM systems.
    """

    # Session lifecycle
    SESSION_CREATED = "session.created"
    SESSION_ACCESSED = "session.accessed"
    SESSION_DISSOLVED = "session.dissolved"
    SESSION_EXPIRED = "session.expired"

    # Signal operations
    SIGNAL_CREATED = "signal.created"
    SIGNAL_REINFORCED = "signal.reinforced"
    SIGNAL_SHARED = "signal.shared"
    SIGNAL_DECAYED = "signal.decayed"
    SIGNAL_INVALIDATED = "signal.invalidated"

    # Context operations
    CONTEXT_ESTABLISHED = "context.established"
    CONTEXT_UPDATED = "context.updated"
    CONTEXT_QUERIED = "context.queried"
    CONTEXT_PROJECTED = "context.projected"

    # Velocity tracking
    VELOCITY_TRACKED = "velocity.tracked"
    VELOCITY_ANOMALY = "velocity.anomaly"

    # Rate limiting
    RATE_LIMIT_CHECKED = "rate_limit.checked"
    RATE_LIMIT_EXCEEDED = "rate_limit.exceeded"
    RATE_LIMIT_RESET = "rate_limit.reset"

    # Validation
    VALIDATION_PASSED = "validation.passed"
    VALIDATION_FAILED = "validation.failed"
    INPUT_SANITIZED = "input.sanitized"

    # Session isolation
    SESSION_BOUNDARY_CHECK = "session.boundary_check"
    SESSION_BOUNDARY_VIOLATION = "session.boundary_violation"

    # Anomaly detection
    ANOMALY_DETECTED = "anomaly.detected"
    ANOMALY_RESOLVED = "anomaly.resolved"

    # Authentication/Authorization
    AUTH_SUCCESS = "auth.success"
    AUTH_FAILURE = "auth.failure"
    ACCESS_GRANTED = "access.granted"
    ACCESS_DENIED = "access.denied"

    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    CONFIG_CHANGED = "config.changed"

    # Security alerts
    SECURITY_ALERT = "security.alert"
    SECURITY_WARNING = "security.warning"


class EventSeverity(StrEnum):
    """Severity levels for security events."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# Default severity mapping for event types
DEFAULT_SEVERITY: dict[SecurityEventType, EventSeverity] = {
    SecurityEventType.SESSION_CREATED: EventSeverity.INFO,
    SecurityEventType.SESSION_ACCESSED: EventSeverity.DEBUG,
    SecurityEventType.SESSION_DISSOLVED: EventSeverity.INFO,
    SecurityEventType.SESSION_EXPIRED: EventSeverity.INFO,
    SecurityEventType.SIGNAL_CREATED: EventSeverity.DEBUG,
    SecurityEventType.SIGNAL_REINFORCED: EventSeverity.DEBUG,
    SecurityEventType.SIGNAL_SHARED: EventSeverity.INFO,
    SecurityEventType.SIGNAL_DECAYED: EventSeverity.DEBUG,
    SecurityEventType.SIGNAL_INVALIDATED: EventSeverity.WARNING,
    SecurityEventType.CONTEXT_ESTABLISHED: EventSeverity.INFO,
    SecurityEventType.CONTEXT_UPDATED: EventSeverity.DEBUG,
    SecurityEventType.CONTEXT_QUERIED: EventSeverity.DEBUG,
    SecurityEventType.CONTEXT_PROJECTED: EventSeverity.DEBUG,
    SecurityEventType.VELOCITY_TRACKED: EventSeverity.DEBUG,
    SecurityEventType.VELOCITY_ANOMALY: EventSeverity.WARNING,
    SecurityEventType.RATE_LIMIT_CHECKED: EventSeverity.DEBUG,
    SecurityEventType.RATE_LIMIT_EXCEEDED: EventSeverity.WARNING,
    SecurityEventType.RATE_LIMIT_RESET: EventSeverity.DEBUG,
    SecurityEventType.VALIDATION_PASSED: EventSeverity.DEBUG,
    SecurityEventType.VALIDATION_FAILED: EventSeverity.WARNING,
    SecurityEventType.INPUT_SANITIZED: EventSeverity.DEBUG,
    SecurityEventType.SESSION_BOUNDARY_CHECK: EventSeverity.DEBUG,
    SecurityEventType.SESSION_BOUNDARY_VIOLATION: EventSeverity.ERROR,
    SecurityEventType.ANOMALY_DETECTED: EventSeverity.WARNING,
    SecurityEventType.ANOMALY_RESOLVED: EventSeverity.INFO,
    SecurityEventType.AUTH_SUCCESS: EventSeverity.INFO,
    SecurityEventType.AUTH_FAILURE: EventSeverity.WARNING,
    SecurityEventType.ACCESS_GRANTED: EventSeverity.DEBUG,
    SecurityEventType.ACCESS_DENIED: EventSeverity.WARNING,
    SecurityEventType.SYSTEM_STARTUP: EventSeverity.INFO,
    SecurityEventType.SYSTEM_SHUTDOWN: EventSeverity.INFO,
    SecurityEventType.CONFIG_CHANGED: EventSeverity.WARNING,
    SecurityEventType.SECURITY_ALERT: EventSeverity.ERROR,
    SecurityEventType.SECURITY_WARNING: EventSeverity.WARNING,
}


@dataclass
class AuditEvent:
    """A structured audit log event.

    Provides all information needed for security analysis and compliance.
    Includes tamper-evident hash chaining.

    Attributes:
        event_id: Unique identifier for this event.
        timestamp: ISO 8601 timestamp in UTC.
        event_type: Category of security event.
        severity: Event severity level.
        session_id: Associated session (if any).
        user_id: Associated user (if any).
        source_ip: Source IP address (if available).
        details: Additional event-specific details.
        previous_hash: Hash of the previous event (for chain integrity).
        event_hash: Hash of this event (computed after creation).
    """

    event_id: str
    timestamp: str
    event_type: SecurityEventType
    severity: EventSeverity
    session_id: str | None = None
    user_id: str | None = None
    source_ip: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    previous_hash: str = ""
    event_hash: str = ""

    def compute_hash(self) -> str:
        """Compute tamper-evident hash of this event.

        Returns:
            SHA-256 hash of event contents.
        """
        content = (
            f"{self.event_id}|{self.timestamp}|{self.event_type.value}|"
            f"{self.severity.value}|{self.session_id}|{self.user_id}|"
            f"{self.source_ip}|{json.dumps(self.details, sort_keys=True)}|"
            f"{self.previous_hash}"
        )
        return hashlib.sha256(content.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the event.
        """
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "source_ip": self.source_ip,
            "details": self.details,
            "previous_hash": self.previous_hash,
            "event_hash": self.event_hash,
        }

    def to_json(self, indent: int | None = None) -> str:
        """Convert to JSON string.

        Args:
            indent: JSON indentation (None for compact).

        Returns:
            JSON string representation.
        """
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuditEvent:
        """Create AuditEvent from dictionary.

        Args:
            data: Dictionary with event data.

        Returns:
            AuditEvent instance.
        """
        return cls(
            event_id=data["event_id"],
            timestamp=data["timestamp"],
            event_type=SecurityEventType(data["event_type"]),
            severity=EventSeverity(data["severity"]),
            session_id=data.get("session_id"),
            user_id=data.get("user_id"),
            source_ip=data.get("source_ip"),
            details=data.get("details", {}),
            previous_hash=data.get("previous_hash", ""),
            event_hash=data.get("event_hash", ""),
        )


@dataclass
class AuditLoggerConfig:
    """Configuration for the audit logger.

    Attributes:
        log_dir: Directory for log files.
        log_file_name: Base name for log files.
        max_file_size_mb: Maximum size before rotation.
        backup_count: Number of rotated files to keep.
        log_to_console: Whether to also log to console.
        log_to_file: Whether to log to file.
        min_severity: Minimum severity to log.
        enable_hash_chain: Whether to compute hash chains.
        json_format: Whether to use JSON format (vs human-readable).
    """

    log_dir: str = "logs/security"
    log_file_name: str = "vection_audit.log"
    max_file_size_mb: int = 50
    backup_count: int = 10
    log_to_console: bool = True
    log_to_file: bool = True
    min_severity: EventSeverity = EventSeverity.DEBUG
    enable_hash_chain: bool = True
    json_format: bool = True


class AuditLogger:
    """Comprehensive audit logger for security events.

    Provides structured, tamper-evident logging for all security-relevant
    events. Supports multiple output destinations and formats.

    Thread-safe and suitable for concurrent use.

    Usage:
        logger = AuditLogger()
        logger.log_event(
            event_type=SecurityEventType.SESSION_CREATED,
            session_id="ses_123",
            details={"source": "api"}
        )
    """

    def __init__(self, config: AuditLoggerConfig | None = None) -> None:
        """Initialize the audit logger.

        Args:
            config: Logger configuration (uses defaults if None).
        """
        self.config = config or AuditLoggerConfig()
        self._lock = threading.Lock()
        self._event_count = 0
        self._last_hash = "genesis"
        self._callbacks: list[Callable[[AuditEvent], None]] = []

        # Set up Python logging
        self._logger = logging.getLogger("vection.security.audit")
        self._logger.setLevel(logging.DEBUG)
        self._logger.handlers.clear()

        # Console handler
        if self.config.log_to_console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(self._severity_to_logging_level(self.config.min_severity))
            if self.config.json_format:
                console_handler.setFormatter(logging.Formatter("%(message)s"))
            else:
                console_handler.setFormatter(
                    logging.Formatter(
                        "%(asctime)s | %(levelname)-8s | %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S",
                    )
                )
            self._logger.addHandler(console_handler)

        # File handler with rotation
        if self.config.log_to_file:
            log_path = Path(self.config.log_dir)
            log_path.mkdir(parents=True, exist_ok=True)
            file_path = log_path / self.config.log_file_name

            file_handler = RotatingFileHandler(
                filename=str(file_path),
                maxBytes=self.config.max_file_size_mb * 1024 * 1024,
                backupCount=self.config.backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(logging.Formatter("%(message)s"))
            self._logger.addHandler(file_handler)

        # Log startup
        self.log_event(
            event_type=SecurityEventType.SYSTEM_STARTUP,
            details={
                "component": "AuditLogger",
                "config": {
                    "log_dir": self.config.log_dir,
                    "min_severity": self.config.min_severity.value,
                    "hash_chain_enabled": self.config.enable_hash_chain,
                },
            },
        )

    def log_event(
        self,
        event_type: SecurityEventType,
        session_id: str | None = None,
        user_id: str | None = None,
        source_ip: str | None = None,
        details: dict[str, Any] | None = None,
        severity: EventSeverity | None = None,
    ) -> AuditEvent:
        """Log a security event.

        Args:
            event_type: Type of security event.
            session_id: Associated session ID.
            user_id: Associated user ID.
            source_ip: Source IP address.
            details: Additional event details.
            severity: Override default severity.

        Returns:
            The created AuditEvent.
        """
        with self._lock:
            self._event_count += 1

            # Generate event ID
            event_id = self._generate_event_id()

            # Determine severity
            if severity is None:
                severity = DEFAULT_SEVERITY.get(event_type, EventSeverity.INFO)

            # Check minimum severity
            if self._severity_level(severity) < self._severity_level(self.config.min_severity):
                # Still create event but don't log
                return AuditEvent(
                    event_id=event_id,
                    timestamp=datetime.now(UTC).isoformat(),
                    event_type=event_type,
                    severity=severity,
                    session_id=session_id,
                    user_id=user_id,
                    source_ip=source_ip,
                    details=details or {},
                )

            # Create event
            event = AuditEvent(
                event_id=event_id,
                timestamp=datetime.now(UTC).isoformat(),
                event_type=event_type,
                severity=severity,
                session_id=session_id,
                user_id=user_id,
                source_ip=source_ip,
                details=details or {},
                previous_hash=self._last_hash if self.config.enable_hash_chain else "",
            )

            # Compute hash
            if self.config.enable_hash_chain:
                event.event_hash = event.compute_hash()
                self._last_hash = event.event_hash

            # Log the event
            log_level = self._severity_to_logging_level(severity)
            if self.config.json_format:
                self._logger.log(log_level, event.to_json())
            else:
                self._logger.log(log_level, self._format_human_readable(event))

            # Notify callbacks
            for callback in self._callbacks:
                try:
                    callback(event)
                except Exception as e:
                    self._logger.warning(f"Audit callback error: {e}")

            return event

    def log_session_event(
        self,
        event_type: SecurityEventType,
        session_id: str,
        details: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Convenience method for session-related events.

        Args:
            event_type: Type of session event.
            session_id: Session identifier.
            details: Additional details.

        Returns:
            The created AuditEvent.
        """
        return self.log_event(
            event_type=event_type,
            session_id=session_id,
            details=details,
        )

    def log_signal_event(
        self,
        event_type: SecurityEventType,
        session_id: str,
        signal_id: str,
        details: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Convenience method for signal-related events.

        Args:
            event_type: Type of signal event.
            session_id: Session identifier.
            signal_id: Signal identifier.
            details: Additional details.

        Returns:
            The created AuditEvent.
        """
        event_details = {"signal_id": signal_id}
        if details:
            event_details.update(details)

        return self.log_event(
            event_type=event_type,
            session_id=session_id,
            details=event_details,
        )

    def log_rate_limit_event(
        self,
        event_type: SecurityEventType,
        session_id: str,
        operation: str,
        current_count: int,
        limit: int,
        window_seconds: float,
    ) -> AuditEvent:
        """Log a rate limiting event.

        Args:
            event_type: RATE_LIMIT_CHECKED or RATE_LIMIT_EXCEEDED.
            session_id: Session identifier.
            operation: Operation being rate limited.
            current_count: Current request count.
            limit: Maximum allowed requests.
            window_seconds: Time window in seconds.

        Returns:
            The created AuditEvent.
        """
        return self.log_event(
            event_type=event_type,
            session_id=session_id,
            details={
                "operation": operation,
                "current_count": current_count,
                "limit": limit,
                "window_seconds": window_seconds,
                "utilization_percent": round((current_count / limit) * 100, 2) if limit > 0 else 0,
            },
        )

    def log_validation_event(
        self,
        passed: bool,
        session_id: str | None,
        field_name: str,
        reason: str | None = None,
        original_value: str | None = None,
    ) -> AuditEvent:
        """Log an input validation event.

        Args:
            passed: Whether validation passed.
            session_id: Session identifier.
            field_name: Name of the validated field.
            reason: Reason for failure (if failed).
            original_value: Sanitized representation of original value.

        Returns:
            The created AuditEvent.
        """
        event_type = SecurityEventType.VALIDATION_PASSED if passed else SecurityEventType.VALIDATION_FAILED
        details: dict[str, Any] = {"field_name": field_name}

        if reason:
            details["reason"] = reason
        if original_value:
            # Truncate for safety
            details["original_value_preview"] = (
                original_value[:100] + "..." if len(original_value) > 100 else original_value
            )

        return self.log_event(
            event_type=event_type,
            session_id=session_id,
            details=details,
        )

    def log_anomaly(
        self,
        anomaly_type: str,
        session_id: str,
        description: str,
        severity: EventSeverity = EventSeverity.WARNING,
        metrics: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Log an anomaly detection event.

        Args:
            anomaly_type: Type of anomaly detected.
            session_id: Session identifier.
            description: Human-readable description.
            severity: Event severity.
            metrics: Quantitative metrics about the anomaly.

        Returns:
            The created AuditEvent.
        """
        return self.log_event(
            event_type=SecurityEventType.ANOMALY_DETECTED,
            session_id=session_id,
            severity=severity,
            details={
                "anomaly_type": anomaly_type,
                "description": description,
                "metrics": metrics or {},
            },
        )

    def log_security_alert(
        self,
        alert_type: str,
        description: str,
        session_id: str | None = None,
        severity: EventSeverity = EventSeverity.ERROR,
        recommended_action: str | None = None,
    ) -> AuditEvent:
        """Log a security alert.

        Args:
            alert_type: Type of security alert.
            description: Detailed description.
            session_id: Associated session (if any).
            severity: Alert severity.
            recommended_action: Suggested response action.

        Returns:
            The created AuditEvent.
        """
        details: dict[str, Any] = {
            "alert_type": alert_type,
            "description": description,
        }
        if recommended_action:
            details["recommended_action"] = recommended_action

        return self.log_event(
            event_type=SecurityEventType.SECURITY_ALERT,
            session_id=session_id,
            severity=severity,
            details=details,
        )

    def add_callback(self, callback: Callable[[AuditEvent], None]) -> None:
        """Add a callback to be notified of all audit events.

        Useful for SIEM integration or real-time alerting.

        Args:
            callback: Function to call with each AuditEvent.
        """
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[AuditEvent], None]) -> None:
        """Remove a previously added callback.

        Args:
            callback: Callback to remove.
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def get_stats(self) -> dict[str, Any]:
        """Get logger statistics.

        Returns:
            Dictionary with logger stats.
        """
        return {
            "event_count": self._event_count,
            "last_hash": self._last_hash[:16] + "..." if self._last_hash != "genesis" else "genesis",
            "callback_count": len(self._callbacks),
            "config": {
                "min_severity": self.config.min_severity.value,
                "hash_chain_enabled": self.config.enable_hash_chain,
                "json_format": self.config.json_format,
            },
        }

    def verify_chain_integrity(self, events: list[AuditEvent]) -> tuple[bool, list[str]]:
        """Verify the integrity of a chain of events.

        Args:
            events: List of events to verify (in order).

        Returns:
            Tuple of (is_valid, list of error messages).
        """
        if not events:
            return True, []

        errors: list[str] = []

        for i, event in enumerate(events):
            # Recompute hash
            expected_hash = event.compute_hash()
            if event.event_hash != expected_hash:
                errors.append(f"Event {event.event_id}: hash mismatch (tampering detected)")

            # Verify chain linkage
            if i > 0:
                if event.previous_hash != events[i - 1].event_hash:
                    errors.append(f"Event {event.event_id}: chain break (missing or reordered event)")

        return len(errors) == 0, errors

    def _generate_event_id(self) -> str:
        """Generate a unique event ID."""
        timestamp = int(time.time() * 1000000)
        return f"evt_{timestamp}_{self._event_count:08d}"

    def _severity_level(self, severity: EventSeverity) -> int:
        """Convert severity to numeric level."""
        levels = {
            EventSeverity.DEBUG: 0,
            EventSeverity.INFO: 1,
            EventSeverity.WARNING: 2,
            EventSeverity.ERROR: 3,
            EventSeverity.CRITICAL: 4,
        }
        return levels.get(severity, 1)

    def _severity_to_logging_level(self, severity: EventSeverity) -> int:
        """Convert EventSeverity to Python logging level."""
        mapping = {
            EventSeverity.DEBUG: logging.DEBUG,
            EventSeverity.INFO: logging.INFO,
            EventSeverity.WARNING: logging.WARNING,
            EventSeverity.ERROR: logging.ERROR,
            EventSeverity.CRITICAL: logging.CRITICAL,
        }
        return mapping.get(severity, logging.INFO)

    def _format_human_readable(self, event: AuditEvent) -> str:
        """Format event for human-readable output."""
        parts = [
            f"[{event.event_type.value}]",
        ]

        if event.session_id:
            parts.append(f"session={event.session_id}")

        if event.user_id:
            parts.append(f"user={event.user_id}")

        if event.details:
            detail_str = ", ".join(f"{k}={v}" for k, v in list(event.details.items())[:5])
            parts.append(f"details=({detail_str})")

        return " | ".join(parts)


# Module-level singleton
_audit_logger: AuditLogger | None = None


def get_audit_logger(config: AuditLoggerConfig | None = None) -> AuditLogger:
    """Get the global audit logger instance.

    Args:
        config: Configuration (only used on first call).

    Returns:
        AuditLogger singleton.
    """
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger(config)
    return _audit_logger
