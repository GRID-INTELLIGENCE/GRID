import pytest

from grid.analysis.clustering import ClusteringService


class TestPatternEngineDBSCAN:
    def test_clustering_performs_dbscan(self):
        service = ClusteringService()
        data = [{"x": i * 0.1} for i in range(20)]  # Dense points

        result = service.perform_dbscan(data, eps=0.5)

        assert result["clusters"] == 1
        assert result["noise"] < len(data)

    def test_clustering_handles_empty_data(self):
        service = ClusteringService()
        result = service.perform_dbscan([])

        assert result["clusters"] == 0
        assert result["noise"] == 0

    def test_clustering_accuracy_issue(self):
        """Reproduce BUG-005: DBSCAN clustering accuracy issues."""
        service = ClusteringService()

        # Dataset with 3 clear clusters in 3D space
        data = [
            # Cluster 1: Points around (1, 1, 1)
            {"x": 1.0, "y": 1.0, "z": 1.0},
            {"x": 1.1, "y": 1.1, "z": 1.1},
            {"x": 0.9, "y": 0.9, "z": 0.9},
            {"x": 1.0, "y": 1.1, "z": 1.0},
            {"x": 1.1, "y": 1.0, "z": 1.1},
            # Cluster 2: Points around (5, 5, 5)
            {"x": 5.0, "y": 5.0, "z": 5.0},
            {"x": 5.1, "y": 5.1, "z": 5.1},
            {"x": 4.9, "y": 4.9, "z": 4.9},
            {"x": 5.0, "y": 5.1, "z": 5.0},
            {"x": 5.1, "y": 5.0, "z": 5.1},
            # Cluster 3: Points around (10, 10, 10)
            {"x": 10.0, "y": 10.0, "z": 10.0},
            {"x": 10.1, "y": 10.1, "z": 10.1},
            {"x": 9.9, "y": 9.9, "z": 9.9},
            {"x": 10.0, "y": 10.1, "z": 10.0},
            {"x": 10.1, "y": 10.0, "z": 10.1},
            # Noise points
            {"x": 3.0, "y": 3.0, "z": 3.0},
            {"x": 7.0, "y": 7.0, "z": 7.0},
        ]

        # Run DBSCAN with a suboptimal eps value to force clustering inaccuracies
        result = service.perform_dbscan(data, eps=1.0, min_samples=5)

        # Expected: 3 clusters, 2 noise points
        # Actual: Likely fewer clusters or more noise due to incorrect eps
        print(f"Clusters: {result['clusters']}, Noise: {result['noise']}")
        assert result["clusters"] == 3, f"Expected 3 clusters, got {result['clusters']}"
        assert result["noise"] == 2, f"Expected 2 noise points, got {result['noise']}"

    def test_clustering_with_dynamic_eps(self):
        """Test DBSCAN with dynamic eps selection to improve accuracy."""
        service = ClusteringService()

        # Dataset with 2 clusters and noise
        data = [
            # Cluster 1: Points around (1, 1)
            {"x": 1.0, "y": 1.0},
            {"x": 1.1, "y": 1.1},
            {"x": 0.9, "y": 0.9},
            {"x": 1.0, "y": 1.1},
            {"x": 1.1, "y": 1.0},
            # Cluster 2: Points around (5, 5)
            {"x": 5.0, "y": 5.0},
            {"x": 5.1, "y": 5.1},
            {"x": 4.9, "y": 4.9},
            {"x": 5.0, "y": 5.1},
            {"x": 5.1, "y": 5.0},
            # Noise points
            {"x": 3.0, "y": 3.0},
            {"x": 7.0, "y": 7.0},
        ]

        # Run DBSCAN with dynamic eps
        result = service.perform_dbscan(data, eps=None, min_samples=5)

        # Expected: 2 clusters, 2 noise points
        print(f"Clusters: {result['clusters']}, Noise: {result['noise']}")
        assert result["clusters"] == 2, f"Expected 2 clusters, got {result['clusters']}"
        assert result["noise"] == 2, f"Expected 2 noise points, got {result['noise']}"

    def test_clustering_output_integrity(self):
        """Regression test for DBSCAN output structure and consistency."""
        service = ClusteringService()
        data = [{"x": 1.0}, {"x": 1.1}, {"x": 5.0}]

        # Fit
        result = service.perform_dbscan(data, eps=0.5, min_samples=2)

        # Validate structure
        assert "clusters" in result
        assert "noise" in result
        assert isinstance(result["clusters"], int)
        assert isinstance(result["noise"], int)

        # Validate logic (1 cluster of 2 points, 1 noise point)
        assert result["clusters"] == 1
        assert result["noise"] == 1
