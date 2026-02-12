#!/usr/bin/env python3
"""
Security Headers Middleware for FastAPI
Adds comprehensive security headers including CSP, HSTS, CSRF protection, and more.
"""

import hashlib
import hmac
import os
import secrets
import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive security headers middleware for FastAPI applications.

    Adds the following security headers:
    - Content Security Policy (CSP)
    - HTTP Strict Transport Security (HSTS)
    - X-Frame-Options
    - X-Content-Type-Options
    - X-XSS-Protection
    - Referrer-Policy
    - Permissions-Policy
    - Cross-Origin Embedder Policy (COEP)
    - Cross-Origin Opener Policy (COOP)
    - Cross-Origin Resource Policy (CORP)
    """

    def __init__(
        self,
        app,
        csp_directives: dict[str, str] | None = None,
        hsts_max_age: int = 31536000,  # 1 year
        hsts_include_subdomains: bool = True,
        hsts_preload: bool = False,
        frame_options: str = "DENY",
        content_type_options: str = "nosniff",
        xss_protection: str = "1; mode=block",
        referrer_policy: str = "strict-origin-when-cross-origin",
        permissions_policy: dict[str, list[str]] | None = None,
        coep: str = "require-corp",
        coop: str = "same-origin",
        corp: str = "same-origin",
        enable_csrf_protection: bool = True,
        csrf_secret: str | None = None,
        allowed_origins: set[str] | None = None,
    ):
        super().__init__(app)

        # CSP Configuration
        default_csp = {
            "default-src": "'self'",
            "script-src": "'self' 'unsafe-inline' 'unsafe-eval'",
            "style-src": "'self' 'unsafe-inline'",
            "img-src": "'self' data: https:",
            "font-src": "'self' data:",
            "connect-src": "'self'",
            "media-src": "'self'",
            "object-src": "'none'",
            "frame-src": "'none'",
            "base-uri": "'self'",
            "form-action": "'self'",
        }
        self.csp_directives = {**default_csp, **(csp_directives or {})}

        # HSTS Configuration
        hsts_parts = [f"max-age={hsts_max_age}"]
        if hsts_include_subdomains:
            hsts_parts.append("includeSubDomains")
        if hsts_preload:
            hsts_parts.append("preload")
        self.hsts_value = "; ".join(hsts_parts)

        # Other security headers
        self.frame_options = frame_options
        self.content_type_options = content_type_options
        self.xss_protection = xss_protection
        self.referrer_policy = referrer_policy

        # Permissions Policy
        if permissions_policy is None:
            permissions_policy = {
                "camera": [],
                "microphone": [],
                "geolocation": [],
                "gyroscope": [],
                "magnetometer": [],
                "payment": [],
                "usb": [],
            }
        self.permissions_policy = self._build_permissions_policy(permissions_policy)

        # Cross-Origin policies
        self.coep = coep
        self.coop = coop
        self.corp = corp

        # CSRF Protection
        self.enable_csrf_protection = enable_csrf_protection
        self.csrf_secret = csrf_secret or os.getenv("CSRF_SECRET", secrets.token_hex(32))
        self.allowed_origins = allowed_origins or {"http://localhost:3000", "https://localhost:3000"}

        # Session storage for CSRF tokens
        self.csrf_tokens: dict[str, dict[str, float]] = {}

    def _build_permissions_policy(self, policy: dict[str, list[str]]) -> str:
        """Build Permissions-Policy header value"""
        directives = []
        for feature, allowlist in policy.items():
            if allowlist:
                directives.append(f"{feature}=({' '.join(allowlist)})")
            else:
                directives.append(f"{feature}=()")
        return ", ".join(directives)

    def _build_csp_header(self) -> str:
        """Build Content Security Policy header"""
        directives = []
        for directive, value in self.csp_directives.items():
            directives.append(f"{directive} {value}")
        return "; ".join(directives)

    def _generate_csrf_token(self, session_id: str) -> str:
        """Generate a CSRF token for the session"""
        timestamp = str(int(time.time()))
        message = f"{session_id}:{timestamp}"
        signature = hmac.new(self.csrf_secret.encode(), message.encode(), hashlib.sha256).hexdigest()

        token = f"{timestamp}:{signature}"
        return token

    def _validate_csrf_token(self, token: str, session_id: str) -> bool:
        """Validate a CSRF token"""
        try:
            timestamp_str, signature = token.split(":", 1)
            timestamp = int(timestamp_str)

            # Check if token is not too old (5 minutes)
            if time.time() - timestamp > 300:
                return False

            # Validate signature
            expected_message = f"{session_id}:{timestamp_str}"
            expected_signature = hmac.new(
                self.csrf_secret.encode(), expected_message.encode(), hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(signature, expected_signature)

        except (ValueError, TypeError):
            return False

    def _check_cors(self, request: Request) -> bool:
        """Check if request passes CORS validation"""
        origin = request.headers.get("origin")
        if not origin:
            return True  # Allow requests without Origin header

        return origin in self.allowed_origins

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # CSRF Protection for state-changing requests
        if self.enable_csrf_protection and request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            # Check CORS
            if not self._check_cors(request):
                return Response(content="CORS policy violation", status_code=403, media_type="text/plain")

            # Validate CSRF token
            csrf_token = request.headers.get("X-CSRF-Token")
            session_id = request.cookies.get("session_id", "anonymous")

            if not csrf_token or not self._validate_csrf_token(csrf_token, session_id):
                return Response(content="CSRF token validation failed", status_code=403, media_type="text/plain")

        # Process the request
        response = await call_next(request)

        # Add security headers to the response
        self._add_security_headers(response, request)

        return response

    def _add_security_headers(self, response: Response, request: Request) -> None:
        """Add all security headers to the response"""

        # Content Security Policy
        csp_header = self._build_csp_header()
        response.headers["Content-Security-Policy"] = csp_header

        # HTTP Strict Transport Security (only for HTTPS)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = self.hsts_value

        # Frame Options
        response.headers["X-Frame-Options"] = self.frame_options

        # Content Type Options
        response.headers["X-Content-Type-Options"] = self.content_type_options

        # XSS Protection
        response.headers["X-XSS-Protection"] = self.xss_protection

        # Referrer Policy
        response.headers["Referrer-Policy"] = self.referrer_policy

        # Permissions Policy
        response.headers["Permissions-Policy"] = self.permissions_policy

        # Cross-Origin Embedder Policy
        response.headers["Cross-Origin-Embedder-Policy"] = self.coep

        # Cross-Origin Opener Policy
        response.headers["Cross-Origin-Opener-Policy"] = self.coop

        # Cross-Origin Resource Policy
        response.headers["Cross-Origin-Resource-Policy"] = self.corp

        # Additional security headers
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["X-DNS-Prefetch-Control"] = "off"

        # Remove server header for security
        if "server" in response.headers:
            del response.headers["server"]
        if "x-powered-by" in response.headers:
            del response.headers["x-powered-by"]

    def get_csrf_token(self, session_id: str) -> str:
        """Get a CSRF token for a session (for frontend use)"""
        return self._generate_csrf_token(session_id)


# Global security headers middleware instance
def create_security_middleware(**kwargs) -> SecurityHeadersMiddleware:
    """Factory function to create security headers middleware with sensible defaults"""
    return SecurityHeadersMiddleware(
        None,  # app will be set by FastAPI
        **kwargs,
    )


# CSRF token generation utility
def generate_csrf_token(session_id: str, secret: str | None = None) -> str:
    """Generate a CSRF token for frontend use"""
    secret = secret or os.getenv("CSRF_SECRET", secrets.token_hex(32))
    timestamp = str(int(time.time()))
    message = f"{session_id}:{timestamp}"
    signature = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()

    return f"{timestamp}:{signature}"


# Security headers utility
def get_security_headers(request: Request | None = None) -> dict[str, str]:
    """Get all security headers as a dictionary"""
    middleware = create_security_middleware()
    # Create a mock response to get headers
    from starlette.responses import Response

    mock_response = Response()
    mock_request = request or Request(
        scope={
            "type": "http",
            "scheme": "https",
            "path": "/",
            "headers": [],
        }
    )
    middleware._add_security_headers(mock_response, mock_request)

    headers = dict(mock_response.headers)

    # Ensure Referrer-Policy is present
    if "Referrer-Policy" not in headers:
        # Use middleware.referrer_policy if available, else default
        ref_policy = getattr(middleware, "referrer_policy", None) or "strict-origin-when-cross-origin"
        headers["Referrer-Policy"] = ref_policy

    return headers
