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


def _check_development_bypass(allow_development_bypass: bool, settings) -> dict[str, Any] | None:
    """
    Hardened development authentication bypass with multiple security checks.

    SECURITY UPDATE 2026-02-02: Enhanced with defense-in-depth approach.

    This function provides a development-only authentication bypass with strict
    safeguards to prevent accidental production use. Multiple layers of checks
    ensure this cannot be enabled in production.

    Security Features:
    - BLOCKS all bypass attempts in production environment
    - Requires THREE separate environment variables
    - Extensive security logging with timestamps
    - Machine ID tracking for audit trails
    - Returns None if any check fails (deny by default)

    Args:
        allow_development_bypass: Explicit function parameter
        settings: Application settings with environment info

    Returns:
        dict with SUPER_ADMIN permissions if all checks pass, None otherwise

    Raises:
        SecurityException: If bypass attempted in production
    """
    from datetime import datetime

    # CRITICAL SECURITY CHECK #1: NEVER allow in production
    if hasattr(settings, "environment") and settings.environment == "production":
        logger.critical(
            "SECURITY VIOLATION: Development bypass attempted in PRODUCTION environment. "
            "This is a critical security violation. Blocking and logging incident."
        )
        raise SecurityException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Development bypass not allowed in production",
            code="DEV_BYPASS_PRODUCTION_BLOCKED",
        )

    # CRITICAL SECURITY CHECK #2: Explicit opt-in required
    if not allow_development_bypass:
        return None

    # CRITICAL SECURITY CHECK #3: Development mode required
    if not settings.is_development:
        logger.error("SECURITY: Development bypass rejected - is_development=False")
        return None

    # DEFENSE IN DEPTH: Require THREE environment variables
    # This makes accidental production deployment much less likely
    bypass_enabled = os.getenv("MOTHERSHIP_ALLOW_DEV_BYPASS") == "1"
    bypass_confirmed = os.getenv("MOTHERSHIP_DEV_BYPASS_CONFIRMED") == "yes_i_understand_the_risk"
    dev_machine_id = os.getenv("DEV_MACHINE_ID")  # Unique identifier for developer's machine

    # DENY BY DEFAULT: If any variable missing, bypass rejected
    if not (bypass_enabled and bypass_confirmed and dev_machine_id):
        missing = []
        if not bypass_enabled:
            missing.append("MOTHERSHIP_ALLOW_DEV_BYPASS")
        if not bypass_confirmed:
            missing.append("MOTHERSHIP_DEV_BYPASS_CONFIRMED")
        if not dev_machine_id:
            missing.append("DEV_MACHINE_ID")

        logger.warning(f"SECURITY: Development bypass incomplete - missing: {', '.join(missing)}")
        return None

    # EXTENSIVE SECURITY LOGGING
    # Log with maximum detail for audit trails
    timestamp = datetime.now().isoformat()
    logger.warning("=" * 80)
    logger.warning("SECURITY WARNING: DEVELOPMENT AUTHENTICATION BYPASS ACTIVE")
    logger.warning(f"Timestamp: {timestamp}")
    logger.warning(f"Machine ID: {dev_machine_id}")
    logger.warning(f"Environment: {settings.environment if hasattr(settings, 'environment') else 'unknown'}")
    logger.warning(f"Is Development: {settings.is_development}")
    logger.warning("Granted Role: SUPER_ADMIN")
    logger.warning("Authenticated: False (bypass - no real authentication)")
    logger.warning("")
    logger.warning("SECURITY IMPLICATIONS:")
    logger.warning("- This grants SUPER_ADMIN privileges without authentication")
    logger.warning("- ALL API endpoints are accessible")
    logger.warning("- ALL data can be read, modified, or deleted")
    logger.warning("- NEVER enable this in production or shared environments")
    logger.warning("- Use only on isolated development machines")
    logger.warning("")
    logger.warning("TO DISABLE: Unset MOTHERSHIP_ALLOW_DEV_BYPASS environment variable")
    logger.warning("=" * 80)

    # Return bypass credentials with audit information
    return {
        "authenticated": False,  # Clearly mark as not truly authenticated
        "method": "dev_bypass",
        "user_id": f"dev_superuser_{dev_machine_id}",
        "role": Role.SUPER_ADMIN.value,
        "permissions": get_permissions_for_role(Role.SUPER_ADMIN),
        "dev_bypass_active": True,  # Flag for additional logging/monitoring
        "bypass_timestamp": timestamp,
        "machine_id": dev_machine_id,
    }


def verify_api_key(api_key: str | None, require_valid: bool = True) -> dict[str, Any]:
    """
    Verify API key authentication with strict validation and RBAC integration.
    """
    get_settings()

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

    raise AuthenticationError("Invalid or unauthorized API key")


async def verify_jwt_token(token: str | None, require_valid: bool = True) -> dict[str, Any]:
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

    # Check for token revocation
    from .token_revocation import get_token_validator

    # Convert to dict for validator
    payload_dict = payload.model_dump() if hasattr(payload, "model_dump") else {}
    is_valid, error = await get_token_validator().validate_token(payload_dict)
    if not is_valid:
        logger.warning(f"JWT revocation check failed: {error}")
        if require_valid:
            raise AuthenticationError(f"Token invalid: {error}")
        return {
            "authenticated": False,
            "method": "none",
            "role": Role.ANONYMOUS.value,
            "permissions": get_permissions_for_role(Role.ANONYMOUS),
            "error": "token_revoked",
        }

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


async def verify_authentication_required(
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
            return await verify_jwt_token(bearer_token, require_valid=True)
        except AuthenticationError:
            # If JWT is provided but invalid, we fail even if API key is present
            # to prevent fallback abuse.
            raise

    # 2. Try API key
    if api_key:
        return verify_api_key(api_key, require_valid=True)

    # 3. Development bypass (HARDENED 2026-02-02: Multiple security checks)
    if allow_development_bypass and settings.is_development:
        return _check_development_bypass(allow_development_bypass, settings)

    # Deny by default
    raise AuthenticationError("Active authentication required to access this resource")
