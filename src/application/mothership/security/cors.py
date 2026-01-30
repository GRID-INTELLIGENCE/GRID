"""
CORS configuration utilities.

Implements secure CORS defaults with explicit origin configuration required.
"""

from __future__ import annotations

from typing import Any


def validate_cors_origins(origins: list[str], environment: str = "production") -> list[str]:
    """
    Validate and sanitize CORS origins.

    Args:
        origins: List of allowed origins
        environment: Deployment environment (production/staging/development)

    Returns:
        Validated list of origins

    Raises:
        ValueError: If invalid configuration detected
    """
    if not origins:
        return []

    # Reject wildcard in production
    if "*" in origins and environment == "production":
        raise ValueError(
            "CORS wildcard (*) is not allowed in production. "
            "Please specify explicit origins in MOTHERSHIP_CORS_ORIGINS."
        )

    # Normalize origins
    validated = []
    for origin in origins:
        origin = origin.strip()
        if origin:
            # Validate origin format (basic check)
            if not (origin.startswith("http://") or origin.startswith("https://") or origin == "*"):
                raise ValueError(f"Invalid CORS origin format: {origin}")
            validated.append(origin)

    return validated


def get_cors_config(
    origins: list[str],
    allow_credentials: bool = False,
    allow_methods: list[str] | None = None,
    allow_headers: list[str] | None = None,
    environment: str = "production",
) -> dict[str, Any]:
    """
    Get CORS middleware configuration with secure defaults.

    Args:
        origins: Allowed CORS origins (empty list = deny all)
        allow_credentials: Allow credentials in CORS requests
        allow_methods: Allowed HTTP methods (None = minimal safe defaults)
        allow_headers: Allowed headers (None = minimal safe defaults)
        environment: Deployment environment

    Returns:
        Dictionary of CORS configuration for CORSMiddleware
    """
    # Validate origins
    validated_origins = validate_cors_origins(origins, environment)

    # Default methods (minimal safe set)
    if allow_methods is None:
        allow_methods = ["GET", "HEAD", "OPTIONS", "POST", "PUT", "DELETE", "PATCH"]

    # Default headers (minimal required set)
    if allow_headers is None:
        allow_headers = [
            "Content-Type",
            "Authorization",
            "X-API-Key",
            "X-Request-ID",
            "X-Correlation-ID",
        ]

    return {
        "allow_origins": validated_origins,
        "allow_credentials": allow_credentials,
        "allow_methods": allow_methods,
        "allow_headers": allow_headers,
        "expose_headers": ["X-Request-ID", "X-Correlation-ID", "X-Process-Time"],
        "max_age": 3600,  # 1 hour preflight cache
    }
