"""Unit tests for the data penalty schema and decay functions.

Tests the penalty severity levels, rules, decay calculation, and serialization.
"""

from datetime import UTC, datetime, timedelta

import pytest

from grid.resilience.penalties import (
    PENALTY_RULES,
    SEVERITY_RANGES,
    DataPenaltySchema,
    PenaltyRule,
    PenaltySeverity,
    calculate_total_penalty,
    decay_penalty,
    get_score_classification,
)


class TestPenaltySeverity:
    """Tests for PenaltySeverity enum and ranges."""

    def test_severity_enum_values(self):
        """Test that severity enum has expected values."""
        assert PenaltySeverity.CRITICAL.value == "critical"
        assert PenaltySeverity.HIGH.value == "high"
        assert PenaltySeverity.MEDIUM.value == "medium"
        assert PenaltySeverity.LOW.value == "low"

    def test_severity_ranges_defined(self):
        """Test that severity ranges are properly defined."""
        assert len(SEVERITY_RANGES) == 4

        # Critical: 20-50
        assert SEVERITY_RANGES[PenaltySeverity.CRITICAL] == (20, 50)
        # High: 10-19
        assert SEVERITY_RANGES[PenaltySeverity.HIGH] == (10, 19)
        # Medium: 5-9
        assert SEVERITY_RANGES[PenaltySeverity.MEDIUM] == (5, 9)
        # Low: 1-4
        assert SEVERITY_RANGES[PenaltySeverity.LOW] == (1, 4)


class TestDataPenaltySchema:
    """Tests for DataPenaltySchema dataclass."""

    def test_create_penalty(self):
        """Test creating a penalty with all fields."""
        penalty = DataPenaltySchema(
            violation_type="test_violation",
            severity=PenaltySeverity.HIGH,
            penalty_points=15.0,
            description="Test violation description",
            component="test/component",
        )

        assert penalty.violation_type == "test_violation"
        assert penalty.severity == PenaltySeverity.HIGH
        assert penalty.penalty_points == 15.0
        assert penalty.description == "Test violation description"
        assert penalty.component == "test/component"
        assert isinstance(penalty.timestamp, datetime)
        assert penalty.metadata == {}

    def test_add_metadata(self):
        """Test adding metadata to a penalty."""
        penalty = DataPenaltySchema(
            violation_type="test",
            severity=PenaltySeverity.LOW,
            penalty_points=2.0,
            description="Test",
        )

        penalty.add_metadata(key1="value1", key2=42)
        assert penalty.metadata["key1"] == "value1"
        assert penalty.metadata["key2"] == 42

    def test_to_dict(self):
        """Test serialization to dictionary."""
        now = datetime.now(UTC)
        penalty = DataPenaltySchema(
            violation_type="sla_violation",
            severity=PenaltySeverity.HIGH,
            penalty_points=15.0,
            description="SLA exceeded",
            component="api/search",
            timestamp=now,
            metadata={"duration": 2.5, "threshold": 1.0},
        )

        result = penalty.to_dict()

        assert result["violation_type"] == "sla_violation"
        assert result["severity"] == "high"
        assert result["penalty_points"] == 15.0
        assert result["description"] == "SLA exceeded"
        assert result["component"] == "api/search"
        assert result["timestamp"] == now.isoformat()
        assert result["metadata"]["duration"] == 2.5

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        now = datetime.now(UTC)
        data = {
            "violation_type": "data_corruption",
            "severity": "critical",
            "penalty_points": 30.0,
            "description": "Data corrupted",
            "component": "storage",
            "timestamp": now.isoformat(),
            "metadata": {"affected_rows": 100},
        }

        penalty = DataPenaltySchema.from_dict(data)

        assert penalty.violation_type == "data_corruption"
        assert penalty.severity == PenaltySeverity.CRITICAL
        assert penalty.penalty_points == 30.0
        assert penalty.component == "storage"
        assert penalty.metadata["affected_rows"] == 100


