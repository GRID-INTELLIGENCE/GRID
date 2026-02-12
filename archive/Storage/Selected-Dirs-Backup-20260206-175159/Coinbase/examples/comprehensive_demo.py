"""
Comprehensive Trading Demo
==========================
Practical example: Complete trading workflow from analysis to action.

Use Case: Complete trading decision-making process
Quality Focus: Practical relevance, accuracy, precision, fluency
"""

from datetime import datetime

from coinbase.core.attention_allocator import AttentionAllocator
from coinbase.patterns.pattern_dictionary import PatternDictionary, PatternType
from coinbase.revenue.portfolio_calendar import EventType, PortfolioCalendar
from coinbase.security.privacy_vault import PrivacyVault
from coinbase.signals.trading_compass import TradingCompass
from coinbase.tools.notification_watch import NotificationWatch
from coinbase.verification.verification_scale import VerificationScale


def comprehensive_trading_demo():
    """
    Complete trading workflow demonstration.

    Demonstrates: All components working in unison
    - Compass: Direction and connection
    - Calendar: Event tracking
    - Dictionary: Pattern recognition
    - Scale: Verification
    - Watch: Notifications
    - Vault: Security
    """
    print("=" * 70)
    print("Coinbase Trading Demo - Complete Workflow")
    print("=" * 70)
    print()

    # Initialize all components
    print("Initializing Components...")
    print("-" * 70)

    allocator = AttentionAllocator()
    calendar = PortfolioCalendar()
    dictionary = PatternDictionary()
    watch = NotificationWatch()
    compass = TradingCompass()
    scale = VerificationScale()
    vault = PrivacyVault()

    print("✓ All components initialized")
    print()

    # Step 1: Allocate attention
    print("Step 1: Attention Allocation")
    print("-" * 70)

    focus = allocator.allocate(
        task="Portfolio analysis and trading decision", priority=0.85, estimated_duration=300.0
    )

    print(f"Task: {focus.task}")
    print(f"Priority: {focus.priority:.2f}")
    print(f"Focus Intensity: {focus.focus_intensity:.2f}")
    print(f"Direction: {focus.direction}")
    print()

    # Step 2: Portfolio assessment
    print("Step 2: Portfolio Assessment")
    print("-" * 70)

    # Simulate existing portfolio
    calendar.schedule_event(EventType.BUY, "BTC", 0.5, 50000.0, datetime(2026, 1, 15))
    calendar.schedule_event(EventType.BUY, "ETH", 2.0, 3000.0, datetime(2026, 1, 16))

    btc_position = calendar.calculate_position("BTC")
    eth_position = calendar.calculate_position("ETH")

    total_value = btc_position["current_value"] + eth_position["current_value"]

    print(f"BTC Position: {btc_position['quantity']} BTC | ${btc_position['current_value']:,.2f}")
    print(f"ETH Position: {eth_position['quantity']} ETH | ${eth_position['current_value']:,.2f}")
    print(f"Total Portfolio Value: ${total_value:,.2f}")
    print()

    # Step 3: Pattern detection
    print("Step 3: Pattern Detection")
    print("-" * 70)

    price_spike = dictionary.recognize(PatternType.PRICE_SPIKE, value=0.12)
    volume_anomaly = dictionary.recognize(PatternType.VOLUME_ANOMALY, value=1.8)
    sentiment_shift = dictionary.recognize(PatternType.SENTIMENT_SHIFT, value=0.65)

    print(f"Price Spike: {'DETECTED' if price_spike.detected else 'None'}")
    print(f"Volume Anomaly: {'DETECTED' if volume_anomaly.detected else 'None'}")
    print(f"Sentiment Shift: {'DETECTED' if sentiment_shift.detected else 'None'}")
    print()

    # Step 4: Price verification
    print("Step 4: Price Verification")
    print("-" * 70)

    verification = scale.weigh_sources(
        "BTC", btc_position["current_price"] / btc_position["quantity"]
    )

    print(f"Verified: {verification.verified}")
    print(f"Consensus Price: ${verification.consensus:,.2f}")
    print(f"Sources Checked: {verification.sources_checked}/{verification.sources_verified}")

    if verification.anomalies:
        print("Anomalies Detected:")
        for anomaly in verification.anomalies:
            print(f"  - {anomaly}")
    print()

    # Step 5: Trading signal generation
    print("Step 5: Trading Signal Generation")
    print("-" * 70)

    # Use verified price or current price
    price_to_use = (
        verification.consensus
        if verification.verified
        else (btc_position["current_price"] / btc_position["quantity"])
    )

    signal = compass.point_direction(sentiment=0.75, momentum=5.0, current_price=price_to_use)

    print(f"Direction: {signal.direction.value}")
    print(f"Confidence: {signal.confidence:.2f}")
    print(f"Reasoning: {signal.reasoning}")

    if signal.target_price:
        print(f"Target Price: ${signal.target_price:,.2f}")
    if signal.stop_loss:
        print(f"Stop Loss: ${signal.stop_loss:,.2f}")
    print()

    # Step 6: Alert configuration
    print("Step 6: Alert Configuration")
    print("-" * 70)

    if signal.target_price:
        watch.set_alarm(
            condition="price_above", threshold=signal.target_price, action="notify_user"
        )
        print(f"Alert: Price above ${signal.target_price:,.2f}")

    if signal.stop_loss:
        watch.set_alarm(condition="price_below", threshold=signal.stop_loss, action="send_alert")
        print(f"Alert: Price below ${signal.stop_loss:,.2f}")
    print()

    # Step 7: Security check
    print("Step 7: Security Check")
    print("-" * 70)

    user_id = "user123"
    hashed_id = vault.hash_user_id(user_id)

    print(f"User ID: {user_id}")
    print(f"Hashed ID: {hashed_id[:16]}...")

    query = "SELECT * FROM portfolio_positions WHERE user_id_hash = ?"
    is_safe = vault.validate_query(query)

    print(f"Query Safe: {is_safe}")
    print()

    # Step 8: Final recommendation
    print("Step 8: Final Recommendation")
    print("-" * 70)

    print("\nBased on analysis:")
    print(f"• Portfolio Value: ${total_value:,.2f}")
    print(f"• Trading Signal: {signal.direction.value}")
    print(f"• Confidence: {signal.confidence:.2f}")
    print(f"• Price Verified: {verification.verified}")

    print("\nRecommendations:")

    if signal.direction.value in ["STRONG_BUY", "BUY"]:
        print(f"• {signal.direction.value} signal - Consider increasing BTC position")
        print(f"• Set stop loss at ${signal.stop_loss:,.2f}")
        print(f"• Target price: ${signal.target_price:,.2f}")
    elif signal.direction.value in ["STRONG_SELL", "SELL"]:
        print(f"• {signal.direction.value} signal - Consider reducing BTC position")
        print(f"• Set stop loss at ${signal.stop_loss:,.2f}")
    else:
        print("• HOLD signal - Maintain current position")
        print("• Monitor for changes")

    if price_spike.detected:
        print("• Price spike detected - Monitor for volatility")

    if not verification.verified:
        print("• Price verification failed - Exercise caution")

    print()

    # Summary
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print("Components Utilized:")
    print("  • Attention Allocator - Focus allocation")
    print("  • Portfolio Calendar - Event tracking")
    print("  • Pattern Dictionary - Pattern recognition")
    print("  • Verification Scale - Price verification")
    print("  • Trading Compass - Signal generation")
    print("  • Notification Watch - Alert management")
    print("  • Privacy Vault - Security")
    print()
    print("Workflow: Portfolio → Patterns → Verification → Signal → Action")
    print()


if __name__ == "__main__":
    comprehensive_trading_demo()
