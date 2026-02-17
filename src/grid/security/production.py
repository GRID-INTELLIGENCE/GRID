"""Production Security Configuration for GRID.

Provides production-hardened security settings and secrets management integration.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class Environment(Enum):
    """Deployment environments."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class SecurityLevel(Enum):
    """Security enforcement levels."""

    PERMISSIVE = "permissive"
    STANDARD = "standard"
    RESTRICTIVE = "restrictive"


@dataclass
class SecurityConfig:
    """Production security configuration."""

    # Environment settings
    environment: Environment
    security_level: SecurityLevel

    # Command controls
    denylisted_commands: list[str]
    min_contribution_score: float
    check_contribution: bool

    # Required environment variables
    required_env_vars: list[str]
    blocked_env_vars: list[str]

    # Secrets management
    use_secrets_manager: bool
    secrets_provider: str | None
    secrets_endpoint: str | None

    # Monitoring and audit
    enable_audit_logging: bool
    log_security_events: bool
    max_failed_attempts: int


class ProductionSecurityManager:
    """Manages production security settings and contracts."""

    # Production-hardened contribution scores
    CONTRIBUTION_SCORES: dict[str, float] = {
        "analyze": 0.85,  # Essential but resource-intensive
        "serve": 0.90,  # Critical infrastructure
        "process": 0.92,  # Core pipeline
        "skills": 0.88,  # High utility but varied risk
    }

    # Environment-specific security configurations
    SECURITY_CONFIGS = {
        Environment.DEVELOPMENT: SecurityConfig(
            environment=Environment.DEVELOPMENT,
            security_level=SecurityLevel.PERMISSIVE,
            denylisted_commands=[],
            min_contribution_score=0.0,
            check_contribution=False,
            required_env_vars=[],
            blocked_env_vars=[],
            use_secrets_manager=False,
            secrets_provider=None,
            secrets_endpoint=None,
            enable_audit_logging=False,
            log_security_events=False,
            max_failed_attempts=100,
        ),
        Environment.STAGING: SecurityConfig(
            environment=Environment.STAGING,
            security_level=SecurityLevel.STANDARD,
            denylisted_commands=["serve"],
            min_contribution_score=0.6,
            check_contribution=True,
            required_env_vars=["GRID_SESSIONS", "GRID_CONVERSATIONS"],
            blocked_env_vars=[],
            use_secrets_manager=True,
            secrets_provider="vault",
            secrets_endpoint=os.getenv("VAULT_ADDR"),
            enable_audit_logging=True,
            log_security_events=True,
            max_failed_attempts=10,
        ),
        Environment.PRODUCTION: SecurityConfig(
            environment=Environment.PRODUCTION,
            security_level=SecurityLevel.RESTRICTIVE,
            denylisted_commands=["serve"],
            min_contribution_score=0.8,
            check_contribution=True,
            required_env_vars=["GRID_SESSIONS", "GRID_CONVERSATIONS", "GRID_ENV"],
            blocked_env_vars=[],
            use_secrets_manager=True,
            secrets_provider="vault",
            secrets_endpoint=os.getenv("VAULT_ADDR"),
            enable_audit_logging=True,
            log_security_events=True,
            max_failed_attempts=3,
        ),
    }

    def __init__(self, environment: Environment | None = None):
        self.environment = environment or self._detect_environment()
        self.config = self.SECURITY_CONFIGS[self.environment]
        self._failed_attempts = 0

    def _detect_environment(self) -> Environment:
        """Detect current environment from variables."""
        env_var = os.getenv("GRID_ENV", "development").lower()

        if env_var == "production":
            return Environment.PRODUCTION
        elif env_var == "staging":
            return Environment.STAGING
        else:
            return Environment.DEVELOPMENT

    def validate_environment(self) -> dict[str, Any]:
        """Validate environment meets security requirements."""
        issues = []
        warnings = []

        # Check required environment variables
        for var in self.config.required_env_vars:
            if not os.getenv(var):
                issues.append(f"Missing required environment variable: {var}")

        # Check for blocked environment variables
        for var in self.config.blocked_env_vars:
            if os.getenv(var):
                issues.append(f"Blocked environment variable is set: {var}")

        # Check secrets management
        if self.config.use_secrets_manager:
            if not self.config.secrets_endpoint:
                warnings.append("Secrets manager enabled but endpoint not configured")

        # Check for API keys in environment (security risk)
        api_keys = [k for k in os.environ.keys() if "API_KEY" in k or "TOKEN" in k]
        if api_keys and self.config.environment != Environment.DEVELOPMENT:
            warnings.append(f"API keys detected in environment: {api_keys}")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "environment": self.environment.value,
            "security_level": self.config.security_level.value,
        }

    def get_command_score(self, command: str) -> float:
        """Get contribution score for command."""
        return self.CONTRIBUTION_SCORES.get(command, 0.5)

    def is_command_allowed(self, command: str) -> tuple[bool, str | None]:
        """Check if command is allowed under current security config."""
        # Check denylist
        if command in self.config.denylisted_commands:
            return False, f"Command '{command}' is denylisted in {self.environment.value}"

        # Check contribution score
        if self.config.check_contribution:
            score = self.get_command_score(command)
            if score < self.config.min_contribution_score:
                return (
                    False,
                    f"Command '{command}' score {score:.2f} below threshold {self.config.min_contribution_score:.2f}",
                )

        # Check failed attempts
        if self._failed_attempts >= self.config.max_failed_attempts:
            return False, "Maximum failed attempts exceeded"

        return True, None

    def record_failed_attempt(self) -> None:
        """Record a failed security attempt."""
        self._failed_attempts += 1

        if self.config.log_security_events:
            logger.warning(
                f"Security attempt failed ({self._failed_attempts}/{self.config.max_failed_attempts}) "
                f"in {self.environment.value}"
            )

    def reset_failed_attempts(self) -> None:
        """Reset failed attempts counter."""
        self._failed_attempts = 0

    def get_environment_config(self) -> dict[str, Any]:
        """Get current environment configuration for display."""
        return {
            "environment": self.config.environment.value,
            "security_level": self.config.security_level.value,
            "denylisted_commands": self.config.denylisted_commands,
            "min_contribution_score": self.config.min_contribution_score,
            "check_contribution": self.config.check_contribution,
            "use_secrets_manager": self.config.use_secrets_manager,
            "secrets_provider": self.config.secrets_provider,
            "enable_audit_logging": self.config.enable_audit_logging,
            "max_failed_attempts": self.config.max_failed_attempts,
        }


# Global security manager instance
security_manager = ProductionSecurityManager()
