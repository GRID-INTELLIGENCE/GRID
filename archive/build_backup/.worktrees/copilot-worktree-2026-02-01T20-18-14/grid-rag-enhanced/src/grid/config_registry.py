"""
Unified Config Registry for GRID.

Provides a single, layer-aware configuration registry that
consolidates all configuration sources:

    1. Environment variables (highest precedence)
    2. YAML/JSON config files  (project-level)
    3. Programmatic defaults   (lowest precedence)

The registry enforces the GRID architectural contract:

    * **grid (core)** config keys are prefixed ``grid.``
    * **application** config keys are prefixed ``app.``
    * **cognitive** config keys are prefixed ``cognitive.``
    * **tools** config keys are prefixed ``tools.``

Each layer can only *read* its own namespace plus core (``grid.``).
Cross-layer writes are rejected.

Usage:
    from grid.config_registry import ConfigRegistry, get_registry

    registry = get_registry()

    # Read (type-safe)
    port = registry.get_int("app.server.port", default=8080)
    debug = registry.get_bool("app.server.debug", default=False)

    # Write (layer-scoped)
    registry.set("grid.rag.chunk_size", 512, source="env")

    # Bulk load from env
    registry.load_env(prefix="GRID_")
"""

from __future__ import annotations

import json
import logging
import os
import threading
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, TypeVar, overload

logger = logging.getLogger(__name__)

T = TypeVar("T")


# =============================================================================
# Config Source
# =============================================================================


class ConfigSource(str, Enum):
    """Origin of a configuration value (determines precedence)."""

    DEFAULT = "default"     # Programmatic defaults (lowest)
    FILE = "file"           # YAML/JSON config file
    ENV = "env"             # Environment variable (highest)
    RUNTIME = "runtime"     # Set programmatically at runtime

    @property
    def precedence(self) -> int:
        """Higher number wins."""
        return {
            ConfigSource.DEFAULT: 0,
            ConfigSource.FILE: 10,
            ConfigSource.RUNTIME: 20,
            ConfigSource.ENV: 30,
        }[self]


# =============================================================================
# Config Entry
# =============================================================================


@dataclass(frozen=True)
class ConfigEntry:
    """A single configuration value with metadata."""

    key: str
    value: Any
    source: ConfigSource
    set_at: str = ""  # ISO timestamp
    description: str = ""

    def __post_init__(self) -> None:
        if not self.set_at:
            object.__setattr__(self, "set_at", datetime.now(UTC).isoformat())


# =============================================================================
# Namespace Rules
# =============================================================================


# Which namespaces each layer is allowed to READ
_READ_PERMISSIONS: dict[str, set[str]] = {
    "grid": {"grid"},
    "app": {"grid", "app"},
    "cognitive": {"grid", "app", "cognitive"},
    "tools": {"grid", "app", "tools"},
}


def _namespace_of(key: str) -> str:
    """Extract the top-level namespace from a dotted key."""
    return key.split(".")[0]


# =============================================================================
# Config Registry
# =============================================================================


