"""
Coinbase Platform - Quick Start Guide
=====================================
Practical guide to using Coinbase for crypto investment analysis.

Quality Focus: Practical relevance, accuracy, precision, fluency
"""

import os

from coinbase.core.attention_allocator import AttentionAllocator
from coinbase.patterns.pattern_dictionary import PatternDictionary, PatternType
from coinbase.revenue.portfolio_calendar import EventType, PortfolioCalendar
from coinbase.security.privacy_vault import PrivacyVault
from coinbase.signals.trading_compass import TradingCompass
from coinbase.tools.notification_watch import NotificationWatch
from coinbase.verification.verification_scale import VerificationScale


def quick_start():
    """
    Quick start guide demonstrating Coinbase platform.

    Shows how to:
    1. Set up portfolio
    2. Monitor positions
    3. Generate trading signals
    4. Verify prices
    5. Set up alerts
    """
    print("=" * 70)
    print("Coinbase Platform - Quick Start Guide")
    print("=" * 70)
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
        print("⚠ Databricks credentials not configured")
        print("Set DATABRICKS_HOST, DATABRICKS_HTTP_PATH, DATABRICKS_TOKEN")
        print("Running in demo mode without database connection\n")

    # Initialize components
    print("Step 1: Initialize Components")
    print("-" * 70)

    allocator = AttentionAllocator()
    calendar = PortfolioCalendar()
    dictionary = PatternDictionary()
    watch = NotificationWatch()
    compass = TradingCompass()
    scale = VerificationScale()
    vault = PrivacyVault()

    print("✓ All components initialized\n")

    # Set up portfolio
    print("Step 2: Set Up Portfolio")
    print("-" * 70)

    # Add positions
    calendar.schedule_event(EventType.BUY, "BTC", 0.5, 50000.0)
    calendar.schedule_event(EventType.BUY, "ETH", 2.0, 3000.0)

    # Calculate positions
    btc_position = calendar.calculate_position("BTC")
    eth_position = calendar.calculate_position("ETH")

    print(f"BTC: {btc_position['quantity']} BTC | ${btc_position['current_value']:,.2f}")
    print(f"ETH: {eth_position['quantity']} ETH | ${eth_position['current_value']:,.2f}")
    print(f"Total: ${btc_position['current_value'] + eth_position['current_value']:,.2f}\n")

    # Generate trading signals
    print("Step 3: Generate Trading Signals")
    print("-" * 70)

    signal = compass.point_direction(sentiment=0.75, momentum=5.0, current_price=50000.0)

    print(f"Signal: {signal.direction.value}")
    print(f"Confidence: {signal.confidence:.2f}")
    print(f"Reasoning: {signal.reasoning}\n")

    # Verify prices
    print("Step 4: Verify Prices")
    print("-" * 70)

    verification = scale.weigh_sources("BTC", 50000.0)

    print(f"Verified: {verification.verified}")
    print(f"Consensus: ${verification.consensus:,.2f}")
    print(f"Sources: {verification.sources_checked}/{verification.sources_verified}\n")

    # Set up alerts
    print("Step 5: Set Up Alerts")
    print("-" * 70)

    watch.set_alarm("price_above", 52000.0, "notify_user")
    print("✓ Alert configured: Price above $52,000\n")

    # Detect patterns
    print("Step 6: Detect Patterns")
    print("-" * 70)

    match = dictionary.recognize(PatternType.PRICE_SPIKE, value=0.15)
    print(f"Price Spike: {'DETECTED' if match.detected else 'None'}\n")

    # Security check
    print("Step 7: Security Check")
    print("-" * 70)

    hashed_id = vault.hash_user_id("user123")
    print(f"User ID hashed: {hashed_id[:16]}...\n")

    # Summary
    print("=" * 70)
    print("Quick Start Complete")
    print("=" * 70)
    print("\nNext Steps:")
    print("• Run examples/portfolio_monitoring.py for real-time monitoring")
    print("• Run examples/trading_signals.py for signal generation")
    print("• Run examples/comprehensive_demo.py for complete workflow")
    print("• Configure Databricks credentials for database operations")
    print()


if __name__ == "__main__":
    quick_start()
