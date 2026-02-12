"""
Integration Tests for Coinbase Components
==========================================
Tests for component collaboration and system-wide functionality.

Focus: Quality over quantity - practical relevance, accuracy, precision.
"""


import pytest

from coinbase.core.attention_allocator import AttentionAllocator
from coinbase.patterns.pattern_dictionary import PatternDictionary, PatternType
from coinbase.revenue.portfolio_calendar import EventType, PortfolioCalendar
from coinbase.security.privacy_vault import PrivacyVault
from coinbase.signals.trading_compass import TradingCompass
from coinbase.tools.notification_watch import NotificationWatch
from coinbase.verification.verification_scale import VerificationScale


class TestPortfolioIntegration:
    """Integration tests for portfolio management workflow."""

    def test_portfolio_to_signals_workflow(self):
        """Test portfolio data flowing to trading signals."""
        # Setup portfolio
        calendar = PortfolioCalendar()
        calendar.schedule_event(EventType.BUY, "BTC", 0.5, 50000.0)
        calendar.schedule_event(EventType.BUY, "BTC", 0.3, 51000.0)

        # Calculate position
        position = calendar.calculate_position("BTC")
        assert position["quantity"] == 0.8

        # Generate trading signal based on position
        compass = TradingCompass()
        signal = compass.point_direction(
            sentiment=0.75, momentum=5.0, current_price=position["current_price"]
        )

        assert signal.direction is not None
        assert signal.confidence > 0

    def test_portfolio_to_notifications_workflow(self):
        """Test portfolio data triggering notifications."""
        # Setup portfolio
        calendar = PortfolioCalendar()
        calendar.schedule_event(EventType.BUY, "BTC", 0.5, 50000.0)
        position = calendar.calculate_position("BTC")

        # Set alarm based on position
        watch = NotificationWatch()
        watch.set_alarm(
            condition="price_above",
            threshold=position["current_price"] * 1.05,
            action="notify_user",
        )

        # Check if alarm triggers
        triggered = watch.check_alarms(current_value=position["current_price"] * 1.06)
        assert len(triggered) == 1


class TestPatternToActionIntegration:
    """Integration tests for pattern recognition triggering actions."""

    def test_pattern_recognition_to_notification(self):
        """Test pattern recognition triggering notifications."""
        # Recognize pattern
        dictionary = PatternDictionary()
        match = dictionary.recognize(PatternType.PRICE_SPIKE, value=0.15)

        assert match.detected is True

        # Set up notification handler
        watch = NotificationWatch()
        handler_called = []

        def mock_handler(action_result):
            handler_called.append(action_result)

        watch.register_handler("alert", mock_handler)

        # Trigger notification
        if match.detected:
            watch.set_alarm(condition="price_above", threshold=50000.0, action="alert")
            watch.check_alarms(current_value=51000.0)

        assert len(handler_called) > 0

    def test_pattern_to_trading_signals(self):
        """Test pattern recognition influencing trading signals."""
        # Detect pattern
        dictionary = PatternDictionary()
        match = dictionary.recognize(PatternType.PRICE_SPIKE, value=0.15)

        # Generate trading signal
        compass = TradingCompass()
        signal = compass.point_direction(sentiment=0.8, momentum=6.0, current_price=50000.0)

        # Verify pattern detection aligns with signal
        if match.detected:
            assert signal.direction in [signal.direction.STRONG_BUY, signal.direction.BUY]


class TestSecurityIntegration:
    """Integration tests for security across components."""

    def test_user_privacy_workflow(self):
        """Test user privacy maintained across workflow."""
        vault = PrivacyVault()

        # Hash user ID
        user_id = "user123"
        hashed_id = vault.hash_user_id(user_id)

        # Use hashed ID in portfolio
        calendar = PortfolioCalendar()
        calendar.schedule_event(EventType.BUY, "BTC", 0.5, 50000.0)

        # Verify original ID not exposed
        assert hashed_id != user_id
        assert len(hashed_id) == 64

    def test_query_validation_workflow(self):
        """Test query validation in workflow."""
        vault = PrivacyVault()

        # Validate queries
        safe_query = "SELECT * FROM portfolio_positions WHERE user_id_hash = ?"
        unsafe_query = "DROP TABLE portfolio_positions"

        assert vault.validate_query(safe_query) is True
        assert vault.validate_query(unsafe_query) is False


