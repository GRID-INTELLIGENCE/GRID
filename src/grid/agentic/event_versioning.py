"""
Event versioning with schema evolution support.

Provides version management for events with automatic migration support
and backward compatibility. Implements audio engineering-inspired lossless
capture with version tracking and schema evolution.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class EventVersion:
    """Version information for an event type."""

    event_type: str
    version: int
    schema: dict[str, Any]
    migration_rules: dict[str, str]  # version -> migration function name
    created_at: datetime
    deprecated_at: datetime | None = None
    description: str = ""

    def is_deprecated(self) -> bool:
        """Check if this version is deprecated."""
        return self.deprecated_at is not None

    def is_compatible_with(self, target_version: int) -> bool:
        """Check if this version can migrate to target version."""
        if self.version == target_version:
            return True

        # Check if there's a migration path
        current = self.version
        while current < target_version:
            next_version_key = str(current + 1)
            if next_version_key not in self.migration_rules:
                return False
            current += 1

        return True


class EventVersionRegistry:
    """
    Registry for event versions with migration support.

    Features:
    - Version tracking for all event types
    - Automatic migration between versions
    - Schema validation
    - Backward compatibility checks
    """

    def __init__(self):
        """Initialize the event version registry."""
        self._versions: dict[str, list[EventVersion]] = {}
        self._migration_functions: dict[str, Callable] = {}
        self._current_versions: dict[str, int] = {}

        logger.info("EventVersionRegistry initialized")

    def register_version(
        self,
        event_type: str,
        version: int,
        schema: dict[str, Any],
        migration_rules: dict[str, str] | None = None,
        description: str = "",
    ) -> EventVersion:
        """
        Register a new event version.

        Args:
            event_type: Type of event
            version: Version number
            schema: JSON schema for the event
            migration_rules: Mapping of version -> migration function name
            description: Description of the version

        Returns:
            Created EventVersion
        """
        event_version = EventVersion(
            event_type=event_type,
            version=version,
            schema=schema,
            migration_rules=migration_rules or {},
            created_at=datetime.now(),
            description=description,
        )

        if event_type not in self._versions:
            self._versions[event_type] = []

        # Insert version in order
        versions = self._versions[event_type]
        insert_index = next((i for i, v in enumerate(versions) if v.version > version), len(versions))
        versions.insert(insert_index, event_version)

        # Update current version if this is the latest
        if version > self._current_versions.get(event_type, 0):
            self._current_versions[event_type] = version

        logger.info(f"Registered {event_type} v{version}")
        return event_version

    def register_migration_function(self, name: str, function: Callable) -> None:
        """
        Register a migration function.

        Args:
            name: Function name for reference
            function: Migration function that takes event data and returns migrated data
        """
        self._migration_functions[name] = function
        logger.debug(f"Registered migration function: {name}")

    def get_version(self, event_type: str, version: int) -> EventVersion | None:
        """
        Get a specific version of an event type.

        Args:
            event_type: Type of event
            version: Version number

        Returns:
            EventVersion or None if not found
        """
        versions = self._versions.get(event_type, [])
        for event_version in versions:
            if event_version.version == version:
                return event_version
        return None

    def get_current_version(self, event_type: str) -> EventVersion | None:
        """
        Get the current version of an event type.

        Args:
            event_type: Type of event

        Returns:
            Current EventVersion or None if not found
        """
        current_version = self._current_versions.get(event_type)
        if current_version is None:
            return None
        return self.get_version(event_type, current_version)

    def migrate_event(
        self,
        event_data: dict[str, Any],
        target_version: int | None = None,
        event_type: str | None = None,
    ) -> dict[str, Any]:
        """
        Migrate event data to a target version.

        Args:
            event_data: Event data to migrate
            target_version: Target version (defaults to current)
            event_type: Event type (extracted from data if not provided)

        Returns:
            Migrated event data
        """
        if event_type is None:
            event_type = event_data.get("event_type")
            if not event_type:
                raise ValueError("Event type must be provided or present in event_data")

        current_version = event_data.get("event_version", 1)

        if target_version is None:
            target_version = self._current_versions.get(event_type, 1)

        if current_version == target_version:
            return event_data

        # Get the current version definition
        version_info = self.get_version(event_type, current_version)
        if not version_info:
            raise ValueError(f"Unknown version {current_version} for event type {event_type}")

        # Perform step-by-step migration
        migrated_data = event_data.copy()
        current = current_version

        while current < target_version:
            next_version_key = str(current + 1)

            # Get current version info for migration rules
            version_info = self.get_version(event_type, current)
            if not version_info:
                raise ValueError(f"Unknown version {current} for event type {event_type}")

            if next_version_key not in version_info.migration_rules:
                raise ValueError(f"No migration rule from v{current} to v{current + 1} for {event_type}")

            migration_function_name = version_info.migration_rules[next_version_key]
            migration_function = self._migration_functions.get(migration_function_name)

            if not migration_function:
                raise ValueError(f"Migration function '{migration_function_name}' not found")

            try:
                migrated_data = migration_function(migrated_data)
                migrated_data["event_version"] = current + 1
                current += 1

                # Get next version info for continued migration
                if current < target_version:
                    version_info = self.get_version(event_type, current)

            except Exception as e:
                logger.error(f"Migration failed for {event_type} v{current} to v{current + 1}: {e}")
                raise

        logger.debug(f"Migrated {event_type} from v{current_version} to v{target_version}")
        return migrated_data

    def validate_event(self, event_data: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate event data against its version schema.

        Args:
            event_data: Event data to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        event_type = event_data.get("event_type")
        version = event_data.get("event_version", 1)

        if not event_type:
            return False, ["Missing event_type"]

        version_info = self.get_version(event_type, version)
        if not version_info:
            return False, [f"Unknown version {version} for event type {event_type}"]

        # Basic schema validation (simplified - would use jsonschema in production)
        errors = []
        schema = version_info.schema

        # Check required fields
        required_fields = schema.get("required", [])
        errors.extend(f"Missing required field: {field}" for field in required_fields if field not in event_data)

        # Check field types
        properties = schema.get("properties", {})
        for field_name, field_schema in properties.items():
            if field_name in event_data:
                expected_type = field_schema.get("type")
                actual_value = event_data[field_name]

                if not self._check_type(actual_value, expected_type):
                    errors.append(f"Field '{field_name}' has invalid type. Expected {expected_type}")

        return len(errors) == 0, errors

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if a value matches the expected type."""
        type_checks = {
            "string": lambda v: isinstance(v, str),
            "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
            "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
            "boolean": lambda v: isinstance(v, bool),
            "array": lambda v: isinstance(v, list),
            "object": lambda v: isinstance(v, dict),
            "null": lambda v: v is None,
        }

        check_fn = type_checks.get(expected_type)
        return check_fn(value) if check_fn else False

    def get_version_history(self, event_type: str) -> list[dict[str, Any]]:
        """
        Get the version history for an event type.

        Args:
            event_type: Type of event

        Returns:
            List of version information
        """
        versions = self._versions.get(event_type, [])
        return [
            {
                "version": v.version,
                "created_at": v.created_at.isoformat(),
                "deprecated_at": v.deprecated_at.isoformat() if v.deprecated_at else None,
                "description": v.description,
                "is_deprecated": v.is_deprecated(),
            }
            for v in versions
        ]

    def deprecate_version(self, event_type: str, version: int) -> bool:
        """
        Deprecate a specific version.

        Args:
            event_type: Type of event
            version: Version to deprecate

        Returns:
            True if deprecated successfully
        """
        version_info = self.get_version(event_type, version)
        if not version_info:
            return False

        if version_info.is_deprecated():
            return True

        version_info.deprecated_at = datetime.now()
        logger.info(f"Deprecated {event_type} v{version}")
        return True

    def get_stats(self) -> dict[str, Any]:
        """
        Get registry statistics.

        Returns:
            Dictionary with registry statistics
        """
        total_versions = sum(len(versions) for versions in self._versions.values())

        return {
            "event_types": len(self._versions),
            "total_versions": total_versions,
            "migration_functions": len(self._migration_functions),
            "current_versions": dict(self._current_versions),
        }


