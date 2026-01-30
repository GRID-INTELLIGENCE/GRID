"""
Security headers middleware for FastAPI.
Provides industry-standard security headers to harden the application.
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to every response.

    Headers included:
    - X-Content-Type-Options: Prevents MIME type sniffing.
    - X-Frame-Options: Prevents clickjacking.
    - X-XSS-Protection: Enables browser XSS filtering.
    - Content-Security-Policy: Restricts where resources can be loaded from.
    - Strict-Transport-Security: Forces HTTPS (if enabled).
    - Referrer-Policy: Controls how much referrer information is sent.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Enables browser XSS filtering
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy (Restrictive default)
        # Note: In production, this should be tuned per-app requirements
        response.headers["Content-Security-Policy"] = (
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

        # HSTS (Strict-Transport-Security)
        # Only add if request is over HTTPS or we are in production
        # In development, it can be annoying if not using HTTPS
        # We check the environment through settings normally,
        # but here we can check the request scheme or assume the SSL termination handles it.
        # For hardening, we'll add it with a moderate max-age.
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Permissions Policy (formerly Feature-Policy)
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), usb=(), interest-cohort=()"

        return response
