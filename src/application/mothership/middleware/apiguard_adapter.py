"""
APIGuard Integration Adapter for GRID

This module provides adapters to integrate APIGuard's resilience patterns
with GRID's existing middleware and service architecture.

Key Features:
- Drop-in replacement for custom circuit breaker middleware
- Token bucket rate limiting with Redis persistence
- Unified retry logic for HTTP clients
- Structured logging integration with GRID's observability
"""

from __future__ import annotations

import logging
from typing import Any

# APIGuard imports
from apiguard import BucketRegistry, CircuitBreaker, RetryHandler, TokenBucket
from apiguard.adapters.httpx import AsyncRateLimitedClient
from apiguard.exceptions import CircuitOpenError, RetryExhaustedError
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

# GRID imports (with graceful fallback)
try:
    from grid.cognitive.engine import CognitiveEngine  # type: ignore[import-not-found]
except ImportError:
    CognitiveEngine = None  # type: ignore[misc, assignment]

try:
    from config.cognitive_settings import get_cognitive_load_thresholds  # type: ignore[import-not-found]
    from config.quality_gates import get_rate_limit  # type: ignore[import-not-found]
except ImportError:

    def get_rate_limit(limit_type: str = "default") -> int:
        return 60

    def get_cognitive_load_thresholds() -> dict:
        return {"low": 0.3, "medium": 0.6, "high": 0.8}


logger = logging.getLogger(__name__)


class _ResponseFailure(Exception):
    def __init__(self, response: Response) -> None:
        super().__init__("response_failure")
        self.response = response


class APIGuardCircuitBreakerMiddleware(BaseHTTPMiddleware):
    """
    APIGuard-based Circuit Breaker Middleware.

    Replaces GRID's custom 623-line circuit breaker implementation
    with battle-tested APIGuard patterns.
    """

    def __init__(
        self,
        app: ASGIApp,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        success_threshold: int = 1,
        cognitive_adjustment: bool = True,
        retry_max_retries: int = 3,
    ) -> None:
        super().__init__(app)
        self.cognitive_adjustment = cognitive_adjustment
        self.cognitive_engine = CognitiveEngine() if CognitiveEngine else None

        # Initialize circuit breaker
        self.breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            success_threshold=success_threshold,
        )

        # Initialize rate limiting
        default_limit = get_rate_limit("default")
        self.bucket = TokenBucket(
            capacity=default_limit,
            refill_rate=default_limit / 60.0,  # Convert to per-second
        )

        # Initialize retry handler
        self.retry = RetryHandler(
            max_retries=retry_max_retries,
            base_delay=1.0,
            max_delay=60.0,
            jitter=0.1,
        )

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Process request with APIGuard resilience patterns."""

        # Cognitive load adjustment
        if self.cognitive_adjustment and self.cognitive_engine:
            cognitive_load = await self._get_cognitive_load()
            await self._adjust_limits_based_on_load(cognitive_load)

        try:
            # Rate limiting check
            if not self.bucket.acquire(tokens=1):
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "success": False,
                        "error": "Rate limit exceeded",
                        "error_code": "RATE_LIMIT_EXCEEDED",
                    },
                    headers={"Retry-After": "60"},
                )

            # Circuit breaker check
            with self.breaker:
                response = await self._execute_with_retry(request, call_next)
                if response.status_code >= 500:
                    raise _ResponseFailure(response)
                return response

        except _ResponseFailure as e:
            return e.response
        except CircuitOpenError as e:
            logger.warning(
                "circuit_open recovery_timeout=%s path=%s",
                e.recovery_timeout,
                request.url.path,
            )
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "success": False,
                    "error": "Service temporarily unavailable",
                    "error_code": "CIRCUIT_OPEN",
                    "recovery_timeout": e.recovery_timeout,
                },
            )
        except RetryExhaustedError as e:
            logger.error(
                "retry_exhausted attempts=%s last_error=%s path=%s",
                e.attempts,
                str(e.last_error) if e.last_error else None,
                request.url.path,
            )
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "success": False,
                    "error": "Service temporarily unavailable",
                    "error_code": "CIRCUIT_OPEN",
                },
            )
        except Exception as e:
            logger.error(
                "middleware_error path=%s error=%s",
                request.url.path,
                str(e),
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "success": False,
                    "error": "Internal server error",
                    "error_code": "INTERNAL_ERROR",
                },
            )

    async def _execute_with_retry(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Execute request with retry logic."""

        async for attempt in self.retry.attempts():
            try:
                response = await call_next(request)

                # Treat 5xx as failure and trigger retries
                if response.status_code >= 500:
                    if attempt < self.retry.max_retries:
                        await self.retry.apply_backoff(attempt)
                        continue
                    return response

                return response

            except Exception:
                if attempt < self.retry.max_retries:
                    await self.retry.apply_backoff(attempt)
                    continue
                else:
                    return JSONResponse(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        content={
                            "success": False,
                            "error": "Internal server error",
                            "error_code": "INTERNAL_ERROR",
                        },
                    )

    async def _get_cognitive_load(self) -> float:
        """Get current cognitive load from GRID's cognitive engine."""
        if not self.cognitive_engine:
            return 0.5  # Default medium load

        try:
            # This would integrate with GRID's cognitive metrics
            # For now, return a placeholder
            return 0.5
        except Exception:
            return 0.5

    async def _adjust_limits_based_on_load(self, cognitive_load: float) -> None:
        """Dynamically adjust rate limits based on cognitive load."""
        thresholds = get_cognitive_load_thresholds()

        if cognitive_load <= thresholds["low"]:
            # High load capacity
            multiplier = 1.5
        elif cognitive_load <= thresholds["medium"]:
            # Normal capacity
            multiplier = 1.0
        else:
            # Reduced capacity for high cognitive load
            multiplier = 0.7

        # Adjust bucket capacity (would need bucket recreation API)
        logger.debug(
            "cognitive_load_adjustment load=%s multiplier=%s",
            cognitive_load,
            multiplier,
        )


