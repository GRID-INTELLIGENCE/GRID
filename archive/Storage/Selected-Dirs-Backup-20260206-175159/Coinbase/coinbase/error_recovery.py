"""Error recovery system with classification, retry logic, and circuit breaker."""

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Any, TypeVar


class ErrorCategory(Enum):
    """Categories of errors for recovery strategies."""

    TRANSIENT = "transient"
    PERMISSION = "permission"
    DEPENDENCY = "dependency"
    VALIDATION = "validation"
    CIRCUIT_OPEN = "circuit_open"
    UNKNOWN = "unknown"


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = auto()  # Normal operation
    OPEN = auto()  # Failing, reject requests
    HALF_OPEN = auto()  # Testing if service recovered


@dataclass
class ErrorContext:
    """Context about an error for recovery."""

    category: ErrorCategory
    recoverable: bool
    strategy: str
    message: str
    circuit_state: CircuitState | None = None


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5
    recovery_timeout: int = 60
    half_open_max_calls: int = 3
    success_threshold: int = 2


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.

    Prevents cascading failures by stopping requests to failing services.
    """

    def __init__(self, name: str, config: CircuitBreakerConfig | None = None):
        """
        Initialize circuit breaker.

        Args:
            name: Circuit breaker name
            config: Optional configuration
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: datetime | None = None
        self.half_open_calls = 0
        self._lock = threading.Lock()

    def can_execute(self) -> bool:
        """
        Check if execution is allowed.

        Returns:
            True if execution should proceed
        """
        with self._lock:
            if self.state == CircuitState.CLOSED:
                return True

            if self.state == CircuitState.OPEN:
                # Check if recovery timeout has passed
                if self.last_failure_time:
                    elapsed = (datetime.now() - self.last_failure_time).seconds
                    if elapsed >= self.config.recovery_timeout:
                        self.state = CircuitState.HALF_OPEN
                        self.half_open_calls = 0
                        return True
                return False

            if self.state == CircuitState.HALF_OPEN:
                if self.half_open_calls < self.config.half_open_max_calls:
                    self.half_open_calls += 1
                    return True
                return False

            return True

    def record_success(self) -> None:
        """Record successful execution."""
        with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self._close_circuit()
            else:
                self.failure_count = 0

    def record_failure(self) -> None:
        """Record failed execution."""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()

            if self.state == CircuitState.HALF_OPEN:
                self._open_circuit()
            elif self.failure_count >= self.config.failure_threshold:
                self._open_circuit()

    def _open_circuit(self) -> None:
        """Open the circuit (stop allowing requests)."""
        self.state = CircuitState.OPEN
        self.success_count = 0
        print(f"[CircuitBreaker] {self.name}: Circuit OPENED")

    def _close_circuit(self) -> None:
        """Close the circuit (resume normal operation)."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        print(f"[CircuitBreaker] {self.name}: Circuit CLOSED")

    def get_state(self) -> CircuitState:
        """Get current circuit state."""
        with self._lock:
            return self.state

    def get_stats(self) -> dict[str, Any]:
        """Get circuit breaker statistics."""
        with self._lock:
            return {
                "name": self.name,
                "state": self.state.name,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "failure_threshold": self.config.failure_threshold,
                "last_failure": (
                    self.last_failure_time.isoformat() if self.last_failure_time else None
                ),
            }


# Global circuit breakers registry
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str, config: CircuitBreakerConfig | None = None) -> CircuitBreaker:
    """
    Get or create circuit breaker.

    Args:
        name: Circuit breaker name
        config: Optional configuration

    Returns:
        CircuitBreaker instance
    """
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name, config)
    return _circuit_breakers[name]


class ErrorClassifier:
    """Classifies errors and determines recovery strategies."""

    @staticmethod
    def classify(error: Exception, circuit_state: CircuitState | None = None) -> ErrorContext:
        """Classify an exception and determine recovery strategy."""
        error_msg = str(error).lower()

        # Check if circuit is open
        if circuit_state == CircuitState.OPEN:
            return ErrorContext(
                category=ErrorCategory.CIRCUIT_OPEN,
                recoverable=False,
                strategy="circuit_open",
                message="Circuit breaker is open - service unavailable",
                circuit_state=circuit_state,
            )

        # Transient errors (timeouts, rate limits, network issues)
        transient_patterns = [
            "timeout",
            "timed out",
            "rate limit",
            "too many requests",
            "connection",
            "network",
            "temporary",
            "unavailable",
        ]
        if any(x in error_msg for x in transient_patterns):
            return ErrorContext(
                category=ErrorCategory.TRANSIENT,
                recoverable=True,
                strategy="retry_with_backoff",
                message=str(error),
                circuit_state=circuit_state,
            )

        # Permission errors (not recoverable)
        permission_patterns = ["permission", "unauthorized", "forbidden", "access denied"]
        if any(x in error_msg for x in permission_patterns):
            return ErrorContext(
                category=ErrorCategory.PERMISSION,
                recoverable=False,
                strategy="abort",
                message=str(error),
                circuit_state=circuit_state,
            )

        # Dependency errors (circuit breaker)
        dependency_patterns = ["dependency", "service unavailable", "downstream", "circuit"]
        if any(x in error_msg for x in dependency_patterns):
            return ErrorContext(
                category=ErrorCategory.DEPENDENCY,
                recoverable=True,
                strategy="circuit_break",
                message=str(error),
                circuit_state=circuit_state,
            )

        # Validation errors (not recoverable)
        validation_patterns = ["validation", "invalid", "malformed", "bad request"]
        if any(x in error_msg for x in validation_patterns):
            return ErrorContext(
                category=ErrorCategory.VALIDATION,
                recoverable=False,
                strategy="abort",
                message=str(error),
                circuit_state=circuit_state,
            )

        # Unknown errors - try retry once
        return ErrorContext(
            category=ErrorCategory.UNKNOWN,
            recoverable=True,
            strategy="retry_with_backoff",
            message=str(error),
            circuit_state=circuit_state,
        )


T = TypeVar("T")


class RecoveryEngine:
    """Executes tasks with automatic error recovery and circuit breaker."""

    max_attempts: int
    base_delay: float
    max_delay: float
    fallback_fn: Callable[..., Any] | None
    circuit_breaker: CircuitBreaker | None

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        fallback_fn: Callable[..., Any] | None = None,
        circuit_breaker: CircuitBreaker | None = None,
    ) -> None:
        """
        Initialize recovery engine.

        Args:
            max_attempts: Maximum retry attempts
            base_delay: Initial delay between retries
            max_delay: Maximum delay between retries
            fallback_fn: Optional fallback function
            circuit_breaker: Optional circuit breaker
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.fallback_fn = fallback_fn
        self.circuit_breaker = circuit_breaker

    def execute_with_recovery(
        self,
        task_fn: Callable[..., T],
        *args: object,
        **kwargs: object,
    ) -> T:
        """
        Execute a task with automatic retry, circuit breaker, and fallback.

        Args:
            task_fn: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Task result

        Raises:
            Exception: If all recovery strategies fail
        """
        # Check circuit breaker
        if self.circuit_breaker and not self.circuit_breaker.can_execute():
            # Try fallback if circuit is open
            if self.fallback_fn:
                print("[Recovery] Circuit open, executing fallback")
                return self.fallback_fn(*args, **kwargs)  # type: ignore[no-any-return]

            error_context = ErrorClassifier.classify(
                Exception("Circuit breaker open"), CircuitState.OPEN
            )
            raise CircuitBreakerOpenError(error_context.message)

        last_error: Exception | None = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                result = task_fn(*args, **kwargs)

                # Record success in circuit breaker
                if self.circuit_breaker:
                    self.circuit_breaker.record_success()

                return result

            except Exception as e:
                last_error = e
                circuit_state = self.circuit_breaker.get_state() if self.circuit_breaker else None
                error_context = ErrorClassifier.classify(e, circuit_state)

                # Record failure in circuit breaker
                if self.circuit_breaker:
                    self.circuit_breaker.record_failure()

                # Handle non-recoverable errors
                if not error_context.recoverable:
                    # Try fallback if available
                    if self.fallback_fn:
                        print("[Recovery] Non-recoverable error, executing fallback")
                        return self.fallback_fn(*args, **kwargs)  # type: ignore[no-any-return]
                    raise

                # Max attempts reached
                if attempt >= self.max_attempts:
                    # Try fallback if available
                    if self.fallback_fn:
                        print("[Recovery] Max attempts reached, executing fallback")
                        return self.fallback_fn(*args, **kwargs)  # type: ignore[no-any-return]
                    raise

                # Calculate exponential backoff delay
                delay: float = min(
                    self.base_delay * (2 ** (attempt - 1)),
                    self.max_delay,
                )

                msg = (
                    f"[Recovery] Attempt {attempt}/{self.max_attempts} failed: "
                    f"{error_context.message}"
                )
                print(msg)
                print(f"[Recovery] Retrying in {delay:.1f}s...")

                time.sleep(delay)

        if last_error is not None:
            raise last_error
        raise RuntimeError("Max attempts exceeded with no error captured")

    def with_circuit_breaker(
        self, circuit_breaker_name: str, config: CircuitBreakerConfig | None = None
    ) -> "RecoveryEngine":
        """
        Create new engine with circuit breaker.

        Args:
            circuit_breaker_name: Name for circuit breaker
            config: Optional circuit breaker config

        Returns:
            New RecoveryEngine with circuit breaker
        """
        cb = get_circuit_breaker(circuit_breaker_name, config)
        return RecoveryEngine(
            max_attempts=self.max_attempts,
            base_delay=self.base_delay,
            max_delay=self.max_delay,
            fallback_fn=self.fallback_fn,
            circuit_breaker=cb,
        )

    def with_fallback(self, fallback_fn: Callable[..., Any]) -> "RecoveryEngine":
        """
        Create new engine with fallback function.

        Args:
            fallback_fn: Fallback function

        Returns:
            New RecoveryEngine with fallback
        """
        return RecoveryEngine(
            max_attempts=self.max_attempts,
            base_delay=self.base_delay,
            max_delay=self.max_delay,
            fallback_fn=fallback_fn,
            circuit_breaker=self.circuit_breaker,
        )


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""

    pass


# Convenience functions
def execute_with_retry[T](
    fn: Callable[..., T], *args: object, max_attempts: int = 3, **kwargs: object
) -> T:
    """Execute function with retry logic."""
    engine = RecoveryEngine(max_attempts=max_attempts)
    return engine.execute_with_recovery(fn, *args, **kwargs)


def execute_with_circuit_breaker[T](
    fn: Callable[..., T], circuit_name: str, *args: object, **kwargs: object
) -> T:
    """Execute function with circuit breaker."""
    cb = get_circuit_breaker(circuit_name)
    engine = RecoveryEngine(circuit_breaker=cb)
    return engine.execute_with_recovery(fn, *args, **kwargs)