class TestPenaltyRule:
    """Tests for PenaltyRule class."""

    def test_create_rule(self):
        """Test creating a penalty rule."""
        rule = PenaltyRule(
            violation_type="test_rule",
            severity=PenaltySeverity.MEDIUM,
            base_points=7.0,
            description="Test rule description",
            remediation="Fix the issue",
        )

        assert rule.violation_type == "test_rule"
        assert rule.severity == PenaltySeverity.MEDIUM
        assert rule.base_points == 7.0
        assert rule.remediation == "Fix the issue"

    def test_calculate_points_static(self):
        """Test calculating points without dynamic calculator."""
        rule = PenaltyRule(
            violation_type="static",
            severity=PenaltySeverity.LOW,
            base_points=3.0,
            description="Static points",
        )

        assert rule.calculate_points() == 3.0
        assert rule.calculate_points({"ignored": True}) == 3.0

    def test_calculate_points_dynamic(self):
        """Test calculating points with dynamic calculator."""

        def dynamic_calc(ctx):
            return ctx.get("multiplier", 1) * 10

        rule = PenaltyRule(
            violation_type="dynamic",
            severity=PenaltySeverity.HIGH,
            base_points=10.0,
            description="Dynamic points",
            dynamic_calculator=dynamic_calc,
        )

        # With context - uses dynamic calculator
        assert rule.calculate_points({"multiplier": 2}) == 20.0
        assert rule.calculate_points({"multiplier": 3}) == 30.0

        # Without context - falls back to base_points
        assert rule.calculate_points() == 10.0

    def test_create_penalty_from_rule(self):
        """Test creating a penalty instance from a rule."""
        rule = PenaltyRule(
            violation_type="retry_exhausted",
            severity=PenaltySeverity.MEDIUM,
            base_points=8.0,
            description="Retries exhausted",
        )

        penalty = rule.create_penalty(component="api/v1/fetch", retry_count=3)

        assert penalty.violation_type == "retry_exhausted"
        assert penalty.severity == PenaltySeverity.MEDIUM
        assert penalty.penalty_points == 8.0
        assert penalty.component == "api/v1/fetch"
        assert penalty.metadata["retry_count"] == 3


class TestPenaltyRules:
    """Tests for predefined PENALTY_RULES."""

    def test_required_rules_exist(self):
        """Test that expected penalty rules are defined."""
        required_rules = [
            "data_corruption",
            "security_breach",
            "sla_violation",
            "retry_exhausted",
            "validation_failed",
        ]

        for rule_name in required_rules:
            assert rule_name in PENALTY_RULES, f"Missing rule: {rule_name}"

    def test_data_corruption_is_critical(self):
        """Test that data_corruption is critical severity."""
        rule = PENALTY_RULES["data_corruption"]
        assert rule.severity == PenaltySeverity.CRITICAL
        assert rule.base_points >= 20  # Critical range

    def test_sla_violation_has_dynamic_calculator(self):
        """Test that sla_violation uses dynamic calculation."""
        rule = PENALTY_RULES["sla_violation"]
        assert rule.dynamic_calculator is not None

        # Test dynamic calculation
        points = rule.calculate_points({"duration": 4.0, "threshold": 2.0})
        assert points == 20.0  # 10 * (4/2)

    def test_all_rules_have_description(self):
        """Test that all rules have descriptions."""
        for name, rule in PENALTY_RULES.items():
            assert rule.description, f"Rule {name} missing description"

    def test_rule_severities_match_points(self):
        """Test that rule base points match their severity range."""
        for name, rule in PENALTY_RULES.items():
            min_pts, max_pts = SEVERITY_RANGES[rule.severity]
            assert min_pts <= rule.base_points <= max_pts, (
                f"Rule {name} has {rule.base_points} points but "
                f"severity {rule.severity.value} expects {min_pts}-{max_pts}"
            )


