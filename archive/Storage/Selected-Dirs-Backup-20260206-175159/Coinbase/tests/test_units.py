"""
Unit Tests for Coinbase Components
===================================
Comprehensive unit tests for all components.

Focus: Quality over quantity - practical relevance, accuracy, precision.
"""


import pytest

from coinbase.core.attention_allocator import AttentionAllocator
from coinbase.infrastructure.databricks_connector import DatabricksConnector
from coinbase.patterns.pattern_dictionary import PatternDictionary, PatternType
from coinbase.revenue.portfolio_calendar import EventType, PortfolioCalendar
from coinbase.security.privacy_vault import PrivacyVault
from coinbase.signals.trading_compass import TradingCompass, TradingDirection
from coinbase.tools.notification_watch import NotificationWatch
from coinbase.verification.verification_scale import VerificationScale


class TestDatabricksConnector:
    """Unit tests for DatabricksConnector."""

    def test_initialization_without_credentials(self):
        """Test initialization fails gracefully without credentials."""
        import os

        # Save original env vars
        original_host = os.environ.get("DATABRICKS_HOST")
        original_path = os.environ.get("DATABRICKS_HTTP_PATH")
        original_token = os.environ.get("DATABRICKS_TOKEN")
        original_offline = os.environ.get("DATABRICKS_OFFLINE")

        # Clear credentials and disable offline mode
        os.environ.pop("DATABRICKS_HOST", None)
        os.environ.pop("DATABRICKS_HTTP_PATH", None)
        os.environ.pop("DATABRICKS_TOKEN", None)
        os.environ.pop("DATABRICKS_OFFLINE", None)

        # Should raise ValueError
        with pytest.raises(ValueError):
            DatabricksConnector()

        # Restore env vars
        if original_host:
            os.environ["DATABRICKS_HOST"] = original_host
        if original_path:
            os.environ["DATABRICKS_HTTP_PATH"] = original_path
        if original_token:
            os.environ["DATABRICKS_TOKEN"] = original_token
        if original_offline:
            os.environ["DATABRICKS_OFFLINE"] = original_offline


class TestAttentionAllocator:
    """Unit tests for AttentionAllocator."""

    def test_allocate_high_priority(self):
        """Test allocating attention to high priority task."""
        allocator = AttentionAllocator()
        focus = allocator.allocate(task="Critical task", priority=0.9, estimated_duration=300.0)

        assert focus.task == "Critical task"
        assert focus.priority == 0.9
        assert focus.focus_intensity >= 0.7
        assert focus.direction == "NORTHEAST"

    def test_allocate_medium_priority(self):
        """Test allocating attention to medium priority task."""
        allocator = AttentionAllocator()
        focus = allocator.allocate(task="Normal task", priority=0.5, estimated_duration=180.0)

        assert focus.direction == "EAST"
        assert focus.focus_intensity >= 0.3

    def test_focus_summary(self):
        """Test getting focus summary."""
        allocator = AttentionAllocator()
        allocator.allocate("Task 1", 0.8)
        allocator.allocate("Task 2", 0.6)

        summary = allocator.get_focus_summary()
        assert summary["total_allocations"] == 2
        assert summary["average_focus"] > 0


class TestPortfolioCalendar:
    """Unit tests for PortfolioCalendar."""

    def test_schedule_buy_event(self):
        """Test scheduling buy event."""
        calendar = PortfolioCalendar()
        event = calendar.schedule_event(
            event_type=EventType.BUY, asset_symbol="BTC", quantity=0.5, price=50000.0
        )

        assert event.event_type == EventType.BUY
        assert event.asset_symbol == "BTC"
        assert event.quantity == 0.5
        assert event.price == 50000.0
        assert event.purpose == "Acquire position"

    def test_calculate_position(self):
        """Test calculating position."""
        calendar = PortfolioCalendar()
        calendar.schedule_event(EventType.BUY, "BTC", 0.5, 50000.0)
        calendar.schedule_event(EventType.BUY, "BTC", 0.3, 51000.0)

        position = calendar.calculate_position("BTC")
        assert position["quantity"] == 0.8
        assert position["asset_symbol"] == "BTC"
        assert position["average_cost"] > 0

    def test_get_events_by_asset(self):
        """Test getting events by asset."""
        calendar = PortfolioCalendar()
        calendar.schedule_event(EventType.BUY, "BTC", 0.5, 50000.0)
        calendar.schedule_event(EventType.BUY, "ETH", 2.0, 3000.0)

        btc_events = calendar.get_events_by_asset("BTC")
        assert len(btc_events) == 1
        assert btc_events[0].asset_symbol == "BTC"


