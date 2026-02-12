"""
JWT Authentication Utilities.

Production-grade JWT token generation, validation, and management.
Uses python-jose for secure token handling.
"""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from pydantic import BaseModel, Field

from .secret_validation import (
    SecretStrength,
    SecretValidationError,
    generate_secure_secret,
    validate_secret_strength,
)

logger = logging.getLogger(__name__)


class TokenPayload(BaseModel):
    """JWT token payload structure."""

    sub: str = Field(..., description="Subject (user ID)")
    exp: int = Field(..., description="Expiration timestamp")
    iat: int = Field(..., description="Issued at timestamp")
    jti: str | None = Field(None, description="JWT ID (unique token identifier)")
    scopes: list[str] = Field(default_factory=list, description="Permission scopes")
    user_id: str | None = Field(None, description="User ID")
    email: str | None = Field(None, description="User email")
    role: str | None = Field(None, description="User role")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class TokenPair(BaseModel):
    """Access and refresh token pair."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration in seconds")


class JWTManager:
    """
    JWT token manager for production use.

    Handles token generation, validation, and refresh.
    """

    def __init__(
        self,
        secret_key: str | None = None,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7,
        environment: str = "production",
    ):
        """
        Initialize JWT manager with secure secret validation.

        Args:
            secret_key: Secret key for signing tokens (if None, will load from env)
            algorithm: JWT signing algorithm (default: HS256)
            access_token_expire_minutes: Access token lifetime in minutes
            refresh_token_expire_days: Refresh token lifetime in days
            environment: Current environment (production, development, testing)

        Raises:
            SecretValidationError: If secret is missing or too weak for environment
        """
        # Load secret from environment if not provided
        # Treat empty string same as None to allow env var fallback
        if secret_key is None or (isinstance(secret_key, str) and not secret_key.strip()):
            env_secret = os.getenv("MOTHERSHIP_SECRET_KEY")
            if not env_secret:
                # In development, allow fallback (but warn)
                if environment.lower() != "production":
                    logger.warning(
                        "JWT secret key not provided and MOTHERSHIP_SECRET_KEY not set. "
                        "Generating temporary secret for development. "
                        "This MUST be fixed before production deployment."
                    )
                    secret_key = generate_secure_secret()
                    logger.info(
                        f"Generated temporary JWT secret (length={len(secret_key)}). "
                        f"Set MOTHERSHIP_SECRET_KEY environment variable with this value "
                        f"or generate a new one with generate_secure_secret()."
                    )
                else:
                    # Production: fail fast
                    raise SecretValidationError(
                        "JWT secret key is required in production. "
                        "Set MOTHERSHIP_SECRET_KEY environment variable. "
                        "Use generate_secure_secret() to create a secure key."
                    )
            else:
                secret_key = env_secret

        # Validate secret strength
        try:
            strength = validate_secret_strength(secret_key, environment)
            if strength == SecretStrength.WEAK:
                if environment.lower() == "production":
                    raise SecretValidationError(
                        f"JWT secret key is too weak for production. "
                        f"Length: {len(secret_key)}. "
                        f"Generate a secure key with generate_secure_secret() or "
                        f"set MOTHERSHIP_SECRET_KEY to a value of at least 32 characters."
                    )
                else:
                    logger.warning(
                        f"JWT secret key is weak (length={len(secret_key)}). "
                        f"Recommended: at least 64 characters. "
                        f"Generate a secure key with generate_secure_secret()."
                    )
        except SecretValidationError:
            raise  # Re-raise validation errors
        except Exception as e:
            logger.error(f"JWT secret validation failed: {e}")
            if environment.lower() == "production":
                raise SecretValidationError(f"JWT secret validation failed: {e}") from e

        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        self._environment = environment

        # Security audit log (without exposing secret)
        # Only log strength if validation succeeded
        if "strength" in locals() and isinstance(strength, SecretStrength):
            logger.info(
                f"JWT Manager initialized with algorithm={algorithm}, "
                f"secret_strength={strength.value}, "
                f"environment={environment}"
            )
        else:
            logger.info(f"JWT Manager initialized with algorithm={algorithm}, environment={environment}")

    def create_access_token(
        self,
        subject: str,
        scopes: list[str] | None = None,
        user_id: str | None = None,
        email: str | None = None,
        metadata: dict[str, Any] | None = None,
        expires_delta: timedelta | None = None,
    ) -> str:
        """
        Create a new access token.

        Args:
            subject: Token subject (typically user ID)
            scopes: Permission scopes
            user_id: User ID
            email: User email
            metadata: Additional metadata
            expires_delta: Custom expiration delta

        Returns:
            Encoded JWT token string
        """
        now = datetime.now(UTC)
        if expires_delta:
            expire = now + expires_delta
        else:
            expire = now + timedelta(minutes=self.access_token_expire_minutes)

        payload = {
            "sub": subject,
            "exp": int(expire.timestamp()),
            "iat": int(now.timestamp()),
            "type": "access",
        }

        if scopes:
            payload["scopes"] = scopes
        if user_id:
            payload["user_id"] = user_id
        if email:
            payload["email"] = email
        if metadata:
            payload["metadata"] = metadata

        try:
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            return token
        except Exception as e:
            logger.exception("Failed to create access token")
            raise ValueError(f"Token creation failed: {e}") from e

    def create_refresh_token(
        self,
        subject: str,
        user_id: str | None = None,
        expires_delta: timedelta | None = None,
    ) -> str:
        """
        Create a new refresh token.

        Args:
            subject: Token subject (typically user ID)
            user_id: User ID
            expires_delta: Custom expiration delta

        Returns:
            Encoded JWT refresh token string
        """
        now = datetime.now(UTC)
        if expires_delta:
            expire = now + expires_delta
        else:
            expire = now + timedelta(days=self.refresh_token_expire_days)

        payload = {
            "sub": subject,
            "exp": int(expire.timestamp()),
            "iat": int(now.timestamp()),
            "type": "refresh",
        }

        if user_id:
            payload["user_id"] = user_id

        try:
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            return token
        except Exception as e:
            logger.exception("Failed to create refresh token")
            raise ValueError(f"Refresh token creation failed: {e}") from e

    def create_token_pair(
        self,
        subject: str,
        scopes: list[str] | None = None,
        user_id: str | None = None,
        email: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TokenPair:
        """
        Create a new access/refresh token pair.

        Args:
            subject: Token subject
            scopes: Permission scopes
            user_id: User ID
            email: User email
            metadata: Additional metadata

        Returns:
            TokenPair with access and refresh tokens
        """
        access_token = self.create_access_token(
            subject=subject,
            scopes=scopes,
            user_id=user_id,
            email=email,
            metadata=metadata,
        )
        refresh_token = self.create_refresh_token(subject=subject, user_id=user_id)

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.access_token_expire_minutes * 60,
        )

    def verify_token(
        self,
        token: str,
        expected_type: str | None = None,
    ) -> TokenPayload:
        """
        Verify and decode a JWT token.

        Args:
            token: JWT token string
            expected_type: Expected token type ('access' or 'refresh')

        Returns:
            Decoded token payload

        Raises:
            JWTError: If token is invalid or expired
            ValueError: If token type doesn't match expected
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )

            # Validate token type if specified
            if expected_type and payload.get("type") != expected_type:
                raise ValueError(f"Invalid token type: expected {expected_type}, got {payload.get('type')}")

            # Convert to TokenPayload model
            return TokenPayload(
                sub=payload.get("sub", ""),
                exp=payload.get("exp", 0),
                iat=payload.get("iat", 0),
                jti=payload.get("jti"),
                scopes=payload.get("scopes", []),
                user_id=payload.get("user_id"),
                email=payload.get("email"),
                metadata=payload.get("metadata", {}),
            )

        except JWTError as e:
            logger.warning("JWT verification failed: %s", str(e))
            raise
        except ValueError:
            # Re-raise type validation errors directly
            raise
        except Exception as e:
            logger.exception("Unexpected error during JWT verification")
            raise JWTError(f"Token verification failed: {e}") from e

    def refresh_access_token(self, refresh_token: str) -> str:
        """
        Generate a new access token from a valid refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            New access token

        Raises:
            JWTError: If refresh token is invalid
        """
        # Verify refresh token
        payload = self.verify_token(refresh_token, expected_type="refresh")

        # Create new access token with same subject
        return self.create_access_token(
            subject=payload.sub,
            user_id=payload.user_id,
            scopes=payload.scopes,
        )

    def decode_unverified(self, token: str) -> dict[str, Any]:
        """
        Decode token without verification (for inspection only).

        WARNING: This does NOT validate the token signature or expiration.
        Use only for debugging or logging purposes.

        Args:
            token: JWT token string

        Returns:
            Decoded payload dictionary
        """
        try:
            return jwt.get_unverified_claims(token)
        except Exception as e:
            logger.warning("Failed to decode token: %s", str(e))
            return {}


