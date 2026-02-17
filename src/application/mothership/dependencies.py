"""
Mothership Cockpit FastAPI Dependencies.

Dependency injection functions for FastAPI endpoints providing
access to services, configuration, and authentication.
"""

from __future__ import annotations

import logging
import os
from typing import Annotated, Any

from fastapi import Depends, Header, HTTPException, Query, Request, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from .config import MothershipSettings, get_settings
from .exceptions import ResourceNotFoundError
from .models import Session
from .repositories import StateStore, get_state_store, get_unit_of_work
from .repositories.db import DbUnitOfWork
from .services import CockpitService

logger = logging.getLogger(__name__)


# =============================================================================
# Security Schemes
# =============================================================================

api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
    description="API key for authentication",
)

bearer_scheme = HTTPBearer(
    auto_error=False,
    description="JWT Bearer token",
)


# =============================================================================
# Configuration Dependencies
# =============================================================================


def get_config() -> MothershipSettings:
    """
    Get application configuration.

    Returns:
        MothershipSettings instance
    """
    return get_settings()


Settings = Annotated[MothershipSettings, Depends(get_config)]


# =============================================================================
# State & Repository Dependencies
# =============================================================================


async def get_store() -> StateStore:
    """
    Get the state store instance.

    Returns:
        StateStore singleton instance
    """
    return get_state_store()


Store = Annotated[StateStore, Depends(get_store)]


async def get_uow() -> Any:
    """
    Get a Unit of Work instance for repository access.

    Returns:
        UnitOfWork instance
    """
    mode = os.getenv("MOTHERSHIP_PERSISTENCE_MODE", "memory").lower().strip()
    if mode == "db":
        return DbUnitOfWork()
    return get_unit_of_work()


UoW = Annotated[Any, Depends(get_uow)]


# =============================================================================
# Service Dependencies
# =============================================================================

# Global service instance (singleton pattern)
_cockpit_service: CockpitService | None = None


def get_cockpit_service() -> CockpitService:
    """
    Get the cockpit service instance.

    Uses singleton pattern to ensure consistent state across requests.

    Returns:
        CockpitService instance
    """
    global _cockpit_service
    if _cockpit_service is None:
        settings = get_settings()
        _cockpit_service = CockpitService(
            session_ttl_minutes=settings.cockpit.session_timeout_minutes,
            max_sessions=settings.cockpit.max_concurrent_sessions,
            max_concurrent_operations=settings.cockpit.task_queue_size,
        )
        _cockpit_service.start()
    return _cockpit_service


def reset_cockpit_service() -> None:
    """Reset the cockpit service (for testing)."""
    global _cockpit_service
    if _cockpit_service:
        _cockpit_service.shutdown()
    _cockpit_service = None


Cockpit = Annotated[CockpitService, Depends(get_cockpit_service)]


# =============================================================================
# Authentication Dependencies
# =============================================================================


async def get_api_key(
    api_key: str | None = Depends(api_key_header),
    settings: MothershipSettings = Depends(get_config),
) -> str | None:
    """
    Extract and validate API key from request headers.

    Args:
        api_key: API key from header
        settings: Application settings

    Returns:
        Validated API key or None
    """
    if api_key is None:
        return None

    # In production, validate against stored keys
    # For now, accept any non-empty key in development
    if settings.is_development:
        return api_key

    # Production validation would go here
    # Example: Check against database or secrets manager
    return api_key


async def get_bearer_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str | None:
    """
    Extract JWT token from Authorization header.

    Args:
        credentials: Bearer credentials

    Returns:
        JWT token string or None
    """
    if credentials is None:
        return None
    return credentials.credentials


from application.mothership.security.rbac import Role, get_permissions_for_role, has_permission

from .security.auth import verify_api_key, verify_jwt_token


