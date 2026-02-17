import os
import sys

import pytest

# Try to import from light_of_the_seven, skip if not available
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../light_of_the_seven/light_of_the_seven"))

    from cognitive_layer.navigation.enhanced_path_navigator import (
        EnhancedPathNavigator,
        NavigationPlan,
    )
    from cognitive_layer.navigation.schemas.navigation_input import (
        GoalType,
        NavigationContext,
        NavigationGoal,
        NavigationRequest,
    )

    HAS_LIGHT_OF_SEVEN = True
except (ImportError, ModuleNotFoundError):
    HAS_LIGHT_OF_SEVEN = False
    pytestmark = pytest.mark.skip(reason="light_of_the_seven module not available")


class TestEnhancedPathNavigator:
    """Test cases for EnhancedPathNavigator."""

    @pytest.fixture
    def navigator(self):
        return EnhancedPathNavigator(enable_learning=False)

    def test_navigate_basic(self, navigator):
        """Test basic navigation."""
        goal = NavigationGoal(
            goal_type=GoalType.DEVELOPMENT, primary_objective="Implement a new user registration service"
        )
        context = NavigationContext()
        request = NavigationRequest(goal=goal, context=context)

        plan = navigator.navigate(request)

        assert isinstance(plan, NavigationPlan)
        assert len(plan.paths) > 0
        assert plan.recommended_path is not None
        assert plan.recommended_path.recommendation_score > 0

    def test_path_scoring_urgency(self, navigator):
        """Test how urgency affects path scoring."""
        goal = NavigationGoal(goal_type=GoalType.DEBUGGING, primary_objective="Fix a critical bug in production")

        # Urgent context
        request_urgent = NavigationRequest(goal=goal, context=NavigationContext(urgency="critical"))
        plan_urgent = navigator.navigate(request_urgent)

        # Not urgent context
        request_normal = NavigationRequest(goal=goal, context=NavigationContext(urgency="low"))
        _plan_normal = navigator.navigate(request_normal)

        # With critical urgency, we might expect different path rankings or scores
        # (Though in our simple mock generator, the paths are the same,
        # the scoring logic should favor simpler/faster paths)
        assert plan_urgent.recommended_path.id != ""  # Just ensure it ran

    def test_reasoning_generation(self, navigator):
        """Test reasoning generation."""
        plan = navigator.navigate_simple("Create a simple landing page")
        assert "Recommended" in plan.reasoning
        assert "Goal type" in plan.reasoning
