"""
Authentication and authorization utilities.

Implements deny-by-default authentication with explicit development mode opt-in.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from fastapi import HTTPException, status

from ..config import get_settings
from .jwt import get_jwt_manager

logger = logging.getLogger(__name__)


class SecurityException(HTTPException):
    """Base exception for security-related errors."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        code: str = "SECURITY_ERROR",
        headers: dict[str, str] | None = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.code = code


class AuthenticationError(SecurityException):
    """Raised when authentication fails."""

    def __init__(self, detail: str = "Authentication required"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            code="AUTHENTICATION_REQUIRED",
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(SecurityException):
    """Raised when authorization fails."""

    def __init__(self, detail: str = "Permission denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            code="AUTHORIZATION_DENIED",
        )


from .rbac import Role, get_permissions_for_role


def verify_api_key(api_key: str | None, require_valid: bool = True) -> dict[str, Any]:
    """
    Verify API key authentication with strict validation and RBAC integration.
    """
    settings = get_settings()

    if not api_key:
        if require_valid:
            raise AuthenticationError("API key required")
        return {
            "authenticated": False,
            "method": "none",
            "user_id": None,
            "role": Role.ANONYMOUS.value,
            "permissions": get_permissions_for_role(Role.ANONYMOUS),
        }

    # Load valid API keys from environment or secret manager
    # Expected format: key1:role1,key2:role2
    api_key_config = os.getenv("MOTHERSHIP_API_KEYS", "")
    valid_keys: dict[str, str] = {}

    if api_key_config:
        for entry in api_key_config.split(","):
            if ":" in entry:
                k, r = entry.split(":", 1)
                valid_keys[k.strip()] = r.strip()
            else:
                valid_keys[entry.strip()] = Role.SERVICE_ACCOUNT.value

    # Legacy fallback for backward compatibility
    legacy_keys = os.getenv("MOTHERSHIP_VALID_API_KEYS", "").split(",")
    for k in legacy_keys:
        k = k.strip()
        if k and k not in valid_keys:
            valid_keys[k] = Role.SERVICE_ACCOUNT.value

    if api_key in valid_keys:
        role_name = valid_keys[api_key]
        try:
            role = Role(role_name.lower())
        except ValueError:
            role = Role.SERVICE_ACCOUNT

        return {
            "authenticated": True,
            "method": "api_key",
            "user_id": f"api_key_{api_key[:8]}",
            "role": role.value,
            "permissions": get_permissions_for_role(role),
        }

    # Development mode hardening
    if settings.is_development:
        # In development, we allow a specific 'dev-key' if no keys are configured
        # but we reject arbitrary non-empty strings to discourage bad habits
        if not valid_keys and api_key == "dev-key-provisioned-for-local-use":
            return {
                "authenticated": True,
                "method": "api_key_dev",
                "user_id": "dev_admin",
                "role": Role.ADMIN.value,
                "permissions": get_permissions_for_role(Role.ADMIN),
            }

    raise AuthenticationError("Invalid or unauthorized API key")


def verify_jwt_token(token: str | None, require_valid: bool = True) -> dict[str, Any]:
    """
    Verify JWT Bearer token authentication using implementation from jwt.py.
    """
    if not token:
        if require_valid:
            raise AuthenticationError("JWT token required")
        return {
            "authenticated": False,
            "method": "none",
            "user_id": None,
            "role": Role.ANONYMOUS.value,
            "permissions": get_permissions_for_role(Role.ANONYMOUS),
        }

    settings = get_settings()
    jwt_manager = get_jwt_manager(
        secret_key=settings.security.secret_key,
        algorithm=settings.security.algorithm,
        environment=settings.environment.value,
    )

    try:
        # Strict validation
        payload = jwt_manager.verify_token(token, expected_type="access")

        # Map scope 'role' or similar to RBAC Role
        if hasattr(payload, "role"):
            role_name = payload.role
        elif payload.metadata and "role" in payload.metadata:
            role_name = payload.metadata["role"]
        else:
            role_name = Role.READER.value
        try:
            role = Role(role_name.lower())
        except (ValueError, AttributeError):
            role = Role.READER

        return {
            "authenticated": True,
            "method": "bearer",
            "user_id": payload.user_id if hasattr(payload, "user_id") else payload.sub,
            "role": role.value,
            "permissions": get_permissions_for_role(role),
            "token_payload": payload.model_dump() if hasattr(payload, "model_dump") else {},
        }
    except Exception as e:
        logger.warning(f"JWT verification failed: {str(e)}")
        if require_valid:
            raise AuthenticationError("Invalid or expired security token")
        return {
            "authenticated": False,
            "method": "none",
            "role": Role.ANONYMOUS.value,
            "permissions": get_permissions_for_role(Role.ANONYMOUS),
            "error": "token_invalid",
        }


def verify_authentication_required(
    api_key: str | None = None,
    bearer_token: str | None = None,
    allow_development_bypass: bool = False,
) -> dict[str, Any]:
    """
    Verify authentication is provided (deny-by-default).
    """
    settings = get_settings()

    # 1. Try JWT token (preferred)
    if bearer_token:
        try:
            return verify_jwt_token(bearer_token, require_valid=True)
        except AuthenticationError:
            # If JWT is provided but invalid, we fail even if API key is present
            # to prevent fallback abuse.
            raise

    # 2. Try API key
    if api_key:
        return verify_api_key(api_key, require_valid=True)

    # 3. Development bypass (must be explicit)
    if allow_development_bypass and settings.is_development:
        # Check for explicit bypass flag in environment to prevent accidental leak
        if os.getenv("MOTHERSHIP_ALLOW_DEV_BYPASS") == "1":
            logger.warning("SECURITY: Bypassing authentication in development mode")
            return {
                "authenticated": False,
                "method": "dev_bypass",
                "user_id": "dev_superuser",
                "role": Role.SUPER_ADMIN.value,
                "permissions": get_permissions_for_role(Role.SUPER_ADMIN),
            }

    # Deny by default
    raise AuthenticationError("Active authentication required to access this resource")
