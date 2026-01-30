"""
Tests for Path Optimization Agent.

Tests the PathOptimizationAgent for the GRID Navigation Agent System,
including adaptive scoring, learning, and path optimization.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

# Try to import from light_of_the_seven, skip if not available
try:
    from light_of_the_seven.cognitive_layer.navigation.agents.base_agent import (
        AgentConfig,
        AgentState,
    )
    from light_of_the_seven.cognitive_layer.navigation.agents.path_optimization_agent import (
        LearningSnapshot,
        OptimizationResult,
        PathLearningData,
        PathOptimizationAgent,
        PathScore,
    )
    from light_of_the_seven.cognitive_layer.navigation.schemas.navigation_input import (
        ComplexityLevel,
        GoalType,
        NavigationContext,
        NavigationGoal,
        NavigationRequest,
        UrgencyLevel,
    )

    HAS_LIGHT_OF_SEVEN = True
except (ImportError, ModuleNotFoundError):
    HAS_LIGHT_OF_SEVEN = False
    pytestmark = pytest.mark.skip(reason="light_of_the_seven module not available")


class TestPathLearningData:
    """Tests for PathLearningData dataclass."""

    def test_default_values(self) -> None:
        """Test default values for path learning data."""
        data = PathLearningData(path_id="path-direct")

        assert data.path_id == "path-direct"
        assert data.total_selections == 0
        assert data.successful_selections == 0
        assert data.total_time_ms == 0.0
        assert data.user_ratings == []
        assert data.last_selected is None

    def test_success_rate_empty(self) -> None:
        """Test success rate with no selections."""
        data = PathLearningData(path_id="path-direct")

        assert data.success_rate == 0.5  # Default neutral

    def test_success_rate_calculation(self) -> None:
        """Test success rate calculation."""
        data = PathLearningData(
            path_id="path-direct",
            total_selections=10,
            successful_selections=8,
        )

        assert data.success_rate == 0.8

    def test_average_rating_empty(self) -> None:
        """Test average rating with no ratings."""
        data = PathLearningData(path_id="path-direct")

        assert data.average_rating == 3.0  # Default neutral

    def test_average_rating_calculation(self) -> None:
        """Test average rating calculation."""
        data = PathLearningData(
            path_id="path-direct",
            user_ratings=[5, 4, 5, 4, 5],
        )

        assert data.average_rating == 4.6

    def test_average_time_calculation(self) -> None:
        """Test average execution time calculation."""
        data = PathLearningData(
            path_id="path-direct",
            total_selections=5,
            total_time_ms=5000.0,
        )

        assert data.average_time_ms == 1000.0


class TestLearningSnapshot:
    """Tests for LearningSnapshot dataclass."""

    def test_to_dict(self) -> None:
        """Test converting snapshot to dictionary."""
        path_data = {"path-direct": PathLearningData(path_id="path-direct")}
        snapshot = LearningSnapshot(
            path_data=path_data,
            goal_type_weights={"development": 1.0},
            context_patterns={"hash123": {"path-direct": 0.5}},
            total_samples=100,
            learning_epoch=5,
            last_updated=datetime.now(),
            accuracy_history=[0.8, 0.85, 0.9],
        )

        result = snapshot.to_dict()

        assert "path_data" in result
        assert "goal_type_weights" in result
        assert result["total_samples"] == 100
        assert result["learning_epoch"] == 5

    def test_from_dict(self) -> None:
        """Test creating snapshot from dictionary."""
        data = {
            "path_data": {
                "path-direct": {
                    "path_id": "path-direct",
                    "total_selections": 10,
                    "successful_selections": 8,
                    "total_time_ms": 5000.0,
                    "user_ratings": [4, 5],
                    "goal_type_counts": {"development": 5},
                }
            },
            "goal_type_weights": {"development": 1.1},
            "context_patterns": {},
            "total_samples": 50,
            "learning_epoch": 2,
            "last_updated": datetime.now().isoformat(),
            "accuracy_history": [0.7, 0.75],
        }

        snapshot = LearningSnapshot.from_dict(data)

        assert snapshot.total_samples == 50
        assert snapshot.learning_epoch == 2
        assert "path-direct" in snapshot.path_data


class TestPathOptimizationAgent:
    """Tests for PathOptimizationAgent."""

    @pytest.fixture
    def agent(self) -> PathOptimizationAgent:
        """Create a test agent."""
        config = AgentConfig(
            name="TestPathOptimizer",
            enable_learning=True,
            learning_rate=0.1,
        )
        return PathOptimizationAgent(config=config)

    @pytest.fixture
    def sample_request(self) -> NavigationRequest:
        """Create a sample navigation request."""
        goal = NavigationGoal(
            goal_type=GoalType.DEVELOPMENT,
            primary_objective="Create a new API endpoint for user authentication",
            success_criteria=["JWT works", "Tests pass"],
        )
        context = NavigationContext(
            urgency=UrgencyLevel.NORMAL,
            complexity=ComplexityLevel.MODERATE,
        )
        return NavigationRequest(
            goal=goal,
            context=context,
            request_id="test-req-001",
        )

    def test_agent_initialization(self, agent: PathOptimizationAgent) -> None:
        """Test agent initializes correctly."""
        assert agent.name == "TestPathOptimizer"
        assert agent.config.enable_learning is True
        assert agent.config.learning_rate == 0.1
        assert agent.state == AgentState.CREATED

    def test_agent_default_config(self) -> None:
        """Test agent with default config."""
        agent = PathOptimizationAgent()

        assert agent.name == "PathOptimizationAgent"
        assert agent.config.enable_learning is True

    @pytest.mark.asyncio
    async def test_agent_start(self, agent: PathOptimizationAgent) -> None:
        """Test agent starts correctly."""
        await agent.start()

        assert agent.state == AgentState.RUNNING
        assert agent.is_running is True

    @pytest.mark.asyncio
    async def test_agent_stop(self, agent: PathOptimizationAgent) -> None:
        """Test agent stops correctly."""
        await agent.start()
        await agent.stop()

        assert agent.state == AgentState.STOPPED
        assert agent.is_running is False

    @pytest.mark.asyncio
    async def test_process_returns_optimization_result(
        self,
        agent: PathOptimizationAgent,
        sample_request: NavigationRequest,
    ) -> None:
        """Test processing returns optimization result."""
        await agent.start()

        result = await agent.process(sample_request)

        assert isinstance(result, OptimizationResult)
        assert result.recommended_path_id is not None
        assert len(result.path_scores) > 0
        assert result.processing_time_ms > 0

    @pytest.mark.asyncio
    async def test_process_scores_multiple_paths(
        self,
        agent: PathOptimizationAgent,
        sample_request: NavigationRequest,
    ) -> None:
        """Test that multiple paths are scored."""
        await agent.start()

        result = await agent.process(sample_request)

        # Should have multiple path scores
        assert len(result.path_scores) >= 2

        # All scores should be PathScore objects
        for score in result.path_scores:
            assert isinstance(score, PathScore)
            assert 0.0 <= score.final_score <= 1.0

    @pytest.mark.asyncio
    async def test_process_selects_best_path(
        self,
        agent: PathOptimizationAgent,
        sample_request: NavigationRequest,
    ) -> None:
        """Test that the best scoring path is recommended."""
        await agent.start()

        result = await agent.process(sample_request)

        # Recommended should be the highest scoring
        if result.path_scores:
            best_score = max(s.final_score for s in result.path_scores)
            recommended = next(s for s in result.path_scores if s.path_id == result.recommended_path_id)
            assert recommended.final_score == best_score

    @pytest.mark.asyncio
    async def test_process_includes_confidence(
        self,
        agent: PathOptimizationAgent,
        sample_request: NavigationRequest,
    ) -> None:
        """Test that confidence is included in result."""
        await agent.start()

        result = await agent.process(sample_request)

        assert 0.0 <= result.confidence <= 1.0

    def test_learn_from_outcome(self, agent: PathOptimizationAgent) -> None:
        """Test learning from an outcome."""
        outcome = {
            "request_id": "test-req-001",
            "success": True,
            "selected_path_id": "path-direct",
            "execution_time_ms": 1500.0,
            "user_rating": 5,
        }

        agent.learn(outcome)

        # Check that path data was updated
        assert "path-direct" in agent._path_data
        assert agent._path_data["path-direct"].total_selections == 1
        assert agent._path_data["path-direct"].successful_selections == 1

    def test_learn_updates_success_rate(self, agent: PathOptimizationAgent) -> None:
        """Test that learning updates success rate."""
        # Learn from multiple outcomes
        agent.learn(
            {
                "request_id": "req-1",
                "success": True,
                "selected_path_id": "path-direct",
                "execution_time_ms": 1000.0,
            }
        )
        agent.learn(
            {
                "request_id": "req-2",
                "success": True,
                "selected_path_id": "path-direct",
                "execution_time_ms": 1200.0,
            }
        )
        agent.learn(
            {
                "request_id": "req-3",
                "success": False,
                "selected_path_id": "path-direct",
                "execution_time_ms": 2000.0,
            }
        )

        path_data = agent._path_data["path-direct"]
        assert path_data.total_selections == 3
        assert path_data.successful_selections == 2
        # Success rate should be 2/3 ≈ 0.667
        assert 0.6 <= path_data.success_rate <= 0.7

    def test_learn_updates_user_ratings(self, agent: PathOptimizationAgent) -> None:
        """Test that learning updates user ratings."""
        agent.learn(
            {
                "request_id": "req-1",
                "success": True,
                "selected_path_id": "path-direct",
                "execution_time_ms": 1000.0,
                "user_rating": 5,
            }
        )
        agent.learn(
            {
                "request_id": "req-2",
                "success": True,
                "selected_path_id": "path-direct",
                "execution_time_ms": 1000.0,
                "user_rating": 4,
            }
        )

        path_data = agent._path_data["path-direct"]
        assert len(path_data.user_ratings) == 2
        assert path_data.average_rating == 4.5

    def test_learn_disabled_when_learning_off(self) -> None:
        """Test that learning is skipped when disabled."""
        config = AgentConfig(enable_learning=False)
        agent = PathOptimizationAgent(config=config)

        agent.learn(
            {
                "request_id": "req-1",
                "success": True,
                "selected_path_id": "path-direct",
                "execution_time_ms": 1000.0,
            }
        )

        # Should not have recorded anything
        assert "path-direct" not in agent._path_data

    def test_record_choice(self, agent: PathOptimizationAgent) -> None:
        """Test recording a user's path choice."""
        # First, simulate a pending outcome
        agent._pending_outcomes["test-req-001"] = {
            "recommended_path_id": "path-direct",
            "context_hash": "abc123",
            "goal_type": GoalType.DEVELOPMENT,
            "timestamp": datetime.now(),
        }

        # User overrides the recommendation
        agent.record_choice(
            request_id="test-req-001",
            selected_path_id="path-incremental",
            user_override=True,
        )

        # The selected path should have been boosted
        assert "path-incremental" in agent._path_data

    def test_adapt_path_scoring(self, agent: PathOptimizationAgent) -> None:
        """Test manual path scoring adjustment."""
        initial_weight = agent._goal_type_weights.get(GoalType.DEVELOPMENT, 1.0)

        agent.adapt_path_scoring(
            goal_type=GoalType.DEVELOPMENT,
            path_id="path-direct",
            adjustment=0.2,
        )

        new_weight = agent._goal_type_weights[GoalType.DEVELOPMENT]
        assert new_weight != initial_weight

    def test_get_accuracy_stats(self, agent: PathOptimizationAgent) -> None:
        """Test getting accuracy statistics."""
        stats = agent.get_accuracy_stats()

        assert "current_accuracy" in stats
        assert "target_accuracy" in stats
        assert "total_samples" in stats
        assert "learning_rate" in stats
        assert stats["target_accuracy"] == 0.95

    def test_get_path_stats(self, agent: PathOptimizationAgent) -> None:
        """Test getting path statistics."""
        # Add some learning data
        agent.learn(
            {
                "request_id": "req-1",
                "success": True,
                "selected_path_id": "path-direct",
                "execution_time_ms": 1000.0,
            }
        )

        stats = agent.get_path_stats()

        assert "path-direct" in stats
        assert "total_selections" in stats["path-direct"]
        assert "success_rate" in stats["path-direct"]

    @pytest.mark.asyncio
    async def test_context_hash_generation(
        self,
        agent: PathOptimizationAgent,
        sample_request: NavigationRequest,
    ) -> None:
        """Test that context hash is generated consistently."""
        await agent.start()

        result1 = await agent.process(sample_request)
        result2 = await agent.process(sample_request)

        # Same request should produce same context hash
        assert result1.metadata["context_hash"] == result2.metadata["context_hash"]

    @pytest.mark.asyncio
    async def test_learning_applied_flag(
        self,
        agent: PathOptimizationAgent,
        sample_request: NavigationRequest,
    ) -> None:
        """Test learning_applied flag in results."""
        await agent.start()

        # First request - no prior learning
        result1 = await agent.process(sample_request)

        # Learn from an outcome
        agent.learn(
            {
                "request_id": sample_request.request_id,
                "success": True,
                "selected_path_id": result1.recommended_path_id,
                "execution_time_ms": 1000.0,
            }
        )

        # Second request - with prior learning
        sample_request.request_id = "test-req-002"
        result2 = await agent.process(sample_request)

        # Should show learning was applied
        assert result2.learning_applied is True

    @pytest.mark.asyncio
    async def test_urgency_affects_scoring(
        self,
        agent: PathOptimizationAgent,
    ) -> None:
        """Test that urgency level affects path scoring."""
        await agent.start()

        # Normal urgency
        normal_request = NavigationRequest(
            goal=NavigationGoal(
                goal_type=GoalType.DEVELOPMENT,
                primary_objective="Create a new feature module",
            ),
            context=NavigationContext(urgency=UrgencyLevel.NORMAL),
        )

        # Critical urgency
        critical_request = NavigationRequest(
            goal=NavigationGoal(
                goal_type=GoalType.DEVELOPMENT,
                primary_objective="Create a new feature module",
            ),
            context=NavigationContext(urgency=UrgencyLevel.CRITICAL),
        )

        normal_result = await agent.process(normal_request)
        critical_result = await agent.process(critical_request)

        # Direct path should score higher for critical urgency
        normal_direct = next((s for s in normal_result.path_scores if s.path_id == "path-direct"), None)
        critical_direct = next((s for s in critical_result.path_scores if s.path_id == "path-direct"), None)

        if normal_direct and critical_direct:
            # Critical should boost direct path more
            assert critical_direct.context_adjustment >= normal_direct.context_adjustment

    @pytest.mark.asyncio
    async def test_complexity_affects_scoring(
        self,
        agent: PathOptimizationAgent,
    ) -> None:
        """Test that complexity level affects path scoring."""
        await agent.start()

        # Simple complexity
        simple_request = NavigationRequest(
            goal=NavigationGoal(
                goal_type=GoalType.DEVELOPMENT,
                primary_objective="Create a simple configuration file",
            ),
            context=NavigationContext(complexity=ComplexityLevel.SIMPLE),
        )

        # Very complex
        complex_request = NavigationRequest(
            goal=NavigationGoal(
                goal_type=GoalType.DEVELOPMENT,
                primary_objective="Create a complex distributed system",
            ),
            context=NavigationContext(complexity=ComplexityLevel.VERY_COMPLEX),
        )

        _simple_result = await agent.process(simple_request)
        complex_result = await agent.process(complex_request)

        # Comprehensive path should score higher for complex tasks
        complex_comprehensive = next((s for s in complex_result.path_scores if s.path_id == "path-comprehensive"), None)

        if complex_comprehensive:
            assert complex_comprehensive.context_adjustment > 0

    @pytest.mark.asyncio
    async def test_metrics_tracking(
        self,
        agent: PathOptimizationAgent,
        sample_request: NavigationRequest,
    ) -> None:
        """Test that metrics are tracked correctly."""
        await agent.start()

        initial_requests = agent.metrics.total_requests

        await agent.execute(sample_request)

        assert agent.metrics.total_requests > initial_requests

    @pytest.mark.asyncio
    async def test_execute_requires_running_state(
        self,
        agent: PathOptimizationAgent,
        sample_request: NavigationRequest,
    ) -> None:
        """Test that execute requires agent to be running."""
        # Agent not started
        with pytest.raises(RuntimeError, match="not running"):
            await agent.execute(sample_request)


