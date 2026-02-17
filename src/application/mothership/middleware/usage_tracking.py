"""
Usage tracking middleware.

Tracks API usage for billing and analytics.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Note: get_api_key would be imported if needed, but we get user_id from request.state
from ..services.billing import UsageMeter

logger = logging.getLogger(__name__)


class UsageTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track API usage for billing.

    Records usage for each API call to track consumption
    and enforce tier limits.
    """

    def __init__(
        self,
        app: ASGIApp,
        exclude_paths: list[str] | None = None,
    ):
        """
        Initialize usage tracking middleware.

        Args:
            app: ASGI application
            exclude_paths: Paths to exclude from tracking
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/ping",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/metrics",
        ]
        self.usage_meter = UsageMeter()

    def _should_track(self, path: str) -> bool:
        """Check if a path should be tracked."""
        return not any(path.startswith(excluded) for excluded in self.exclude_paths)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """
        Process request and track usage.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response
        """
        # Skip tracking for excluded paths
        if not self._should_track(request.url.path):
            return await call_next(request)

        # Get user context from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        api_key_id = getattr(request.state, "api_key_id", None)

        # Only track authenticated requests
        if not user_id:
            return await call_next(request)

        # Process request
        response = await call_next(request)

        # Track usage only for successful requests
        if response.status_code < 400:
            try:
                await self.usage_meter.record_usage(
                    user_id=user_id,
                    endpoint=request.url.path,
                    api_key_id=api_key_id,
                    metadata={
                        "method": request.method,
                        "status_code": response.status_code,
                    },
                )
            except Exception as e:
                # Don't fail the request if usage tracking fails
                logger.error(f"Usage tracking failed: {e}", exc_info=True)

        return response
