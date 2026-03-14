"""
OAuth2 Auth Provider Abstraction Layer.

Provides a pluggable authentication provider interface that supports:
- Internal JWT (current default — JWTManager)
- External OAuth2/OIDC providers (Auth0, Keycloak, etc.)

The active provider is selected via MOTHERSHIP_AUTH_PROVIDER env var.
Rollback to internal JWT is always available via config change.

TDC-20260314-0002: Migrate to new auth provider
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

import jwt as pyjwt
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Provider Types
# =============================================================================


class AuthProviderType(StrEnum):
    """Supported auth provider types."""

    INTERNAL = "internal"
    OAUTH2 = "oauth2"


# =============================================================================
# Auth Result Models
# =============================================================================


@dataclass
class AuthToken:
    """Normalized token representation across providers."""

    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int = 1800
    id_token: str | None = None
    scopes: list[str] = field(default_factory=list)


@dataclass
class AuthUser:
    """Normalized user identity across providers."""

    user_id: str
    email: str | None = None
    username: str | None = None
    scopes: list[str] = field(default_factory=list)
    roles: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    provider: str = "internal"


@dataclass
class VerificationResult:
    """Token verification result."""

    valid: bool
    user: AuthUser | None = None
    error: str | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Provider Config
# =============================================================================


class OAuth2ProviderConfig(BaseModel):
    """Configuration for external OAuth2/OIDC provider."""

    issuer_url: str = Field("", description="OIDC issuer URL (e.g., https://auth.example.com/realms/grid)")
    client_id: str = Field("", description="OAuth2 client ID")
    client_secret: str = Field("", description="OAuth2 client secret")
    audience: str = Field("", description="Expected audience claim")
    jwks_uri: str = Field("", description="JWKS endpoint for public key discovery")
    token_endpoint: str = Field("", description="Token endpoint for password/code exchange")
    userinfo_endpoint: str = Field("", description="UserInfo endpoint")
    scopes: list[str] = Field(default_factory=lambda: ["openid", "profile", "email"])
    algorithms: list[str] = Field(default_factory=lambda: ["RS256"])
    # Claim mapping: external claim name → internal field
    claim_map: dict[str, str] = Field(
        default_factory=lambda: {
            "sub": "user_id",
            "email": "email",
            "preferred_username": "username",
            "realm_access.roles": "roles",
        }
    )

    @classmethod
    def from_env(cls) -> OAuth2ProviderConfig:
        """Load OAuth2 config from environment variables."""
        env = os.environ
        return cls(
            issuer_url=env.get("MOTHERSHIP_OAUTH2_ISSUER_URL", ""),
            client_id=env.get("MOTHERSHIP_OAUTH2_CLIENT_ID", ""),
            client_secret=env.get("MOTHERSHIP_OAUTH2_CLIENT_SECRET", ""),
            audience=env.get("MOTHERSHIP_OAUTH2_AUDIENCE", ""),
            jwks_uri=env.get("MOTHERSHIP_OAUTH2_JWKS_URI", ""),
            token_endpoint=env.get("MOTHERSHIP_OAUTH2_TOKEN_ENDPOINT", ""),
            userinfo_endpoint=env.get("MOTHERSHIP_OAUTH2_USERINFO_ENDPOINT", ""),
        )


# =============================================================================
# Abstract Provider Interface
# =============================================================================


class AuthProvider(ABC):
    """Abstract auth provider interface."""

    @abstractmethod
    async def authenticate(self, username: str, password: str, scopes: list[str] | None = None) -> AuthToken:
        """Authenticate user credentials and return tokens."""

    @abstractmethod
    async def verify_token(self, token: str) -> VerificationResult:
        """Verify an access token and return identity."""

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> AuthToken:
        """Exchange a refresh token for new tokens."""

    @abstractmethod
    async def revoke_token(self, token: str, token_type_hint: str = "access_token") -> bool:
        """Revoke a token."""

    @property
    @abstractmethod
    def provider_type(self) -> AuthProviderType:
        """Return the provider type identifier."""


# =============================================================================
# Internal JWT Provider (wraps existing JWTManager)
# =============================================================================


class InternalJWTProvider(AuthProvider):
    """
    Internal JWT provider — wraps the existing JWTManager + CredentialValidationService.

    This is the current default and preserves full backward compatibility.
    """

    def __init__(self):
        self._jwt_manager = None
        self._credential_validator = None

    def _get_jwt_manager(self):
        if self._jwt_manager is None:
            from .jwt import get_jwt_manager

            self._jwt_manager = get_jwt_manager()
        return self._jwt_manager

    def _get_credential_validator(self):
        if self._credential_validator is None:
            from .credential_validation import get_credential_validator

            self._credential_validator = get_credential_validator()
        return self._credential_validator

    @property
    def provider_type(self) -> AuthProviderType:
        return AuthProviderType.INTERNAL

    async def authenticate(self, username: str, password: str, scopes: list[str] | None = None) -> AuthToken:
        """Authenticate via internal credential store + JWT generation."""
        from ..config import get_settings

        settings = get_settings()
        granted_scopes = scopes or ["read"]

        # In production, validate credentials
        if not settings.is_development:
            validator = self._get_credential_validator()
            result = await validator.validate_credentials(username, password)
            if not result.success:
                raise AuthenticationError(result.error_message or "Authentication failed")

        jwt_mgr = self._get_jwt_manager()
        user_id = f"user_{username}"
        email = f"{username}@example.com" if "@" not in username else username

        token_pair = jwt_mgr.create_token_pair(
            subject=username,
            scopes=granted_scopes,
            user_id=user_id,
            email=email,
        )

        return AuthToken(
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
            token_type=token_pair.token_type,
            expires_in=token_pair.expires_in,
            scopes=granted_scopes,
        )

    async def verify_token(self, token: str) -> VerificationResult:
        """Verify JWT using internal JWTManager."""
        jwt_mgr = self._get_jwt_manager()
        try:
            payload = jwt_mgr.verify_token(token, expected_type="access")
            payload_dict = payload.model_dump() if hasattr(payload, "model_dump") else {}

            # Check revocation
            from .token_revocation import get_token_validator

            is_valid, error = await get_token_validator().validate_token(payload_dict)
            if not is_valid:
                return VerificationResult(valid=False, error=error or "Token revoked")

            user = AuthUser(
                user_id=payload.user_id or payload.sub,
                email=payload.email,
                username=payload.sub,
                scopes=payload.scopes or [],
                provider="internal",
                metadata=payload.metadata or {},
            )
            return VerificationResult(valid=True, user=user, raw_payload=payload_dict)

        except Exception as e:
            return VerificationResult(valid=False, error=str(e))

    async def refresh_token(self, refresh_token: str) -> AuthToken:
        """Refresh access token using internal JWTManager."""
        jwt_mgr = self._get_jwt_manager()
        new_access = jwt_mgr.refresh_access_token(refresh_token)
        return AuthToken(
            access_token=new_access,
            expires_in=jwt_mgr.access_token_expire_minutes * 60,
        )

    async def revoke_token(self, token: str, token_type_hint: str = "access_token") -> bool:
        """Revoke token via internal revocation list."""
        jwt_mgr = self._get_jwt_manager()
        try:
            payload = jwt_mgr.verify_token(token)
            payload_dict = payload.model_dump() if hasattr(payload, "model_dump") else {}
            from .token_revocation import get_token_validator

            return await get_token_validator().revoke_token(payload_dict, reason="api_revoke")
        except Exception as e:
            logger.warning("Token revocation failed: %s", e)
            return False


# =============================================================================
# External OAuth2/OIDC Provider
# =============================================================================


class OAuth2Provider(AuthProvider):
    """
    External OAuth2/OIDC provider.

    Validates tokens against an external identity provider using JWKS
    for public key discovery. Supports Auth0, Keycloak, Okta, etc.
    """

    def __init__(self, config: OAuth2ProviderConfig):
        self._config = config
        self._jwks_client: Any = None
        self._jwks_cache_expiry: datetime | None = None

    @property
    def provider_type(self) -> AuthProviderType:
        return AuthProviderType.OAUTH2

    def _get_jwks_client(self):
        """Get or create PyJWT JWKS client with caching."""
        now = datetime.now(UTC)
        if self._jwks_client is None or (self._jwks_cache_expiry and now > self._jwks_cache_expiry):
            jwks_uri = self._config.jwks_uri or f"{self._config.issuer_url}/.well-known/jwks.json"
            self._jwks_client = pyjwt.PyJWKClient(jwks_uri, cache_keys=True, lifespan=3600)
            self._jwks_cache_expiry = now + timedelta(hours=1)
        return self._jwks_client

    async def authenticate(self, username: str, password: str, scopes: list[str] | None = None) -> AuthToken:
        """
        Authenticate via OAuth2 Resource Owner Password Credentials (ROPC) grant.

        In production, prefer Authorization Code flow from the frontend.
        ROPC is provided for service-to-service and CLI authentication.
        """
        import httpx

        token_endpoint = self._config.token_endpoint or f"{self._config.issuer_url}/protocol/openid-connect/token"
        requested_scopes = " ".join(scopes or self._config.scopes)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                token_endpoint,
                data={
                    "grant_type": "password",
                    "client_id": self._config.client_id,
                    "client_secret": self._config.client_secret,
                    "username": username,
                    "password": password,
                    "scope": requested_scopes,
                },
            )

            if response.status_code != 200:
                body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                error_desc = body.get("error_description", "Authentication failed")
                raise AuthenticationError(error_desc)

            data = response.json()

        return AuthToken(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            token_type=data.get("token_type", "bearer"),
            expires_in=data.get("expires_in", 1800),
            id_token=data.get("id_token"),
            scopes=data.get("scope", "").split() if data.get("scope") else [],
        )

    async def verify_token(self, token: str) -> VerificationResult:
        """Verify access token using JWKS public key from the external provider."""
        try:
            jwks_client = self._get_jwks_client()
            signing_key = jwks_client.get_signing_key_from_jwt(token)

            decode_options: dict[str, Any] = {
                "algorithms": self._config.algorithms,
            }
            if self._config.audience:
                decode_options["audience"] = self._config.audience
            if self._config.issuer_url:
                decode_options["issuer"] = self._config.issuer_url

            payload = pyjwt.decode(
                token,
                signing_key.key,
                **decode_options,
            )

            # Map external claims to internal AuthUser
            user = self._map_claims(payload)
            return VerificationResult(valid=True, user=user, raw_payload=payload)

        except pyjwt.ExpiredSignatureError:
            return VerificationResult(valid=False, error="Token has expired")
        except pyjwt.InvalidAudienceError:
            return VerificationResult(valid=False, error="Invalid audience")
        except pyjwt.InvalidIssuerError:
            return VerificationResult(valid=False, error="Invalid issuer")
        except Exception as e:
            logger.warning("OAuth2 token verification failed: %s", e)
            return VerificationResult(valid=False, error=str(e))

    def _map_claims(self, payload: dict[str, Any]) -> AuthUser:
        """Map external provider claims to internal AuthUser using claim_map config."""
        claim_map = self._config.claim_map

        def _resolve(path: str, data: dict) -> Any:
            """Resolve dotted path like 'realm_access.roles' from nested dict."""
            parts = path.split(".")
            current = data
            for part in parts:
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    return None
            return current

        user_id = _resolve(claim_map.get("sub", "sub"), payload) or payload.get("sub", "")
        email = _resolve(claim_map.get("email", "email"), payload)
        username = _resolve(claim_map.get("preferred_username", "preferred_username"), payload)
        roles_key = claim_map.get("realm_access.roles", "realm_access.roles")
        roles = _resolve(roles_key, payload) or []

        scopes = payload.get("scope", "").split() if isinstance(payload.get("scope"), str) else []

        return AuthUser(
            user_id=str(user_id),
            email=email,
            username=username or str(user_id),
            scopes=scopes,
            roles=roles if isinstance(roles, list) else [],
            provider="oauth2",
            metadata={k: v for k, v in payload.items() if k not in ("sub", "email", "exp", "iat", "aud", "iss")},
        )

    async def refresh_token(self, refresh_token: str) -> AuthToken:
        """Exchange refresh token at the external provider's token endpoint."""
        import httpx

        token_endpoint = self._config.token_endpoint or f"{self._config.issuer_url}/protocol/openid-connect/token"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                token_endpoint,
                data={
                    "grant_type": "refresh_token",
                    "client_id": self._config.client_id,
                    "client_secret": self._config.client_secret,
                    "refresh_token": refresh_token,
                },
            )

            if response.status_code != 200:
                raise AuthenticationError("Refresh token invalid or expired")

            data = response.json()

        return AuthToken(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            token_type=data.get("token_type", "bearer"),
            expires_in=data.get("expires_in", 1800),
        )

    async def revoke_token(self, token: str, token_type_hint: str = "access_token") -> bool:
        """Revoke token at the external provider's revocation endpoint."""
        import httpx

        revocation_endpoint = f"{self._config.issuer_url}/protocol/openid-connect/revoke"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    revocation_endpoint,
                    data={
                        "client_id": self._config.client_id,
                        "client_secret": self._config.client_secret,
                        "token": token,
                        "token_type_hint": token_type_hint,
                    },
                )
                return response.status_code == 200
        except Exception as e:
            logger.warning("OAuth2 token revocation failed: %s", e)
            return False


