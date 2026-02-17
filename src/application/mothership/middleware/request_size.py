"""
Request size limiting middleware.

Enforces maximum request body size to prevent DoS attacks.
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce maximum request body size.

    Prevents denial-of-service attacks via large request bodies.
    """

    def __init__(
        self,
        app: ASGIApp,
        max_size_bytes: int = 10 * 1024 * 1024,  # 10MB default
        exclude_paths: list[str] | None = None,
    ):
        """
        Initialize request size limit middleware.

        Args:
            app: ASGI application
            max_size_bytes: Maximum request body size in bytes
            exclude_paths: Paths to exclude from size limiting
        """
        super().__init__(app)
        self.max_size_bytes = max_size_bytes
        self.exclude_paths = exclude_paths or ["/health", "/ping", "/metrics"]

    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        """Process request with size limit enforcement."""
        # Skip size limiting for excluded paths
        if any(request.url.path.startswith(p) for p in self.exclude_paths):
            return await call_next(request)

        # Check Content-Length header if present
        content_length = request.headers.get("Content-Length")
        if content_length:
            try:
                size = int(content_length)
                if size > self.max_size_bytes:
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={
                            "success": False,
                            "error": {
                                "code": "REQUEST_TOO_LARGE",
                                "message": f"Request body exceeds maximum size of {self.max_size_bytes} bytes",
                            },
                        },
                    )
            except ValueError:
                # Invalid Content-Length header, continue (will fail later if needed)
                pass

        # Process request (streaming bodies are handled by FastAPI/Starlette)
        return await call_next(request)
