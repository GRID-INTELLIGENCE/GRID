"""Discoverable Protocol - Interface for discoverable entities.

Defines the contract for entities that can be discovered through
VECTION's emergence layer. Any object implementing this protocol
can be observed, analyzed, and surfaced as emergent patterns.

This follows Python's Protocol-based structural subtyping approach,
allowing duck-typing with static type checking support.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Discoverable(Protocol):
    """Protocol for entities that can be discovered through emergence.

    Any class implementing this protocol can be observed by the
    EmergenceLayer and potentially surfaced as an emergent pattern.

    Required Methods:
        to_dict: Convert to dictionary for observation.
        get_discovery_keys: Get keys used for pattern matching.

    Optional Properties:
        discovery_salience: How important is this for discovery.
        discovery_timestamp: When this entity was created/observed.
    """

    def to_dict(self) -> dict[str, Any]:
        """Convert entity to dictionary representation.

        This is the primary method used by the EmergenceLayer to
        observe and analyze the entity.

        Returns:
            Dictionary with entity data suitable for pattern detection.
        """
        ...

    def get_discovery_keys(self) -> list[str]:
        """Get keys used for pattern matching and correlation.

        Returns keys that should be used when looking for correlations,
        clusters, and sequences involving this entity.

        Returns:
            List of discovery key strings.

        Example:
            >>> event.get_discovery_keys()
            ['action:search', 'topic:authentication', 'user:123']
        """
        ...


@runtime_checkable
class SalientDiscoverable(Discoverable, Protocol):
    """Extended protocol for entities with salience tracking.

    Adds salience-related properties for more sophisticated
    pattern discovery and prioritization.
    """

    @property
    def discovery_salience(self) -> float:
        """Get salience score for discovery prioritization.

        Higher salience means this entity should be weighted more
        heavily in pattern detection and emergence scoring.

        Returns:
            Salience score between 0.0 and 1.0.
        """
        ...

    @property
    def discovery_timestamp(self) -> datetime:
        """Get timestamp for temporal pattern analysis.

        Returns:
            Datetime when this entity was created or observed.
        """
        ...


@runtime_checkable
class CorrelableDiscoverable(Discoverable, Protocol):
    """Extended protocol for entities that can be correlated.

    Adds correlation-specific methods for finding relationships
    between entities.
    """

    def get_correlation_fingerprint(self) -> str:
        """Get a fingerprint for correlation matching.

        Entities with similar fingerprints are more likely to
        be correlated in pattern detection.

        Returns:
            Fingerprint string for correlation matching.
        """
        ...

    def correlates_with(self, other: Discoverable) -> float:
        """Check correlation strength with another discoverable.

        Args:
            other: Another discoverable entity.

        Returns:
            Correlation score between 0.0 (uncorrelated) and 1.0 (highly correlated).
        """
        ...


class DiscoverableAdapter:
    """Adapter to make arbitrary objects discoverable.

    Wraps any object to make it conform to the Discoverable protocol,
    extracting reasonable defaults for discovery keys and dict conversion.

    Usage:
        >>> obj = SomeObject(data="value")
        >>> discoverable = DiscoverableAdapter(obj)
        >>> emergence_layer.observe(discoverable)
    """

    def __init__(
        self,
        obj: Any,
        salience: float = 0.5,
        discovery_keys: list[str] | None = None,
    ) -> None:
        """Initialize the adapter.

        Args:
            obj: Object to wrap.
            salience: Salience score for the wrapped object.
            discovery_keys: Explicit discovery keys (auto-generated if None).
        """
        self._obj = obj
        self._salience = max(0.0, min(1.0, salience))
        self._discovery_keys = discovery_keys
        self._timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        """Convert wrapped object to dictionary."""
        if hasattr(self._obj, "to_dict") and callable(self._obj.to_dict):
            return self._obj.to_dict()

        if hasattr(self._obj, "__dict__"):
            return {k: v for k, v in self._obj.__dict__.items() if not k.startswith("_") and not callable(v)}

        if isinstance(self._obj, dict):
            return self._obj

        return {"value": str(self._obj), "type": type(self._obj).__name__}

    def get_discovery_keys(self) -> list[str]:
        """Get discovery keys for the wrapped object."""
        if self._discovery_keys is not None:
            return self._discovery_keys

        # Auto-generate keys from dict representation
        data = self.to_dict()
        keys: list[str] = []

        for key in ("action", "type", "intent", "topic", "category"):
            if key in data and data[key]:
                keys.append(f"{key}:{data[key]}")

        # Add type key
        keys.append(f"_type:{type(self._obj).__name__}")

        return keys

    @property
    def discovery_salience(self) -> float:
        """Get salience score."""
        return self._salience

    @property
    def discovery_timestamp(self) -> datetime:
        """Get creation timestamp."""
        return self._timestamp


def make_discoverable(
    obj: Any,
    salience: float = 0.5,
    discovery_keys: list[str] | None = None,
) -> DiscoverableAdapter:
    """Factory function to make any object discoverable.

    Args:
        obj: Object to make discoverable.
        salience: Salience score.
        discovery_keys: Explicit discovery keys.

    Returns:
        DiscoverableAdapter wrapping the object.
    """
    return DiscoverableAdapter(obj, salience, discovery_keys)


def is_discoverable(obj: Any) -> bool:
    """Check if an object implements the Discoverable protocol.

    Args:
        obj: Object to check.

    Returns:
        True if object is discoverable.
    """
    return isinstance(obj, Discoverable)


def is_salient_discoverable(obj: Any) -> bool:
    """Check if an object implements SalientDiscoverable.

    Args:
        obj: Object to check.

    Returns:
        True if object is salient discoverable.
    """
    return isinstance(obj, SalientDiscoverable)
