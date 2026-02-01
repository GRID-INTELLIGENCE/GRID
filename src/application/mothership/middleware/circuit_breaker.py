"""
Circuit Breaker Middleware for Cascading Failure Prevention.

Implements the circuit breaker pattern at the middleware level to protect
the API from cascading failures. When a service or endpoint experiences
repeated failures, the circuit "opens" to prevent further damage and
allows time for recovery.

Circuit States:
- CLOSED: Normal operation, requests flow through
- OPEN: Failures exceeded threshold, requests rejected immediately
- HALF_OPEN: Recovery period, limited requests allowed to test

Usage:
    from application.mothership.middleware.circuit_breaker import CircuitBreakerMiddleware

    app.add_middleware(
        CircuitBreakerMiddleware,
        failure_threshold=5,
        recovery_timeout=30,
    )
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Constants
# =============================================================================


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Rejecting requests
    HALF_OPEN = "half_open"  # Testing recovery


class FailureType(str, Enum):
    """Types of failures that can trigger the circuit breaker."""

    TIMEOUT = "timeout"
    SERVER_ERROR = "server_error"
    CONNECTION_ERROR = "connection_error"
    EXCEPTION = "exception"


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class CircuitConfig:
    """Configuration for a circuit breaker."""

    # Thresholds
    failure_threshold: int = 5  # Failures before opening
    success_threshold: int = 3  # Successes needed to close from half-open

    # Timeouts
    recovery_timeout_seconds: float = 30.0  # Time before attempting recovery
    request_timeout_seconds: float = 30.0  # Request timeout (triggers failure)

    # Half-open behavior
    half_open_max_requests: int = 3  # Max requests in half-open state

    # Failure tracking
    failure_window_seconds: float = 60.0  # Window for counting failures
    error_codes: set[int] = field(default_factory=lambda: {500, 502, 503, 504})

    # Exclusions
    excluded_paths: list[str] = field(
        default_factory=lambda: [
            "/health",
            "/health/live",
            "/health/ready",
            "/ping",
            "/metrics",
        ]
    )


@dataclass
class CircuitMetrics:
    """Metrics for a circuit breaker."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rejected_requests: int = 0  # Requests rejected while circuit is open
    state_transitions: int = 0
    last_failure_time: datetime | None = None
    last_success_time: datetime | None = None
    last_state_change: datetime | None = None
    time_in_open_state_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "rejected_requests": self.rejected_requests,
            "state_transitions": self.state_transitions,
            "success_rate": (
                round(self.successful_requests / self.total_requests, 4) if self.total_requests > 0 else 1.0
            ),
            "last_failure_time": (self.last_failure_time.isoformat() if self.last_failure_time else None),
            "last_success_time": (self.last_success_time.isoformat() if self.last_success_time else None),
            "time_in_open_state_seconds": round(self.time_in_open_state_seconds, 2),
        }


@dataclass
class FailureRecord:
    """Record of a failure event."""

    timestamp: float
    failure_type: FailureType
    status_code: int | None = None
    error_message: str | None = None


