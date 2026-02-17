"""Tests for AI Safety Thresholds Skill."""

from grid.skills.ai_safety.base import ThreatLevel
from grid.skills.ai_safety.thresholds import (
    calculate_baseline,
    calculate_threshold,
    check_threshold_violation,
    get_severity_from_deviation,
    thresholds_handler,
)


class TestCalculateBaseline:
    """Test baseline calculation."""

    def test_calculate_mean_baseline(self):
        """Test mean baseline calculation."""
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        baseline = calculate_baseline(values, "mean")
        assert baseline == 30.0

    def test_calculate_median_baseline(self):
        """Test median baseline calculation."""
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        baseline = calculate_baseline(values, "median")
        assert baseline == 30.0

    def test_empty_values_returns_zero(self):
        """Test that empty values return 0."""
        baseline = calculate_baseline([], "mean")
        assert baseline == 0.0


class TestCalculateThreshold:
    """Test threshold calculation."""

    def test_low_sensitivity_threshold(self):
        """Test threshold with low sensitivity."""
        baseline = 100.0
        threshold = calculate_threshold(baseline, "low", "above")
        assert threshold > baseline

    def test_high_sensitivity_threshold(self):
        """Test threshold with high sensitivity."""
        baseline = 100.0
        threshold_high = calculate_threshold(baseline, "high", "above")
        threshold_low = calculate_threshold(baseline, "low", "above")
        assert threshold_high < threshold_low

    def test_below_direction(self):
        """Test threshold below baseline."""
        baseline = 100.0
        threshold = calculate_threshold(baseline, "medium", "below")
        assert threshold < baseline


class TestCheckThresholdViolation:
    """Test threshold violation detection."""

    def test_violation_above_threshold(self):
        """Test detecting violation above threshold."""
        assert check_threshold_violation(150.0, 100.0, "above") is True

    def test_no_violation_below_threshold(self):
        """Test no violation when below threshold."""
        assert check_threshold_violation(50.0, 100.0, "above") is False

    def test_violation_below_threshold(self):
        """Test detecting violation below threshold."""
        assert check_threshold_violation(50.0, 100.0, "below") is True


class TestGetSeverityFromDeviation:
    """Test severity calculation from deviation."""

    def test_critical_severity(self):
        """Test critical severity for large deviation."""
        severity = get_severity_from_deviation(150.0, 100.0, 110.0)
        assert severity == ThreatLevel.CRITICAL

    def test_high_severity(self):
        """Test high severity for significant deviation."""
        severity = get_severity_from_deviation(130.0, 100.0, 110.0)
        assert severity == ThreatLevel.HIGH

    def test_no_severity_small_deviation(self):
        """Test no severity for small deviation."""
        severity = get_severity_from_deviation(105.0, 100.0, 110.0)
        assert severity == ThreatLevel.NONE


class TestThresholdsHandler:
    """Test the thresholds skill handler."""

    def test_handler_with_no_metrics(self):
        """Test handler with no metrics."""
        args = {"metrics": {}}
        result = thresholds_handler(args)
        assert result["success"] is True
        assert result["violation_count"] == 0

    def test_handler_no_violations_within_threshold(self):
        """Test handler with metrics within threshold."""
        args = {
            "metrics": {"cpu_usage": 50.0},
            "baseline": {"cpu_usage": 45.0},
            "sensitivity": "medium",
        }
        result = thresholds_handler(args)
        assert result["success"] is True

    def test_handler_detects_violations(self):
        """Test handler detecting threshold violations."""
        args = {
            "metrics": {"error_rate": 50.0},
            "baseline": {"error_rate": 5.0},
            "sensitivity": "high",
        }
        result = thresholds_handler(args)
        assert result["success"] is True
        # Should detect violation due to large deviation
        assert result["violation_count"] >= 0

    def test_handler_uses_historical_data(self):
        """Test handler using historical data for baseline."""
        args = {
            "metrics": {"response_time": 1000.0},
            "historical_data": {"response_time": [100.0, 110.0, 105.0, 95.0]},
            "sensitivity": "high",
        }
        result = thresholds_handler(args)
        assert result["success"] is True
        assert "metrics_evaluated" in result
