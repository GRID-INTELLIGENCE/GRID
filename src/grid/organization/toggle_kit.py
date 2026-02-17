"""Boolean toggle kit for architectural feature flags.

Enhanced with:
- Feature dependencies (features can require other features)
- Rollout percentages for gradual deployment
- Audit logging for change tracking
- Validation for configuration integrity
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class FeatureDefinition:
    """Complete feature definition with metadata."""

    name: str
    enabled: bool = False
    description: str = ""
    rollout_percentage: float = 0.0  # 0.0 to 100.0
    dependencies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class ToggleChange:
    """Record of a toggle change for audit purposes."""

    feature_name: str
    old_value: bool
    new_value: bool
    timestamp: str
    source: str  # "environment", "api", "file", "unknown"
    user: str | None = None


class ToggleKit:
    """Manages boolean toggles for enabling/disabling architectural features.

    Features:
    - Basic boolean toggles
    - Feature dependencies
    - Rollout percentages
    - Audit logging
    - Validation
    """

    DEFAULT_CONFIG_PATH = Path(__file__).parents[3] / "schemas" / "feature_toggles.json"

    def __init__(self, config_path: str | None = None, audit_log_path: str | None = None):
        if config_path is None:
            self.config_path = self.DEFAULT_CONFIG_PATH
        else:
            self.config_path = Path(config_path)

        self.audit_log_path = str(self.config_path.parent / "toggle_audit.log")

        self.toggles: dict[str, bool] = self._load_toggles()
        self.feature_definitions: dict[str, FeatureDefinition] = {}
        self.audit_log: list[ToggleChange] = []

        self._load_audit_log()

    def _load_toggles(self) -> dict[str, bool]:
        """Load toggles from configuration file."""
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    config_data = json.load(f)

                # Parse feature definitions if present
                if isinstance(config_data, dict):
                    # Check if new format with feature definitions
                    if "features" in config_data:
                        self._parse_feature_definitions(config_data["features"])
                        return config_data.get("toggles", {})
                    else:
                        # Legacy format: direct boolean toggles
                        self.toggles = {k: bool(v) for k, v in config_data.items() if k != "features"}

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse toggles file {self.config_path}: {e}")
                self.toggles = {}
            except Exception as e:
                logger.error(f"Error loading toggles: {e}")
                self.toggles = {}
        else:
            logger.info(f"Toggles file not found at {self.config_path}, using defaults")
            self.toggles = {}

    def _parse_feature_definitions(self, features_data: dict[str, Any]) -> None:
        """Parse feature definitions from configuration."""
        now = datetime.now(UTC).isoformat()

        for name, config in features_data.items():
            if isinstance(config, bool):
                # Simple boolean format
                self.feature_definitions[name] = FeatureDefinition(
                    name=name, enabled=config, created_at=now, updated_at=now
                )
            elif isinstance(config, dict):
                # Full definition format
                self.feature_definitions[name] = FeatureDefinition(
                    name=name,
                    enabled=config.get("enabled", False),
                    description=config.get("description", ""),
                    rollout_percentage=config.get("rollout_percentage", 0.0),
                    dependencies=config.get("dependencies", []),
                    metadata=config.get("metadata", {}),
                    created_at=now,
                    updated_at=now,
                )

    def _load_audit_log(self) -> None:
        """Load audit log from file."""
        audit_file = Path(self.audit_log_path)
        if audit_file.exists():
            try:
                with open(audit_file) as f:
                    for line in f.readlines():
                        if line.strip():
                            entry = json.loads(line)
                            self.audit_log.append(ToggleChange(**entry))
            except Exception as e:
                logger.warning(f"Failed to load audit log: {e}")

    def _save_toggles(self) -> None:
        """Persist toggles to configuration file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Merge current toggles with feature definitions
        config_data = {
            "features": {
                name: {
                    "enabled": feat.enabled,
                    "description": feat.description,
                    "rollout_percentage": feat.rollout_percentage,
                    "dependencies": feat.dependencies,
                    "metadata": feat.metadata,
                    "created_at": feat.created_at,
                    "updated_at": feat.updated_at,
                }
                for name, feat in self.feature_definitions.items()
            },
            "toggles": self.toggles,
        }

        with open(self.config_path, "w") as f:
            json.dump(config_data, f, indent=2)

    def _save_audit_log(self) -> None:
        """Persist audit log to file."""
        audit_file = Path(self.audit_log_path)
        audit_file.parent.mkdir(parents=True, exist_ok=True)

        with open(audit_file, "a") as f:
            for change in self.audit_log[-100:]:  # Keep last 100 entries
                f.write(
                    json.dumps(
                        {
                            "feature_name": change.feature_name,
                            "old_value": change.old_value,
                            "new_value": change.new_value,
                            "timestamp": change.timestamp,
                            "source": change.source,
                            "user": change.user,
                        }
                    )
                    + "\n"
                )

    def _log_change(self, feature_name: str, old_value: bool, new_value: bool, source: str = "unknown") -> None:
        """Log a toggle change for audit purposes."""
        change = ToggleChange(
            feature_name=feature_name,
            old_value=old_value,
            new_value=new_value,
            timestamp=datetime.now(UTC).isoformat(),
            source=source,
            user=os.getenv("USER") or os.getenv("USERNAME"),
        )
        self.audit_log.append(change)
        self._save_audit_log()

    def _check_dependencies(self, feature_name: str, value: bool) -> tuple[bool, list[str]]:
        """Check if feature dependencies are satisfied."""
        if not value:
            return True, []  # Disabling doesn't require dependencies

        if feature_name not in self.feature_definitions:
            return True, []  # Unknown features don't have tracked dependencies

        deps = self.feature_definitions[feature_name].dependencies
        missing = [dep for dep in deps if not self.is_enabled(dep)]

        return len(missing) == 0, missing

    def is_enabled(self, feature_name: str, default: bool = False, context: dict[str, Any] | None = None) -> bool:
        """Check if a feature toggle is enabled.

        Args:
            feature_name: Name of the feature to check
            default: Default value if feature is not defined
            context: Optional context for rollout percentage calculation

        Returns:
            True if feature is enabled, False otherwise
        """
        # Check if feature exists in definitions
        if feature_name in self.feature_definitions:
            feature = self.feature_definitions[feature_name]

            # Check dependencies first
            deps_ok, missing = self._check_dependencies(feature_name, feature.enabled)
            if not deps_ok:
                logger.debug(f"Feature {feature_name} disabled: missing dependencies {missing}")
                return False

            # Check rollout percentage
            if feature.rollout_percentage > 0 and feature.rollout_percentage < 100:
                return self._is_in_rollout(feature_name, context)

            return feature.enabled

        # Fall back to simple toggle for legacy support
        return self.toggles.get(feature_name, default)

    def _is_in_rollout(self, feature_name: str, context: dict[str, Any] | None = None) -> bool:
        """Determine if a user/context is in the rollout percentage."""
        # Use context identifier (user_id, session_id, etc.) for consistent rollout
        identifier = context.get("user_id") if context else "default"
        if not identifier:
            import hashlib

            identifier = hashlib.md5(str(id(context)).encode()).hexdigest()[:8]  # noqa: S324 non-cryptographic use

        # Simple hash-based rollout
        import hashlib

        hash_value = int(hashlib.md5(f"{feature_name}:{identifier}".encode()).hexdigest()[:8], 16)  # noqa: S324 non-cryptographic use
        rollout_threshold = int(
            (feature_name in self.feature_definitions and self.feature_definitions[feature_name].rollout_percentage)
            * 655.35
        )

        return (hash_value % 100) <= rollout_threshold

    def set_toggle(
        self, feature_name: str, value: bool, source: str = "api", force: bool = False
    ) -> tuple[bool, list[str]]:
        """Set a feature toggle value.

        Args:
            feature_name: Name of the feature
            value: New value
            source: Source of the change (environment, api, file, cli)
            force: Force the change even if dependencies are missing

        Returns:
            Tuple of (success, list of warnings/errors)
        """
        warnings = []
        old_value = self.is_enabled(feature_name)

        if not force:
            deps_ok, missing = self._check_dependencies(feature_name, value)
            if not deps_ok:
                logger.error(f"Cannot enable {feature_name}: missing dependencies {missing}")
                return False, [f"Missing dependencies: {', '.join(missing)}"]

        if feature_name in self.feature_definitions:
            self.feature_definitions[feature_name].enabled = value
            self.feature_definitions[feature_name].updated_at = datetime.now(UTC).isoformat()
        else:
            # Legacy toggle storage
            self.toggles[feature_name] = value

        self._log_change(feature_name, old_value, value, source)
        self._save_toggles()

        logger.info(f"Toggle {feature_name} set to {value} (source: {source})")
        return True, warnings

    def add_feature(
        self,
        name: str,
        enabled: bool = False,
        description: str = "",
        rollout_percentage: float = 0.0,
        dependencies: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Add a new feature definition."""
        if name in self.feature_definitions:
            logger.warning(f"Feature {name} already exists, use set_toggle to modify")
            return False

        self.feature_definitions[name] = FeatureDefinition(
            name=name,
            enabled=enabled,
            description=description,
            rollout_percentage=rollout_percentage,
            dependencies=dependencies or [],
            metadata=metadata or {},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        self._save_toggles()
        logger.info(f"Feature {name} added to toggle kit")
        return True

    def get_feature(self, feature_name: str) -> FeatureDefinition | None:
        """Get feature definition."""
        return self.feature_definitions.get(feature_name)

    def list_features(self) -> dict[str, FeatureDefinition]:
        """List all feature definitions."""
        return dict(self.feature_definitions)

    def list_toggles(self) -> dict[str, bool]:
        """List all active toggles (legacy compatibility)."""
        return {
            name: self.is_enabled(name) for name in list(self.feature_definitions.keys()) + list(self.toggles.keys())
        }

    def get_audit_log(self, limit: int = 50) -> list[ToggleChange]:
        """Get recent audit log entries."""
        return self.audit_log[-limit:]

    def validate_configuration(self) -> dict[str, Any]:
        """Validate the current toggle configuration.

        Returns:
            Dictionary with 'valid', 'errors', and 'warnings' keys
        """
        errors = []
        warnings = []

        # Check for circular dependencies
        for feature_name in self.feature_definitions:
            visited: set[str] = set()
            if self._has_cycle(feature_name, visited, set()):
                errors.append(f"Circular dependency detected for {feature_name}")

        # Check for missing dependencies
        warnings.extend(
            f"Feature {name} depends on unknown feature {dep}"
            for name, feature in self.feature_definitions.items()
            for dep in feature.dependencies
            if dep not in self.feature_definitions
        )

        # Check rollout percentages
        for name, feature in self.feature_definitions.items():
            if feature.rollout_percentage < 0 or feature.rollout_percentage > 100:
                errors.append(f"Invalid rollout percentage for {name}: {feature.rollout_percentage}")

        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    def _has_cycle(self, feature_name: str, visited: set[str], visiting: set[str]) -> bool:
        """Check for circular dependencies."""
        if feature_name in visiting:
            return True
        if feature_name in visited:
            return False

        visiting.add(feature_name)
        visited.add(feature_name)

        feature = self.feature_definitions.get(feature_name)
        if feature:
            for dep in feature.dependencies:
                if self._has_cycle(dep, visited, visiting.copy()):
                    return True

        visiting.discard(feature_name)
        return False

    def export_config(self, format: str = "json") -> str:
        """Export configuration in specified format."""
        if format == "json":
            config = {
                "features": {
                    name: {
                        "enabled": feat.enabled,
                        "description": feat.description,
                        "rollout_percentage": feat.rollout_percentage,
                        "dependencies": feat.dependencies,
                        "metadata": feat.metadata,
                    }
                    for name, feat in self.feature_definitions.items()
                },
                "toggles": self.toggles,
            }
            return json.dumps(config, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")


def create_toggle_kit(config_path: str | None = None, features: dict[str, dict[str, Any]] | None = None) -> ToggleKit:
    """Factory function to create and configure a ToggleKit instance."""
    kit = ToggleKit(config_path)

    if features:
        for name, config in features.items():
            kit.add_feature(
                name=name,
                enabled=config.get("enabled", False),
                description=config.get("description", ""),
                rollout_percentage=config.get("rollout_percentage", 0.0),
                dependencies=config.get("dependencies", []),
                metadata=config.get("metadata", {}),
            )

    return kit
