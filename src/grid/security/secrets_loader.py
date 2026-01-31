"""
Secure Secrets Management Module
================================

Centralized secrets loading with security best practices:
- Environment variable loading with validation
- GCP Secret Manager integration
- No hardcoded defaults for sensitive values
- Audit logging for secret access
- Secret strength validation

Usage:
    from grid.security.secrets_loader import get_secret, SecretManager

    # Simple usage
    api_key = get_secret("OPENAI_API_KEY")

    # With SecretManager for more control
    secrets = SecretManager()
    stripe_key = secrets.get("STRIPE_API_KEY", required=True)
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SecretSource(Enum):
    """Source of the secret value."""

    ENVIRONMENT = "environment"
    GCP_SECRET_MANAGER = "gcp_secret_manager"
    LOCAL_FILE = "local_file"
    NOT_FOUND = "not_found"


class SecretValidationError(Exception):
    """Raised when a secret fails validation."""

    pass


class SecretNotFoundError(Exception):
    """Raised when a required secret is not found."""

    pass


@dataclass
class SecretMetadata:
    """Metadata about a retrieved secret."""

    name: str
    source: SecretSource
    retrieved_at: datetime
    is_valid: bool
    validation_errors: list[str] = field(default_factory=list)
    # Never store the actual value in metadata!


@dataclass
class SecretConfig:
    """Configuration for secret retrieval."""

    # Minimum length for secrets (excluding specific overrides)
    min_length: int = 16

    # Allow fallback to environment variables if GCP fails
    allow_env_fallback: bool = True

    # GCP Secret Manager settings
    gcp_project_id: str | None = None
    gcp_secret_prefix: str = "grid-"

    # Local development settings
    allow_local_file: bool = False
    local_secrets_path: Path | None = None

    # Validation settings
    reject_weak_patterns: list[str] = field(
        default_factory=lambda: [
            "password",
            "secret",
            "123456",
            "test",
            "default",
            "changeme",
            "admin",
            "example",
            "placeholder",
        ]
    )

    # Audit settings
    audit_access: bool = True


# Well-known secret patterns and their minimum lengths
SECRET_PATTERNS: dict[str, dict[str, Any]] = {
    "STRIPE_API_KEY": {"prefix": "sk_", "min_length": 32},
    "OPENAI_API_KEY": {"prefix": "sk-", "min_length": 40},
    "GITHUB_TOKEN": {"prefix": "ghp_", "min_length": 36},
    "GITHUB_PAT": {"prefix": "ghp_", "min_length": 36},
    "DATABRICKS_TOKEN": {"prefix": "dapi", "min_length": 32},
    "GCP_API_KEY": {"min_length": 32},
    "MISTRAL_API_KEY": {"min_length": 32},
    "GEMINI_API_KEY": {"min_length": 32},
    "JWT_SECRET": {"min_length": 32},
    "ENCRYPTION_KEY": {"min_length": 32},
}


class SecretManager:
    """
    Secure secret management with multiple backends.

    Priority order:
    1. GCP Secret Manager (production)
    2. Environment variables
    3. Local secrets file (development only)
    """

    def __init__(self, config: SecretConfig | None = None):
        self.config = config or SecretConfig()
        self._cache: dict[str, tuple[str, SecretMetadata]] = {}
        self._access_log: list[dict[str, Any]] = []
        self._gcp_client: Any = None

    def get(
        self,
        name: str,
        required: bool = True,
        validate: bool = True,
        default: str | None = None,
    ) -> str | None:
        """
        Retrieve a secret by name.

        Args:
            name: The secret name (e.g., "OPENAI_API_KEY")
            required: If True, raises SecretNotFoundError when not found
            validate: If True, validates secret strength
            default: Default value if not found (only for non-required secrets)

        Returns:
            The secret value or None if not found and not required

        Raises:
            SecretNotFoundError: If required secret is not found
            SecretValidationError: If secret fails validation
        """
        # Check cache first
        if name in self._cache:
            cached_value, metadata = self._cache[name]
            self._log_access(name, metadata.source, cached=True)
            return cached_value

        # Try each source in priority order
        value, source = self._retrieve_secret(name)

        if value is None:
            if required and default is None:
                raise SecretNotFoundError(
                    f"Required secret '{name}' not found. "
                    f"Set the {name} environment variable or configure GCP Secret Manager."
                )
            if default is not None:
                logger.warning(
                    f"Secret '{name}' not found, using provided default. This should only be used in development."
                )
                return default
            return None

        # Validate if requested
        metadata = SecretMetadata(
            name=name,
            source=source,
            retrieved_at=datetime.now(UTC),
            is_valid=True,
        )

        if validate:
            validation_errors = self._validate_secret(name, value)
            if validation_errors:
                metadata.is_valid = False
                metadata.validation_errors = validation_errors
                error_msg = f"Secret '{name}' failed validation: {'; '.join(validation_errors)}"
                logger.error(error_msg)
                raise SecretValidationError(error_msg)

        # Cache and log
        self._cache[name] = (value, metadata)
        self._log_access(name, source, cached=False)

        return value

    def _retrieve_secret(self, name: str) -> tuple[str | None, SecretSource]:
        """Try to retrieve secret from available sources."""
        # 1. Try GCP Secret Manager first (production)
        if self.config.gcp_project_id:
            value = self._get_from_gcp(name)
            if value:
                return value, SecretSource.GCP_SECRET_MANAGER

        # 2. Try environment variable
        value = os.environ.get(name)
        if value:
            return value, SecretSource.ENVIRONMENT

        # 3. Try local secrets file (development only)
        if self.config.allow_local_file and self.config.local_secrets_path:
            value = self._get_from_local_file(name)
            if value:
                logger.warning(f"Loaded secret '{name}' from local file. This should NEVER be used in production!")
                return value, SecretSource.LOCAL_FILE

        return None, SecretSource.NOT_FOUND

    def _get_from_gcp(self, name: str) -> str | None:
        """Retrieve secret from GCP Secret Manager."""
        try:
            if self._gcp_client is None:
                from google.cloud import secretmanager

                self._gcp_client = secretmanager.SecretManagerServiceClient()

            # Build the resource name
            secret_name = f"{self.config.gcp_secret_prefix}{name.lower().replace('_', '-')}"
            resource_name = f"projects/{self.config.gcp_project_id}/secrets/{secret_name}/versions/latest"

            response = self._gcp_client.access_secret_version(name=resource_name)
            return response.payload.data.decode("UTF-8")

        except ImportError:
            logger.debug("GCP Secret Manager client not available")
            return None
        except Exception as e:
            logger.debug(f"GCP Secret Manager retrieval failed for '{name}': {e}")
            return None

    def _get_from_local_file(self, name: str) -> str | None:
        """Retrieve secret from local file (development only)."""
        if not self.config.local_secrets_path:
            return None

        secrets_file = Path(self.config.local_secrets_path)
        if not secrets_file.exists():
            return None

        try:
            with open(secrets_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("#") or "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    if key.strip() == name:
                        return value.strip().strip("\"'")
        except Exception as e:
            logger.error(f"Failed to read local secrets file: {e}")

        return None

    def _validate_secret(self, name: str, value: str) -> list[str]:
        """Validate secret strength and format."""
        errors: list[str] = []

        # Get pattern-specific requirements
        pattern_config = SECRET_PATTERNS.get(name, {})
        min_length = pattern_config.get("min_length", self.config.min_length)
        expected_prefix = pattern_config.get("prefix")

        # Check minimum length
        if len(value) < min_length:
            errors.append(f"Secret too short (minimum {min_length} characters)")

        # Check expected prefix
        if expected_prefix and not value.startswith(expected_prefix):
            errors.append(f"Secret should start with '{expected_prefix}'")

        # Check for weak patterns
        value_lower = value.lower()
        for weak_pattern in self.config.reject_weak_patterns:
            if weak_pattern in value_lower:
                errors.append(f"Secret contains weak pattern: '{weak_pattern}'")

        # Check entropy (basic check - at least some variety)
        if len(set(value)) < min(8, len(value) // 2):
            errors.append("Secret has low entropy (too repetitive)")

        return errors

    def _log_access(self, name: str, source: SecretSource, cached: bool) -> None:
        """Log secret access for audit purposes."""
        if not self.config.audit_access:
            return

        # Never log the actual secret value!
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "secret_name": name,
            "source": source.value,
            "cached": cached,
            "pid": os.getpid(),
        }
        self._access_log.append(entry)

        # Keep log bounded
        if len(self._access_log) > 1000:
            self._access_log = self._access_log[-500:]

    def get_access_log(self) -> list[dict[str, Any]]:
        """Get the audit log of secret accesses."""
        return self._access_log.copy()

    def clear_cache(self) -> None:
        """Clear the secret cache."""
        self._cache.clear()


# Global singleton instance
_default_manager: SecretManager | None = None


def get_secret_manager() -> SecretManager:
    """Get or create the default SecretManager instance."""
    global _default_manager
    if _default_manager is None:
        # Configure based on environment
        config = SecretConfig(
            gcp_project_id=os.environ.get("GOOGLE_CLOUD_PROJECT"),
            allow_local_file=os.environ.get("GRID_ENV", "development") == "development",
        )
        _default_manager = SecretManager(config)
    return _default_manager


def get_secret(
    name: str,
    required: bool = True,
    validate: bool = True,
    default: str | None = None,
) -> str | None:
    """
    Convenience function to retrieve a secret.

    Args:
        name: The secret name (e.g., "OPENAI_API_KEY")
        required: If True, raises SecretNotFoundError when not found
        validate: If True, validates secret strength
        default: Default value if not found (only for non-required secrets)

    Returns:
        The secret value or None if not found and not required
    """
    return get_secret_manager().get(name, required=required, validate=validate, default=default)


def mask_secret(value: str, visible_chars: int = 4) -> str:
    """
    Mask a secret value for safe logging.

    Args:
        value: The secret value to mask
        visible_chars: Number of characters to show at start and end

    Returns:
        Masked string like "sk-pr...j0veoA"
    """
    if not value:
        return "***"
    if len(value) <= visible_chars * 2:
        return "*" * len(value)
    return f"{value[:visible_chars]}...{value[-visible_chars:]}"


def validate_secret_strength(value: str, name: str | None = None) -> tuple[bool, list[str]]:
    """
    Validate a secret's strength without storing it.

    Args:
        value: The secret value to validate
        name: Optional secret name for pattern-specific validation

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    manager = SecretManager()
    errors = manager._validate_secret(name or "GENERIC", value)
    return len(errors) == 0, errors


# Path resolution helpers
def get_project_root() -> Path:
    """Get the project root directory from environment or detection."""
    # Check environment variable first
    if env_root := os.environ.get("GRID_PROJECT_ROOT"):
        return Path(env_root)

    # Try to detect from current file location
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
            return parent

    # Fallback to current directory
    return Path.cwd()


def get_config_path(filename: str) -> Path:
    """Get a configuration file path relative to project root."""
    return get_project_root() / "config" / filename


def get_logs_path(filename: str | None = None) -> Path:
    """Get a logs directory path, creating if needed."""
    logs_dir = get_project_root() / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    if filename:
        return logs_dir / filename
    return logs_dir


def get_data_path(filename: str | None = None) -> Path:
    """Get a data directory path, creating if needed."""
    data_dir = get_project_root() / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    if filename:
        return data_dir / filename
    return data_dir
