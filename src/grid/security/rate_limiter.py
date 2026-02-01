import logging
import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.application.mothership.config import MothershipSettings
from src.grid.infrastructure.cache import CacheFactory

logger = logging.getLogger(__name__)

settings = MothershipSettings.from_env()


class RateLimiter:
    """
    Rate limiter using Token Bucket or Fixed Window algorithm via CacheInterface.
    """

    def __init__(self):
        self.cache = CacheFactory.create(settings.cache.backend)
        self.enabled = settings.security.rate_limit_enabled
        self.limit = settings.security.rate_limit_requests
        self.window = settings.security.rate_limit_window_seconds

    async def check_limit(self, key: str) -> bool:
        """
        Check if key has exceeded limit.
        Returns True if allowed, False if limited.
        """
        if not self.enabled:
            return True

        current_time = int(time.time())
        window_start = current_time // self.window
        cache_key = f"ratelimit:{key}:{window_start}"

        # Simple Fixed Window Counter
        # Note: This is an async operation on cache
        current_count = await self.cache.get(cache_key)

        if current_count is None:
            await self.cache.set(cache_key, 1, ttl=self.window)
            return True

        if int(current_count) < self.limit:
            # Increment.
            # Note: Race condition exists without atomic INCR, but acceptable for soft limits.
            # If backend supports atomic incr, use that. MemoryCache doesn't yet.
            await self.cache.set(cache_key, int(current_count) + 1, ttl=self.window)
            return True

        return False


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, exclude_paths: list[str] = None):
        super().__init__(app)
        self.limiter = RateLimiter()
        self.exclude_paths = exclude_paths or ["/docs", "/openapi.json", "/health", "/metrics"]

    async def dispatch(self, request: Request, call_next):
        if any(request.url.path.startswith(p) for p in self.exclude_paths):
            return await call_next(request)

        # Identify client (IP or User ID)
        client_id = request.client.host if request.client else "unknown"
        if hasattr(request.state, "user"):
            client_id = request.state.user.get("sub", client_id)

        allowed = await self.limiter.check_limit(client_id)
        if not allowed:
            return Response(status_code=429, content="Too Many Requests")

        return await call_next(request)