@dataclass
class Circuit:
    """A circuit breaker instance for a specific key (path/service)."""

    key: str
    config: CircuitConfig
    state: CircuitState = CircuitState.CLOSED
    failures: list[FailureRecord] = field(default_factory=list)
    half_open_successes: int = 0
    half_open_requests: int = 0
    opened_at: float | None = None
    metrics: CircuitMetrics = field(default_factory=CircuitMetrics)

    def _now(self) -> float:
        """Get current timestamp."""
        return time.time()

    def _prune_old_failures(self) -> None:
        """Remove failures outside the tracking window."""
        cutoff = self._now() - self.config.failure_window_seconds
        self.failures = [f for f in self.failures if f.timestamp >= cutoff]

    def should_allow_request(self) -> bool:
        """Determine if a request should be allowed through."""
        now = self._now()

        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has elapsed
            if self.opened_at and (now - self.opened_at) >= self.config.recovery_timeout_seconds:
                self._transition_to_half_open()
                return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            # Allow limited requests in half-open state
            return self.half_open_requests < self.config.half_open_max_requests

        return True

    def record_success(self) -> None:
        """Record a successful request."""
        self.metrics.total_requests += 1
        self.metrics.successful_requests += 1
        self.metrics.last_success_time = datetime.now(UTC)

        if self.state == CircuitState.HALF_OPEN:
            self.half_open_successes += 1
            if self.half_open_successes >= self.config.success_threshold:
                self._transition_to_closed()

    def record_failure(
        self,
        failure_type: FailureType,
        status_code: int | None = None,
        error_message: str | None = None,
    ) -> None:
        """Record a failed request."""
        now = self._now()

        self.metrics.total_requests += 1
        self.metrics.failed_requests += 1
        self.metrics.last_failure_time = datetime.now(UTC)

        failure = FailureRecord(
            timestamp=now,
            failure_type=failure_type,
            status_code=status_code,
            error_message=error_message,
        )
        self.failures.append(failure)
        self._prune_old_failures()

        if self.state == CircuitState.HALF_OPEN:
            # Any failure in half-open immediately opens the circuit
            self._transition_to_open()
        elif self.state == CircuitState.CLOSED:
            # Check if we've exceeded the failure threshold
            if len(self.failures) >= self.config.failure_threshold:
                self._transition_to_open()

    def record_rejection(self) -> None:
        """Record a rejected request (circuit open)."""
        self.metrics.total_requests += 1
        self.metrics.rejected_requests += 1

    def _transition_to_open(self) -> None:
        """Transition circuit to OPEN state."""
        if self.state != CircuitState.OPEN:
            logger.warning(f"Circuit breaker OPEN for '{self.key}' after {len(self.failures)} failures")
            self.state = CircuitState.OPEN
            self.opened_at = self._now()
            self.metrics.state_transitions += 1
            self.metrics.last_state_change = datetime.now(UTC)

    def _transition_to_half_open(self) -> None:
        """Transition circuit to HALF_OPEN state."""
        if self.state == CircuitState.OPEN:
            logger.info(f"Circuit breaker HALF_OPEN for '{self.key}' - testing recovery")
            self.state = CircuitState.HALF_OPEN
            self.half_open_successes = 0
            self.half_open_requests = 0
            self.metrics.state_transitions += 1
            self.metrics.last_state_change = datetime.now(UTC)

            # Track time spent in open state
            if self.opened_at:
                self.metrics.time_in_open_state_seconds += self._now() - self.opened_at

    def _transition_to_closed(self) -> None:
        """Transition circuit to CLOSED state."""
        if self.state != CircuitState.CLOSED:
            logger.info(f"Circuit breaker CLOSED for '{self.key}' - recovered")
            self.state = CircuitState.CLOSED
            self.failures.clear()
            self.half_open_successes = 0
            self.half_open_requests = 0
            self.opened_at = None
            self.metrics.state_transitions += 1
            self.metrics.last_state_change = datetime.now(UTC)

    def force_open(self) -> None:
        """Manually open the circuit."""
        self._transition_to_open()

    def force_close(self) -> None:
        """Manually close the circuit."""
        self._transition_to_closed()

    def reset(self) -> None:
        """Reset the circuit to initial state."""
        self.state = CircuitState.CLOSED
        self.failures.clear()
        self.half_open_successes = 0
        self.half_open_requests = 0
        self.opened_at = None
        logger.info(f"Circuit breaker RESET for '{self.key}'")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "key": self.key,
            "state": self.state.value,
            "failure_count": len(self.failures),
            "failure_threshold": self.config.failure_threshold,
            "recovery_timeout_seconds": self.config.recovery_timeout_seconds,
            "half_open_successes": self.half_open_successes,
            "half_open_requests": self.half_open_requests,
            "opened_at": (datetime.fromtimestamp(self.opened_at, tz=UTC).isoformat() if self.opened_at else None),
            "metrics": self.metrics.to_dict(),
        }


# =============================================================================
# Circuit Breaker Manager
# =============================================================================


