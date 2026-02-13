import time

import pytest

from safety.ai_workflow_safety import AIWorkflowSafetyEngine, InteractionRecord, TemporalSafetyConfig
from safety.content_safety_checker import ContentSafetyChecker
from safety.monitoring import EnhancedSafetyMonitor, SafetyEvent


@pytest.fixture
def safety_config():
    return TemporalSafetyConfig(
        developmental_safety_mode=True,
        rate_limit_max=5,
        rate_limit_window=10,
        min_response_interval=0.0,
        max_burst_responses=100,
        enable_hook_detection=False,
    )


@pytest.fixture
def safety_engine(safety_config):
    return AIWorkflowSafetyEngine("test_user", safety_config, user_age=12)


@pytest.fixture
def content_checker():
    return ContentSafetyChecker()


@pytest.mark.asyncio
async def test_developmental_safety_checks(safety_engine):
    """Test age-appropriate safety checks are evaluated for minors."""
    import time as _time

    now = _time.time()
    # Feed interactions directly to the wellbeing tracker so the engine's
    # pre-check gates (developmental safety, hook detection) cannot block
    # and prevent metric recording.
    for i in range(11):
        interaction = InteractionRecord(
            timestamp=now + i,
            user_input_length=5,
            ai_response_length=5,
            response_time=0.1,
        )
        safety_engine.wellbeing_tracker.update_metrics(interaction)

    dev_safety = safety_engine.wellbeing_tracker.check_developmental_safety("Rapid")

    # For a 12-year-old, developmental safety must be evaluated (not skipped)
    assert "age_group" in dev_safety
    assert dev_safety["age_group"] == "pre_teen"
    # The system should return a valid safety assessment (safe or with issues)
    assert "is_safe" in dev_safety
    assert "reasons" in dev_safety
    # Metrics should have been populated after enough interactions
    assert dev_safety["metrics"]["total_interactions"] >= 10


def test_rate_limiting(safety_engine):
    """Test sliding window rate limiting functionality"""
    user_id = "test_user"
    timestamp = time.time()

    # RateLimiter.check_rate_limit(user_id, input_text, timestamp) returns dict with 'allowed'
    # First 5 requests should pass (limit is 5)
    for _ in range(5):
        result = safety_engine.rate_limiter.check_rate_limit(user_id, "x", timestamp)
        assert result["allowed"] is True

    # 6th request should be rate limited (rate_limit_max=5, so 6 in same window is over)
    result = safety_engine.rate_limiter.check_rate_limit(user_id, "x", timestamp)
    assert result["allowed"] is False

    # Wait for window to pass
    future_timestamp = timestamp + 11
    result = safety_engine.rate_limiter.check_rate_limit(user_id, "x", future_timestamp)
    assert result["allowed"] is True


def test_content_safety(content_checker):
    """Test sensitive term and topic detection"""
    # Test sensitive term
    result = content_checker.check_content("This contains a private_key")
    assert result["is_safe"] is False
    assert any(issue["type"] == "sensitive_term_detected" for issue in result["issues"])

    # Test sensitive topic
    result = content_checker.check_content("There is too much violence in this game")
    assert result["is_safe"] is False
    assert any(issue["type"] == "sensitive_topic_detected" for issue in result["issues"])

    # Test age-appropriate content
    result = content_checker.check_content("graphic content", user_age=10)
    assert result["is_safe"] is False
    assert any(issue["type"] == "age_inappropriate_content" for issue in result["issues"])


def test_safety_monitor():
    """Test structured logging and alerting"""
    monitor = EnhancedSafetyMonitor(alert_thresholds={"test_event": (2, 60)})
    alerts = []

    def alert_handler(alert):
        alerts.append(alert)

    monitor.add_alert_handler(alert_handler)

    event = SafetyEvent(event_type="test_event", severity="high")

    # First event - no alert
    monitor.record_event(event)
    assert len(alerts) == 0

    # Second event - triggers alert
    monitor.record_event(event)
    assert len(alerts) == 1
    assert alerts[0]["alert_type"] == "test_event_threshold_exceeded"
