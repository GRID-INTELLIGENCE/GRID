"""
Smoke Tests for Coinbase Components
====================================
Critical path tests ensuring core functionality.

Focus: Quality over quantity - practical relevance, accuracy, precision.
"""


import pytest

from coinbase.core.attention_allocator import AttentionAllocator
from coinbase.infrastructure.databricks_connector import DatabricksConnector
from coinbase.patterns.pattern_dictionary import PatternDictionary, PatternType
from coinbase.revenue.portfolio_calendar import EventType, PortfolioCalendar
from coinbase.security.privacy_vault import PrivacyVault
from coinbase.signals.trading_compass import TradingCompass
from coinbase.tools.notification_watch import NotificationWatch
from coinbase.verification.verification_scale import VerificationScale


def test_databricks_connector_initialization():
    """Smoke test: Databricks connector can be initialized."""
    import os

    # Test with credentials
    if all(
        [
            os.getenv("DATABRICKS_HOST"),
            os.getenv("DATABRICKS_HTTP_PATH"),
            os.getenv("DATABRICKS_TOKEN"),
        ]
    ):
        connector = DatabricksConnector()
        assert connector is not None
        assert connector.connection_params is not None
    else:
        # Test error handling
        with pytest.raises(ValueError):
            DatabricksConnector()


def test_attention_allocator_basic():
    """Smoke test: Attention allocator can allocate focus."""
    allocator = AttentionAllocator()
    focus = allocator.allocate(task="Test task", priority=0.8)

    assert focus.task == "Test task"
    assert focus.focus_intensity > 0


def test_portfolio_calendar_basic():
    """Smoke test: Portfolio calendar can schedule events."""
    calendar = PortfolioCalendar()
    event = calendar.schedule_event(
        event_type=EventType.BUY, asset_symbol="BTC", quantity=0.5, price=50000.0
    )

    assert event is not None
    assert event.asset_symbol == "BTC"


def test_pattern_dictionary_basic():
    """Smoke test: Pattern dictionary can recognize patterns."""
    dictionary = PatternDictionary()
    match = dictionary.recognize(PatternType.PRICE_SPIKE, value=0.15)

    assert match is not None
    assert match.detected is True


def test_notification_watch_basic():
    """Smoke test: Notification watch can set alarms."""
    watch = NotificationWatch()
    alarm = watch.set_alarm(condition="price_above", threshold=52000.0, action="notify_user")

    assert alarm is not None
    assert alarm.condition == "price_above"


def test_trading_compass_basic():
    """Smoke test: Trading compass can generate signals."""
    compass = TradingCompass()
    signal = compass.point_direction(sentiment=0.75, momentum=5.0, current_price=50000.0)

    assert signal is not None
    assert signal.direction is not None


def test_verification_scale_basic():
    """Smoke test: Verification scale can verify prices."""
    scale = VerificationScale()
    result = scale.weigh_sources(asset_symbol="BTC", reported_price=50000.0)

    assert result is not None
    assert result.sources_checked == 3


def test_privacy_vault_basic():
    """Smoke test: Privacy vault can hash data."""
    vault = PrivacyVault()
    hashed = vault.hash_user_id("user123")

    assert hashed is not None
    assert len(hashed) == 64
    assert hashed != "user123"


def test_critical_workflow_portfolio_to_signal():
    """Smoke test: Portfolio data flows to trading signals."""
    # Setup portfolio
    calendar = PortfolioCalendar()
    calendar.schedule_event(EventType.BUY, "BTC", 0.5, 50000.0)
    position = calendar.calculate_position("BTC")

    # Generate signal
    compass = TradingCompass()
    signal = compass.point_direction(
        sentiment=0.75, momentum=5.0, current_price=position["current_price"]
    )

    assert position["quantity"] > 0
    assert signal is not None


def test_critical_workflow_pattern_to_notification():
    """Smoke test: Pattern recognition triggers notifications."""
    # Recognize pattern
    dictionary = PatternDictionary()
    match = dictionary.recognize(PatternType.PRICE_SPIKE, value=0.15)

    # Set alarm
    watch = NotificationWatch()
    watch.set_alarm("price_above", 50000.0, "alert")

    # Check alarm
    triggered = watch.check_alarms(current_value=51000.0)

    assert match.detected is True
    assert len(triggered) > 0


def test_critical_workflow_security():
    """Smoke test: Security workflow functions correctly."""
    vault = PrivacyVault()

    # Hash user ID
    hashed_id = vault.hash_user_id("user123")

    # Validate query
    is_safe = vault.validate_query("SELECT * FROM portfolio_positions WHERE user_id_hash = ?")

    assert len(hashed_id) == 64
    assert is_safe is True


def test_critical_workflow_verification():
    """Smoke test: Verification workflow functions correctly."""
    scale = VerificationScale()
    result = scale.weigh_sources("BTC", 50000.0)

    assert result is not None
    assert result.sources_checked == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
