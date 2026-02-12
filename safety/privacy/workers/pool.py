"""
Worker Pool for Batch Privacy Processing.

Provides async worker pool for processing multiple privacy requests in parallel.
"""

from __future__ import annotations

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable, Union

from safety.observability.logging_setup import get_logger

logger = get_logger("privacy.workers")


@dataclass
class BatchResult:
    """Result of batch processing."""

    total: int
    processed: int
    failed: int
    results: list[dict[str, Any]] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    duration_seconds: float = 0.0


class PrivacyWorkerPool:
    """
    Worker pool for batch privacy processing.

    Features:
    - Configurable number of workers
    - Per-item timeout
    - Progress tracking
    - Error handling with partial results
    """

    def __init__(
        self,
        max_workers: int = 4,
        items_timeout: float = 30.0,
    ):
        self._max_workers = max_workers
        self._items_timeout = items_timeout
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._semaphore = asyncio.Semaphore(max_workers)

    async def process_batch(
        self,
        items: list[dict[str, Any]],
        processor: Callable[[dict[str, Any]], dict[str, Any]],
    ) -> BatchResult:
        """
        Process a batch of items in parallel.

        Args:
            items: List of items to process
            processor: Async function to process each item

        Returns:
            BatchResult with all results and errors
        """
        start_time = time.perf_counter()

        if not items:
            return BatchResult(
                total=0,
                processed=0,
                failed=0,
                duration_seconds=0.0,
            )

        results = []
        errors = []

        async def process_with_semaphore(item: dict[str, Any], index: int) -> dict[str, Any]:
            async with self._semaphore:
                try:
                    # Run in executor to avoid blocking
                    result = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(self._executor, lambda: processor(item)),
                        timeout=self._items_timeout,
                    )
                    return {"index": index, "result": result, "error": None}
                except asyncio.TimeoutError:
                    logger.warning("batch_item_timeout", index=index)
                    return {
                        "index": index,
                        "result": None,
                        "error": {"type": "timeout", "item_index": index},
                    }
                except Exception as e:
                    logger.error("batch_item_error", index=index, error=str(e))
                    return {
                        "index": index,
                        "result": None,
                        "error": {"type": "error", "message": str(e), "item_index": index},
                    }

        # Process all items
        tasks = [process_with_semaphore(item, i) for i, item in enumerate(items)]
        task_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect results
        for task_result in task_results:
            if isinstance(task_result, Exception):
                errors.append({"type": "exception", "message": str(task_result)})
                continue
            # Type guard: task_result is now guaranteed to be dict[str, Any]
            assert isinstance(task_result, dict), "Expected dict after Exception check"
            if task_result.get("error"):
                errors.append(task_result["error"])
                results.append(task_result["result"])
            else:
                results.append(task_result["result"])

        duration = time.perf_counter() - start_time

        return BatchResult(
            total=len(items),
            processed=len(results),
            failed=len(errors),
            results=[r for r in results if r is not None],
            errors=errors,
            duration_seconds=duration,
        )

    async def process_with_limit(
        self,
        items: list[str],
        processor: Callable[[str], dict[str, Any]],
        max_concurrent: int | None = None,
    ) -> BatchResult:
        """
        Process text items with concurrency limit.

        Args:
            items: List of text strings to process
            processor: Function to process each text
            max_concurrent: Override max concurrent (default: max_workers)

        Returns:
            BatchResult
        """
        if max_concurrent:
            semaphore = asyncio.Semaphore(max_concurrent)
        else:
            semaphore = self._semaphore

        async def process_item(text: str, index: int) -> dict[str, Any]:
            async with semaphore:
                try:
                    result = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(self._executor, lambda: processor(text)),
                        timeout=self._items_timeout,
                    )
                    return {"index": index, "result": result, "error": None}
                except asyncio.TimeoutError:
                    return {
                        "index": index,
                        "result": None,
                        "error": {"type": "timeout", "item_index": index},
                    }
                except Exception as e:
                    return {
                        "index": index,
                        "result": None,
                        "error": {"type": "error", "message": str(e), "item_index": index},
                    }

        start_time = time.perf_counter()

        if not items:
            return BatchResult(total=0, processed=0, failed=0, duration_seconds=0.0)

        tasks = [process_item(text, i) for i, text in enumerate(items)]
        task_results = await asyncio.gather(*tasks, return_exceptions=True)

        results = []
        errors = []

        for task_result in task_results:
            if isinstance(task_result, Exception):
                errors.append({"type": "exception", "message": str(task_result)})
                continue
            # Type guard: task_result is now guaranteed to be dict[str, Any]
            assert isinstance(task_result, dict), "Expected dict after Exception check"
            if task_result.get("error"):
                errors.append(task_result["error"])
            else:
                results.append(task_result["result"])

        duration = time.perf_counter() - start_time

        return BatchResult(
            total=len(items),
            processed=len(results),
            failed=len(errors),
            results=results,
            errors=errors,
            duration_seconds=duration,
        )

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the worker pool."""
        self._executor.shutdown(wait=wait)
        logger.info("privacy_worker_pool_shutdown")


# Global pool instance
_pool: PrivacyWorkerPool | None = None


def get_worker_pool(max_workers: int = 4) -> PrivacyWorkerPool:
    """Get or create the global worker pool."""
    global _pool
    if _pool is None:
        _pool = PrivacyWorkerPool(max_workers=max_workers)
    return _pool


async def process_batch(
    items: list[dict[str, Any]],
    processor: Callable[[dict[str, Any]], dict[str, Any]],
    max_workers: int = 4,
) -> BatchResult:
    """
    Convenience function to process a batch of items.

    Args:
        items: Items to process
        processor: Processing function
        max_workers: Max concurrent workers

    Returns:
        BatchResult
    """
    pool = get_worker_pool(max_workers)
    return await pool.process_batch(items, processor)
