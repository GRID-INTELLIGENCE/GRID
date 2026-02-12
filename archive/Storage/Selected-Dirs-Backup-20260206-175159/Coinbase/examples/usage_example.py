"""
Coinbase Example Usage
=======================
Example usage of Coinbase crypto investment platform.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    """Run example usage."""
    # Check if Databricks credentials are available
    if not all(
        [
            os.getenv("DATABRICKS_HOST"),
            os.getenv("DATABRICKS_HTTP_PATH"),
            os.getenv("DATABRICKS_TOKEN"),
        ]
    ):
        print("⚠ Databricks credentials not found. Running in demo mode without database.")
        print(
            "  Set DATABRICKS_HOST, DATABRICKS_HTTP_PATH, and DATABRICKS_TOKEN environment variables."
        )
        print("  Example: export DATABRICKS_HOST='your-workspace.cloud.databricks.com'\n")

        # Mock example without database
        print("=== Coinbase Demo Mode ===\n")
        print("Features available:")
        print("  ✓ Portfolio analysis with risk assessment")
        print("  ✓ Trading signals (STRONG_BUY/BUY/HOLD/SELL/STRONG_SELL)")
        print("  ✓ Multi-source price verification (CoinGecko, Binance, Coinbase)")
        print("  ✓ Anomaly detection (price spikes, volume anomalies)")
        print("  ✓ Revenue tracking and calculation")
        print("\nExample output (with database):")
        print("Portfolio Value: $25,000.00")
        print("PnL: 10.00%")
        print("Risk Level: medium")
        print("Diversification: 60.0%")
        print("\nTrading Signal: BUY")
        print("Confidence: 0.70")
        print("Reasoning: Positive sentiment (0.45) and upward trend (2.50%)")
        print("Target Price: $52,500.00")
        print("Stop Loss: $47,500.00")
        print("\nPrice Verified: True")
        print("Consensus Price: $50,100.00")
        print("Sources: 3/3")
        print("\nRevenue (30 days): $25,000.00")
        print("Daily Rate: $833.33/day")
        return

    # Initialize app from environment variables
    print("Initializing Coinbase application...")
    from coinbase.app import create_app

    app = create_app()
    print("✓ Application initialized\n")

    # Add crypto asset
    print("Adding Bitcoin asset...")
    app.add_crypto_asset(
        symbol="BTC",
        name="Bitcoin",
        asset_type="bitcoin",
        current_price=50000.0,
        market_cap=1000000000000.0,
        volume_24h=30000000000.0,
    )
    print("✓ Bitcoin asset added\n")

    # Add portfolio position
    print("Adding portfolio position...")
    app.add_portfolio_position(
        user_id="user123",
        asset_symbol="BTC",
        quantity=0.5,
        average_cost=45000.0,
    )
    print("✓ Position added\n")

    # Analyze portfolio
    print("Analyzing portfolio...")
    analysis = app.analyze_portfolio("user123")
    print(f"Portfolio Value: ${analysis['total_value']:,.2f}")
    print(f"PnL: {analysis['pnl_percentage']:.2f}%")
    print(f"Risk Level: {analysis['risk_level']}")
    print(f"Diversification: {analysis['diversification_score']:.1f}%")
    print("\nRecommendations:")
    for rec in analysis["recommendations"]:
        print(f"  - {rec}")
    print()

    # Get trading signal
    print("Getting trading signal...")
    signal = app.get_trading_signal("BTC")
    print(f"Trading Signal: {signal.signal.value}")
    print(f"Confidence: {signal.confidence:.2f}")
    print(f"Reasoning: {signal.reasoning}")
    if signal.target_price:
        print(f"Target Price: ${signal.target_price:,.2f}")
    if signal.stop_loss:
        print(f"Stop Loss: ${signal.stop_loss:,.2f}")
    print()

    # Verify price
    print("Verifying price...")
    verification = app.verify_price("BTC", 50000.0)
    print(f"Price Verified: {verification['verified']}")
    print(f"Consensus Price: ${verification['consensus_price']:,.2f}")
    print(f"Sources: {verification['sources_checked']}/{verification['sources_verified']}")
    if verification["anomalies"]:
        print("\nAnomalies:")
        for anomaly in verification["anomalies"]:
            print(f"  - {anomaly}")
    print()

    # Calculate revenue
    print("Calculating revenue...")
    revenue = app.calculate_revenue("user123", days=30)
    print(f"Revenue (30 days): ${revenue['revenue']:,.2f}")
    print(f"Daily Rate: ${revenue['revenue_rate']:,.2f}/day")
    print()

    print("Example completed successfully!")


if __name__ == "__main__":
    main()
