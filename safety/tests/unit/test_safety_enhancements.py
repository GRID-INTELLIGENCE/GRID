import pytest
import time
from safety.ai_workflow_safety import AIWorkflowSafetyEngine, TemporalSafetyConfig
from safety.content_safety_checker import ContentSafetyChecker
from safety.monitoring import EnhancedSafetyMonitor, SafetyEvent

@pytest.fixture
def safety_config():
    return TemporalSafetyConfig(
        developmental_safety_mode=True,
        rate_limit_max=5,
        rate_limit_window=10
    )

@pytest.fixture
def safety_engine(safety_config):
    return AIWorkflowSafetyEngine("test_user", safety_config, user_age=12)

@pytest.fixture
def content_checker():
    return ContentSafetyChecker()

@pytest.mark.asyncio
async def test_developmental_safety_checks(safety_engine):
    """Test age-appropriate safety checks"""
    # Simulate high attention span risk (this would normally come from tracker)
    # For unit test, we can check the method directly or via evaluate
    assessment = await safety_engine.evaluate_interaction(
        user_input="Quick message",
        ai_response="Quick response",
        response_time=0.1  # Low response time contributes to density risk
    )

    # After multiple rapid interactions, developmental safety issues should emerge
    for _ in range(10):
        await safety_engine.evaluate_interaction(
            user_input="Rapid",
            ai_response="Rapid",
            response_time=0.1
        )

    dev_safety = safety_engine.wellbeing_tracker.check_developmental_safety("Rapid")
    # Given the rapid rate, issues should be detected
    assert "high_attention_span_risk" in dev_safety["reasons"] or dev_safety["is_safe"] is False

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
