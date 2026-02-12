"""
Mothership Cockpit Middleware Package.

Custom middleware components for request processing, authentication,
logging, and security features.

Provides:
- Request ID and correlation tracking
- Timing and performance metrics
- Structured request/response logging
- Security headers enforcement
- Rate limiting (in-memory and Redis-backed)
- Error handling
- Circuit breaker for cascading failure prevention
- Security enforcement with input sanitization
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from contextvars import ContextVar
from datetime import UTC, datetime, timezone
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from ..logging_structured import bind_context, clear_context

logger = logging.getLogger(__name__)

# Context variables for request tracking
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)
correlation_id_ctx: ContextVar[str | None] = ContextVar("correlation_id", default=None)
request_start_time_ctx: ContextVar[float | None] = ContextVar("request_start_time", default=None)


def get_request_id() -> str | None:
    """Get the current request ID from context."""
    return request_id_ctx.get()


def get_correlation_id() -> str | None:
    """Get the current correlation ID from context."""
    return correlation_id_ctx.get()


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(UTC)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to generate and track request IDs.

    Assigns a unique request ID to each request and propagates
    correlation IDs for distributed tracing.
    """

    def __init__(self, app: ASGIApp, header_name: str = "X-Request-ID"):
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Get or generate request ID
        request_id = request.headers.get(self.header_name) or str(uuid.uuid4())
        correlation_id = request.headers.get("X-Correlation-ID") or request_id

        # Set context variables
        request_id_ctx.set(request_id)
        correlation_id_ctx.set(correlation_id)

        # Bind structured logging context
        bind_context(request_id=request_id, correlation_id=correlation_id)

        # Store in request state for easy access
        request.state.request_id = request_id
        request.state.correlation_id = correlation_id

        try:
            # Process request
            response = await call_next(request)

            # Add IDs to response headers
            response.headers[self.header_name] = request_id
            response.headers["X-Correlation-ID"] = correlation_id

            return response
        finally:
            clear_context()


class TimingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track request timing.

    Adds X-Process-Time header with request duration in seconds.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.perf_counter()
        request_start_time_ctx.set(start_time)

        response = await call_next(request)

        process_time = time.perf_counter() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.6f}"
        response.headers["X-Process-Time-Ms"] = f"{process_time * 1000:.2f}"

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for structured request/response logging.

    Logs request details on entry and response details on exit
    with timing information and optional body logging.
    """

    def __init__(
        self,
        app: ASGIApp,
        log_request_body: bool = False,
        log_response_body: bool = False,
        exclude_paths: list[str] | None = None,
    ):
        super().__init__(app)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.exclude_paths = exclude_paths or ["/health", "/ping", "/metrics"]

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip logging for excluded paths
        if any(request.url.path.startswith(p) for p in self.exclude_paths):
            return await call_next(request)

        request_id = get_request_id() or "unknown"
        correlation_id = get_correlation_id()
        start_time = time.perf_counter()

        # Log request
        log_data = {
            "type": "request",
            "request_id": request_id,
            "correlation_id": correlation_id,
            "method": request.method,
            "path": request.url.path,
            "query": str(request.url.query) if request.url.query else None,
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("User-Agent"),
            "has_auth": bool(request.headers.get("Authorization")),
            "has_api_key": bool(request.headers.get("X-API-Key")),
            "timestamp": utc_now().isoformat(),
        }

        if self.log_request_body and request.method in {"POST", "PUT", "PATCH"}:
            try:
                body = await request.body()
                if body:
                    log_data["body_size"] = len(body)
            except Exception:
                pass

        logger.info(f"Incoming request: {json.dumps(log_data)}")

        # Process request
        response = await call_next(request)

        # Log response
        duration = time.perf_counter() - start_time
        response_log = {
            "type": "response",
            "request_id": request_id,
            "correlation_id": correlation_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
            "timestamp": utc_now().isoformat(),
        }

        log_level = logging.INFO
        if response.status_code >= 500:
            log_level = logging.ERROR
        elif response.status_code >= 400:
            log_level = logging.WARNING

        logger.log(log_level, f"Request completed: {json.dumps(response_log)}")

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Industry-grade security headers middleware.
    Hardens the application against common web vulnerabilities.
    """

    def __init__(
        self,
        app: ASGIApp,
        content_security_policy: str | None = None,
        hsts_max_age: int = 31536000,
        custom_headers: dict[str, str] | None = None,
    ):
        super().__init__(app)
        # Industry default CSP if none provided
        self.csp = content_security_policy or (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "font-src 'self'; "
            "object-src 'none'; "
            "media-src 'self'; "
            "frame-src 'none'"
        )
        self.hsts_max_age = hsts_max_age
        self.custom_headers = custom_headers or {}

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Hardened Security Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Privacy: Minimal permissions by default
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), usb=(), interest-cohort=()"

        # Content Security Policy
        response.headers["Content-Security-Policy"] = self.csp

        # HSTS (Strict-Transport-Security) - Industry grade if over HTTPS
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = f"max-age={self.hsts_max_age}; includeSubDomains; preload"

        # Anti-Cache for sensitive paths (optional, but good for security)
        if request.url.path.startswith("/api/v1/admin") or request.url.path.startswith("/api/v1/auth"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Custom headers
        for name, value in self.custom_headers.items():
            response.headers[name] = value

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiting middleware.

    For production, use Redis-backed rate limiting.
    """

    def __init__(
        self,
        app: ASGIApp,
        requests_per_minute: int = 60,
        burst_size: int = 10,
        exclude_paths: list[str] | None = None,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.exclude_paths = exclude_paths or ["/health", "/ping"]
        self._store: dict[str, list[float]] = {}

    def _get_client_key(self, request: Request) -> str:
        """Get identifier for rate limiting (IP or API key)."""
        # Prefer API key if present
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key:{api_key[:16]}"

        # Fall back to IP
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"

    def _is_rate_limited(self, key: str) -> bool:
        """Check if key has exceeded rate limit."""
        now = time.time()
        window = 60.0  # 1 minute window

        # Get request timestamps for this key
        if key not in self._store:
            self._store[key] = []

        # Remove old timestamps
        self._store[key] = [ts for ts in self._store[key] if now - ts < window]

        # Check limit
        if len(self._store[key]) >= self.requests_per_minute:
            return True

        # Record this request
        self._store[key].append(now)
        return False

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(p) for p in self.exclude_paths):
            return await call_next(request)

        client_key = self._get_client_key(request)

        if self._is_rate_limited(client_key):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "success": False,
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Please slow down.",
                    },
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)

        # Add rate limit headers
        remaining = self.requests_per_minute - len(self._store.get(client_key, []))
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))

        return response

    def reset_store(self) -> None:
        """Reset the rate limit store (for testing)."""
        self._store.clear()


# Global rate limiter instance for testing resets
_rate_limiter_instance: RateLimitMiddleware | None = None


def get_rate_limiter() -> RateLimitMiddleware | None:
    """Get the global rate limiter instance."""
    return _rate_limiter_instance


def reset_rate_limiter() -> None:
    """Reset the global rate limiter store (for testing)."""
    global _rate_limiter_instance
    if _rate_limiter_instance is not None:
        _rate_limiter_instance.reset_store()


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for catching unhandled exceptions.

    Ensures all errors return a consistent JSON response format.
    """

    def __init__(self, app: ASGIApp, debug: bool = False):
        super().__init__(app)
        self.debug = debug

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:
            request_id = get_request_id() or "unknown"
            correlation_id = get_correlation_id()
            logger.exception(f"Unhandled exception in request {request_id}: {exc}")

            error_detail = str(exc) if self.debug else "Internal server error"

            response = JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "success": False,
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": error_detail,
                    },
                    "request_id": request_id,
                    "correlation_id": correlation_id,
                    "timestamp": utc_now().isoformat(),
                },
            )
            response.headers["X-Request-ID"] = request_id
            if correlation_id:
                response.headers["X-Correlation-ID"] = correlation_id
            return response