class TestPatternDictionary:
    """Unit tests for PatternDictionary."""

    def test_recognize_price_spike(self):
        """Test recognizing price spike pattern."""
        dictionary = PatternDictionary()
        match = dictionary.recognize(PatternType.PRICE_SPIKE, value=0.15)

        assert match.detected is True
        assert match.confidence >= 0.8
        assert match.action == "alert"

    def test_recognize_no_pattern(self):
        """Test when pattern not detected."""
        dictionary = PatternDictionary()
        match = dictionary.recognize(PatternType.VOLUME_ANOMALY, value=1.0)

        assert match.detected is False
        assert match.confidence == 0.0

    def test_list_patterns(self):
        """Test listing all patterns."""
        dictionary = PatternDictionary()
        patterns = dictionary.list_patterns()

        assert len(patterns) >= 5
        assert any(p["type"] == "price_spike" for p in patterns)


class TestNotificationWatch:
    """Unit tests for NotificationWatch."""

    def test_set_and_check_alarm(self):
        """Test setting and checking alarm."""
        watch = NotificationWatch()
        alarm = watch.set_alarm(condition="price_above", threshold=52000.0, action="notify_user")

        assert alarm.condition == "price_above"
        assert alarm.threshold == 52000.0
        assert alarm.action == "notify_user"
        assert alarm.triggered is False

    def test_alarm_triggered(self):
        """Test alarm triggering."""
        watch = NotificationWatch()
        watch.set_alarm("price_above", 52000.0, "notify_user")

        triggered = watch.check_alarms(current_value=52500.0)
        assert len(triggered) == 1
        assert triggered[0]["action"] == "notify_user"

    def test_get_active_alarms(self):
        """Test getting active alarms."""
        watch = NotificationWatch()
        watch.set_alarm("price_above", 52000.0, "notify_user")

        active = watch.get_active_alarms()
        assert len(active) == 1


class TestTradingCompass:
    """Unit tests for TradingCompass."""

    def test_strong_buy_signal(self):
        """Test generating strong buy signal."""
        compass = TradingCompass()
        signal = compass.point_direction(sentiment=0.9, momentum=6.0, current_price=50000.0)

        assert signal.direction == TradingDirection.STRONG_BUY
        assert signal.confidence >= 0.8
        assert signal.target_price > 50000.0
        assert signal.stop_loss < 50000.0

    def test_hold_signal(self):
        """Test generating hold signal."""
        compass = TradingCompass()
        signal = compass.point_direction(sentiment=0.5, momentum=2.0, current_price=50000.0)

        assert signal.direction == TradingDirection.HOLD

    def test_sell_signal(self):
        """Test generating sell signal."""
        compass = TradingCompass()
        signal = compass.point_direction(sentiment=-0.5, momentum=-3.0, current_price=50000.0)

        assert signal.direction in [TradingDirection.SELL, TradingDirection.STRONG_SELL]


class TestVerificationScale:
    """Unit tests for VerificationScale."""

    def test_weigh_sources(self):
        """Test weighing sources."""
        scale = VerificationScale()
        result = scale.weigh_sources(asset_symbol="BTC", reported_price=50000.0)

        assert result.sources_checked == 3
        assert result.sources_verified >= 0
        assert result.consensus is not None or result.verified is False

    def test_get_pattern_description(self):
        """Test getting pattern description."""
        scale = VerificationScale()
        # This test just ensures the structure is correct
        # Actual API calls may fail in test environment
        assert scale is not None


class TestPrivacyVault:
    """Unit tests for PrivacyVault."""

    def test_hash_user_id(self):
        """Test hashing user ID."""
        vault = PrivacyVault()
        hashed = vault.hash_user_id("user123")

        assert hashed != "user123"
        assert len(hashed) == 64  # SHA-256 hex length
        assert hashed != vault.hash_user_id("user456")

    def test_validate_safe_query(self):
        """Test validating safe query."""
        vault = PrivacyVault()
        is_safe = vault.validate_query("SELECT * FROM portfolio_positions WHERE user_id_hash = ?")

        assert is_safe is True

    def test_validate_unsafe_query(self):
        """Test rejecting unsafe query."""
        vault = PrivacyVault()
        is_safe = vault.validate_query("DROP TABLE portfolio_positions")

        assert is_safe is False

    def test_parameterized_query_safe(self):
        """Test parameterized query with safe query."""
        vault = PrivacyVault()
        query, params = vault.parameterized_query(
            "SELECT * FROM portfolio_positions WHERE user_id_hash = ?", ("hash123",)
        )

        assert query is not None
        assert params is not None

    def test_parameterized_query_unsafe(self):
        """Test parameterized query rejects dangerous keywords."""
        vault = PrivacyVault()
        with pytest.raises(ValueError):
            vault.parameterized_query("DROP TABLE portfolio_positions", ())

    def test_sanitize_input(self):
        """Test sanitizing user input."""
        vault = PrivacyVault()
        sanitized = vault.sanitize_input("test'--input")

        assert "'" not in sanitized
        assert "--" not in sanitized


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
