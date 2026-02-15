import asyncio
import logging
import re
import time
from collections import OrderedDict
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from safety.ai_workflow_safety import AIWorkflowSafetyEngine, TemporalSafetyConfig

from safety.privacy.observability.metrics import (
    SAFETY_ENGINE_CACHE_HITS,
    SAFETY_ENGINE_CACHE_MISSES,
    SAFETY_ENGINE_CACHE_SIZE,
)

logger = logging.getLogger(__name__)


class ContextSafeEngineManager:
    """
    Manages AIWorkflowSafetyEngine instances with thread-safe access,
    LRU eviction, and automatic cleanup to prevent memory leaks.
    """

    def __init__(self, max_cache_size: int = 10000, cleanup_interval_seconds: int = 300):
        self._engines: OrderedDict[str, tuple[AIWorkflowSafetyEngine, float]] = OrderedDict()
        self._lock = asyncio.Lock()
        self._max_cache_size = max_cache_size
        self._cleanup_interval = cleanup_interval_seconds
        self._last_cleanup = time.monotonic()

    async def get_engine(
        self, user_id: str, config: Optional["TemporalSafetyConfig"] = None
    ) -> "AIWorkflowSafetyEngine":
        """
        Retrieves or creates an AIWorkflowSafetyEngine for the given user_id.
        Updates the LRU access order.
        """
        # Validate user_id input
        if not user_id or not isinstance(user_id, str):
            raise ValueError("user_id must be a non-empty string")
        if len(user_id) > 255:
            raise ValueError("user_id too long (max 255 characters)")
        if not re.match(r"^[a-zA-Z0-9._-]+$", user_id):
            raise ValueError(
                "user_id contains invalid characters (only alphanumeric, dots, underscores, and hyphens allowed)"
            )

        async with self._lock:
            # Calculate single timestamp for consistency - use throughout method
            current_time = datetime.now(UTC).timestamp()

            # Periodic cleanup trigger
            if time.monotonic() - self._last_cleanup > self._cleanup_interval:
                await self._cleanup_expired(current_time)

            if user_id in self._engines:
                # Move to end to show recent use (LRU pattern)
                self._engines.move_to_end(user_id)
                engine, _ = self._engines[user_id]
                # Update access time - use current_time for consistency
                self._engines[user_id] = (engine, current_time)
                SAFETY_ENGINE_CACHE_HITS.inc()
                return engine

            SAFETY_ENGINE_CACHE_MISSES.inc()

            # Create new engine if not found
            if config is None:
                from safety.ai_workflow_safety import TemporalSafetyConfig

                config = TemporalSafetyConfig()

            from safety.ai_workflow_safety import AIWorkflowSafetyEngine

            engine = AIWorkflowSafetyEngine(user_id, config)

            # Enforce max cache size (LRU eviction)
            if len(self._engines) >= self._max_cache_size:
                # popitem(last=False) removes the first (oldest accessed) item
                removed_id, _ = self._engines.popitem(last=False)
                logger.info(f"Evicted safety engine for user {removed_id} due to cache limit")

            self._engines[user_id] = (engine, current_time)
            SAFETY_ENGINE_CACHE_SIZE.observe(len(self._engines))
            return engine

    async def _cleanup_expired(self, current_time: float | None = None, max_age_hours: int = 1):
        """
        Removes engines that haven't been accessed in the specified duration.
        Current implementation assumes holding the lock from the caller.

        Args:
            current_time: Timestamp to use for cutoff calculation (if None, uses datetime.now())
            max_age_hours: Maximum age in hours before engine is considered expired
        """
        if current_time is None:
            current_time = datetime.now(UTC).timestamp()
        cutoff_timestamp = current_time - (max_age_hours * 3600)

        # Identify expired keys
        expired_keys = [uid for uid, (_, last_access) in self._engines.items() if last_access < cutoff_timestamp]

        for uid in expired_keys:
            del self._engines[uid]

        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired safety engines")

        self._last_cleanup = time.monotonic()


# Global singleton instance of the manager
_engine_manager = ContextSafeEngineManager()


async def get_safe_engine(user_id: str, config: Optional["TemporalSafetyConfig"] = None) -> "AIWorkflowSafetyEngine":
    """Helper accessor for the global manager instance."""
    return await _engine_manager.get_engine(user_id, config)