# Global JWT manager instance (initialized from settings)
_jwt_manager: JWTManager | None = None


def get_jwt_manager(
    secret_key: str | None = None,
    algorithm: str = "HS256",
    access_token_expire_minutes: int = 30,
    refresh_token_expire_days: int = 7,
    environment: str | None = None,
) -> JWTManager:
    """
    Get or create the global JWT manager instance with secure secret validation.

    Args:
        secret_key: JWT secret key (if None, loads from MOTHERSHIP_SECRET_KEY env var)
        algorithm: JWT algorithm
        access_token_expire_minutes: Access token lifetime
        refresh_token_expire_days: Refresh token lifetime
        environment: Current environment (auto-detected if None)

    Returns:
        JWTManager instance

    Raises:
        SecretValidationError: If secret is missing or too weak for environment
    """
    global _jwt_manager
    if _jwt_manager is None:
        # Auto-detect environment if not provided
        if environment is None:
            environment = os.getenv("MOTHERSHIP_ENVIRONMENT", "production").lower()

        _jwt_manager = JWTManager(
            secret_key=secret_key,
            algorithm=algorithm,
            access_token_expire_minutes=access_token_expire_minutes,
            refresh_token_expire_days=refresh_token_expire_days,
            environment=environment,
        )
    return _jwt_manager


def reset_jwt_manager() -> None:
    """Reset the global JWT manager (for testing)."""
    global _jwt_manager
    _jwt_manager = None
