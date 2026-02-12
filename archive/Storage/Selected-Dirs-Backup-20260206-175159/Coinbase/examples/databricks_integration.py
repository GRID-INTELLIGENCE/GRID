"""
Databricks Integration Example
===============================
Demonstrate Databricks as top priority for artifact creation.

Use Case: Store and analyze portfolio data in Databricks
Quality Focus: Practical relevance, accuracy, precision
"""

import os

from coinbase.database.databricks_analyzer import DatabricksPortfolioAnalyzer
from coinbase.database.databricks_persistence import (
    DatabricksPortfolioPersistence,
    PortfolioPosition,
)
from coinbase.integrations.yahoo_finance import YahooPortfolioParser


def databricks_integration_demo(csv_path: str):
    """
    Demonstrate Databricks integration with real portfolio data.

    Shows: Portfolio data storage, analysis, and retrieval from Databricks
    """
    print("=" * 70)
    print("Databricks Integration Demo")
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
        print("⚠ Databricks credentials not found")
        print("Set DATABRICKS_HOST, DATABRICKS_HTTP_PATH, DATABRICKS_TOKEN")
        print("\nRunning in demo mode without Databricks connection\n")
        return

    # Step 1: Parse Yahoo Finance portfolio
    print("Step 1: Parse Yahoo Finance Portfolio")
    print("-" * 70)

    parser = YahooPortfolioParser(csv_path)
    positions = parser.parse()

    summary = parser.get_portfolio_summary()

    print(f"Total Positions: {summary['total_positions']}")
    print(f"Total Value: ${summary['total_value']:,.2f}")
    print(f"Total Gain/Loss: ${summary['total_gain_loss']:,.2f}")
    print()

    # Step 2: Initialize Databricks persistence
    print("Step 2: Initialize Databricks Persistence")
    print("-" * 70)

    persistence = DatabricksPortfolioPersistence()
    print("✓ Databricks tables initialized")
    print()

    # Step 3: Save positions to Databricks
    print("Step 3: Save Positions to Databricks")
    print("-" * 70)

    # Convert Yahoo positions to PortfolioPosition objects
    portfolio_positions = []
    for yahoo_pos in positions:
        portfolio_pos = PortfolioPosition(
            symbol=yahoo_pos.symbol,
            asset_name=yahoo_pos.symbol,
            sector="Unknown",
            quantity=yahoo_pos.quantity,
            purchase_price=yahoo_pos.purchase_price,
            current_price=yahoo_pos.current_price,
            purchase_value=yahoo_pos.purchase_value,
            current_value=yahoo_pos.current_value,
            total_gain_loss=yahoo_pos.total_gain_loss,
            gain_loss_percentage=yahoo_pos.gain_loss_percentage,
            purchase_date=yahoo_pos.purchase_date,
            commission=yahoo_pos.commission,
            high_limit=yahoo_pos.high_limit,
            low_limit=yahoo_pos.low_limit,
            comment=yahoo_pos.comment,
            transaction_type=yahoo_pos.transaction_type,
        )
        portfolio_positions.append(portfolio_pos)

    # Save to Databricks
    user_id = "user123"
    persistence.save_positions_batch(user_id, portfolio_positions)

    # Save portfolio summary
    persistence.save_portfolio_summary(user_id, summary)

    print(f"✓ Saved {len(portfolio_positions)} positions to Databricks")
    print("✓ Saved portfolio summary to Databricks")
    print()

    # Step 4: Analyze portfolio from Databricks
    print("Step 4: Analyze Portfolio from Databricks")
    print("-" * 70)

    analyzer = DatabricksPortfolioAnalyzer()
    analysis = analyzer.analyze_portfolio(user_id)

    print(f"Total Positions: {analysis['total_positions']}")
    print(f"Total Value: ${analysis['total_value']:,.2f}")
    print(f"Total Gain/Loss: ${analysis['total_gain_loss']:,.2f}")
    print(f"Gain/Loss %: {analysis['gain_loss_percentage']:.2f}%")
    print()

    # Step 5: Get top performers from Databricks
    print("Step 5: Top Performers (from Databricks)")
    print("-" * 70)

    top_performers = analyzer.get_top_performers(user_id, 3)
    for i, pos in enumerate(top_performers, 1):
        print(f"{i}. {pos['symbol']}")
        print(f"   Gain/Loss: {pos['gain_loss_percentage']:.2f}% | ${pos['total_gain_loss']:,.2f}")
        print(f"   Quantity: {pos['quantity']} | Value: ${pos['current_value']:,.2f}")
    print()

    # Step 6: Get concentration risk from Databricks
    print("Step 6: Concentration Risk (from Databricks)")
    print("-" * 70)

    risk = analyzer.get_concentration_risk(user_id)
    print(f"Risk Level: {risk['risk_level']}")
    print(f"Top Position: {risk['top_position_percentage']:.2f}%")
    print(f"Top 3 Positions: {risk['top_3_percentage']:.2f}%")
    print(f"Recommendation: {risk['recommendation']}")
    print()

    # Step 7: Get sector allocation from Databricks
    print("Step 7: Sector Allocation (from Databricks)")
    print("-" * 70)

    sector_allocation = analyzer.get_sector_allocation(user_id)
    for sector, percentage in sorted(sector_allocation.items(), key=lambda x: x[1], reverse=True):
        print(f"{sector}: {percentage:.2f}%")
    print()

    # Summary
    print("=" * 70)
    print("Databricks Integration Complete")
    print("=" * 70)
    print("\nWorkflow Demonstrated:")
    print("1. Parse Yahoo Finance portfolio data")
    print("2. Initialize Databricks tables")
    print("3. Save positions to Databricks")
    print("4. Analyze portfolio from Databricks")
    print("5. Retrieve top performers from Databricks")
    print("6. Calculate concentration risk from Databricks")
    print("7. Get sector allocation from Databricks")
    print()
    print("Databricks provides:")
    print("• Persistent storage for portfolio data")
    print("• Privacy-first design (user ID hashing)")
    print("• Scalable analytics")
    print("• Real-time portfolio analysis")
    print("• Historical data tracking")
    print()


if __name__ == "__main__":
    databricks_integration_demo("e:/Coinbase/portfolios/yahoo_portfolio.csv")
