"""
Environment settings for main GRID codebase
"""

from pydantic_settings import BaseSettings
from typing import Literal

class EnvironmentSettings(BaseSettings):
    """Basic environment settings for GRID"""

    # Environment Configuration
    MOTHERSHIP_ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    # GCP Configuration
    GOOGLE_CLOUD_PROJECT: str | None = None

    # Logging Configuration
    LOG_LEVEL: str = "INFO"

# Create singleton instance
environment_settings = EnvironmentSettings()
