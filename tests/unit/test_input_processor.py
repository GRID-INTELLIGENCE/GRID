import os
import sys

import pytest

# Try to import from light_of_the_seven, skip if not available
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../light_of_the_seven/light_of_the_seven"))

    from cognitive_layer.navigation.input_processor import (
        InputProcessingError,
        NavigationInputProcessor,
    )
    from cognitive_layer.navigation.schemas.navigation_input import (
        ComplexityLevel,
        GoalType,
        UrgencyLevel,
    )

    HAS_LIGHT_OF_SEVEN = True
except (ImportError, ModuleNotFoundError):
    HAS_LIGHT_OF_SEVEN = False
    pytestmark = pytest.mark.skip(reason="light_of_the_seven module not available")


class TestNavigationInputProcessor:
    """Test cases for NavigationInputProcessor."""

    @pytest.fixture
    def processor(self):
        return NavigationInputProcessor()

    def test_detect_goal_type(self, processor):
        """Test goal type detection from string."""
        assert processor._detect_goal_type("Fix the memory leak") == GoalType.DEBUGGING
        assert processor._detect_goal_type("Implement a new feature") == GoalType.DEVELOPMENT
        assert processor._detect_goal_type("Optimize the database") == GoalType.OPTIMIZATION
        assert processor._detect_goal_type("Analyze the logs") == GoalType.ANALYSIS
        assert processor._detect_goal_type("Connect to the remote API") == GoalType.INTEGRATION

    def test_detect_urgency(self, processor):
        """Test urgency detection from string."""
        assert processor._detect_urgency("URGENT: fix it now") == UrgencyLevel.CRITICAL
        assert processor._detect_urgency("This is a high priority task") == UrgencyLevel.HIGH
        assert processor._detect_urgency("No pressure, do it low priority") == UrgencyLevel.LOW
        assert processor._detect_urgency("Normal task") == UrgencyLevel.NORMAL

    def test_process_string_input(self, processor):
        """Test processing a simple string input."""
        request = processor.process("Implement user authentication with JWT")
        assert request.goal.primary_objective == "Implement user authentication with JWT"
        assert request.goal.goal_type == GoalType.DEVELOPMENT
        assert request.context.urgency == UrgencyLevel.NORMAL
        assert len(request.goal.success_criteria) > 0

    def test_process_dict_input(self, processor):
        """Test processing a dictionary input."""
        input_dict = {"goal": "Fix bug in auth", "context": {"urgency": "critical"}}
        request = processor.process(input_dict)
        assert request.goal.goal_type == GoalType.DEBUGGING
        assert request.context.urgency == UrgencyLevel.CRITICAL

    def test_process_invalid_input(self, processor):
        """Test processing invalid input."""
        with pytest.raises(InputProcessingError):
            processor.process("")  # Empty string

        with pytest.raises(InputProcessingError):
            processor.process("Short")  # Less than 10 chars