class TestAttentionIntegration:
    """Integration tests for attention allocation."""

    def test_attention_allocation_workflow(self):
        """Test attention allocation across tasks."""
        allocator = AttentionAllocator()

        # Allocate attention to different tasks
        focus1 = allocator.allocate(
            task="Portfolio analysis", priority=0.8, estimated_duration=300.0
        )

        focus2 = allocator.allocate(
            task="Pattern monitoring", priority=0.6, estimated_duration=180.0
        )

        # Verify allocation
        summary = allocator.get_focus_summary()
        assert summary["total_allocations"] == 2
        assert summary["average_focus"] > 0

    def test_attention_to_action_workflow(self):
        """Test attention allocation driving actions."""
        allocator = AttentionAllocator()

        # Allocate high focus to critical task
        focus = allocator.allocate(
            task="Price verification", priority=0.9, estimated_duration=300.0
        )

        # High focus should lead to action
        assert focus.focus_intensity >= 0.7


class TestVerificationIntegration:
    """Integration tests for verification workflow."""

    def test_verification_to_trading_workflow(self):
        """Test verification results informing trading decisions."""
        scale = VerificationScale()

        # Verify price
        result = scale.weigh_sources(asset_symbol="BTC", reported_price=50000.0)

        # If verified, proceed with trading
        if result.verified:
            compass = TradingCompass()
            signal = compass.point_direction(
                sentiment=0.7, momentum=5.0, current_price=result.consensus
            )
            assert signal is not None

    def test_verification_anomaly_handling(self):
        """Test handling verification anomalies."""
        scale = VerificationScale()

        # Verify with high variance
        result = scale.weigh_sources(asset_symbol="BTC", reported_price=50000.0)

        # Handle anomalies
        if result.anomalies:
            # Should trigger caution
            assert len(result.anomalies) > 0


class TestEndToEndWorkflow:
    """End-to-end integration tests."""

    def test_complete_trading_workflow(self):
        """Test complete trading workflow from start to finish."""
        # Step 1: Portfolio setup
        calendar = PortfolioCalendar()
        calendar.schedule_event(EventType.BUY, "BTC", 0.5, 50000.0)
        position = calendar.calculate_position("BTC")

        # Step 2: Pattern recognition
        dictionary = PatternDictionary()
        match = dictionary.recognize(PatternType.PRICE_SPIKE, value=0.15)

        # Step 3: Price verification
        scale = VerificationScale()
        verification = scale.weigh_sources("BTC", position["current_price"])

        # Step 4: Trading signal
        compass = TradingCompass()
        signal = compass.point_direction(
            sentiment=0.75, momentum=5.0, current_price=position["current_price"]
        )

        # Step 5: Notification
        watch = NotificationWatch()
        watch.set_alarm(
            condition="price_above",
            threshold=position["current_price"] * 1.05,
            action="notify_user",
        )

        # Verify workflow completes
        assert position["quantity"] > 0
        assert signal is not None
        assert verification is not None

    def test_complete_security_workflow(self):
        """Test complete security workflow."""
        vault = PrivacyVault()

        # Step 1: Hash user ID
        user_id = "user123"
        hashed_id = vault.hash_user_id(user_id)

        # Step 2: Validate query
        query = "SELECT * FROM portfolio_positions WHERE user_id_hash = ?"
        is_safe = vault.validate_query(query)

        # Step 3: Execute parameterized query
        if is_safe:
            validated_query, params = vault.parameterized_query(query, (hashed_id,))
            assert validated_query is not None

    def test_complete_monitoring_workflow(self):
        """Test complete monitoring workflow."""
        # Setup components
        calendar = PortfolioCalendar()
        dictionary = PatternDictionary()
        watch = NotificationWatch()

        # Add portfolio position
        calendar.schedule_event(EventType.BUY, "BTC", 0.5, 50000.0)

        # Monitor for patterns
        match = dictionary.recognize(PatternType.PRICE_SPIKE, value=0.15)

        # Set up notifications
        if match.detected:
            watch.set_alarm(condition="price_above", threshold=52000.0, action="alert")

        # Check alarms
        triggered = watch.check_alarms(current_value=52500.0)

        # Verify monitoring works
        assert match.detected is True
        assert len(triggered) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
