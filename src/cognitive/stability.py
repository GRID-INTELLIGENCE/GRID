"""Stability metrics for cognitive vectors.

As documented in docs/research/k1_cognitive_vectors.md

Stability metrics measure the consistency and coherence of cognitive vectors
over time, across versions, and between glimpses.
"""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import numpy as np

from cognitive.cognitive_unit import CognitiveVector

logger = logging.getLogger(__name__)


@dataclass
class StabilityMetrics:
    """Container for all stability metrics.

    Measures:
    - Coherence: Similarity of consecutive vectors
    - Entanglement: Cross-modal correlation
    - Persistence: Topology stability across versions
    - Decoherence: Duration before coherence drops below threshold
    """

    # Coherence metrics
    coherence_score: float = 0.0
    coherence_variance: float = 0.0
    coherence_trend: float = 0.0  # Positive = improving, negative = declining

    # Entanglement metrics
    entanglement_ratio: float = 0.0
    cross_modal_correlation: dict[str, float] = field(default_factory=dict)

    # Persistence metrics
    persistence_index: float = 0.0
    topology_similarity: dict[tuple[int, int], float] = field(default_factory=dict)

    # Decoherence metrics
    decoherence_time: float = 0.0  # Duration before coherence drops below threshold
    decoherence_threshold: float = 0.85

    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    window_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "coherence_score": self.coherence_score,
            "coherence_variance": self.coherence_variance,
            "coherence_trend": self.coherence_trend,
            "entanglement_ratio": self.entanglement_ratio,
            "cross_modal_correlation": self.cross_modal_correlation,
            "persistence_index": self.persistence_index,
            "topology_similarity": {f"{k[0]}-{k[1]}": v for k, v in self.topology_similarity.items()},
            "decoherence_time": self.decoherence_time,
            "decoherence_threshold": self.decoherence_threshold,
            "timestamp": self.timestamp.isoformat(),
            "window_id": self.window_id,
            "metadata": self.metadata,
        }

    def is_stable(self, threshold: float = 0.7) -> bool:
        """Check if metrics indicate stable cognitive state.

        Args:
            threshold: Stability threshold (default 0.7)

        Returns:
            True if stable
        """
        avg_metrics = (self.coherence_score + self.entanglement_ratio + self.persistence_index) / 3.0

        return avg_metrics >= threshold


