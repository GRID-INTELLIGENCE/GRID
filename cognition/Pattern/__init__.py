"""
Pattern Module

Handles pattern recognition and matching algorithms for cognitive processing.
Provides basic pattern matching with extensibility for advanced features.
"""

import logging
import math
import re
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class PatternType(Enum):
    """Types of cognitive patterns."""

    SEQUENCE = "sequence"
    TEMPORAL = "temporal"
    SEMANTIC = "semantic"
    STRUCTURAL = "structural"
    BEHAVIORAL = "behavioral"


class MatchStrength(Enum):
    """Strength of pattern match."""

    WEAK = 0.3
    MODERATE = 0.6
    STRONG = 0.8
    EXACT = 1.0


@dataclass
class PatternFeature:
    """A feature within a cognitive pattern."""

    feature_id: str
    feature_type: str
    value: Any
    weight: float = 1.0
    optional: bool = False


@dataclass
class CognitivePattern:
    """Represents a cognitive pattern with features and metadata."""

    pattern_id: str
    name: str
    pattern_type: PatternType
    features: list[PatternFeature] = field(default_factory=list)
    template: dict[str, Any] | None = None
    confidence_threshold: float = 0.5
    metadata: dict[str, Any] = field(default_factory=dict)
    learning_state: dict[str, Any] | None = None

    def add_feature(self, feature: PatternFeature) -> None:
        """Add a feature to the pattern."""
        self.features.append(feature)

    def get_feature_by_id(self, feature_id: str) -> PatternFeature | None:
        """Get a feature by its ID."""
        for feature in self.features:
            if feature.feature_id == feature_id:
                return feature
        return None

    def calculate_similarity(self, other_features: list[PatternFeature]) -> float:
        """Calculate similarity with another set of features."""
        if not self.features and not other_features:
            return 1.0
        if not self.features or not other_features:
            return 0.0

        # Simple weighted Jaccard similarity
        self_feature_set = {f.feature_id: f.value for f in self.features}
        other_feature_set = {f.feature_id: f.value for f in other_features}

        intersection = 0.0
        union = 0.0
        total_weight = 0.0

        all_feature_ids = set(self_feature_set.keys()) | set(other_feature_set.keys())

        for feature_id in all_feature_ids:
            self_value = self_feature_set.get(feature_id)
            other_value = other_feature_set.get(feature_id)

            if self_value is not None and other_value is not None:
                # Calculate feature similarity
                if isinstance(self_value, (int, float)) and isinstance(other_value, (int, float)):
                    similarity = 1.0 - min(
                        1.0, abs(self_value - other_value) / max(abs(self_value), abs(other_value), 1.0)
                    )
                elif isinstance(self_value, str) and isinstance(other_value, str):
                    similarity = 1.0 if self_value == other_value else 0.0
                else:
                    similarity = 1.0 if self_value == other_value else 0.0

                # Get weight
                feature = self.get_feature_by_id(feature_id)
                weight = feature.weight if feature else 1.0

                intersection += similarity * weight
                union += weight
                total_weight += weight
            else:
                # Feature missing in one set
                feature = self.get_feature_by_id(feature_id)
                weight = feature.weight if feature else 1.0
                if not feature or not feature.optional:
                    union += weight
                    total_weight += weight

        return intersection / union if union > 0 else 0.0


class PatternMatcher(ABC):
    """Abstract base class for pattern matchers."""

    @abstractmethod
    def match(self, pattern: CognitivePattern, input_data: Any) -> tuple[float, dict[str, Any]]:
        """Match a pattern against input data. Return (confidence, match_details)."""
        pass

    @abstractmethod
    def can_match(self, pattern_type: PatternType) -> bool:
        """Check if this matcher can handle the pattern type."""
        pass


