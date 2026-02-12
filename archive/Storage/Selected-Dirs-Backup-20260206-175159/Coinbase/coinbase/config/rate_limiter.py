"""
Rate Limiting Module for External APIs
======================================
Configurable rate limiting for CoinGecko, Binance, and Yahoo Finance APIs.

Usage:
    from coinbase.config.rate_limiter import RateLimiter, RateLimitConfig

    # Configure rate limits
    config = RateLimitConfig(
        requests_per_minute=100,
        burst_size=10
    )

    limiter = RateLimiter(config)

    # Check if request is allowed
    if limiter.allow_request('coingecko'):
        # Make API call
        pass
"""

import logging
import time
from collections import deque
from dataclasses import dataclass
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    requests_per_minute: int = 100
    burst_size: int = 10
    window_seconds: int = 60
    retry_after_header: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.requests_per_minute, int) or self.requests_per_minute < 1:
            raise ValueError("requests_per_minute must be a positive integer")
        if not isinstance(self.burst_size, int) or self.burst_size < 1:
            raise ValueError("burst_size must be a positive integer")
        if not isinstance(self.window_seconds, int) or self.window_seconds < 1:
            raise ValueError("window_seconds must be a positive integer")
        if self.requests_per_minute > 100000:
            raise ValueError("requests_per_minute exceeds maximum allowed (100000)")
        if self.burst_size > 10000:
            raise ValueError("burst_size exceeds maximum allowed (10000)")


@dataclass
class RateLimitStatus:
    """Current rate limit status."""

    allowed: bool
    remaining: int
    reset_time: float
    retry_after: int | None = None


class TokenBucket:
    """
    Token bucket algorithm for rate limiting.

    Allows burst traffic up to burst_size, then enforces steady rate.
    """

    def __init__(self, rate: float, burst_size: int):
        """
        Initialize token bucket.

        Args:
            rate: Tokens per second
            burst_size: Maximum bucket size
        """
        self.rate = rate
        self.burst_size = burst_size
        self.tokens = burst_size
        self.last_update = time.time()
        self._lock = Lock()

    def consume(self, tokens: int = 1) -> tuple[bool, float]:
        """
        Try to consume tokens from bucket.

        Args:
            tokens: Number of tokens to consume

        Returns:
            Tuple of (success, wait_time)
        """
        with self._lock:
            now = time.time()
            elapsed = now - self.last_update

            # Add tokens based on elapsed time
            self.tokens = min(self.burst_size, self.tokens + int(elapsed * self.rate))
            self.last_update = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True, 0.0

            # Calculate wait time
            wait_time = (tokens - self.tokens) / self.rate
            return False, wait_time

    def get_status(self) -> tuple[int, float]:
        """Get current token count and reset time."""
        with self._lock:
            now = time.time()
            elapsed = now - self.last_update
            tokens = min(self.burst_size, self.tokens + elapsed * self.rate)

            if tokens < self.burst_size:
                reset_time = now + (self.burst_size - tokens) / self.rate
            else:
                reset_time = now

            return int(tokens), reset_time


