"""
Shared exception hierarchy for GRID Application Layer.

Goal:
- Provide a stable, application-level exception hierarchy that *always* has the same types.
- When the Mothership layer is available, wrap its exceptions so callers can:
  - catch application-layer types consistently
  - still inspect original/root causes when needed

This design avoids type issues caused by re-exporting foreign exception classes directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# ──────────────────────────────────────────────────────────────────────────────
# Base application exception
# ──────────────────────────────────────────────────────────────────────────────


@dataclass
class ErrorDetails:
    """Structured details for API-friendly error reporting."""

    code: str = "APPLICATION_ERROR"
    message: str = "An unexpected error occurred"
    details: dict[str, Any] | None = None
    status_code: int = 500

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details or {},
            }
        }


class ApplicationError(Exception):
    """Base exception for all GRID application-layer errors.

    Attributes:
        code: Stable machine-readable code.
        message: Human-readable message.
        details: Structured details dict (safe to serialize).
        status_code: Suggested HTTP status code.
        cause: Optional original exception (e.g., from Mothership layer).
    """

    def __init__(
        self,
        message: str = "An unexpected error occurred",
        *,
        code: str = "APPLICATION_ERROR",
        details: dict[str, Any] | None = None,
        status_code: int = 500,
        cause: BaseException | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        self.cause = cause
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        return ErrorDetails(
            code=self.code,
            message=self.message,
            details=self.details,
            status_code=self.status_code,
        ).to_dict()


# Alias retained for compatibility with earlier naming
MothershipError = ApplicationError  # Back-compat name used across codebase


# ──────────────────────────────────────────────────────────────────────────────
# Specific application-layer exception types
# ──────────────────────────────────────────────────────────────────────────────


class ValidationError(ApplicationError):
    pass


class SchemaValidationError(ValidationError):
    pass


class ConfigurationError(ApplicationError):
    pass


class EnvironmentError(ApplicationError):
    pass


class AuthenticationError(ApplicationError):
    pass


class AuthorizationError(ApplicationError):
    pass


class InvalidTokenError(AuthenticationError):
    pass


class ResourceNotFoundError(ApplicationError):
    pass


class ResourceExistsError(ApplicationError):
    pass


class ResourceLockedError(ApplicationError):
    pass


class IntegrationError(ApplicationError):
    pass


class IntegrationConnectionError(IntegrationError):
    pass


class IntegrationTimeoutError(IntegrationError):
    pass


class IntegrationRateLimitError(IntegrationError):
    pass


class CockpitError(ApplicationError):
    pass


class SystemNotReadyError(CockpitError):
    pass


class OperationInProgressError(CockpitError):
    pass


class OperationFailedError(CockpitError):
    pass


class StateTransitionError(CockpitError):
    pass


class TelemetryError(ApplicationError):
    pass


class MetricCollectionError(TelemetryError):
    pass


class WebSocketError(ApplicationError):
    pass


class WebSocketConnectionError(WebSocketError):
    pass


class WebSocketMessageError(WebSocketError):
    pass


# ──────────────────────────────────────────────────────────────────────────────
# Wrapping helpers for Mothership exceptions (optional dependency)
# ──────────────────────────────────────────────────────────────────────────────


def _safe_getattr(obj: Any, name: str, default: Any) -> Any:
    try:
        return getattr(obj, name, default)
    except Exception:
        return default


def wrap_mothership_exception(err: BaseException) -> ApplicationError:
    """Wrap a Mothership exception into the appropriate ApplicationError subtype.

    This keeps the *application-layer* types stable while preserving:
    - status_code (if present)
    - code (if present)
    - details (if present)
    - the original exception as `cause`
    """
    # Defaults if the foreign exception doesn't carry these fields
    status_code = int(_safe_getattr(err, "status_code", 500))
    code = str(_safe_getattr(err, "code", "APPLICATION_ERROR"))
    details = _safe_getattr(err, "details", None)
    if details is not None and not isinstance(details, dict):
        details = {"details": details}

    message = str(err) if str(err) else _safe_getattr(err, "message", "An unexpected error occurred")
    message = str(message) if message is not None else "An unexpected error occurred"

    # Map by foreign class name (robust, avoids importing types that may not exist)
    name = err.__class__.__name__

    mapping: dict[str, type[ApplicationError]] = {
        # Validation / schema
        "ValidationError": ValidationError,
        "SchemaValidationError": SchemaValidationError,
        # Config / env
        "ConfigurationError": ConfigurationError,
        "EnvironmentError": EnvironmentError,
        # Auth
        "AuthenticationError": AuthenticationError,
        "AuthorizationError": AuthorizationError,
        "InvalidTokenError": InvalidTokenError,
        # Resources
        "ResourceNotFoundError": ResourceNotFoundError,
        "ResourceExistsError": ResourceExistsError,
        "ResourceLockedError": ResourceLockedError,
        # Integration
        "IntegrationError": IntegrationError,
        "IntegrationConnectionError": IntegrationConnectionError,
        "IntegrationTimeoutError": IntegrationTimeoutError,
        "IntegrationRateLimitError": IntegrationRateLimitError,
        # Cockpit/system
        "CockpitError": CockpitError,
        "SystemNotReadyError": SystemNotReadyError,
        "OperationInProgressError": OperationInProgressError,
        "OperationFailedError": OperationFailedError,
        "StateTransitionError": StateTransitionError,
        # Telemetry
        "TelemetryError": TelemetryError,
        "MetricCollectionError": MetricCollectionError,
        # WebSocket
        "WebSocketError": WebSocketError,
        "WebSocketConnectionError": WebSocketConnectionError,
        "WebSocketMessageError": WebSocketMessageError,
        # Base
        "MothershipError": MothershipError,
    }

    exc_type = mapping.get(name, ApplicationError)
    return exc_type(
        message=message,
        code=code,
        details=details,
        status_code=status_code,
        cause=err,
    )


__all__ = [
    # Base
    "ApplicationError",
    "MothershipError",
    "ErrorDetails",
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
    # WebSocket
    "WebSocketError",
    "WebSocketConnectionError",
    "WebSocketMessageError",
    # Helpers
    "wrap_mothership_exception",
]
