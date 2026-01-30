"""Landscape detector for detecting ever-shifting landscapes.

This module implements hybrid pattern detection for comprehensive landscape
monitoring, detecting shifts in system structures and patterns.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from grid.awareness.context import Context
from grid.essence.core_state import EssentialState
from grid.patterns.hybrid_detection import HybridPatternDetector

logger = logging.getLogger(__name__)


@dataclass
class LandscapeShift:
    """Represents a detected landscape shift."""

    shift_type: str
    magnitude: float
    affected_domains: list[str]
    detected_patterns: list[str]
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "shift_type": self.shift_type,
            "magnitude": self.magnitude,
            "affected_domains": self.affected_domains,
            "detected_patterns": self.detected_patterns,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class LandscapeSnapshot:
    """Snapshot of landscape state at a point in time."""

    timestamp: datetime
    patterns: list[str]
    structural_features: dict[str, Any]
    domain_metrics: dict[str, float]
    shift_indicators: dict[str, float] = field(default_factory=dict)


class StatisticalLandscapeAnalyzer:
    """Statistical analysis for landscape detection."""

    def __init__(self, window_size: int = 10) -> None:
        self.window_size = window_size
        self.snapshots: list[LandscapeSnapshot] = []

    def add_snapshot(self, snapshot: LandscapeSnapshot) -> None:
        """Add a landscape snapshot."""
        self.snapshots.append(snapshot)
        # Keep only recent snapshots
        if len(self.snapshots) > self.window_size * 2:
            self.snapshots = self.snapshots[-self.window_size * 2 :]

    def detect_statistical_shifts(self, threshold: float = 0.3) -> list[LandscapeShift]:
        """Detect statistical shifts in landscape.

        Args:
            threshold: Shift detection threshold

        Returns:
            List of detected shifts
        """
        if len(self.snapshots) < self.window_size:
            return []

        shifts = []
        recent = self.snapshots[-self.window_size :]
        previous = self.snapshots[-self.window_size * 2 : -self.window_size]

        if not previous:
            return []

        # Compare pattern distributions
        recent_patterns = set()
        for snapshot in recent:
            recent_patterns.update(snapshot.patterns)

        previous_patterns = set()
        for snapshot in previous:
            previous_patterns.update(snapshot.patterns)

        pattern_change = len(recent_patterns ^ previous_patterns) / max(len(recent_patterns | previous_patterns), 1)

        if pattern_change > threshold:
            shifts.append(
                LandscapeShift(
                    shift_type="pattern_distribution",
                    magnitude=pattern_change,
                    affected_domains=list(recent_patterns - previous_patterns),
                    detected_patterns=list(recent_patterns - previous_patterns),
                    metadata={"pattern_change_ratio": pattern_change},
                )
            )

        # Compare domain metrics
        recent_metrics = self._aggregate_metrics(recent)
        previous_metrics = self._aggregate_metrics(previous)

        for domain, recent_value in recent_metrics.items():
            previous_value = previous_metrics.get(domain, recent_value)
            if previous_value > 0:
                change_ratio = abs(recent_value - previous_value) / previous_value
                if change_ratio > threshold:
                    shifts.append(
                        LandscapeShift(
                            shift_type="metric_change",
                            magnitude=change_ratio,
                            affected_domains=[domain],
                            detected_patterns=[],
                            metadata={
                                "domain": domain,
                                "previous_value": previous_value,
                                "recent_value": recent_value,
                            },
                        )
                    )

        return shifts

    def _aggregate_metrics(self, snapshots: list[LandscapeSnapshot]) -> dict[str, float]:
        """Aggregate metrics across snapshots."""
        aggregated: dict[str, float] = {}
        counts: dict[str, int] = {}

        for snapshot in snapshots:
            for domain, value in snapshot.domain_metrics.items():
                if domain not in aggregated:
                    aggregated[domain] = 0.0
                    counts[domain] = 0
                aggregated[domain] += value
                counts[domain] += 1

        # Average
        for domain in aggregated:
            if counts[domain] > 0:
                aggregated[domain] /= counts[domain]

        return aggregated


class SyntacticLandscapeAnalyzer:
    """Syntactic analysis for landscape structure detection."""

    def __init__(self) -> None:
        self.structural_history: list[dict[str, Any]] = []

    def analyze_structure(self, snapshot: LandscapeSnapshot) -> dict[str, Any]:
        """Analyze structural features of landscape."""
        structure = {
            "pattern_count": len(snapshot.patterns),
            "structural_features": snapshot.structural_features.copy(),
            "complexity": self._calculate_complexity(snapshot),
        }

        self.structural_history.append(structure)
        if len(self.structural_history) > 20:
            self.structural_history = self.structural_history[-20:]

        return structure

    def detect_structural_shifts(self, threshold: float = 0.2) -> list[LandscapeShift]:
        """Detect structural shifts in landscape."""
        if len(self.structural_history) < 2:
            return []

        shifts = []
        previous = self.structural_history[-2]
        current = self.structural_history[-1]

        # Complexity change
        complexity_change = abs(current["complexity"] - previous["complexity"]) / max(previous["complexity"], 1.0)

        if complexity_change > threshold:
            shifts.append(
                LandscapeShift(
                    shift_type="structural_complexity",
                    magnitude=complexity_change,
                    affected_domains=[],
                    detected_patterns=[],
                    metadata={
                        "previous_complexity": previous["complexity"],
                        "current_complexity": current["complexity"],
                    },
                )
            )

        # Pattern count change
        pattern_change = abs(current["pattern_count"] - previous["pattern_count"]) / max(previous["pattern_count"], 1)

        if pattern_change > threshold:
            shifts.append(
                LandscapeShift(
                    shift_type="pattern_count",
                    magnitude=pattern_change,
                    affected_domains=[],
                    detected_patterns=[],
                    metadata={
                        "previous_count": previous["pattern_count"],
                        "current_count": current["pattern_count"],
                    },
                )
            )

        return shifts

    def _calculate_complexity(self, snapshot: LandscapeSnapshot) -> float:
        """Calculate structural complexity score."""
        complexity = 0.0

        # Pattern diversity
        complexity += len(snapshot.patterns) * 0.1

        # Structural feature complexity
        if snapshot.structural_features:
            complexity += len(snapshot.structural_features) * 0.05
            # Depth complexity
            depth = snapshot.structural_features.get("depth", 0)
            complexity += depth * 0.2

        return min(complexity, 10.0)  # Cap at 10.0


class NeuralLandscapeAnalyzer:
    """Neural network analysis for landscape pattern learning."""

    def __init__(self) -> None:
        self.learned_landscapes: dict[str, dict[str, Any]] = {}
        self.pattern_weights: dict[str, float] = {}

    def learn_landscape(self, snapshot: LandscapeSnapshot, label: str) -> None:
        """Learn a landscape pattern.

        Args:
            snapshot: Landscape snapshot
            label: Label for this landscape pattern
        """
        features = self._extract_features(snapshot)
        self.learned_landscapes[label] = features
        self.pattern_weights[label] = 1.0

    def detect_neural_shifts(self, snapshot: LandscapeSnapshot, threshold: float = 0.3) -> list[LandscapeShift]:
        """Detect shifts using neural pattern matching.

        Args:
            snapshot: Current landscape snapshot
            threshold: Shift detection threshold

        Returns:
            List of detected shifts
        """
        if not self.learned_landscapes:
            return []

        current_features = self._extract_features(snapshot)
        shifts = []

        for label, learned_features in self.learned_landscapes.items():
            similarity = self._calculate_similarity(current_features, learned_features)
            difference = 1.0 - similarity

            if difference > threshold:
                shifts.append(
                    LandscapeShift(
                        shift_type="neural_pattern_divergence",
                        magnitude=difference,
                        affected_domains=[],
                        detected_patterns=[label],
                        metadata={
                            "learned_pattern": label,
                            "similarity": similarity,
                            "difference": difference,
                        },
                    )
                )

        return shifts

    def _extract_features(self, snapshot: LandscapeSnapshot) -> dict[str, float]:
        """Extract features from snapshot for neural analysis."""
        features: dict[str, float] = {
            "pattern_count": float(len(snapshot.patterns)),
            "metric_count": float(len(snapshot.domain_metrics)),
        }

        # Aggregate domain metrics
        if snapshot.domain_metrics:
            features["avg_metric_value"] = sum(snapshot.domain_metrics.values()) / len(snapshot.domain_metrics)
            features["max_metric_value"] = max(snapshot.domain_metrics.values())
            features["min_metric_value"] = min(snapshot.domain_metrics.values())

        # Structural features
        if snapshot.structural_features:
            features["structural_depth"] = float(snapshot.structural_features.get("depth", 0))
            features["structural_breadth"] = float(snapshot.structural_features.get("breadth", 0))

        return features

    def _calculate_similarity(self, features1: dict[str, float], features2: dict[str, float]) -> float:
        """Calculate similarity between feature sets."""
        all_keys = set(features1.keys()) | set(features2.keys())
        if not all_keys:
            return 0.0

        similarities = []
        for key in all_keys:
            val1 = features1.get(key, 0.0)
            val2 = features2.get(key, 0.0)

            max_val = max(abs(val1), abs(val2), 1.0)
            similarity = 1.0 - abs(val1 - val2) / max_val
            similarities.append(max(0.0, similarity))

        return sum(similarities) / len(similarities) if similarities else 0.0


class LandscapeDetector:
    """Hybrid landscape detector combining statistical, syntactic, and neural approaches."""

    def __init__(self) -> None:
        self.statistical = StatisticalLandscapeAnalyzer()
        self.syntactic = SyntacticLandscapeAnalyzer()
        self.neural = NeuralLandscapeAnalyzer()
        self.hybrid_pattern_detector = HybridPatternDetector()
        self.detected_shifts: list[LandscapeShift] = []

    async def detect_landscape_shifts(
        self,
        state: EssentialState,
        context: Context,
        threshold: float = 0.3,
    ) -> list[LandscapeShift]:
        """Detect landscape shifts using hybrid approach.

        Args:
            state: Current essential state
            context: Current context
            threshold: Shift detection threshold

        Returns:
            List of detected landscape shifts
        """
        # Use hybrid pattern detection
        hybrid_result = await self.hybrid_pattern_detector.detect(state)

        # Create landscape snapshot
        snapshot = LandscapeSnapshot(
            timestamp=datetime.now(),
            patterns=hybrid_result.combined_patterns,
            structural_features={
                "depth": state.context_depth,
                "breadth": len(state.quantum_state) if isinstance(state.quantum_state, dict) else 0,
            },
            domain_metrics={
                "coherence": state.coherence_factor,
                "context_depth": context.temporal_depth,
            },
        )

        # Run all analyzers
        statistical_shifts = self.statistical.detect_statistical_shifts(threshold)
        self.statistical.add_snapshot(snapshot)

        self.syntactic.analyze_structure(snapshot)
        syntactic_shifts = self.syntactic.detect_structural_shifts(threshold)

        neural_shifts = self.neural.detect_neural_shifts(snapshot, threshold)

        # Combine all shifts
        all_shifts = statistical_shifts + syntactic_shifts + neural_shifts

        # Remove duplicates and merge similar shifts
        merged_shifts = self._merge_shifts(all_shifts)

        self.detected_shifts.extend(merged_shifts)
        if len(self.detected_shifts) > 100:
            self.detected_shifts = self.detected_shifts[-100:]

        logger.info(
            f"Detected {len(merged_shifts)} landscape shifts: "
            f"{len(statistical_shifts)} statistical, "
            f"{len(syntactic_shifts)} syntactic, "
            f"{len(neural_shifts)} neural"
        )

        return merged_shifts

    def _merge_shifts(self, shifts: list[LandscapeShift]) -> list[LandscapeShift]:
        """Merge similar shifts."""
        if not shifts:
            return []

        merged: list[LandscapeShift] = []
        processed: set = set()

        for shift in shifts:
            # Create a key for deduplication
            key = (shift.shift_type, tuple(sorted(shift.affected_domains)))

            if key not in processed:
                # Check if we can merge with existing shift
                merged_shift = None
                for existing in merged:
                    if existing.shift_type == shift.shift_type and set(existing.affected_domains) == set(
                        shift.affected_domains
                    ):
                        # Merge: take maximum magnitude
                        existing.magnitude = max(existing.magnitude, shift.magnitude)
                        existing.detected_patterns = list(
                            set(existing.detected_patterns) | set(shift.detected_patterns)
                        )
                        merged_shift = existing
                        break

                if merged_shift is None:
                    merged.append(shift)

                processed.add(key)

        return merged

    async def learn_landscape_pattern(self, label: str, state: EssentialState, context: Context) -> None:
        """Learn a landscape pattern for future detection.

        Args:
            label: Label for the pattern
            state: Essential state
            context: Context
        """
        # Use hybrid pattern detection
        hybrid_result = await self.hybrid_pattern_detector.detect(state)
        snapshot = LandscapeSnapshot(
            timestamp=datetime.now(),
            patterns=hybrid_result.combined_patterns,
            structural_features={
                "depth": state.context_depth,
                "breadth": len(state.quantum_state) if isinstance(state.quantum_state, dict) else 0,
            },
            domain_metrics={
                "coherence": state.coherence_factor,
                "context_depth": context.temporal_depth,
            },
        )

        self.neural.learn_landscape(snapshot, label)

        logger.info(f"Learned landscape pattern: {label}")

    def get_recent_shifts(self, limit: int = 10) -> list[LandscapeShift]:
        """Get recent landscape shifts."""
        return self.detected_shifts[-limit:]
