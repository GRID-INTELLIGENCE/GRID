"""
Centralized environment management for GRID.

Handles loading, validation, and secure access to environment variables using Pydantic.
"""

import logging
import os
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class EnvironmentSettings(BaseSettings):
    """Defines and validates environment variables for the GRID application."""

    # Environment Configuration
    MOTHERSHIP_ENVIRONMENT: Literal["development", "staging", "production", "test"] = Field(
        default="development", description="The runtime environment for the application."
    )

    # GCP Configuration
    GOOGLE_CLOUD_PROJECT: str | None = Field(
        default=None, description="Google Cloud project ID, required for production secrets."
    )

    # Logging Configuration
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="The log level for the application."
    )

    # Model Configuration
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def is_production(self) -> bool:
        """Returns True if the environment is production."""
        return self.MOTHERSHIP_ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        """Returns True if the environment is development."""
        return self.MOTHERSHIP_ENVIRONMENT == "development"


@lru_cache
def get_environment_settings() -> EnvironmentSettings:
    """
    Loads, validates, and returns the environment settings.

    Uses a cached instance to avoid repeated file I/O and validation.
    """
    try:
        settings = EnvironmentSettings()
        if settings.is_production and not settings.GOOGLE_CLOUD_PROJECT:
            raise ValueError("GOOGLE_CLOUD_PROJECT must be set in a production environment.")
        logger.info(f"Environment loaded successfully for: {settings.MOTHERSHIP_ENVIRONMENT}")
        return settings
    except Exception as e:
        logger.critical(f"Failed to load environment settings: {e}")
        raise


# Initialize and export a singleton instance
environment_settings = get_environment_settings()


def sanitize_environment() -> dict[str, list[str]]:
    """
    Sanitize the current process environment variables.

    Scans ``os.environ`` for keys with suspicious characters and removes them.
    Returns a report mapping category names to lists of messages describing
    changes that were made.
    """
    report: dict[str, list[str]] = {"removed": [], "warnings": []}
    keys_to_remove: list[str] = []
    for key in os.environ:
        # Allow only alphanumeric, underscores, and dots in env-var names
        if not key.replace("_", "").replace(".", "").isalnum():
            keys_to_remove.append(key)

    for key in keys_to_remove:
        logger.warning(f"Removing potentially unsafe environment key: {key}")
        report["removed"].append(key)
        del os.environ[key]

    # Deduplicate PATH entries while preserving order
    raw_path = os.environ.get("PATH", "")
    if raw_path:
        seen: set[str] = set()
        deduped: list[str] = []
        for entry in raw_path.split(os.pathsep):
            normed = os.path.normpath(entry) if entry else entry
            if normed not in seen:
                seen.add(normed)
                deduped.append(normed)
        os.environ["PATH"] = os.pathsep.join(deduped)

    return report


def sanitize_path() -> None:
    """
    Sanitize the ``PATH`` environment variable in-place.

    Removes non-existent directories and normalises every entry.
    """
    raw = os.environ.get("PATH", "")
    entries = raw.split(os.pathsep)
    cleaned: list[str] = []
    for entry in entries:
        normed = os.path.normpath(entry)
        if os.path.isdir(normed):
            cleaned.append(normed)
        else:
            logger.debug(f"Removing non-existent PATH entry: {entry}")
    os.environ["PATH"] = os.pathsep.join(cleaned)
