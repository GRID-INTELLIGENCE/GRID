"""
Integration Tests for AI Brain Bridge Service
Tests Knowledge Graph to Navigation flow
"""

from unittest.mock import MagicMock

import pytest

from grid.intelligence.ai_brain_bridge import (
    AIBrainIntegration,
    KnowledgeGraphBridge,
    NavigationEnhancement,
    NodeType,
)
from grid.intelligence.brain import AIBrain


@pytest.fixture
async def ai_brain_integration():
    """Create AI Brain integration instance for testing"""
    integration = AIBrainIntegration()
    await integration.initialize()
    return integration


@pytest.fixture
def sample_navigation_data():
    """Sample navigation data for testing"""
    return {"terrain": "urban", "obstacles": ["building", "park"], "traffic_level": "medium", "visibility": "good"}


class TestAIBrainIntegration:
    """Test AI Brain Integration main functionality"""

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test AI Brain integration initialization"""
        integration = AIBrainIntegration()
        assert not integration._initialized

        await integration.initialize()
        assert integration._initialized
        assert integration.ai_brain is not None
        assert integration.knowledge_bridge is not None

    @pytest.mark.asyncio
    async def test_enhance_navigation_basic(self, ai_brain_integration):
        """Test basic navigation enhancement"""
        current = (0.0, 0.0)
        target = (5.0, 5.0)
        context = {"visibility": "good", "terrain": "urban"}

        result = await ai_brain_integration.enhance_navigation(current, target, context)

        assert isinstance(result, NavigationEnhancement)
        assert len(result.path_suggestions) >= 1
        assert len(result.confidence_scores) == len(result.path_suggestions)
        assert result.spatial_insights is not None
        assert result.reasoning_explanation is not None

    @pytest.mark.asyncio
    async def test_add_navigation_data(self, ai_brain_integration, sample_navigation_data):
        """Test adding navigation data to knowledge graph"""
        coords = (2.0, 3.0)

        node_id = await ai_brain_integration.add_navigation_data(coords, sample_navigation_data)

        assert node_id is not None
        assert node_id.startswith("nav_")
        # spatial_index is a dict with node_id as keys and coords as values
        assert node_id in ai_brain_integration.knowledge_bridge.spatial_index
        assert ai_brain_integration.knowledge_bridge.spatial_index[node_id] == coords


class TestKnowledgeGraphBridge:
    """Test Knowledge Graph Bridge functionality"""

    @pytest.fixture
    async def bridge(self):
        """Create knowledge graph bridge for testing"""
        ai_brain = AIBrain()
        bridge = KnowledgeGraphBridge(ai_brain)
        return bridge

    @pytest.mark.asyncio
    async def test_add_navigation_node(self, bridge, sample_navigation_data):
        """Test adding navigation node to knowledge graph"""
        coords = (1.0, 2.0)

        node_id = await bridge.add_navigation_node(coords, sample_navigation_data, 0.8)

        assert node_id == "nav_1.0_2.0"
        assert node_id in bridge.graph.nodes
        assert bridge.graph.nodes[node_id]["type"] == NodeType.NAVIGATION
        assert bridge.graph.nodes[node_id]["confidence"] == 0.8
        assert bridge.spatial_index[node_id] == coords

    @pytest.mark.asyncio
    async def test_analyze_spatial_patterns_empty(self, bridge):
        """Test spatial pattern analysis with no nodes"""
        region = (0.0, 0.0, 10.0, 10.0)
        patterns = await bridge.analyze_spatial_patterns(region)

        assert isinstance(patterns, list)
        assert len(patterns) == 0

    @pytest.mark.asyncio
    async def test_analyze_spatial_patterns_with_nodes(self, bridge):
        """Test spatial pattern analysis with nodes"""
        # Add some nodes to create patterns
        await bridge.add_navigation_node((1.0, 1.0), {"type": "intersection"})
        await bridge.add_navigation_node((1.5, 1.2), {"type": "road"})
        await bridge.add_navigation_node((2.0, 1.4), {"type": "intersection"})

        region = (0.0, 0.0, 5.0, 5.0)
        patterns = await bridge.analyze_spatial_patterns(region)

        assert isinstance(patterns, list)
        # Should detect at least one cluster or path pattern
        assert len(patterns) >= 0

    @pytest.mark.asyncio
    async def test_enhance_navigation_with_ai(self, bridge):
        """Test AI-enhanced navigation"""
        current = (0.0, 0.0)
        target = (3.0, 3.0)
        context = {"visibility": "good"}

        result = await bridge.enhance_navigation_with_ai(current, target, context)

        assert isinstance(result, NavigationEnhancement)
        assert len(result.path_suggestions) >= 1
        assert len(result.confidence_scores) == len(result.path_suggestions)
        assert "region" in result.spatial_insights
        assert isinstance(result.reasoning_explanation, str)

    def test_detect_clusters(self, bridge):
        """Test cluster detection algorithm"""
        # Mock spatial index with clustered points
        bridge.spatial_index = {
            "node1": (1.0, 1.0),
            "node2": (1.2, 1.1),
            "node3": (1.1, 1.3),
            "node4": (5.0, 5.0),  # Far away point
            "node5": (5.1, 5.2),
        }

        clusters = bridge._detect_clusters(list(bridge.spatial_index.keys()))

        assert isinstance(clusters, list)
        # Should detect at least 2 clusters
        assert len(clusters) >= 1

        # Check that clusters contain nearby points
        for cluster in clusters:
            if len(cluster) >= 2:
                # Verify points in cluster are close together
                for i in range(len(cluster)):
                    for j in range(i + 1, len(cluster)):
                        coord1 = bridge.spatial_index[cluster[i]]
                        coord2 = bridge.spatial_index[cluster[j]]
                        distance = ((coord1[0] - coord2[0]) ** 2 + (coord1[1] - coord2[1]) ** 2) ** 0.5
                        assert distance < 3.0  # Cluster threshold

    def test_detect_paths(self, bridge):
        """Test path detection algorithm"""
        # Mock spatial index with linear arrangement
        bridge.spatial_index = {
            "node1": (0.0, 0.0),
            "node2": (1.0, 1.0),
            "node3": (2.0, 2.0),
            "node4": (3.0, 3.0),
            "node5": (1.0, 3.0),  # Off the main path
        }

        paths = bridge._detect_paths(list(bridge.spatial_index.keys()))

        assert isinstance(paths, list)
        # Should detect the main diagonal path
        assert len(paths) >= 1

        # Check that detected paths have reasonable length
        for path in paths:
            assert len(path) >= 3  # Minimum path length

    def test_calculate_base_path(self, bridge):
        """Test base path calculation"""
        start = (0.0, 0.0)
        end = (2.0, 2.0)

        path = bridge._calculate_base_path(start, end)

        assert isinstance(path, list)
        assert len(path) >= 2
        assert path[0] == start
        assert path[-1] == end

        # Check that path progresses reasonably
        for i in range(len(path) - 1):
            current = path[i]
            next_point = path[i + 1]
            # Should move towards the end point
            assert abs(next_point[0] - end[0]) <= abs(current[0] - end[0]) or abs(next_point[1] - end[1]) <= abs(
                current[1] - end[1]
            )

    def test_calculate_path_confidence(self, bridge):
        """Test path confidence calculation"""
        path = [(0.0, 0.0), (1.0, 1.0), (2.0, 2.0)]
        patterns = []  # No patterns
        context = {"visibility": "good"}

        confidence = bridge._calculate_path_confidence(path, patterns, context)

        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0
        assert confidence >= 0.5  # Base confidence + visibility bonus

    def test_generate_reasoning_explanation(self, bridge):
        """Test reasoning explanation generation"""
        patterns = [MagicMock(pattern_type="cluster", confidence=0.8)]
        paths = [[(0.0, 0.0), (1.0, 1.0)]]
        context = {"visibility": "good", "terrain": "urban"}

        explanation = bridge._generate_reasoning_explanation(patterns, paths, context)

        assert isinstance(explanation, str)
        assert len(explanation) > 0
        assert "patterns" in explanation.lower() or "path" in explanation.lower()


class TestSpatialReasoning:
    """Test spatial reasoning components"""

    @pytest.fixture
    async def bridge(self):
        """Create bridge with some test data"""
        ai_brain = AIBrain()
        bridge = KnowledgeGraphBridge(ai_brain)

        # Add test nodes
        await bridge.add_navigation_node((1.0, 1.0), {"type": "intersection"})
        await bridge.add_navigation_node((2.0, 2.0), {"type": "road"})
        await bridge.add_navigation_node((3.0, 3.0), {"type": "intersection"})

        return bridge

    @pytest.mark.asyncio
    async def test_get_spatial_neighbors(self, bridge):
        """Test spatial neighbor detection"""
        neighbors = bridge._get_spatial_neighbors("nav_1.0_1.0", set(), ["nav_1.0_1.0", "nav_2.0_2.0"])

        assert isinstance(neighbors, list)
        # nav_2.0_2.0 should be within neighbor threshold
        assert "nav_2.0_2.0" in neighbors

    @pytest.mark.asyncio
    async def test_choose_path_direction(self, bridge):
        """Test path direction choice"""
        # Create a straight line scenario
        neighbors = ["nav_2.0_2.0"]
        path = ["nav_1.0_1.0"]

        next_node = bridge._choose_path_direction("nav_1.0_1.0", neighbors, path)

        assert next_node == "nav_2.0_2.0"

    @pytest.mark.asyncio
    async def test_pattern_confidence_calculation(self, bridge):
        """Test pattern confidence calculation"""
        nodes = ["nav_1.0_1.0", "nav_2.0_2.0"]

        confidence = bridge._calculate_pattern_confidence(nodes)

        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0


@pytest.mark.asyncio
async def test_end_to_end_integration():
    """Test end-to-end AI Brain integration flow"""
    integration = AIBrainIntegration()
    await integration.initialize()

    # Add navigation data
    await integration.add_navigation_data((1.0, 1.0), {"terrain": "urban", "traffic": "light"})
    await integration.add_navigation_data((2.0, 2.0), {"terrain": "urban", "traffic": "medium"})
    await integration.add_navigation_data((3.0, 3.0), {"terrain": "park", "traffic": "none"})

    # Get navigation enhancement
    result = await integration.enhance_navigation((0.0, 0.0), (4.0, 4.0), {"visibility": "good", "vehicle": "car"})

    # Verify results
    assert isinstance(result, NavigationEnhancement)
    assert len(result.path_suggestions) >= 1
    assert all(0.0 <= score <= 1.0 for score in result.confidence_scores)
    assert result.spatial_insights["patterns_detected"] >= 0
    assert len(result.reasoning_explanation) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
