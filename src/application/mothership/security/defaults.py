"""
Security defaults and constants.

Defines deny-by-default security posture with explicit configuration
required for production deployments.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SecurityDefaults:
    """
    Security default values following deny-by-default principle.

    Production deployments MUST explicitly configure:
    - CORS origins (empty list by default, must be explicit)
    - Secret key (empty string by default, MUST be set)
    - Authentication method (required in production)
    """

    # CORS: deny by default, require explicit configuration
    cors_origins: list[str] | None = None  # None means empty list (deny all)
    cors_allow_credentials: bool = False
    cors_allow_methods: list[str] | None = None  # None means ["GET", "HEAD", "OPTIONS"]
    cors_allow_headers: list[str] | None = None  # None means minimal required headers

    # Authentication: required in production by default
    require_authentication: bool = True

    # Request limits
    max_request_size_bytes: int = 10 * 1024 * 1024  # 10MB default
    max_upload_size_bytes: int = 50 * 1024 * 1024  # 50MB default

    # Security headers
    content_security_policy: str = "default-src 'self'"
    strict_transport_security: bool = True
    hsts_max_age_seconds: int = 31536000  # 1 year

    def __post_init__(self) -> None:
        """Set defaults for None values."""
        if self.cors_origins is None:
            self.cors_origins = []
        if self.cors_allow_methods is None:
            self.cors_allow_methods = ["GET", "HEAD", "OPTIONS"]
        if self.cors_allow_headers is None:
            self.cors_allow_headers = [
                "Content-Type",
                "Authorization",
                "X-API-Key",
                "X-Request-ID",
            ]


def get_security_defaults() -> SecurityDefaults:
    """
    Get security defaults with deny-by-default posture.

    Returns:
        SecurityDefaults instance with secure defaults
    """
    return SecurityDefaults()
