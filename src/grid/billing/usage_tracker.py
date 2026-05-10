import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from grid.infrastructure.database import DatabaseManager

logger = logging.getLogger(__name__)

_DEAD_LETTER_CAP = 10_000
# Sentinel dict placed in queue to wake the worker on shutdown.
# Using a specific id() identity check so type narrowing stays clean.
_STOP_SENTINEL: dict[str, Any] = {"__stop_sentinel__": True}


class UsageTracker:
    """
    Tracks and persists usage events via a bounded queue + single consumer worker.

    Replaces threshold-triggered asyncio.create_task(flush) fan-out with a
    deterministic single-worker pattern: one long-lived task drains the queue
    and flushes on batch_size or flush_interval, whichever comes first.
    Backpressure: queue-full events go to dead-letter (bounded); dead-letter
    items are prepended to the next batch for retry.
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        batch_size: int = 100,
        flush_interval: int = 60,
        max_queue_size: int = 10_000,
    ) -> None:
        self.db = db_manager
        self._batch_size = batch_size
        self._flush_interval = flush_interval
        self._queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=max_queue_size)
        self._stop_event = asyncio.Event()
        self._worker_task: asyncio.Task | None = None
        self._dead_letter: list[dict[str, Any]] = []
        # Counters
        self.events_enqueued = 0
        self.events_flushed = 0
        self.events_dead_lettered = 0
        self.events_dropped = 0
        self.flush_failures = 0

    async def start(self) -> None:
        """Start the single consumer worker task."""
        if self._worker_task and not self._worker_task.done():
            return
        self._stop_event.clear()
        self._worker_task = asyncio.create_task(self._worker_loop())
        logger.info("UsageTracker started.")

    async def stop(self) -> None:
        """Signal shutdown; worker drains queue and flushes remaining events."""
        self._stop_event.set()
        # Wake worker: await put() so we block until there's space even if the
        # queue is currently full (worker drains it, then accepts the sentinel).
        try:
            await asyncio.wait_for(self._queue.put(_STOP_SENTINEL), timeout=30.0)
        except asyncio.TimeoutError:
            pass  # Worker will still exit on next flush_interval timeout
        if self._worker_task:
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("UsageTracker stopped.")

    async def track_event(self, user_id: str, event_type: str, quantity: int = 1) -> None:
        """Enqueue a usage event. Routes to dead-letter when queue is full."""
        event: dict[str, Any] = {
            "user_id": user_id,
            "event_type": event_type,
            "quantity": quantity,
            "timestamp": datetime.now(UTC),
        }
        try:
            self._queue.put_nowait(event)
            self.events_enqueued += 1
        except asyncio.QueueFull:
            self._dead_letter.append(event)
            self.events_dead_lettered += 1
            self.events_dropped += 1
            if len(self._dead_letter) > _DEAD_LETTER_CAP:
                self._dead_letter = self._dead_letter[-_DEAD_LETTER_CAP:]
            logger.warning("UsageTracker queue full; event routed to dead-letter")

    async def flush(self) -> None:
        """Drain queue and dead-letter synchronously. For tests and manual use."""
        batch: list[dict[str, Any]] = []
        while not self._queue.empty():
            try:
                item = self._queue.get_nowait()
                if item is not _STOP_SENTINEL:
                    batch.append(item)
                self._queue.task_done()
            except asyncio.QueueEmpty:
                break
        if self._dead_letter:
            batch = self._dead_letter + batch
            self._dead_letter.clear()
        if batch:
            await self._flush_batch(batch)

    async def _worker_loop(self) -> None:
        """Single consumer: drain queue into batches, flush on size or interval."""
        batch: list[dict[str, Any]] = []

        while True:
            try:
                item = await asyncio.wait_for(
                    self._queue.get(), timeout=float(self._flush_interval)
                )
                self._queue.task_done()

                # Sentinel means stop was requested; flush current batch and exit
                if item is _STOP_SENTINEL:
                    break

                batch.append(item)
                if len(batch) >= self._batch_size:
                    await self._flush_batch(batch)
                    batch = []

            except asyncio.TimeoutError:
                if batch:
                    await self._flush_batch(batch)
                    batch = []
                # Check if we should exit after an interval with no items
                if self._stop_event.is_set() and self._queue.empty():
                    break

        # Final flush of anything remaining
        if batch:
            await self._flush_batch(batch)
        if self._dead_letter:
            await self._flush_batch(self._dead_letter)
            self._dead_letter.clear()

    async def _flush_batch(self, batch: list[dict[str, Any]]) -> None:
        """Write a batch to the database; on failure route to dead-letter for retry."""
        # Prepend accumulated dead-letter items for retry
        if self._dead_letter:
            batch = self._dead_letter + batch
            self._dead_letter.clear()

        if not batch:
            return

        try:
            query = "INSERT INTO usage_logs (user_id, event_type, quantity, timestamp) VALUES (?, ?, ?, ?)"
            params = [
                (e["user_id"], e["event_type"], e["quantity"], e["timestamp"])
                for e in batch
            ]
            await self.db.execute_many(query, params)
            await self.db.commit()
            self.events_flushed += len(batch)
            logger.debug(f"Flushed {len(batch)} usage events.")
        except Exception as e:
            self.flush_failures += 1
            logger.error(f"Failed to flush usage logs: {e}")
            self._dead_letter.extend(batch)
            if len(self._dead_letter) > _DEAD_LETTER_CAP:
                self._dead_letter = self._dead_letter[-_DEAD_LETTER_CAP:]
            logger.info(f"Re-buffered {len(batch)} events to dead-letter for retry")
