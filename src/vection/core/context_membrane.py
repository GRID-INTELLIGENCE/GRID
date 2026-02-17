"""ContextMembrane - Selective permeability for context.

Controls what enters and exits context awareness. Not everything
observed should persist. Not everything persisted should be accessible.

The membrane provides:
- Retention decisions based on salience + recency + relevance
- Decay functions to reduce stale context influence
- Salience scoring based on current cognitive state
- Filtering for context queries

This is the "immune system" of VECTION - protecting context integrity
while allowing valuable information to flow.
"""

from __future__ import annotations

import logging
import math
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, TypeVar

from vection.schemas.context_state import Anchor, AnchorType, VectionContext
from vection.schemas.emergence_signal import EmergenceSignal, SignalType
from vection.schemas.velocity_vector import DirectionCategory, VelocityVector

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetentionDecision(StrEnum):
    """Retention decision outcomes."""

    RETAIN = "retain"  # Keep in active context
    ARCHIVE = "archive"  # Move to long-term storage
    DECAY = "decay"  # Reduce salience, may expire
    DISCARD = "discard"  # Remove immediately


class MembranePermeability(StrEnum):
    """Membrane permeability levels."""

    CLOSED = "closed"  # Block all new context
    RESTRICTED = "restricted"  # Only high-salience passes
    NORMAL = "normal"  # Standard filtering
    PERMISSIVE = "permissive"  # Lower thresholds
    OPEN = "open"  # Accept all context


@dataclass
class RetentionRule:
    """A rule for context retention decisions."""

    name: str
    condition: Callable[[EmergenceSignal], bool]
    decision: RetentionDecision
    priority: int = 0  # Higher priority rules evaluated first
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DecayProfile:
    """Configuration for decay behavior."""

    base_rate: float = 0.05  # Base decay rate per interval
    min_salience: float = 0.05  # Minimum salience before discard
    recency_weight: float = 0.3  # Weight of recency in decay
    reinforcement_boost: float = 0.1  # Boost when reinforced
    max_age_hours: float = 24.0  # Maximum age before forced decay

    def calculate_decay(
        self,
        current_salience: float,
        age_seconds: float,
        staleness_seconds: float,
    ) -> float:
        """Calculate decay amount for a signal.

        Args:
            current_salience: Current salience value.
            age_seconds: Total age of signal.
            staleness_seconds: Time since last reinforcement.

        Returns:
            Amount to subtract from salience.
        """
        # Base decay
        decay = self.base_rate

        # Age-based acceleration (older signals decay faster)
        age_hours = age_seconds / 3600
        age_factor = 1.0 + (age_hours / 12.0) * 0.5  # +50% at 12 hours
        decay *= age_factor

        # Staleness penalty (unreinforced signals decay faster)
        staleness_hours = staleness_seconds / 3600
        if staleness_hours > 1.0:
            staleness_factor = 1.0 + (staleness_hours - 1.0) * 0.3
            decay *= staleness_factor

        # Low salience signals decay faster
        if current_salience < 0.3:
            decay *= 1.5

        return min(decay, current_salience)  # Don't go negative


@dataclass
class SalienceFactors:
    """Factors contributing to salience calculation."""

    base_salience: float
    recency_factor: float
    relevance_factor: float
    reinforcement_factor: float
    velocity_alignment: float
    final_salience: float


