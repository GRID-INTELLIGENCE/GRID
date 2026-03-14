"""
Authentication and token management endpoints.

Provides JWT token generation, refresh, validation, and user registration endpoints.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from application.mothership.dependencies import Auth, RateLimited, RequestContext, Settings
from application.mothership.schemas import ApiResponse, ResponseMeta
from application.mothership.security.auth_provider import get_auth_provider
from application.mothership.security.credential_validation import validate_production_credentials
from application.mothership.security.jwt import get_jwt_manager
from application.mothership.security.token_revocation import get_token_validator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


class LoginRequest(BaseModel):
    """Login request payload."""

    username: str = Field(..., description="Username or email", min_length=1, max_length=255)
    password: str = Field(..., description="User password", min_length=1, max_length=255)
    scopes: list[str] = Field(default_factory=lambda: ["read", "write"], description="Requested scopes")


class TokenResponse(BaseModel):
    """Token response."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    scopes: list[str] = Field(default_factory=list, description="Granted scopes")


class RefreshRequest(BaseModel):
    """Token refresh request."""

    refresh_token: str = Field(..., description="Valid refresh token")


class RefreshResponse(BaseModel):
    """Token refresh response."""

    access_token: str = Field(..., description="New access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")


class ValidateResponse(BaseModel):
    """Token validation response."""

    valid: bool = Field(..., description="Whether token is valid")
    user_id: str | None = Field(None, description="User ID from token")
    email: str | None = Field(None, description="Email from token")
    scopes: list[str] = Field(default_factory=list, description="Token scopes")
    expires_at: int | None = Field(None, description="Token expiration timestamp")


class UserResponse(BaseModel):
    """Current user response."""

    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    full_name: str | None = Field(None, description="Full name")
    trust_tier: str = Field(default="standard", description="Trust tier")
    is_active: bool = Field(default=True, description="Whether user is active")
    scopes: list[str] = Field(default_factory=list, description="User scopes")


class RegisterRequest(BaseModel):
    """User registration request."""

    username: str = Field(..., description="Username", min_length=3, max_length=50)
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., description="Password", min_length=8, max_length=255)
    full_name: str | None = Field(None, description="Full name", max_length=255)


@router.post("/register", response_model=ApiResponse[UserResponse], status_code=status.HTTP_201_CREATED)
async def register_user(
    request: RegisterRequest,
    _: RateLimited,
    request_context: RequestContext,
) -> ApiResponse[UserResponse]:
    """
    Register a new user account.

    Creates a new user with BASIC trust tier. In development mode,
    this creates the user without external dependencies. In production,
    this would integrate with the user store.

    Args:
        request: Registration details
        _: Rate limiting enforcement
        request_context: Request context

    Returns:
        API response with created user details

    Raises:
        HTTPException: If registration fails (e.g., user already exists)
    """
    request_id = request_context.get("request_id", "unknown")

    # Generate unique user ID
    import uuid

    user_id = str(uuid.uuid4())

    # In a real implementation, this would:
    # 1. Check if email/username already exists
    # 2. Hash the password securely
    # 3. Store user in database
    # 4. Potentially send verification email

    # For now, we simulate successful registration
    logger.info("User registered: %s (%s) (request_id=%s)", request.username, request.email, request_id)

    response_data = UserResponse(
        id=user_id,
        username=request.username,
        email=request.email,
        full_name=request.full_name,
        trust_tier="BASIC",  # New users start with BASIC tier
        is_active=True,
        scopes=["read"],  # New users get read-only by default
    )

    return ApiResponse(
        success=True,
        data=response_data,
        meta=ResponseMeta(request_id=request_id),
    )