class SlidingWindow:
    """
    Sliding window rate limiting algorithm.

    Tracks requests in a time window and enforces limits.
    """

    def __init__(self, max_requests: int, window_seconds: int):
        """
        Initialize sliding window.

        Args:
            max_requests: Maximum requests allowed in window
            window_seconds: Window size in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: deque = deque()
        self._lock = Lock()

    def allow_request(self) -> tuple[bool, int, float]:
        """
        Check if request is allowed.

        Returns:
            Tuple of (allowed, remaining, reset_time)
        """
        with self._lock:
            now = time.time()
            cutoff = now - self.window_seconds

            # Remove old requests
            while self.requests and self.requests[0] < cutoff:
                self.requests.popleft()

            # Check if request is allowed
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                remaining = self.max_requests - len(self.requests)
                reset_time = now + self.window_seconds if self.requests else now
                return True, remaining, reset_time

            # Request denied
            remaining = 0
            reset_time = self.requests[0] + self.window_seconds
            return False, remaining, reset_time

    def get_status(self) -> tuple[int, float]:
        """Get current request count and reset time."""
        with self._lock:
            now = time.time()
            cutoff = now - self.window_seconds

            # Remove old requests
            while self.requests and self.requests[0] < cutoff:
                self.requests.popleft()

            remaining = self.max_requests - len(self.requests)
            reset_time = self.requests[0] + self.window_seconds if self.requests else now

            return remaining, reset_time


class RateLimiter:
    """
    Rate limiter for external APIs.

    Supports multiple APIs with different rate limits.
    """

    # Default rate limits for different APIs
    DEFAULT_LIMITS: dict[str, RateLimitConfig] = {
        "coingecko": RateLimitConfig(
            requests_per_minute=30, burst_size=5  # Free tier: 30 calls/minute
        ),
        "binance": RateLimitConfig(
            requests_per_minute=1200, burst_size=20  # 1200 weight per minute
        ),
        "yahoo_finance": RateLimitConfig(requests_per_minute=100, burst_size=10),
    }

    def __init__(self, configs: dict[str, RateLimitConfig] | None = None):
        """
        Initialize rate limiter.

        Args:
            configs: Optional custom rate limit configurations
        """
        self.configs = configs or self.DEFAULT_LIMITS.copy()
        self._buckets: dict[str, TokenBucket] = {}
        self._windows: dict[str, SlidingWindow] = {}
        self._lock = Lock()

        # Initialize rate limiters
        self._init_limiters()

    def _init_limiters(self) -> None:
        """Initialize rate limiters for each API."""
        for api_name, config in self.configs.items():
            rate = config.requests_per_minute / 60.0
            self._buckets[api_name] = TokenBucket(rate, config.burst_size)
            self._windows[api_name] = SlidingWindow(
                config.requests_per_minute, config.window_seconds
            )

    def allow_request(self, api_name: str, tokens: int = 1) -> RateLimitStatus:
        """
        Check if request is allowed for given API.

        Args:
            api_name: Name of the API (coingecko, binance, yahoo_finance)
            tokens: Number of tokens to consume (for weighted APIs)

        Returns:
            RateLimitStatus with allow/deny decision
        """
        if api_name not in self._buckets:
            logger.warning(f"Unknown API: {api_name}, allowing request")
            return RateLimitStatus(allowed=True, remaining=100, reset_time=time.time())

        # Check both token bucket and sliding window
        bucket = self._buckets[api_name]
        window = self._windows[api_name]

        bucket_allowed, wait_time = bucket.consume(tokens)
        window_allowed, remaining, reset_time = window.allow_request()

        if bucket_allowed and window_allowed:
            return RateLimitStatus(allowed=True, remaining=remaining, reset_time=reset_time)

        # Request denied
        retry_after = int(max(wait_time, reset_time - time.time())) + 1
        return RateLimitStatus(
            allowed=False, remaining=0, reset_time=reset_time, retry_after=retry_after
        )

    def get_status(self, api_name: str) -> RateLimitStatus:
        """
        Get current rate limit status for API.

        Args:
            api_name: Name of the API

        Returns:
            Current rate limit status
        """
        if api_name not in self._buckets:
            return RateLimitStatus(allowed=True, remaining=100, reset_time=time.time())

        bucket = self._buckets[api_name]
        window = self._windows[api_name]

        bucket_tokens, _ = bucket.get_status()
        window_remaining, reset_time = window.get_status()

        remaining = min(bucket_tokens, window_remaining)

        return RateLimitStatus(allowed=remaining > 0, remaining=remaining, reset_time=reset_time)

    def wait_if_needed(self, api_name: str, timeout: float | None = None) -> bool:
        """
        Wait until request is allowed.

        Args:
            api_name: Name of the API
            timeout: Maximum time to wait (seconds)

        Returns:
            True if request allowed, False if timeout
        """
        start_time = time.time()

        while True:
            status = self.allow_request(api_name)
            if status.allowed:
                return True

            if timeout and time.time() - start_time > timeout:
                return False

            wait_time = min(status.retry_after or 1, 1.0)
            time.sleep(wait_time)

    def update_config(self, api_name: str, config: RateLimitConfig) -> None:
        """
        Update rate limit configuration for API.

        Args:
            api_name: Name of the API
            config: New rate limit configuration
        """
        with self._lock:
            self.configs[api_name] = config
            rate = config.requests_per_minute / 60.0
            self._buckets[api_name] = TokenBucket(rate, config.burst_size)
            self._windows[api_name] = SlidingWindow(
                config.requests_per_minute, config.window_seconds
            )


# Global rate limiter instance
_global_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance."""
    global _global_limiter
    if _global_limiter is None:
        _global_limiter = RateLimiter()
    return _global_limiter


def configure_rate_limiter(configs: dict[str, RateLimitConfig]) -> RateLimiter:
    """
    Configure global rate limiter with custom settings.

    Args:
        configs: Rate limit configurations for each API

    Returns:
        Configured RateLimiter instance
    """
    global _global_limiter
    _global_limiter = RateLimiter(configs)
    return _global_limiter


# Convenience functions
def check_rate_limit(api_name: str) -> bool:
    """Quick check if API request is allowed."""
    limiter = get_rate_limiter()
    status = limiter.allow_request(api_name)
    return status.allowed


def get_rate_limit_status(api_name: str) -> RateLimitStatus:
    """Get rate limit status for API."""
    limiter = get_rate_limiter()
    return limiter.get_status(api_name)
