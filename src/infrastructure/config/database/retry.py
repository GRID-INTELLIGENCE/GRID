"""
Connection Retry with Exponential Backoff.

Provides robust retry logic for database connections:
- Configurable retry count
- Exponential backoff
- Jitter to prevent thundering herd
- Async support

Extracted from Mothership's Databricks connector retry pattern.
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RetryConfig:
    """
    Immutable retry configuration.

    Attributes:
        max_retries: Maximum number of retry attempts
        base_delay_seconds: Initial delay before first retry
        max_delay_seconds: Maximum delay cap
        exponential_base: Multiplier for exponential backoff
        jitter: If True, add random jitter to delays
        jitter_factor: Jitter range (0.0-1.0)
    """

    max_retries: int = 3
    base_delay_seconds: float = 2.0
    max_delay_seconds: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    jitter_factor: float = 0.1


@dataclass(frozen=True, slots=True)
class RetryResult:
    """Result of a retry operation."""

    success: bool
    attempts: int
    total_delay_seconds: float
    last_error: Exception | None = None


class ConnectionRetry:
    """
    Retry handler with exponential backoff.

    Usage:
        retry = ConnectionRetry(config=RetryConfig(max_retries=5))

        # Sync
        result = retry.execute(lambda: connect_to_db())

        # Async
        result = await retry.execute_async(lambda: connect_to_db_async())

        # With custom on_retry callback
        retry = ConnectionRetry(
            on_retry=lambda attempt, delay, error: logger.warning(f"Retry {attempt}...")
        )
    """

    def __init__(
        self,
        config: RetryConfig | None = None,
        *,
        on_retry: Callable[[int, float, Exception], None] | None = None,
    ):
        """
        Initialize retry handler.

        Args:
            config: Retry configuration
            on_retry: Callback(attempt, delay, error) on each retry
        """
        self._config = config or RetryConfig()
        self._on_retry = on_retry

    @property
    def config(self) -> RetryConfig:
        """Get retry configuration."""
        return self._config

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for given attempt number.

        Uses exponential backoff with optional jitter.

        Args:
            attempt: Attempt number (1-indexed)

        Returns:
            Delay in seconds
        """
        # Exponential backoff
        delay = self._config.base_delay_seconds * (self._config.exponential_base ** (attempt - 1))

        # Cap at max delay
        delay = min(delay, self._config.max_delay_seconds)

        # Add jitter
        if self._config.jitter:
            jitter_range = delay * self._config.jitter_factor
            jitter = random.uniform(-jitter_range, jitter_range)  # noqa: S311
            delay = max(0, delay + jitter)

        return delay

    def execute(
        self,
        operation: Callable[[], Any],
        *,
        retry_on: tuple[type[Exception], ...] | None = None,
    ) -> RetryResult:
        """
        Execute operation with retry logic (synchronous).

        Args:
            operation: Function to execute
            retry_on: Tuple of exception types to retry on (default: all)

        Returns:
            RetryResult with success status and metadata
        """
        retry_exceptions = retry_on or (Exception,)
        total_delay = 0.0
        last_error: Exception | None = None

        for attempt in range(1, self._config.max_retries + 1):
            try:
                operation()
                return RetryResult(
                    success=True,
                    attempts=attempt,
                    total_delay_seconds=total_delay,
                )

            except retry_exceptions as e:
                last_error = e

                if attempt < self._config.max_retries:
                    delay = self.calculate_delay(attempt)
                    total_delay += delay

                    logger.warning(
                        f"Operation failed (attempt {attempt}/{self._config.max_retries}): {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )

                    # Call retry callback
                    if self._on_retry:
                        self._on_retry(attempt, delay, e)

                    time.sleep(delay)

        # All retries exhausted
        logger.error(f"All {self._config.max_retries} attempts failed")
        return RetryResult(
            success=False,
            attempts=self._config.max_retries,
            total_delay_seconds=total_delay,
            last_error=last_error,
        )

    async def execute_async(
        self,
        operation: Callable[[], Any],
        *,
        retry_on: tuple[type[Exception], ...] | None = None,
    ) -> RetryResult:
        """
        Execute operation with retry logic (asynchronous).

        Args:
            operation: Async function to execute
            retry_on: Tuple of exception types to retry on (default: all)

        Returns:
            RetryResult with success status and metadata
        """
        retry_exceptions = retry_on or (Exception,)
        total_delay = 0.0
        last_error: Exception | None = None

        for attempt in range(1, self._config.max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(operation):
                    await operation()
                else:
                    await asyncio.to_thread(operation)

                return RetryResult(
                    success=True,
                    attempts=attempt,
                    total_delay_seconds=total_delay,
                )

            except retry_exceptions as e:
                last_error = e

                if attempt < self._config.max_retries:
                    delay = self.calculate_delay(attempt)
                    total_delay += delay

                    logger.warning(
                        f"Async operation failed (attempt {attempt}/{self._config.max_retries}): {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )

                    # Call retry callback
                    if self._on_retry:
                        self._on_retry(attempt, delay, e)

                    await asyncio.sleep(delay)

        # All retries exhausted
        logger.error(f"All {self._config.max_retries} async attempts failed")
        return RetryResult(
            success=False,
            attempts=self._config.max_retries,
            total_delay_seconds=total_delay,
            last_error=last_error,
        )


def with_retry(
    max_retries: int = 3,
    base_delay: float = 2.0,
    retry_on: tuple[type[Exception], ...] | None = None,
) -> Callable[[Callable], Callable]:
    """
    Decorator to add retry logic to any function.

    Usage:
        @with_retry(max_retries=5, retry_on=(ConnectionError,))
        def connect_to_database():
            ...
    """
    config = RetryConfig(max_retries=max_retries, base_delay_seconds=base_delay)
    retry_handler = ConnectionRetry(config)

    def decorator(func: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = retry_handler.execute(
                lambda: func(*args, **kwargs),
                retry_on=retry_on,
            )
            if result.success:
                return None  # Success
            raise result.last_error or Exception("Retry failed")

        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            result = await retry_handler.execute_async(
                lambda: func(*args, **kwargs),
                retry_on=retry_on,
            )
            if result.success:
                return None  # Success
            raise result.last_error or Exception("Retry failed")

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper

    return decorator
