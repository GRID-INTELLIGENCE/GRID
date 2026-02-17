"""VECTION Security Module.

Provides comprehensive security infrastructure for the VECTION context emergence engine.
Implements industry-standard security practices:

- Rate Limiting: Prevents abuse through configurable request throttling
- Input Validation: Sanitizes all inputs to prevent injection attacks
- Session Isolation: Enforces strict session boundaries
- Audit Logging: Comprehensive, transparent logging for security review
- Anomaly Detection: Pattern-based detection of suspicious activity
- Security Events: Structured security event emission for SIEM integration

All security measures are transparent and follow the principle of least surprise.
Logging is explicit and auditable - no hidden tracking or covert operations.

Usage:
    from vection.security import (
        SecurityManager,
        get_security_manager,
        RateLimiter,
        InputValidator,
        SessionIsolator,
        AuditLogger,
        AnomalyDetector,
    )

    # Initialize security manager
    security = get_security_manager()

    # Check rate limit before operation
    if not security.rate_limiter.allow(session_id, operation="reinforce"):
        raise RateLimitExceeded("Too many reinforce calls")

    # Validate input
    validated = security.validator.validate_signal_metadata(metadata)

    # Log security event
    security.audit.log_event(
        event_type=SecurityEventType.SIGNAL_CREATED,
        session_id=session_id,
        details={"signal_id": signal.signal_id}
    )
"""

from __future__ import annotations

__version__ = "1.0.0"

__all__ = [
    # Core security manager
    "SecurityManager",
    "get_security_manager",
    "SecurityConfig",
    # Rate limiting
    "RateLimiter",
    "RateLimitConfig",
    "RateLimitExceeded",
    # Input validation
    "InputValidator",
    "ValidationError",
    "ValidationResult",
    # Session isolation
    "SessionIsolator",
    "SessionBoundaryViolation",
    # Audit logging
    "AuditLogger",
    "AuditEvent",
    "SecurityEventType",
    # Anomaly detection
    "AnomalyDetector",
    "AnomalyAlert",
    "AnomalyType",
    # Security events
    "SecurityEvent",
    "SecurityEventEmitter",
]

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .anomaly_detector import AnomalyAlert, AnomalyDetector, AnomalyType
    from .audit_logger import AuditEvent, AuditLogger, SecurityEventType
    from .events import SecurityEvent, SecurityEventEmitter
    from .input_validator import InputValidator, ValidationError, ValidationResult
    from .manager import SecurityConfig, SecurityManager
    from .rate_limiter import RateLimitConfig, RateLimiter, RateLimitExceeded
    from .session_isolator import SessionBoundaryViolation, SessionIsolator


# Lazy imports to avoid circular dependencies
_security_manager: Any = None


def __getattr__(name: str) -> Any:
    """Lazy import mechanism for security components."""
    if name == "SecurityManager":
        from .manager import SecurityManager

        return SecurityManager

    if name == "get_security_manager":
        from .manager import get_security_manager

        return get_security_manager

    if name == "SecurityConfig":
        from .manager import SecurityConfig

        return SecurityConfig

    if name == "RateLimiter":
        from .rate_limiter import RateLimiter

        return RateLimiter

    if name == "RateLimitConfig":
        from .rate_limiter import RateLimitConfig

        return RateLimitConfig

    if name == "RateLimitExceeded":
        from .rate_limiter import RateLimitExceeded

        return RateLimitExceeded

    if name == "InputValidator":
        from .input_validator import InputValidator

        return InputValidator

    if name == "ValidationError":
        from .input_validator import ValidationError

        return ValidationError

    if name == "ValidationResult":
        from .input_validator import ValidationResult

        return ValidationResult

    if name == "SessionIsolator":
        from .session_isolator import SessionIsolator

        return SessionIsolator

    if name == "SessionBoundaryViolation":
        from .session_isolator import SessionBoundaryViolation

        return SessionBoundaryViolation

    if name == "AuditLogger":
        from .audit_logger import AuditLogger

        return AuditLogger

    if name == "AuditEvent":
        from .audit_logger import AuditEvent

        return AuditEvent

    if name == "SecurityEventType":
        from .audit_logger import SecurityEventType

        return SecurityEventType

    if name == "AnomalyDetector":
        from .anomaly_detector import AnomalyDetector

        return AnomalyDetector

    if name == "AnomalyAlert":
        from .anomaly_detector import AnomalyAlert

        return AnomalyAlert

    if name == "AnomalyType":
        from .anomaly_detector import AnomalyType

        return AnomalyType

    if name == "SecurityEvent":
        from .events import SecurityEvent

        return SecurityEvent

    if name == "SecurityEventEmitter":
        from .events import SecurityEventEmitter

        return SecurityEventEmitter

    raise AttributeError(f"module 'vection.security' has no attribute {name!r}")


def get_security_manager() -> Any:
    """Get the global security manager instance.

    Returns:
        SecurityManager: Singleton security manager.
    """
    global _security_manager
    if _security_manager is None:
        from .manager import SecurityManager

        _security_manager = SecurityManager()
    return _security_manager
