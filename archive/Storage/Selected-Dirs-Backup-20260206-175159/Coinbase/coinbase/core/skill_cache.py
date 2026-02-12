"""
Skill Cache Module
==================
Caching layer for skill metadata and execution results.

Usage:
    from coinbase.core.skill_cache import SkillCache, cached_skill_execution

    cache = SkillCache()

    # Cache skill result
    result = cache.get_or_execute("skill_id", lambda: expensive_operation())
"""

import hashlib
import json
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Single cache entry."""

    key: str
    value: Any
    timestamp: datetime
    ttl_seconds: int
    access_count: int = 1
    last_accessed: datetime = field(default_factory=datetime.now)

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return datetime.now() - self.timestamp > timedelta(seconds=self.ttl_seconds)

    def touch(self) -> None:
        """Update last accessed time and increment count."""
        self.last_accessed = datetime.now()
        self.access_count += 1


class SkillCache:
    """
    Cache for skill metadata and execution results.

    Features:
    - In-memory caching with TTL
    - LRU eviction policy
    - Cache statistics tracking
    - Thread-safe operations
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        Initialize skill cache.

        Args:
            max_size: Maximum number of cached entries (1-10000)
            default_ttl: Default TTL in seconds (1-86400)
        """
        # Validate inputs
        if not isinstance(max_size, int) or max_size < 1 or max_size > 10000:
            raise ValueError(f"max_size must be an integer between 1 and 10000, got {max_size}")
        if not isinstance(default_ttl, int) or default_ttl < 1 or default_ttl > 86400:
            raise ValueError(
                f"default_ttl must be an integer between 1 and 86400 seconds, got {default_ttl}"
            )

        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: dict[str, CacheEntry] = {}
        self._stats = {"hits": 0, "misses": 0, "evictions": 0, "insertions": 0}
        self._lock = False  # Simple lock flag for thread safety

    def _acquire_lock(self) -> None:
        """Acquire simple lock."""
        import threading

        if not hasattr(self, "_real_lock"):
            self._real_lock = threading.Lock()
        self._real_lock.acquire()

    def _release_lock(self) -> None:
        """Release lock."""
        if hasattr(self, "_real_lock"):
            self._real_lock.release()

    def _generate_key(self, skill_id: str, params: dict | None = None) -> str:
        """Generate cache key from skill ID and parameters."""
        if params:
            # Create hash of parameters
            params_str = json.dumps(params, sort_keys=True)
            params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
            return f"{skill_id}:{params_hash}"
        return skill_id

    def get(self, key: str) -> Any | None:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        self._acquire_lock()
        try:
            entry = self._cache.get(key)

            if entry is None:
                self._stats["misses"] += 1
                return None

            if entry.is_expired():
                del self._cache[key]
                self._stats["misses"] += 1
                return None

            entry.touch()
            self._stats["hits"] += 1
            return entry.value

        finally:
            self._release_lock()

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Optional custom TTL
        """
        self._acquire_lock()
        try:
            # Evict expired entries
            self._evict_expired()

            # Evict oldest if at capacity
            if len(self._cache) >= self.max_size:
                self._evict_oldest()

            # Create new entry
            entry = CacheEntry(
                key=key,
                value=value,
                timestamp=datetime.now(),
                ttl_seconds=ttl_seconds or self.default_ttl,
            )

            self._cache[key] = entry
            self._stats["insertions"] += 1

        finally:
            self._release_lock()

    def get_or_execute(
        self, key: str, executor: Callable[[], Any], ttl_seconds: int | None = None
    ) -> Any:
        """
        Get from cache or execute function and cache result.

        Args:
            key: Cache key
            executor: Function to execute if cache miss
            ttl_seconds: Optional custom TTL

        Returns:
            Cached or computed value
        """
        # Try cache first
        cached = self.get(key)
        if cached is not None:
            return cached

        # Execute and cache
        try:
            result = executor()
            self.set(key, result, ttl_seconds)
            return result
        except Exception as e:
            logger.error(f"Execution failed for key {key}: {e}")
            raise

    def invalidate(self, key: str) -> bool:
        """
        Invalidate cache entry.

        Args:
            key: Cache key

        Returns:
            True if entry was found and removed
        """
        self._acquire_lock()
        try:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
        finally:
            self._release_lock()

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all entries matching pattern.

        Args:
            pattern: Key pattern to match

        Returns:
            Number of entries invalidated
        """
        self._acquire_lock()
        try:
            keys_to_remove = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_remove:
                del self._cache[key]
            return len(keys_to_remove)
        finally:
            self._release_lock()

    def clear(self) -> None:
        """Clear all cache entries."""
        self._acquire_lock()
        try:
            self._cache.clear()
            logger.info("Cache cleared")
        finally:
            self._release_lock()

    def _evict_expired(self) -> None:
        """Remove expired entries."""
        expired_keys = [k for k, v in self._cache.items() if v.is_expired()]
        for key in expired_keys:
            del self._cache[key]
            self._stats["evictions"] += 1

    def _evict_oldest(self) -> None:
        """Remove least recently used entry."""
        if not self._cache:
            return

        # Find oldest by last accessed
        oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].last_accessed)
        del self._cache[oldest_key]
        self._stats["evictions"] += 1

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        self._acquire_lock()
        try:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0

            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hit_rate": round(hit_rate, 4),
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "evictions": self._stats["evictions"],
                "insertions": self._stats["insertions"],
            }
        finally:
            self._release_lock()

    def get_cache_info(self) -> list[dict[str, Any]]:
        """Get information about cached entries."""
        self._acquire_lock()
        try:
            return [
                {
                    "key": entry.key,
                    "age_seconds": (datetime.now() - entry.timestamp).seconds,
                    "ttl_seconds": entry.ttl_seconds,
                    "access_count": entry.access_count,
                    "expired": entry.is_expired(),
                }
                for entry in self._cache.values()
            ]
        finally:
            self._release_lock()


# Global cache instance
_global_skill_cache: SkillCache | None = None


def get_skill_cache() -> SkillCache:
    """Get global skill cache instance."""
    global _global_skill_cache
    if _global_skill_cache is None:
        _global_skill_cache = SkillCache()
    return _global_skill_cache


def cached_skill_execution(ttl_seconds: int | None = None) -> Callable:
    """
    Decorator for caching skill execution results.

    Args:
        ttl_seconds: Optional custom TTL

    Usage:
        @cached_skill_execution(ttl_seconds=300)
        def my_skill(data):
            return expensive_computation(data)
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Generate cache key
            cache = get_skill_cache()

            # Create key from function name and arguments
            key_data = {"func": func.__name__, "args": args, "kwargs": kwargs}
            key_str = json.dumps(key_data, sort_keys=True, default=str)
            key = hashlib.md5(key_str.encode()).hexdigest()

            # Try cache
            cached = cache.get(key)
            if cached is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached

            # Execute and cache
            result = func(*args, **kwargs)
            cache.set(key, result, ttl_seconds)
            logger.debug(f"Cached result for {func.__name__}")

            return result

        return wrapper

    return decorator


def invalidate_skill_cache(skill_id: str) -> None:
    """
    Invalidate cache entries for a skill.

    Args:
        skill_id: Skill ID to invalidate
    """
    cache = get_skill_cache()
    count = cache.invalidate_pattern(skill_id)
    logger.info(f"Invalidated {count} cache entries for skill {skill_id}")


# Convenience functions
def cache_skill_result(skill_id: str, params: dict, result: Any, ttl: int = 3600) -> None:
    """Cache skill execution result."""
    cache = get_skill_cache()
    key = cache._generate_key(skill_id, params)
    cache.set(key, result, ttl)


def get_cached_skill_result(skill_id: str, params: dict | None = None) -> Any | None:
    """Get cached skill result."""
    cache = get_skill_cache()
    key = cache._generate_key(skill_id, params)
    return cache.get(key)
