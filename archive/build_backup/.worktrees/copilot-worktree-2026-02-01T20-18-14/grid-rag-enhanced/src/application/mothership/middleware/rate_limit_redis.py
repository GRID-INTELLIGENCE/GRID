"""
Cognitive-aware Redis-backed rate limiting middleware.

Provides distributed rate limiting using Redis with fallback to in-memory storage.
Dynamically adjusts rate limits based on cognitive load metrics.
"""

from __future__ import annotations

import importlib
import logging
import time
from typing import Any

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Import cognitive engine
from grid.cognitive.engine import CognitiveEngine

# Import quality gates configuration
try:
    from config.cognitive_settings import get_cognitive_load_thresholds
    from config.quality_gates import get_rate_limit
except ImportError:
    # Fallback if modules not available
    def get_rate_limit(limit_type: str = "default") -> int:
        return 60

    def get_cognitive_load_thresholds() -> dict:
        return {"low": 0.3, "medium": 0.6, "high": 0.8}


logger = logging.getLogger(__name__)


class CognitiveRedisRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Cognitive-aware Redis-backed rate limiting middleware.
    Dynamically adjusts rate limits based on cognitive load metrics.
    """

    def __init__(
        self,
        app: ASGIApp,
        requests_per_minute: int | None = None,
        redis_url: str | None = None,
        exclude_paths: list[str] | None = None,
        cognitive_engine: CognitiveEngine | None = None,
    ):
        super().__init__(app)
        self.cognitive_engine = cognitive_engine
        self.cognitive_thresholds = get_cognitive_load_thresholds()
        self.base_requests_per_minute = requests_per_minute or get_rate_limit("default")
        self.redis_url = redis_url
        self.exclude_paths = exclude_paths or ["/health", "/ping", "/metrics"]
        self._redis_client: Any | None = None
        self._fallback_store: dict[str, list[float]] = {}
        self._redis_initialized = False

    def _get_client_key(self, request: Request) -> str:
        """Get identifier for rate limiting."""
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key:{api_key[:16]}"
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"

    def _get_cognitive_adjustment_factor(self, key: str) -> float:
        """Get rate limit adjustment factor based on cognitive load."""
        if not self.cognitive_engine:
            return 1.0

        try:
            # Get cognitive load metrics for the user/system
            load_metrics = self.cognitive_engine.get_load_metrics(key)
            cognitive_load = load_metrics.get("overall_load", 0.0)

            # Apply adaptive scaling based on cognitive load
            if cognitive_load > self.cognitive_thresholds["high"]:
                return 0.5  # Reduce rate limit by 50% under high load
            elif cognitive_load > self.cognitive_thresholds["medium"]:
                return 0.75  # Reduce rate limit by 25% under medium load
            return 1.0
        except Exception as e:
            logger.warning(f"Cognitive load check failed: {e}, using default factor")
            return 1.0

    async def _ensure_redis(self) -> None:
        """Ensure Redis client is initialized."""
        if self._redis_initialized:
            return

        if not self.redis_url:
            raise RuntimeError("Redis URL not configured")

        try:
            aioredis = importlib.import_module("redis.asyncio")

            self._redis_client = aioredis.from_url(self.redis_url, decode_responses=False)
            # Test connection
            redis_client = self._redis_client
            if redis_client is not None:
                await redis_client.ping()
            self._redis_initialized = True
            logger.info("Redis rate limiting enabled")
        except ImportError:
            logger.warning("Redis package not available, using in-memory rate limiting")
            self._redis_client = None
            self._redis_initialized = True
        except Exception as e:
            logger.warning(f"Redis connection failed, using in-memory: {e}")
            self._redis_client = None
            self._redis_initialized = True

    async def _is_rate_limited_cognitive(self, key: str) -> tuple[bool, int, int]:
        """Cognitive-aware rate limit check."""
        adjustment_factor = self._get_cognitive_adjustment_factor(key)
        effective_rpm = max(1, int(self.base_requests_per_minute * adjustment_factor))

        try:
            if self.redis_url and self._redis_initialized:
                return await self._is_rate_limited_redis(key, effective_rpm)
            return self._is_rate_limited_memory(key, effective_rpm)
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Fallback to in-memory with base RPM
            return self._is_rate_limited_memory(key, self.base_requests_per_minute)

    async def _is_rate_limited_redis(self, key: str, effective_rpm: int) -> tuple[bool, int, int]:
        """Redis implementation with cognitive-adjusted limits."""
        await self._ensure_redis()
        if not self._redis_client:
            raise RuntimeError("Redis client not available")

        redis_key = f"cog_rate_limit:{key}"
        now = int(time.time())
        window_start = now - 60

        try:
            pipe = self._redis_client.pipeline()
            pipe.zremrangebyscore(redis_key, 0, window_start)
            pipe.zcard(redis_key)
            pipe.zadd(redis_key, {str(now): now})
            pipe.expire(redis_key, 120)
            results = await pipe.execute()

            current_count = results[1] if len(results) > 1 else 0

            if current_count >= effective_rpm:
                return True, 0, effective_rpm

            remaining = max(0, effective_rpm - current_count - 1)
            return False, remaining, effective_rpm
        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            raise

    def _is_rate_limited_memory(self, key: str, effective_rpm: int) -> tuple[bool, int, int]:
        """In-memory implementation with cognitive-adjusted limits."""
        now = time.time()
        window = 60.0

        if key not in self._fallback_store:
            self._fallback_store[key] = []

        self._fallback_store[key] = [ts for ts in self._fallback_store[key] if now - ts < window]
        current_count = len(self._fallback_store[key])

        if current_count >= effective_rpm:
            return True, 0, effective_rpm

        self._fallback_store[key].append(now)
        remaining = max(0, effective_rpm - current_count - 1)
        return False, remaining, effective_rpm

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        """Process request with cognitive-aware rate limiting."""
        if any(request.url.path.startswith(p) for p in self.exclude_paths):
            return await call_next(request)

        client_key = self._get_client_key(request)

        try:
            is_limited, remaining, effective_rpm = await self._is_rate_limited_cognitive(client_key)
        except Exception as e:
            logger.error(f"Cognitive rate limit check failed: {e}, allowing request")
            is_limited = False
            remaining = self.base_requests_per_minute
            effective_rpm = self.base_requests_per_minute

        if is_limited:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "success": False,
                    "error": {
                        "code": "COGNITIVE_RATE_LIMIT_EXCEEDED",
                        "message": "Rate limit exceeded based on current cognitive load",
                        "cognitive_adjustment": effective_rpm / self.base_requests_per_minute
                    },
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(effective_rpm),
                    "X-RateLimit-Remaining": "0",
                    "X-Cognitive-Load-Adjustment": f"{effective_rpm / self.base_requests_per_minute:.2f}"
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(effective_rpm)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-Cognitive-Load-Adjustment"] = f"{effective_rpm / self.base_requests_per_minute:.2f}"

        return response

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis_client:
            await self._redis_client.close()