async def verify_authentication(
    api_key: str | None = Depends(get_api_key),
    bearer_token: str | None = Depends(get_bearer_token),
    settings: MothershipSettings = Depends(get_config),
) -> dict[str, Any]:
    """
    Verify request authentication using centralized security logic.
    Supports both API key and JWT authentication with RBAC integration.
    """
    # 1. Try JWT authentication (Highest Priority)
    if bearer_token:
        try:
            return await verify_jwt_token(bearer_token, require_valid=True)
        except Exception as e:
            logger.warning(f"JWT verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e) if settings.is_development else "Invalid or expired authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            ) from e

    # 2. API Key authentication
    if api_key:
        try:
            return verify_api_key(api_key, require_valid=True)
        except Exception as e:
            logger.warning(f"API Key verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e) if settings.is_development else "Invalid API Key",
            ) from e

    # 3. Development mode bypass
    if settings.is_development and os.getenv("MOTHERSHIP_ALLOW_UNAUTHENTICATED_DEV") == "1":
        logger.info("Using unauthenticated development bypass")
        return {
            "authenticated": False,
            "method": "dev_bypass",
            "user_id": "dev_user",
            "role": Role.ADMIN.value,
            "permissions": get_permissions_for_role(Role.ADMIN),
        }

    # Deny-by-default for production
    if settings.is_production:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 4. Anonymous fallback for non-production
    return {
        "authenticated": False,
        "method": "none",
        "user_id": "anonymous",
        "role": Role.ANONYMOUS.value,
        "permissions": get_permissions_for_role(Role.ANONYMOUS),
    }


Auth = Annotated[dict[str, Any], Depends(verify_authentication)]


async def require_authentication(
    auth: Auth,
) -> dict[str, Any]:
    """
    Require authentication for an endpoint.
    """
    if not auth.get("authenticated", False) and auth.get("method") != "dev_bypass":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return auth


RequiredAuth = Annotated[dict[str, Any], Depends(require_authentication)]


async def require_permission(
    permission: str,
    auth: Auth,
) -> dict[str, Any]:
    """
    Require a specific permission using the RBAC system.
    """
    permissions = auth.get("permissions", set())
    if has_permission(permissions, permission):
        return auth

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Operation requires '{permission}' permission",
    )


async def require_admin(auth: dict[str, Any] = Depends(require_authentication)) -> dict[str, Any]:
    """Require admin permission."""
    return await require_permission("admin", auth)


async def require_write(auth: dict[str, Any] = Depends(require_authentication)) -> dict[str, Any]:
    """Require write permission."""
    return await require_permission("write", auth)


AdminAuth = Annotated[dict[str, Any], Depends(require_admin)]
WriteAuth = Annotated[dict[str, Any], Depends(require_write)]


# =============================================================================
# Session Dependencies
# =============================================================================


async def get_session_id(
    x_session_id: str | None = Header(None, alias="X-Session-ID"),
    session_id: str | None = Query(None, alias="session_id"),
) -> str | None:
    """
    Extract session ID from headers or query params.

    Args:
        x_session_id: Session ID from header
        session_id: Session ID from query param

    Returns:
        Session ID or None
    """
    return x_session_id or session_id


SessionId = Annotated[str | None, Depends(get_session_id)]


async def get_current_session(
    session_id: SessionId,
    cockpit: Cockpit,
) -> Session | None:
    """
    Get the current session if session ID is provided.

    Args:
        session_id: Session ID
        cockpit: Cockpit service

    Returns:
        Session object or None
    """
    if not session_id:
        return None

    try:
        return cockpit.sessions.get_session(session_id)
    except ResourceNotFoundError:
        return None


CurrentSession = Annotated[Session | None, Depends(get_current_session)]


async def require_session(
    session: CurrentSession,
) -> Session:
    """
    Require a valid session.

    Args:
        session: Current session

    Returns:
        Validated session

    Raises:
        HTTPException: If no valid session
    """
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid session required",
            headers={"X-Session-ID": "required"},
        )

    if not session.is_active():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired",
        )

    return session


RequiredSession = Annotated[Session, Depends(require_session)]


# =============================================================================
# Request Context Dependencies
# =============================================================================


