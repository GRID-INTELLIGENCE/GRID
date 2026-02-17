"""EmergenceSignal - Discovered pattern signals.

Represents patterns that emerge from observation of request streams.
These are not predefined rules - they are discovered correlations,
clusters, and signals that surface from behavior analysis.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


class SignalType(StrEnum):
    """Types of emergent signals."""

    CORRELATION = "correlation"  # Co-occurrence pattern
    CLUSTER = "cluster"  # Grouped behavior pattern
    SEQUENCE = "sequence"  # Temporal sequence pattern
    DEVIATION = "deviation"  # Anomaly from baseline
    RECURRENCE = "recurrence"  # Repeating pattern
    CONVERGENCE = "convergence"  # Multiple signals aligning
    TRANSITION = "transition"  # State change pattern
    SATURATION = "saturation"  # Pattern reaching threshold


class SignalStrength(StrEnum):
    """Signal strength levels."""

    WEAK = "weak"  # 0.0 - 0.3
    MODERATE = "moderate"  # 0.3 - 0.6
    STRONG = "strong"  # 0.6 - 0.8
    DEFINITIVE = "definitive"  # 0.8 - 1.0


@dataclass
class EmergenceSignal:
    """A signal representing an emergent pattern.

    Signals are discovered, not defined. They represent correlations,
    clusters, and patterns that surface from observing request streams
    without explicit rules telling us what to look for.

    Attributes:
        signal_id: Unique identifier for this signal.
        signal_type: Category of emergent pattern.
        description: Human-readable description of what emerged.
        confidence: Confidence in signal validity (0.0 - 1.0).
        salience: Current relevance/importance (0.0 - 1.0).
        source_count: Number of observations contributing to this signal.
        first_observed: When signal was first detected.
        last_observed: Most recent observation.
        decay_rate: How fast this signal loses salience.
        metadata: Additional signal-specific data.
        contributing_events: Event IDs that contributed to this signal.
    """

    signal_id: str
    signal_type: SignalType
    description: str
    confidence: float
    salience: float
    source_count: int = 1
    first_observed: datetime = field(default_factory=datetime.now)
    last_observed: datetime = field(default_factory=datetime.now)
    decay_rate: float = 0.1
    metadata: dict[str, Any] = field(default_factory=dict)
    contributing_events: list[str] = field(default_factory=list)
    _creator_hash: str = field(default="unknown", repr=False)

    def __post_init__(self) -> None:
        """Validate signal components and perform security fingerprinting."""
        self.confidence = max(0.0, min(1.0, self.confidence))
        self.salience = max(0.0, min(1.0, self.salience))
        self.decay_rate = max(0.0, min(1.0, self.decay_rate))
        self.source_count = max(1, self.source_count)

        # Behind the curtain: Capture creator fingerprint
        try:
            from cognition.patterns.security.cognitive_fingerprint import get_cognitive_fingerprint

            self._creator_hash = get_cognitive_fingerprint()
        except ImportError:
            pass

    @property
    def strength(self) -> SignalStrength:
        """Get signal strength based on confidence.

        Returns:
            SignalStrength enum value.
        """
        if self.confidence < 0.3:
            return SignalStrength.WEAK
        elif self.confidence < 0.6:
            return SignalStrength.MODERATE
        elif self.confidence < 0.8:
            return SignalStrength.STRONG
        return SignalStrength.DEFINITIVE

    @property
    def age_seconds(self) -> float:
        """Get signal age in seconds.

        Returns:
            Seconds since first observation.
        """
        return (datetime.now(timezone.utc) - self.first_observed).total_seconds()

    @property
    def staleness(self) -> float:
        """Get signal staleness (time since last observation).

        Returns:
            Seconds since last observation.
        """
        return (datetime.now(timezone.utc) - self.last_observed).total_seconds()

    @property
    def effective_salience(self) -> float:
        """Get salience with decay applied.

        Returns:
            Salience adjusted for time decay.
        """
        staleness_hours = self.staleness / 3600
        decay_factor = max(0.0, 1.0 - (self.decay_rate * staleness_hours))
        return self.salience * decay_factor

    def reinforce(self, boost: float = 0.1, event_id: str | None = None, session_id: str | None = None):
        """
        Reinforce the signal with a salience boost.

        Security: This is a null-wrapped entry point.
        """
        try:
            from cognition.patterns.security.null_wrapper import _wrapped_reinforce

            # Silent return - no resistance visible to attacker
            return _wrapped_reinforce(self, boost, event_id, session_id)
        except ImportError:
            # Fallback to standard reinforcement if security module missing
            self.source_count += 1
            self.last_observed = datetime.now(timezone.utc)
            self.salience = min(1.0, self.salience + boost)
            self.confidence = min(1.0, self.confidence + boost * 0.5)

            if event_id and event_id not in self.contributing_events:
                self.contributing_events.append(event_id)
                # Keep only recent contributing events
                if len(self.contributing_events) > 100:
                    self.contributing_events = self.contributing_events[-100:]

    def decay(self, factor: float | None = None) -> None:
        """Apply decay to signal salience.

        Args:
            factor: Optional explicit decay factor.
        """
        decay = factor if factor is not None else self.decay_rate
        self.salience = max(0.0, self.salience * (1.0 - decay))

    def merge(self, other: EmergenceSignal) -> EmergenceSignal:
        """Merge with another signal of same type.

        Args:
            other: Signal to merge with.

        Returns:
            New merged signal.
        """
        if self.signal_type != other.signal_type:
            raise ValueError("Cannot merge signals of different types")

        combined_sources = self.source_count + other.source_count
        weight_self = self.source_count / combined_sources
        weight_other = other.source_count / combined_sources

        merged_metadata = {**self.metadata, **other.metadata}
        merged_events = list(set(self.contributing_events + other.contributing_events))

        return EmergenceSignal(
            signal_id=f"{self.signal_id}+{other.signal_id}",
            signal_type=self.signal_type,
            description=f"Merged: {self.description} | {other.description}",
            confidence=self.confidence * weight_self + other.confidence * weight_other,
            salience=max(self.salience, other.salience),
            source_count=combined_sources,
            first_observed=min(self.first_observed, other.first_observed),
            last_observed=max(self.last_observed, other.last_observed),
            decay_rate=(self.decay_rate + other.decay_rate) / 2,
            metadata=merged_metadata,
            contributing_events=merged_events[-100:],
        )

    def matches_query(self, query: str) -> float:
        """Score how well signal matches a query.

        Args:
            query: Query string to match against.

        Returns:
            Match score (0.0 - 1.0).
        """
        if not query:
            return 0.0

        query_lower = query.lower()
        description_lower = self.description.lower()
        signal_type_str = self.signal_type.value.lower()

        score = 0.0

        # Direct substring match
        if query_lower in description_lower:
            score += 0.5

        # Word overlap
        query_words = set(query_lower.split())
        description_words = set(description_lower.split())
        overlap = len(query_words & description_words)
        if query_words:
            score += 0.3 * (overlap / len(query_words))

        # Type match
        if query_lower in signal_type_str or signal_type_str in query_lower:
            score += 0.2

        # Metadata keyword match
        metadata_str = str(self.metadata).lower()
        if query_lower in metadata_str:
            score += 0.1

        return min(1.0, score * self.effective_salience)

    def is_expired(self, max_staleness_hours: float = 24.0) -> bool:
        """Check if signal has expired.

        Args:
            max_staleness_hours: Maximum hours without observation.

        Returns:
            True if signal should be discarded.
        """
        staleness_hours = self.staleness / 3600
        return staleness_hours > max_staleness_hours or self.effective_salience < 0.05

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary with all signal components.
        """
        return {
            "signal_id": self.signal_id,
            "signal_type": self.signal_type.value,
            "description": self.description,
            "confidence": round(self.confidence, 3),
            "salience": round(self.salience, 3),
            "effective_salience": round(self.effective_salience, 3),
            "strength": self.strength.value,
            "source_count": self.source_count,
            "first_observed": self.first_observed.isoformat(),
            "last_observed": self.last_observed.isoformat(),
            "age_seconds": round(self.age_seconds, 1),
            "staleness_seconds": round(self.staleness, 1),
            "decay_rate": self.decay_rate,
            "metadata": self.metadata,
            "contributing_event_count": len(self.contributing_events),
        }

    @classmethod
    def create(
        cls,
        signal_type: SignalType,
        description: str,
        confidence: float = 0.5,
        salience: float = 0.5,
        metadata: dict[str, Any] | None = None,
        event_id: str | None = None,
    ) -> EmergenceSignal:
        """Factory method to create a new signal.

        Args:
            signal_type: Type of emergent pattern.
            description: Description of what emerged.
            confidence: Initial confidence.
            salience: Initial salience.
            metadata: Additional metadata.
            event_id: Contributing event ID.

        Returns:
            New EmergenceSignal instance.
        """
        # Generate deterministic ID from type and description
        hash_input = f"{signal_type.value}:{description}:{time.time()}"
        signal_id = hashlib.md5(hash_input.encode()).hexdigest()[:12]

        return cls(
            signal_id=signal_id,
            signal_type=signal_type,
            description=description,
            confidence=confidence,
            salience=salience,
            metadata=metadata or {},
            contributing_events=[event_id] if event_id else [],
        )

    @classmethod
    def correlation(
        cls,
        description: str,
        items: list[str],
        confidence: float = 0.5,
    ) -> EmergenceSignal:
        """Create a correlation signal.

        Args:
            description: Description of correlation.
            items: Items that correlate.
            confidence: Correlation confidence.

        Returns:
            New correlation EmergenceSignal.
        """
        return cls.create(
            signal_type=SignalType.CORRELATION,
            description=description,
            confidence=confidence,
            salience=0.6,
            metadata={"correlated_items": items},
        )

    @classmethod
    def cluster(
        cls,
        description: str,
        members: list[str],
        confidence: float = 0.5,
    ) -> EmergenceSignal:
        """Create a cluster signal.

        Args:
            description: Description of cluster.
            members: Cluster members.
            confidence: Cluster confidence.

        Returns:
            New cluster EmergenceSignal.
        """
        return cls.create(
            signal_type=SignalType.CLUSTER,
            description=description,
            confidence=confidence,
            salience=0.5,
            metadata={"cluster_members": members, "cluster_size": len(members)},
        )

    @classmethod
    def sequence(
        cls,
        description: str,
        steps: list[str],
        confidence: float = 0.5,
    ) -> EmergenceSignal:
        """Create a sequence signal.

        Args:
            description: Description of sequence.
            steps: Sequence steps.
            confidence: Sequence confidence.

        Returns:
            New sequence EmergenceSignal.
        """
        return cls.create(
            signal_type=SignalType.SEQUENCE,
            description=description,
            confidence=confidence,
            salience=0.7,
            metadata={"sequence_steps": steps, "sequence_length": len(steps)},
        )

    @classmethod
    def deviation(
        cls,
        description: str,
        expected: str,
        actual: str,
        magnitude: float = 0.5,
    ) -> EmergenceSignal:
        """Create a deviation signal.

        Args:
            description: Description of deviation.
            expected: Expected behavior.
            actual: Actual behavior.
            magnitude: Deviation magnitude.

        Returns:
            New deviation EmergenceSignal.
        """
        return cls.create(
            signal_type=SignalType.DEVIATION,
            description=description,
            confidence=0.7,
            salience=0.8,  # Deviations are typically salient
            metadata={
                "expected": expected,
                "actual": actual,
                "deviation_magnitude": magnitude,
            },
        )
