"""Pool Settings Configuration Module.

Provides centralized configuration for WorkerPool and ComponentPool,
replacing hardcoded values with environment-variable-driven settings.
Supports timestamp-based naming patterns for component IDs.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class NamingPattern(StrEnum):
    """Predefined naming patterns for component IDs."""

    SIMPLE = "{type}_{index}"  # worker_0, processor_1
    TIMESTAMP = "{type}_{timestamp}_{index}"  # worker_20250308_001_0
    TIMESTAMP_ONLY = "{type}_{timestamp}"  # worker_20250308_001


@dataclass
class PoolSettings:
    """
    Configuration for WorkerPool and ComponentPool.

    All values default to pre-refactor hardcoded values for backward compatibility.
    """

    # Pool sizing
    worker_min: int = 2
    worker_max: int = 20
    component_min: int = 2
    component_max: int = 20

    # Operational intervals (seconds)
    health_check_interval: int = 30
    idle_timeout_seconds: int = 60

    # Naming configuration
    naming_pattern: str = "{type}_{index}"
    naming_include_timestamp: bool = False
    naming_timestamp_format: str = "%Y%m%d_%H%M%S"

    @classmethod
    def from_env(cls) -> PoolSettings:
        """Load pool settings from environment variables."""
        env = os.environ

        def _parse_int(key: str, default: int) -> int:
            try:
                return int(env.get(key, str(default)))
            except ValueError:
                return default

        def _parse_bool(key: str, default: bool = False) -> bool:
            value = env.get(key, "").lower()
            if not value:
                return default
            return value in ("true", "1", "yes", "y", "on")

        # Parse pattern with timestamp support
        naming_pattern = env.get("MOTHERSHIP_COMPONENT_NAMING_PATTERN", "{type}_{index}")
        include_timestamp = _parse_bool("MOTHERSHIP_COMPONENT_NAMING_TIMESTAMP")

        # If timestamp enabled but pattern doesn't include it, append it
        if include_timestamp and "{timestamp}" not in naming_pattern:
            # Insert timestamp before index
            naming_pattern = naming_pattern.replace("_{index}", "_{timestamp}_{index}")

        return cls(
            worker_min=_parse_int("MOTHERSHIP_WORKER_MIN", 2),
            worker_max=_parse_int("MOTHERSHIP_WORKER_MAX", 20),
            component_min=_parse_int("MOTHERSHIP_COMPONENT_MIN", 2),
            component_max=_parse_int("MOTHERSHIP_COMPONENT_MAX", 20),
            health_check_interval=_parse_int("MOTHERSHIP_HEALTH_CHECK_INTERVAL", 30),
            idle_timeout_seconds=_parse_int("MOTHERSHIP_IDLE_TIMEOUT", 60),
            naming_pattern=naming_pattern,
            naming_include_timestamp=include_timestamp,
            naming_timestamp_format=env.get(
                "MOTHERSHIP_COMPONENT_NAMING_TIMESTAMP_FORMAT", "%Y%m%d_%H%M%S"
            ),
        )

    def validate(self) -> list[str]:
        """Validate pool settings and return list of issues."""
        issues = []

        if self.worker_min >= self.worker_max:
            issues.append(
                f"worker_min ({self.worker_min}) must be less than worker_max ({self.worker_max})"
            )
        if self.component_min >= self.component_max:
            issues.append(
                f"component_min ({self.component_min}) must be less than component_max ({self.component_max})"
            )
        if self.worker_min < 1:
            issues.append(f"worker_min ({self.worker_min}) must be at least 1")
        if self.component_min < 1:
            issues.append(f"component_min ({self.component_min}) must be at least 1")
        if self.health_check_interval < 1:
            issues.append(f"health_check_interval ({self.health_check_interval}) must be positive")
        if self.idle_timeout_seconds < 1:
            issues.append(f"idle_timeout_seconds ({self.idle_timeout_seconds}) must be positive")

        # Validate pattern contains required placeholders
        if "{index}" not in self.naming_pattern:
            issues.append("naming_pattern must contain {index} placeholder")
        if "{type}" not in self.naming_pattern:
            issues.append("naming_pattern must contain {type} placeholder")

        return issues

    def generate_component_id(
        self,
        component_type: str,
        index: int,
        timestamp: datetime | None = None,
    ) -> str:
        """Generate a component ID using the configured naming pattern."""
        if timestamp is None and self.naming_include_timestamp:
            timestamp = datetime.now()

        ts_str = timestamp.strftime(self.naming_timestamp_format) if timestamp else ""

        return self.naming_pattern.format(
            type=component_type,
            index=index,
            timestamp=ts_str,
        )

    def generate_worker_id(self, index: int, timestamp: datetime | None = None) -> str:
        """Generate a worker ID using the configured naming pattern."""
        return self.generate_component_id("worker", index, timestamp)