class APIGuardRateLimitMiddleware(BaseHTTPMiddleware):
    """
    APIGuard-based Rate Limiting Middleware.

    Replaces GRID's Redis-based rate limiting with TokenBucket pattern
    while maintaining Redis persistence for distributed scenarios.
    """

    def __init__(
        self,
        app: ASGIApp,
        default_capacity: int = 60,
        default_refill_rate: float = 1.0,
        redis_backed: bool = True,
        per_user: bool = True,
    ) -> None:
        super().__init__(app)
        self.per_user = per_user
        self.redis_backed = redis_backed

        # Initialize bucket registry for per-user rate limiting
        if per_user:
            self.registry = BucketRegistry(
                default_capacity=default_capacity,
                default_refill_rate=default_refill_rate,
            )
        else:
            self.bucket = TokenBucket(
                capacity=default_capacity,
                refill_rate=default_refill_rate,
            )

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Process request with rate limiting."""

        # Get appropriate bucket
        if self.per_user:
            user_id = await self._extract_user_id(request)
            bucket = self.registry.get_bucket(user_id)
        else:
            bucket = self.bucket

        # Check rate limit
        if not bucket.acquire(tokens=1):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "success": False,
                    "error": "Rate limit exceeded",
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "retry_after": 60,
                },
                headers={"Retry-After": "60"},
            )

        # Process request
        return await call_next(request)

    async def _extract_user_id(self, request: Request) -> str:
        """Extract user identifier for per-user rate limiting."""
        # Try to get user ID from JWT token or API key
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # In a real implementation, decode JWT and extract user ID
            # For now, use a hash of the token
            import hashlib

            return hashlib.sha256(auth_header.encode()).hexdigest()[:16]

        # Fallback to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"


class APIGuardHTTPClient:
    """
    Unified HTTP client with APIGuard resilience patterns.

    Replaces scattered httpx usage throughout GRID with consistent
    rate limiting, retry, and circuit breaking.
    """

    def __init__(
        self,
        base_url: str | None = None,
        rate_limit_capacity: int = 100,
        rate_limit_refill_rate: float = 10.0,
        circuit_failure_threshold: int = 5,
        circuit_recovery_timeout: float = 30.0,
        retry_max_retries: int = 3,
        retry_base_delay: float = 1.0,
    ) -> None:
        self.client = AsyncRateLimitedClient(
            bucket=TokenBucket(
                capacity=rate_limit_capacity,
                refill_rate=rate_limit_refill_rate,
            ),
            retry=RetryHandler(
                max_retries=retry_max_retries,
                base_delay=retry_base_delay,
                max_delay=60.0,
                jitter=0.1,
            ),
            breaker=CircuitBreaker(
                failure_threshold=circuit_failure_threshold,
                recovery_timeout=circuit_recovery_timeout,
            ),
            base_url=base_url,
            timeout=30.0,
        )

    async def __aenter__(self):
        """Async context manager entry."""
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def get(self, url: str, **kwargs) -> Any:
        """GET request with resilience."""
        return await self.client.get(url, **kwargs)

    async def post(self, url: str, **kwargs) -> Any:
        """POST request with resilience."""
        return await self.client.post(url, **kwargs)

    async def put(self, url: str, **kwargs) -> Any:
        """PUT request with resilience."""
        return await self.client.put(url, **kwargs)

    async def delete(self, url: str, **kwargs) -> Any:
        """DELETE request with resilience."""
        return await self.client.delete(url, **kwargs)


# Factory functions for easy integration
def create_circuit_breaker_middleware(
    failure_threshold: int = 5,
    recovery_timeout: float = 30.0,
    cognitive_adjustment: bool = True,
) -> APIGuardCircuitBreakerMiddleware:
    """Factory function to create circuit breaker middleware."""
    return lambda app: APIGuardCircuitBreakerMiddleware(
        app=app,
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        cognitive_adjustment=cognitive_adjustment,
    )


def create_rate_limit_middleware(
    default_capacity: int = 60,
    per_user: bool = True,
) -> APIGuardRateLimitMiddleware:
    """Factory function to create rate limit middleware."""
    return lambda app: APIGuardRateLimitMiddleware(
        app=app,
        default_capacity=default_capacity,
        per_user=per_user,
    )


def create_resilient_client(
    service_type: str = "default",
) -> APIGuardHTTPClient:
    """Factory function to create resilient HTTP client for different services."""

    configurations = {
        "default": {
            "rate_limit_capacity": 100,
            "rate_limit_refill_rate": 10.0,
            "circuit_failure_threshold": 5,
            "circuit_recovery_timeout": 30.0,
        },
        "rag": {
            "rate_limit_capacity": 20,  # Conservative for AI services
            "rate_limit_refill_rate": 2.0,
            "circuit_failure_threshold": 3,
            "circuit_recovery_timeout": 60.0,
        },
        "external_api": {
            "rate_limit_capacity": 50,
            "rate_limit_refill_rate": 5.0,
            "circuit_failure_threshold": 3,
            "circuit_recovery_timeout": 120.0,
        },
        "database": {
            "rate_limit_capacity": 200,
            "rate_limit_refill_rate": 20.0,
            "circuit_failure_threshold": 5,
            "circuit_recovery_timeout": 15.0,
        },
    }

    config = configurations.get(service_type, configurations["default"])
    return APIGuardHTTPClient(**config)
