"""
Comprehensive test suite for Navigation & Context Intelligence components.

Tests the core "brain" of GRID's CLI experience including:
- EnhancedPathNavigator: Learning-enabled path optimization
- UserContextManager: User behavior pattern recognition
- NavigationDecision: Context-aware decision making
- Pattern recognition and learning integration
"""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest

# Add necessary imports for navigation components
try:
    from grid.context.schemas import (
        FileAccessPattern,
        TaskPattern,
        ToolUsagePattern,
    )
    from grid.context.user_context_manager import UserContextManager

    HAS_CONTEXT = True
    # Try to import EnhancedPathNavigator from legacy location
    try:
        from archive.light_of_seven_legacy.cognitive_layer.navigation.enhanced_path_navigator import (
            EnhancedPathNavigator,
            NavigationPlan,
            NavigationStep,
        )
        from archive.light_of_seven_legacy.cognitive_layer.navigation.schemas.navigation_input import (
            GoalType,
            NavigationContext,
            NavigationGoal,
            NavigationRequest,
            UrgencyLevel,
        )

        HAS_LEGACY_NAVIGATOR = True
    except ImportError:
        # Fallback to current location if available
        try:
            from grid.navigation.enhanced_navigator import (
                EnhancedPathNavigator,
                NavigationPlan,
                NavigationStep,
            )
            from grid.navigation.schemas.navigation_input import (
                GoalType,
                NavigationContext,
                NavigationGoal,
                NavigationRequest,
                UrgencyLevel,
            )

            HAS_LEGACY_NAVIGATOR = True
        except ImportError:
            HAS_LEGACY_NAVIGATOR = False

except ImportError:
    HAS_CONTEXT = False
    HAS_LEGACY_NAVIGATOR = False


