"""
Yahoo Finance Integration Scopes.

This module defines the integration strategy for Yahoo Finance market data,
designed for recursive efficiency in financial agency tasks.
"""


class YahooFinanceScopes:
    # RECURSIVE DATA FETCHING: Optimized for depth-first financial analysis
    MARKET_SUMMARY = "finance.market_summary"  # High-level indices
    TICKER_DETAILS = "finance.ticker_details"  # Specific asset data
    HISTORICAL_DATA = "finance.historical"  # Time-series for backtesting
    ANALYST_INSIGHTS = "finance.recommendations"  # Sentiment layer


def get_placement_map() -> dict[str, str]:
    return {
        "service": "application/mothership/services/finance/yfinance_adapter.py",
        "router": "application/mothership/routers/finance.py",
        "scheduler": "scripts/maintenance/budget_scheduler.py",  # For periodic updates
    }


if __name__ == "__main__":
    print("Yahoo Finance Integration Scopes mapped for recursive efficiency.")
