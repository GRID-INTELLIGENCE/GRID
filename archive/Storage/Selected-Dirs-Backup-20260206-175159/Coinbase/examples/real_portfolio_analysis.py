"""
Real Portfolio Analysis
========================
Analyze real Yahoo Finance portfolio data.

Use Case: Analyze actual portfolio and generate actionable insights
Quality Focus: Practical relevance, accuracy, precision with real data
"""

from coinbase.integrations.yahoo_finance import YahooPortfolioParser
from coinbase.patterns.pattern_dictionary import PatternDictionary
from coinbase.signals.trading_compass import TradingCompass
from coinbase.tools.notification_watch import NotificationWatch


def analyze_real_portfolio(csv_path: str):
    """
    Analyze real Yahoo Finance portfolio.

    Demonstrates: Real data analysis, signal generation, actionable insights
    """
    print("=" * 70)
    print("Real Portfolio Analysis - Yahoo Finance Data")
    print("=" * 70)
    print()

    # Parse portfolio
    print("Step 1: Parse Portfolio Data")
    print("-" * 70)

    parser = YahooPortfolioParser(csv_path)
    positions = parser.parse()

    summary = parser.get_portfolio_summary()

    print(f"Total Positions: {summary['total_positions']}")
    print(f"Total Value: ${summary['total_value']:,.2f}")
    print(f"Total Purchase Value: ${summary['total_purchase_value']:,.2f}")
    print(f"Total Gain/Loss: ${summary['total_gain_loss']:,.2f}")
    print(f"Gain/Loss %: {summary['gain_loss_percentage']:.2f}%")
    print()

    # Top performers
    print("Step 2: Top Performers")
    print("-" * 70)

    top_performers = parser.get_top_performers(5)
    for i, pos in enumerate(top_performers, 1):
        print(f"{i}. {pos.symbol}")
        print(f"   Gain/Loss: {pos.gain_loss_percentage:.2f}% | ${pos.total_gain_loss:,.2f}")
        print(f"   Quantity: {pos.quantity} | Value: ${pos.current_value:,.2f}")
        if pos.comment:
            print(f"   Note: {pos.comment[:80]}...")
    print()

    # Worst performers
    print("Step 3: Worst Performers")
    print("-" * 70)

    worst_performers = parser.get_worst_performers(5)
    for i, pos in enumerate(worst_performers, 1):
        print(f"{i}. {pos.symbol}")
        print(f"   Gain/Loss: {pos.gain_loss_percentage:.2f}% | ${pos.total_gain_loss:,.2f}")
        print(f"   Quantity: {pos.quantity} | Value: ${pos.current_value:,.2f}")
        if pos.high_limit:
            print(f"   High Limit: ${pos.high_limit:,.2f}")
        if pos.low_limit:
            print(f"   Low Limit: ${pos.low_limit:,.2f}")
    print()

    # Generate trading signals
    print("Step 4: Trading Signals")
    print("-" * 70)

    compass = TradingCompass()

    # Generate signals for top positions
    print("Top Positions - Trading Signals:")
    for pos in top_performers[:3]:
        signal = compass.point_direction(
            sentiment=0.75, momentum=5.0, current_price=pos.current_price
        )
        print(f"\n{pos.symbol}:")
        print(f"  Signal: {signal.direction.value}")
        print(f"  Confidence: {signal.confidence:.2f}")
        print(f"  Current: ${pos.current_price:,.2f} | PnL: {pos.gain_loss_percentage:.2f}%")
    print()

    # Pattern detection
    print("Step 5: Pattern Detection")
    print("-" * 70)

    dictionary = PatternDictionary()

    # Check for patterns in portfolio
    print("Portfolio Patterns:")

    # Check for concentration risk
    if summary["total_positions"] < 10:
        print("• Concentration Risk: High (few positions)")

    # Check for performance patterns
    if summary["gain_loss_percentage"] > 10:
        print("• Performance Pattern: Strong upward trend")
    elif summary["gain_loss_percentage"] < 0:
        print("• Performance Pattern: Underperforming")

    # Check position-specific patterns
    for pos in positions:
        if pos.gain_loss_percentage > 20:
            print(f"• {pos.symbol}: Strong performer (+{pos.gain_loss_percentage:.2f}%)")
        elif pos.gain_loss_percentage < -10:
            print(f"• {pos.symbol}: Underperformer ({pos.gain_loss_percentage:.2f}%)")
    print()

    # Alert configuration
    print("Step 6: Alert Configuration")
    print("-" * 70)

    watch = NotificationWatch()

    # Set alerts for positions with limits
    alerts_set = 0
    for pos in positions:
        if pos.high_limit:
            watch.set_alarm(condition="price_above", threshold=pos.high_limit, action="notify_user")
            print(f"• {pos.symbol}: Alert at ${pos.high_limit:,.2f}")
            alerts_set += 1

        if pos.low_limit:
            watch.set_alarm(condition="price_below", threshold=pos.low_limit, action="send_alert")
            print(f"• {pos.symbol}: Alert at ${pos.low_limit:,.2f}")
            alerts_set += 1

    if alerts_set == 0:
        print("No limits set in portfolio data")
    print()

    # Recommendations
    print("Step 7: Recommendations")
    print("-" * 70)

    print("\nBased on analysis:")

    # Portfolio-level recommendations
    if summary["gain_loss_percentage"] > 10:
        print("• Portfolio performing well - consider taking partial profits")
    elif summary["gain_loss_percentage"] < 0:
        print("• Portfolio underperforming - review holdings")

    # Position-level recommendations
    print("\nPosition Recommendations:")

    for pos in top_performers[:3]:
        if pos.gain_loss_percentage > 20:
            print(f"• {pos.symbol}: Strong performer - consider taking profits")
        elif pos.gain_loss_percentage > 10:
            print(f"• {pos.symbol}: Good performer - hold position")

    for pos in worst_performers[:3]:
        if pos.gain_loss_percentage < -10:
            print(f"• {pos.symbol}: Underperforming - consider reducing exposure")
        elif pos.gain_loss_percentage < 0:
            print(f"• {pos.symbol}: Slight loss - monitor closely")

    # Risk assessment
    print("\nRisk Assessment:")

    if summary["total_positions"] < 10:
        print("• Concentration Risk: High - diversify portfolio")

    # Check for high volatility positions
    high_volatility = [p for p in positions if abs(p.gain_loss_percentage) > 15]
    if high_volatility:
        print(f"• Volatility Risk: {len(high_volatility)} positions with high volatility")

    print()

    # Summary
    print("=" * 70)
    print("Analysis Complete")
    print("=" * 70)
    print(f"\nPortfolio Value: ${summary['total_value']:,.2f}")
    print(
        f"Total Gain/Loss: ${summary['total_gain_loss']:,.2f} ({summary['gain_loss_percentage']:.2f}%)"
    )
    print(f"Positions Analyzed: {summary['total_positions']}")
    print(
        f"Top Performer: {top_performers[0].symbol} ({top_performers[0].gain_loss_percentage:.2f}%)"
    )
    print(
        f"Worst Performer: {worst_performers[0].symbol} ({worst_performers[0].gain_loss_percentage:.2f}%)"
    )
    print()


if __name__ == "__main__":
    analyze_real_portfolio("e:/Coinbase/portfolios/yahoo_portfolio.csv")
