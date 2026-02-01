"""VectionContext and Anchor schemas - Session context state.

Defines the core state structures for VECTION context management.
VectionContext represents accumulated session context that flows
across requests rather than resetting.
"""

from __future__ import annotations

import hashlib
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


class AnchorType(str, Enum):
    """Types of context anchors."""

    TOPIC = "topic"  # Subject matter anchor
    INTENT = "intent"  # User intent anchor
    TASK = "task"  # Task/workflow anchor
    ENTITY = "entity"  # Named entity anchor
    TEMPORAL = "temporal"  # Time-based anchor
    CAUSAL = "causal"  # Causal relationship anchor
    CUSTOM = "custom"  # User-defined anchor


class ContextStatus(str, Enum):
    """Status of a VectionContext."""

    INITIALIZING = "initializing"  # Being established
    ACTIVE = "active"  # Actively tracking
    STABLE = "stable"  # Consistent pattern established
    DRIFTING = "drifting"  # Trajectory changing
    STALE = "stale"  # Needs refresh
    DISSOLVED = "dissolved"  # No longer valid


@dataclass
class Anchor:
    """Thread anchoring point for context continuity.

    Anchors are stable reference points that help maintain context
    coherence across requests. They represent persistent elements
    that the session revolves around.

    Attributes:
        anchor_id: Unique identifier for this anchor.
        anchor_type: Category of anchor.
        value: The anchor value (topic, entity, etc.).
        weight: Importance weight (0.0 - 1.0).
        created_at: When anchor was established.
        last_referenced: Last time anchor was relevant.
        reference_count: Number of times referenced.
        metadata: Additional anchor-specific data.
    """

    anchor_id: str
    anchor_type: AnchorType
    value: str
    weight: float = 0.5
    created_at: datetime = field(default_factory=datetime.now)
    last_referenced: datetime = field(default_factory=datetime.now)
    reference_count: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate anchor components."""
        self.weight = max(0.0, min(1.0, self.weight))
        self.reference_count = max(1, self.reference_count)

    @property
    def age_seconds(self) -> float:
        """Get anchor age in seconds."""
        return (datetime.now() - self.created_at).total_seconds()

    @property
    def staleness(self) -> float:
        """Get seconds since last reference."""
        return (datetime.now() - self.last_referenced).total_seconds()

    @property
    def effective_weight(self) -> float:
        """Get weight with staleness decay applied."""
        staleness_hours = self.staleness / 3600
        decay_factor = max(0.1, 1.0 - (0.1 * staleness_hours))
        return self.weight * decay_factor

    def reference(self, boost: float = 0.05) -> None:
        """Mark anchor as referenced.

        Args:
            boost: Amount to boost weight.
        """
        self.last_referenced = datetime.now()
        self.reference_count += 1
        self.weight = min(1.0, self.weight + boost)

    def decay(self, factor: float = 0.1) -> None:
        """Apply decay to anchor weight.

        Args:
            factor: Decay factor.
        """
        self.weight = max(0.0, self.weight * (1.0 - factor))

    def is_stale(self, max_staleness_hours: float = 4.0) -> bool:
        """Check if anchor is stale.

        Args:
            max_staleness_hours: Maximum hours without reference.

        Returns:
            True if anchor should be considered stale.
        """
        staleness_hours = self.staleness / 3600
        return staleness_hours > max_staleness_hours or self.effective_weight < 0.1

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "anchor_id": self.anchor_id,
            "anchor_type": self.anchor_type.value,
            "value": self.value,
            "weight": round(self.weight, 3),
            "effective_weight": round(self.effective_weight, 3),
            "created_at": self.created_at.isoformat(),
            "last_referenced": self.last_referenced.isoformat(),
            "reference_count": self.reference_count,
            "age_seconds": round(self.age_seconds, 1),
            "staleness_seconds": round(self.staleness, 1),
            "metadata": self.metadata,
        }

    @classmethod
    def create(
        cls,
        anchor_type: AnchorType,
        value: str,
        weight: float = 0.5,
        metadata: dict[str, Any] | None = None,
    ) -> Anchor:
        """Factory method to create a new anchor.

        Args:
            anchor_type: Type of anchor.
            value: Anchor value.
            weight: Initial weight.
            metadata: Additional metadata.

        Returns:
            New Anchor instance.
        """
        hash_input = f"{anchor_type.value}:{value}:{time.time()}"
        anchor_id = hashlib.md5(hash_input.encode()).hexdigest()[:10]

        return cls(
            anchor_id=anchor_id,
            anchor_type=anchor_type,
            value=value,
            weight=weight,
            metadata=metadata or {},
        )

    @classmethod
    def topic(cls, value: str, weight: float = 0.6) -> Anchor:
        """Create a topic anchor."""
        return cls.create(AnchorType.TOPIC, value, weight)

    @classmethod
    def intent(cls, value: str, weight: float = 0.7) -> Anchor:
        """Create an intent anchor."""
        return cls.create(AnchorType.INTENT, value, weight)

    @classmethod
    def task(cls, value: str, weight: float = 0.8) -> Anchor:
        """Create a task anchor."""
        return cls.create(AnchorType.TASK, value, weight)

    @classmethod
    def entity(cls, value: str, weight: float = 0.5) -> Anchor:
        """Create an entity anchor."""
        return cls.create(AnchorType.ENTITY, value, weight)


@dataclass
class VectionContext:
    """Session context state for VECTION.

    Represents accumulated context that flows across requests.
    This is what fills the gap: context_establishment is no longer null.

    Attributes:
        session_id: Unique session identifier.
        status: Current context status.
        thread_anchors: Stable reference points for context.
        accumulated_signals: Emergent pattern signals.
        cognitive_velocity: Current cognitive motion vector.
        temporal_window: Active time window (start, end).
        interaction_count: Number of interactions tracked.
        established_at: When context was established.
        last_updated: Most recent update.
        salience_map: Current salience scores by topic.
        projections: Cached future projections.
        metadata: Additional context metadata.
    """

    session_id: str
    status: ContextStatus = ContextStatus.INITIALIZING
    thread_anchors: list[Anchor] = field(default_factory=list)
    accumulated_signals: deque[Any] = field(default_factory=lambda: deque(maxlen=100))
    cognitive_velocity: Any = None  # VelocityVector, lazy import
    temporal_window: tuple[float, float] = field(default_factory=lambda: (time.time(), time.time()))
    interaction_count: int = 0
    established_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    salience_map: dict[str, float] = field(default_factory=dict)
    projections: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def age_seconds(self) -> float:
        """Get context age in seconds."""
        return (datetime.now() - self.established_at).total_seconds()

    @property
    def staleness(self) -> float:
        """Get seconds since last update."""
        return (datetime.now() - self.last_updated).total_seconds()

    @property
    def is_established(self) -> bool:
        """Check if context is established (not null)."""
        return self.status not in (ContextStatus.INITIALIZING, ContextStatus.DISSOLVED)

    @property
    def anchor_count(self) -> int:
        """Get number of active anchors."""
        return len([a for a in self.thread_anchors if not a.is_stale()])

    @property
    def signal_count(self) -> int:
        """Get number of accumulated signals."""
        return len(self.accumulated_signals)

    @property
    def has_velocity(self) -> bool:
        """Check if cognitive velocity is tracked."""
        return self.cognitive_velocity is not None

    @property
    def window_duration_seconds(self) -> float:
        """Get temporal window duration."""
        return self.temporal_window[1] - self.temporal_window[0]

    def add_anchor(self, anchor: Anchor) -> None:
        """Add or update an anchor.

        Args:
            anchor: Anchor to add.
        """
        # Check for existing anchor with same type and value
        for existing in self.thread_anchors:
            if existing.anchor_type == anchor.anchor_type and existing.value == anchor.value:
                existing.reference()
                return

        self.thread_anchors.append(anchor)
        self._touch()

    def remove_anchor(self, anchor_id: str) -> bool:
        """Remove an anchor by ID.

        Args:
            anchor_id: ID of anchor to remove.

        Returns:
            True if anchor was removed.
        """
        for i, anchor in enumerate(self.thread_anchors):
            if anchor.anchor_id == anchor_id:
                self.thread_anchors.pop(i)
                self._touch()
                return True
        return False

    def add_signal(self, signal: Any) -> None:
        """Add an emergence signal.

        Args:
            signal: EmergenceSignal to add.
        """
        self.accumulated_signals.append(signal)
        self._touch()

        # Update salience map
        if hasattr(signal, "description") and hasattr(signal, "effective_salience"):
            key = signal.description[:50]
            self.salience_map[key] = signal.effective_salience

    def get_salient_signals(self, threshold: float = 0.3) -> list[Any]:
        """Get signals above salience threshold.

        Args:
            threshold: Minimum effective salience.

        Returns:
            List of salient signals.
        """
        salient = []
        for signal in self.accumulated_signals:
            if hasattr(signal, "effective_salience") and signal.effective_salience >= threshold:
                salient.append(signal)
        return salient

    def get_anchors_by_type(self, anchor_type: AnchorType) -> list[Anchor]:
        """Get anchors of a specific type.

        Args:
            anchor_type: Type to filter by.

        Returns:
            List of matching anchors.
        """
        return [a for a in self.thread_anchors if a.anchor_type == anchor_type]

    def get_dominant_anchors(self, limit: int = 3) -> list[Anchor]:
        """Get the most important anchors.

        Args:
            limit: Maximum number to return.

        Returns:
            List of dominant anchors sorted by effective weight.
        """
        sorted_anchors = sorted(
            [a for a in self.thread_anchors if not a.is_stale()],
            key=lambda a: a.effective_weight,
            reverse=True,
        )
        return sorted_anchors[:limit]

    def update_velocity(self, velocity: Any) -> None:
        """Update cognitive velocity.

        Args:
            velocity: New VelocityVector.
        """
        self.cognitive_velocity = velocity
        self._touch()

        # Update projections from velocity
        if hasattr(velocity, "project"):
            self.projections = velocity.project(3)

    def extend_temporal_window(self, timestamp: float | None = None) -> None:
        """Extend the temporal window.

        Args:
            timestamp: New end timestamp (defaults to now).
        """
        end_time = timestamp or time.time()
        self.temporal_window = (self.temporal_window[0], max(self.temporal_window[1], end_time))

    def decay_all(self, factor: float = 0.1) -> None:
        """Apply decay to all anchors and signals.

        Args:
            factor: Decay factor.
        """
        for anchor in self.thread_anchors:
            anchor.decay(factor)

        for signal in self.accumulated_signals:
            if hasattr(signal, "decay"):
                signal.decay(factor)

        # Prune stale anchors
        self.thread_anchors = [a for a in self.thread_anchors if not a.is_stale()]

        # Prune expired signals
        self.accumulated_signals = deque(
            [s for s in self.accumulated_signals if not (hasattr(s, "is_expired") and s.is_expired())],
            maxlen=100,
        )

        self._touch()

    def update_status(self) -> None:
        """Update context status based on current state."""
        if self.status == ContextStatus.DISSOLVED:
            return

        staleness_minutes = self.staleness / 60

        if staleness_minutes > 30:
            self.status = ContextStatus.STALE
        elif self.has_velocity and hasattr(self.cognitive_velocity, "drift"):
            if abs(self.cognitive_velocity.drift) > 0.5:
                self.status = ContextStatus.DRIFTING
            elif self.interaction_count > 5:
                self.status = ContextStatus.STABLE
            else:
                self.status = ContextStatus.ACTIVE
        elif self.interaction_count > 3:
            self.status = ContextStatus.ACTIVE
        else:
            self.status = ContextStatus.INITIALIZING

    def dissolve(self) -> None:
        """Mark context as dissolved."""
        self.status = ContextStatus.DISSOLVED
        self.thread_anchors.clear()
        self.accumulated_signals.clear()
        self.salience_map.clear()
        self.projections.clear()
        self._touch()

    def _touch(self) -> None:
        """Update last_updated timestamp."""
        self.last_updated = datetime.now()
        self.interaction_count += 1

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "session_id": self.session_id,
            "status": self.status.value,
            "is_established": self.is_established,
            "anchor_count": self.anchor_count,
            "signal_count": self.signal_count,
            "has_velocity": self.has_velocity,
            "interaction_count": self.interaction_count,
            "established_at": self.established_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "age_seconds": round(self.age_seconds, 1),
            "staleness_seconds": round(self.staleness, 1),
            "window_duration_seconds": round(self.window_duration_seconds, 1),
            "dominant_anchors": [a.to_dict() for a in self.get_dominant_anchors()],
            "salience_map": {k: round(v, 3) for k, v in self.salience_map.items()},
            "projections": self.projections,
            "velocity": (
                self.cognitive_velocity.to_dict()
                if self.has_velocity and hasattr(self.cognitive_velocity, "to_dict")
                else None
            ),
            "metadata": self.metadata,
        }

    @classmethod
    def create(cls, session_id: str, metadata: dict[str, Any] | None = None) -> VectionContext:
        """Factory method to create a new context.

        Args:
            session_id: Unique session identifier.
            metadata: Initial metadata.

        Returns:
            New VectionContext instance.
        """
        return cls(
            session_id=session_id,
            status=ContextStatus.INITIALIZING,
            metadata=metadata or {},
        )
