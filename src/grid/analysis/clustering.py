"""DBSCAN clustering service for pattern analysis."""

from __future__ import annotations

from typing import Any

import numpy as np


class ClusteringService:
    """Clustering service using DBSCAN for pattern grouping."""

    def perform_dbscan(
        self,
        data: list[dict[str, Any]],
        eps: float | None = 0.5,
        min_samples: int = 2,
    ) -> dict[str, int]:
        """Run DBSCAN clustering on data points.

        Args:
            data: List of dicts with numeric feature values.
            eps: Maximum distance between two samples. If None, auto-select.
            min_samples: Minimum number of samples in a neighborhood for a core point.

        Returns:
            Dict with 'clusters' (number of clusters) and 'noise' (number of noise points).
        """
        if not data:
            return {"clusters": 0, "noise": 0}

        # Extract feature matrix from dicts
        all_keys = sorted({k for d in data for k in d if isinstance(d[k], (int, float))})
        if not all_keys:
            return {"clusters": 0, "noise": len(data)}

        matrix = np.array([[d.get(k, 0.0) for k in all_keys] for d in data])

        if eps is None:
            eps = self._auto_eps(matrix)

        # DBSCAN implementation
        n = len(matrix)
        labels = [-1] * n  # -1 = unvisited/noise
        cluster_id = 0

        for i in range(n):
            if labels[i] != -1:
                continue

            neighbors = self._region_query(matrix, i, eps)
            if len(neighbors) < min_samples:
                # Noise point (stays -1)
                continue

            # Expand cluster
            labels[i] = cluster_id
            seed_set = list(neighbors)
            seed_set.remove(i)

            j = 0
            while j < len(seed_set):
                q = seed_set[j]
                if labels[q] == -1:
                    labels[q] = cluster_id
                    q_neighbors = self._region_query(matrix, q, eps)
                    if len(q_neighbors) >= min_samples:
                        for nb in q_neighbors:
                            if nb not in seed_set:
                                seed_set.append(nb)
                elif labels[q] == -1:
                    labels[q] = cluster_id
                j += 1

            cluster_id += 1

        noise_count = labels.count(-1)
        num_clusters = cluster_id

        return {"clusters": num_clusters, "noise": noise_count}

    @staticmethod
    def _region_query(matrix: np.ndarray, point_idx: int, eps: float) -> list[int]:
        """Find all points within eps distance of point_idx."""
        distances = np.sqrt(np.sum((matrix - matrix[point_idx]) ** 2, axis=1))
        return [i for i, d in enumerate(distances) if d <= eps]

    @staticmethod
    def _auto_eps(matrix: np.ndarray) -> float:
        """Auto-select eps using k-distance heuristic."""
        from itertools import combinations

        n = len(matrix)
        if n < 2:
            return 0.5

        # Compute pairwise distances and use median as eps
        dists: list[float] = []
        for i, j in combinations(range(min(n, 50)), 2):
            d = float(np.sqrt(np.sum((matrix[i] - matrix[j]) ** 2)))
            dists.append(d)

        if not dists:
            return 0.5

        dists.sort()
        # Use a value around the 10th percentile for tight clusters
        idx = max(0, len(dists) // 10)
        return dists[idx] * 1.5 if dists[idx] > 0 else 0.5
