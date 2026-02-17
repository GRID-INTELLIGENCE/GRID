"""Security Manager - Orchestrates all security components.

Provides a unified interface for VECTION security operations,
coordinating rate limiting, input validation, session isolation,
anomaly detection, and audit logging.

Features:
- Unified security configuration
- Coordinated security checks
- Centralized security statistics
- Security event handling
- Component lifecycle management
- Integration with VECTION core

Usage:
    from vection.security.manager import SecurityManager, get_security_manager

    # Get the global security manager
    security = get_security_manager()

    # Perform security checks
    security.validate_request(session_id, event_data)

    # Check rate limits
    if not security.check_rate_limit(session_id, "reinforce"):
        raise RateLimitExceeded("Too many requests")

    # Get security stats
    stats = security.get_stats()
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from vection.security.anomaly_detector import (
    AnomalyAlert,
    AnomalyDetector,
    AnomalyDetectorConfig,
    AnomalyType,
    get_anomaly_detector,
)
from vection.security.audit_logger import (
    AuditEvent,
    AuditLogger,
    AuditLoggerConfig,
    SecurityEventType,
    get_audit_logger,
)
from vection.security.input_validator import (
    InputValidator,
    InputValidatorConfig,
    ValidationError,
    ValidationResult,
    get_input_validator,
)
from vection.security.rate_limiter import (
    RateLimitConfig,
    RateLimiter,
    RateLimitStatus,
    get_rate_limiter,
)
from vection.security.session_isolator import (
    AccessType,
    SessionIsolator,
    SessionIsolatorConfig,
    get_session_isolator,
)

logger = logging.getLogger(__name__)


@dataclass
class SecurityConfig:
    """Configuration for the security manager.

    Attributes:
        enabled: Whether security checks are enabled.
        rate_limit_config: Rate limiter configuration.
        validator_config: Input validator configuration.
        isolator_config: Session isolator configuration.
        anomaly_config: Anomaly detector configuration.
        audit_config: Audit logger configuration.
        fail_open: Whether to allow operations if security check fails.
        log_all_requests: Whether to log all requests (high volume).
        block_on_anomaly: Whether to block on anomaly detection.
        anomaly_block_severity: Minimum severity to trigger block.
    """

    enabled: bool = True
    rate_limit_config: RateLimitConfig | None = None
    validator_config: InputValidatorConfig | None = None
    isolator_config: SessionIsolatorConfig | None = None
    anomaly_config: AnomalyDetectorConfig | None = None
    audit_config: AuditLoggerConfig | None = None
    fail_open: bool = False
    log_all_requests: bool = False
    block_on_anomaly: bool = False
    anomaly_block_severity: str = "high"


@dataclass
class SecurityCheckResult:
    """Result of a comprehensive security check.

    Attributes:
        allowed: Whether the operation is allowed.
        rate_limit_status: Rate limit check result.
        validation_result: Input validation result.
        isolation_allowed: Session isolation check result.
        anomaly_alerts: Any anomaly alerts generated.
        blocked_reason: Reason if operation was blocked.
        warnings: Non-blocking warnings.
    """

    allowed: bool = True
    rate_limit_status: RateLimitStatus | None = None
    validation_result: ValidationResult | None = None
    isolation_allowed: bool = True
    anomaly_alerts: list[AnomalyAlert] = field(default_factory=list)
    blocked_reason: str | None = None
    warnings: list[str] = field(default_factory=list)

    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)

    def block(self, reason: str) -> None:
        """Block the operation with a reason."""
        self.allowed = False
        self.blocked_reason = reason

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "allowed": self.allowed,
            "blocked_reason": self.blocked_reason,
            "rate_limit": self.rate_limit_status.to_dict() if self.rate_limit_status else None,
            "validation": self.validation_result.to_dict() if self.validation_result else None,
            "isolation_allowed": self.isolation_allowed,
            "anomaly_count": len(self.anomaly_alerts),
            "warnings": self.warnings,
        }


class SecurityManager:
    """Unified security manager for VECTION.

    Orchestrates all security components and provides a single
    interface for security operations.

    Thread-safe and suitable for concurrent use.

    Usage:
        manager = SecurityManager()

        # Full security check
        result = manager.check_request(session_id, operation, data)
        if not result.allowed:
            return error_response(result.blocked_reason)

        # Individual component access
        manager.rate_limiter.require(session_id, operation)
        manager.validator.validate_metadata(data)
    """

    def __init__(self, config: SecurityConfig | None = None) -> None:
        """Initialize the security manager.

        Args:
            config: Security configuration.
        """
        self.config = config or SecurityConfig()
        self._lock = threading.Lock()

        # Initialize components with configurations
        self._rate_limiter = get_rate_limiter(self.config.rate_limit_config)
        self._validator = get_input_validator(self.config.validator_config)
        self._isolator = get_session_isolator(self.config.isolator_config)
        self._anomaly_detector = get_anomaly_detector(self.config.anomaly_config)
        self._audit_logger = get_audit_logger(self.config.audit_config)

        # Statistics
        self._total_checks = 0
        self._total_blocked = 0
        self._started_at = datetime.now(UTC)

        # Callbacks
        self._security_callbacks: list[Callable[[SecurityCheckResult], None]] = []

        # Register anomaly callback for blocking
        if self.config.block_on_anomaly:
            self._anomaly_detector.on_anomaly(self._handle_anomaly_alert)

        # Log startup
        self._audit_logger.log_event(
            event_type=SecurityEventType.SYSTEM_STARTUP,
            details={
                "component": "SecurityManager",
                "config": {
                    "enabled": self.config.enabled,
                    "fail_open": self.config.fail_open,
                    "block_on_anomaly": self.config.block_on_anomaly,
                },
            },
        )

        logger.info("SecurityManager initialized")

    @property
    def rate_limiter(self) -> RateLimiter:
        """Get the rate limiter component."""
        return self._rate_limiter

    @property
    def validator(self) -> InputValidator:
        """Get the input validator component."""
        return self._validator

    @property
    def isolator(self) -> SessionIsolator:
        """Get the session isolator component."""
        return self._isolator

    @property
    def anomaly_detector(self) -> AnomalyDetector:
        """Get the anomaly detector component."""
        return self._anomaly_detector

    @property
    def audit(self) -> AuditLogger:
        """Get the audit logger component."""
        return self._audit_logger

    def check_request(
        self,
        session_id: str,
        operation: str,
        data: dict[str, Any] | None = None,
        target_session: str | None = None,
    ) -> SecurityCheckResult:
        """Perform comprehensive security check for a request.

        Args:
            session_id: Session making the request.
            operation: Operation being performed.
            data: Optional request data to validate.
            target_session: Target session for cross-session operations.

        Returns:
            SecurityCheckResult with all check results.
        """
        result = SecurityCheckResult()

        if not self.config.enabled:
            return result

        with self._lock:
            self._total_checks += 1

        try:
            # Rate limit check
            rate_status = self._rate_limiter.check(session_id, operation)
            result.rate_limit_status = rate_status

            if not rate_status.allowed:
                result.block(f"Rate limit exceeded for operation '{operation}'")
                self._record_blocked("rate_limit", session_id, operation)
                return result

            # Input validation
            if data is not None:
                validation = self._validator.validate_metadata(data)
                result.validation_result = validation

                if not validation.is_valid:
                    result.block("Input validation failed")
                    self._record_blocked("validation", session_id, operation)
                    return result

                # Add any validation warnings
                for warning in validation.warnings:
                    result.add_warning(f"Validation: {warning}")

            # Session isolation check
            if target_session is not None and target_session != session_id:
                isolation_allowed = self._isolator.can_access(
                    source_session=session_id,
                    target_session=target_session,
                    access_type=self._operation_to_access_type(operation),
                )
                result.isolation_allowed = isolation_allowed

                if not isolation_allowed:
                    result.block(f"Session boundary violation: cannot access session '{target_session}'")
                    self._record_blocked("isolation", session_id, operation)
                    return result

            # Anomaly detection (non-blocking by default)
            # Specific anomaly checks are performed elsewhere;
            # this just checks for any active critical alerts
            if self.config.block_on_anomaly:
                active_alerts = self._anomaly_detector.get_active_alerts(session_id)
                critical_alerts = [a for a in active_alerts if a.severity.value in ("high", "critical")]
                result.anomaly_alerts = critical_alerts

                if critical_alerts:
                    result.block(f"Session has {len(critical_alerts)} active security alerts")
                    self._record_blocked("anomaly", session_id, operation)
                    return result

            # Log the request if configured
            if self.config.log_all_requests:
                self._audit_logger.log_event(
                    event_type=SecurityEventType.SESSION_ACCESSED,
                    session_id=session_id,
                    details={
                        "operation": operation,
                        "target_session": target_session,
                        "has_data": data is not None,
                    },
                )

            # Notify callbacks
            self._notify_callbacks(result)

            return result

        except Exception as e:
            logger.error(f"Security check error: {e}")
            if self.config.fail_open:
                result.add_warning(f"Security check failed, allowing due to fail_open: {e}")
                return result
            else:
                result.block(f"Security check error: {e}")
                return result

    def check_rate_limit(
        self,
        session_id: str,
        operation: str,
        consume: bool = True,
    ) -> bool:
        """Check rate limit for an operation.

        Args:
            session_id: Session identifier.
            operation: Operation type.
            consume: Whether to consume quota.

        Returns:
            True if allowed, False if rate limited.
        """
        if not self.config.enabled:
            return True
        return self._rate_limiter.allow(session_id, operation, consume)

    def validate_input(
        self,
        data: dict[str, Any],
        require_valid: bool = True,
    ) -> ValidationResult:
        """Validate input data.

        Args:
            data: Data to validate.
            require_valid: Whether to raise exception on failure.

        Returns:
            ValidationResult.

        Raises:
            ValidationError: If validation fails and require_valid is True.
        """
        result = self._validator.validate_metadata(data)
        if require_valid and not result.is_valid:
            raise ValidationError(
                "Input validation failed",
                errors=result.errors,
            )
        return result

    def check_session_access(
        self,
        source_session: str,
        target_session: str,
        access_type: AccessType = AccessType.READ,
        resource_type: str = "signal",
    ) -> bool:
        """Check if session can access another session's resources.

        Args:
            source_session: Session requesting access.
            target_session: Session being accessed.
            access_type: Type of access.
            resource_type: Type of resource.

        Returns:
            True if access is allowed.
        """
        if not self.config.enabled:
            return True
        return self._isolator.can_access(source_session, target_session, access_type, resource_type)

    def require_session_access(
        self,
        source_session: str,
        target_session: str,
        access_type: AccessType = AccessType.READ,
        resource_type: str = "signal",
    ) -> None:
        """Require session access, raising exception if denied.

        Args:
            source_session: Session requesting access.
            target_session: Session being accessed.
            access_type: Type of access.
            resource_type: Type of resource.

        Raises:
            SessionBoundaryViolation: If access is denied.
        """
        if not self.config.enabled:
            return
        self._isolator.require_session_access(source_session, target_session, access_type, resource_type)

    def check_anomaly(
        self,
        session_id: str,
        anomaly_type: AnomalyType,
        **kwargs: Any,
    ) -> AnomalyAlert | None:
        """Perform an anomaly check.

        Args:
            session_id: Session identifier.
            anomaly_type: Type of anomaly to check.
            **kwargs: Additional arguments for the specific check.

        Returns:
            AnomalyAlert if anomaly detected, None otherwise.
        """
        if not self.config.enabled:
            return None

        # Route to appropriate check method
        if anomaly_type == AnomalyType.BURST_REINFORCEMENT:
            return self._anomaly_detector.check_reinforcement_burst(
                session_id,
                signal_id=kwargs.get("signal_id"),
                count=kwargs.get("count"),
                window_seconds=kwargs.get("window_seconds"),
            )
        elif anomaly_type == AnomalyType.SIGNAL_FLOODING:
            return self._anomaly_detector.check_signal_flood(
                session_id,
                signals_per_minute=kwargs.get("signals_per_minute"),
            )
        elif anomaly_type == AnomalyType.TIMESTAMP_MANIPULATION:
            return self._anomaly_detector.check_timestamp_anomaly(
                session_id,
                timestamps=kwargs.get("timestamps", []),
            )
        else:
            return self._anomaly_detector.check_custom(
                session_id,
                condition=kwargs.get("condition", False),
                anomaly_type=anomaly_type,
                description=kwargs.get("description", ""),
            )

    def log_security_event(
        self,
        event_type: SecurityEventType,
        session_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Log a security event.

        Args:
            event_type: Type of security event.
            session_id: Associated session.
            details: Event details.

        Returns:
            The created AuditEvent.
        """
        return self._audit_logger.log_event(
            event_type=event_type,
            session_id=session_id,
            details=details,
        )

    def log_security_alert(
        self,
        alert_type: str,
        description: str,
        session_id: str | None = None,
        recommended_action: str | None = None,
    ) -> AuditEvent:
        """Log a security alert.

        Args:
            alert_type: Type of alert.
            description: Alert description.
            session_id: Associated session.
            recommended_action: Suggested action.

        Returns:
            The created AuditEvent.
        """
        return self._audit_logger.log_security_alert(
            alert_type=alert_type,
            description=description,
            session_id=session_id,
            recommended_action=recommended_action,
        )

    def create_session_grant(
        self,
        source_session: str,
        target_session: str,
        access_types: set[AccessType] | None = None,
        expiry_hours: float | None = None,
    ) -> Any:
        """Create a cross-session access grant.

        Args:
            source_session: Session granting access.
            target_session: Session receiving access.
            access_types: Allowed access types.
            expiry_hours: Hours until grant expires.

        Returns:
            The created SessionGrant.
        """
        return self._isolator.create_grant(
            source_session=source_session,
            target_session=target_session,
            access_types=access_types,
            expiry_hours=expiry_hours,
        )

    def revoke_session_grant(self, grant_id: str) -> bool:
        """Revoke a session access grant.

        Args:
            grant_id: Grant to revoke.

        Returns:
            True if grant was revoked.
        """
        return self._isolator.revoke_grant(grant_id)

    def on_security_event(self, callback: Callable[[SecurityCheckResult], None]) -> None:
        """Register a callback for security check results.

        Args:
            callback: Function called with each security check result.
        """
        self._security_callbacks.append(callback)

    def get_stats(self) -> dict[str, Any]:
        """Get comprehensive security statistics.

        Returns:
            Dictionary with all security component stats.
        """
        uptime = (datetime.now(UTC) - self._started_at).total_seconds()

        return {
            "enabled": self.config.enabled,
            "uptime_seconds": round(uptime, 1),
            "total_checks": self._total_checks,
            "total_blocked": self._total_blocked,
            "block_rate_percent": (
                round((self._total_blocked / self._total_checks) * 100, 2) if self._total_checks > 0 else 0
            ),
            "components": {
                "rate_limiter": self._rate_limiter.get_stats(),
                "validator": self._validator.get_stats(),
                "isolator": self._isolator.get_stats(),
                "anomaly_detector": self._anomaly_detector.get_stats(),
                "audit_logger": self._audit_logger.get_stats(),
            },
            "config": {
                "fail_open": self.config.fail_open,
                "block_on_anomaly": self.config.block_on_anomaly,
                "log_all_requests": self.config.log_all_requests,
            },
        }

    def get_session_security_status(self, session_id: str) -> dict[str, Any]:
        """Get security status for a specific session.

        Args:
            session_id: Session identifier.

        Returns:
            Dictionary with session security status.
        """
        return {
            "session_id": session_id,
            "rate_limits": self._rate_limiter.get_session_status(session_id),
            "active_grants": [g.to_dict() for g in self._isolator.get_grants_for_session(session_id)],
            "active_alerts": [a.to_dict() for a in self._anomaly_detector.get_active_alerts(session_id)],
            "violation_history": [v.to_dict() for v in self._isolator.get_violation_history(session_id, limit=10)],
        }

    def cleanup_session(self, session_id: str) -> dict[str, int]:
        """Clean up security data for a session.

        Args:
            session_id: Session to clean up.

        Returns:
            Dictionary with cleanup counts.
        """
        grants_revoked = self._isolator.revoke_all_grants(session_id)
        self._anomaly_detector.clear_session_data(session_id)
        self._rate_limiter.reset(session_id)

        self._audit_logger.log_event(
            event_type=SecurityEventType.SESSION_DISSOLVED,
            session_id=session_id,
            details={"grants_revoked": grants_revoked},
        )

        return {
            "grants_revoked": grants_revoked,
        }

    def _operation_to_access_type(self, operation: str) -> AccessType:
        """Map operation name to access type.

        Args:
            operation: Operation name.

        Returns:
            AccessType enum value.
        """
        operation_lower = operation.lower()

        if any(kw in operation_lower for kw in ("write", "create", "update", "delete", "reinforce")):
            return AccessType.WRITE
        if any(kw in operation_lower for kw in ("share",)):
            return AccessType.SHARE
        if any(kw in operation_lower for kw in ("query", "search")):
            return AccessType.QUERY

        return AccessType.READ

    def _record_blocked(self, reason: str, session_id: str, operation: str) -> None:
        """Record a blocked operation.

        Args:
            reason: Blocking reason.
            session_id: Session identifier.
            operation: Operation that was blocked.
        """
        with self._lock:
            self._total_blocked += 1

        self._audit_logger.log_event(
            event_type=SecurityEventType.ACCESS_DENIED,
            session_id=session_id,
            details={
                "reason": reason,
                "operation": operation,
            },
        )

    def _handle_anomaly_alert(self, alert: AnomalyAlert) -> None:
        """Handle anomaly alerts for potential blocking.

        Args:
            alert: The anomaly alert.
        """
        # Log critical anomalies
        if alert.severity.value in ("high", "critical"):
            self._audit_logger.log_security_alert(
                alert_type=alert.anomaly_type.value,
                description=alert.description,
                session_id=alert.session_id,
                recommended_action=alert.recommended_action,
            )

    def _notify_callbacks(self, result: SecurityCheckResult) -> None:
        """Notify registered callbacks of security check result.

        Args:
            result: The security check result.
        """
        for callback in self._security_callbacks:
            try:
                callback(result)
            except Exception as e:
                logger.warning(f"Security callback error: {e}")


# Module-level singleton
_security_manager: SecurityManager | None = None


def get_security_manager(config: SecurityConfig | None = None) -> SecurityManager:
    """Get the global security manager instance.

    Args:
        config: Configuration (only used on first call).

    Returns:
        SecurityManager singleton.
    """
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager(config)
    return _security_manager


def reset_security_manager() -> None:
    """Reset the global security manager (for testing)."""
    global _security_manager
    _security_manager = None
