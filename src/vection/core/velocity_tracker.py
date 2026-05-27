"""VelocityTracker - Cognitive motion tracking module.

Tracks cognitive velocity over time for sessions:
- Direction: where the user is heading cognitively
- Magnitude: speed of cognitive activity
- Momentum: tendency to continue current direction
- Drift: deviation from expected trajectory
- Projection: predicted future context needs

This module provides the "motion" in context emergence - understanding
not just where the user is, but where they're going.
"""

from __future__ import annotations

import logging
import time
from collections import OrderedDict, deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from vection.schemas.velocity_vector import DirectionCategory, VelocityVector

logger = logging.getLogger(__name__)


@dataclass
class VelocitySnapshot:
    """Point-in-time velocity measurement."""

    timestamp: float
    velocity: VelocityVector
    event_type: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def age_seconds(self) -> float:
        """Get age of this snapshot in seconds."""
        return time.time() - self.timestamp


@dataclass
class VelocityTrend:
    """Trend analysis over velocity history."""

    direction_stability: float  # 0.0 = chaotic, 1.0 = consistent
    magnitude_trend: float  # negative = slowing, positive = accelerating
    momentum_trend: float  # negative = losing, positive = gaining
    drift_trend: float  # negative = converging, positive = diverging
    dominant_direction: DirectionCategory
    transition_count: int  # Number of direction changes
    analysis_window_seconds: float


class VelocityTracker:
    """Tracks cognitive velocity for a session.

    Monitors the direction, speed, momentum, and drift of cognitive
    activity to enable prediction of future context needs.
    """

    def __init__(
        self,
        session_id: str,
        history_size: int = 50,
        direction_history_size: int = 20,
    ) -> None:
        """Initialize velocity tracker."""
        self.session_id = session_id
        self.history: deque[VelocitySnapshot] = deque(maxlen=history_size)
        self.direction_sequence: deque[str] = deque(maxlen=direction_history_size)
        self.intent_sequence: deque[str] = deque(maxlen=direction_history_size)
        self.topic_frequency: dict[str, int] = {}
        self._event_timestamps: deque[float] = deque(maxlen=50)
        self._current_velocity: VelocityVector | None = None
        self._created_at: datetime = datetime.now()
        self._last_update: datetime = datetime.now()

    @property
    def current_velocity(self) -> VelocityVector:
        """Get current velocity vector."""
        if self._current_velocity is None:
            return VelocityVector.zero()
        return self._current_velocity

    def track_event(
        self,
        event_data: dict[str, Any],
        event_type: str | None = None,
    ) -> VelocityVector:
        """Track an event and update velocity.

        Security: Velocity Anomaly Detection (AESP) enforced.
        """
        now = time.time()

        # Verify timestamp integrity
        try:
            from cognition.patterns.security.velocity_anomaly import get_velocity_anomaly_detector

            ts_list = list(self._event_timestamps) + [now]
            if not get_velocity_anomaly_detector().validate_timestamp_integrity(ts_list):
                # Anomaly detected! Force monotonicity to neutralize spoofing.
                if self._event_timestamps:
                    now = max(now, self._event_timestamps[-1] + 0.001)
        except ImportError:
            pass

        self._event_timestamps.append(now)

        # Extract direction from event
        direction = self._extract_direction(event_data)
        self.direction_sequence.append(direction)

        # Extract and track intent
        intent = self._extract_intent(event_data)
        if intent:
            self.intent_sequence.append(intent)

        # Track topics
        topics = self._extract_topics(event_data)
        for topic in topics:
            self.topic_frequency[topic] = self.topic_frequency.get(topic, 0) + 1

        # Calculate velocity components
        direction_category = self._categorize_direction(direction)
        magnitude = self._calculate_magnitude()
        momentum = self._calculate_momentum()
        drift = self._calculate_drift()
        confidence = self._calculate_confidence()

        # Create new velocity vector
        velocity = VelocityVector(
            direction=direction_category,
            direction_detail=direction,
            magnitude=magnitude,
            momentum=momentum,
            drift=drift,
            confidence=confidence,
            history=list(self.direction_sequence)[-10:],
        )

        # Store snapshot
        snapshot = VelocitySnapshot(
            timestamp=now,
            velocity=velocity,
            event_type=event_type,
            metadata={"topics": topics, "intent": intent},
        )
        self.history.append(snapshot)

        self._current_velocity = velocity
        self._last_update = datetime.now()

        logger.debug(
            f"Velocity updated: direction={direction_category.value}, "
            f"magnitude={magnitude:.2f}, momentum={momentum:.2f}"
        )

        return velocity

    def _extract_direction(self, event_data: dict[str, Any]) -> str:
        """Extract direction from event data."""
        intent = self._extract_intent(event_data)
        if intent:
            return intent
        return "unknown"

    def _extract_intent(self, event_data: dict[str, Any]) -> str | None:
        """Extract intent from event data."""
        action = event_data.get("action") or event_data.get("type")
        if action:
            return str(action)
        return None

    def _extract_topics(self, event_data: dict[str, Any]) -> list[str]:
        """Extract topics from event data."""
        topics: list[str] = []
        content = event_data.get("content") or event_data.get("query") or ""
        if isinstance(content, str):
            words = content.lower().split()
            topics.extend([w for w in words if len(w) > 4 and w.isalpha()][:5])
        return topics

    def _categorize_direction(self, direction: str) -> DirectionCategory:
        """Categorize direction string to enum."""
        direction_lower = direction.lower()
        if "analyze" in direction_lower or "debug" in direction_lower:
            return DirectionCategory.INVESTIGATION
        if "create" in direction_lower or "run" in direction_lower:
            return DirectionCategory.EXECUTION
        return DirectionCategory.UNKNOWN

    def _calculate_magnitude(self) -> float:
        """Calculate velocity magnitude from event rate."""
        if len(self._event_timestamps) < 2:
            return 0.3
        time_span = self._event_timestamps[-1] - self._event_timestamps[0]
        if time_span <= 0:
            return 0.5
        rate = len(self._event_timestamps) / time_span
        return min(1.0, rate * 0.5 + 0.2)

    def _calculate_momentum(self) -> float:
        """Calculate momentum as direction-consistency rate over recent history.

        1.0 = every consecutive step kept the same direction (pure momentum)
        0.0 = every step reversed direction (no momentum)
        """
        seq = list(self.direction_sequence)
        if len(seq) < 2:
            return 0.5
        same = sum(1 for a, b in zip(seq, seq[1:]) if a == b)
        return same / (len(seq) - 1)

    def _calculate_drift(self) -> float:
        """Calculate drift as the rate of direction changes over recent history.

        0.0 = perfectly stable (same direction throughout)
        1.0 = maximum churn (direction flips on every step)
        """
        seq = list(self.direction_sequence)
        if len(seq) < 2:
            return 0.0
        transitions = sum(1 for a, b in zip(seq, seq[1:]) if a != b)
        return transitions / (len(seq) - 1)

    def _calculate_confidence(self) -> float:
        """Calculate confidence from observation depth.

        Scales linearly from 0.0 (no history) to 1.0 at 20+ events.
        """
        return min(1.0, len(self.history) / 20.0)

    def to_dict(self) -> dict[str, Any]:
        """Convert tracker state to dictionary."""
        return {
            "session_id": self.session_id,
            "current_velocity": self.current_velocity.to_dict() if self._current_velocity else None,
        }


