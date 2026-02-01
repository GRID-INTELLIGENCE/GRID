"""
GCP Secret Manager Integration for GRID.

Provides secure secrets retrieval from Google Cloud Secret Manager.
Follows cloud-native security practices with automatic rotation.
"""

import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SecretMetadata:
    """Metadata for a secret."""

    name: str
    version: str
    created_date: str
    rotation_enabled: bool
    rotation_frequency: str


class CloudSecretsProvider(ABC):
    """Abstract base class for cloud secrets providers."""

    @abstractmethod
    async def get_secret(self, secret_name: str, version: str | None = None) -> str:
        """Retrieve secret value."""
        pass

    @abstractmethod
    async def get_secret_metadata(self, secret_name: str) -> SecretMetadata:
        """Get secret metadata including rotation info."""
        pass

    @abstractmethod
    async def list_secrets(self, prefix: str = "") -> list[str]:
        """List available secrets."""
        pass


class GCPSecretsProvider(CloudSecretsProvider):
    """GCP Secret Manager provider."""

    def __init__(self, project_id: str = None):
        try:
            from google.cloud import secretmanager  # type: ignore[import-untyped]

            self.client = secretmanager.SecretManagerServiceAsyncClient()
            self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
            if not self.project_id:
                raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is required")
            logger.info(f"Initialized GCP Secret Manager provider for project: {self.project_id}")
        except ImportError:
            raise ImportError("google-cloud-secret-manager package required for GCP Secret Manager")

    async def get_secret(self, secret_name: str, version: str | None = None) -> str:
        """Get secret from GCP Secret Manager."""
        try:
            full_name = f"projects/{self.project_id}/secrets/{secret_name}"
            if version:
                full_name += f"/versions/{version}"
            else:
                full_name += "/versions/latest"

            response = await self.client.access_secret_version(name=full_name)
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logger.error(f"Failed to get secret {secret_name}: {e}")
            raise

    async def get_secret_metadata(self, secret_name: str) -> SecretMetadata:
        """Get secret metadata from GCP."""
        try:
            full_name = f"projects/{self.project_id}/secrets/{secret_name}"
            response = await self.client.get_secret(name=full_name)
            return SecretMetadata(
                name=response.name.split("/")[-1],
                version=response.version_id,
                created_date=response.create_time.isoformat(),
                rotation_enabled=response.rotation is not None,
                rotation_frequency=response.rotation.period if response.rotation else "disabled",
            )
        except Exception as e:
            logger.error(f"Failed to get metadata for {secret_name}: {e}")
            raise

    async def list_secrets(self, prefix: str = "") -> list[str]:
        """List secrets from GCP."""
        try:
            parent = f"projects/{self.project_id}"
            secrets = []
            async for secret in self.client.list_secrets(parent=parent):
                if not prefix or secret.name.startswith(prefix):
                    secrets.append(secret.name)
            return secrets
        except Exception as e:
            logger.error(f"Failed to list secrets: {e}")
            raise


def get_gcp_provider() -> GCPSecretsProvider | None:
    """Auto-detect and initialize GCP secrets provider."""
    # Check for GCP credentials
    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv("GOOGLE_CLOUD_PROJECT"):
        return GCPSecretsProvider()

    logger.warning("GCP credentials not detected")
    return None


async def get_secret(secret_name: str, required: bool = True) -> str | None:
    """
    Get secret from GCP Secret Manager or environment variables.

    Priority:
    1. GCP Secret Manager
    2. Environment variables (development only)
    """
    provider = get_gcp_provider()

    if provider:
        try:
            return await provider.get_secret(secret_name)
        except Exception as e:
            environment = os.getenv("MOTHERSHIP_ENVIRONMENT", "development").lower()
            if environment == "production":
                raise ValueError(f"Required secret {secret_name} not found in GCP Secret Manager: {e}")

    # Fallback to environment variables (development only)
    value = os.getenv(secret_name)
    if required and not value:
        environment = os.getenv("MOTHERSHIP_ENVIRONMENT", "development").lower()
        if environment == "production":
            raise ValueError(f"Required secret {secret_name} not found and GCP Secret Manager not available")
        raise ValueError(f"Required secret {secret_name} not found in environment variables")
    return value


# Load configuration from YAML
def load_secrets_config() -> dict:
    """Load secrets manager configuration."""
    config_path = Path(__file__).parent.parent.parent.parent / "config" / "secrets_manager.yaml"

    if config_path.exists():
        import yaml  # type: ignore[import-untyped]

        with open(config_path) as f:
            return yaml.safe_load(f)

    # Default configuration
    return {
        "provider": {"type": "gcp", "allow_fallback": False},
        "gcp": {"project_id": os.getenv("GOOGLE_CLOUD_PROJECT"), "prefix": "grid-production-"},
    }
