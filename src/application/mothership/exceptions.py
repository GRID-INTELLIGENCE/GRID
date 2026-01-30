"""
Mothership Cockpit Custom Exceptions.

Hierarchical exception classes for precise error handling
throughout the Mothership Cockpit application.
"""

from __future__ import annotations

from typing import Any


class MothershipError(Exception):
    """Base exception for all Mothership Cockpit errors.

    All custom exceptions in the application should inherit from this class
    to enable catch-all error handling when needed.

    Attributes:
        message: Human-readable error description
        code: Machine-readable error code for API responses
        details: Additional context about the error
        status_code: HTTP status code to return (default 500)
    """

    def __init__(
        self,
        message: str = "An unexpected error occurred",
        code: str = "MOTHERSHIP_ERROR",
        details: dict[str, Any] | None = None,
        status_code: int = 500,
    ) -> None:
        self.message = message
        self.code = code
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Serialize exception for API responses."""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.code!r}, message={self.message!r})"


# =============================================================================
# Configuration Errors
# =============================================================================


class ConfigurationError(MothershipError):
    """Raised when configuration is invalid or missing."""

    def __init__(
        self,
        message: str = "Invalid configuration",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="CONFIGURATION_ERROR",
            details=details,
            status_code=500,
        )


class EnvironmentError(ConfigurationError):
    """Raised when required environment variables are missing."""

    def __init__(self, variable: str) -> None:
        super().__init__(
            message=f"Required environment variable not set: {variable}",
            details={"variable": variable},
        )


# =============================================================================
# Authentication & Authorization Errors
# =============================================================================


class AuthenticationError(MothershipError):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str = "Authentication failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            details=details,
            status_code=401,
        )


class InvalidTokenError(AuthenticationError):
    """Raised when a token is invalid or expired."""

    def __init__(self, reason: str = "Token is invalid or expired") -> None:
        super().__init__(message=reason, details={"reason": reason})


class AuthorizationError(MothershipError):
    """Raised when user lacks required permissions."""

    def __init__(
        self,
        message: str = "Insufficient permissions",
        required_permission: str | None = None,
    ) -> None:
        details = {}
        if required_permission:
            details["required_permission"] = required_permission
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            details=details,
            status_code=403,
        )


# =============================================================================
# Resource Errors
# =============================================================================


class ResourceNotFoundError(MothershipError):
    """Raised when a requested resource does not exist."""

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
    ) -> None:
        super().__init__(
            message=f"{resource_type} not found: {resource_id}",
            code="RESOURCE_NOT_FOUND",
            details={"resource_type": resource_type, "resource_id": resource_id},
            status_code=404,
        )


class ResourceExistsError(MothershipError):
    """Raised when attempting to create a resource that already exists."""

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
    ) -> None:
        super().__init__(
            message=f"{resource_type} already exists: {resource_id}",
            code="RESOURCE_EXISTS",
            details={"resource_type": resource_type, "resource_id": resource_id},
            status_code=409,
        )


class ResourceLockedError(MothershipError):
    """Raised when a resource is locked by another operation."""

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        locked_by: str | None = None,
    ) -> None:
        details = {"resource_type": resource_type, "resource_id": resource_id}
        if locked_by:
            details["locked_by"] = locked_by
        super().__init__(
            message=f"{resource_type} is locked: {resource_id}",
            code="RESOURCE_LOCKED",
            details=details,
            status_code=423,
        )


# =============================================================================
# Validation Errors
# =============================================================================


class ValidationError(MothershipError):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str = "Validation failed",
        field: str | None = None,
        value: Any | None = None,
    ) -> None:
        details: dict[str, Any] = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)[:100]  # Truncate for safety
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details=details,
            status_code=422,
        )


class SchemaValidationError(ValidationError):
    """Raised when request body doesn't match expected schema."""

    def __init__(self, errors: list[dict[str, Any]]) -> None:
        super().__init__(
            message="Request body validation failed",
            field=None,
            value=None,
        )
        self.code = "SCHEMA_VALIDATION_ERROR"
        self.details = {"errors": errors}


# =============================================================================
# Integration Errors
# =============================================================================


class IntegrationError(MothershipError):
    """Base class for external integration errors."""

    def __init__(
        self,
        service: str,
        message: str = "Integration error",
        details: dict[str, Any] | None = None,
    ) -> None:
        integration_details = {"service": service}
        if details:
            integration_details.update(details)
        super().__init__(
            message=f"[{service}] {message}",
            code="INTEGRATION_ERROR",
            details=integration_details,
            status_code=502,
        )


class IntegrationConnectionError(IntegrationError):
    """Raised when unable to connect to an external service."""

    def __init__(self, service: str, reason: str | None = None) -> None:
        details = {}
        if reason:
            details["reason"] = reason
        super().__init__(
            service=service,
            message=f"Failed to connect to {service}",
            details=details,
        )


class IntegrationTimeoutError(IntegrationError):
    """Raised when an external service request times out."""

    def __init__(self, service: str, timeout_seconds: float) -> None:
        super().__init__(
            service=service,
            message=f"Request timed out after {timeout_seconds}s",
            details={"timeout_seconds": timeout_seconds},
        )
        self.status_code = 504


