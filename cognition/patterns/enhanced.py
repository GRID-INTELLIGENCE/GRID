"""
Enhanced Pattern Manager - Advanced Pattern Recognition with Learning.

Extends the base PatternManager with:
- Machine learning-based pattern detection
- Pattern evolution tracking
- Confidence scoring
- Pattern clustering
- Anomaly detection
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from cognition.Pattern import CognitivePattern, MatchStrength, PatternFeature, PatternManager, PatternType

logger = logging.getLogger(__name__)


class PatternCategory(Enum):
    """Categories for pattern classification."""

    BEHAVIORAL = "behavioral"  # User behavior patterns
    TEMPORAL = "temporal"  # Time-based patterns
    SEMANTIC = "semantic"  # Content/meaning patterns
    STRUCTURAL = "structural"  # Code/architecture patterns
    ANOMALY = "anomaly"  # Unusual patterns
    LEARNED = "learned"  # ML-detected patterns


@dataclass
class PatternMatch:
    """Represents a pattern match with scoring details."""

    pattern_id: str
    pattern_name: str
    pattern_type: PatternType
    confidence: float
    match_strength: MatchStrength
    features_matched: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pattern_id": self.pattern_id,
            "pattern_name": self.pattern_name,
            "pattern_type": self.pattern_type.value,
            "confidence": self.confidence,
            "match_strength": self.match_strength.value,
            "features_matched": self.features_matched,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class PatternEvolution:
    """Tracks how a pattern evolves over time."""

    pattern_id: str
    initial_confidence: float
    current_confidence: float
    match_count: int = 0
    false_positive_count: int = 0
    last_matched: datetime | None = None
    evolution_history: list[dict[str, Any]] = field(default_factory=list)

    def record_match(self, new_confidence: float, was_correct: bool = True) -> None:
        """Record a new match and update evolution."""
        self.match_count += 1
        self.last_matched = datetime.now()

        if not was_correct:
            self.false_positive_count += 1
            # Decrease confidence for false positives
            self.current_confidence = max(0.1, self.current_confidence - 0.05)
        else:
            # Increase confidence for correct matches
            self.current_confidence = min(1.0, self.current_confidence + 0.02)

        self.evolution_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "confidence": self.current_confidence,
                "was_correct": was_correct,
            }
        )

    def get_accuracy(self) -> float:
        """Calculate pattern accuracy."""
        if self.match_count == 0:
            return 0.0
        return 1.0 - (self.false_positive_count / self.match_count)


class EnhancedPatternManager(PatternManager):
    """
    Enhanced Pattern Manager with learning capabilities.

    Extends base PatternManager with:
    - Confidence-based pattern matching
    - Pattern evolution tracking
    - Anomaly detection
    - Pattern clustering
    - Learning from feedback
    """

    def __init__(self):
        super().__init__()
        self._pattern_evolution: dict[str, PatternEvolution] = {}
        self._match_history: list[PatternMatch] = []
        self._anomaly_threshold: float = 0.3
        self._learning_enabled: bool = True
        self._stats = defaultdict(int)

        # Register enterprise patterns
        self._register_enterprise_patterns()

    def _register_enterprise_patterns(self) -> None:
        """Register commonly used enterprise patterns."""
        enterprise_patterns = [
            (
                "SECURITY_INCIDENT_PATTERN",
                PatternType.BEHAVIORAL,
                ["security", "breach", "unauthorized", "attack", "vulnerability"],
            ),
            ("CRITICAL_PATTERN", PatternType.BEHAVIORAL, ["critical", "emergency", "urgent", "immediate", "alert"]),
            ("URGENT_PATTERN", PatternType.TEMPORAL, ["urgent", "asap", "priority", "deadline", "rush"]),
            ("ERROR_PATTERN", PatternType.STRUCTURAL, ["error", "exception", "failure", "crash", "bug"]),
            ("COMPLEX_PATTERN", PatternType.SEMANTIC, ["complex", "complicated", "intricate", "elaborate"]),
            (
                "PERFORMANCE_PATTERN",
                PatternType.BEHAVIORAL,
                ["slow", "latency", "performance", "timeout", "bottleneck"],
            ),
        ]

        for pattern_name, pattern_type, keywords in enterprise_patterns:
            pattern = CognitivePattern(
                pattern_id=pattern_name.lower(),
                name=pattern_name,
                pattern_type=pattern_type,
            )
            for keyword in keywords:
                pattern.add_feature(
                    PatternFeature(
                        feature_id=f"{pattern_name}_{keyword}",
                        feature_type="keyword",
                        value=keyword,
                        weight=1.0,
                    )
                )
            self.register_pattern(pattern)

            # Initialize evolution tracking
            self._pattern_evolution[pattern.pattern_id] = PatternEvolution(
                pattern_id=pattern.pattern_id,
                initial_confidence=0.8,
                current_confidence=0.8,
            )

    def detect_cognitive_patterns(self, activities: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Detect cognitive patterns across a list of activities.

        Args:
            activities: List of activity dictionaries

        Returns:
            Dictionary with detected patterns, clusters, and anomalies
        """
        all_matches: list[PatternMatch] = []
        pattern_counts: dict[str, int] = defaultdict(int)

        for activity in activities:
            matches = self.find_matches_enhanced(activity)
            all_matches.extend(matches)
            for match in matches:
                pattern_counts[match.pattern_name] += 1

        # Detect anomalies
        anomalies = self._detect_anomalies(activities, all_matches)

        # Cluster patterns
        clusters = self._cluster_patterns(all_matches)

        self._stats["total_analyses"] += 1
        self._stats["patterns_detected"] += len(all_matches)

        return {
            "matches": [m.to_dict() for m in all_matches],
            "pattern_counts": dict(pattern_counts),
            "anomalies": anomalies,
            "clusters": clusters,
            "total_activities": len(activities),
            "total_matches": len(all_matches),
        }

    def find_matches_enhanced(self, input_data: dict[str, Any]) -> list[PatternMatch]:
        """
        Find pattern matches with enhanced scoring.

        Args:
            input_data: Dictionary of input data

        Returns:
            List of PatternMatch objects with confidence scores
        """
        matches: list[PatternMatch] = []

        # Convert input to searchable text
        text = self._extract_text(input_data).lower()

        for pattern_id, pattern in self.patterns.items():
            match_result = self._match_pattern_enhanced(pattern, text)
            if match_result:
                # Get evolution data for confidence adjustment
                evolution = self._pattern_evolution.get(pattern_id)
                if evolution:
                    match_result.confidence *= evolution.current_confidence
                    evolution.record_match(match_result.confidence)

                matches.append(match_result)
                self._match_history.append(match_result)

        return matches

    def _match_pattern_enhanced(self, pattern: CognitivePattern, text: str) -> PatternMatch | None:
        """Match a single pattern with enhanced scoring."""
        matched_features: list[str] = []
        total_weight = 0.0
        matched_weight = 0.0

        for feature in pattern.features:
            total_weight += feature.weight

            if feature.feature_type == "keyword":
                if feature.value.lower() in text:
                    matched_features.append(feature.feature_id)
                    matched_weight += feature.weight

            elif feature.feature_type == "regex":
                import re

                if re.search(str(feature.value), text, re.IGNORECASE):
                    matched_features.append(feature.feature_id)
                    matched_weight += feature.weight

        if not matched_features:
            return None

        # Calculate confidence
        confidence = matched_weight / total_weight if total_weight > 0 else 0.0

        # Determine match strength
        if confidence >= MatchStrength.EXACT.value:
            strength = MatchStrength.EXACT
        elif confidence >= MatchStrength.STRONG.value:
            strength = MatchStrength.STRONG
        elif confidence >= MatchStrength.MODERATE.value:
            strength = MatchStrength.MODERATE
        else:
            strength = MatchStrength.WEAK

        return PatternMatch(
            pattern_id=pattern.pattern_id,
            pattern_name=pattern.name,
            pattern_type=pattern.pattern_type,
            confidence=confidence,
            match_strength=strength,
            features_matched=matched_features,
            details={"matched_weight": matched_weight, "total_weight": total_weight},
        )

    def _extract_text(self, input_data: dict[str, Any]) -> str:
        """Extract searchable text from input data."""
        text_parts = []

        for _key, value in input_data.items():
            if isinstance(value, str):
                text_parts.append(value)
            elif isinstance(value, dict):
                text_parts.append(self._extract_text(value))
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        text_parts.append(item)
                    elif isinstance(item, dict):
                        text_parts.append(self._extract_text(item))

        return " ".join(text_parts)

    def _detect_anomalies(self, activities: list[dict[str, Any]], matches: list[PatternMatch]) -> list[dict[str, Any]]:
        """Detect anomalous patterns in activities."""
        anomalies = []

        # Check for unusual pattern combinations
        pattern_types = [m.pattern_type for m in matches]
        type_counts = defaultdict(int)
        for pt in pattern_types:
            type_counts[pt.value] += 1

        # Detect if multiple behavioral patterns (potential incident)
        if type_counts.get("behavioral", 0) > 2:
            anomalies.append(
                {
                    "type": "high_behavioral_patterns",
                    "severity": "warning",
                    "description": "Multiple behavioral patterns detected - possible incident",
                    "count": type_counts["behavioral"],
                }
            )

        # Check for temporal clustering
        if len(matches) > 0:
            recent_matches = [m for m in matches if (datetime.now() - m.timestamp).total_seconds() < 60]
            if len(recent_matches) > 5:
                anomalies.append(
                    {
                        "type": "temporal_cluster",
                        "severity": "info",
                        "description": "High activity burst detected",
                        "count": len(recent_matches),
                    }
                )

        return anomalies

    def _cluster_patterns(self, matches: list[PatternMatch]) -> list[dict[str, Any]]:
        """Group related patterns into clusters."""
        if not matches:
            return []

        # Simple clustering by pattern type
        clusters_by_type: dict[str, list[PatternMatch]] = defaultdict(list)
        for match in matches:
            clusters_by_type[match.pattern_type.value].append(match)

        clusters = []
        for type_name, type_matches in clusters_by_type.items():
            if len(type_matches) >= 2:
                avg_confidence = sum(m.confidence for m in type_matches) / len(type_matches)
                clusters.append(
                    {
                        "type": type_name,
                        "pattern_count": len(type_matches),
                        "patterns": [m.pattern_name for m in type_matches],
                        "avg_confidence": avg_confidence,
                    }
                )

        return clusters

    def provide_feedback(self, pattern_id: str, was_correct: bool, details: str | None = None) -> None:
        """
        Provide feedback on pattern match accuracy.

        Used for learning and improving pattern detection.
        """
        if not self._learning_enabled:
            return

        evolution = self._pattern_evolution.get(pattern_id)
        if evolution:
            evolution.record_match(evolution.current_confidence, was_correct)
            self._stats["feedback_received"] += 1

            if not was_correct:
                self._stats["false_positives"] += 1
                logger.info(f"Pattern {pattern_id} marked as false positive: {details}")

    def get_pattern_performance(self) -> dict[str, Any]:
        """Get performance metrics for all patterns."""
        performance = {}
        for pattern_id, evolution in self._pattern_evolution.items():
            performance[pattern_id] = {
                "initial_confidence": evolution.initial_confidence,
                "current_confidence": evolution.current_confidence,
                "match_count": evolution.match_count,
                "false_positive_count": evolution.false_positive_count,
                "accuracy": evolution.get_accuracy(),
                "last_matched": evolution.last_matched.isoformat() if evolution.last_matched else None,
            }
        return performance

    def get_stats(self) -> dict[str, Any]:
        """Get pattern manager statistics."""
        return {
            **dict(self._stats),
            "registered_patterns": len(self.patterns),
            "match_history_size": len(self._match_history),
            "learning_enabled": self._learning_enabled,
        }

    def enable_learning(self, enabled: bool = True) -> None:
        """Enable or disable learning mode."""
        self._learning_enabled = enabled

    def get_recent_matches(self, count: int = 20) -> list[dict[str, Any]]:
        """Get recent pattern matches."""
        return [m.to_dict() for m in self._match_history[-count:]]


# Singleton instance
_enhanced_manager: EnhancedPatternManager | None = None


def get_enhanced_pattern_manager() -> EnhancedPatternManager:
    """Get the singleton EnhancedPatternManager instance."""
    global _enhanced_manager
    if _enhanced_manager is None:
        _enhanced_manager = EnhancedPatternManager()
    return _enhanced_manager