# =============================================================================
# Import re-used exception
# =============================================================================

from .auth import AuthenticationError

# =============================================================================
# Provider Factory
# =============================================================================

_active_provider: AuthProvider | None = None


def get_auth_provider() -> AuthProvider:
    """
    Get the active auth provider based on configuration.

    Selection order:
    1. MOTHERSHIP_AUTH_PROVIDER env var ("internal" or "oauth2")
    2. Default: "internal" (preserves backward compatibility)

    Rollback procedure: Set MOTHERSHIP_AUTH_PROVIDER=internal
    """
    global _active_provider
    if _active_provider is not None:
        return _active_provider

    provider_type = os.getenv("MOTHERSHIP_AUTH_PROVIDER", "internal").lower()

    if provider_type == "oauth2":
        config = OAuth2ProviderConfig.from_env()
        if not config.issuer_url:
            logger.error(
                "MOTHERSHIP_AUTH_PROVIDER=oauth2 but MOTHERSHIP_OAUTH2_ISSUER_URL is not set. "
                "Falling back to internal provider."
            )
            _active_provider = InternalJWTProvider()
        else:
            _active_provider = OAuth2Provider(config)
            logger.info("Auth provider: OAuth2 (issuer=%s)", config.issuer_url)
    else:
        _active_provider = InternalJWTProvider()
        logger.info("Auth provider: Internal JWT")

    return _active_provider


def reset_auth_provider() -> None:
    """Reset the active provider (for testing)."""
    global _active_provider
    _active_provider = None
