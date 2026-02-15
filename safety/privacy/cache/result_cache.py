"""
Result Cache for Privacy Detection.

Provides caching for detection results with TTL support.
Designed for both singular (personal) and collaborative (shared) contexts.
"""

from __future__ import annotations

import hashlib
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any

from safety.observability.logging_setup import get_logger

logger = get_logger("privacy.cache")


@dataclass
class CacheEntry:
    """Cached detection result with metadata."""

    result: list[dict[str, Any]]
    created_at: float
    ttl: int
    context_id: str  # For collaborative filtering

    @property
    def is_expired(self) -> bool:
        return time.time() - self.created_at > self.ttl


class DetectionCache:
    """
    LRU cache for PII detection results.

    Supports both:
    - Singular mode: user-specific caching (default)
    - Collaborative mode: shared workspace caching with context_id
    """

    def __init__(
        self,
        max_size: int = 10000,
        default_ttl: int = 3600,  # 1 hour
        collaborative: bool = False,
    ):
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._collaborative = collaborative

        # Metrics
        self._hits = 0
        self._misses = 0

    def _generate_key(
        self,
        content: str,
        enabled_patterns: frozenset[str],
        context_id: str | None = None,
    ) -> str:
        """Generate cache key from content and patterns."""
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        patterns_hash = hashlib.sha256(",".join(sorted(enabled_patterns)).encode()).hexdigest()[:8]

        # Include context_id for collaborative filtering
        ctx = context_id or "default"
        return f"privacy:{ctx}:{content_hash}:{patterns_hash}"

    async def get(
        self,
        content: str,
        enabled_patterns: frozenset[str],
        context_id: str | None = None,
    ) -> list[dict[str, Any]] | None:
        """
        Retrieve cached detection results.

        Args:
            content: The text content to check
            enabled_patterns: Which patterns were enabled
            context_id: Workspace/team ID for collaborative mode

        Returns:
            Cached result or None if not found/expired
        """
        key = self._generate_key(content, enabled_patterns, context_id)

        if key not in self._cache:
            self._misses += 1
            return None

        entry = self._cache[key]

        # Check expiration
        if entry.is_expired:
            del self._cache[key]
            self._misses += 1
            return None

        # Move to end (most recently used)
        self._cache.move_to_end(key)
        self._hits += 1

        logger.debug(
            "cache_hit",
            key=key[:32],
            hits=self._hits,
            misses=self._misses,
        )

        return entry.result

    async def set(
        self,
        content: str,
        result: list[dict[str, Any]],
        enabled_patterns: frozenset[str],
        ttl: int | None = None,
        context_id: str | None = None,
    ) -> None:
        """
        Cache detection results.

        Args:
            content: The text content
            result: Detection results to cache
            enabled_patterns: Which patterns were used
            ttl: Time-to-live in seconds
            context_id: Workspace/team ID for collaborative mode
        """
        key = self._generate_key(content, enabled_patterns, context_id)

        # Evict oldest if at capacity
        while len(self._cache) >= self._max_size:
            self._cache.popitem(last=False)

        self._cache[key] = CacheEntry(
            result=result,
            created_at=time.time(),
            ttl=ttl or self._default_ttl,
            context_id=context_id or "default",
        )

        # Move to end (most recently used)
        self._cache.move_to_end(key)

    async def invalidate(
        self,
        context_id: str | None = None,
    ) -> int:
        """
        Invalidate cache entries.

        Args:
            context_id: If provided, only invalidate entries for this context.
                       If None, invalidate all entries.

        Returns:
            Number of entries invalidated
        """
        if context_id is None:
            count = len(self._cache)
            self._cache.clear()
            return count

        # Invalidate only specific context
        keys_to_remove = [k for k, v in self._cache.items() if v.context_id == context_id]
        for key in keys_to_remove:
            del self._cache[key]

        return len(keys_to_remove)

    async def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0

        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "size": len(self._cache),
            "max_size": self._max_size,
            "collaborative": self._collaborative,
        }

    async def close(self) -> None:
        """Clean up resources."""
        self._cache.clear()


# Global instance for singular (personal) use
_default_cache: DetectionCache | None = None


def get_detection_cache(
    max_size: int = 10000,
    default_ttl: int = 3600,
    collaborative: bool = False,
) -> DetectionCache:
    """
    Get or create a detection cache instance.

    For singular/personal use, use the default instance.
    For collaborative use, create a new instance per workspace.
    """
    global _default_cache

    if not collaborative:
        if _default_cache is None:
            _default_cache = DetectionCache(
                max_size=max_size,
                default_ttl=default_ttl,
                collaborative=False,
            )
        return _default_cache

    # Create new instance for collaborative use
    return DetectionCache(
        max_size=max_size,
        default_ttl=default_ttl,
        collaborative=True,
    )


async def invalidate_context_cache(context_id: str) -> int:
    """Invalidate cache for a specific collaborative context."""
    cache = get_detection_cache()
    return await cache.invalidate(context_id)
