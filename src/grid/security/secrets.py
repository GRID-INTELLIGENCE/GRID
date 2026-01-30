"""Secrets Management Integration for GRID.

Provides secure secrets retrieval and caching for production deployments.
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


from pydantic import BaseModel, StrictStr, field_validator


class Secret(BaseModel):
    """Secret data container."""

    key: StrictStr
    value: StrictStr
    version: StrictStr | None = None
    expires_at: datetime | None = None
    metadata: dict[str, Any] | None = None

    @field_validator("value")
    def validate_secret_strength(cls, v: str) -> str:
        # Basic sanity check, can be expanded
        if not v:
            raise ValueError("Secret value cannot be empty")
        return v


class SecretsProvider(ABC):
    """Abstract base class for secrets providers."""

    @abstractmethod
    async def get_secret(self, key: str) -> Secret | None:
        """Retrieve a secret by key."""
        pass

    @abstractmethod
    async def list_secrets(self, prefix: str = "") -> list[str]:
        """List available secrets with optional prefix filter."""
        pass

    @abstractmethod
    async def refresh_secret(self, key: str) -> Secret | None:
        """Force refresh a secret from the provider."""
        pass


class VaultProvider(SecretsProvider):
    """HashiCorp Vault secrets provider."""

    def __init__(self, url: str, token: str, mount_path: str = "secret"):
        self.url = url.rstrip("/")
        self.token = token
        self.mount_path = mount_path
        self._session = None

    async def _get_session(self) -> Any:
        """Get HTTP session for Vault requests."""
        if self._session is None:
            import aiohttp  # type: ignore

            self._session = aiohttp.ClientSession(
                headers={"X-Vault-Token": self.token}, timeout=aiohttp.ClientTimeout(total=10)
            )
        return self._session

    async def get_secret(self, key: str) -> Secret | None:
        """Retrieve secret from Vault."""
        try:
            session = await self._get_session()
            url = f"{self.url}/v1/{self.mount_path}/data/{key}"

            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.model_dump_json()
                    secret_data = data.get("data", {}).get("data", {})

                    return Secret(
                        key=key,
                        value=secret_data.get("value", ""),
                        version=str(data.get("data", {}).get("metadata", {}).get("version", "")),
                        metadata=secret_data.get("metadata", {}),
                    )
                else:
                    logger.warning(f"Vault request failed: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Error retrieving secret from Vault: {e}")
            return None

    async def list_secrets(self, prefix: str = "") -> list[str]:
        """List secrets from Vault."""
        try:
            session = await self._get_session()
            url = f"{self.url}/v1/{self.mount_path}/metadata/{prefix}"

            async with session.get(url, params={"list": "true"}) as response:
                if response.status == 200:
                    data = await response.model_dump_json()
                    keys = data.get("data", {}).get("keys", [])
                    return [str(k) for k in keys]
                else:
                    logger.warning(f"Vault list request failed: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Error listing secrets from Vault: {e}")
            return []

    async def refresh_secret(self, key: str) -> Secret | None:
        """Refresh secret from Vault."""
        return await self.get_secret(key)


class EnvironmentProvider(SecretsProvider):
    """Environment variable provider for development."""

    def __init__(self, prefix: str = "GRID_SECRET_"):
        self.prefix = prefix

    async def get_secret(self, key: str) -> Secret | None:
        """Get secret from environment variables."""
        env_key = f"{self.prefix}{key.upper()}"
        value = os.getenv(env_key)

        if value:
            return Secret(key=key, value=value, metadata={"source": "environment"})
        return None

    async def list_secrets(self, prefix: str = "") -> list[str]:
        """List secrets from environment variables."""
        secrets = []
        for key, _value in os.environ.items():
            if key.startswith(self.prefix):
                secret_key = key[len(self.prefix) :].lower()
                if not prefix or secret_key.startswith(prefix):
                    secrets.append(secret_key)
        return secrets

    async def refresh_secret(self, key: str) -> Secret | None:
        """Refresh secret from environment."""
        return await self.get_secret(key)


class SecretsManager:
    """Enhanced secrets manager with caching and rotation."""

    def __init__(self, provider: SecretsProvider, cache_ttl: int = 300):
        self.provider = provider
        self.cache_ttl = cache_ttl  # seconds
        self._cache: dict[str, tuple[Secret, datetime]] = {}
        self._failed_retrievals: dict[str, datetime] = {}

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached secret is still valid."""
        if key not in self._cache:
            return False

        secret, cached_at = self._cache[key]

        # Check expiration
        if secret.expires_at and datetime.now() >= secret.expires_at:
            return False

        # Check cache TTL
        if datetime.now() >= cached_at + timedelta(seconds=self.cache_ttl):
            return False

        return True

    def _should_retry(self, key: str) -> bool:
        """Check if we should retry a failed retrieval."""
        if key not in self._failed_retrievals:
            return True

        last_failure = self._failed_retrievals[key]
        retry_delay = min(300, 2 ** len(str(hash(key)) % 10))  # Exponential backoff

        return datetime.now() >= last_failure + timedelta(seconds=retry_delay)

    async def get_secret(self, key: str) -> Secret | None:
        """Get secret with caching and fallback."""
        # Check cache first
        if self._is_cache_valid(key):
            cached_secret, _ = self._cache[key]
            return cached_secret

        # Check if we should retry
        if not self._should_retry(key):
            logger.warning(f"Skipping secret retrieval for {key} - in backoff period")
            return None

        try:
            # Retrieve from provider
            secret: Secret | None = await self.provider.get_secret(key)

            if secret:
                # Cache the secret
                valid_secret: Secret = secret
                self._cache[key] = (valid_secret, datetime.now())

                # Clear failed retrieval if successful
                if key in self._failed_retrievals:
                    del self._failed_retrievals[key]

                logger.info(f"Successfully retrieved secret: {key}")
                return secret
            else:
                # Record failed retrieval
                self._failed_retrievals[key] = datetime.now()
                logger.warning(f"Failed to retrieve secret: {key}")
                return None

        except Exception as e:
            self._failed_retrievals[key] = datetime.now()
            logger.error(f"Error retrieving secret {key}: {e}")
            return None

    async def get_api_key(self, service: str) -> str | None:
        """Get API key for specific service."""
        secret_key = f"api_key_{service}"
        secret = await self.get_secret(secret_key)
        return secret.value if secret else None

    async def list_secrets(self, prefix: str = "") -> list[str]:
        """List available secrets."""
        return await self.provider.list_secrets(prefix)

    def clear_cache(self, key: str | None = None) -> None:
        """Clear cache for specific key or all secrets."""
        if key:
            self._cache.pop(key, None)
            self._failed_retrievals.pop(key, None)
        else:
            self._cache.clear()
            self._failed_retrievals.clear()

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return {
            "cached_secrets": len(self._cache),
            "failed_retrievals": len(self._failed_retrievals),
            "cache_ttl_seconds": self.cache_ttl,
        }


