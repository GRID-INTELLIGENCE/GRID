from __future__ import annotations

import json
import logging
import os

import redis
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis-backed cache implementation."""

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, password: str | None = None):
        try:
            self.client = redis.Redis(
                host=host, port=port, db=db, password=password, decode_responses=True, socket_timeout=2
            )
            # Test connection
            self.client.ping()
            self.available = True
            logger.info(f"Connected to Redis at {host}:{port}")
        except Exception as e:
            self.available = False
            logger.warning(f"Redis connection failed: {e}. Caching will be disabled or fall back.")

    def get(self, key: str) -> str | None:
        if not self.available:
            return None
        try:
            return self.client.get(key)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    def set(self, key: str, value: str, expire: int = 3600) -> bool:
        if not self.available:
            return False
        try:
            return self.client.set(key, value, ex=expire)
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False


class MemoryCache:
    """In-memory fallback cache."""

    def __init__(self):
        self._data: dict[str, str] = {}
        logger.info("Initialized in-memory cache fallback")

    def get(self, key: str) -> str | None:
        return self._data.get(key)

    def set(self, key: str, value: str, expire: int = None) -> bool:
        self._data[key] = value
        return True


class GlobalCache:
    """Factory for cache instances."""

    _instance: RedisCache | MemoryCache | None = None

    @classmethod
    def get_instance(cls) -> RedisCache | MemoryCache:
        if cls._instance is None:
            use_redis = os.getenv("MOTHERSHIP_USE_REDIS", "0") == "1"
            if use_redis:
                cls._instance = RedisCache(
                    host=os.getenv("REDIS_HOST", "localhost"),
                    port=int(os.getenv("REDIS_PORT", "6379")),
                )
                if not cls._instance.available:
                    cls._instance = MemoryCache()
            else:
                cls._instance = MemoryCache()
        return cls._instance


def cache_json(key: str, expire: int = 3600):
    """Decorator for caching JSON-serializable function results."""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache = GlobalCache.get_instance()
            # Simple key generation (can be improved)
            cache_key = f"{func.__name__}:{key}:" + str(args) + str(kwargs)
            cached_val = cache.get(cache_key)
            if cached_val:
                return json.loads(cached_val)

            result = await func(*args, **kwargs)

            # Serialize result
            if isinstance(result, BaseModel):
                val_to_cache = result.model_dump_json()
            else:
                val_to_cache = json.dumps(result)

            cache.set(cache_key, val_to_cache, expire=expire)
            return result

        return wrapper

    return decorator