class SequenceMatcher(PatternMatcher):
    """Matches sequential patterns."""

    def can_match(self, pattern_type: PatternType) -> bool:
        return pattern_type == PatternType.SEQUENCE

    def match(self, pattern: CognitivePattern, input_data: Any) -> tuple[float, dict[str, Any]]:
        """Match sequence pattern."""
        if not isinstance(input_data, list):
            return 0.0, {"error": "Input must be a list"}

        if not pattern.template or "sequence" not in pattern.template:
            return 0.0, {"error": "Pattern must have sequence template"}

        expected_sequence = pattern.template["sequence"]
        if len(expected_sequence) != len(input_data):
            return 0.0, {"error": "Sequence length mismatch"}

        matches = 0.0
        total = len(expected_sequence)

        for _i, (expected, actual) in enumerate(zip(expected_sequence, input_data, strict=False)):
            if expected == actual:
                matches += 1
            elif isinstance(expected, str) and isinstance(actual, str):
                # Partial string match
                if expected.lower() in actual.lower():
                    matches += 0.5

        confidence = matches / total if total > 0 else 0.0

        return confidence, {"matches": matches, "total": total, "sequence_alignment": expected_sequence == input_data}


class SemanticMatcher(PatternMatcher):
    """Matches semantic patterns using keyword and concept matching."""

    def __init__(self):
        self.stopwords = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
        }

    def can_match(self, pattern_type: PatternType) -> bool:
        return pattern_type == PatternType.SEMANTIC

    def match(self, pattern: CognitivePattern, input_data: Any) -> tuple[float, dict[str, Any]]:
        """Match semantic pattern."""
        if not isinstance(input_data, str):
            return 0.0, {"error": "Input must be a string"}

        # Extract keywords from pattern features
        pattern_keywords = set()
        for feature in pattern.features:
            if feature.feature_type == "keyword":
                if isinstance(feature.value, str):
                    pattern_keywords.add(feature.value.lower())
                elif isinstance(feature.value, list):
                    pattern_keywords.update([v.lower() for v in feature.value])

        if not pattern_keywords:
            return 0.0, {"error": "No keywords found in pattern"}

        # Tokenize and normalize input
        input_tokens = self._tokenize(input_data.lower())
        input_words = set(input_tokens) - self.stopwords

        # Calculate semantic similarity
        intersection = pattern_keywords & input_words
        union = pattern_keywords | input_words

        jaccard = len(intersection) / len(union) if union else 0.0

        # Boost for exact phrase matches
        phrase_boost = 0.0
        if pattern.template and "phrases" in pattern.template:
            for phrase in pattern.template["phrases"]:
                if phrase.lower() in input_data.lower():
                    phrase_boost += 0.2

        confidence = min(1.0, jaccard + phrase_boost)

        return confidence, {
            "matched_keywords": list(intersection),
            "pattern_keywords": list(pattern_keywords),
            "input_words": list(input_words),
            "jaccard_similarity": jaccard,
            "phrase_boost": phrase_boost,
        }

    def _tokenize(self, text: str) -> list[str]:
        """Simple tokenization."""
        # Split on non-word characters and filter
        tokens = re.findall(r"\b\w+\b", text)
        return [t for t in tokens if len(t) > 2]


