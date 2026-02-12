"""
Coinbase Database Layer
========================
Databricks-backed database for crypto investment platform.
"""

from .ai_safe_analyzer import (
    AISafePortfolioAnalyzer,
    get_ai_safe_analyzer,
)
from .crypto_db import (
    CryptoAsset,
    CryptoAssetType,
    CryptoDatabase,
    PortfolioPosition,
    Transaction,
    TransactionType,
)
from .databricks_analyzer import DatabricksPortfolioAnalyzer
from .databricks_persistence import DatabricksPortfolioPersistence
from .databricks_schema import (
    ALL_SCHEMAS,
    MERGE_PORTFOLIO_POSITION,
    MERGE_PORTFOLIO_SUMMARY,
)
from .secure_persistence import (
    SecurePortfolioPersistence,
    get_secure_persistence,
)

__all__ = [
    "CryptoDatabase",
    "CryptoAsset",
    "CryptoAssetType",
    "PortfolioPosition",
    "Transaction",
    "TransactionType",
    "ALL_SCHEMAS",
    "MERGE_PORTFOLIO_POSITION",
    "MERGE_PORTFOLIO_SUMMARY",
    "DatabricksPortfolioPersistence",
    "DatabricksPortfolioAnalyzer",
    "SecurePortfolioPersistence",
    "get_secure_persistence",
    "AISafePortfolioAnalyzer",
    "get_ai_safe_analyzer",
]
