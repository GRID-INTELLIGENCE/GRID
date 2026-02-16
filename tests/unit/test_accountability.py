"""Unit tests for the accountability calculator and delivery scoring.

Tests the AccountabilityCalculator, DeliveryScore, and integration with
resilience metrics.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from grid.resilience.accountability import (
    AccountabilityCalculator,
    DeliveryClassification,
    DeliveryScore,
)
from grid.resilience.metrics import MetricsCollector
from grid.resilience.penalties import DataPenaltySchema, PenaltySeverity


class TestDeliveryScore:
    """Tests for DeliveryScore dataclass."""

    def test_create_delivery_score(self):
        """Test creating a delivery score."""
        score = DeliveryScore(
            endpoint="GET:/api/v1/search",
            score=95.0,
            classification=DeliveryClassification.EXCELLENT,
            penalties_applied=[],
            bonuses_applied=[{"type": "low_latency", "points": 3}],
            recommendation="Maintain current performance.",
        )

        assert score.endpoint == "GET:/api/v1/search"
        assert score.score == 95.0
        assert score.classification == "EXCELLENT"
        assert len(score.bonuses_applied) == 1

    def test_to_dict(self):
        """Test serialization to dictionary."""
        now = datetime.now(UTC)
        score = DeliveryScore(
            endpoint="POST:/api/v1/upsert",
            score=85.5,
            classification=DeliveryClassification.GOOD,
            penalties_applied=[{"type": "low_success_rate", "points": -10}],
            bonuses_applied=[],
            timestamp=now,
            recommendation="Improve success rate.",
        )

        result = score.to_dict()

        assert result["endpoint"] == "POST:/api/v1/upsert"
        assert result["score"] == 85.5
        assert result["classification"] == "GOOD"
        assert len(result["penalties_applied"]) == 1
        assert result["timestamp"] == now.isoformat()


class TestDeliveryClassification:
    """Tests for classification constants."""

    def test_classification_values(self):
        """Test that classification constants are defined."""
        assert DeliveryClassification.EXCELLENT == "EXCELLENT"
        assert DeliveryClassification.GOOD == "GOOD"
        assert DeliveryClassification.DEGRADED == "DEGRADED"
        assert DeliveryClassification.CRITICAL == "CRITICAL"


class TestAccountabilityCalculator:
    """Tests for AccountabilityCalculator."""

    @pytest.fixture
    def collector(self):
        """Create a fresh metrics collector for testing."""
        return MetricsCollector()

    @pytest.fixture
    def calculator(self, collector):
        """Create an accountability calculator with a test collector."""
        return AccountabilityCalculator(metrics_collector=collector)

    def test_score_no_metrics(self, calculator):
        """Test score calculation with no prior metrics."""
        score = calculator.calculate_score("GET:/api/new-endpoint")

        # Should return base score of 100
        assert score.score == 100.0
        assert score.classification == DeliveryClassification.EXCELLENT
        assert len(score.penalties_applied) == 0

    def test_score_with_low_latency_bonus(self, calculator):
        """Test that low latency adds bonus points."""
        score = calculator.calculate_score("GET:/api/fast", latency_ms=50.0)

        assert score.score == 103.0  # 100 + 3 bonus
        assert any(b["type"] == "low_latency" for b in score.bonuses_applied)

    def test_score_excellent_success_rate(self, calculator, collector):
        """Test excellent classification with high success rate."""
        endpoint = "GET:/api/healthy"

        # Record successful attempts
        for _ in range(20):
            collector.record_attempt(endpoint, success=True)

        score = calculator.calculate_score(endpoint)

        assert score.score >= 100.0
        assert score.classification == DeliveryClassification.EXCELLENT

    def test_score_low_success_rate_penalty(self, calculator, collector):
        """Test penalty for success rate below 95%."""
        endpoint = "GET:/api/degraded"

        # 93% success rate (14/15)
        for _ in range(14):
            collector.record_attempt(endpoint, success=True)
        collector.record_attempt(endpoint, success=False)

        score = calculator.calculate_score(endpoint)

        # Should have low_success_rate penalty (-10)
        assert any(p["type"] == "low_success_rate" for p in score.penalties_applied)
        assert score.score == 90.0  # 100 - 10

    def test_score_critical_success_rate_penalty(self, calculator, collector):
        """Test penalty for success rate below 90%."""
        endpoint = "GET:/api/critical"

        # 80% success rate (8/10)
        for _ in range(8):
            collector.record_attempt(endpoint, success=True)
        for _ in range(2):
            collector.record_attempt(endpoint, success=False)

        score = calculator.calculate_score(endpoint)

        # Should have critical_success_rate penalty (-25)
        assert any(p["type"] == "critical_success_rate" for p in score.penalties_applied)
        assert score.score == 75.0  # 100 - 25
        assert score.classification == DeliveryClassification.DEGRADED

    def test_score_high_fallback_rate_penalty(self, calculator, collector):
        """Test penalty for high fallback rate."""
        endpoint = "GET:/api/fallback-heavy"

        # Record attempts with high fallback usage
        for _ in range(8):
            collector.record_attempt(endpoint, success=True)
        for _ in range(2):
            collector.record_attempt(endpoint, success=True)
            collector.record_fallback(endpoint)

        score = calculator.calculate_score(endpoint)

        # 20% fallback rate should trigger penalty
        assert any(p["type"] == "high_fallback_rate" for p in score.penalties_applied)

    def test_score_high_retry_penalty(self, calculator, collector):
        """Test penalty for high average retries."""
        endpoint = "GET:/api/retry-heavy"

        # Record failures with many retries
        collector.record_attempt(endpoint, success=False, required_retry=True)
        collector.record_retry(endpoint)
        collector.record_retry(endpoint)
        collector.record_retry(endpoint)  # 3 retries for 1 failure

        score = calculator.calculate_score(endpoint)

        # avg_retries_per_failure > 2 should trigger penalty
        assert any(p["type"] == "high_retry_count" for p in score.penalties_applied)

    def test_score_recent_error_penalty(self, calculator, collector):
        """Test penalty for recent error."""
        endpoint = "GET:/api/recent-error"

        # Record a recent failure
        collector.record_attempt(endpoint, success=False, error=Exception("Test error"))

        score = calculator.calculate_score(endpoint)

        # Recent error should trigger penalty
        assert any(p["type"] == "recent_error" for p in score.penalties_applied)

    def test_perfect_streak_bonus(self, calculator, collector):
        """Test bonus for perfect streak."""
        endpoint = "GET:/api/perfect"

        # Record 15 successful attempts (> 10 for bonus)
        for _ in range(15):
            collector.record_attempt(endpoint, success=True)

        score = calculator.calculate_score(endpoint)

        # Should have perfect streak bonus
        assert any(b["type"] == "perfect_streak" for b in score.bonuses_applied)
        assert score.score >= 105.0  # 100 + 5 bonus

    def test_multiple_penalties_accumulate(self, calculator, collector):
        """Test that multiple penalties accumulate."""
        endpoint = "GET:/api/troubled"

        # Create conditions for multiple penalties
        # Low success rate
        for _ in range(7):
            collector.record_attempt(endpoint, success=True)
        for _ in range(3):
            collector.record_attempt(endpoint, success=False, error=Exception("Error"))

        # High fallback rate
        for _ in range(2):
            collector.record_fallback(endpoint)

        score = calculator.calculate_score(endpoint)

        # Should have multiple penalties
        assert len(score.penalties_applied) >= 2
        assert score.classification in (
            DeliveryClassification.DEGRADED,
            DeliveryClassification.CRITICAL,
        )

    def test_critical_classification(self, calculator, collector):
        """Test that very low scores get CRITICAL classification."""
        endpoint = "GET:/api/broken"

        # Many failures
        for _ in range(2):
            collector.record_attempt(endpoint, success=True)
        for _ in range(8):
            collector.record_attempt(endpoint, success=False, error=Exception("Error"))
            collector.record_fallback(endpoint)

        score = calculator.calculate_score(endpoint)

        assert score.classification == DeliveryClassification.CRITICAL
        assert score.score < 60

    def test_recommendation_for_excellent(self, calculator):
        """Test recommendation for excellent score."""
        score = calculator.calculate_score("GET:/api/perfect", latency_ms=50)

        assert "Maintain" in score.recommendation

    def test_recommendation_for_degraded(self, calculator, collector):
        """Test recommendation for degraded score."""
        endpoint = "GET:/api/degraded"

        for _ in range(8):
            collector.record_attempt(endpoint, success=True)
        for _ in range(2):
            collector.record_attempt(endpoint, success=False)

        score = calculator.calculate_score(endpoint)

        assert "critical_success_rate" in score.recommendation.lower() or "Improve" in score.recommendation


class TestAccountabilityCalculatorPenalties:
    """Tests for data penalty integration."""

    @pytest.fixture
    def calculator(self):
        """Create a calculator with fresh collector."""
        return AccountabilityCalculator(metrics_collector=MetricsCollector())

    def test_register_and_apply_penalty(self, calculator):
        """Test registering and applying data penalties."""
        endpoint = "GET:/api/penalized"

        # Register a penalty
        penalty = DataPenaltySchema(
            violation_type="test_penalty",
            severity=PenaltySeverity.MEDIUM,
            penalty_points=8.0,
            description="Test penalty",
        )
        calculator.register_penalty(endpoint, penalty)

        score = calculator.calculate_score(endpoint)

        # Score should be reduced by penalty
        assert any(p["type"] == "data_penalties" for p in score.penalties_applied)
        assert score.score < 100.0

    def test_penalty_decay(self, calculator):
        """Test that old penalties decay."""
        endpoint = "GET:/api/old-penalty"

        # Register an old penalty (24 hours ago)
        old_time = datetime.now(UTC) - timedelta(hours=24)
        penalty = DataPenaltySchema(
            violation_type="old_penalty",
            severity=PenaltySeverity.MEDIUM,
            penalty_points=10.0,
            description="Old penalty",
            timestamp=old_time,
        )
        calculator.register_penalty(endpoint, penalty)

        score = calculator.calculate_score(endpoint)

        # Should be decayed to ~5 points
        data_penalty = next(
            (p for p in score.penalties_applied if p["type"] == "data_penalties"),
            None,
        )
        assert data_penalty is not None
        # Decayed points should be about -5 (half of 10)
        assert data_penalty["points"] == pytest.approx(-5.0, rel=0.1)

    def test_clear_penalties(self, calculator):
        """Test clearing penalties."""
        endpoint = "GET:/api/clear-test"

        penalty = DataPenaltySchema(
            violation_type="test",
            severity=PenaltySeverity.LOW,
            penalty_points=5.0,
            description="Test",
        )
        calculator.register_penalty(endpoint, penalty)

        # Clear and verify
        cleared = calculator.clear_penalties(endpoint)
        assert cleared == 1

        # Score should be back to base
        score = calculator.calculate_score(endpoint)
        assert score.score == 100.0


class TestAccountabilityCalculatorTrend:
    """Tests for trend calculation."""

    @pytest.fixture
    def collector(self):
        """Create a fresh metrics collector for testing."""
        return MetricsCollector()

    @pytest.fixture
    def calculator(self, collector):
        """Create a calculator with fresh collector."""
        return AccountabilityCalculator(metrics_collector=collector)

    def test_trend_insufficient_data(self, calculator):
        """Test trend with no history."""
        trend = calculator.get_trend("GET:/api/unknown")

        assert trend["trend"] == "insufficient_data"
        assert trend["data_points"] == 0

    def test_trend_stable(self, calculator):
        """Test stable trend detection."""
        endpoint = "GET:/api/stable"

        # Generate consistent scores
        for _ in range(5):
            calculator.calculate_score(endpoint)

        trend = calculator.get_trend(endpoint, hours=24)

        assert trend["trend"] == "stable"
        assert trend["data_points"] == 5
        assert trend["average_score"] == 100.0

    def test_get_all_scores(self, calculator):
        """Test getting all endpoint scores."""
        # Calculate scores for multiple endpoints
        calculator.calculate_score("GET:/api/endpoint1")
        calculator.calculate_score("POST:/api/endpoint2")

        all_scores = calculator.get_all_scores()

        assert len(all_scores) == 2
        assert "GET:/api/endpoint1" in all_scores
        assert "POST:/api/endpoint2" in all_scores

    def test_export_summary(self, calculator, collector):
        """Test exporting summary for monitoring."""
        # Add some endpoints with different scores
        endpoint1 = "GET:/api/good"
        endpoint2 = "GET:/api/bad"

        for _ in range(10):
            collector.record_attempt(endpoint1, success=True)

        for _ in range(5):
            collector.record_attempt(endpoint2, success=True)
        for _ in range(5):
            collector.record_attempt(endpoint2, success=False)

        calculator.calculate_score(endpoint1)
        calculator.calculate_score(endpoint2)

        summary = calculator.export_summary()

        assert summary["total_endpoints"] == 2
        assert "average_score" in summary
        assert endpoint1 in summary["endpoints"]
        assert endpoint2 in summary["endpoints"]


class TestAccountabilityMiddlewareIntegration:
    """Tests for middleware integration (without running actual server)."""

    def test_middleware_imports(self):
        """Test that middleware can be imported."""
        from application.mothership.middleware.accountability import (
            DEFAULT_TRACKED_PREFIXES,
            AccountabilityMiddleware,
        )

        assert AccountabilityMiddleware is not None
        assert "/api/" in DEFAULT_TRACKED_PREFIXES
        assert "/rag/" in DEFAULT_TRACKED_PREFIXES
        assert "/health/" in DEFAULT_TRACKED_PREFIXES

    def test_middleware_init(self):
        """Test middleware initialization."""
        from application.mothership.middleware.accountability import AccountabilityMiddleware

        # Mock app
        mock_app = MagicMock()

        middleware = AccountabilityMiddleware(mock_app)

        assert middleware.tracked_prefixes == ("/api/", "/rag/", "/health/")
        assert middleware.log_degraded is True

    def test_middleware_custom_prefixes(self):
        """Test middleware with custom prefixes."""
        from application.mothership.middleware.accountability import AccountabilityMiddleware

        mock_app = MagicMock()
        custom_prefixes = ("/custom/", "/v2/")

        middleware = AccountabilityMiddleware(mock_app, tracked_prefixes=custom_prefixes, log_degraded=False)

        assert middleware.tracked_prefixes == custom_prefixes
        assert middleware.log_degraded is False