def setup_middleware(app: FastAPI, settings: Any) -> None:
    """
    Configure all middleware for the application.

    Args:
        app: FastAPI application instance
        settings: Application settings
    """
    # Add middleware in reverse order (last added runs first)

    # Error handling (runs first, catches all errors)
    app.add_middleware(
        ErrorHandlingMiddleware,
        debug=getattr(settings, "debug_enabled", False),
    )

    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)

    # Security enforcer (input sanitization, auth verification)
    if getattr(settings, "security", None):
        from .security_enforcer import SecurityEnforcerMiddleware

        app.add_middleware(
            SecurityEnforcerMiddleware,
            strict_mode=getattr(settings.security, "strict_mode", True),
            audit_logging=getattr(settings, "telemetry", None) and settings.telemetry.enabled,
            sanitize_inputs=getattr(settings.security, "input_sanitization_enabled", True),
            enforce_https=settings.is_production if hasattr(settings, "is_production") else False,
            max_body_size=getattr(settings.security, "max_request_size_bytes", 10 * 1024 * 1024),
        )

    # Circuit breaker (cascading failure prevention)
    if getattr(settings, "security", None) and getattr(settings.security, "circuit_breaker_enabled", False):
        from .circuit_breaker import CircuitBreakerMiddleware

        app.add_middleware(
            CircuitBreakerMiddleware,
            failure_threshold=getattr(settings.security, "circuit_breaker_failure_threshold", 5),
            recovery_timeout=getattr(settings.security, "circuit_breaker_recovery_timeout", 30),
            request_timeout=getattr(settings.security, "request_timeout_seconds", 30.0),
        )

    # Request logging
    if getattr(settings, "telemetry", None) and settings.telemetry.enabled:
        app.add_middleware(RequestLoggingMiddleware)

    # Timing
    app.add_middleware(TimingMiddleware)

    # Request ID (runs last, sets up context for others)
    app.add_middleware(RequestIDMiddleware)

    # Request size limiting (deny-by-default security)
    if hasattr(settings, "security"):
        from .request_size import RequestSizeLimitMiddleware

        app.add_middleware(
            RequestSizeLimitMiddleware,
            max_size_bytes=settings.security.max_request_size_bytes,
        )

    # Usage tracking (for billing)
    from .usage_tracking import UsageTrackingMiddleware

    app.add_middleware(UsageTrackingMiddleware)

    # Rate limiting (if enabled)
    if getattr(settings, "security", None) and settings.security.rate_limit_enabled:
        # Use Redis-backed rate limiting if Redis is enabled, otherwise use in-memory
        if getattr(settings, "database", None) and settings.database.redis_enabled:
            from .rate_limit_redis import RedisRateLimitMiddleware

            app.add_middleware(
                RedisRateLimitMiddleware,
                requests_per_minute=settings.security.rate_limit_requests,
                redis_url=settings.database.redis_url,
            )
        else:
            app.add_middleware(
                RateLimitMiddleware,
                requests_per_minute=settings.security.rate_limit_requests,
            )


# Lazy imports for optional middleware
def get_circuit_breaker_middleware():
    """Get CircuitBreakerMiddleware class (lazy import)."""
    from .circuit_breaker import CircuitBreakerMiddleware

    return CircuitBreakerMiddleware


def get_security_enforcer_middleware():
    """Get SecurityEnforcerMiddleware class (lazy import)."""
    from .security_enforcer import SecurityEnforcerMiddleware

    return SecurityEnforcerMiddleware


def get_circuit_manager():
    """Get circuit breaker manager instance."""
    from .circuit_breaker import get_circuit_manager

    return get_circuit_manager()


__all__ = [
    # Context functions
    "get_request_id",
    "get_correlation_id",
    # Middleware classes
    "RequestIDMiddleware",
    "TimingMiddleware",
    "RequestLoggingMiddleware",
    "SecurityHeadersMiddleware",
    "RateLimitMiddleware",
    "ErrorHandlingMiddleware",
    # Lazy middleware getters
    "get_circuit_breaker_middleware",
    "get_security_enforcer_middleware",
    "get_circuit_manager",
    # Setup function
    "setup_middleware",
]
