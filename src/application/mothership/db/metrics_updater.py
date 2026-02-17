"""Background metrics updater for DB engine connections."""

import asyncio
import logging

from .engine import METRICS_ENABLED, _db_connections, get_async_engine

logger = logging.getLogger(__name__)

_metrics_updater_task: asyncio.Task | None = None
_metrics_updater_interval = 30  # Update every 30 seconds


async def _update_db_metrics() -> None:
    """Update DB connection metrics."""
    if not METRICS_ENABLED:
        return

    try:
        engine = get_async_engine()
        if engine and engine.pool:
            pool_size = engine.pool.size()
            checked_out = engine.pool.checkedout()
            _db_connections.set(checked_out)
            logger.debug(f"DB metrics updated: {checked_out}/{pool_size} connections")
    except Exception as e:
        logger.error(f"Failed to update DB metrics: {e}")


async def _metrics_updater_loop() -> None:
    """Background task to continuously update DB metrics."""
    while True:
        await _update_db_metrics()
        await asyncio.sleep(_metrics_updater_interval)


async def start_metrics_updater() -> None:
    """Start the background metrics updater."""
    global _metrics_updater_task

    if _metrics_updater_task is None or _metrics_updater_task.done():
        _metrics_updater_task = asyncio.create_task(_metrics_updater_loop())
        logger.info("DB metrics updater started")


async def stop_metrics_updater() -> None:
    """Stop the background metrics updater."""
    global _metrics_updater_task

    if _metrics_updater_task and not _metrics_updater_task.done():
        _metrics_updater_task.cancel()
        try:
            await _metrics_updater_task
        except asyncio.CancelledError:
            pass
        logger.info("DB metrics updater stopped")


__all__ = [
    "start_metrics_updater",
    "stop_metrics_updater",
    "_update_db_metrics",
]
