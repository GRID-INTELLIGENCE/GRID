"""Enhanced retry decorators with automatic metrics collection.

Wraps retry/fallback decorators to automatically record metrics to the global
MetricsCollector for observability.
"""

import functools
import logging
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar, cast

from grid.resilience.metrics import get_metrics_collector
from grid.resilience.retry_decorator import async_fallback, async_retry, fallback, retry

logger = logging.getLogger(__name__)

T = TypeVar("T")

__all__ = [
    "observed_retry",
    "observed_async_retry",
    "observed_fallback",
    "observed_async_fallback",
]


def observed_retry(
    operation_name: str,
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    exceptions: tuple[type[Exception], ...] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for synchronous functions with retry + automatic metrics.

    Combines retry logic with automatic metrics collection for observability.

    Example:
        @observed_retry(
            "network.fetch_api",
            max_attempts=3,
            exceptions=(ConnectionError, TimeoutError)
        )
        def fetch_data(url: str) -> dict:
            return requests.get(url).json()

    Args:
        operation_name: Unique identifier for metrics tracking.
        max_attempts: Maximum retry attempts.
        backoff_factor: Exponential backoff multiplier.
        initial_delay: Initial delay in seconds.
        exceptions: Exceptions to retry on.

    Returns:
        Decorated function with retry + metrics.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Apply base retry decorator
        retry_decorated = retry(
            max_attempts=max_attempts,
            backoff_factor=backoff_factor,
            initial_delay=initial_delay,
            exceptions=exceptions,
        )(func)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            collector = get_metrics_collector()
            try:
                result = retry_decorated(*args, **kwargs)
                collector.record_attempt(operation_name, success=True)
                return result
            except Exception as e:
                collector.record_attempt(operation_name, success=False, error=e)
                raise

        return cast(Callable[..., T], wrapper)

    return decorator


def observed_async_retry(
    operation_name: str,
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    exceptions: tuple[type[Exception], ...] | None = None,
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """Decorator for async functions with retry + automatic metrics.

    Example:
        @observed_async_retry(
            "llm.inference",
            max_attempts=3,
            exceptions=(asyncio.TimeoutError,)
        )
        async def llm_complete(prompt: str) -> str:
            return await model.complete(prompt)

    Args:
        operation_name: Unique identifier for metrics tracking.
        max_attempts: Maximum retry attempts.
        backoff_factor: Exponential backoff multiplier.
        initial_delay: Initial delay in seconds.
        exceptions: Exceptions to retry on.

    Returns:
        Decorated async function with retry + metrics.
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        # Apply base retry decorator
        retry_decorated = async_retry(
            max_attempts=max_attempts,
            backoff_factor=backoff_factor,
            initial_delay=initial_delay,
            exceptions=exceptions,
        )(func)

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            collector = get_metrics_collector()
            try:
                result = await retry_decorated(*args, **kwargs)
                collector.record_attempt(operation_name, success=True)
                return result
            except Exception as e:
                collector.record_attempt(operation_name, success=False, error=e)
                raise

        return cast(Callable[..., Awaitable[T]], wrapper)

    return decorator


def observed_fallback(
    operation_name: str,
    fallback_func: Callable[..., T],
    exceptions: tuple[type[Exception], ...] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for synchronous functions with fallback + automatic metrics.

    Example:
        def default_result() -> dict:
            return {"cached": True, "status": "fallback"}

        @observed_fallback(
            "api.search",
            fallback_func=default_result
        )
        def search_api(query: str) -> dict:
            return requests.get(f"https://api.example.com/search?q={query}").json()

    Args:
        operation_name: Unique identifier for metrics tracking.
        fallback_func: Function to call on failure.
        exceptions: Exceptions to trigger fallback.

    Returns:
        Decorated function with fallback + metrics.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Apply base fallback decorator
        fallback_decorated = fallback(
            fallback_func=fallback_func,
            exceptions=exceptions,
        )(func)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            collector = get_metrics_collector()
            try:
                result = fallback_decorated(*args, **kwargs)
                collector.record_attempt(operation_name, success=True)
                return result
            except Exception as e:
                collector.record_fallback(operation_name)
                collector.record_attempt(operation_name, success=False, error=e)
                raise

        return cast(Callable[..., T], wrapper)

    return decorator


def observed_async_fallback(
    operation_name: str,
    fallback_func: Callable[..., Awaitable[T]],
    exceptions: tuple[type[Exception], ...] | None = None,
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """Decorator for async functions with fallback + automatic metrics.

    Example:
        async def default_result_async() -> dict:
            return {"cached": True, "status": "fallback"}

        @observed_async_fallback(
            "api.async_search",
            fallback_func=default_result_async
        )
        async def search_api_async(query: str) -> dict:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://api.example.com/search?q={query}") as resp:
                    return await resp.json()

    Args:
        operation_name: Unique identifier for metrics tracking.
        fallback_func: Async function to call on failure.
        exceptions: Exceptions to trigger fallback.

    Returns:
        Decorated async function with fallback + metrics.
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        # Apply base fallback decorator
        fallback_decorated = async_fallback(
            fallback_func=fallback_func,
            exceptions=exceptions,
        )(func)

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            collector = get_metrics_collector()
            try:
                result = await fallback_decorated(*args, **kwargs)
                collector.record_attempt(operation_name, success=True)
                return result
            except Exception as e:
                collector.record_fallback(operation_name)
                collector.record_attempt(operation_name, success=False, error=e)
                raise

        return cast(Callable[..., Awaitable[T]], wrapper)

    return decorator