# Global registry instance
_global_registry: EventVersionRegistry | None = None


def get_event_version_registry() -> EventVersionRegistry:
    """Get or create global event version registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = EventVersionRegistry()
    return _global_registry


def set_event_version_registry(registry: EventVersionRegistry) -> None:
    """Set global event version registry."""
    global _global_registry
    _global_registry = registry


# Built-in migration functions
def migrate_v1_to_v2_add_timestamp(event_data: dict[str, Any]) -> dict[str, Any]:
    """Example migration: add timestamp field to v1 events."""
    migrated = event_data.copy()
    if "timestamp" not in migrated:
        migrated["timestamp"] = datetime.now().isoformat()
    return migrated


def migrate_v2_to_v3_rename_fields(event_data: dict[str, Any]) -> dict[str, Any]:
    """Example migration: rename user_id to actor_id."""
    migrated = event_data.copy()
    if "user_id" in migrated:
        migrated["actor_id"] = migrated.pop("user_id")
    return migrated


# Register built-in migration functions
def _register_builtin_migrations():
    """Register built-in migration functions."""
    registry = get_event_version_registry()
    registry.register_migration_function("migrate_v1_to_v2_add_timestamp", migrate_v1_to_v2_add_timestamp)
    registry.register_migration_function("migrate_v2_to_v3_rename_fields", migrate_v2_to_v3_rename_fields)


# Auto-register built-ins on import
_register_builtin_migrations()