@pytest.mark.skipif(not HAS_CONTEXT, reason="Context components not available")
class TestUserContextManager:
    """Test UserContextManager for user behavior pattern recognition."""

    @pytest.fixture
    def temp_context_dir(self):
        """Create temporary directory for context storage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def context_manager(self, temp_context_dir):
        """Create UserContextManager instance."""
        return UserContextManager(context_root=temp_context_dir, user_id="test_user")

    def test_profile_initialization(self, context_manager):
        """Test that user profile is properly initialized."""
        assert context_manager.profile is not None
        assert context_manager.profile.user_id == "test_user"
        assert context_manager.profile.preferences is not None

    def test_profile_persistence(self, context_manager, temp_context_dir):
        """Test that user profile is properly saved and loaded."""
        # Modify profile
        context_manager.profile.preferences.default_complexity = "medium"
        context_manager.save_profile()

        # Create new manager to test loading
        new_manager = UserContextManager(context_root=temp_context_dir, user_id="test_user")
        assert new_manager.profile.preferences.default_complexity == "medium"

    def test_task_pattern_tracking(self, context_manager):
        """Test task pattern recognition and tracking."""
        # Simulate task completion
        task_pattern = TaskPattern(
            task_type="development",
            tools_used=["git", "pytest"],
            completion_time=datetime.now(),
            success=True,
        )

        context_manager.track_task_pattern(task_pattern)
        assert len(context_manager.profile.work_patterns) > 0
        assert context_manager.profile.work_patterns[0].task_type == "development"

    def test_file_access_patterns(self, context_manager):
        """Test file access pattern recognition."""
        file_pattern = FileAccessPattern(
            file_type=".py",
            access_time=datetime.now(),
            access_frequency=5,
        )

        context_manager.track_file_access(file_pattern)
        assert len(context_manager.profile.file_access_patterns) > 0
        assert context_manager.profile.file_access_patterns[0].file_type == ".py"

    def test_tool_usage_patterns(self, context_manager):
        """Test tool usage pattern recognition."""
        tool_pattern = ToolUsagePattern(
            tool_name="pytest",
            usage_count=10,
            last_used=datetime.now(),
        )

        context_manager.track_tool_usage(tool_pattern)
        assert len(context_manager.profile.tool_usage_patterns) > 0
        assert context_manager.profile.tool_usage_patterns[0].tool_name == "pytest"

    def test_work_pattern_analysis(self, context_manager):
        """Test work pattern analysis and recommendations."""
        # Add multiple patterns
        for _i in range(3):
            task_pattern = TaskPattern(
                task_type="testing",
                tools_used=["pytest", "unittest"],
                completion_time=datetime.now(),
                success=True,
            )
            context_manager.track_task_pattern(task_pattern)

        # Test pattern analysis
        recommendations = context_manager.analyze_work_patterns()
        assert "testing" in recommendations
        assert "pytest" in recommendations["testing"]["recommended_tools"]


@pytest.mark.skipif(not HAS_LEGACY_NAVIGATOR, reason="EnhancedPathNavigator not available")
class TestEnhancedPathNavigator:
    """Test EnhancedPathNavigator for learning-enabled path optimization."""

    @pytest.fixture
    def navigator(self):
        """Create EnhancedPathNavigator instance."""
        return EnhancedPathNavigator(enable_learning=False)

    def test_basic_navigation(self, navigator):
        """Test basic navigation with simple goal."""
        goal = NavigationGoal(goal_type=GoalType.DEVELOPMENT, primary_objective="Implement user authentication service")
        context = NavigationContext()
        request = NavigationRequest(goal=goal, context=context)

        plan = navigator.navigate(request)

        assert isinstance(plan, NavigationPlan)
        assert len(plan.paths) > 0
        assert plan.recommended_path is not None
        assert plan.recommended_path.recommendation_score > 0
        assert len(plan.recommended_path.steps) > 0

    def test_urgency_impact_on_scoring(self, navigator):
        """Test that urgency affects path scoring."""
        goal = NavigationGoal(goal_type=GoalType.DEBUGGING, primary_objective="Fix critical production bug")

        # Test with different urgency levels
        normal_context = NavigationContext(urgency=UrgencyLevel.NORMAL)
        critical_context = NavigationContext(urgency=UrgencyLevel.CRITICAL)

        normal_request = NavigationRequest(goal=goal, context=normal_context)
        critical_request = NavigationRequest(goal=goal, context=critical_context)

        normal_plan = navigator.navigate(normal_request)
        critical_plan = navigator.navigate(critical_request)

        # Critical urgency should have higher scoring paths
        assert critical_plan.recommended_path.recommendation_score >= normal_plan.recommended_path.recommendation_score

    def test_complexity_impact_on_path_generation(self, navigator):
        """Test that complexity affects path generation."""
        goal = NavigationGoal(
            goal_type=GoalType.DEVELOPMENT, primary_objective="Implement complex machine learning pipeline"
        )

        # Test with different complexity levels
        simple_context = NavigationContext(complexity=ComplexityLevel.LOW)
        complex_context = NavigationContext(complexity=ComplexityLevel.HIGH)

        simple_request = NavigationRequest(goal=goal, context=simple_context)
        complex_request = NavigationRequest(goal=goal, context=complex_context)

        simple_plan = navigator.navigate(simple_request)
        complex_plan = navigator.navigate(complex_request)

        # High complexity should generate more detailed paths
        assert len(complex_plan.recommended_path.steps) >= len(simple_plan.recommended_path.steps)

    def test_learning_integration(self, navigator):
        """Test learning integration and adaptive scoring."""
        # Enable learning for this test
        learning_navigator = EnhancedPathNavigator(enable_learning=True)

        goal = NavigationGoal(goal_type=GoalType.DEVELOPMENT, primary_objective="Create REST API endpoint")
        context = NavigationContext()
        request = NavigationRequest(goal=goal, context=context)

        # First navigation
        initial_plan = learning_navigator.navigate(request)
        initial_score = initial_plan.recommended_path.recommendation_score

        # Simulate positive feedback
        outcome = NavigationOutcome(
            path_id=initial_plan.recommended_path.id, success=True, completion_time=120.0, user_feedback=0.9
        )
        learning_navigator.record_outcome(outcome)

        # Second navigation should have improved score
        updated_plan = learning_navigator.navigate(request)
        updated_score = updated_plan.recommended_path.recommendation_score

        assert updated_score >= initial_score

    def test_simple_string_interface(self, navigator):
        """Test backward-compatible simple string interface."""
        plan = navigator.navigate_simple("Create a new database model")

        assert isinstance(plan, NavigationPlan)
        assert len(plan.paths) > 0
        assert "database" in plan.recommended_path.name.lower() or "model" in plan.recommended_path.name.lower()

    def test_path_visualization_integration(self, navigator):
        """Test integration with path visualization."""
        goal = NavigationGoal(goal_type=GoalType.DEVELOPMENT, primary_objective="Implement authentication system")
        context = NavigationContext()
        request = NavigationRequest(goal=goal, context=context)

        plan = navigator.navigate(request)

        # Test visualization data generation
        visualization_data = plan.to_visualization_format()
        assert "nodes" in visualization_data
        assert "edges" in visualization_data
        assert len(visualization_data["nodes"]) > 0
        assert len(visualization_data["edges"]) > 0


class TestNavigationIntegration:
    """Test integration between navigation and context components."""

    @pytest.fixture
    def mock_context_manager(self):
        """Create mock UserContextManager."""
        manager = Mock()
        manager.analyze_work_patterns.return_value = {
            "development": {
                "recommended_tools": ["git", "pytest", "fastapi"],
                "common_patterns": ["api_development", "testing"],
            }
        }
        return manager

    @pytest.fixture
    def mock_navigator(self):
        """Create mock EnhancedPathNavigator."""
        navigator = Mock()
        navigator.navigate.return_value = NavigationPlan(
            paths=[
                Mock(
                    id="path_1",
                    name="API Development Path",
                    recommendation_score=0.95,
                    steps=[
                        NavigationStep(
                            id="step_1",
                            name="Design API",
                            description="Create API specification",
                            estimated_time_seconds=3600,
                        )
                    ],
                )
            ],
            recommended_path=None,
        )
        return navigator

    def test_context_aware_navigation(self, mock_context_manager, mock_navigator):
        """Test navigation that adapts to user context."""
        # Simulate context-aware navigation
        goal = NavigationGoal(goal_type=GoalType.DEVELOPMENT, primary_objective="Create new API endpoint")

        # Use context to inform navigation
        context_patterns = mock_context_manager.analyze_work_patterns()

        # Navigation should use context patterns
        plan = mock_navigator.navigate(
            NavigationRequest(goal=goal, context=NavigationContext(user_context=context_patterns))
        )

        assert plan.recommended_path is not None
        assert "api" in plan.recommended_path.name.lower()
        assert plan.recommended_path.recommendation_score > 0.9

    def test_learning_feedback_loop(self, mock_context_manager, mock_navigator):
        """Test feedback loop between navigation and context learning."""
        # Simulate successful navigation
        outcome = NavigationOutcome(path_id="path_1", success=True, completion_time=1800.0, user_feedback=0.95)

        # Record outcome in both systems
        mock_navigator.record_outcome(outcome)
        mock_context_manager.track_navigation_outcome.assert_called_with(outcome)


class TestNavigationDecision:
    """Test navigation decision making and scoring."""

    def test_decision_matrix_generation(self):
        """Test generation of decision matrices for path selection."""
        from grid.navigation.decision_matrix import DecisionMatrixGenerator

        generator = DecisionMatrixGenerator()
        goal = NavigationGoal(goal_type=GoalType.DEVELOPMENT, primary_objective="Implement user authentication")
        context = NavigationContext()

        decision_matrix = generator.generate_matrix(goal, context)

        assert "criteria" in decision_matrix
        assert "alternatives" in decision_matrix
        assert len(decision_matrix["criteria"]) > 3  # Should have multiple criteria
        assert len(decision_matrix["alternatives"]) > 1  # Should have multiple paths

    def test_adaptive_scoring(self):
        """Test adaptive scoring with learned weights."""
        from grid.navigation.adaptive_scorer import AdaptiveScorer

        scorer = AdaptiveScorer()
        path = Mock(
            id="test_path",
            steps=[NavigationStep(id="step1", name="Design", description="Design phase", estimated_time_seconds=3600)],
        )

        # Test scoring with different contexts
        simple_context = NavigationContext(complexity=ComplexityLevel.LOW)
        complex_context = NavigationContext(complexity=ComplexityLevel.HIGH)

        simple_score = scorer.score_path(path, simple_context)
        complex_score = scorer.score_path(path, complex_context)

        # Complex context should adjust scoring
        assert complex_score != simple_score

    def test_path_selection_optimization(self):
        """Test path selection optimization."""
        from grid.navigation.path_optimizer import PathOptimizer

        optimizer = PathOptimizer()
        paths = [
            Mock(id="path1", recommendation_score=0.8, estimated_time_seconds=7200),
            Mock(id="path2", recommendation_score=0.9, estimated_time_seconds=3600),
            Mock(id="path3", recommendation_score=0.7, estimated_time_seconds=1800),
        ]

        # Test optimization with different constraints
        balanced_selection = optimizer.optimize(paths, constraint="balanced")
        speed_selection = optimizer.optimize(paths, constraint="speed")
        quality_selection = optimizer.optimize(paths, constraint="quality")

        # Should select different paths based on constraints
        assert balanced_selection.id != speed_selection.id
        assert quality_selection.recommendation_score >= speed_selection.recommendation_score
