"""VelocityVector - Cognitive motion tracking.

Tracks where a session is heading, not just where it is.
Provides direction, magnitude, momentum, drift, and projection capabilities.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class DirectionCategory(StrEnum):
    """High-level cognitive direction categories."""

    EXPLORATION = "exploration"  # Broad, discovery-oriented
    INVESTIGATION = "investigation"  # Deep-dive, causal analysis
    EXECUTION = "execution"  # Task completion focus
    SYNTHESIS = "synthesis"  # Combining, creating
    REFLECTION = "reflection"  # Review, retrospection
    TRANSITION = "transition"  # Shifting between modes
    UNKNOWN = "unknown"  # Insufficient data


@dataclass
class VelocityVector:
    """Cognitive motion representation.

    Captures not just current state but movement through cognitive space.
    Enables prediction of future context needs based on trajectory.

    Attributes:
        direction: Primary cognitive direction (category).
        direction_detail: Specific direction description.
        magnitude: Speed of cognitive motion (0.0 - 1.0).
        momentum: Tendency to continue current trajectory (0.0 - 1.0).
        drift: Deviation from expected path (-1.0 to 1.0).
        confidence: Certainty of trajectory assessment (0.0 - 1.0).
        timestamp: When this vector was calculated.
        history: Recent direction changes for pattern detection.
    """

    direction: DirectionCategory
    direction_detail: str
    magnitude: float
    momentum: float
    drift: float
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)
    history: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate vector components."""
        self.magnitude = max(0.0, min(1.0, self.magnitude))
        self.momentum = max(0.0, min(1.0, self.momentum))
        self.drift = max(-1.0, min(1.0, self.drift))
        self.confidence = max(0.0, min(1.0, self.confidence))

    def project(self, steps: int = 3) -> list[str]:
        """Project likely future context needs.

        Args:
            steps: Number of steps to project forward.

        Returns:
            List of projected context need descriptions.
        """
        if self.confidence < 0.3:
            return ["DATA_MISSING: insufficient trajectory confidence"]

        projections: list[str] = []
        current_momentum = self.momentum

        for i in range(steps):
            # Decay momentum over projection steps
            step_confidence = current_momentum * (0.8**i)

            if step_confidence < 0.2:
                break

            projection = self._project_step(i + 1, step_confidence)
            if projection:
                projections.append(projection)

            current_momentum *= 0.9  # Momentum decay

        return projections if projections else ["projection_uncertain"]

    def _project_step(self, step: int, confidence: float) -> str | None:
        """Generate projection for a single step.

        Args:
            step: Step number (1-based).
            confidence: Confidence for this step.

        Returns:
            Projection description or None if uncertain.
        """
        direction_projections = {
            DirectionCategory.EXPLORATION: [
                "broader_context_needed",
                "related_topics_retrieval",
                "discovery_support",
            ],
            DirectionCategory.INVESTIGATION: [
                "causal_analysis_context",
                "root_cause_patterns",
                "diagnostic_support",
            ],
            DirectionCategory.EXECUTION: [
                "task_completion_context",
                "action_guidance",
                "implementation_patterns",
            ],
            DirectionCategory.SYNTHESIS: [
                "integration_context",
                "combination_patterns",
                "creative_support",
            ],
            DirectionCategory.REFLECTION: [
                "retrospective_context",
                "summary_patterns",
                "evaluation_support",
            ],
            DirectionCategory.TRANSITION: [
                "context_shift_preparation",
                "bridging_context",
                "mode_switch_support",
            ],
            DirectionCategory.UNKNOWN: [
                "general_context",
                "exploratory_support",
                "baseline_retrieval",
            ],
        }

        projections = direction_projections.get(self.direction, [])
        if step <= len(projections):
            return projections[step - 1]
        return None

    def indicates(self, pattern: str) -> bool:
        """Check if velocity indicates a specific pattern.

        Args:
            pattern: Pattern string to check against.

        Returns:
            True if velocity indicates the pattern.
        """
        pattern_lower = pattern.lower()

        # Direction-based indicators
        direction_indicators = {
            "ml_heavy_workload": self.direction == DirectionCategory.EXECUTION and self.magnitude > 0.7,
            "deep_analysis": self.direction == DirectionCategory.INVESTIGATION and self.momentum > 0.6,
            "exploration_mode": self.direction == DirectionCategory.EXPLORATION and self.drift < 0.3,
            "synthesis_needed": self.direction == DirectionCategory.SYNTHESIS,
            "high_momentum": self.momentum > 0.7,
            "drifting": abs(self.drift) > 0.5,
            "stable_trajectory": abs(self.drift) < 0.2 and self.momentum > 0.5,
            "uncertain": self.confidence < 0.4,
        }

        return direction_indicators.get(pattern_lower, False)

    def combine(self, other: VelocityVector, weight: float = 0.5) -> VelocityVector:
        """Combine with another velocity vector.

        Args:
            other: Another velocity vector to combine with.
            weight: Weight for the other vector (0.0 - 1.0).

        Returns:
            New combined velocity vector.
        """
        weight = max(0.0, min(1.0, weight))
        self_weight = 1.0 - weight

        # Choose dominant direction based on confidence-weighted magnitude
        self_score = self.magnitude * self.confidence * self_weight
        other_score = other.magnitude * other.confidence * weight

        dominant_direction = self.direction if self_score >= other_score else other.direction
        dominant_detail = self.direction_detail if self_score >= other_score else other.direction_detail

        return VelocityVector(
            direction=dominant_direction,
            direction_detail=dominant_detail,
            magnitude=self.magnitude * self_weight + other.magnitude * weight,
            momentum=self.momentum * self_weight + other.momentum * weight,
            drift=self.drift * self_weight + other.drift * weight,
            confidence=(self.confidence + other.confidence) / 2,
            history=self.history[-5:] + other.history[-5:],
        )

    def decay(self, factor: float = 0.9) -> VelocityVector:
        """Apply decay to velocity components.

        Args:
            factor: Decay factor (0.0 - 1.0).

        Returns:
            Decayed velocity vector.
        """
        return VelocityVector(
            direction=self.direction,
            direction_detail=self.direction_detail,
            magnitude=self.magnitude * factor,
            momentum=self.momentum * factor,
            drift=self.drift * factor,
            confidence=self.confidence * factor,
            history=self.history,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary with all vector components.
        """
        return {
            "direction": self.direction.value,
            "direction_detail": self.direction_detail,
            "magnitude": round(self.magnitude, 3),
            "momentum": round(self.momentum, 3),
            "drift": round(self.drift, 3),
            "confidence": round(self.confidence, 3),
            "timestamp": self.timestamp.isoformat(),
            "history": self.history[-10:],
        }

    @classmethod
    def zero(cls) -> VelocityVector:
        """Create a zero velocity vector.

        Returns:
            VelocityVector with all components at zero/unknown.
        """
        return cls(
            direction=DirectionCategory.UNKNOWN,
            direction_detail="no_motion",
            magnitude=0.0,
            momentum=0.0,
            drift=0.0,
            confidence=0.0,
        )

    @classmethod
    def from_direction(
        cls,
        direction: str,
        magnitude: float = 0.5,
        confidence: float = 0.7,
    ) -> VelocityVector:
        """Create velocity vector from direction string.

        Args:
            direction: Direction category string or detail.
            magnitude: Initial magnitude.
            confidence: Initial confidence.

        Returns:
            New VelocityVector.
        """
        # Try to match to DirectionCategory
        try:
            category = DirectionCategory(direction.lower())
        except ValueError:
            # Infer category from direction detail
            category = cls._infer_category(direction)

        return cls(
            direction=category,
            direction_detail=direction,
            magnitude=magnitude,
            momentum=0.5,
            drift=0.0,
            confidence=confidence,
        )

    @staticmethod
    def _infer_category(detail: str) -> DirectionCategory:
        """Infer direction category from detail string.

        Args:
            detail: Direction detail string.

        Returns:
            Inferred DirectionCategory.
        """
        detail_lower = detail.lower()

        category_keywords = {
            DirectionCategory.EXPLORATION: ["explore", "discover", "browse", "search"],
            DirectionCategory.INVESTIGATION: [
                "investigate",
                "analyze",
                "debug",
                "diagnose",
                "why",
            ],
            DirectionCategory.EXECUTION: [
                "execute",
                "run",
                "implement",
                "build",
                "create",
            ],
            DirectionCategory.SYNTHESIS: ["combine", "merge", "synthesize", "integrate"],
            DirectionCategory.REFLECTION: ["review", "reflect", "summarize", "evaluate"],
            DirectionCategory.TRANSITION: ["switch", "change", "transition", "shift"],
        }

        for category, keywords in category_keywords.items():
            if any(kw in detail_lower for kw in keywords):
                return category

        return DirectionCategory.UNKNOWN