# Global secrets manager instance
_secrets_manager: SecretsManager | None = None


def get_secrets_manager() -> SecretsManager | None:
    """Get the global secrets manager instance."""
    return _secrets_manager


def initialize_secrets_manager(environment: str = "development") -> SecretsManager:
    """Initialize secrets manager based on environment."""
    global _secrets_manager

    provider: SecretsProvider | Any = None

    # Try local secrets manager first (for all environments)
    try:
        from .local_secrets_manager import LocalSecretsProvider

        provider = LocalSecretsProvider()
        logger.info("Initialized Local Secrets Manager provider")
    except ImportError:
        logger.warning("Local Secrets Manager not available")

    if environment == "production":
        # In production, also try GCP Secret Manager as additional layer
        try:
            from .gcp_secrets import get_gcp_provider

            gcp_provider = get_gcp_provider()
            if gcp_provider:
                # Create adapter to match SecretsProvider interface
                class GCPProviderAdapter(SecretsProvider):
                    def __init__(self, gcp_provider):
                        self.gcp = gcp_provider

                    async def get_secret(self, key: str) -> Secret | None:
                        try:
                            value = await self.gcp.get_secret(key)
                            return Secret(key=key, value=value, metadata={"source": "gcp"})
                        except Exception:
                            return None

                    async def list_secrets(self, prefix: str = "") -> list[str]:
                        return await self.gcp.list_secrets(prefix)

                    async def refresh_secret(self, key: str) -> Secret | None:
                        return await self.get_secret(key)

                # Use GCP as primary in production, local as fallback
                provider = GCPProviderAdapter(gcp_provider)
                logger.info("Initialized GCP Secret Manager provider (production mode)")
        except ImportError:
            logger.warning("GCP Secret Manager dependencies not available")
    else:
        # Development/staging: use local provider (already initialized above)
        pass

    _secrets_manager = SecretsManager(provider, cache_ttl=300)
    return _secrets_manager


async def get_api_key(service: str) -> str | None:
    """Convenience function to get API key for service."""
    manager = get_secrets_manager()
    if manager:
        return await manager.get_api_key(service)

    # Fallback to environment variables
    env_key = f"{service.upper()}_API_KEY"
    return os.getenv(env_key)
