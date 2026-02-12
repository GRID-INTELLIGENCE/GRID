"""
Real-Time Portfolio Monitoring
================================
Practical example: Monitor portfolio and generate actionable insights.

Use Case: Investor wants real-time portfolio health assessment
Quality Focus: Practical relevance, accuracy, precision
"""

from datetime import datetime

from coinbase.patterns.pattern_dictionary import PatternDictionary, PatternType
from coinbase.revenue.portfolio_calendar import EventType, PortfolioCalendar
from coinbase.signals.trading_compass import TradingCompass
from coinbase.tools.notification_watch import NotificationWatch


def monitor_portfolio(user_id: str):
    """
    Monitor portfolio in real-time.

    Demonstrates: Calendar (events), Compass (signals), Dictionary (patterns), Watch (notifications)
    """
    print("=" * 60)
    print("Real-Time Portfolio Monitoring")
    print("=" * 60)
    print()

    # Initialize components
    calendar = PortfolioCalendar()
    compass = TradingCompass()
    dictionary = PatternDictionary()
    watch = NotificationWatch()

    # Simulate existing portfolio
    calendar.schedule_event(EventType.BUY, "BTC", 0.5, 50000.0, datetime(2026, 1, 15))
    calendar.schedule_event(EventType.BUY, "ETH", 2.0, 3000.0, datetime(2026, 1, 16))
    calendar.schedule_event(EventType.BUY, "BTC", 0.3, 51000.0, datetime(2026, 1, 17))

    # Calculate positions
    btc_position = calendar.calculate_position("BTC")
    eth_position = calendar.calculate_position("ETH")

    print("Portfolio Summary")
    print("-" * 40)
    print(f"BTC: {btc_position['quantity']} BTC | ${btc_position['current_value']:,.2f}")
    print(f"ETH: {eth_position['quantity']} ETH | ${eth_position['current_value']:,.2f}")
    print(f"Total Value: ${btc_position['current_value'] + eth_position['current_value']:,.2f}")
    print()

    # Check for patterns
    print("Pattern Detection")
    print("-" * 40)

    # Simulate price spike detection
    price_spike = dictionary.recognize(PatternType.PRICE_SPIKE, value=0.12)
    print(f"Price Spike: {'DETECTED' if price_spike.detected else 'None'}")

    volume_anomaly = dictionary.recognize(PatternType.VOLUME_ANOMALY, value=1.8)
    print(f"Volume Anomaly: {'DETECTED' if volume_anomaly.detected else 'None'}")
    print()

    # Generate trading signals
    print("Trading Signals")
    print("-" * 40)

    btc_signal = compass.point_direction(
        sentiment=0.75,
        momentum=5.0,
        current_price=btc_position["current_price"] / btc_position["quantity"],
    )

    print(f"BTC Signal: {btc_signal.direction.value}")
    print(f"Confidence: {btc_signal.confidence:.2f}")
    print(f"Reasoning: {btc_signal.reasoning}")
    print()

    # Set up alerts
    print("Alert Configuration")
    print("-" * 40)

    watch.set_alarm(
        condition="price_above",
        threshold=btc_position["current_price"] * 1.05,
        action="notify_user",
    )
    print(f"Alert: Price above ${btc_position['current_price'] * 1.05:,.2f}")
    print()

    # Check alerts
    print("Alert Status")
    print("-" * 40)
    triggered = watch.check_alarms(current_value=btc_position["current_price"] * 1.06)
    print(f"Active Alerts: {len(triggered)}")
    print()

    # Recommendations
    print("Recommendations")
    print("-" * 40)

    if btc_signal.direction.value in ["STRONG_BUY", "BUY"]:
        print("• BTC showing bullish momentum - consider increasing position")
    elif btc_signal.direction.value in ["STRONG_SELL", "SELL"]:
        print("• BTC showing bearish momentum - consider reducing exposure")
    else:
        print("• BTC showing neutral momentum - hold current position")

    if price_spike.detected:
        print("• Price spike detected - monitor for volatility")

    print()


if __name__ == "__main__":
    monitor_portfolio("user123")
