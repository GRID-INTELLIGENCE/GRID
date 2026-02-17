"""Error Classification System for GRID Agentic System.

Categorizes execution errors into meaningful taxonomies to enable targeted
recovery strategies and behavioral analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ErrorCategory(StrEnum):
    """Broad categories of errors encountered during agent execution."""

    TRANSIENT = "transient"  # Temporary network, timeout
    VALIDATION = "validation"  # Invalid input, schema error
    RESOURCE = "resource"  # Rate limit, out of memory
    LOGIC = "logic"  # Agent logic error, hallucination detection
    DEPENDENCY = "dependency"  # External service or tool failure
    SECURITY = "security"  # Permission or safety filter violation
    COMPLIANCE = "compliance"  # Guardian rule violation, safety policy breach
    UNKNOWN = "unknown"


class ErrorSeverity(StrEnum):
    """Severity levels for errors."""

    LOW = "low"  # Can be ignored or retried silently
    MEDIUM = "medium"  # Requires fallback or user notification
    HIGH = "high"  # Requires immediate stop or circuit break
    CRITICAL = "critical"  # System-wide danger


@dataclass
class ErrorContext:
    """Detailed context for a specific execution error."""

    error_type: str
    category: ErrorCategory
    severity: ErrorSeverity
    recoverable: bool
    message: str
    suggested_retries: int = 3
    fallback_strategy: str = "default"
    metadata: dict[str, Any] = field(default_factory=dict)


class ErrorClassifier:
    """Classifies exceptions into structured ErrorContext objects."""

    @staticmethod
    def classify(error: Exception, context_data: dict[str, Any] | None = None) -> ErrorContext:
        """Classify a Python exception into an ErrorContext."""
        error_name = type(error).__name__
        message = str(error)

        # Default classification
        category = ErrorCategory.UNKNOWN
        severity = ErrorSeverity.MEDIUM
        recoverable = True
        suggested_retries = 3
        fallback_strategy = "retry"

        # Classification Logic
        if "timeout" in message.lower() or "Timeout" in error_name:
            category = ErrorCategory.TRANSIENT
            severity = ErrorSeverity.LOW
            fallback_strategy = "retry_with_backoff"

        elif "rate limit" in message.lower() or "quota" in message.lower():
            category = ErrorCategory.RESOURCE
            severity = ErrorSeverity.MEDIUM
            recoverable = True
            suggested_retries = 5
            fallback_strategy = "slow_retry"

        elif "permission" in message.lower() or "denied" in message.lower() or "Forbidden" in error_name:
            category = ErrorCategory.SECURITY
            severity = ErrorSeverity.HIGH
            recoverable = False
            fallback_strategy = "abort"

        elif "validation" in message.lower() or "schema" in message.lower() or "ValueError" in error_name:
            category = ErrorCategory.VALIDATION
            severity = ErrorSeverity.LOW
            recoverable = True
            fallback_strategy = "fix_and_retry"

        elif "Connection" in error_name:
            category = ErrorCategory.DEPENDENCY
            severity = ErrorSeverity.MEDIUM
            recoverable = True
            fallback_strategy = "circuit_break"

        elif any(kw in message.lower() for kw in ("guardian", "safety", "blocked", "compliance", "rule violation")):
            category = ErrorCategory.COMPLIANCE
            severity = ErrorSeverity.HIGH
            recoverable = False
            suggested_retries = 0
            fallback_strategy = "abort"
        return ErrorContext(
            error_type=error_name,
            category=category,
            severity=severity,
            recoverable=recoverable,
            message=message,
            suggested_retries=suggested_retries,
            fallback_strategy=fallback_strategy,
            metadata=context_data or {},
        )
