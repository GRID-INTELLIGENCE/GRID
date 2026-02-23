"""
CPU-Bound Task Executor for FastAPI.

Provides a ProcessPoolExecutor wrapper to offload heavy computational tasks
(NumPy, Scikit-learn, NetworkX) without blocking the async event loop.

Usage:
    from application.mothership.utils.cpu_executor import run_cpu_bound

    @router.post("/compute")
    async def compute_heavy(request: ComputeRequest):
        result = await run_cpu_bound(heavy_numpy_operation, request.data)
        return {"result": result}
"""

from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Global executor instance (initialized lazily)
_executor: ProcessPoolExecutor | None = None


def get_executor() -> ProcessPoolExecutor:
    """
    Get or create the global ProcessPoolExecutor.

    Worker count defaults to CPU count, capped at 4 to prevent resource exhaustion.
    """
    global _executor
    if _executor is None:
        max_workers = min(os.cpu_count() or 4, 4)
        _executor = ProcessPoolExecutor(max_workers=max_workers)
        logger.info(f"CPU executor initialized with {max_workers} workers")
    return _executor


async def run_cpu_bound[T](
    func: Callable[..., T],
    *args: Any,
    **kwargs: Any,
) -> T:
    """
    Run a CPU-bound function in a separate process.

    This prevents blocking the async event loop when performing
    heavy computational tasks like NumPy operations, ML inference,
    or graph computations.

    Args:
        func: The CPU-bound function to execute
        *args: Positional arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function

    Returns:
        The result of the function execution

    Raises:
        Exception: Any exception raised by the function is propagated

    Example:
        def heavy_computation(data: list) -> float:
            import numpy as np
            arr = np.array(data)
            return float(np.mean(arr ** 2))

        result = await run_cpu_bound(heavy_computation, [1, 2, 3, 4, 5])
    """
    loop = asyncio.get_running_loop()
    executor = get_executor()

    # Use partial to bind kwargs if present
    if kwargs:
        func = partial(func, **kwargs)

    try:
        result = await loop.run_in_executor(executor, func, *args)
        return result
    except Exception as e:
        logger.error(f"CPU-bound task failed: {func.__name__} - {e}")
        raise


def shutdown_executor() -> None:
    """
    Shutdown the executor gracefully.

    Should be called during application shutdown to clean up worker processes.
    """
    global _executor
    if _executor is not None:
        logger.info("Shutting down CPU executor...")
        _executor.shutdown(wait=True, cancel_futures=False)
        _executor = None
        logger.info("CPU executor shutdown complete")


# Thread pool variant for I/O-bound blocking operations
_thread_executor: ProcessPoolExecutor | None = None


async def run_blocking_io[T](
    func: Callable[..., T],
    *args: Any,
    **kwargs: Any,
) -> T:
    """
    Run a blocking I/O function in the default thread pool.

    Use this for blocking I/O operations (file reads, sync HTTP calls)
    that don't release the GIL. For CPU-bound work, use run_cpu_bound instead.

    Args:
        func: The blocking function to execute
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        The result of the function execution
    """
    loop = asyncio.get_running_loop()

    if kwargs:
        func = partial(func, **kwargs)

    # Use None to run in the default thread pool (not process pool)
    return await loop.run_in_executor(None, func, *args)


__all__ = [
    "get_executor",
    "run_cpu_bound",
    "run_blocking_io",
    "shutdown_executor",
]
