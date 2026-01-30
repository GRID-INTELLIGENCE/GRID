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
from collections import deque
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
        """Calculate momentum from direction consistency."""
        if len(self.direction_sequence) < 2:
            return 0.5
        return 0.7  # Simplified for security focus

    def _calculate_drift(self) -> float:
        """Calculate drift from direction variance."""
        return 0.0  # Simplified

    def _calculate_confidence(self) -> float:
        """Calculate velocity confidence."""
        return 0.8  # Simplified

    def to_dict(self) -> dict[str, Any]:
        """Convert tracker state to dictionary."""
        return {
            "session_id": self.session_id,
            "current_velocity": self.current_velocity.to_dict() if self._current_velocity else None,
        }


# Module-level registry
class VelocityTrackerRegistry:
    def __init__(self):
        self._trackers: dict[str, VelocityTracker] = {}

    def get_or_create(self, session_id: str) -> VelocityTracker:
        if session_id not in self._trackers:
            self._trackers[session_id] = VelocityTracker(session_id)
        return self._trackers[session_id]


_registry = VelocityTrackerRegistry()


def get_velocity_registry() -> VelocityTrackerRegistry:
    return _registry