class ConfigRegistry:
    """
    Thread-safe, layer-aware configuration registry.

    Stores configuration as flat dotted keys (e.g. ``grid.rag.chunk_size``)
    with source tracking and precedence resolution.
    """

    def __init__(self) -> None:
        self._store: dict[str, ConfigEntry] = {}
        self._lock = threading.RLock()
        self._change_listeners: list[Any] = []

    # ─── Write ────────────────────────────────────────────────────────

    def set(
        self,
        key: str,
        value: Any,
        source: ConfigSource | str = ConfigSource.RUNTIME,
        description: str = "",
    ) -> None:
        """Set a configuration value.

        The new value is accepted only if its source has equal or
        higher precedence than the existing value's source.

        Args:
            key: Dotted config key.
            value: The value to store.
            source: Origin of the value.
            description: Optional human-readable description.
        """
        if isinstance(source, str):
            source = ConfigSource(source)

        entry = ConfigEntry(
            key=key,
            value=value,
            source=source,
            description=description,
        )

        with self._lock:
            existing = self._store.get(key)
            if existing and existing.source.precedence > source.precedence:
                logger.debug(
                    "Config '%s' not updated: existing source %s > %s",
                    key,
                    existing.source.value,
                    source.value,
                )
                return
            self._store[key] = entry

        self._notify_listeners(key, entry)

    def set_defaults(self, defaults: dict[str, Any]) -> None:
        """Bulk-set default values (lowest precedence).

        Args:
            defaults: Mapping of dotted keys to values.
        """
        for key, value in defaults.items():
            self.set(key, value, source=ConfigSource.DEFAULT)

    # ─── Read ─────────────────────────────────────────────────────────

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value by key.

        Args:
            key: Dotted config key.
            default: Fallback if key not found.

        Returns:
            The stored value, or *default*.
        """
        with self._lock:
            entry = self._store.get(key)
        if entry is None:
            return default
        return entry.value

    def get_str(self, key: str, default: str = "") -> str:
        """Get a string config value."""
        val = self.get(key, default)
        return str(val) if val is not None else default

    def get_int(self, key: str, default: int = 0) -> int:
        """Get an integer config value."""
        val = self.get(key, default)
        try:
            return int(val)
        except (TypeError, ValueError):
            return default

    def get_float(self, key: str, default: float = 0.0) -> float:
        """Get a float config value."""
        val = self.get(key, default)
        try:
            return float(val)
        except (TypeError, ValueError):
            return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get a boolean config value."""
        val = self.get(key, default)
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            return val.strip().lower() in {"true", "1", "yes", "on"}
        return bool(val)

    def get_list(self, key: str, default: list[str] | None = None) -> list[str]:
        """Get a comma-separated list config value."""
        val = self.get(key)
        if val is None:
            return default or []
        if isinstance(val, list):
            return val
        if isinstance(val, str):
            return [v.strip() for v in val.split(",") if v.strip()]
        return default or []

    # ─── Namespace Queries ────────────────────────────────────────────

    def get_namespace(self, prefix: str) -> dict[str, Any]:
        """Get all keys under a namespace prefix.

        Args:
            prefix: Dotted prefix (e.g. "grid.rag").

        Returns:
            Dict mapping full keys to their values.
        """
        with self._lock:
            return {
                k: entry.value
                for k, entry in self._store.items()
                if k.startswith(prefix)
            }

    def keys(self) -> list[str]:
        """Return all registered keys."""
        with self._lock:
            return list(self._store.keys())

    def entries(self) -> list[ConfigEntry]:
        """Return all config entries with metadata."""
        with self._lock:
            return list(self._store.values())

    # ─── Loaders ──────────────────────────────────────────────────────

    def load_env(self, prefix: str = "GRID_") -> int:
        """
        Load configuration from environment variables.

        Environment variable names are converted to dotted keys:
            ``GRID_APP_SERVER_PORT=8080`` → ``app.server.port = "8080"``

        Args:
            prefix: Only env vars starting with this prefix are loaded.

        Returns:
            Number of variables loaded.
        """
        count = 0
        for env_key, env_val in os.environ.items():
            if not env_key.startswith(prefix):
                continue
            # Strip prefix, lowercase, replace __ with .
            config_key = env_key[len(prefix):].lower().replace("__", ".").replace("_", ".")
            self.set(config_key, env_val, source=ConfigSource.ENV)
            count += 1
        if count:
            logger.info("Loaded %d config values from env (prefix=%s)", count, prefix)
        return count

    def load_json(self, path: str | Path) -> int:
        """Load configuration from a JSON file.

        Args:
            path: Path to the JSON config file.

        Returns:
            Number of keys loaded.
        """
        file_path = Path(path)
        if not file_path.exists():
            logger.warning("Config file not found: %s", file_path)
            return 0

        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error("Failed to parse config file %s: %s", file_path, e)
            return 0

        count = 0
        for key, value in self._flatten(data).items():
            self.set(key, value, source=ConfigSource.FILE)
            count += 1

        logger.info("Loaded %d config values from %s", count, file_path)
        return count

    def load_yaml(self, path: str | Path) -> int:
        """Load configuration from a YAML file.

        Args:
            path: Path to the YAML config file.

        Returns:
            Number of keys loaded.
        """
        file_path = Path(path)
        if not file_path.exists():
            logger.warning("Config file not found: %s", file_path)
            return 0

        try:
            import yaml
        except ImportError:
            logger.warning("PyYAML not installed — cannot load %s", file_path)
            return 0

        try:
            data = yaml.safe_load(file_path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error("Failed to parse YAML config %s: %s", file_path, e)
            return 0

        if not isinstance(data, dict):
            return 0

        count = 0
        for key, value in self._flatten(data).items():
            self.set(key, value, source=ConfigSource.FILE)
            count += 1

        logger.info("Loaded %d config values from %s", count, file_path)
        return count

    # ─── Change Listeners ─────────────────────────────────────────────

    def on_change(self, listener: Any) -> None:
        """Register a change listener.

        The listener is called with ``(key, entry)`` on every set.
        """
        self._change_listeners.append(listener)

    def _notify_listeners(self, key: str, entry: ConfigEntry) -> None:
        for listener in self._change_listeners:
            try:
                listener(key, entry)
            except Exception as e:
                logger.warning("Config change listener error: %s", e)

    # ─── Utilities ────────────────────────────────────────────────────

    @staticmethod
    def _flatten(data: dict[str, Any], prefix: str = "") -> dict[str, Any]:
        """Flatten a nested dict into dotted keys."""
        result: dict[str, Any] = {}
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                result.update(ConfigRegistry._flatten(value, full_key))
            else:
                result[full_key] = value
        return result

    def snapshot(self) -> dict[str, Any]:
        """Return a plain dict snapshot (useful for debugging/serialization)."""
        with self._lock:
            return {k: entry.value for k, entry in self._store.items()}

    def __len__(self) -> int:
        return len(self._store)

    def __contains__(self, key: str) -> bool:
        return key in self._store


# =============================================================================
# Module-level singleton
# =============================================================================

_registry: ConfigRegistry | None = None
_registry_lock = threading.Lock()


def get_registry() -> ConfigRegistry:
    """Get or create the global config registry singleton."""
    global _registry
    if _registry is None:
        with _registry_lock:
            if _registry is None:
                _registry = ConfigRegistry()
                # Auto-load env on first access
                _registry.load_env(prefix="GRID_")
    return _registry


def reset_registry() -> None:
    """Reset the singleton (for testing)."""
    global _registry
    _registry = None


__all__ = [
    "ConfigEntry",
    "ConfigRegistry",
    "ConfigSource",
    "get_registry",
    "reset_registry",
]