class IntegrationRateLimitError(IntegrationError):
    """Raised when rate limited by an external service."""

    def __init__(
        self,
        service: str,
        retry_after: int | None = None,
    ) -> None:
        details = {}
        if retry_after:
            details["retry_after_seconds"] = retry_after
        super().__init__(
            service=service,
            message="Rate limit exceeded",
            details=details,
        )
        self.status_code = 429


# =============================================================================
# Cockpit Operational Errors
# =============================================================================


class CockpitError(MothershipError):
    """Base class for cockpit-specific operational errors."""

    def __init__(
        self,
        message: str,
        code: str = "COCKPIT_ERROR",
        details: dict[str, Any] | None = None,
        status_code: int = 500,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            details=details,
            status_code=status_code,
        )


class SystemNotReadyError(CockpitError):
    """Raised when the system is not ready for an operation."""

    def __init__(
        self,
        component: str,
        reason: str | None = None,
    ) -> None:
        super().__init__(
            message=f"System component not ready: {component}",
            code="SYSTEM_NOT_READY",
            details={"component": component, "reason": reason},
            status_code=503,
        )


class OperationInProgressError(CockpitError):
    """Raised when an operation is already in progress."""

    def __init__(
        self,
        operation: str,
        operation_id: str | None = None,
    ) -> None:
        details: dict[str, Any] = {"operation": operation}
        if operation_id:
            details["operation_id"] = operation_id
        super().__init__(
            message=f"Operation already in progress: {operation}",
            code="OPERATION_IN_PROGRESS",
            details=details,
            status_code=409,
        )


class OperationFailedError(CockpitError):
    """Raised when an operation fails."""

    def __init__(
        self,
        operation: str,
        reason: str,
        recoverable: bool = True,
    ) -> None:
        super().__init__(
            message=f"Operation failed: {operation}",
            code="OPERATION_FAILED",
            details={
                "operation": operation,
                "reason": reason,
                "recoverable": recoverable,
            },
            status_code=500,
        )


class StateTransitionError(CockpitError):
    """Raised when an invalid state transition is attempted."""

    def __init__(
        self,
        current_state: str,
        target_state: str,
        allowed_transitions: list[str] | None = None,
    ) -> None:
        details: dict[str, Any] = {
            "current_state": current_state,
            "target_state": target_state,
        }
        if allowed_transitions:
            details["allowed_transitions"] = allowed_transitions
        super().__init__(
            message=f"Invalid state transition from {current_state} to {target_state}",
            code="STATE_TRANSITION_ERROR",
            details=details,
            status_code=409,
        )


# =============================================================================
# Telemetry Errors
# =============================================================================


class TelemetryError(MothershipError):
    """Base class for telemetry-related errors."""

    def __init__(
        self,
        message: str = "Telemetry error",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="TELEMETRY_ERROR",
            details=details,
            status_code=500,
        )


class MetricCollectionError(TelemetryError):
    """Raised when metric collection fails."""

    def __init__(self, metric_name: str, reason: str) -> None:
        super().__init__(
            message=f"Failed to collect metric: {metric_name}",
            details={"metric_name": metric_name, "reason": reason},
        )


class AlertThresholdError(TelemetryError):
    """Raised when an alert threshold is violated."""

    def __init__(
        self,
        metric_name: str,
        current_value: float,
        threshold: float,
        severity: str = "warning",
    ) -> None:
        super().__init__(
            message=f"Alert threshold exceeded for {metric_name}",
            details={
                "metric_name": metric_name,
                "current_value": current_value,
                "threshold": threshold,
                "severity": severity,
            },
        )


# =============================================================================
# WebSocket Errors
# =============================================================================


class WebSocketError(MothershipError):
    """Base class for WebSocket-related errors."""

    def __init__(
        self,
        message: str = "WebSocket error",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="WEBSOCKET_ERROR",
            details=details,
            status_code=500,
        )


class WebSocketConnectionError(WebSocketError):
    """Raised when WebSocket connection fails."""

    def __init__(self, reason: str) -> None:
        super().__init__(
            message=f"WebSocket connection failed: {reason}",
            details={"reason": reason},
        )


class WebSocketMessageError(WebSocketError):
    """Raised when WebSocket message handling fails."""

    def __init__(self, message_type: str, reason: str) -> None:
        super().__init__(
            message="Failed to process WebSocket message",
            details={"message_type": message_type, "reason": reason},
        )


__all__ = [
    # Base
    "MothershipError",
    # Configuration
    "ConfigurationError",
    "EnvironmentError",
    # Authentication & Authorization
    "AuthenticationError",
    "InvalidTokenError",
    "AuthorizationError",
    # Resources
    "ResourceNotFoundError",
    "ResourceExistsError",
    "ResourceLockedError",
    # Validation
    "ValidationError",
    "SchemaValidationError",
    # Integration
    "IntegrationError",
    "IntegrationConnectionError",
    "IntegrationTimeoutError",
    "IntegrationRateLimitError",
    # Cockpit
    "CockpitError",
    "SystemNotReadyError",
    "OperationInProgressError",
    "OperationFailedError",
    "StateTransitionError",
    # Telemetry
    "TelemetryError",
    "MetricCollectionError",
    "AlertThresholdError",
    # WebSocket
    "WebSocketError",
    "WebSocketConnectionError",
    "WebSocketMessageError",
]
