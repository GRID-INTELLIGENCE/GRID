"""Periodic processing engine."""

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ProcessingMode(StrEnum):
    """Processing modes."""

    PERIODIC = "periodic"  # Default: periodic processing
    REALTIME = "realtime"  # Emergency: real-time processing
    HYBRID = "hybrid"  # Mixed mode


class ProcessingSchedule(BaseModel):
    """Processing schedule configuration."""

    interval_seconds: float = Field(default=60.0, description="Processing interval in seconds")
    batch_size: int = Field(default=100, description="Batch size for processing")
    max_processing_time: float | None = Field(default=None, description="Max processing time per cycle")
    enabled: bool = Field(default=True, description="Whether schedule is enabled")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class PeriodicProcessor:
    """Processes operations periodically with configurable intervals."""

    def __init__(self, schedule: ProcessingSchedule | None = None):
        """Initialize periodic processor.

        Args:
            schedule: Processing schedule (defaults to 60s interval)
        """
        self.schedule = schedule or ProcessingSchedule()
        self._processing_queue: list[dict[str, Any]] = []
        self._processor_func: Callable[[list[dict[str, Any]]], Any] | None = None
        self._running = False
        self._task: asyncio.Task | None = None
        self._stats: dict[str, Any] = {
            "cycles": 0,
            "items_processed": 0,
            "last_cycle": None,
            "errors": 0,
        }

    def set_processor(self, processor_func: Callable[[list[dict[str, Any]]], Any]) -> None:
        """Set the processing function.

        Args:
            processor_func: Function to process items
        """
        self._processor_func = processor_func

    def enqueue(self, item: dict[str, Any]) -> None:
        """Enqueue an item for processing.

        Args:
            item: Item to process
        """
        self._processing_queue.append(item)

    def enqueue_batch(self, items: list[dict[str, Any]]) -> None:
        """Enqueue multiple items.

        Args:
            items: Items to process
        """
        self._processing_queue.extend(items)

    async def start(self) -> None:
        """Start periodic processing."""
        if self._running:
            return

        if not self._processor_func:
            raise ValueError("No processor function set. Call set_processor first.")

        self._running = True
        self._task = asyncio.create_task(self._processing_loop())

    async def stop(self) -> None:
        """Stop periodic processing."""
        self._running = False
        if self._task:
            await self._task
            self._task = None

    async def _processing_loop(self) -> None:
        """Main processing loop."""
        while self._running:
            try:
                await self._process_cycle()
                await asyncio.sleep(self.schedule.interval_seconds)
            except Exception as e:
                self._stats["errors"] += 1
                print(f"Error in processing cycle: {e}")

    async def _process_cycle(self) -> None:
        """Process one cycle."""
        if not self._processing_queue:
            return

        # Get batch
        batch = self._processing_queue[: self.schedule.batch_size]
        self._processing_queue = self._processing_queue[self.schedule.batch_size :]

        # Process batch
        start_time = datetime.now(UTC)
        try:
            if self._processor_func:
                await asyncio.to_thread(self._processor_func, batch)

            self._stats["cycles"] += 1
            self._stats["items_processed"] += len(batch)
            self._stats["last_cycle"] = start_time.isoformat()
        except Exception:
            self._stats["errors"] += 1
            raise

    def get_stats(self) -> dict[str, Any]:
        """Get processing statistics.

        Returns:
            Statistics dictionary
        """
        return {
            **self._stats,
            "queue_size": len(self._processing_queue),
            "schedule": self.schedule.model_dump(),
        }

    def get_queue_size(self) -> int:
        """Get current queue size."""
        return len(self._processing_queue)