async def get_request_context(
    request: Request,
    auth: Auth,
    session: CurrentSession,
    settings: Settings,
) -> dict[str, Any]:
    """
    Build request context with all relevant information.

    Args:
        request: FastAPI request object
        auth: Authentication context
        session: Current session if any
        settings: Application settings

    Returns:
        Request context dictionary
    """
    return {
        "request_id": request.headers.get("X-Request-ID"),
        "correlation_id": request.headers.get("X-Correlation-ID"),
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("User-Agent"),
        "auth": auth,
        "session_id": session.id if session else None,
        "user_id": auth.get("user_id"),
        "environment": settings.environment.value,
    }


RequestContext = Annotated[dict[str, Any], Depends(get_request_context)]


# =============================================================================
# Pagination Dependencies
# =============================================================================


async def get_pagination(
    page: int = Query(1, ge=1, le=10000, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str | None = Query(None, description="Field to sort by"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
) -> dict[str, Any]:
    """
    Extract pagination parameters from query string.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        sort_by: Field to sort by
        sort_order: Sort direction (asc/desc)

    Returns:
        Pagination parameters dictionary
    """
    return {
        "page": page,
        "page_size": page_size,
        "offset": (page - 1) * page_size,
        "limit": page_size,
        "sort_by": sort_by,
        "sort_order": sort_order,
    }


Pagination = Annotated[dict[str, Any], Depends(get_pagination)]


# =============================================================================
# Health Check Dependencies
# =============================================================================


async def check_system_ready(
    cockpit: Cockpit,
    settings: Settings,
) -> bool:
    """
    Check if system is ready to handle requests.

    Args:
        cockpit: Cockpit service
        settings: Application settings

    Returns:
        True if system is ready

    Raises:
        HTTPException: If system not ready
    """
    if not cockpit.is_healthy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System not ready",
        )
    return True


SystemReady = Annotated[bool, Depends(check_system_ready)]


# =============================================================================
# Rate Limiting Dependencies
# =============================================================================

# Simple in-memory rate limiter (use Redis in production)
_rate_limit_store: dict[str, list] = {}


async def check_rate_limit(
    request: Request,
    auth: Auth,
    settings: Settings,
) -> bool:
    """
    Check rate limiting for the request.

    Args:
        request: FastAPI request
        auth: Authentication context
        settings: Application settings

    Returns:
        True if within rate limits

    Raises:
        HTTPException: If rate limit exceeded
    """
    if not settings.security.rate_limit_enabled:
        return True

    # Use user_id or IP for rate limiting
    key = auth.get("user_id") or (request.client.host if request.client else "unknown")

    import time

    now = time.time()
    window = settings.security.rate_limit_window_seconds
    max_requests = settings.security.rate_limit_requests

    # Clean old entries and add current request
    if key not in _rate_limit_store:
        _rate_limit_store[key] = []

    _rate_limit_store[key] = [ts for ts in _rate_limit_store[key] if now - ts < window]

    if len(_rate_limit_store[key]) >= max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(window)},
        )

    _rate_limit_store[key].append(now)
    return True


RateLimited = Annotated[bool, Depends(check_rate_limit)]


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Configuration
    "get_config",
    "Settings",
    # State & Repository
    "get_store",
    "Store",
    "get_uow",
    "UoW",
    # Services
    "get_cockpit_service",
    "reset_cockpit_service",
    "Cockpit",
    # Authentication
    "get_api_key",
    "get_bearer_token",
    "verify_authentication",
    "require_authentication",
    "require_permission",
    "require_admin",
    "require_write",
    "Auth",
    "RequiredAuth",
    "AdminAuth",
    "WriteAuth",
    # Session
    "get_session_id",
    "get_current_session",
    "require_session",
    "SessionId",
    "CurrentSession",
    "RequiredSession",
    # Request Context
    "get_request_context",
    "RequestContext",
    # Pagination
    "get_pagination",
    "Pagination",
    # Health
    "check_system_ready",
    "SystemReady",
    # Rate Limiting
    "check_rate_limit",
    "RateLimited",
]