@router.post("/login", response_model=ApiResponse[TokenResponse])
async def login(
    request: LoginRequest,
    _: RateLimited,
    settings: Settings,
    request_context: RequestContext,
) -> ApiResponse[TokenResponse]:
    """
    Authenticate user and generate JWT tokens.

    Routes through the active auth provider (internal JWT or external OAuth2).
    Provider is selected via MOTHERSHIP_AUTH_PROVIDER env var.

    **Development Mode:**
    - Any username/password combination is accepted
    - Tokens are generated for testing purposes

    **Production Mode:**
    - Credentials are validated via the configured auth provider
    - Failed attempts are logged and rate-limited

    Args:
        request: Login credentials
        _: Rate limiting enforcement
        settings: Application settings
        request_context: Request context

    Returns:
        API response with token pair

    Raises:
        HTTPException: If authentication fails
    """
    request_id = request_context.get("request_id", "unknown")

    # Normalize scopes - ensure valid permissions only
    valid_scopes = {"read", "write", "admin"}
    granted_scopes = [s for s in request.scopes if s in valid_scopes]
    if not granted_scopes:
        granted_scopes = ["read"]  # Default to read-only

    try:
        provider = get_auth_provider()
        auth_token = await provider.authenticate(
            username=request.username,
            password=request.password,
            scopes=granted_scopes,
        )

        response_data = TokenResponse(
            access_token=auth_token.access_token,
            refresh_token=auth_token.refresh_token or "",
            token_type=auth_token.token_type,
            expires_in=auth_token.expires_in,
            scopes=auth_token.scopes or granted_scopes,
        )

        logger.info(
            "User authenticated successfully via %s: %s (request_id=%s)",
            provider.provider_type,
            request.username,
            request_id,
        )

        return ApiResponse(
            success=True,
            data=response_data,
            meta=ResponseMeta(request_id=request_id),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.warning(
            "Authentication failed for user: %s, error: %s (request_id=%s)",
            request.username,
            str(e),
            request_id,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e) if str(e) else "Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


@router.post("/refresh", response_model=ApiResponse[RefreshResponse])
async def refresh_token(
    request: RefreshRequest,
    _: RateLimited,
    settings: Settings,
    request_context: RequestContext,
) -> ApiResponse[RefreshResponse]:
    """
    Refresh an access token using a valid refresh token.

    Args:
        request: Refresh token
        _: Rate limiting enforcement
        settings: Application settings
        request_context: Request context

    Returns:
        API response with new access token

    Raises:
        HTTPException: If refresh token is invalid or expired
    """
    request_id = request_context.get("request_id", "unknown")

    try:
        provider = get_auth_provider()
        auth_token = await provider.refresh_token(request.refresh_token)

        response_data = RefreshResponse(
            access_token=auth_token.access_token,
            token_type=auth_token.token_type,
            expires_in=auth_token.expires_in,
        )

        logger.info("Token refreshed successfully via %s (request_id=%s)", provider.provider_type, request_id)

        return ApiResponse(
            success=True,
            data=response_data,
            meta=ResponseMeta(request_id=request_id),
        )

    except Exception as e:
        logger.warning("Token refresh failed: %s (request_id=%s)", str(e), request_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


@router.get("/validate", response_model=ApiResponse[ValidateResponse])
async def validate_token(
    auth: Auth,
    request_context: RequestContext,
) -> ApiResponse[ValidateResponse]:
    """
    Validate the current authentication token.

    This endpoint can be used to check if a token is still valid
    and retrieve information about the authenticated user.

    Args:
        auth: Authentication context (automatically validated)
        request_context: Request context

    Returns:
        API response with token validation result
    """
    request_id = request_context.get("request_id", "unknown")

    # If we got here, the token is valid (dependencies validated it)
    token_payload = auth.get("token_payload", {})

    response_data = ValidateResponse(
        valid=auth.get("authenticated", False),
        user_id=auth.get("user_id"),
        email=auth.get("email"),
        scopes=list(
            token_payload.get("scopes") if token_payload.get("scopes") is not None else auth.get("permissions", [])
        ),
        expires_at=token_payload.get("exp"),
    )

    return ApiResponse(
        success=True,
        data=response_data,
        meta=ResponseMeta(request_id=request_id),
    )


@router.get("/me", response_model=ApiResponse[UserResponse])
async def get_current_user(
    auth: Auth,
    request_context: RequestContext,
) -> ApiResponse[UserResponse]:
    """
    Get current authenticated user information.

    Returns details about the currently authenticated user based on the JWT token.

    Args:
        auth: Authentication context (automatically validated)
        request_context: Request context

    Returns:
        API response with current user details
    """
    request_id = request_context.get("request_id", "unknown")
    token_payload = auth.get("token_payload", {})

    # Extract user info from auth context
    user_id = auth.get("user_id", "unknown")
    email = auth.get("email", "")
    username = token_payload.get("sub", "")
    scopes = list(
        token_payload.get("scopes") if token_payload.get("scopes") is not None else auth.get("permissions", [])
    )

    response_data = UserResponse(
        id=user_id,
        username=username,
        email=email,
        full_name=None,  # Could be populated from user store in production
        trust_tier="standard",  # Default tier, could be from user store
        is_active=True,
        scopes=scopes,
    )

    return ApiResponse(
        success=True,
        data=response_data,
        meta=ResponseMeta(request_id=request_id),
    )


@router.post("/logout", response_model=ApiResponse[dict[str, Any]])
async def logout(
    auth: Auth,
    request_context: RequestContext,
) -> ApiResponse[dict[str, Any]]:
    """
    Logout and invalidate current session.

    Revokes the current JWT token by adding it to the revocation list.
    The token will be invalid for future requests after logout.

    Args:
        auth: Authentication context
        request_context: Request context

    Returns:
        API response with logout confirmation
    """
    request_id = request_context.get("request_id", "unknown")
    user_id = auth.get("user_id", "unknown")
    token_payload = auth.get("token_payload", {})

    # Revoke the token
    revoked = False
    if token_payload:
        validator = get_token_validator()
        revoked = await validator.revoke_token(token_payload, reason="logout")
        if revoked:
            logger.info("Token revoked for user: %s (request_id=%s)", user_id, request_id)
        else:
            logger.warning("Failed to revoke token for user: %s (request_id=%s)", user_id, request_id)

    logger.info("User logged out: %s (request_id=%s)", user_id, request_id)

    return ApiResponse(
        success=True,
        data={
            "message": "Logged out successfully",
            "user_id": user_id,
            "token_revoked": revoked,
        },
        meta=ResponseMeta(request_id=request_id),
    )


# Rebuild models for Pydantic v2
LoginRequest.model_rebuild()
TokenResponse.model_rebuild()
RefreshRequest.model_rebuild()
RefreshResponse.model_rebuild()
ValidateResponse.model_rebuild()
UserResponse.model_rebuild()
RegisterRequest.model_rebuild()
