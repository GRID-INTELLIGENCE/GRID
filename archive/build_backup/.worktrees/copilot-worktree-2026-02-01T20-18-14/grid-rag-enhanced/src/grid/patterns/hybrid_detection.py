"""Hybrid pattern detection system for dynamic knowledge base.

This module implements a hybrid approach combining statistical, syntactic,
and neural network pattern detection methods for comprehensive landscape monitoring.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from grid.essence.core_state import EssentialState

logger = logging.getLogger(__name__)


@dataclass
class PatternDetectionResult:
    """Result from pattern detection."""

    patterns: list[str]
    confidence: float
    method: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class HybridPatternResult:
    """Combined result from hybrid pattern detection."""

    statistical_patterns: list[str]
    syntactic_patterns: list[str]
    neural_patterns: list[str]
    combined_patterns: list[str]
    confidence_scores: dict[str, float]
    metadata: dict[str, Any] = field(default_factory=dict)


class StatisticalPatternDetector:
    """Statistical pattern detector for trend analysis and distribution changes."""

    def __init__(self) -> None:
        self.history: list[dict[str, Any]] = []

    async def detect(self, state: EssentialState, window_size: int = 10) -> PatternDetectionResult:
        """Detect statistical patterns in state evolution.

        Args:
            state: Current essential state
            window_size: Size of sliding window for trend analysis

        Returns:
            PatternDetectionResult with statistical patterns
        """
        # Extract numeric metrics from quantum state
        metrics = self._extract_metrics(state)

        # Add to history
        self.history.append(metrics)

        # Keep only recent history
        if len(self.history) > window_size * 2:
            self.history = self.history[-window_size * 2 :]

        patterns = []
        confidence = 0.0

        if len(self.history) >= window_size:
            # Detect trends
            trends = self._detect_trends(window_size)
            patterns.extend(trends)

            # Detect distribution changes
            distribution_changes = self._detect_distribution_changes(window_size)
            patterns.extend(distribution_changes)

            # Calculate confidence based on history depth
            confidence = min(len(self.history) / (window_size * 2), 1.0)

        return PatternDetectionResult(
            patterns=patterns,
            confidence=confidence,
            method="statistical",
            metadata={"history_size": len(self.history), "window_size": window_size},
        )

    def _extract_metrics(self, state: EssentialState) -> dict[str, float]:
        """Extract numeric metrics from state."""
        metrics: dict[str, float] = {
            "coherence": state.coherence_factor,
            "context_depth": state.context_depth,
        }

        # Extract metrics from quantum state
        if isinstance(state.quantum_state, dict):
            for key, value in state.quantum_state.items():
                if isinstance(value, (int, float)):
                    metrics[key] = float(value)
                elif isinstance(value, dict) and "value" in value:
                    try:
                        metrics[key] = float(value["value"])
                    except (ValueError, TypeError):
                        pass

        return metrics

    def _detect_trends(self, window_size: int) -> list[str]:
        """Detect trends in metrics."""
        if len(self.history) < window_size:
            return []

        trends = []
        recent = self.history[-window_size:]

        # Get all metric keys
        all_keys = set()
        for entry in recent:
            all_keys.update(entry.keys())

        for key in all_keys:
            values = [entry.get(key, 0.0) for entry in recent if key in entry]
            if len(values) < 2:
                continue

            # Calculate trend (slope)
            x = np.arange(len(values))
            slope = np.polyfit(x, values, 1)[0]

            if slope > 0.01:
                trends.append(f"INCREASING_{key.upper()}")
            elif slope < -0.01:
                trends.append(f"DECREASING_{key.upper()}")

        return trends

    def _detect_distribution_changes(self, window_size: int) -> list[str]:
        """Detect distribution changes in metrics."""
        if len(self.history) < window_size * 2:
            return []

        changes = []
        old_window = self.history[-window_size * 2 : -window_size]
        new_window = self.history[-window_size:]

        # Get all metric keys
        all_keys = set()
        for entry in old_window + new_window:
            all_keys.update(entry.keys())

        for key in all_keys:
            old_values = [entry.get(key, 0.0) for entry in old_window if key in entry]
            new_values = [entry.get(key, 0.0) for entry in new_window if key in entry]

            if len(old_values) < 2 or len(new_values) < 2:
                continue

            # Compare means
            old_mean = np.mean(old_values)
            new_mean = np.mean(new_values)

            # Compare variances
            old_var = np.var(old_values)
            new_var = np.var(new_values)

            # Detect significant changes
            mean_change = abs(new_mean - old_mean) / (old_mean + 1e-6)
            var_change = abs(new_var - old_var) / (old_var + 1e-6)

            if mean_change > 0.1:
                changes.append(f"DISTRIBUTION_SHIFT_{key.upper()}")
            if var_change > 0.2:
                changes.append(f"VARIANCE_CHANGE_{key.upper()}")

        return changes


class SyntacticPatternDetector:
    """Syntactic pattern detector for structural pattern recognition."""

    def __init__(self) -> None:
        self.structural_patterns = {
            "hierarchical": ["parent", "child", "level", "depth", "tree"],
            "network": ["node", "edge", "connection", "graph", "link"],
            "sequential": ["sequence", "order", "step", "chain", "pipeline"],
            "parallel": ["parallel", "concurrent", "simultaneous", "async"],
            "circular": ["cycle", "loop", "circular", "recursive"],
        }

    async def detect(self, state: EssentialState) -> PatternDetectionResult:
        """Detect syntactic/structural patterns in state.

        Args:
            state: Current essential state

        Returns:
            PatternDetectionResult with syntactic patterns
        """
        patterns = []
        confidence = 0.0

        # Analyze quantum state structure
        structure = self._analyze_structure(state.quantum_state)

        # Match against known structural patterns - check both structure and quantum_state
        quantum_state_str = str(state.quantum_state).lower() if isinstance(state.quantum_state, dict) else ""
        quantum_state_keys = list(state.quantum_state.keys()) if isinstance(state.quantum_state, dict) else []

        for pattern_type, keywords in self.structural_patterns.items():
            # Check structure
            if self._matches_pattern(structure, keywords):
                patterns.append(f"SYNTACTIC_{pattern_type.upper()}")
            # Also check quantum state directly
            elif any(
                keyword.lower() in quantum_state_str or keyword.lower() in [k.lower() for k in quantum_state_keys]
                for keyword in keywords
            ):
                patterns.append(f"SYNTACTIC_{pattern_type.upper()}")

        # Analyze relational web if available
        if hasattr(state, "relational_web"):
            rel_patterns = self._analyze_relationships(state.relational_web)
            patterns.extend(rel_patterns)

        # Calculate confidence based on pattern matches
        confidence = min(len(patterns) / 5.0, 1.0)

        return PatternDetectionResult(
            patterns=patterns,
            confidence=confidence,
            method="syntactic",
            metadata={"structure_type": structure.get("type", "unknown")},
        )

    def _analyze_structure(self, quantum_state: dict[str, Any]) -> dict[str, Any]:
        """Analyze structure of quantum state."""
        structure = {"type": "unknown", "depth": 0, "breadth": 0}

        if isinstance(quantum_state, dict):
            structure["type"] = "dictionary"
            structure["breadth"] = len(quantum_state)

            # Check for nested structures
            max_depth = 0
            for value in quantum_state.values():
                if isinstance(value, dict):
                    nested = self._analyze_structure(value)
                    max_depth = max(max_depth, nested["depth"] + 1)
                elif isinstance(value, list):
                    max_depth = max(max_depth, 1)

            structure["depth"] = max_depth

        elif isinstance(quantum_state, list):
            structure["type"] = "list"
            structure["breadth"] = len(quantum_state)

        return structure

    def _matches_pattern(self, structure: dict[str, Any], keywords: list[str]) -> bool:
        """Check if structure matches pattern keywords."""
        # Check structure keys and values
        structure_str = str(structure).lower()
        structure_keys = [k.lower() for k in structure.keys()] if isinstance(structure, dict) else []

        # Check if any keyword matches structure string or keys
        return any(keyword.lower() in structure_str or keyword.lower() in structure_keys for keyword in keywords)

    def _analyze_relationships(self, relational_web: dict[str, Any]) -> list[str]:
        """Analyze relationships in relational web."""
        patterns = []

        if not isinstance(relational_web, dict):
            return patterns

        # Check for hierarchical relationships
        if any("parent" in str(k).lower() or "child" in str(k).lower() for k in relational_web.keys()):
            patterns.append("SYNTACTIC_HIERARCHICAL")

        # Check for network relationships
        if len(relational_web) > 3:
            patterns.append("SYNTACTIC_NETWORK")

        return patterns


class NeuralPatternDetector:
    """Neural network pattern detector for deep pattern learning.

    This is a simplified implementation. In a full system, this would use
    actual neural networks for pattern learning.
    """

    def __init__(self) -> None:
        self.learned_patterns: dict[str, float] = {}
        self.pattern_weights: dict[str, float] = {}

    async def detect(self, state: EssentialState) -> PatternDetectionResult:
        """Detect patterns using neural network approach.

        Args:
            state: Current essential state

        Returns:
            PatternDetectionResult with neural patterns
        """
        patterns = []
        confidence = 0.0

        # Extract features from state
        features = self._extract_features(state)

        # Match against learned patterns
        for pattern_name, pattern_features in self.learned_patterns.items():
            similarity = self._calculate_similarity(features, pattern_features)
            if similarity > 0.7:
                patterns.append(f"NEURAL_{pattern_name.upper()}")

        # Learn new patterns if confidence is high
        if len(patterns) == 0 and state.coherence_factor > 0.7:
            pattern_name = f"pattern_{len(self.learned_patterns)}"
            self.learned_patterns[pattern_name] = features
            self.pattern_weights[pattern_name] = state.coherence_factor

        # Calculate confidence based on pattern matches and coherence
        confidence = min((len(patterns) * 0.3) + (state.coherence_factor * 0.7), 1.0)

        return PatternDetectionResult(
            patterns=patterns,
            confidence=confidence,
            method="neural",
            metadata={
                "learned_patterns": len(self.learned_patterns),
                "features": len(features),
            },
        )

    def _extract_features(self, state: EssentialState) -> dict[str, float]:
        """Extract features from state for neural pattern matching."""
        features: dict[str, float] = {
            "coherence": state.coherence_factor,
            "context_depth": state.context_depth,
        }

        # Extract features from quantum state
        if isinstance(state.quantum_state, dict):
            # Count different types of values
            features["dict_size"] = len(state.quantum_state)
            features["numeric_count"] = sum(1 for v in state.quantum_state.values() if isinstance(v, (int, float)))
            features["dict_count"] = sum(1 for v in state.quantum_state.values() if isinstance(v, dict))
            features["list_count"] = sum(1 for v in state.quantum_state.values() if isinstance(v, list))

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

            # Normalize and calculate similarity
            max_val = max(abs(val1), abs(val2), 1.0)
            similarity = 1.0 - abs(val1 - val2) / max_val
            similarities.append(max(0.0, similarity))

        return sum(similarities) / len(similarities) if similarities else 0.0


class HybridPatternDetector:
    """Hybrid pattern detector combining statistical, syntactic, and neural approaches."""

    def __init__(self) -> None:
        self.statistical = StatisticalPatternDetector()
        self.syntactic = SyntacticPatternDetector()
        self.neural = NeuralPatternDetector()

    async def detect(self, state: EssentialState, weights: dict[str, float] | None = None) -> HybridPatternResult:
        """Detect patterns using hybrid approach.

        Args:
            state: Current essential state
            weights: Optional weights for combining methods (default: equal weights)

        Returns:
            HybridPatternResult with combined patterns
        """
        if weights is None:
            weights = {"statistical": 0.33, "syntactic": 0.33, "neural": 0.34}

        # Run all detectors in parallel
        statistical_result = await self.statistical.detect(state)
        syntactic_result = await self.syntactic.detect(state)
        neural_result = await self.neural.detect(state)

        # Combine patterns
        all_patterns = set()
        all_patterns.update(statistical_result.patterns)
        all_patterns.update(syntactic_result.patterns)
        all_patterns.update(neural_result.patterns)

        # Calculate weighted confidence
        confidence_scores = {
            "statistical": statistical_result.confidence * weights["statistical"],
            "syntactic": syntactic_result.confidence * weights["syntactic"],
            "neural": neural_result.confidence * weights["neural"],
        }

        overall_confidence = sum(confidence_scores.values())

        # Select high-confidence patterns
        combined_patterns = list(all_patterns)

        # Metadata
        metadata = {
            "statistical": statistical_result.metadata,
            "syntactic": syntactic_result.metadata,
            "neural": neural_result.metadata,
            "overall_confidence": overall_confidence,
            "weights": weights,
        }

        logger.info(
            f"Hybrid detection: {len(statistical_result.patterns)} statistical, "
            f"{len(syntactic_result.patterns)} syntactic, "
            f"{len(neural_result.patterns)} neural patterns"
        )

        return HybridPatternResult(
            statistical_patterns=statistical_result.patterns,
            syntactic_patterns=syntactic_result.patterns,
            neural_patterns=neural_result.patterns,
            combined_patterns=combined_patterns,
            confidence_scores=confidence_scores,
            metadata=metadata,
        )
