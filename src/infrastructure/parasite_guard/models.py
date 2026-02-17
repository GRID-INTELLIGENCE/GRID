"""
Core data models for Parasite Guard system.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum, auto
from typing import Any


class ParasiteSeverity(StrEnum):
    """Severity levels for parasite detections."""

    CRITICAL = auto()  # Service-impacting
    HIGH = auto()  # Component-impacting
    MEDIUM = auto()  # Observable impact
    LOW = auto()  # Minor impact


@dataclass(frozen=True)
class SourceMap:
    """
    Immutable description of the origin of a parasitic call.

    Used by SourceTraceResolver to locate the seed function/module
    that generated the original offending request.
    """

    module: str  # Module name (e.g., "app.middleware")
    function: str  # Function name (e.g., "websocket_send")
    line: int  # Line number
    file: str  # Full file path
    package: str | None = None  # Package name if applicable
    class_name: str | None = None  # Class name if method


@dataclass
class ParasiteContext:
    """
    All information that survives the whole request lifecycle.

    Created when a detector identifies a parasite, passed through
    profiling, tracing, and sanitization.
    """

    id: uuid.UUID
    component: str  # Component ID (e.g., "websocket", "eventbus")
    pattern: str  # Pattern name (e.g., "no_ack", "leak")
    rule: str  # Detector name that fired
    severity: ParasiteSeverity
    start_ts: datetime = field(default_factory=lambda: datetime.now(UTC))
    end_ts: datetime | None = None

    # Detection details
    source: SourceMap | None = None
    detection_metadata: dict[str, Any] = field(default_factory=dict)

    # Sanitization tracking
    sanitized: bool = False
    sanitization_result: SanitizationResult | None = None

    # Additional metadata
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Ensure id is UUID."""
        if not isinstance(self.id, uuid.UUID):
            object.__setattr__(self, "id", uuid.UUID(self.id) if isinstance(self.id, str) else uuid.uuid4())

    def complete(self, sanitized: bool, result: SanitizationResult | None = None):
        """Mark the parasite as handled."""
        self.end_ts = datetime.now(UTC)
        self.sanitized = sanitized
        self.sanitization_result = result

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            "id": str(self.id),
            "component": self.component,
            "pattern": self.pattern,
            "rule": self.rule,
            "severity": self.severity.name,
            "start_ts": self.start_ts.isoformat(),
            "end_ts": self.end_ts.isoformat() if self.end_ts else None,
            "source": {
                "module": self.source.module,
                "function": self.source.function,
                "line": self.source.line,
                "file": self.source.file,
            }
            if self.source
            else None,
            "detection_metadata": self.detection_metadata,
            "sanitized": self.sanitized,
            "sanitization_result": self.sanitization_result.to_dict() if self.sanitization_result else None,
            "meta": self.meta,
        }


@dataclass
class DetectionResult:
    """Result from a detector."""

    detected: bool
    context: ParasiteContext | None = None
    reason: str = ""
    confidence: float = 1.0  # 0.0 to 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "detected": self.detected,
            "context": self.context.to_dict() if self.context else None,
            "reason": self.reason,
            "confidence": self.confidence,
        }


@dataclass
class SanitizationResult:
    """Result from a sanitizer."""

    success: bool
    steps: list[str] = field(default_factory=list)
    error: str | None = None
    duration_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "steps": self.steps,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
        }


@dataclass
class ParasiteLogEntry:
    """
    Structured log entry for parasite detection/sanitization.

    Used by ParasiteProfiler for consistent log formatting.
    """

    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    parasite_id: str = ""
    event_type: str = "detection"  # detection, profiling, tracing, sanitization
    component: str = ""
    pattern: str = ""
    severity: str = ""
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "parasite_id": self.parasite_id,
            "event_type": self.event_type,
            "component": self.component,
            "pattern": self.pattern,
            "severity": self.severity,
            "message": self.message,
            "data": self.data,
        }
