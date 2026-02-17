"""
Tests for Navigation Input Schema and Processor.

Tests the NavigationInputProcessor and related schema classes
for the GRID Navigation Agent System.
"""

from __future__ import annotations

from datetime import datetime

import pytest

# Try to import from light_of_the_seven, skip if not available
try:
    from light_of_the_seven.cognitive_layer.navigation.input_processor import (
        InputProcessingError,
        NavigationInputProcessor,
    )
    from light_of_the_seven.cognitive_layer.navigation.schemas.navigation_input import (
        ComplexityLevel,
        GoalType,
        LearningData,
        NavigationContext,
        NavigationGoal,
        NavigationOutcome,
        NavigationRequest,
        PathConstraint,
        RiskTolerance,
        SkillLevel,
        UrgencyLevel,
    )

    HAS_LIGHT_OF_SEVEN = True
except (ImportError, ModuleNotFoundError):
    HAS_LIGHT_OF_SEVEN = False
    pytestmark = pytest.mark.skip(reason="light_of_the_seven module not available")


class TestGoalType:
    """Tests for GoalType enum."""

    def test_goal_type_values(self) -> None:
        """Test all goal type values exist."""
        assert GoalType.DEVELOPMENT.value == "development"
        assert GoalType.ANALYSIS.value == "analysis"
        assert GoalType.DEBUGGING.value == "debugging"
        assert GoalType.OPTIMIZATION.value == "optimization"
        assert GoalType.INTEGRATION.value == "integration"
        assert GoalType.MAINTENANCE.value == "maintenance"

    def test_goal_type_from_string(self) -> None:
        """Test creating goal type from string."""
        assert GoalType("development") == GoalType.DEVELOPMENT
        assert GoalType("debugging") == GoalType.DEBUGGING


class TestUrgencyLevel:
    """Tests for UrgencyLevel enum."""

    def test_urgency_values(self) -> None:
        """Test all urgency level values."""
        assert UrgencyLevel.LOW.value == "low"
        assert UrgencyLevel.NORMAL.value == "normal"
        assert UrgencyLevel.HIGH.value == "high"
        assert UrgencyLevel.CRITICAL.value == "critical"


class TestComplexityLevel:
    """Tests for ComplexityLevel enum."""

    def test_complexity_values(self) -> None:
        """Test all complexity level values."""
        assert ComplexityLevel.SIMPLE.value == "simple"
        assert ComplexityLevel.MODERATE.value == "moderate"
        assert ComplexityLevel.COMPLEX.value == "complex"
        assert ComplexityLevel.VERY_COMPLEX.value == "very_complex"


class TestNavigationContext:
    """Tests for NavigationContext model."""

    def test_default_context(self) -> None:
        """Test creating context with defaults."""
        context = NavigationContext()

        assert context.urgency == UrgencyLevel.NORMAL
        assert context.complexity == ComplexityLevel.MODERATE
        assert context.skill_level == SkillLevel.INTERMEDIATE
        assert context.risk_tolerance == RiskTolerance.MEDIUM
        assert context.system_state == {}
        assert context.available_resources == []
        assert context.dependencies == []
        assert context.constraints == []

    def test_context_with_values(self) -> None:
        """Test creating context with custom values."""
        context = NavigationContext(
            urgency=UrgencyLevel.HIGH,
            complexity=ComplexityLevel.COMPLEX,
            skill_level=SkillLevel.EXPERT,
            risk_tolerance=RiskTolerance.HIGH,
            dependencies=["module_a", "module_b"],
            constraints=["no_external_api"],
        )

        assert context.urgency == UrgencyLevel.HIGH
        assert context.complexity == ComplexityLevel.COMPLEX
        assert context.skill_level == SkillLevel.EXPERT
        assert len(context.dependencies) == 2
        assert len(context.constraints) == 1

    def test_context_with_system_state(self) -> None:
        """Test context with system state."""
        context = NavigationContext(
            system_state={"cpu_usage": 0.5, "memory_free": 1024},
            available_resources=["gpu", "ssd"],
        )

        assert context.system_state["cpu_usage"] == 0.5
        assert "gpu" in context.available_resources

    def test_context_learned_patterns(self) -> None:
        """Test context with learned patterns."""
        context = NavigationContext(
            learned_patterns={"pattern_a": 0.8, "pattern_b": 0.6},
            success_history={"path_direct": 0.9},
        )

        assert context.learned_patterns["pattern_a"] == 0.8
        assert context.success_history["path_direct"] == 0.9