class ContextMembrane:
    """Selective permeability for context.

    The membrane controls what enters and exits context awareness,
    applying retention rules, decay functions, and salience scoring
    to maintain context integrity.

    Usage:
        membrane = ContextMembrane()
        if membrane.should_retain(signal):
            context.add_signal(signal)

        membrane.apply_decay(context)

        salience = membrane.score_salience(signal, velocity)
    """

    def __init__(
        self,
        permeability: MembranePermeability = MembranePermeability.NORMAL,
        decay_profile: DecayProfile | None = None,
        retain_threshold: float = 0.2,
        archive_threshold: float = 0.1,
    ) -> None:
        """Initialize the context membrane.

        Args:
            permeability: Initial permeability level.
            decay_profile: Decay configuration.
            retain_threshold: Minimum salience for retention.
            archive_threshold: Minimum salience for archival.
        """
        self._permeability = permeability
        self._decay_profile = decay_profile or DecayProfile()
        self._retain_threshold = retain_threshold
        self._archive_threshold = archive_threshold

        self._retention_rules: list[RetentionRule] = []
        self._archived_signals: deque[EmergenceSignal] = deque(maxlen=500)
        self._discarded_count: int = 0
        self._retained_count: int = 0
        self._decay_applications: int = 0

        self._current_velocity: VelocityVector | None = None
        self._relevance_keywords: set[str] = set()

        # Initialize default retention rules
        self._init_default_rules()

        logger.info(
            f"ContextMembrane initialized: permeability={permeability.value}, retain_threshold={retain_threshold}"
        )

    @property
    def permeability(self) -> MembranePermeability:
        """Get current permeability level."""
        return self._permeability

    @permeability.setter
    def permeability(self, value: MembranePermeability) -> None:
        """Set permeability level."""
        old_value = self._permeability
        self._permeability = value
        if old_value != value:
            logger.info(f"Membrane permeability changed: {old_value.value} → {value.value}")

    def set_velocity_context(self, velocity: VelocityVector) -> None:
        """Set current velocity for relevance scoring.

        Args:
            velocity: Current cognitive velocity.
        """
        self._current_velocity = velocity

    def add_relevance_keywords(self, keywords: list[str]) -> None:
        """Add keywords for relevance scoring.

        Args:
            keywords: Keywords to track.
        """
        self._relevance_keywords.update(kw.lower() for kw in keywords)

    def clear_relevance_keywords(self) -> None:
        """Clear relevance keywords."""
        self._relevance_keywords.clear()

    # =========================================================================
    # Retention Decisions
    # =========================================================================

    def should_retain(self, signal: EmergenceSignal) -> bool:
        """Determine if a signal should be retained.

        Args:
            signal: Signal to evaluate.

        Returns:
            True if signal should be retained in active context.
        """
        decision = self.evaluate_retention(signal)
        return decision == RetentionDecision.RETAIN

    def evaluate_retention(self, signal: EmergenceSignal) -> RetentionDecision:
        """Evaluate retention decision for a signal.

        Args:
            signal: Signal to evaluate.

        Returns:
            RetentionDecision enum value.
        """
        # Check permeability override
        if self._permeability == MembranePermeability.CLOSED:
            return RetentionDecision.DISCARD

        if self._permeability == MembranePermeability.OPEN:
            self._retained_count += 1
            return RetentionDecision.RETAIN

        # Apply custom rules first (sorted by priority)
        sorted_rules = sorted(self._retention_rules, key=lambda r: -r.priority)
        for rule in sorted_rules:
            try:
                if rule.condition(signal):
                    self._track_decision(rule.decision)
                    return rule.decision
            except Exception as e:
                logger.warning(f"Retention rule '{rule.name}' failed: {e}")

        # Default threshold-based decision
        salience = self.score_salience(signal).final_salience

        # Adjust thresholds based on permeability
        retain_threshold = self._adjust_threshold(self._retain_threshold)
        archive_threshold = self._adjust_threshold(self._archive_threshold)

        if salience >= retain_threshold:
            self._retained_count += 1
            return RetentionDecision.RETAIN
        elif salience >= archive_threshold:
            return RetentionDecision.ARCHIVE
        elif salience >= self._decay_profile.min_salience:
            return RetentionDecision.DECAY
        else:
            self._discarded_count += 1
            return RetentionDecision.DISCARD

    def _adjust_threshold(self, base_threshold: float) -> float:
        """Adjust threshold based on permeability."""
        adjustments = {
            MembranePermeability.RESTRICTED: 1.5,
            MembranePermeability.NORMAL: 1.0,
            MembranePermeability.PERMISSIVE: 0.7,
        }
        factor = adjustments.get(self._permeability, 1.0)
        return min(1.0, base_threshold * factor)

    def _track_decision(self, decision: RetentionDecision) -> None:
        """Track decision statistics."""
        if decision == RetentionDecision.RETAIN:
            self._retained_count += 1
        elif decision == RetentionDecision.DISCARD:
            self._discarded_count += 1

    def add_retention_rule(self, rule: RetentionRule) -> None:
        """Add a custom retention rule.

        Args:
            rule: Retention rule to add.
        """
        self._retention_rules.append(rule)
        logger.debug(f"Added retention rule: {rule.name}")

    def remove_retention_rule(self, name: str) -> bool:
        """Remove a retention rule by name.

        Args:
            name: Rule name.

        Returns:
            True if rule was removed.
        """
        for i, rule in enumerate(self._retention_rules):
            if rule.name == name:
                self._retention_rules.pop(i)
                return True
        return False

    # =========================================================================
    # Decay Functions
    # =========================================================================

    def apply_decay(self, context: VectionContext) -> dict[str, int]:
        """Apply decay to a context's signals and anchors.

        Args:
            context: Context to apply decay to.

        Returns:
            Statistics about decay application.
        """
        self._decay_applications += 1
        stats = {
            "signals_decayed": 0,
            "signals_archived": 0,
            "signals_discarded": 0,
            "anchors_decayed": 0,
            "anchors_removed": 0,
        }

        # Decay signals
        signals_to_keep = []
        for signal in context.accumulated_signals:
            if not isinstance(signal, EmergenceSignal):
                signals_to_keep.append(signal)
                continue

            decay_amount = self._decay_profile.calculate_decay(
                current_salience=signal.salience,
                age_seconds=signal.age_seconds,
                staleness_seconds=signal.staleness,
            )

            signal.decay(decay_amount)
            stats["signals_decayed"] += 1

            # Re-evaluate retention after decay
            if signal.is_expired() or signal.effective_salience < self._decay_profile.min_salience:
                self._archive_signal(signal)
                stats["signals_discarded"] += 1
            else:
                signals_to_keep.append(signal)

        # Update context signals
        context.accumulated_signals = deque(signals_to_keep, maxlen=100)

        # Decay anchors
        for anchor in context.thread_anchors:
            anchor.decay(self._decay_profile.base_rate)
            stats["anchors_decayed"] += 1

        # Remove stale anchors
        original_anchor_count = len(context.thread_anchors)
        context.thread_anchors = [a for a in context.thread_anchors if not a.is_stale()]
        stats["anchors_removed"] = original_anchor_count - len(context.thread_anchors)

        logger.debug(
            f"Decay applied to context {context.session_id}: "
            f"{stats['signals_decayed']} signals, {stats['anchors_decayed']} anchors"
        )

        return stats

    def reinforce(self, signal: EmergenceSignal, boost: float | None = None) -> None:
        """Reinforce a signal (opposite of decay).

        Args:
            signal: Signal to reinforce.
            boost: Optional boost amount (defaults to profile setting).
        """
        boost_amount = boost if boost is not None else self._decay_profile.reinforcement_boost
        signal.reinforce(boost_amount)

    def _archive_signal(self, signal: EmergenceSignal) -> None:
        """Archive a signal for long-term storage."""
        self._archived_signals.append(signal)

    def get_archived_signals(self, limit: int = 50) -> list[EmergenceSignal]:
        """Get archived signals.

        Args:
            limit: Maximum signals to return.

        Returns:
            List of archived signals.
        """
        return list(self._archived_signals)[-limit:]

    # =========================================================================
    # Salience Scoring
    # =========================================================================

    def score_salience(
        self,
        signal: EmergenceSignal,
        velocity: VelocityVector | None = None,
    ) -> SalienceFactors:
        """Score the salience of a signal.

        Args:
            signal: Signal to score.
            velocity: Optional velocity for alignment scoring.

        Returns:
            SalienceFactors with detailed breakdown.
        """
        velocity = velocity or self._current_velocity

        # Base salience from signal
        base_salience = signal.salience

        # Recency factor (more recent = more salient)
        staleness_hours = signal.staleness / 3600
        recency_factor = max(0.0, 1.0 - (staleness_hours / 4.0))  # Decay over 4 hours

        # Relevance factor (keyword matching)
        relevance_factor = self._calculate_relevance(signal)

        # Reinforcement factor (evidence count)
        reinforcement_factor = min(1.0, math.log1p(signal.source_count) / 3.0)

        # Velocity alignment factor
        velocity_alignment = self._calculate_velocity_alignment(signal, velocity)

        # Combine factors (weighted average)
        weights = {
            "base": 0.3,
            "recency": 0.2,
            "relevance": 0.25,
            "reinforcement": 0.15,
            "velocity": 0.1,
        }

        final_salience = (
            base_salience * weights["base"]
            + recency_factor * weights["recency"]
            + relevance_factor * weights["relevance"]
            + reinforcement_factor * weights["reinforcement"]
            + velocity_alignment * weights["velocity"]
        )

        # Apply confidence scaling
        final_salience *= signal.confidence

        return SalienceFactors(
            base_salience=base_salience,
            recency_factor=recency_factor,
            relevance_factor=relevance_factor,
            reinforcement_factor=reinforcement_factor,
            velocity_alignment=velocity_alignment,
            final_salience=min(1.0, final_salience),
        )

    def _calculate_relevance(self, signal: EmergenceSignal) -> float:
        """Calculate relevance factor based on keywords."""
        if not self._relevance_keywords:
            return 0.5  # Neutral if no keywords set

        description_words = set(signal.description.lower().split())
        matches = description_words & self._relevance_keywords

        if not matches:
            return 0.2  # Low relevance

        # Scale by match ratio
        relevance = len(matches) / len(self._relevance_keywords)
        return min(1.0, relevance + 0.3)  # Boost matched signals

    def _calculate_velocity_alignment(
        self,
        signal: EmergenceSignal,
        velocity: VelocityVector | None,
    ) -> float:
        """Calculate alignment with current velocity."""
        if velocity is None:
            return 0.5  # Neutral if no velocity

        # Map signal types to direction categories
        type_direction_affinity = {
            SignalType.CORRELATION: [
                DirectionCategory.INVESTIGATION,
                DirectionCategory.SYNTHESIS,
            ],
            SignalType.CLUSTER: [
                DirectionCategory.EXPLORATION,
                DirectionCategory.SYNTHESIS,
            ],
            SignalType.SEQUENCE: [
                DirectionCategory.EXECUTION,
                DirectionCategory.INVESTIGATION,
            ],
            SignalType.DEVIATION: [
                DirectionCategory.INVESTIGATION,
                DirectionCategory.REFLECTION,
            ],
            SignalType.RECURRENCE: [
                DirectionCategory.EXECUTION,
                DirectionCategory.REFLECTION,
            ],
        }

        affinities = type_direction_affinity.get(signal.signal_type, [])
        if velocity.direction in affinities:
            return 0.8 + (velocity.momentum * 0.2)  # High alignment

        return 0.3  # Low alignment

    # =========================================================================
    # Filtering
    # =========================================================================

    def filter_signals(
        self,
        signals: list[EmergenceSignal],
        min_salience: float = 0.0,
        signal_types: list[SignalType] | None = None,
        max_age_seconds: float | None = None,
    ) -> list[EmergenceSignal]:
        """Filter signals based on criteria.

        Args:
            signals: Signals to filter.
            min_salience: Minimum salience threshold.
            signal_types: Optional list of allowed types.
            max_age_seconds: Optional maximum age.

        Returns:
            Filtered list of signals.
        """
        filtered = []

        for signal in signals:
            # Salience check
            salience = self.score_salience(signal).final_salience
            if salience < min_salience:
                continue

            # Type check
            if signal_types is not None and signal.signal_type not in signal_types:
                continue

            # Age check
            if max_age_seconds is not None and signal.age_seconds > max_age_seconds:
                continue

            filtered.append(signal)

        # Sort by salience
        return sorted(
            filtered,
            key=lambda s: self.score_salience(s).final_salience,
            reverse=True,
        )

    def filter_anchors(
        self,
        anchors: list[Anchor],
        min_weight: float = 0.0,
        anchor_types: list[AnchorType] | None = None,
        max_staleness_hours: float | None = None,
    ) -> list[Anchor]:
        """Filter anchors based on criteria.

        Args:
            anchors: Anchors to filter.
            min_weight: Minimum effective weight.
            anchor_types: Optional list of allowed types.
            max_staleness_hours: Optional maximum staleness.

        Returns:
            Filtered list of anchors.
        """
        filtered = []

        for anchor in anchors:
            # Weight check
            if anchor.effective_weight < min_weight:
                continue

            # Type check
            if anchor_types is not None and anchor.anchor_type not in anchor_types:
                continue

            # Staleness check
            if max_staleness_hours is not None:
                staleness_hours = anchor.staleness / 3600
                if staleness_hours > max_staleness_hours:
                    continue

            filtered.append(anchor)

        # Sort by effective weight
        return sorted(filtered, key=lambda a: a.effective_weight, reverse=True)

    # =========================================================================
    # Statistics and State
    # =========================================================================

    def get_stats(self) -> dict[str, Any]:
        """Get membrane statistics.

        Returns:
            Dictionary with membrane statistics.
        """
        return {
            "permeability": self._permeability.value,
            "retain_threshold": self._retain_threshold,
            "archive_threshold": self._archive_threshold,
            "retained_count": self._retained_count,
            "discarded_count": self._discarded_count,
            "archived_count": len(self._archived_signals),
            "decay_applications": self._decay_applications,
            "custom_rules": len(self._retention_rules),
            "relevance_keywords": len(self._relevance_keywords),
            "has_velocity_context": self._current_velocity is not None,
        }

    def reset_stats(self) -> None:
        """Reset statistics counters."""
        self._retained_count = 0
        self._discarded_count = 0
        self._decay_applications = 0

    # =========================================================================
    # Default Rules
    # =========================================================================

    def _init_default_rules(self) -> None:
        """Initialize default retention rules."""
        # Always retain high-confidence deviations
        self.add_retention_rule(
            RetentionRule(
                name="retain_deviations",
                condition=lambda s: s.signal_type == SignalType.DEVIATION and s.confidence > 0.7,
                decision=RetentionDecision.RETAIN,
                priority=100,
            )
        )

        # Always retain highly reinforced signals
        self.add_retention_rule(
            RetentionRule(
                name="retain_reinforced",
                condition=lambda s: s.source_count >= 5 and s.confidence > 0.5,
                decision=RetentionDecision.RETAIN,
                priority=90,
            )
        )

        # Discard very old, low-confidence signals
        self.add_retention_rule(
            RetentionRule(
                name="discard_stale",
                condition=lambda s: s.age_seconds > 7200 and s.confidence < 0.3,
                decision=RetentionDecision.DISCARD,
                priority=80,
            )
        )


# Module-level convenience functions
_membrane: ContextMembrane | None = None


def get_membrane() -> ContextMembrane:
    """Get the global context membrane instance.

    Returns:
        ContextMembrane singleton.
    """
    global _membrane
    if _membrane is None:
        _membrane = ContextMembrane()
    return _membrane