class TestDecayPenalty:
    """Tests for penalty decay calculation."""

    def test_no_decay_for_recent_penalty(self):
        """Test that very recent penalties have minimal decay."""
        now = datetime.now(UTC)
        penalty = DataPenaltySchema(
            violation_type="test",
            severity=PenaltySeverity.MEDIUM,
            penalty_points=10.0,
            description="Test",
            timestamp=now,
        )

        decayed = decay_penalty(penalty, now)
        assert decayed == pytest.approx(10.0, rel=0.01)

    def test_half_decay_after_half_life(self):
        """Test that penalty is halved after half-life period."""
        now = datetime.now(UTC)
        penalty = DataPenaltySchema(
            violation_type="test",
            severity=PenaltySeverity.MEDIUM,
            penalty_points=10.0,
            description="Test",
            timestamp=now - timedelta(hours=24),
        )

        decayed = decay_penalty(penalty, now, half_life_hours=24.0)
        assert decayed == pytest.approx(5.0, rel=0.01)

    def test_quarter_decay_after_two_half_lives(self):
        """Test that penalty is quartered after two half-lives."""
        now = datetime.now(UTC)
        penalty = DataPenaltySchema(
            violation_type="test",
            severity=PenaltySeverity.MEDIUM,
            penalty_points=20.0,
            description="Test",
            timestamp=now - timedelta(hours=48),
        )

        decayed = decay_penalty(penalty, now, half_life_hours=24.0)
        assert decayed == pytest.approx(5.0, rel=0.01)

    def test_custom_half_life(self):
        """Test decay with custom half-life."""
        now = datetime.now(UTC)
        penalty = DataPenaltySchema(
            violation_type="test",
            severity=PenaltySeverity.HIGH,
            penalty_points=16.0,
            description="Test",
            timestamp=now - timedelta(hours=12),
        )

        # With 12-hour half-life, penalty should be halved
        decayed = decay_penalty(penalty, now, half_life_hours=12.0)
        assert decayed == pytest.approx(8.0, rel=0.01)

    def test_future_penalty_no_decay(self):
        """Test that future penalties don't have negative decay."""
        now = datetime.now(UTC)
        penalty = DataPenaltySchema(
            violation_type="test",
            severity=PenaltySeverity.LOW,
            penalty_points=5.0,
            description="Test",
            timestamp=now + timedelta(hours=1),  # Future
        )

        decayed = decay_penalty(penalty, now)
        assert decayed == 5.0  # No decay for future


class TestCalculateTotalPenalty:
    """Tests for total penalty calculation."""

    def test_empty_list(self):
        """Test total penalty for empty list."""
        assert calculate_total_penalty([]) == 0.0

    def test_single_penalty(self):
        """Test total penalty for single penalty."""
        now = datetime.now(UTC)
        penalties = [
            DataPenaltySchema(
                violation_type="test",
                severity=PenaltySeverity.MEDIUM,
                penalty_points=10.0,
                description="Test",
                timestamp=now,
            )
        ]

        total = calculate_total_penalty(penalties, now)
        assert total == pytest.approx(10.0, rel=0.01)

    def test_multiple_penalties_with_decay(self):
        """Test total penalty with multiple penalties and decay."""
        now = datetime.now(UTC)
        penalties = [
            # Recent penalty (full points)
            DataPenaltySchema(
                violation_type="recent",
                severity=PenaltySeverity.MEDIUM,
                penalty_points=10.0,
                description="Recent",
                timestamp=now,
            ),
            # 24-hour old penalty (half points)
            DataPenaltySchema(
                violation_type="old",
                severity=PenaltySeverity.MEDIUM,
                penalty_points=10.0,
                description="Old",
                timestamp=now - timedelta(hours=24),
            ),
        ]

        total = calculate_total_penalty(penalties, now, half_life_hours=24.0)
        # 10 + 5 = 15
        assert total == pytest.approx(15.0, rel=0.01)


class TestGetScoreClassification:
    """Tests for score classification."""

    def test_normal_classification(self):
        """Test scores above 90 are normal."""
        assert get_score_classification(100) == "normal"
        assert get_score_classification(95) == "normal"
        assert get_score_classification(91) == "normal"

    def test_alert_classification(self):
        """Test scores 76-90 are alert."""
        assert get_score_classification(90) == "alert"
        assert get_score_classification(85) == "alert"
        assert get_score_classification(76) == "alert"

    def test_throttle_classification(self):
        """Test scores 50-75 are throttle."""
        assert get_score_classification(75) == "throttle"
        assert get_score_classification(60) == "throttle"
        assert get_score_classification(50) == "throttle"

    def test_degraded_classification(self):
        """Test scores below 50 are degraded."""
        assert get_score_classification(49) == "degraded"
        assert get_score_classification(25) == "degraded"
        assert get_score_classification(0) == "degraded"
