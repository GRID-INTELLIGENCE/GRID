"""Pattern vectorization for K1 prerequisites.

Implements Phase 2 from k1_cognitive_vectors.md:
- Pattern vectorization
- Drift apex detection
- RDP simplification
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from cognitive.cognitive_unit import (
    CognitiveUnit,
    CognitiveVector,
    apply_rdp_simplification,
    detect_drift_apex,
)

logger = logging.getLogger(__name__)


@dataclass
class VectorizationConfig:
    """Configuration for cognitive vectorization."""

    # Vector dimensions
    vector_size: int = 32  # Output vector size

    # Simplification parameters
    rdp_epsilon: float = 0.05  # RDP simplification threshold

    # Normalization parameters
    normalize: bool = True  # Whether to normalize vectors
    clip_values: bool = True  # Whether to clip values to [0, 1]

    # Feature extraction
    include_derivative: bool = True  # Include derivative features
    include_integral: bool = False  # Include integral features

    # Temporal window
    window_size: int = 10  # Number of units to vectorize together

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class VectorizationResult:
    """Result of vectorizing a sequence of cognitive units."""

    vectors: np.ndarray  # Shape: (n_vectors, vector_size)
    feature_names: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_feature_vector(self, index: int) -> np.ndarray:
        """Get a specific feature vector.

        Args:
            index: Index of vector to retrieve

        Returns:
            Feature vector
        """
        return self.vectors[index]

    def get_statistics(self) -> dict[str, float]:
        """Get statistics about the vectorized representation.

        Returns:
            Dictionary of statistics
        """
        return {
            "num_vectors": len(self.vectors),
            "vector_size": self.vectors.shape[1] if len(self.vectors) > 0 else 0,
            "mean_norm": float(np.mean(np.linalg.norm(self.vectors, axis=1))),
            "std_norm": float(np.std(np.linalg.norm(self.vectors, axis=1))),
            "sparsity": float(np.mean(self.vectors == 0.0)),
        }


class CognitiveVectorizer:
    """Pattern vectorization for K1 prerequisites.

    Converts sequences of cognitive units into geometric vectors for
    pattern analysis and K1 tracking.
    """

    def __init__(self, config: VectorizationConfig | None = None):
        """Initialize the cognitive vectorizer.

        Args:
            config: Optional vectorization configuration
        """
        self.config = config or VectorizationConfig()

        # Feature definitions
        self._init_feature_names()

        logger.info(f"CognitiveVectorizer initialized with config: vector_size={self.config.vector_size}")

    def _init_feature_names(self) -> None:
        """Initialize feature name list."""
        base_features = [
            "vision_hue",
            "vision_luminance",
            "vision_saturation",
            "sound_mel",
            "sound_amplitude",
            "locomotion_heading",
            "locomotion_speed",
        ]

        derivative_features = [f"{f}_derivative" for f in base_features] if self.config.include_derivative else []
        integral_features = [f"{f}_integral" for f in base_features] if self.config.include_integral else []

        # Fill remaining slots with contextual features
        contextual_count = (
            self.config.vector_size - len(base_features) - len(derivative_features) - len(integral_features)
        )
        contextual_features = [f"context_{i}" for i in range(contextual_count)] if contextual_count > 0 else []

        self.feature_names = base_features + derivative_features + integral_features + contextual_features

    def vectorize_behavior(self, units: list[CognitiveUnit]) -> CognitiveVector:
        """Convert sequence of units into geometric vector.

        Args:
            units: List of cognitive units

        Returns:
            CognitiveVector with vectorized representation
        """
        if not units:
            return CognitiveVector()

        # Convert each unit to vector
        vectors = np.array([u.to_vector(self.config.vector_size) for u in units])

        # Calculate derivatives if requested
        if self.config.include_derivative and len(vectors) > 1:
            derivatives = np.diff(vectors, axis=0)
            # Pad to match original shape
            derivatives = np.vstack([derivatives, derivatives[-1:]])

            # Concatenate with original vectors
            base_size = 7  # Number of base features
            vectors = vectors.copy()

            # Add derivative features (capped at vector_size)
            deriv_slots = min(derivatives.shape[1], self.config.vector_size - base_size)
            if deriv_slots > 0:
                vectors = np.hstack([vectors[:, :base_size], derivatives[:, :deriv_slots]])

        # Normalize if requested
        if self.config.normalize:
            vectors = self._normalize_vectors(vectors)

        # Clip values if requested
        if self.config.clip_values:
            vectors = np.clip(vectors, 0.0, 1.0)

        # Create result
        VectorizationResult(
            vectors=vectors,
            feature_names=self.feature_names[: vectors.shape[1]],
            metadata={
                "num_units": len(units),
                "config": self.config.metadata,
            },
        )

        # Return cognitive vector with updated units
        return CognitiveVector(units=units)

    def vectorize_windows(
        self,
        units: list[CognitiveUnit],
        stride: int = 1,
    ) -> list[np.ndarray]:
        """Vectorize sliding windows of units.

        Args:
            units: List of cognitive units
            stride: Step size between windows

        Returns:
            List of window vectors
        """
        if len(units) < self.config.window_size:
            # Pad if not enough units
            units = self._pad_units(units, self.config.window_size)

        windows = []
        for i in range(0, len(units) - self.config.window_size + 1, stride):
            window = units[i : i + self.config.window_size]
            cv = self.vectorize_behavior(window)
            if cv.to_matrix().shape[0] > 0:
                windows.append(cv.centroid())

        return windows

    def _normalize_vectors(self, vectors: np.ndarray) -> np.ndarray:
        """Normalize vectors to unit length.

        Args:
            vectors: Input vectors

        Returns:
            Normalized vectors
        """
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0  # Avoid division by zero
        return vectors / norms

    def _pad_units(self, units: list[CognitiveUnit], target_size: int) -> list[CognitiveUnit]:
        """Pad units to target size.

        Args:
            units: Input units
            target_size: Target size

        Returns:
            Padded units
        """
        if len(units) >= target_size:
            return units

        # Pad with copies of the last unit
        last_unit = units[-1] if units else CognitiveUnit()
        padding = [last_unit] * (target_size - len(units))
        return units + padding

    def detect_drift_apex(
        self,
        units: list[CognitiveUnit] | CognitiveVector,
    ) -> tuple[float, int]:
        """Detect the furthest point from expected path.

        Args:
            units: List of cognitive units or CognitiveVector

        Returns:
            Tuple of (drift_magnitude, apex_index)
        """
        # Extract locomotion components
        if isinstance(units, CognitiveVector):
            loco_components = [u.locomotion for u in units.units]
        else:
            loco_components = [u.locomotion for u in units]

        return detect_drift_apex(loco_components)

    def apply_rdp_simplification(
        self,
        units: list[CognitiveUnit] | CognitiveVector,
        epsilon: float | None = None,
    ) -> list[tuple[float, float]]:
        """Apply Ramer-Douglas-Peucker simplification to reduce points.

        Args:
            units: List of cognitive units or CognitiveVector
            epsilon: Optional custom epsilon (uses config default if None)

        Returns:
            Simplified list of (x, y) points
        """
        epsilon = epsilon or self.config.rdp_epsilon

        # Extract points from locomotion components
        if isinstance(units, CognitiveVector):
            loco_components = [u.locomotion for u in units.units]
        else:
            loco_components = [u.locomotion for u in units]

        # Convert to (x, y) coordinates
        points = []
        for loco in loco_components:
            x = math.cos(loco.heading * 2 * math.pi) * loco.speed
            y = math.sin(loco.heading * 2 * math.pi) * loco.speed
            points.append((x, y))

        return apply_rdp_simplification(points, epsilon)

    def compute_geometric_features(self, units: list[CognitiveUnit]) -> dict[str, float]:
        """Compute geometric features from a sequence of units.

        Args:
            units: List of cognitive units

        Returns:
            Dictionary of geometric features
        """
        if len(units) < 2:
            return {
                "length": 0.0,
                "displacement": 0.0,
                "straightness": 1.0,
                "curvature": 0.0,
                "angular_change": 0.0,
            }

        cv = self.vectorize_behavior(units)

        # Basic geometric features
        length = cv.length()
        displacement = cv.displacement()
        straightness = cv.straightness()

        # Curvature (average angle change)
        angles = []
        for i in range(1, len(units)):
            loco1 = units[i - 1].locomotion
            loco2 = units[i].locomotion

            # Convert to vectors
            v1 = np.array(
                [
                    math.cos(loco1.heading * 2 * math.pi) * loco1.speed,
                    math.sin(loco1.heading * 2 * math.pi) * loco1.speed,
                ]
            )
            v2 = np.array(
                [
                    math.cos(loco2.heading * 2 * math.pi) * loco2.speed,
                    math.sin(loco2.heading * 2 * math.pi) * loco2.speed,
                ]
            )

            # Calculate angle between vectors
            if np.linalg.norm(v1) > 0 and np.linalg.norm(v2) > 0:
                dot = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
                dot = max(-1.0, min(1.0, dot))
                angles.append(math.acos(dot))

        curvature = float(np.mean(angles)) if angles else 0.0

        # Total angular change
        angular_change = float(sum(angles)) if angles else 0.0

        return {
            "length": length,
            "displacement": displacement,
            "straightness": straightness,
            "curvature": curvature,
            "angular_change": angular_change,
        }

    def extract_trajectory_signature(
        self,
        units: list[CognitiveUnit],
        resolution: int = 16,
    ) -> np.ndarray:
        """Extract a fixed-size signature from a variable-length trajectory.

        Args:
            units: List of cognitive units
            resolution: Number of points in the signature

        Returns:
            Fixed-size signature vector
        """
        if not units:
            return np.zeros(resolution * 2)

        cv = self.vectorize_behavior(units)

        # Resample trajectory to fixed number of points
        matrix = cv.to_matrix()
        if matrix.shape[0] == 0:
            return np.zeros(resolution * 2)

        # Use centroid as trajectory representation
        # This is a simplified approach - could use more sophisticated methods
        centroid = cv.centroid()

        # Create signature by combining centroid with drift information
        drift_magnitude, drift_index = self.detect_drift_apex(units)

        # Signature: [centroid (32), drift_magnitude, drift_index, rest padded]
        signature = np.zeros(resolution * 2)

        # First half: centroid
        sig_size = min(len(centroid), resolution)
        signature[:sig_size] = centroid[:sig_size]

        # Second half: additional features
        signature[resolution] = drift_magnitude
        if drift_index > 0:
            signature[resolution + 1] = drift_index / len(units)

        # Add geometric features
        geo = self.compute_geometric_features(units)
        feature_names = ["length", "displacement", "straightness", "curvature", "angular_change"]
        for i, name in enumerate(feature_names):
            if resolution + 2 + i < len(signature):
                signature[resolution + 2 + i] = geo[name]

        return signature

    def cluster_vectors(
        self,
        vectors: list[np.ndarray],
        n_clusters: int = 3,
    ) -> dict[str, Any]:
        """Cluster vectors using k-means.

        Args:
            vectors: List of vectors to cluster
            n_clusters: Number of clusters

        Returns:
            Dictionary with cluster assignments and centroids
        """
        if len(vectors) < n_clusters:
            # Not enough vectors for requested clusters
            return {
                "assignments": list(range(len(vectors))),
                "centroids": vectors,
                "inertia": 0.0,
            }

        # Convert to numpy array
        X = np.array(vectors)

        # Simple k-means implementation

        def simple_kmeans(data: np.ndarray, k: int, max_iter: int = 100) -> tuple[np.ndarray, np.ndarray, float]:
            """Simple k-means clustering."""
            # Initialize centroids randomly
            indices = np.random.choice(len(data), k, replace=False)
            centroids = data[indices]

            for _ in range(max_iter):
                # Assign points to nearest centroid
                distances = np.sqrt(((data - centroids[:, np.newaxis]) ** 2).sum(axis=2))
                assignments = np.argmin(distances, axis=0)

                # Update centroids
                new_centroids = np.array([data[assignments == i].mean(axis=0) for i in range(k)])
                new_centroids = np.nan_to_num(new_centroids, nan=0.0)

                # Check convergence
                if np.allclose(centroids, new_centroids):
                    break

                centroids = new_centroids

            # Calculate inertia
            inertia = np.sum([np.sum((data[assignments == i] - centroids[i]) ** 2) for i in range(k)])

            return centroids, assignments, inertia

        centroids, assignments, inertia = simple_kmeans(X, n_clusters)

        return {
            "assignments": assignments.tolist(),
            "centroids": centroids.tolist(),
            "inertia": float(inertia),
        }

    def compare_signatures(
        self,
        sig1: np.ndarray,
        sig2: np.ndarray,
        method: str = "cosine",
    ) -> float:
        """Compare two trajectory signatures.

        Args:
            sig1: First signature
            sig2: Second signature
            method: Comparison method ("cosine", "euclidean", "correlation")

        Returns:
            Similarity score (0-1)
        """
        # Ensure same length
        max_len = max(len(sig1), len(sig2))
        if len(sig1) < max_len:
            sig1 = np.pad(sig1, (0, max_len - len(sig1)))
        if len(sig2) < max_len:
            sig2 = np.pad(sig2, (0, max_len - len(sig2)))

        if method == "cosine":
            dot = np.dot(sig1, sig2)
            norm1 = np.linalg.norm(sig1)
            norm2 = np.linalg.norm(sig2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return float(dot / (norm1 * norm2))

        elif method == "euclidean":
            dist = np.linalg.norm(sig1 - sig2)
            max_dist = np.sqrt(len(sig1))  # Maximum possible distance
            return float(1.0 - min(dist / max_dist, 1.0))

        elif method == "correlation":
            if len(sig1) < 2:
                return 0.0

            corr = np.corrcoef(sig1, sig2)[0, 1]
            return float(abs(corr) if not np.isnan(corr) else 0.0)

        else:
            raise ValueError(f"Unknown comparison method: {method}")


class VectorDatabase:
    """Simple in-memory database for storing and searching cognitive vectors."""

    def __init__(self, vector_size: int = 32):
        """Initialize the vector database.

        Args:
            vector_size: Size of vectors to store
        """
        self.vector_size = vector_size
        self.vectors: dict[str, np.ndarray] = {}
        self.metadata: dict[str, dict[str, Any]] = {}
        self._vectorizer = CognitiveVectorizer(VectorizationConfig(vector_size=vector_size))

    def store(self, key: str, units: list[CognitiveUnit], metadata: dict[str, Any] | None = None) -> None:
        """Store a vectorized trajectory.

        Args:
            key: Unique key for the trajectory
            units: List of cognitive units
            metadata: Optional metadata to store
        """
        cv = self._vectorizer.vectorize_behavior(units)
        vector = cv.centroid()

        self.vectors[key] = vector
        self.metadata[key] = metadata or {}

    def search(
        self,
        query_units: list[CognitiveUnit],
        top_k: int = 5,
        method: str = "cosine",
    ) -> list[tuple[str, float, dict[str, Any]]]:
        """Search for similar trajectories.

        Args:
            query_units: Query trajectory
            top_k: Number of results to return
            method: Comparison method

        Returns:
            List of (key, similarity, metadata) tuples
        """
        if not self.vectors:
            return []

        # Vectorize query
        query_cv = self._vectorizer.vectorize_behavior(query_units)
        query_vector = query_cv.centroid()

        # Calculate similarities
        results = []
        for key, vector in self.vectors.items():
            similarity = self._vectorizer.compare_signatures(
                query_vector,
                vector,
                method=method,
            )
            results.append((key, similarity, self.metadata[key].copy()))

        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:top_k]

    def delete(self, key: str) -> bool:
        """Delete a vector from the database.

        Args:
            key: Key to delete

        Returns:
            True if deleted, False if not found
        """
        if key in self.vectors:
            del self.vectors[key]
            del self.metadata[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all vectors from the database."""
        self.vectors.clear()
        self.metadata.clear()

    def size(self) -> int:
        """Get the number of vectors in the database.

        Returns:
            Number of vectors
        """
        return len(self.vectors)
