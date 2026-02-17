"""
Resource Management Utilities for Chaos Resilience.

Provides semaphores, resource pools, and guards to prevent resource exhaustion
during chaos testing scenarios like high load or parasitic attacks.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Callable

logger = logging.getLogger(__name__)


class ResourcePool:
    """
    Resource pool with configurable limits and graceful degradation.

    Manages concurrent access to resources like database connections,
    external API calls, or CPU-intensive operations.
    """

    def __init__(
        self,
        max_concurrent: int = 100,  # Increased from 10 for high traffic
        name: str = "resource_pool",
        timeout_seconds: float = 30.0,
        queue_size: int = 200,  # Add queue for burst handling
    ):
        self.max_concurrent = max_concurrent
        self.name = name
        self.timeout_seconds = timeout_seconds
        self.queue_size = queue_size
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._active_count = 0
        self._total_requests = 0
        self._rejected_requests = 0
        self._queued_requests = 0

    async def acquire(self) -> ResourceGuard:
        """Acquire a resource guard."""
        try:
            await asyncio.wait_for(self._semaphore.acquire(), timeout=self.timeout_seconds)
            self._active_count += 1
            self._total_requests += 1
            return ResourceGuard(self)
        except asyncio.TimeoutError:
            self._rejected_requests += 1
            logger.warning(
                f"Resource pool {self.name} timeout: active={self._active_count}, "
                f"rejected={self._rejected_requests}"
            )
            raise

    def release(self) -> None:
        """Release a resource."""
        self._active_count -= 1
        self._semaphore.release()

    @property
    def active_count(self) -> int:
        """Get current active resource count."""
        return self._active_count

    @property
    def available_count(self) -> int:
        """Get available resource slots."""
        return self.max_concurrent - self._active_count

    @property
    def utilization_percent(self) -> float:
        """Get resource utilization percentage."""
        if self.max_concurrent == 0:
            return 0.0
        return (self._active_count / self.max_concurrent) * 100.0


class ResourceGuard:
    """Context manager for resource acquisition and release."""

    def __init__(self, pool: ResourcePool):
        self.pool = pool

    async def __aenter__(self) -> None:
        return None

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.pool.release()


# Global resource pools for different resource types
_resource_pools: dict[str, ResourcePool] = {}


def get_resource_pool(name: str, max_concurrent: int = 10) -> ResourcePool:
    """
    Get or create a resource pool.

    Args:
        name: Pool identifier
        max_concurrent: Maximum concurrent operations

    Returns:
        ResourcePool instance
    """
    if name not in _resource_pools:
        _resource_pools[name] = ResourcePool(max_concurrent=max_concurrent, name=name)
    return _resource_pools[name]


@asynccontextmanager
async def resource_guard(
    pool_name: str,
    max_concurrent: int = 10,
    timeout_seconds: float = 30.0,
) -> AsyncIterator[None]:
    """
    Context manager for resource protection.

    Usage:
        async with resource_guard("api_calls", max_concurrent=5):
            await make_api_call()

    Args:
        pool_name: Name of the resource pool
        max_concurrent: Maximum concurrent operations
        timeout_seconds: Timeout for acquiring resources
    """
    pool = get_resource_pool(pool_name, max_concurrent)
    pool.timeout_seconds = timeout_seconds

    guard = await pool.acquire()
    try:
        async with guard:
            yield
    finally:
        pass


class CircuitBreaker:
    """
    Simple circuit breaker for external service calls.

    Prevents cascading failures by temporarily stopping calls to failing services.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout_seconds: float = 30.0,
        success_threshold: int = 3,
        name: str = "circuit_breaker",
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.success_threshold = success_threshold
        self.name = name

        self._state = "closed"  # closed, open, half_open
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0.0

    @property
    def state(self) -> str:
        """Get current circuit breaker state."""
        return self._state

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        return (
            self._state == "open"
            and time.time() - self._last_failure_time >= self.recovery_timeout_seconds
        )

    def _record_success(self) -> None:
        """Record a successful operation."""
        self._success_count += 1
        if self._state == "half_open" and self._success_count >= self.success_threshold:
            self._state = "closed"
            self._failure_count = 0
            self._success_count = 0
            logger.info(f"Circuit breaker {self.name} closed (recovered)")

    def _record_failure(self) -> None:
        """Record a failed operation."""
        self._failure_count += 1
        self._last_failure_time = time.time()
        self._success_count = 0

        if self._failure_count >= self.failure_threshold:
            if self._state == "closed":
                self._state = "open"
                logger.warning(f"Circuit breaker {self.name} opened (failure threshold exceeded)")
            elif self._state == "half_open":
                self._state = "open"
                logger.warning(f"Circuit breaker {self.name} re-opened (half-open failure)")

    async def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Async function to call
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenError: If circuit is open
        """
        if self._state == "open":
            if self._should_attempt_reset():
                self._state = "half_open"
                logger.info(f"Circuit breaker {self.name} attempting recovery")
            else:
                raise CircuitBreakerOpenError(f"Circuit breaker {self.name} is open")

        try:
            result = await func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


# Global circuit breakers
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str, **kwargs: Any) -> CircuitBreaker:
    """
    Get or create a circuit breaker.

    Args:
        name: Circuit breaker identifier
        **kwargs: Circuit breaker configuration

    Returns:
        CircuitBreaker instance
    """
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name=name, **kwargs)
    return _circuit_breakers[name]


# Import time at the end to avoid circular imports
import time
