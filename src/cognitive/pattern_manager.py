"""Advanced Pattern Manager.

Implements machine learning from pattern matches with:
- learn_from_match: Incremental learning from pattern recognitions
- Pattern model updates based on feedback
- Pattern generalization across contexts
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class PatternConfidence(str, Enum):
    """Confidence levels for patterns."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PatternModel:
    """A learned pattern model."""

    pattern_id: str
    name: str
    pattern_type: str  # "flow", "spatial", "rhythm", "time", etc.
    context: str | None = None  # Context where pattern applies
    confidence: float = 0.0
    success_rate: float = 0.0
    failure_count: int = 0
    last_seen: datetime = field(default_factory=lambda: datetime.now(UTC))
    usage_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class LearningUpdate:
    """Update to a pattern model from new observation."""

    pattern_id: str
    was_correct: bool
    user_feedback: str | None = None  # "correct", "incorrect", "neutral"
    confidence_adjustment: float = 0.0  # -0.1 to 0.1
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class PatternMatch:
    """A recognized pattern match."""

    pattern_id: str
    matched: bool
    pattern_name: str
    context: str | None = None
    confidence: float
    features: dict[str, Any] = field(default_factory=dict)


class AdvancedPatternManager:
    """Advanced pattern manager with machine learning capabilities.

    Features:
    - Learn from pattern matches with feedback
    - Generalize patterns across contexts
    - Update pattern models with success/failure data
    - Pattern generalization and adaptation
    """

    def __init__(self):
        self._patterns: dict[str, PatternModel] = {}
        self._feedback_history: list[LearningUpdate] = []
        self._learning_rate: float = 0.5  # 0.0 to 1.0 learning rate

    def register_pattern(
        self,
        pattern_id: str,
        name: str,
        pattern_type: str,
        context: str | None = None,
        initial_confidence: float = 0.5,
        parameters: dict[str, Any] | None = None,
    ) -> PatternModel:
        """Register a new pattern model for learning.

        Args:
            pattern_id: Unique pattern identifier
            name: Pattern name
            pattern_type: Pattern type (flow, spatial, rhythm, time, etc.)
            context: Context where pattern applies
            initial_confidence: Initial confidence (0.0 to 1.0)
            parameters: Optional pattern-specific parameters

        Returns:
            Registered pattern model
        """
        model = PatternModel(
            pattern_id=pattern_id,
            name=name,
            pattern_type=pattern_type,
            context=context,
            confidence=initial_confidence,
        )

        self._patterns[pattern_id] = model
        logger.info(f"Registered pattern: {pattern_id} ({name})")

    def learn_from_match(
        self,
        pattern_id: str,
        features: dict[str, Any],
        was_correct: bool,
        user_feedback: str | None = None,
        context: str | None = None,
    ) -> LearningUpdate:
        """Update a pattern model based on a match and feedback.

        Args:
            pattern_id: Pattern ID to update
            features: Observed pattern features
            was_correct: Whether the pattern was correct
            user_feedback: User feedback ("correct", "incorrect", "neutral")
            context: Context where pattern was applied

        Returns:
            Learning update result
        """
        if pattern_id not in self._patterns:
            logger.warning(f"Pattern {pattern_id} not found")
            return None

        model = self._patterns[pattern_id]

        if not model:
            logger.warning(f"Pattern {pattern_id} has no model data to update")
            return None

        # Calculate confidence adjustment
        confidence_delta = 0.1 if was_correct else (-0.1 if user_feedback == "incorrect" else 0.0)

        # Update confidence with exponential moving average
        old_confidence = model.confidence
        new_confidence = old_confidence + (confidence_delta * self._learning_rate)

        # Update usage count
        model.usage_count += 1

        # Update parameters based on features
        self._update_pattern_parameters(model, features)

        # Record feedback
        update = LearningUpdate(
            pattern_id=pattern_id,
            was_correct=was_correct,
            user_feedback=user_feedback,
            confidence_adjustment=confidence_delta,
            context=context,
        )

        self._feedback_history.append(update)
        logger.info(
            f"Pattern {pattern_id} updated: was_correct={was_correct}, "
            f"confidence={new_confidence:.2f}, rate={self._learning_rate:.2f}"
        )

        return update

    def match_pattern(
        self,
        features: dict[str, Any],
        context: str | None = None,
    ) -> PatternMatch | None:
        """Match input features against learned patterns.

        Args:
            features: Observed features from pattern recognition
            context: Optional context hint

        Returns:
            Pattern match result with the best matching pattern
        """
        matches = []

        # Check each registered pattern
        for pattern_id, model in self._patterns.items():
            # Check if context matches
            if model.context and context:
                if not self._is_context_match(model.context, context):
                    continue

            # Check feature match
            match_score = self._calculate_feature_match(features, model.parameters)
            if match_score > model.confidence * 0.8:
                matches.append(
                    {
                        "pattern_id": pattern_id,
                        "matched": True,
                        "pattern_name": model.name,
                        "context": model.context,
                        "confidence": match_score,
                        "features": features,
                    }
                )

        if not matches:
            return None

        # Sort matches by confidence
        matches.sort(key=lambda m: m["confidence"], reverse=True)

        if matches:
            return matches[0]
        else:
            return None

    def _calculate_feature_match(self, features: dict[str, Any], pattern_params: dict[str, Any]) -> float:
        """Calculate feature similarity score."""
        score = 0.0

        # Feature comparison
        for feature_key, observed_value in features.items():
            if feature_key not in pattern_params:
                continue
            param_value = pattern_params.get(feature_key, 0.0)

            # Simple similarity score
            if isinstance(observed_value, (int, float)):
                diff = abs(observed_value - param_value) / (abs(param_value) + 1)
                score += 1.0 / (diff + 0.1)
            elif isinstance(observed_value, str):
                if observed_value.lower() == str(param_value).lower():
                    score += 0.8
                elif observed_value == param_value:
                    score += 1.0

        return score

    def _is_context_match(self, pattern_context: str, input_context: str) -> bool:
        """Check if contexts match semantically."""
        if not pattern_context or not input_context:
            return True  # No context specified, allow match

        pattern_words = set(pattern_context.lower().split())
        input_words = set(input_context.lower().split())

        # Simple intersection
        if pattern_words.intersection(input_words):
            return True

        # Check subset/superset relationship
        if pattern_words.issubset(input_words):
            return True
        elif input_words.issuperset(pattern_words):
            return True

        return False

    def get_pattern_model(self, pattern_id: str) -> PatternModel | None:
        """Get a learned pattern model.

        Args:
            pattern_id: Pattern identifier

        Returns:
            Pattern model or None
        """
        return self._patterns.get(pattern_id)

    def get_learning_stats(self) -> dict[str, Any]:
        """Get statistics about pattern learning progress."""
        total_updates = len(self._feedback_history)
        correct_count = sum(1 for u in self._feedback_history if u.was_correct)
        success_rate = correct_count / total_updates if total_updates > 0 else 0.0

        return {
            "total_patterns": len(self._patterns),
            "total_updates": total_updates,
            "success_rate": success_rate,
            "average_confidence": (
                sum(p.confidence for p in self._patterns.values()) / len(self._patterns) if self._patterns else 0.0
            ),
            "most_learned_patterns": [
                pid
                for pid, _model in sorted(self._patterns.items(), key=lambda item: item[1].confidence, reverse=True)[:5]
            ],
        }

    def export_patterns(self) -> dict[str, dict[str, Any]]:
        """Export all learned patterns for inspection."""
        return {
            pid: {
                "name": model.name,
                "confidence": model.confidence,
                "usage_count": model.usage_count,
                "success_rate": model.success_rate,
                "parameters": model.parameters,
                "context": model.context,
            }
            for pid, model in self._patterns.items()
        }
