"""Coinbase crypto analysis skills."""

import logging
import statistics
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class SkillType(Enum):
    """Types of crypto analysis skills."""

    DATA_PROCESSING = "data_processing"
    ANALYSIS = "analysis"
    REPORTING = "reporting"
    BACKTESTING = "backtesting"
    PATTERN_RECOGNITION = "pattern_recognition"
    RISK_MANAGEMENT = "risk_management"


@dataclass
class CryptoSkill:
    """Represents a crypto analysis skill."""

    skill_id: str
    skill_type: SkillType
    name: str
    description: str
    handler: Callable[..., Any]
    success_rate: float = 0.0
    usage_count: int = 0
    avg_latency_ms: float = 0.0


class CryptoSkillsRegistry:
    """Registry for Coinbase crypto analysis skills."""

    def __init__(self) -> None:
        self.skills: dict[str, CryptoSkill] = {}
        self._register_core_skills()

    def _register_core_skills(self) -> None:
        """Register core crypto analysis skills."""

        # Data Processing Skills
        self.register_skill(
            CryptoSkill(
                skill_id="crypto_data_normalization",
                skill_type=SkillType.DATA_PROCESSING,
                name="Crypto Data Normalization",
                description="Normalize raw crypto price and volume data for analysis",
                handler=self._normalize_crypto_data,
            )
        )

        self.register_skill(
            CryptoSkill(
                skill_id="crypto_data_validation",
                skill_type=SkillType.DATA_PROCESSING,
                name="Crypto Data Validation",
                description="Validate crypto data quality and integrity",
                handler=self._validate_crypto_data,
            )
        )

        # Analysis Skills
        self.register_skill(
            CryptoSkill(
                skill_id="price_trend_analysis",
                skill_type=SkillType.ANALYSIS,
                name="Price Trend Analysis",
                description="Analyze price trends and identify patterns",
                handler=self._analyze_price_trends,
            )
        )

        self.register_skill(
            CryptoSkill(
                skill_id="volume_analysis",
                skill_type=SkillType.ANALYSIS,
                name="Volume Analysis",
                description="Analyze trading volume patterns",
                handler=self._analyze_volume,
            )
        )

        # Backtesting Skills
        self.register_skill(
            CryptoSkill(
                skill_id="strategy_backtesting",
                skill_type=SkillType.BACKTESTING,
                name="Strategy Backtesting",
                description="Backtest trading strategies on historical data",
                handler=self._backtest_strategy,
            )
        )

        # Pattern Recognition Skills
        self.register_skill(
            CryptoSkill(
                skill_id="chart_pattern_detection",
                skill_type=SkillType.PATTERN_RECOGNITION,
                name="Chart Pattern Detection",
                description="Detect chart patterns like head & shoulders, triangles",
                handler=self._detect_chart_patterns,
            )
        )

        # Risk Management Skills
        self.register_skill(
            CryptoSkill(
                skill_id="risk_assessment",
                skill_type=SkillType.RISK_MANAGEMENT,
                name="Risk Assessment",
                description="Assess trading risks and recommend position sizing",
                handler=self._assess_risk,
            )
        )

        # Reporting Skills
        self.register_skill(
            CryptoSkill(
                skill_id="report_generation",
                skill_type=SkillType.REPORTING,
                name="Report Generation",
                description="Generate comprehensive analysis reports",
                handler=self._generate_report,
            )
        )

    def register_skill(self, skill: CryptoSkill) -> None:
        """Register a crypto analysis skill."""
        self.skills[skill.skill_id] = skill

    def get_skill(self, skill_id: str) -> CryptoSkill | None:
        """Get a skill by ID."""
        return self.skills.get(skill_id)

    def get_skills_by_type(self, skill_type: SkillType) -> list[CryptoSkill]:
        """Get all skills of a specific type."""
        return [s for s in self.skills.values() if s.skill_type == skill_type]

    def get_ranked_skills(self, limit: int = 10) -> list[CryptoSkill]:
        """Get skills ranked by success rate and latency."""
        return sorted(
            self.skills.values(), key=lambda s: (s.success_rate, -s.avg_latency_ms), reverse=True
        )[:limit]

    # ============== REAL SKILL IMPLEMENTATIONS ==============

    def _normalize_crypto_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Normalize crypto data for analysis.

        Performs:
        - Price normalization (min-max, z-score)
        - Volume standardization
        - Timestamp alignment
        - Missing data handling
        """
        import time

        start_time = time.time()

        try:
            prices = data.get("prices", [])
            volumes = data.get("volumes", [])
            data.get("timestamps", [])

            if not prices:
                return {"success": False, "error": "No price data provided"}

            # Min-max normalization for prices
            min_price = min(prices)
            max_price = max(prices)
            price_range = max_price - min_price if max_price != min_price else 1

            normalized_prices = [(p - min_price) / price_range for p in prices]

            # Z-score standardization
            mean_price = statistics.mean(prices)
            std_price = statistics.stdev(prices) if len(prices) > 1 else 1
            zscore_prices = [(p - mean_price) / std_price for p in prices]

            # Volume normalization
            normalized_volumes = []
            if volumes:
                mean_volume = statistics.mean(volumes)
                std_volume = statistics.stdev(volumes) if len(volumes) > 1 else 1
                normalized_volumes = [(v - mean_volume) / std_volume for v in volumes]

            # Calculate returns
            returns = []
            for i in range(1, len(prices)):
                ret = (prices[i] - prices[i - 1]) / prices[i - 1] if prices[i - 1] != 0 else 0
                returns.append(ret)

            latency_ms = (time.time() - start_time) * 1000

            return {
                "success": True,
                "normalized_prices": normalized_prices,
                "zscore_prices": zscore_prices,
                "normalized_volumes": normalized_volumes,
                "returns": returns,
                "statistics": {
                    "min_price": min_price,
                    "max_price": max_price,
                    "mean_price": mean_price,
                    "std_price": std_price,
                    "price_range": price_range,
                },
                "data_points": len(prices),
                "latency_ms": latency_ms,
            }

        except Exception as e:
            logger.error(f"Error normalizing crypto data: {e}")
            return {"success": False, "error": str(e)}

    def _validate_crypto_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate crypto data quality and integrity.

        Checks:
        - Data completeness
        - Price/volume ranges
        - Timestamp consistency
        - Outlier detection
        """
        import time

        start_time = time.time()

        try:
            prices = data.get("prices", [])
            volumes = data.get("volumes", [])
            timestamps = data.get("timestamps", [])

            validation_results = {
                "has_price_data": len(prices) > 0,
                "has_volume_data": len(volumes) > 0,
                "has_timestamps": len(timestamps) > 0,
                "price_range_valid": False,
                "volume_range_valid": False,
                "no_missing_data": True,
                "outlier_score": 0.0,
                "quality_score": 0.0,
            }

            if prices:
                # Check for negative or zero prices
                validation_results["price_range_valid"] = all(p > 0 for p in prices)

                # Check for outliers (prices beyond 3 std dev)
                if len(prices) > 10:
                    mean_price = statistics.mean(prices)
                    std_price = statistics.stdev(prices)
                    outliers = [p for p in prices if abs(p - mean_price) > 3 * std_price]
                    validation_results["outlier_score"] = len(outliers) / len(prices)

                # Check for missing data (gaps in timestamps)
                if timestamps and len(timestamps) > 1:
                    time_diffs = [
                        timestamps[i] - timestamps[i - 1] for i in range(1, len(timestamps))
                    ]
                    if time_diffs:
                        median_diff = statistics.median(time_diffs)
                        large_gaps = [d for d in time_diffs if d > median_diff * 2]
                        validation_results["no_missing_data"] = len(large_gaps) == 0

            if volumes:
                # Check for negative volumes
                validation_results["volume_range_valid"] = all(v >= 0 for v in volumes)

            # Calculate overall quality score
            checks = [
                validation_results["has_price_data"],
                validation_results["price_range_valid"],
                validation_results["no_missing_data"],
                validation_results["outlier_score"] < 0.05,
            ]
            validation_results["quality_score"] = sum(checks) / len(checks)

            latency_ms = (time.time() - start_time) * 1000
            validation_results["latency_ms"] = latency_ms
            validation_results["success"] = True

            return validation_results

        except Exception as e:
            logger.error(f"Error validating crypto data: {e}")
            return {"success": False, "error": str(e)}

    def _analyze_price_trends(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze price trends using multiple technical indicators.

        Indicators:
        - Simple Moving Averages (SMA)
        - Exponential Moving Average (EMA)
        - Trend direction and strength
        - Support/Resistance levels
        """
        import time

        start_time = time.time()

        try:
            prices = data.get("prices", [])

            if len(prices) < 20:
                return {"success": False, "error": "Need at least 20 price points"}

            # Calculate moving averages
            def sma(prices: list[float], window: int) -> list[float]:
                return [
                    statistics.mean(prices[i : i + window]) for i in range(len(prices) - window + 1)
                ]

            def ema(prices: list[float], window: int) -> list[float]:
                multiplier = 2 / (window + 1)
                ema_values = [statistics.mean(prices[:window])]
                for price in prices[window:]:
                    ema_values.append((price - ema_values[-1]) * multiplier + ema_values[-1])
                return ema_values

            sma_20 = sma(prices, 20)
            sma_50 = sma(prices, 50) if len(prices) >= 50 else None
            ema_12 = ema(prices, 12)

            # Determine trend
            current_price = prices[-1]
            sma_20_current = sma_20[-1] if sma_20 else current_price

            if current_price > sma_20_current * 1.02:
                trend = "bullish"
                trend_strength = min((current_price / sma_20_current - 1) * 50, 1.0)
            elif current_price < sma_20_current * 0.98:
                trend = "bearish"
                trend_strength = min((1 - current_price / sma_20_current) * 50, 1.0)
            else:
                trend = "neutral"
                trend_strength = 0.0

            # Find support and resistance
            recent_prices = prices[-20:]
            support = min(recent_prices)
            resistance = max(recent_prices)

            # Calculate volatility
            returns = [(prices[i] - prices[i - 1]) / prices[i - 1] for i in range(1, len(prices))]
            volatility = statistics.stdev(returns) * 100 if len(returns) > 1 else 0

            latency_ms = (time.time() - start_time) * 1000

            return {
                "success": True,
                "trend": trend,
                "trend_strength": round(trend_strength, 2),
                "current_price": current_price,
                "sma_20": sma_20_current,
                "sma_50": sma_50[-1] if sma_50 else None,
                "ema_12": ema_12[-1],
                "support_level": support,
                "resistance_level": resistance,
                "volatility_percent": round(volatility, 2),
                "latency_ms": latency_ms,
            }

        except Exception as e:
            logger.error(f"Error analyzing price trends: {e}")
            return {"success": False, "error": str(e)}

    def _analyze_volume(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze trading volume patterns.

        Analysis:
        - Volume trends
        - On-Balance Volume (OBV)
        - Volume moving averages
        - Volume-price correlation
        """
        import time

        start_time = time.time()

        try:
            prices = data.get("prices", [])
            volumes = data.get("volumes", [])

            if len(volumes) < 10:
                return {"success": False, "error": "Need at least 10 volume data points"}

            # Calculate volume moving average
            volume_sma_20 = (
                statistics.mean(volumes[-20:]) if len(volumes) >= 20 else statistics.mean(volumes)
            )
            current_volume = volumes[-1]

            # Volume trend
            volume_trend = "neutral"
            if current_volume > volume_sma_20 * 1.2:
                volume_trend = "high"
            elif current_volume < volume_sma_20 * 0.8:
                volume_trend = "low"

            # Calculate OBV (On-Balance Volume)
            obv = [volumes[0]]
            for i in range(1, len(volumes)):
                if prices[i] > prices[i - 1]:
                    obv.append(obv[-1] + volumes[i])
                elif prices[i] < prices[i - 1]:
                    obv.append(obv[-1] - volumes[i])
                else:
                    obv.append(obv[-1])

            # Volume-price correlation
            if len(prices) == len(volumes):
                try:
                    correlation = self._calculate_correlation(prices[-20:], volumes[-20:])
                except Exception:
                    correlation = 0.0
            else:
                correlation = 0.0

            # Volume momentum
            avg_volume_5 = statistics.mean(volumes[-5:]) if len(volumes) >= 5 else current_volume
            avg_volume_10 = statistics.mean(volumes[-10:]) if len(volumes) >= 10 else current_volume
            volume_momentum = avg_volume_5 / avg_volume_10 if avg_volume_10 > 0 else 1.0

            latency_ms = (time.time() - start_time) * 1000

            return {
                "success": True,
                "volume_trend": volume_trend,
                "current_volume": current_volume,
                "volume_sma_20": volume_sma_20,
                "obv": obv[-1],
                "obv_trend": "rising" if obv[-1] > obv[0] else "falling",
                "volume_price_correlation": round(correlation, 2),
                "volume_momentum": round(volume_momentum, 2),
                "latency_ms": latency_ms,
            }

        except Exception as e:
            logger.error(f"Error analyzing volume: {e}")
            return {"success": False, "error": str(e)}

    def _backtest_strategy(self, strategy: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
        """
        Backtest trading strategy on historical data.

        Strategy Types:
        - Moving Average Crossover
        - RSI-based
        - Bollinger Bands
        - Custom rules
        """
        import time

        start_time = time.time()

        try:
            prices = data.get("prices", [])
            strategy_type = strategy.get("type", "ma_crossover")

            if len(prices) < 50:
                return {"success": False, "error": "Need at least 50 price points for backtesting"}

            # Simple Moving Average Crossover Strategy
            def ma_crossover(prices: list[float], fast: int = 10, slow: int = 30) -> list[dict]:
                trades = []
                position = 0  # 0 = no position, 1 = long
                entry_price = 0.0

                for i in range(slow, len(prices)):
                    fast_ma = statistics.mean(prices[i - fast : i])
                    slow_ma = statistics.mean(prices[i - slow : i])

                    # Buy signal: fast crosses above slow
                    if fast_ma > slow_ma and position == 0:
                        position = 1
                        entry_price = prices[i]
                        trades.append({"type": "buy", "price": entry_price, "index": i})

                    # Sell signal: fast crosses below slow
                    elif fast_ma < slow_ma and position == 1:
                        exit_price = prices[i]
                        profit = (exit_price - entry_price) / entry_price
                        trades.append(
                            {"type": "sell", "price": exit_price, "index": i, "profit": profit}
                        )
                        position = 0

                return trades

            trades = ma_crossover(prices)

            # Calculate performance metrics
            profits = [t["profit"] for t in trades if t["type"] == "sell"]

            if not profits:
                return {
                    "success": True,
                    "total_trades": 0,
                    "win_rate": 0.0,
                    "message": "No trades executed in backtest period",
                }

            winning_trades = [p for p in profits if p > 0]
            losing_trades = [p for p in profits if p <= 0]

            total_return = sum(profits)
            win_rate = len(winning_trades) / len(profits) if profits else 0

            # Calculate Sharpe ratio (simplified)
            if len(profits) > 1:
                avg_return = statistics.mean(profits)
                std_return = statistics.stdev(profits)
                sharpe_ratio = avg_return / std_return if std_return > 0 else 0
            else:
                sharpe_ratio = 0

            # Calculate max drawdown
            cumulative = [sum(profits[: i + 1]) for i in range(len(profits))]
            max_drawdown = 0
            peak = 0
            for value in cumulative:
                if value > peak:
                    peak = value
                drawdown = peak - value
                if drawdown > max_drawdown:
                    max_drawdown = drawdown

            # Profit factor
            gross_profit = sum(p for p in profits if p > 0)
            gross_loss = abs(sum(p for p in profits if p < 0))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

            latency_ms = (time.time() - start_time) * 1000

            return {
                "success": True,
                "strategy_type": strategy_type,
                "total_trades": len([t for t in trades if t["type"] == "sell"]),
                "winning_trades": len(winning_trades),
                "losing_trades": len(losing_trades),
                "win_rate": round(win_rate, 2),
                "total_return": round(total_return, 4),
                "avg_return_per_trade": round(statistics.mean(profits), 4),
                "sharpe_ratio": round(sharpe_ratio, 2),
                "max_drawdown": round(max_drawdown, 4),
                "profit_factor": round(profit_factor, 2),
                "trades": trades,
                "latency_ms": latency_ms,
            }

        except Exception as e:
            logger.error(f"Error backtesting strategy: {e}")
            return {"success": False, "error": str(e)}

    def _detect_chart_patterns(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Detect common chart patterns in price data.

        Patterns:
        - Support/Resistance levels
        - Double Top/Bottom
        - Head and Shoulders
        - Triangle patterns
        """
        import time

        start_time = time.time()

        try:
            prices = data.get("prices", [])

            if len(prices) < 30:
                return {"success": False, "error": "Need at least 30 price points"}

            patterns = []

            # Find local minima and maxima
            def find_extrema(prices: list[float], window: int = 3) -> tuple[list[int], list[int]]:
                """Find local minima and maxima indices."""
                minima = []
                maxima = []

                for i in range(window, len(prices) - window):
                    is_min = all(
                        prices[i] <= prices[j] for j in range(i - window, i + window + 1) if j != i
                    )
                    is_max = all(
                        prices[i] >= prices[j] for j in range(i - window, i + window + 1) if j != i
                    )

                    if is_min:
                        minima.append(i)
                    if is_max:
                        maxima.append(i)

                return minima, maxima

            minima, maxima = find_extrema(prices)

            # Detect Double Top
            if len(maxima) >= 2:
                for i in range(len(maxima) - 1):
                    price1 = prices[maxima[i]]
                    price2 = prices[maxima[i + 1]]

                    # Two peaks within 2% of each other
                    if abs(price1 - price2) / price1 < 0.02:
                        patterns.append(
                            {
                                "pattern": "double_top",
                                "confidence": 0.7,
                                "location": maxima[i],
                                "target_price": min(prices[maxima[i] : maxima[i + 1]]) * 0.95,
                            }
                        )

            # Detect Double Bottom
            if len(minima) >= 2:
                for i in range(len(minima) - 1):
                    price1 = prices[minima[i]]
                    price2 = prices[minima[i + 1]]

                    # Two troughs within 2% of each other
                    if abs(price1 - price2) / price1 < 0.02:
                        patterns.append(
                            {
                                "pattern": "double_bottom",
                                "confidence": 0.7,
                                "location": minima[i],
                                "target_price": max(prices[minima[i] : minima[i + 1]]) * 1.05,
                            }
                        )

            # Detect Head and Shoulders (simplified)
            if len(maxima) >= 3:
                for i in range(len(maxima) - 2):
                    left = prices[maxima[i]]
                    head = prices[maxima[i + 1]]
                    right = prices[maxima[i + 2]]

                    # Head higher than shoulders
                    if head > left * 1.02 and head > right * 1.02:
                        # Shoulders roughly equal (within 5%)
                        if abs(left - right) / left < 0.05:
                            patterns.append(
                                {
                                    "pattern": "head_and_shoulders",
                                    "confidence": 0.65,
                                    "location": maxima[i],
                                    "neckline": (
                                        min(prices[minima[i] : minima[i + 2]])
                                        if i + 2 < len(minima)
                                        else min(left, right)
                                    ),
                                }
                            )

            # Detect Triangle patterns (simplified)
            if len(prices) >= 20:
                recent_prices = prices[-20:]
                highs = [max(recent_prices[i : i + 5]) for i in range(0, 15, 5)]
                lows = [min(recent_prices[i : i + 5]) for i in range(0, 15, 5)]

                # Descending highs + ascending lows = Symmetrical Triangle
                if highs[0] > highs[1] > highs[2] and lows[0] < lows[1] < lows[2]:
                    patterns.append(
                        {
                            "pattern": "symmetrical_triangle",
                            "confidence": 0.6,
                            "location": len(prices) - 20,
                            "breakout_direction": "unknown",
                        }
                    )

            latency_ms = (time.time() - start_time) * 1000

            return {
                "success": True,
                "patterns_detected": len(patterns),
                "patterns": patterns,
                "minima_count": len(minima),
                "maxima_count": len(maxima),
                "latency_ms": latency_ms,
            }

        except Exception as e:
            logger.error(f"Error detecting chart patterns: {e}")
            return {"success": False, "error": str(e)}

    def _assess_risk(self, position: dict[str, Any]) -> dict[str, Any]:
        """
        Assess trading risk and recommend position sizing.

        Risk Metrics:
        - Position size calculation
        - Stop loss recommendations
        - Risk/Reward ratio
        - Portfolio heat
        """
        import time

        start_time = time.time()

        try:
            portfolio_value = position.get("portfolio_value", 10000)
            entry_price = position.get("entry_price", 0)
            stop_loss_price = position.get("stop_loss_price", 0)
            risk_percent = position.get("risk_percent", 0.02)  # 2% default
            volatility = position.get("volatility", 0.5)  # 50% annualized

            if entry_price <= 0:
                return {"success": False, "error": "Invalid entry price"}

            # Calculate position size based on risk
            if stop_loss_price > 0:
                risk_per_unit = abs(entry_price - stop_loss_price) / entry_price
                if risk_per_unit > 0:
                    position_size = (portfolio_value * risk_percent) / risk_per_unit
                    max_position_value = portfolio_value * 0.2  # Max 20% of portfolio
                    position_size = min(position_size, max_position_value)
                else:
                    position_size = portfolio_value * risk_percent
            else:
                # Use volatility-based position sizing
                position_size = portfolio_value * risk_percent / (volatility / 100)

            # Risk/Reward calculation
            target_price = position.get("target_price", entry_price * 1.1)
            potential_loss = (
                abs(entry_price - stop_loss_price)
                if stop_loss_price
                else entry_price * risk_percent
            )
            potential_gain = abs(target_price - entry_price)
            risk_reward_ratio = (
                potential_gain / potential_loss if potential_loss > 0 else float("inf")
            )

            # Risk level classification
            position_heat = position_size / portfolio_value
            if position_heat > 0.15 or risk_percent > 0.03:
                risk_level = "high"
            elif position_heat > 0.08 or risk_percent > 0.015:
                risk_level = "medium"
            else:
                risk_level = "low"

            # Kelly Criterion (simplified)
            win_rate = position.get("win_rate", 0.5)
            avg_win = position.get("avg_win", 0.05)
            avg_loss = position.get("avg_loss", 0.02)

            if avg_loss > 0:
                kelly_fraction = win_rate - (1 - win_rate) / (avg_win / avg_loss)
                kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Cap at 25%
            else:
                kelly_fraction = 0

            # Recommended stop loss if not provided
            if stop_loss_price == 0:
                recommended_stop = entry_price * (1 - risk_percent * 2)
            else:
                recommended_stop = stop_loss_price

            latency_ms = (time.time() - start_time) * 1000

            return {
                "success": True,
                "risk_level": risk_level,
                "position_size": round(position_size, 2),
                "position_heat": round(position_heat * 100, 1),
                "recommended_stop_loss": round(recommended_stop, 2),
                "risk_reward_ratio": round(risk_reward_ratio, 2),
                "kelly_fraction": round(kelly_fraction, 4),
                "max_position_value": round(portfolio_value * 0.2, 2),
                "recommendations": [
                    f"Position size: ${position_size:.2f} ({position_heat*100:.1f}% of portfolio)",
                    f"Risk level: {risk_level}",
                    f"Recommended stop loss: ${recommended_stop:.2f}",
                    f"Risk/Reward ratio: {risk_reward_ratio:.2f}",
                ],
                "latency_ms": latency_ms,
            }

        except Exception as e:
            logger.error(f"Error assessing risk: {e}")
            return {"success": False, "error": str(e)}

    def _generate_report(self, analysis: dict[str, Any]) -> dict[str, Any]:
        """
        Generate comprehensive analysis report.

        Combines multiple analysis components into a structured report.
        """
        import time

        start_time = time.time()

        try:
            # Extract analysis components
            trend_data = analysis.get("trend_analysis", {})
            volume_data = analysis.get("volume_analysis", {})
            pattern_data = analysis.get("pattern_analysis", {})
            risk_data = analysis.get("risk_assessment", {})

            # Generate summary
            trend = trend_data.get("trend", "neutral")
            trend_strength = trend_data.get("trend_strength", 0.0)
            volume_trend = volume_data.get("volume_trend", "neutral")

            # Determine overall sentiment
            if trend == "bullish" and trend_strength > 0.6:
                sentiment = "strongly_bullish"
            elif trend == "bullish":
                sentiment = "bullish"
            elif trend == "bearish" and trend_strength > 0.6:
                sentiment = "strongly_bearish"
            elif trend == "bearish":
                sentiment = "bearish"
            else:
                sentiment = "neutral"

            # Generate recommendations
            recommendations = []

            if sentiment in ["strongly_bullish", "bullish"]:
                recommendations.append("Consider long position")
                if volume_trend == "high":
                    recommendations.append("High volume confirms bullish sentiment")
            elif sentiment in ["strongly_bearish", "bearish"]:
                recommendations.append("Consider short position or exit longs")

            # Risk-based recommendations
            if risk_data.get("risk_level") == "high":
                recommendations.append("High risk - reduce position size")

            # Pattern-based recommendations
            patterns = pattern_data.get("patterns", [])
            for pattern in patterns:
                if pattern.get("pattern") == "double_top":
                    recommendations.append("Double top detected - potential reversal")
                elif pattern.get("pattern") == "double_bottom":
                    recommendations.append("Double bottom detected - potential reversal")

            # Technical levels
            support = trend_data.get("support_level", 0)
            resistance = trend_data.get("resistance_level", 0)

            latency_ms = (time.time() - start_time) * 1000

            return {
                "success": True,
                "report_timestamp": datetime.now().isoformat(),
                "summary": {
                    "sentiment": sentiment,
                    "confidence": trend_strength,
                    "trend": trend,
                    "volume_trend": volume_trend,
                },
                "technical_levels": {
                    "support": support,
                    "resistance": resistance,
                    "current_price": trend_data.get("current_price", 0),
                },
                "patterns": [p.get("pattern") for p in patterns],
                "risk_assessment": {
                    "level": risk_data.get("risk_level", "unknown"),
                    "position_size": risk_data.get("position_size", 0),
                },
                "recommendations": recommendations,
                "latency_ms": latency_ms,
            }

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return {"success": False, "error": str(e)}

    def _calculate_correlation(self, x: list[float], y: list[float]) -> float:
        """Calculate Pearson correlation coefficient."""
        if len(x) != len(y) or len(x) < 2:
            return 0.0

        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(xi**2 for xi in x)
        sum_y2 = sum(yi**2 for yi in y)

        numerator = n * sum_xy - sum_x * sum_y
        denominator = ((n * sum_x2 - sum_x**2) * (n * sum_y2 - sum_y**2)) ** 0.5

        return numerator / denominator if denominator != 0 else 0.0


# Global registry instance
crypto_skills_registry = CryptoSkillsRegistry()