class TestNavigationGoal:
    """Tests for NavigationGoal model."""

    def test_valid_goal(self) -> None:
        """Test creating a valid goal."""
        goal = NavigationGoal(
            goal_type=GoalType.DEVELOPMENT,
            primary_objective="Create a new API endpoint for user authentication",
            success_criteria=["JWT token works", "Tests pass"],
        )

        assert goal.goal_type == GoalType.DEVELOPMENT
        assert len(goal.primary_objective) > 10
        assert len(goal.success_criteria) == 2

    def test_goal_with_constraints(self) -> None:
        """Test goal with constraints and preferences."""
        goal = NavigationGoal(
            goal_type=GoalType.OPTIMIZATION,
            primary_objective="Optimize the database query performance by 50%",
            max_execution_time=3600.0,
            preferred_approaches=["indexing", "query_rewrite"],
            excluded_approaches=["denormalization"],
        )

        assert goal.max_execution_time == 3600.0
        assert "indexing" in goal.preferred_approaches
        assert "denormalization" in goal.excluded_approaches

    def test_goal_objective_validation(self) -> None:
        """Test that short objectives are rejected."""
        with pytest.raises(ValueError, match="at least 10 characters"):
            NavigationGoal(
                goal_type=GoalType.DEVELOPMENT,
                primary_objective="Short",
            )

    def test_goal_objective_strip_whitespace(self) -> None:
        """Test that objectives are stripped of whitespace."""
        goal = NavigationGoal(
            goal_type=GoalType.DEVELOPMENT,
            primary_objective="   Create a new feature for the system   ",
        )

        assert goal.primary_objective == "Create a new feature for the system"

    def test_goal_priority_bounds(self) -> None:
        """Test goal priority bounds."""
        goal = NavigationGoal(
            goal_type=GoalType.DEVELOPMENT,
            primary_objective="Create something important",
            priority=10,
        )
        assert goal.priority == 10

        # Test default priority
        goal2 = NavigationGoal(
            goal_type=GoalType.DEVELOPMENT,
            primary_objective="Create something normal",
        )
        assert goal2.priority == 5


class TestNavigationRequest:
    """Tests for NavigationRequest model."""

    def test_valid_request(self) -> None:
        """Test creating a valid request."""
        goal = NavigationGoal(
            goal_type=GoalType.DEVELOPMENT,
            primary_objective="Implement user authentication API",
        )
        context = NavigationContext(urgency=UrgencyLevel.HIGH)

        request = NavigationRequest(
            goal=goal,
            context=context,
        )

        assert request.goal == goal
        assert request.context == context
        assert request.request_id.startswith("nav-")
        assert request.source == "cli"
        assert request.enable_learning is True
        assert request.max_alternatives == 3

    def test_request_with_learning_params(self) -> None:
        """Test request with learning parameters."""
        goal = NavigationGoal(
            goal_type=GoalType.DEBUGGING,
            primary_objective="Fix the memory leak in data processing module",
        )

        request = NavigationRequest(
            goal=goal,
            enable_learning=True,
            learning_weight=0.2,
            adaptation_threshold=0.8,
        )

        assert request.learning_weight == 0.2
        assert request.adaptation_threshold == 0.8

    def test_request_output_preferences(self) -> None:
        """Test request with output preferences."""
        goal = NavigationGoal(
            goal_type=GoalType.ANALYSIS,
            primary_objective="Analyze the codebase for security vulnerabilities",
        )

        request = NavigationRequest(
            goal=goal,
            max_alternatives=5,
            include_confidence=True,
            include_reasoning=True,
            verbosity="detailed",
        )

        assert request.max_alternatives == 5
        assert request.include_confidence is True
        assert request.verbosity == "detailed"

    def test_request_dry_run(self) -> None:
        """Test request with dry run flag."""
        goal = NavigationGoal(
            goal_type=GoalType.REFACTORING,
            primary_objective="Refactor the authentication module structure",
        )

        request = NavigationRequest(
            goal=goal,
            dry_run=True,
            timeout_ms=5000,
        )

        assert request.dry_run is True
        assert request.timeout_ms == 5000

    def test_request_timestamp(self) -> None:
        """Test request has valid timestamp."""
        goal = NavigationGoal(
            goal_type=GoalType.DEVELOPMENT,
            primary_objective="Create a new feature module",
        )

        request = NavigationRequest(goal=goal)

        assert isinstance(request.timestamp, datetime)


