"""
Environment settings for main GRID codebase
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Literal

class EnvironmentSettings(BaseSettings):
    """Basic environment settings for GRID"""

    # Environment Configuration
    MOTHERSHIP_ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    # GCP Configuration
    GOOGLE_CLOUD_PROJECT: str | None = None

    # Logging Configuration
    LOG_LEVEL: str | None = "INFO"

    @field_validator('LOG_LEVEL')
    @classmethod
    def validate_log_level(cls, v):
        if v is None:
            return "INFO"  # Default value
        v_upper = v.upper()
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v_upper not in valid_levels:
            raise ValueError(f'LOG_LEVEL must be one of {valid_levels}')
        return v_upper

    @field_validator('GOOGLE_CLOUD_PROJECT')
    @classmethod
    def validate_gcp_project(cls, v):
        if v is not None and not v.strip():
            raise ValueError('GOOGLE_CLOUD_PROJECT cannot be empty string')
        return v

# Create singleton instance
environment_settings = EnvironmentSettings()