class TestPathOptimizationAgentWithStorage:
    """Tests for PathOptimizationAgent with storage backend."""

    @pytest.fixture
    def mock_storage(self) -> MagicMock:
        """Create a mock storage backend."""
        storage = MagicMock()
        storage.load = AsyncMock(return_value=None)
        storage.save = AsyncMock()
        return storage

    @pytest.fixture
    def agent_with_storage(self, mock_storage: MagicMock) -> PathOptimizationAgent:
        """Create agent with mock storage."""
        return PathOptimizationAgent(storage_backend=mock_storage)

    @pytest.mark.asyncio
    async def test_loads_state_on_start(
        self,
        agent_with_storage: PathOptimizationAgent,
        mock_storage: MagicMock,
    ) -> None:
        """Test that state is loaded on start."""
        await agent_with_storage.start()

        mock_storage.load.assert_called_once()

    @pytest.mark.asyncio
    async def test_saves_state_on_stop(
        self,
        agent_with_storage: PathOptimizationAgent,
        mock_storage: MagicMock,
    ) -> None:
        """Test that state is saved on stop."""
        await agent_with_storage.start()
        await agent_with_storage.stop()

        mock_storage.save.assert_called_once()


class TestPathOptimizationAgentAdaptation:
    """Tests for adaptive learning features."""

    @pytest.fixture
    def agent(self) -> PathOptimizationAgent:
        """Create agent with low adaptation threshold."""
        config = AgentConfig(
            enable_learning=True,
            learning_rate=0.1,
            update_threshold=0.5,  # Low threshold for testing
        )
        return PathOptimizationAgent(config=config)

    def test_learning_rate_adjustment(self, agent: PathOptimizationAgent) -> None:
        """Test that learning rate is adjusted based on accuracy."""
        # Simulate many successful predictions
        for _i in range(20):
            agent._recent_predictions.append(("path-direct", True))

        initial_rate = agent.config.learning_rate
        agent._adjust_learning_rate(0.96)  # Above target

        # Learning rate should decrease
        assert agent.config.learning_rate <= initial_rate

    def test_learning_rate_increases_on_poor_performance(
        self,
        agent: PathOptimizationAgent,
    ) -> None:
        """Test that learning rate increases when performing poorly."""
        initial_rate = agent.config.learning_rate

        # Simulate poor performance
        agent._adjust_learning_rate(0.4)

        # Learning rate should increase
        assert agent.config.learning_rate >= initial_rate

    def test_learning_rate_bounds(self, agent: PathOptimizationAgent) -> None:
        """Test that learning rate stays within bounds."""
        # Try to push rate very high
        for _ in range(100):
            agent._adjust_learning_rate(0.1)

        assert agent.config.learning_rate <= PathOptimizationAgent.MAX_LEARNING_RATE

        # Try to push rate very low
        for _ in range(100):
            agent._adjust_learning_rate(0.99)

        assert agent.config.learning_rate >= PathOptimizationAgent.MIN_LEARNING_RATE
