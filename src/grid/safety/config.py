"""GRID Safety Configuration.

Centralizes configuration for guardrails, denylists, and environment blockers.
"""

from __future__ import annotations

import os

from pydantic import BaseModel, Field


class SafetyConfig(BaseModel):
    """Configuration for CLI safety mechanisms."""

    denylist: list[str] = Field(default_factory=list)
    blocked_env_vars: list[str] = Field(default_factory=list)
    required_env_vars: list[str] = Field(default_factory=list)
    contribution_threshold: float = 0.5
    check_contribution: bool = True

    @classmethod
    def from_env(cls) -> SafetyConfig:
        """Load configuration from environment variables."""
        return cls(
            denylist=[c.strip() for c in os.getenv("GRID_COMMAND_DENYLIST", "").split(",") if c.strip()],
            blocked_env_vars=[v.strip() for v in os.getenv("GRID_BLOCKED_ENV_VARS", "").split(",") if v.strip()],
            required_env_vars=[v.strip() for v in os.getenv("GRID_REQUIRED_ENV_VARS", "").split(",") if v.strip()],
            contribution_threshold=float(os.getenv("GRID_MIN_CONTRIBUTION", "0.5")),
            check_contribution=os.getenv("GRID_CHECK_CONTRIBUTION", "1") == "1",
        )


# Global config instance
safety_config = SafetyConfig.from_env()
