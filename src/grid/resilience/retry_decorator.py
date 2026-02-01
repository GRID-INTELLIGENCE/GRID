"""Resilient retry and fallback decorators for error recovery.

Provides reusable decorators for automatic retry logic with exponential backoff,
fallback strategies, and integration with the GRID error classification system.

Leverages grid.resilience.error_classifier and grid.resilience.recovery_engine
for intelligent error handling and recovery strategies.
"""

import asyncio
import functools
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar, cast

logger = logging.getLogger(__name__)

T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_attempts: int = 3,
        backoff_factor: float = 2.0,
        initial_delay: float = 1.0,
        max_delay: float = 300.0,
        exceptions: tuple[type[Exception], ...] | None = None,
        on_retry: Callable[[int, Exception], None] | None = None,
    ) -> None:
        """Initialize retry configuration.

        Args:
            max_attempts: Maximum number of retry attempts (default: 3).
            backoff_factor: Exponential backoff multiplier (default: 2.0).
            initial_delay: Initial delay in seconds (default: 1.0).
            max_delay: Maximum delay cap in seconds (default: 300.0).
            exceptions: Tuple of exceptions to retry on. If None, retries on all exceptions.
            on_retry: Optional callback invoked before each retry attempt.
        """
        self.max_attempts = max_attempts
        self.backoff_factor = backoff_factor
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exceptions = exceptions or (Exception,)
        self.on_retry = on_retry

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for the given attempt number.

        Uses exponential backoff formula: delay = initial_delay * (backoff_factor ^ attempt)

        Args:
            attempt: Zero-indexed attempt number.

        Returns:
            Delay in seconds, capped at max_delay.
        """
        delay = self.initial_delay * (self.backoff_factor**attempt)
        return min(delay, self.max_delay)


def retry(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    exceptions: tuple[type[Exception], ...] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for synchronous functions with automatic retry logic.

    Retries the decorated function with exponential backoff on transient failures.

    Example:
        @retry(max_attempts=3, exceptions=(ConnectionError, TimeoutError))
        def fetch_data(url: str) -> dict:
            return requests.get(url).json()

    Args:
        max_attempts: Maximum number of attempts (default: 3).
        backoff_factor: Exponential backoff multiplier (default: 2.0).
        initial_delay: Initial delay in seconds (default: 1.0).
        exceptions: Tuple of exception types to retry on.

    Returns:
        Decorated function that automatically retries on failure.
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        backoff_factor=backoff_factor,
        initial_delay=initial_delay,
        exceptions=exceptions,
    )

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Exception | None = None

            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except config.exceptions as e:
                    last_exception = e
                    if attempt < config.max_attempts - 1:
                        delay = config.calculate_delay(attempt)
                        logger.warning(
                            f"🔄 Retry attempt {attempt + 1}/{config.max_attempts} "
                            f"for {func.__name__} after {e.__class__.__name__}. "
                            f"Waiting {delay:.2f}s..."
                        )
                        if config.on_retry:
                            config.on_retry(attempt, e)
                        time.sleep(delay)
                    else:
                        logger.error(f"✗ All {config.max_attempts} attempts failed for {func.__name__}: {e}")

            if last_exception:
                raise last_exception
            return func(*args, **kwargs)

        return cast(Callable[..., T], wrapper)

    return decorator


def async_retry(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    exceptions: tuple[type[Exception], ...] | None = None,
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """Decorator for async functions with automatic retry logic.

    Retries the decorated async function with exponential backoff on transient failures.

    Example:
        @async_retry(max_attempts=3, exceptions=(asyncio.TimeoutError,))
        async def fetch_data_async(url: str) -> dict:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    return await resp.json()

    Args:
        max_attempts: Maximum number of attempts (default: 3).
        backoff_factor: Exponential backoff multiplier (default: 2.0).
        initial_delay: Initial delay in seconds (default: 1.0).
        exceptions: Tuple of exception types to retry on.

    Returns:
        Decorated async function that automatically retries on failure.
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        backoff_factor=backoff_factor,
        initial_delay=initial_delay,
        exceptions=exceptions,
    )

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Exception | None = None

            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except config.exceptions as e:
                    last_exception = e
                    if attempt < config.max_attempts - 1:
                        delay = config.calculate_delay(attempt)
                        logger.warning(
                            f"🔄 Retry attempt {attempt + 1}/{config.max_attempts} "
                            f"for {func.__name__} after {e.__class__.__name__}. "
                            f"Waiting {delay:.2f}s..."
                        )
                        if config.on_retry:
                            config.on_retry(attempt, e)
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"✗ All {config.max_attempts} attempts failed for {func.__name__}: {e}")

            if last_exception:
                raise last_exception
            return await func(*args, **kwargs)

        return cast(Callable[..., Awaitable[T]], wrapper)

    return decorator


def fallback[T](
    fallback_func: Callable[..., T],
    exceptions: tuple[type[Exception], ...] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for synchronous functions with fallback strategy.

    If the decorated function raises an exception, invokes the fallback function instead.

    Example:
        def default_result() -> dict:
            return {"status": "unavailable", "cached": True}

        @fallback(fallback_func=default_result)
        def fetch_data(url: str) -> dict:
            return requests.get(url, timeout=2).json()

    Args:
        fallback_func: Function to call if original function fails.
        exceptions: Tuple of exception types to trigger fallback. If None, catches all.

    Returns:
        Decorated function with fallback behavior.
    """
    if exceptions is None:
        exceptions = (Exception,)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                logger.warning(f"⚡ Fallback triggered for {func.__name__} due to {e.__class__.__name__}: {e}")
                return fallback_func(*args, **kwargs)

        return cast(Callable[..., T], wrapper)

    return decorator


def async_fallback[T](
    fallback_func: Callable[..., Awaitable[T]],
    exceptions: tuple[type[Exception], ...] | None = None,
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """Decorator for async functions with fallback strategy.

    If the decorated async function raises an exception, invokes the fallback async function.

    Example:
        async def default_result_async() -> dict:
            return {"status": "unavailable", "cached": True}

        @async_fallback(fallback_func=default_result_async)
        async def fetch_data_async(url: str) -> dict:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=2) as resp:
                    return await resp.json()

    Args:
        fallback_func: Async function to call if original function fails.
        exceptions: Tuple of exception types to trigger fallback. If None, catches all.

    Returns:
        Decorated async function with fallback behavior.
    """
    if exceptions is None:
        exceptions = (Exception,)

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return await func(*args, **kwargs)
            except exceptions as e:
                logger.warning(f"⚡ Fallback triggered for {func.__name__} due to {e.__class__.__name__}: {e}")
                return await fallback_func(*args, **kwargs)

        return cast(Callable[..., Awaitable[T]], wrapper)

    return decorator


__all__ = [
    "RetryConfig",
    "retry",
    "async_retry",
    "fallback",
    "async_fallback",
]