# Module-level registry
DEFAULT_MAX_TRACKERS = 10_000


class VelocityTrackerRegistry:
    """Bounded LRU registry of per-session VelocityTrackers.

    The admission gate calls get_or_create() on every request keyed by entity_id
    (which includes per-IP keys for anonymous traffic). Without a cap, an attacker
    rotating entity-ids or IPs would grow this map without bound. Eviction is
    least-recently-used: the tracker untouched for the longest time is dropped first
    once the cap is reached. An evicted entity simply rebuilds drift history from
    scratch on its next request — the same cold-start behaviour as a fresh process.
    """

    def __init__(self, max_trackers: int = DEFAULT_MAX_TRACKERS) -> None:
        self._max_trackers = max_trackers
        self._trackers: OrderedDict[str, VelocityTracker] = OrderedDict()

    def get_or_create(self, session_id: str) -> VelocityTracker:
        tracker = self._trackers.get(session_id)
        if tracker is not None:
            self._trackers.move_to_end(session_id)
            return tracker
        tracker = VelocityTracker(session_id)
        self._trackers[session_id] = tracker
        if len(self._trackers) > self._max_trackers:
            evicted_id, _ = self._trackers.popitem(last=False)
            logger.debug("velocity_registry.evicted session=%s", evicted_id)
        return tracker

    def __len__(self) -> int:
        return len(self._trackers)


_registry = VelocityTrackerRegistry()


def get_velocity_registry() -> VelocityTrackerRegistry:
    return _registry