class StabilityAnalyzer:
    """Analyzer for cognitive vector stability metrics.

    Computes stability metrics for:
    - Single sequences (coherence, entanglement)
    - Multiple versions (persistence, topology)
    - Time-series (decoherence, trends)
    """

    def __init__(self, history_size: int = 100):
        """Initialize the stability analyzer.

        Args:
            history_size: Maximum number of vectors to track for trend analysis
        """
        self.history_size = history_size
        self.vector_history: deque[tuple[CognitiveVector, datetime]] = deque(maxlen=history_size)

    def coherence_score(self, vectors: list[CognitiveVector]) -> float:
        """Measure similarity of consecutive vectors.

        Coherence measures how smoothly the cognitive state transitions
        from one moment to the next. High coherence indicates stable,
        predictable evolution.

        Args:
            vectors: List of cognitive vectors

        Returns:
            Coherence score (0-1, 1 = perfectly smooth transitions)
        """
        if len(vectors) < 2:
            return 1.0

        similarities = []
        for i in range(1, len(vectors)):
            sim = self._vector_similarity(vectors[i - 1], vectors[i])
            similarities.append(sim)

        return sum(similarities) / len(similarities)

    def entanglement_ratio(self, vectors: list[CognitiveVector]) -> float:
        """Measure cross-modal correlation within vectors.

        Entanglement measures how different sensory modalities are correlated.
        High entanglement indicates integrated perception (e.g., visual and
        auditory information are processed together).

        Args:
            vectors: List of cognitive vectors

        Returns:
            Entanglement ratio (0-1, 1 = perfectly entangled)
        """
        if not vectors:
            return 0.0

        # Concatenate all vectors
        matrix = np.vstack([v.to_matrix() for v in vectors])

        # Split into modalities (3 vision, 2 sound, 2 locomotion)
        vision_cols = matrix[:, :3]
        sound_cols = matrix[:, 3:5]
        locomotion_cols = matrix[:, 5:7]

        # Calculate correlations between modalities
        correlations = []

        # Vision-Sound correlation
        vision_sound = self._correlation_2d(vision_cols.mean(axis=1), sound_cols.mean(axis=1))
        correlations.append(abs(vision_sound))

        # Vision-Locomotion correlation
        vision_locomotion = self._correlation_2d(vision_cols.mean(axis=1), locomotion_cols.mean(axis=1))
        correlations.append(abs(vision_locomotion))

        # Sound-Locomotion correlation
        sound_locomotion = self._correlation_2d(sound_cols.mean(axis=1), locomotion_cols.mean(axis=1))
        correlations.append(abs(sound_locomotion))

        return sum(correlations) / len(correlations) if correlations else 0.0

    def persistence_index(self, vectors_per_version: list[list[CognitiveVector]]) -> float:
        """Measure topology stability across versions.

        Persistence measures how much the cognitive trajectory structure
        is preserved across different versions/glimpses.

        Args:
            vectors_per_version: List of cognitive vector lists, one per version

        Returns:
            Persistence index (0-1, 1 = perfectly preserved topology)
        """
        if len(vectors_per_version) < 2:
            return 1.0

        # Compare consecutive versions
        similarities = []
        for i in range(1, len(vectors_per_version)):
            v1 = vectors_per_version[i - 1]
            v2 = vectors_per_version[i]

            # Compare topological features
            topo_sim = self._topology_similarity(v1, v2)
            similarities.append(topo_sim)

        return sum(similarities) / len(similarities) if similarities else 1.0

    def decoherence_time(
        self,
        vectors: list[CognitiveVector],
        threshold: float = 0.85,
        time_interval: float = 1.0,
    ) -> float:
        """Measure duration before coherence drops below threshold.

        Decoherence time indicates how long cognitive state remains coherent
        before destabilizing.

        Args:
            vectors: List of cognitive vectors
            threshold: Coherence threshold (default 0.85)
            time_interval: Time interval between vectors (seconds)

        Returns:
            Decoherence time (seconds)
        """
        if len(vectors) < 2:
            return float("inf")  # Never decoheres with < 2 vectors

        # Calculate rolling coherence
        for i in range(1, len(vectors)):
            # Check coherence of last `window_size` vectors
            window = vectors[max(0, i - 5) : i + 1]
            if len(window) < 2:
                continue

            coh = self.coherence_score(window)
            if coh < threshold:
                return i * time_interval

        return float("inf")  # Never decohered

    def _vector_similarity(self, v1: CognitiveVector, v2: CognitiveVector) -> float:
        """Calculate similarity between two cognitive vectors.

        Args:
            v1: First cognitive vector
            v2: Second cognitive vector

        Returns:
            Similarity score (0-1)
        """
        matrix1 = v1.to_matrix()
        matrix2 = v2.to_matrix()

        # Use mean cosine similarity across units
        if matrix1.shape[0] != matrix2.shape[0]:
            # Different lengths - pad the shorter one
            max_len = max(matrix1.shape[0], matrix2.shape[0])
            padded1 = np.zeros((max_len, matrix1.shape[1]))
            padded2 = np.zeros((max_len, matrix2.shape[1]))
            padded1[: matrix1.shape[0]] = matrix1
            padded2[: matrix2.shape[0]] = matrix2
            matrix1, matrix2 = padded1, padded2

        # Calculate cosine similarity for each position
        similarities = []
        for i in range(matrix1.shape[0]):
            dot = np.dot(matrix1[i], matrix2[i])
            norm1 = np.linalg.norm(matrix1[i])
            norm2 = np.linalg.norm(matrix2[i])

            if norm1 == 0 or norm2 == 0:
                similarities.append(0.0)
            else:
                similarities.append(dot / (norm1 * norm2))

        return sum(similarities) / len(similarities) if similarities else 0.0

    def _correlation_2d(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate Pearson correlation between two 1D arrays.

        Args:
            a: First array
            b: Second array

        Returns:
            Correlation coefficient (-1 to 1)
        """
        if len(a) != len(b) or len(a) < 2:
            return 0.0

        mean_a = np.mean(a)
        mean_b = np.mean(b)

        numerator = np.sum((a - mean_a) * (b - mean_b))
        denominator = np.sqrt(np.sum((a - mean_a) ** 2)) * np.sqrt(np.sum((b - mean_b) ** 2))

        if denominator == 0:
            return 0.0

        return float(numerator / denominator)

    def _topology_similarity(self, v1: list[CognitiveVector], v2: list[CognitiveVector]) -> float:
        """Compare topological features of two vector sequences.

        Args:
            v1: First list of cognitive vectors
            v2: Second list of cognitive vectors

        Returns:
            Topology similarity (0-1)
        """
        if not v1 or not v2:
            return 0.0

        # Extract key topological features
        features1 = self._extract_topology_features(v1)
        features2 = self._extract_topology_features(v2)

        # Compare features
        scores = []

        # Length similarity
        len_sim = 1.0 - abs(len(v1) - len(v2)) / max(len(v1), len(v2))
        scores.append(len_sim)

        # Centroid similarity
        centroid_sim = float(1.0 - np.linalg.norm(features1["centroid"] - features2["centroid"]) / 2.0)
        scores.append(centroid_sim)

        # Straightness similarity
        straight_sim = 1.0 - abs(features1["straightness"] - features2["straightness"])
        scores.append(straight_sim)

        # Variance similarity
        var_diff = abs(features1["variance"] - features2["variance"])
        var_sim = 1.0 / (1.0 + var_diff)
        scores.append(var_sim)

        return sum(scores) / len(scores)

    def _extract_topology_features(self, vectors: list[CognitiveVector]) -> dict[str, Any]:
        """Extract topological features from a vector sequence.

        Args:
            vectors: List of cognitive vectors

        Returns:
            Dictionary of topological features
        """
        # Combine all units from all vectors
        all_units = []
        for v in vectors:
            all_units.extend(v.units)

        if not all_units:
            return {
                "centroid": np.zeros(32),
                "straightness": 1.0,
                "variance": 0.0,
            }

        # Create combined vector
        combined = CognitiveVector(units=all_units)

        return {
            "centroid": combined.centroid(),
            "straightness": combined.straightness(),
            "variance": combined.variance(),
        }

    def compute_all_metrics(
        self,
        vectors: list[CognitiveVector],
        window_id: str = "",
        vectors_per_version: list[list[CognitiveVector]] | None = None,
        decoherence_threshold: float = 0.85,
    ) -> StabilityMetrics:
        """Compute all stability metrics for a set of vectors.

        Args:
            vectors: List of cognitive vectors
            window_id: Optional window identifier
            vectors_per_version: Optional list of vector lists for persistence analysis
            decoherence_threshold: Threshold for decoherence detection

        Returns:
            StabilityMetrics with all computed metrics
        """
        # Add to history for trend analysis
        now = datetime.now(UTC)
        for v in vectors:
            self.vector_history.append((v, now))

        # Compute coherence
        coherence = self.coherence_score(vectors)

        # Compute coherence variance
        if len(self.vector_history) > 5:
            recent_coherences = []
            for i in range(1, min(6, len(self.vector_history))):
                prev_vec = self.vector_history[-i - 1][0]
                curr_vec = self.vector_history[-i][0]
                recent_coherences.append(self._vector_similarity(prev_vec, curr_vec))
            coherence_variance = np.var(recent_coherences) if recent_coherences else 0.0
        else:
            coherence_variance = 0.0

        # Compute coherence trend
        if len(self.vector_history) > 10:
            old_coherence = self.coherence_score([v for v, _ in list(self.vector_history)[:10]])
            coherence_trend = coherence - old_coherence
        else:
            coherence_trend = 0.0

        # Compute entanglement
        entanglement = self.entanglement_ratio(vectors)

        # Compute persistence
        if vectors_per_version is not None:
            persistence = self.persistence_index(vectors_per_version)

            # Compute topology similarity between specific version pairs
            topology_sim = {}
            for i in range(len(vectors_per_version) - 1):
                for j in range(i + 1, min(i + 3, len(vectors_per_version))):
                    sim = self._topology_similarity(vectors_per_version[i], vectors_per_version[j])
                    topology_sim[(i, j)] = sim
        else:
            persistence = 1.0
            topology_sim = {}

        # Compute decoherence time
        decoherence = self.decoherence_time(vectors, decoherence_threshold)

        return StabilityMetrics(
            coherence_score=coherence,
            coherence_variance=coherence_variance,
            coherence_trend=coherence_trend,
            entanglement_ratio=entanglement,
            persistence_index=persistence,
            topology_similarity=topology_sim,
            decoherence_time=decoherence,
            decoherence_threshold=decoherence_threshold,
            window_id=window_id,
            metadata={
                "vector_count": len(vectors),
                "history_size": len(self.vector_history),
            },
        )


def detect_coherence_breakdown(
    vectors: list[CognitiveVector],
    threshold: float = 0.7,
    window_size: int = 5,
) -> list[int]:
    """Detect points where coherence drops below threshold.

    Args:
        vectors: List of cognitive vectors
        threshold: Coherence threshold
        window_size: Window size for coherence calculation

    Returns:
        List of indices where coherence drops below threshold
    """
    if len(vectors) < window_size:
        return []

    breakdowns = []
    for i in range(window_size - 1, len(vectors)):
        window = vectors[i - window_size + 1 : i + 1]

        # Calculate pairwise coherence
        similarities = []
        for j in range(1, len(window)):
            sim = np.mean(
                [
                    np.dot(
                        window[j - 1].units[k].to_vector(),
                        window[j].units[k].to_vector() if k < len(window[j].units) else np.zeros(32),
                    )
                    for k in range(min(len(window[j - 1].units), len(window[j].units)))
                ]
            )
            similarities.append(sim)

        avg_coherence = sum(similarities) / len(similarities) if similarities else 1.0

        if avg_coherence < threshold:
            breakdowns.append(i)

    return breakdowns


def calculate_cross_modal_coupling(vectors: list[CognitiveVector]) -> dict[str, dict[str, float]]:
    """Calculate coupling strength between different modalities over time.

    Args:
        vectors: List of cognitive vectors

    Returns:
        Dictionary mapping modality pairs to coupling statistics
    """
    modalities = ["vision", "sound", "locomotion"]
    indices = {"vision": (0, 3), "sound": (3, 5), "locomotion": (5, 7)}

    results = {}

    for i, mod1 in enumerate(modalities):
        for j, mod2 in enumerate(modalities):
            if i >= j:
                continue

            pair_name = f"{mod1}-{mod2}"

            # Extract modality data
            idx1_start, idx1_end = indices[mod1]
            idx2_start, idx2_end = indices[mod2]

            # Calculate coupling over time
            couplings = []
            for vec in vectors:
                matrix = vec.to_matrix()

                if matrix.shape[0] < 2:
                    continue

                data1 = matrix[:, idx1_start:idx1_end].flatten()
                data2 = matrix[:, idx2_start:idx2_end].flatten()

                # Calculate coupling as correlation
                corr = np.corrcoef(data1, data2)[0, 1] if len(data1) > 1 and len(data2) > 1 else 0.0
                couplings.append(abs(corr))

            results[pair_name] = {
                "mean_coupling": float(np.mean(couplings)) if couplings else 0.0,
                "std_coupling": float(np.std(couplings)) if len(couplings) > 1 else 0.0,
                "max_coupling": float(np.max(couplings)) if couplings else 0.0,
                "min_coupling": float(np.min(couplings)) if couplings else 0.0,
            }

    return results