class TestPathConstraint:
    """Tests for PathConstraint model."""

    def test_default_constraints(self) -> None:
        """Test default path constraints."""
        constraint = PathConstraint()

        assert constraint.max_memory_usage is None
        assert constraint.max_cpu_time is None
        assert constraint.requires_internet is False
        assert constraint.requires_admin is False

    def test_resource_constraints(self) -> None:
        """Test resource constraints."""
        constraint = PathConstraint(
            max_memory_usage=512.0,
            max_cpu_time=60.0,
            max_steps=10,
        )

        assert constraint.max_memory_usage == 512.0
        assert constraint.max_cpu_time == 60.0
        assert constraint.max_steps == 10

    def test_dependency_constraints(self) -> None:
        """Test dependency constraints."""
        constraint = PathConstraint(
            required_libraries=["numpy", "pandas"],
            forbidden_libraries=["tensorflow"],
            required_services=["redis"],
        )

        assert "numpy" in constraint.required_libraries
        assert "tensorflow" in constraint.forbidden_libraries
        assert "redis" in constraint.required_services

    def test_quality_constraints(self) -> None:
        """Test quality constraints."""
        constraint = PathConstraint(
            min_test_coverage=0.8,
            max_error_rate=0.05,
            min_confidence=0.7,
        )

        assert constraint.min_test_coverage == 0.8
        assert constraint.max_error_rate == 0.05
        assert constraint.min_confidence == 0.7


class TestLearningData:
    """Tests for LearningData model."""

    def test_default_learning_data(self) -> None:
        """Test default learning data."""
        data = LearningData()

        assert data.total_samples == 0
        assert data.learning_epoch == 0
        assert data.success_rates == {}
        assert data.preferred_patterns == {}

    def test_add_outcome(self) -> None:
        """Test adding outcome to learning data."""
        data = LearningData()

        data.add_outcome(
            goal_id="goal-001",
            success=True,
            execution_time=1500.0,
            pattern="incremental",
            rating=5,
        )

        assert data.total_samples == 1
        assert data.success_rates["incremental"] == 1.0
        assert data.execution_times["goal-001"] == 1500.0
        assert data.user_ratings["goal-001"] == 5
        assert data.last_updated is not None

    def test_add_multiple_outcomes(self) -> None:
        """Test adding multiple outcomes."""
        data = LearningData()

        data.add_outcome("goal-001", True, 1000.0, "direct")
        data.add_outcome("goal-002", False, 2000.0, "direct")
        data.add_outcome("goal-003", True, 1500.0, "direct")

        assert data.total_samples == 3
        # Success rate should be calculated as running average
        assert 0.5 <= data.success_rates["direct"] <= 0.75


class TestNavigationOutcome:
    """Tests for NavigationOutcome model."""

    def test_valid_outcome(self) -> None:
        """Test creating a valid outcome."""
        outcome = NavigationOutcome(
            request_id="nav-123",
            success=True,
            selected_path_id="path-direct",
            execution_time_ms=1500.0,
            steps_completed=3,
        )

        assert outcome.success is True
        assert outcome.selected_path_id == "path-direct"
        assert outcome.execution_time_ms == 1500.0
        assert outcome.steps_completed == 3

    def test_outcome_with_feedback(self) -> None:
        """Test outcome with user feedback."""
        outcome = NavigationOutcome(
            request_id="nav-456",
            success=True,
            selected_path_id="path-incremental",
            execution_time_ms=3000.0,
            user_rating=4,
            user_feedback="Good approach but could be faster",
        )

        assert outcome.user_rating == 4
        assert "faster" in outcome.user_feedback

    def test_outcome_with_errors(self) -> None:
        """Test outcome with errors."""
        outcome = NavigationOutcome(
            request_id="nav-789",
            success=False,
            selected_path_id="path-comprehensive",
            execution_time_ms=5000.0,
            errors_encountered=["Import error", "Test failure"],
        )

        assert outcome.success is False
        assert len(outcome.errors_encountered) == 2


