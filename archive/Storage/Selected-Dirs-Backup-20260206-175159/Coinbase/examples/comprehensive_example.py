"""
Coinbase Comprehensive Example
===============================
Demonstrates all components working together.

This example shows how the fundamental references (Compass, Calendar, Dictionary,
Scale, Watch, Vault) collaborate to create a powerful crypto investment platform.
"""

import os

from coinbase.core.attention_allocator import AttentionAllocator
from coinbase.infrastructure.databricks_analyzer import DatabricksAnalyzer
from coinbase.infrastructure.databricks_connector import DatabricksConnector
from coinbase.patterns.pattern_dictionary import PatternDictionary, PatternType
from coinbase.revenue.portfolio_calendar import EventType, PortfolioCalendar
from coinbase.security.privacy_vault import PrivacyVault
from coinbase.signals.trading_compass import TradingCompass
from coinbase.tools.notification_watch import NotificationWatch
from coinbase.verification.verification_scale import VerificationScale


def main():
    """Run comprehensive example."""
    print("=" * 60)
    print("Coinbase Comprehensive Example")
    print("=" * 60)
    print()

    # Check for Databricks credentials
    has_credentials = all(
        [
            os.getenv("DATABRICKS_HOST"),
            os.getenv("DATABRICKS_HTTP_PATH"),
            os.getenv("DATABRICKS_TOKEN"),
        ]
    )

    if not has_credentials:
        print("⚠ Databricks credentials not found")
        print("Running in demo mode without database connection\n")

    # Step 1: Initialize Components
    print("Step 1: Initialize Components")
    print("-" * 40)

    # Compass pattern: Databricks connection
    connector = DatabricksConnector() if has_credentials else None
    analyzer = DatabricksAnalyzer(connector) if has_credentials else None
    print("✓ Databricks Connector (Compass)")

    # Compass pattern: Trading signals
    trading_compass = TradingCompass()
    print("✓ Trading Compass (Compass)")

    # Calendar pattern: Portfolio tracking
    portfolio_calendar = PortfolioCalendar()
    print("✓ Portfolio Calendar (Calendar)")

    # Dictionary pattern: Pattern recognition
    pattern_dictionary = PatternDictionary()
    print("✓ Pattern Dictionary (Dictionary)")

    # Watch pattern: Notifications
    notification_watch = NotificationWatch()
    print("✓ Notification Watch (Watch)")

    # Scale pattern: Verification
    verification_scale = VerificationScale()
    print("✓ Verification Scale (Scale)")

    # Vault pattern: Security
    privacy_vault = PrivacyVault()
    print("✓ Privacy Vault (Vault)")

    print()

    # Step 2: Portfolio Management
    print("Step 2: Portfolio Management (Calendar)")
    print("-" * 40)

    # Schedule buy events
    portfolio_calendar.schedule_event(
        event_type=EventType.BUY, asset_symbol="BTC", quantity=0.5, price=50000.0
    )
    print("✓ Bought 0.5 BTC @ $50,000")

    portfolio_calendar.schedule_event(
        event_type=EventType.BUY, asset_symbol="ETH", quantity=2.0, price=3000.0
    )
    print("✓ Bought 2.0 ETH @ $3,000")

    # Calculate positions
    btc_position = portfolio_calendar.calculate_position("BTC")
    print(f"\nBTC Position: {btc_position['quantity']} BTC")
    print(f"  Value: ${btc_position['current_value']:,.2f}")
    print(f"  PnL: ${btc_position['unrealized_pnl']:,.2f} ({btc_position['pnl_percentage']:.2f}%)")

    print()

    # Step 3: Trading Signals (Compass)
    print("Step 3: Trading Signals (Compass)")
    print("-" * 40)

    # Generate trading signal
    signal = trading_compass.point_direction(sentiment=0.75, momentum=5.0, current_price=51000.0)
    print(f"Direction: {signal.direction.value}")
    print(f"Confidence: {signal.confidence:.2f}")
    print(f"Reasoning: {signal.reasoning}")
    if signal.target_price:
        print(f"Target: ${signal.target_price:,.2f}")
    if signal.stop_loss:
        print(f"Stop Loss: ${signal.stop_loss:,.2f}")

    print()

    # Step 4: Pattern Recognition (Dictionary)
    print("Step 4: Pattern Recognition (Dictionary)")
    print("-" * 40)

    # Check for price spike
    price_spike = pattern_dictionary.recognize(PatternType.PRICE_SPIKE, value=0.15)
    print(f"Price Spike: {price_spike.detected} | Confidence: {price_spike.confidence:.2f}")

    # Check for volume anomaly
    volume_anomaly = pattern_dictionary.recognize(PatternType.VOLUME_ANOMALY, value=1.5)
    print(
        f"Volume Anomaly: {volume_anomaly.detected} | Confidence: {volume_anomaly.confidence:.2f}"
    )

    print()

    # Step 5: Notifications (Watch)
    print("Step 5: Notifications (Watch)")
    print("-" * 40)

    # Set price alarm
    notification_watch.set_alarm(condition="price_above", threshold=52000.0, action="notify_user")
    print("✓ Alarm set: Price above $52,000")

    # Check alarms
    triggered = notification_watch.check_alarms(current_value=52500.0)
    print(f"Triggered actions: {len(triggered)}")

    print()

    # Step 6: Price Verification (Scale)
    print("Step 6: Price Verification (Scale)")
    print("-" * 40)

    # Verify price
    verification = verification_scale.weigh_sources(asset_symbol="BTC", reported_price=51000.0)
    print(f"Verified: {verification.verified}")
    print(f"Consensus: ${verification.consensus:,.2f}")
    print(f"Sources: {verification.sources_checked}/{verification.sources_verified}")

    if verification.anomalies:
        print("\nAnomalies:")
        for anomaly in verification.anomalies:
            print(f"  - {anomaly}")

    print()

    # Step 7: Security (Vault)
    print("Step 7: Security (Vault)")
    print("-" * 40)

    # Hash user ID
    user_id = "user123"
    hashed_id = privacy_vault.hash_user_id(user_id)
    print(f"User ID: {user_id}")
    print(f"Hashed: {hashed_id[:16]}...")

    # Validate query
    safe_query = "SELECT * FROM portfolio_positions WHERE user_id_hash = ?"
    is_safe = privacy_vault.validate_query(safe_query)
    print(f"\nQuery safe: {is_safe}")

    print()

    # Step 8: Attention Allocation (Compass)
    print("Step 8: Attention Allocation (Compass)")
    print("-" * 40)

    attention_allocator = AttentionAllocator()

    # Allocate focus to high priority task
    focus = attention_allocator.allocate(
        task="Portfolio optimization", priority=0.8, estimated_duration=300.0
    )
    print(f"Task: {focus.task}")
    print(f"Priority: {focus.priority:.2f}")
    print(f"Focus: {focus.focus_intensity:.2f}")
    print(f"Direction: {focus.direction}")

    # Get summary
    summary = attention_allocator.get_focus_summary()
    print(f"\nTotal allocations: {summary['total_allocations']}")
    print(f"Average focus: {summary['average_focus']:.2f}")

    print()

    # Summary
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print("All components working in unison:")
    print("  • Compass (Databricks, Trading) - Direction and connection")
    print("  • Calendar (Portfolio) - Event tracking")
    print("  • Dictionary (Patterns) - Recognition and translation")
    print("  • Scale (Verification) - Weighing sources")
    print("  • Watch (Notifications) - Alarms and alerts")
    print("  • Vault (Security) - Privacy and protection")
    print()
    print("Wide proximity of expertise achieved through collaboration.")
    print()


if __name__ == "__main__":
    main()
