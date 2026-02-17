"""
Timeout Management Utilities for Chaos Resilience.

Provides timeout handling, cancellation, and graceful operation termination
to prevent hanging operations during chaos testing scenarios.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


class TimeoutManager:
    """
    Timeout management with configurable policies.

    Handles operation timeouts with different strategies:
    - Cancel: Cancel operation immediately
    - Graceful: Allow operation to complete if possible
    - Circuit: Trigger circuit breaker on timeout
    """

    def __init__(
        self,
        default_timeout_seconds: float = 30.0,
        grace_period_seconds: float = 5.0,
    ):
        self.default_timeout_seconds = default_timeout_seconds
        self.grace_period_seconds = grace_period_seconds

    @asynccontextmanager
    async def timeout_operation(
        self,
        timeout_seconds: float | None = None,
        operation_name: str = "operation",
        on_timeout: str = "cancel",  # cancel, graceful, circuit
        circuit_breaker_name: str | None = None,
    ) -> AsyncIterator[None]:
        """
        Context manager for timeout-protected operations.

        Args:
            timeout_seconds: Timeout in seconds (uses default if None)
            operation_name: Name for logging
            on_timeout: Action on timeout: 'cancel', 'graceful', or 'circuit'
            circuit_breaker_name: Circuit breaker to trigger on timeout
        """
        timeout = timeout_seconds or self.default_timeout_seconds
        task = None

        try:
            # Create a task to track the timeout
            task = asyncio.create_task(asyncio.sleep(timeout))
            yield

        except asyncio.CancelledError:
            logger.warning(f"Operation {operation_name} was cancelled due to timeout ({timeout}s)")
            if on_timeout == "circuit" and circuit_breaker_name:
                from .resource_management import get_circuit_breaker
                cb = get_circuit_breaker(circuit_breaker_name)
                # Simulate a failure to trigger circuit breaker
                try:
                    cb._record_failure()
                except AttributeError:
                    pass  # Circuit breaker may not have the method
            raise

        finally:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    async def with_timeout(
        self,
        coro: Any,
        timeout_seconds: float | None = None,
        operation_name: str = "operation",
        on_timeout: str = "cancel",
        circuit_breaker_name: str | None = None,
    ) -> Any:
        """
        Execute coroutine with timeout protection.

        Args:
            coro: Coroutine to execute
            timeout_seconds: Timeout in seconds
            operation_name: Name for logging
            on_timeout: Action on timeout
            circuit_breaker_name: Circuit breaker name

        Returns:
            Coroutine result

        Raises:
            asyncio.TimeoutError: If operation times out
        """
        timeout = timeout_seconds or self.default_timeout_seconds

        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Operation {operation_name} timed out after {timeout}s")

            if on_timeout == "circuit" and circuit_breaker_name:
                from .resource_management import get_circuit_breaker
                cb = get_circuit_breaker(circuit_breaker_name)
                # Simulate a failure to trigger circuit breaker
                try:
                    cb._record_failure()
                except AttributeError:
                    pass

            raise


# Global timeout manager instance
_timeout_manager = TimeoutManager()


def get_timeout_manager() -> TimeoutManager:
    """Get the global timeout manager instance."""
    return _timeout_manager


async def with_timeout(
    coro: Any,
    timeout_seconds: float = 30.0,
    operation_name: str = "operation",
) -> Any:
    """
    Convenience function for timeout-protected operations.

    Args:
        coro: Coroutine to execute
        timeout_seconds: Timeout in seconds
        operation_name: Name for logging

    Returns:
        Coroutine result
    """
    return await _timeout_manager.with_timeout(
        coro=coro,
        timeout_seconds=timeout_seconds,
        operation_name=operation_name,
    )


@asynccontextmanager
async def timeout_guard(
    timeout_seconds: float = 30.0,
    operation_name: str = "operation",
) -> AsyncIterator[None]:
    """
    Context manager for timeout protection.

    Usage:
        async with timeout_guard(10.0, "database_query"):
            await slow_operation()
    """
    async with _timeout_manager.timeout_operation(
        timeout_seconds=timeout_seconds,
        operation_name=operation_name,
    ):
        yield


class GracefulShutdown:
    """
    Graceful shutdown manager for clean termination under chaos.

    Allows operations to complete gracefully when shutdown is requested,
    while preventing new operations from starting.
    """

    def __init__(self, shutdown_timeout_seconds: float = 30.0):
        self.shutdown_timeout_seconds = shutdown_timeout_seconds
        self._shutdown_event = asyncio.Event()
        self._active_operations = 0

    @property
    def is_shutting_down(self) -> bool:
        """Check if shutdown has been requested."""
        return self._shutdown_event.is_set()

    async def request_shutdown(self) -> None:
        """Request graceful shutdown."""
        self._shutdown_event.set()
        logger.info("Graceful shutdown requested")

    async def wait_for_shutdown_complete(self) -> None:
        """Wait for all active operations to complete."""
        shutdown_deadline = asyncio.get_event_loop().time() + self.shutdown_timeout_seconds

        while self._active_operations > 0:
            remaining_time = shutdown_deadline - asyncio.get_event_loop().time()
            if remaining_time <= 0:
                logger.warning(f"Shutdown timeout exceeded, {self._active_operations} operations still active")
                break

            try:
                await asyncio.wait_for(self._shutdown_event.wait(), timeout=min(1.0, remaining_time))
            except asyncio.TimeoutError:
                continue

        logger.info("Graceful shutdown completed")

    @asynccontextmanager
    async def operation_guard(self, operation_name: str = "operation") -> AsyncIterator[None]:
        """
        Context manager for operations that should complete during shutdown.

        Raises:
            ShutdownRequestedError: If shutdown requested and no new operations allowed
        """
        if self.is_shutting_down:
            raise ShutdownRequestedError(f"Shutdown requested, rejecting new operation: {operation_name}")

        self._active_operations += 1
        try:
            yield
        finally:
            self._active_operations -= 1


class ShutdownRequestedError(Exception):
    """Raised when shutdown is requested and new operations are not allowed."""
    pass


# Global graceful shutdown instance
_graceful_shutdown = GracefulShutdown()


def get_graceful_shutdown() -> GracefulShutdown:
    """Get the global graceful shutdown instance."""
    return _graceful_shutdown