class TestNavigationInputProcessor:
    """Tests for NavigationInputProcessor."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.processor = NavigationInputProcessor()

    def test_process_string_input(self) -> None:
        """Test processing simple string input."""
        request = self.processor.process("Create a new API endpoint for user authentication")

        assert isinstance(request, NavigationRequest)
        assert request.goal.goal_type == GoalType.DEVELOPMENT
        assert "authentication" in request.goal.primary_objective

    def test_process_string_detects_debugging(self) -> None:
        """Test that debugging keywords are detected."""
        request = self.processor.process("Debug the memory leak issue in the data processing module")

        assert request.goal.goal_type == GoalType.DEBUGGING

    def test_process_string_detects_optimization(self) -> None:
        """Test that optimization keywords are detected."""
        request = self.processor.process("Optimize the database query performance to reduce latency")

        assert request.goal.goal_type == GoalType.OPTIMIZATION

    def test_process_string_detects_integration(self) -> None:
        """Test that integration keywords are detected."""
        request = self.processor.process("Integrate and connect the external payment service")

        assert request.goal.goal_type == GoalType.INTEGRATION

    def test_process_string_detects_analysis(self) -> None:
        """Test that analysis keywords are detected."""
        request = self.processor.process("Analyze and examine the system logs to review usage patterns")

        assert request.goal.goal_type == GoalType.ANALYSIS

    def test_process_string_detects_urgency(self) -> None:
        """Test that urgency is detected from string."""
        request = self.processor.process("Critical: Fix the production outage immediately")

        assert request.context.urgency == UrgencyLevel.CRITICAL

    def test_process_string_detects_complexity(self) -> None:
        """Test that complexity is detected from string."""
        request = self.processor.process("Simple fix for the typo in the configuration file")

        assert request.context.complexity == ComplexityLevel.SIMPLE

    def test_process_dict_input(self) -> None:
        """Test processing dictionary input."""
        input_dict = {
            "goal": {
                "goal_type": "development",
                "primary_objective": "Implement user authentication API",
                "success_criteria": ["JWT works", "Tests pass"],
            },
            "context": {
                "urgency": "high",
                "complexity": "moderate",
            },
        }

        request = self.processor.process(input_dict)

        assert isinstance(request, NavigationRequest)
        assert request.goal.goal_type == GoalType.DEVELOPMENT
        assert request.context.urgency == UrgencyLevel.HIGH

    def test_process_dict_with_string_goal(self) -> None:
        """Test processing dict with string goal."""
        input_dict = {
            "goal": "Create a new feature for user management",
            "context": {"urgency": "normal"},
        }

        request = self.processor.process(input_dict)

        assert request.goal.goal_type == GoalType.DEVELOPMENT
        assert "user management" in request.goal.primary_objective

    def test_process_navigation_request_passthrough(self) -> None:
        """Test that NavigationRequest passes through."""
        original = NavigationRequest(
            goal=NavigationGoal(
                goal_type=GoalType.DEVELOPMENT,
                primary_objective="Create a test feature",
            )
        )

        result = self.processor.process(original)

        assert result == original

    def test_process_empty_string_raises_error(self) -> None:
        """Test that empty string raises error."""
        with pytest.raises(InputProcessingError, match="Empty goal string"):
            self.processor.process("")

    def test_process_short_string_raises_error(self) -> None:
        """Test that short string raises error."""
        with pytest.raises(InputProcessingError, match="too short"):
            self.processor.process("Fix it")

    def test_process_invalid_type_raises_error(self) -> None:
        """Test that invalid type raises error."""
        with pytest.raises(InputProcessingError, match="Unsupported input type"):
            self.processor.process(12345)  # type: ignore

    def test_process_invalid_dict_raises_error(self) -> None:
        """Test that invalid dict raises error."""
        with pytest.raises(InputProcessingError, match="Missing required field"):
            self.processor.process({"context": {"urgency": "high"}})

    def test_success_criteria_generation(self) -> None:
        """Test that success criteria are generated."""
        request = self.processor.process("Create a new API endpoint with tests")

        assert len(request.goal.success_criteria) > 0

    def test_extract_entities(self) -> None:
        """Test entity extraction from text."""
        entities = self.processor.extract_entities("Create a Python API endpoint using FastAPI")

        assert "python" in entities["technologies"]
        assert "api" in entities["technologies"]
        assert "create" in entities["actions"]
        assert "endpoint" in entities["targets"]

    def test_normalize_context_enums(self) -> None:
        """Test context enum normalization."""
        input_dict = {
            "goal": {
                "goal_type": "DEVELOPMENT",  # Uppercase
                "primary_objective": "Create a new feature module",
            },
            "context": {
                "urgency": "HIGH",  # Uppercase
                "complexity": "COMPLEX",  # Uppercase
            },
        }

        request = self.processor.process(input_dict)

        # Should normalize to lowercase enum values
        assert request.context.urgency == UrgencyLevel.HIGH
        assert request.context.complexity == ComplexityLevel.COMPLEX


class TestInputProcessorBackwardCompatibility:
    """Tests for backward compatibility of input processor."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.processor = NavigationInputProcessor()

    def test_process_raw_input_alias(self) -> None:
        """Test that process_raw_input is an alias for process."""
        result1 = self.processor.process("Create a new feature for the system")
        result2 = self.processor.process_raw_input("Create a new feature for the system")

        assert result1.goal.goal_type == result2.goal.goal_type
        assert result1.goal.primary_objective == result2.goal.primary_objective

    def test_flat_dict_structure(self) -> None:
        """Test handling of flat dictionary structure."""
        input_dict = {
            "primary_objective": "Create a new module for user handling",
            "goal_type": "development",
        }

        request = self.processor.process(input_dict)

        assert request.goal.goal_type == GoalType.DEVELOPMENT
        assert "user handling" in request.goal.primary_objective

    def test_objective_alias(self) -> None:
        """Test handling of 'objective' as alias."""
        input_dict = {
            "objective": "Create a new feature for reporting",
            "goal_type": "development",
        }

        request = self.processor.process(input_dict)

        assert "reporting" in request.goal.primary_objective