class CircuitBreakerManager:
    """
    Manager for multiple circuit breakers.

    Provides centralized management of circuit breakers for different
    paths or services, with support for global and per-path configuration.
    """

    def __init__(
        self,
        default_config: CircuitConfig | None = None,
    ):
        self._circuits: dict[str, Circuit] = {}
        self._default_config = default_config or CircuitConfig()
        self._lock = asyncio.Lock()

    def get_circuit(
        self,
        key: str,
        config: CircuitConfig | None = None,
    ) -> Circuit:
        """Get or create a circuit breaker for a key."""
        if key not in self._circuits:
            self._circuits[key] = Circuit(
                key=key,
                config=config or self._default_config,
            )
        return self._circuits[key]

    def get_all_circuits(self) -> dict[str, Circuit]:
        """Get all circuits."""
        return self._circuits.copy()

    def reset_circuit(self, key: str) -> bool:
        """Reset a specific circuit."""
        if key in self._circuits:
            self._circuits[key].reset()
            return True
        return False

    def reset_all_circuits(self) -> int:
        """Reset all circuits. Returns count of circuits reset."""
        count = len(self._circuits)
        for circuit in self._circuits.values():
            circuit.reset()
        return count

    def force_open_circuit(self, key: str) -> bool:
        """Force a circuit open."""
        if key in self._circuits:
            self._circuits[key].force_open()
            return True
        return False

    def force_close_circuit(self, key: str) -> bool:
        """Force a circuit closed."""
        if key in self._circuits:
            self._circuits[key].force_close()
            return True
        return False

    def get_metrics(self) -> dict[str, Any]:
        """Get aggregated metrics for all circuits."""
        total_requests = 0
        total_failures = 0
        total_rejections = 0
        open_circuits = 0

        for circuit in self._circuits.values():
            total_requests += circuit.metrics.total_requests
            total_failures += circuit.metrics.failed_requests
            total_rejections += circuit.metrics.rejected_requests
            if circuit.state == CircuitState.OPEN:
                open_circuits += 1

        return {
            "total_circuits": len(self._circuits),
            "open_circuits": open_circuits,
            "total_requests": total_requests,
            "total_failures": total_failures,
            "total_rejections": total_rejections,
            "circuits": {k: v.to_dict() for k, v in self._circuits.items()},
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return self.get_metrics()


# Global manager instance
_circuit_manager: CircuitBreakerManager | None = None


def get_circuit_manager() -> CircuitBreakerManager:
    """Get or create the global circuit breaker manager."""
    global _circuit_manager
    if _circuit_manager is None:
        _circuit_manager = CircuitBreakerManager()
    return _circuit_manager


def reset_circuit_manager() -> None:
    """Reset the global circuit manager (for testing)."""
    global _circuit_manager
    _circuit_manager = None


# =============================================================================
# Middleware
# =============================================================================


class CircuitBreakerMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware implementing the circuit breaker pattern.

    Protects the API from cascading failures by:
    1. Tracking failures per path
    2. Opening circuits when failure threshold is exceeded
    3. Rejecting requests while circuit is open
    4. Testing recovery with half-open state
    5. Closing circuit when recovery is confirmed

    Usage:
        app.add_middleware(
            CircuitBreakerMiddleware,
            failure_threshold=5,
            recovery_timeout=30,
        )
    """

    def __init__(
        self,
        app: ASGIApp,
        failure_threshold: int = 5,
        success_threshold: int = 3,
        recovery_timeout: float = 30.0,
        request_timeout: float = 30.0,
        failure_window: float = 60.0,
        error_codes: set[int] | None = None,
        excluded_paths: list[str] | None = None,
        granularity: str = "path",  # "path", "method_path", or "global"
    ):
        """
        Initialize circuit breaker middleware.

        Args:
            app: ASGI application
            failure_threshold: Number of failures before opening circuit
            success_threshold: Successes needed to close from half-open
            recovery_timeout: Seconds before attempting recovery
            request_timeout: Request timeout in seconds
            failure_window: Window for counting failures
            error_codes: HTTP status codes that count as failures
            excluded_paths: Paths excluded from circuit breaker
            granularity: Circuit key granularity
        """
        super().__init__(app)

        self.config = CircuitConfig(
            failure_threshold=failure_threshold,
            success_threshold=success_threshold,
            recovery_timeout_seconds=recovery_timeout,
            request_timeout_seconds=request_timeout,
            failure_window_seconds=failure_window,
            error_codes=error_codes or {500, 502, 503, 504},
            excluded_paths=excluded_paths or ["/health", "/health/live", "/health/ready", "/ping", "/metrics"],
        )
        self.granularity = granularity
        self.manager = get_circuit_manager()

    def _get_circuit_key(self, request: Request) -> str:
        """Generate circuit key based on granularity."""
        path = request.url.path

        if self.granularity == "global":
            return "global"
        elif self.granularity == "method_path":
            return f"{request.method}:{path}"
        else:  # path
            return path

    def _is_excluded(self, request: Request) -> bool:
        """Check if request path is excluded from circuit breaker."""
        path = request.url.path
        return any(
            path == excluded or path.startswith(excluded.rstrip("/") + "/") for excluded in self.config.excluded_paths
        )

    def _is_failure_response(self, response: Response) -> bool:
        """Check if response indicates a failure."""
        return response.status_code in self.config.error_codes

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Process request through circuit breaker."""

        # Skip excluded paths
        if self._is_excluded(request):
            return await call_next(request)

        circuit_key = self._get_circuit_key(request)
        circuit = self.manager.get_circuit(circuit_key, self.config)

        # Check if request should be allowed
        if not circuit.should_allow_request():
            circuit.record_rejection()
            logger.warning(
                f"Circuit breaker rejecting request to {request.url.path} "
                f"(circuit: {circuit_key}, state: {circuit.state.value})"
            )
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "success": False,
                    "error": {
                        "code": "CIRCUIT_OPEN",
                        "message": "Service temporarily unavailable due to high error rate",
                        "circuit": circuit_key,
                        "retry_after_seconds": int(
                            self.config.recovery_timeout_seconds - (time.time() - (circuit.opened_at or time.time()))
                        ),
                    },
                },
                headers={
                    "Retry-After": str(int(self.config.recovery_timeout_seconds)),
                    "X-Circuit-State": circuit.state.value,
                },
            )

        # Track half-open requests
        if circuit.state == CircuitState.HALF_OPEN:
            circuit.half_open_requests += 1

        # Process request
        try:
            response = await asyncio.wait_for(
                call_next(request),
                timeout=self.config.request_timeout_seconds,
            )

            # Check response status
            if self._is_failure_response(response):
                circuit.record_failure(
                    failure_type=FailureType.SERVER_ERROR,
                    status_code=response.status_code,
                )
            else:
                circuit.record_success()

            # Add circuit state header
            response.headers["X-Circuit-State"] = circuit.state.value

            return response

        except TimeoutError:
            circuit.record_failure(
                failure_type=FailureType.TIMEOUT,
                error_message=f"Request timed out after {self.config.request_timeout_seconds}s",
            )
            logger.error(f"Request timeout for {request.url.path} (circuit: {circuit_key})")
            return JSONResponse(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                content={
                    "success": False,
                    "error": {
                        "code": "REQUEST_TIMEOUT",
                        "message": "Request timed out",
                        "timeout_seconds": self.config.request_timeout_seconds,
                    },
                },
                headers={"X-Circuit-State": circuit.state.value},
            )

        except Exception as e:
            circuit.record_failure(
                failure_type=FailureType.EXCEPTION,
                error_message=str(e),
            )
            logger.exception(f"Exception processing request {request.url.path}: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "success": False,
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "Internal server error",
                    },
                },
                headers={"X-Circuit-State": circuit.state.value},
            )


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Enums
    "CircuitState",
    "FailureType",
    # Data classes
    "CircuitConfig",
    "CircuitMetrics",
    "FailureRecord",
    "Circuit",
    # Manager
    "CircuitBreakerManager",
    "get_circuit_manager",
    "reset_circuit_manager",
    # Middleware
    "CircuitBreakerMiddleware",
]
