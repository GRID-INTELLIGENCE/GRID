import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from grid.infrastructure.database import DatabaseManager

logger = logging.getLogger(__name__)


class UsageTracker:
    """
    Tracks and persists usage events asynchronously using batch insertion.
    Follows Local-First principles (SQLite persistence).
    """

    def __init__(self, db_manager: DatabaseManager, batch_size: int = 100, flush_interval: int = 60):
        self.db = db_manager
        self._buffer: list[dict[str, Any]] = []
        self._lock = asyncio.Lock()
        self._batch_size = batch_size
        self._flush_interval = flush_interval
        self._running = False
        self._flush_task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the periodic flush task."""
        if self._running:
            return
        self._running = True
        self._flush_task = asyncio.create_task(self._periodic_flush())
        logger.info("UsageTracker started.")

    async def stop(self) -> None:
        """Stop tracking and flush remaining events."""
        self._running = False
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        await self.flush()
        logger.info("UsageTracker stopped.")

    async def track_event(self, user_id: str, event_type: str, quantity: int = 1) -> None:
        """Buffer a usage event."""
        async with self._lock:
            self._buffer.append(
                {"user_id": user_id, "event_type": event_type, "quantity": quantity, "timestamp": datetime.now(UTC)}
            )
            should_flush = len(self._buffer) >= self._batch_size

        if should_flush:
            # We don't await flush here to avoid blocking caller, unless critical
            # Ideally we flush in background, or just signal.
            # But duplicate flushes are safe due to lock in flush().
            asyncio.create_task(self.flush())

    async def flush(self) -> None:
        """Write buffered events to database."""
        async with self._lock:
            if not self._buffer:
                return

            batch = self._buffer[:]
            self._buffer.clear()

        try:
            query = "INSERT INTO usage_logs (user_id, event_type, quantity, timestamp) VALUES (?, ?, ?, ?)"
            # Ensure order matches query params
            params = [(e["user_id"], e["event_type"], e["quantity"], e["timestamp"]) for e in batch]

            await self.db.execute_many(query, params)
            await self.db.commit()

            # TODO: Add aggregation logic here if needed (e.g. update monthly stats)

            logger.debug(f"Flushed {len(batch)} usage events.")

        except Exception as e:
            logger.error(f"Failed to flush usage logs: {e}")
            # Optional: Re-buffer failed events?
            # For simplicity/safety against poison pills, we discard and log.

    async def _periodic_flush(self) -> None:
        while self._running:
            await asyncio.sleep(self._flush_interval)
            await self.flush()
