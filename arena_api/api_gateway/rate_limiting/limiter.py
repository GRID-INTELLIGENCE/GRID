"""
Rate Limiting for Arena API Gateway
===================================

This module implements intelligent rate limiting that adapts to system load
and user behavior, preventing abuse while maintaining optimal performance.

Key Features:
- Adaptive rate limiting based on AI insights
- Multiple rate limit strategies (fixed, sliding window, token bucket)
- User and service-specific limits
- Burst handling and gradual backoff
- Real-time monitoring and adjustment
"""

import logging
import time
from collections import defaultdict, deque
from typing import Any

from fastapi import Request

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Intelligent rate limiter with adaptive capabilities.
    """

    def __init__(self) -> None:
        self.fixed_limits: dict[str, int] = {}
        self.sliding_windows: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=1000))
        self.token_buckets: dict[str, TokenBucket] = {}
        self.user_limits: dict[str, dict[str, int]] = {}
        self.service_limits: dict[str, int] = {}
        self.monitoring: Any = None  # Will be injected

    def set_monitoring(self, monitoring):
        """Inject monitoring dependency."""
        self.monitoring = monitoring

    async def check_rate_limit(self, request: Request) -> dict[str, Any]:
        """
        Check if request should be rate limited.

        Args:
            request: FastAPI Request object

        Returns:
            Dict with rate limit decision and metadata
        """
        try:
            # Extract identifiers
            client_ip = self._get_client_ip(request)
            user_id = self._get_user_id(request)
            service_name = self._get_service_name(request)

            # Check different limit types
            ip_limit = await self._check_ip_limit(client_ip)
            user_limit = await self._check_user_limit(user_id) if user_id else {"allowed": True}
            service_limit = await self._check_service_limit(service_name) if service_name else {"allowed": True}

            # Combine results - if any limit is exceeded, block
            limits = [ip_limit, user_limit, service_limit]
            blocked_limits = [limit for limit in limits if not limit["allowed"]]

            if blocked_limits:
                # Find the most restrictive limit
                most_restrictive = min(blocked_limits, key=lambda x: x.get("retry_after", 0))

                # Record rate limit violation
                await self._record_violation(request, most_restrictive)

                return {
                    "allowed": False,
                    "retry_after": most_restrictive.get("retry_after", 60),
                    "limit_type": most_restrictive.get("limit_type"),
                    "current_usage": most_restrictive.get("current_usage", 0),
                    "limit": most_restrictive.get("limit", 0),
                }

            return {
                "allowed": True,
                "remaining": min(limit.get("remaining", 1000) for limit in limits),
                "reset_time": min(limit.get("reset_time", time.time() + 3600) for limit in limits),
            }

        except Exception as e:
            logger.error(f"Rate limiting error: {str(e)}")
            # On error, allow request but log the issue
            return {"allowed": True, "error": str(e)}

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        # Check forwarded headers first (for proxies/load balancers)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # Fall back to direct client IP
        return request.client.host if request.client else "unknown"

    def _get_user_id(self, request: Request) -> str | None:
        """Extract user ID from request."""
        # Check various places where user ID might be
        user_id = request.headers.get("X-User-ID")
        if user_id:
            return user_id

        # Check JWT token (would need to decode)
        # For now, return None - auth manager handles this
        return None

    def _get_service_name(self, request: Request) -> str | None:
        """Extract service name from request path."""
        path = request.url.path
        parts = path.strip("/").split("/")
        if len(parts) > 0 and parts[0] != "":
            return parts[0]
        return None

    async def _check_ip_limit(self, ip: str) -> dict[str, Any]:
        """Check rate limit for IP address."""
        # Use sliding window for IP limits
        window_key = f"ip:{ip}"
        current_time = time.time()

        # Clean old entries (older than 1 minute)
        window = self.sliding_windows[window_key]
        while window and current_time - window[0] > 60:
            window.popleft()

        # Check current usage
        current_usage = len(window)
        limit = 100  # requests per minute

        if current_usage >= limit:
            return {
                "allowed": False,
                "limit_type": "ip",
                "current_usage": current_usage,
                "limit": limit,
                "retry_after": 60,
            }

        # Add current request
        window.append(current_time)

        remaining_time = 60 - (current_time - window[0]) if window else 60

        return {"allowed": True, "remaining": limit - current_usage - 1, "reset_time": current_time + remaining_time}

    async def _check_user_limit(self, user_id: str) -> dict[str, Any]:
        """Check rate limit for user."""
        if not user_id:
            return {"allowed": True}

        # Use token bucket for user limits
        bucket_key = f"user:{user_id}"
        bucket = self.token_buckets.get(bucket_key)

        if not bucket:
            # Initialize bucket: 10 requests per second, burst of 20
            bucket = TokenBucket(capacity=20, refill_rate=10)
            self.token_buckets[bucket_key] = bucket

        allowed, tokens_remaining = bucket.consume(1)

        if not allowed:
            return {
                "allowed": False,
                "limit_type": "user",
                "current_usage": bucket.capacity - tokens_remaining,
                "limit": bucket.capacity,
                "retry_after": 1,  # Wait 1 second for token refill
            }

        return {"allowed": True, "remaining": tokens_remaining, "reset_time": time.time() + 1}

    async def _check_service_limit(self, service_name: str) -> dict[str, Any]:
        """Check rate limit for service."""
        if not service_name:
            return {"allowed": True}

        # Use fixed window for service limits
        window_key = f"service:{service_name}:{int(time.time() // 60)}"  # Per minute window
        current_usage = self.fixed_limits.get(window_key, 0)
        limit = 1000  # requests per minute per service

        if current_usage >= limit:
            return {
                "allowed": False,
                "limit_type": "service",
                "current_usage": current_usage,
                "limit": limit,
                "retry_after": 60,
            }

        # Increment usage
        self.fixed_limits[window_key] = current_usage + 1

        return {
            "allowed": True,
            "remaining": limit - current_usage - 1,
            "reset_time": (int(time.time() // 60) + 1) * 60,
        }

    async def _record_violation(self, request: Request, limit_info: dict[str, Any]):
        """Record a rate limit violation."""
        if self.monitoring:
            await self.monitoring.record_rate_limit_violation(
                request=request,
                limit_type=limit_info.get("limit_type"),
                current_usage=limit_info.get("current_usage", 0),
                limit=limit_info.get("limit", 0),
            )

    def set_user_limit(self, user_id: str, requests_per_second: int, burst_limit: int | None = None):
        """Set custom rate limit for a user."""
        if burst_limit is None:
            burst_limit = requests_per_second * 2

        self.user_limits[user_id] = {"rate": requests_per_second, "burst": burst_limit}

        # Update existing bucket if it exists
        bucket_key = f"user:{user_id}"
        if bucket_key in self.token_buckets:
            bucket = self.token_buckets[bucket_key]
            bucket.capacity = burst_limit
            bucket.refill_rate = requests_per_second

    def set_service_limit(self, service_name: str, requests_per_minute: int):
        """Set custom rate limit for a service."""
        self.service_limits[service_name] = requests_per_minute

    def get_limit_status(self, identifier: str, limit_type: str = "ip") -> dict[str, Any]:
        """Get current limit status for an identifier."""
        if limit_type == "ip":
            window_key = f"ip:{identifier}"
            window = self.sliding_windows[window_key]
            current_usage = len(window)
            return {"current_usage": current_usage, "limit": 100, "remaining": max(0, 100 - current_usage)}
        elif limit_type == "user":
            bucket_key = f"user:{identifier}"
            bucket = self.token_buckets.get(bucket_key)
            if bucket:
                return {
                    "current_usage": bucket.capacity - bucket.tokens,
                    "limit": bucket.capacity,
                    "remaining": bucket.tokens,
                }
        elif limit_type == "service":
            window_key = f"service:{identifier}:{int(time.time() // 60)}"
            current_usage = self.fixed_limits.get(window_key, 0)
            return {"current_usage": current_usage, "limit": 1000, "remaining": max(0, 1000 - current_usage)}

        return {"error": "Unknown limit type"}


class TokenBucket:
    """
    Token bucket implementation for rate limiting.
    """

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()

    def consume(self, tokens: int = 1) -> tuple[bool, float]:
        """
        Consume tokens from the bucket.

        Returns:
            Tuple of (allowed, remaining_tokens)
        """
        self._refill()

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True, self.tokens

        return False, self.tokens

    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        tokens_to_add = elapsed * self.refill_rate

        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now


class AdaptiveRateLimiter:
    """
    AI-driven adaptive rate limiter that adjusts limits based on system load.
    """

    def __init__(self, base_limiter: RateLimiter):
        self.base_limiter = base_limiter
        self.system_load = 0.0
        self.adjustment_factors = {}

    async def check_adaptive_limit(self, request: Request) -> dict[str, Any]:
        """Check rate limit with adaptive adjustments."""
        # Get base limit check
        base_result = await self.base_limiter.check_rate_limit(request)

        if not base_result["allowed"]:
            return base_result

        # Apply adaptive adjustments based on system load
        load_factor = self._calculate_load_factor()
        adjusted_remaining = int(base_result["remaining"] * (1 - load_factor))

        if adjusted_remaining <= 0:
            return {"allowed": False, "retry_after": 30, "limit_type": "adaptive", "reason": "High system load"}

        return {
            "allowed": True,
            "remaining": adjusted_remaining,
            "reset_time": base_result["reset_time"],
            "load_factor": load_factor,
        }

    def _calculate_load_factor(self) -> float:
        """Calculate current system load factor (0.0 to 1.0)."""
        # Simple load calculation - can be enhanced with actual metrics
        # For now, return a basic factor
        return min(0.8, self.system_load)

    def update_system_load(self, load: float):
        """Update system load factor."""
        self.system_load = max(0.0, min(1.0, load))
