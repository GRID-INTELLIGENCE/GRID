"""
Signals Layer
==============
Trading signal generation for Coinbase.
"""

from .trading_compass import TradingCompass, TradingDirection, TradingSignal

__all__ = ["TradingCompass", "TradingSignal", "TradingDirection"]