class PatternManager:
    """Manages cognitive patterns and matching operations."""

    def __init__(self):
        self.patterns: dict[str, CognitivePattern] = {}
        self.matchers: list[PatternMatcher] = []
        self.logger = logging.getLogger(f"{__name__}.PatternManager")

        # Register default matchers
        self.register_matcher(SequenceMatcher())
        self.register_matcher(SemanticMatcher())

    def register_pattern(self, pattern: CognitivePattern) -> None:
        """Register a cognitive pattern."""
        self.patterns[pattern.pattern_id] = pattern
        self.logger.info(f"Registered pattern {pattern.pattern_id}: {pattern.name}")

    def get_pattern(self, pattern_id: str) -> CognitivePattern | None:
        """Get a pattern by ID."""
        return self.patterns.get(pattern_id)

    def register_matcher(self, matcher: PatternMatcher) -> None:
        """Register a pattern matcher."""
        self.matchers.append(matcher)
        self.logger.debug(f"Registered matcher: {matcher.__class__.__name__}")

    def match_pattern(self, pattern_id: str, input_data: Any) -> tuple[float, dict[str, Any]]:
        """Match a specific pattern against input data."""
        pattern = self.get_pattern(pattern_id)
        if not pattern:
            return 0.0, {"error": f"Pattern {pattern_id} not found"}

        # Find appropriate matcher
        for matcher in self.matchers:
            if matcher.can_match(pattern.pattern_type):
                try:
                    confidence, details = matcher.match(pattern, input_data)
                    self.logger.debug(f"Pattern {pattern_id} match: {confidence:.2f}")
                    return confidence, details
                except Exception as e:
                    self.logger.error(f"Matcher failed for pattern {pattern_id}: {e}")

        return 0.0, {"error": f"No matcher available for pattern type {pattern.pattern_type}"}

    def find_matches(
        self, input_data: Any, pattern_type: PatternType | None = None
    ) -> list[tuple[str, float, dict[str, Any]]]:
        """Find all patterns that match the input data."""
        matches = []

        for pattern_id, pattern in self.patterns.items():
            if pattern_type and pattern.pattern_type != pattern_type:
                continue

            confidence, details = self.match_pattern(pattern_id, input_data)
            if confidence >= pattern.confidence_threshold:
                matches.append((pattern_id, confidence, details))

        # Sort by confidence (descending)
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches

    def create_pattern_from_template(
        self, pattern_id: str, name: str, pattern_type: PatternType, template: dict[str, Any]
    ) -> CognitivePattern:
        """Create a pattern from a template."""
        pattern = CognitivePattern(pattern_id=pattern_id, name=name, pattern_type=pattern_type, template=template)

        # Auto-generate features from template
        if pattern_type == PatternType.SEMANTIC and "keywords" in template:
            for keyword in template["keywords"]:
                feature = PatternFeature(
                    feature_id=f"keyword_{keyword}", feature_type="keyword", value=keyword, weight=1.0
                )
                pattern.add_feature(feature)

        elif pattern_type == PatternType.SEQUENCE and "sequence" in template:
            for i, item in enumerate(template["sequence"]):
                feature = PatternFeature(
                    feature_id=f"seq_item_{i}", feature_type="sequence_item", value=item, weight=1.0
                )
                pattern.add_feature(feature)

        self.register_pattern(pattern)
        return pattern

    def list_patterns(self) -> list[str]:
        """List all pattern IDs."""
        return list(self.patterns.keys())

    def get_pattern_statistics(self) -> dict[str, Any]:
        """Get statistics about registered patterns."""
        pattern_types: dict[str, int] = {}
        for pattern in self.patterns.values():
            pattern_types[pattern.pattern_type.value] = pattern_types.get(pattern.pattern_type.value, 0) + 1

        return {
            "total_patterns": len(self.patterns),
            "pattern_types": pattern_types,
            "available_matchers": len(self.matchers),
        }


