"""
Authentication and token management endpoints.

Provides JWT token generation, refresh, and validation endpoints.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from application.mothership.dependencies import Auth, RateLimited, RequestContext, Settings
from application.mothership.schemas import ApiResponse, ResponseMeta
from application.mothership.security.credential_validation import validate_production_credentials
from application.mothership.security.jwt import get_jwt_manager
from application.mothership.security.token_revocation import get_token_validator, revoke_token_by_jti

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


@router.post("/login", response_model=ApiResponse[TokenResponse])
async def login(
    request: LoginRequest,
    _: RateLimited,
    settings: Settings,
    request_context: RequestContext,
) -> ApiResponse[TokenResponse]:
    """
    Authenticate user and generate JWT tokens.

    **Development Mode:**
    - Any username/password combination is accepted
    - Tokens are generated for testing purposes

    **Production Mode:**
    - Credentials are validated against user store
    - Secure password hashing verification
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
    auth_result = None

    # Production credential validation
    if not settings.is_development:
        auth_result = await validate_production_credentials(request.username, request.password)

        if not auth_result.success:
            logger.warning(
                "Authentication failed for user: %s, reason: %s (request_id=%s)",
                request.username,
                auth_result.error_code,
                request_id
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=auth_result.error_message or "Authentication failed",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # Generate JWT token pair
    # Convert empty string to None to allow env var fallback
    secret_key_param = (
        settings.security.secret_key if settings.security.secret_key and settings.security.secret_key.strip() else None
    )
    jwt_manager = get_jwt_manager(
        secret_key=secret_key_param,
        environment=settings.environment.value,
        algorithm=settings.security.algorithm,
        access_token_expire_minutes=settings.security.access_token_expire_minutes,
        refresh_token_expire_days=settings.security.refresh_token_expire_days,
    )

    # Normalize scopes - ensure valid permissions only
    valid_scopes = {"read", "write", "admin"}
    granted_scopes = [s for s in request.scopes if s in valid_scopes]
    if not granted_scopes:
        granted_scopes = ["read"]  # Default to read-only

    # Get user details from auth result in production, or use defaults in dev
    if not settings.is_development and auth_result and auth_result.user:
        user_id = auth_result.user.user_id
        email = auth_result.user.email or f"{request.username}@example.com"
    else:
        user_id = f"user_{request.username}"
        email = f"{request.username}@example.com" if "@" not in request.username else request.username

    try:
        token_pair = jwt_manager.create_token_pair(
            subject=request.username,
            scopes=granted_scopes,
            user_id=user_id,
            email=email,
            metadata={
                "login_method": "password",
                "request_id": request_id,
            },
        )

        response_data = TokenResponse(
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
            token_type=token_pair.token_type,
            expires_in=token_pair.expires_in,
            scopes=granted_scopes,
        )

        logger.info("User authenticated successfully: %s (request_id=%s)", request.username, request_id)

        return ApiResponse(
            success=True,
            data=response_data,
            meta=ResponseMeta(request_id=request_id),
        )

    except Exception as e:
        logger.exception("Token generation failed for user: %s", request.username)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed - unable to generate tokens",
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

    jwt_manager = get_jwt_manager(
        secret_key=settings.security.secret_key,
        environment=settings.environment.value,
        algorithm=settings.security.algorithm,
        access_token_expire_minutes=settings.security.access_token_expire_minutes,
        refresh_token_expire_days=settings.security.refresh_token_expire_days,
    )

    try:
        # Generate new access token from refresh token
        new_access_token = jwt_manager.refresh_access_token(request.refresh_token)

        response_data = RefreshResponse(
            access_token=new_access_token,
            token_type="bearer",
            expires_in=settings.security.access_token_expire_minutes * 60,
        )

        logger.info("Token refreshed successfully (request_id=%s)", request_id)

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
