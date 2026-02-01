import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class CacheInterface(ABC):
    """Abstract interface for caching operations."""

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        pass

    @abstractmethod
    async def clear(self) -> None:
        pass


class MemoryCache(CacheInterface):
    """
    In-memory cache implementation using Python dict.
    Not shared across processes. Suitable for local dev.
    """

    def __init__(self):
        self._store: dict[str, dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            data = self._store.get(key)
            if not data:
                return None

            if data["expires_at"] < time.time():
                del self._store[key]
                return None

            return data["value"]

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        async with self._lock:
            self._store[key] = {"value": value, "expires_at": time.time() + ttl}

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._store.pop(key, None)

    async def clear(self) -> None:
        async with self._lock:
            self._store.clear()


class CacheFactory:
    @staticmethod
    def create(backend: str = "memory") -> CacheInterface:
        if backend == "memory":
            logger.info("Initializing MemoryCache")
            return MemoryCache()
        # Reserved for 'sqlite' or 'redis' implementations later
        logger.warning(f"Unknown backend '{backend}', falling back to MemoryCache")
        return MemoryCache()