class AdvancedPatternManager(PatternManager):
    """Advanced pattern manager with Online Logistic Regression learning.

    Implements a production-safe learning algorithm:
    - **Bias**: starts at -0.5 (skeptical default, ~37% base probability)
    - **Clamping**: z-score bounded to [-20, 20] to prevent overflow
    - **L2 Regularization**: sparse decay (0.001) prevents weight explosion
    - **JSON Persistence**: all state in ``learning_state`` dict, no Pickle
    """

    # Hyperparameters
    LEARNING_RATE: float = 0.1
    DECAY: float = 0.001  # L2 regularization factor
    MAX_SCORE: float = 20.0  # Clamping range for z-score
    DEFAULT_BIAS: float = -0.5  # Skeptical default (~37% probability)

    def __init__(self, learning_rate: float = 0.1, decay: float = 0.001) -> None:
        super().__init__()
        self.pattern_relationships: dict[str, list[str]] = {}
        self.learning_enabled = False
        self.learning_rate = learning_rate
        self.decay = decay
        self.match_history: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Relationship helpers (unchanged)
    # ------------------------------------------------------------------

    def add_relationship(self, pattern_id: str, related_pattern_id: str) -> None:
        """Add a relationship between patterns."""
        if pattern_id not in self.pattern_relationships:
            self.pattern_relationships[pattern_id] = []
        self.pattern_relationships[pattern_id].append(related_pattern_id)

    def enable_learning(self) -> None:
        """Enable pattern learning from matches."""
        self.learning_enabled = True

    def find_related_patterns(self, pattern_id: str) -> list[str]:
        """Find patterns related to the given pattern."""
        return self.pattern_relationships.get(pattern_id, [])

    # ------------------------------------------------------------------
    # Online Logistic Regression internals
    # ------------------------------------------------------------------

    @staticmethod
    def _sigmoid(z: float) -> float:
        """Numerically stable sigmoid with clamping.

        Clamps *z* to [-20, 20] before computing ``1 / (1 + exp(-z))``
        to prevent :class:`OverflowError` from ``math.exp``.
        """
        z = max(-20.0, min(20.0, z))
        return 1.0 / (1.0 + math.exp(-z))

    def _init_learning_state(self, pattern: CognitivePattern) -> dict[str, Any]:
        """Ensure *pattern* has a valid ``learning_state`` dict.

        Returns the (possibly freshly-created) state for convenience.
        """
        if pattern.learning_state is None:
            pattern.learning_state = {
                "weights": {},
                "bias": self.DEFAULT_BIAS,
                "samples_seen": 0,
                "version": "v1",
            }
        return pattern.learning_state

    def _extract_features(self, input_data: Any) -> dict[str, float]:
        """Convert raw input into a normalised feature dictionary.

        - **str**: bag-of-words with ``log(1 + count)`` scaling
        - **dict**: values cast to ``float`` directly
        - **list**: delegates to the parent matcher (no features extracted)
        """
        features: dict[str, float] = {}

        if isinstance(input_data, str):
            for word in input_data.lower().split():
                features[word] = features.get(word, 0.0) + 1.0
            # Log-scale to tame repeated tokens
            for key in features:
                features[key] = math.log(1.0 + features[key])

        elif isinstance(input_data, dict):
            for k, v in input_data.items():
                try:
                    features[str(k)] = float(v)
                except (TypeError, ValueError):
                    continue

        return features

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def predict_proba(self, pattern_id: str, input_data: Any) -> float:
        """Calculate the probability (0.0–1.0) that *input_data* matches *pattern_id*.

        Uses the learned weights and bias with a clamped sigmoid activation.
        Returns 0.0 if the pattern is not registered.
        """
        pattern = self.get_pattern(pattern_id)
        if not pattern:
            return 0.0

        state = self._init_learning_state(pattern)
        weights = state["weights"]
        features = self._extract_features(input_data)

        # Dot product: bias + Σ(w_i · x_i)
        z_score: float = state["bias"]
        for feature_name, feature_value in features.items():
            z_score += weights.get(feature_name, 0.0) * feature_value

        return self._sigmoid(z_score)

    def learn_from_match(
        self,
        pattern_id: str,
        input_data: Any,
        actual_label: float,
    ) -> None:
        """Online SGD update with L2 regularisation.

        Args:
            pattern_id: Pattern to update.
            input_data: The observed input (str, dict, …).
            actual_label: ``1.0`` for a confirmed match, ``0.0`` for no-match.
        """
        if not self.learning_enabled:
            return

        pattern = self.get_pattern(pattern_id)
        if not pattern:
            self.logger.warning("Cannot learn: pattern %s not found", pattern_id)
            return

        state = self._init_learning_state(pattern)
        features = self._extract_features(input_data)

        # Forward pass
        predicted_prob = self.predict_proba(pattern_id, input_data)

        # Error signal
        error = actual_label - predicted_prob

        # Update bias: b ← b + η · error
        state["bias"] += self.learning_rate * error

        # Update weights with sparse L2 decay:
        # w_i ← w_i + η · (error · x_i  −  λ · w_i)
        weights = state["weights"]
        for feature_name, feature_value in features.items():
            current_w = weights.get(feature_name, 0.0)
            gradient = error * feature_value
            regularisation = self.decay * current_w
            weights[feature_name] = current_w + self.learning_rate * (gradient - regularisation)

        state["samples_seen"] += 1

        self.match_history.append({"pattern_id": pattern_id, "label": actual_label, "predicted": predicted_prob})
        self.logger.info(
            "Learned on %s: label=%.1f, predicted=%.4f, error=%.4f, samples=%d",
            pattern_id,
            actual_label,
            predicted_prob,
            error,
            state["samples_seen"],
        )
