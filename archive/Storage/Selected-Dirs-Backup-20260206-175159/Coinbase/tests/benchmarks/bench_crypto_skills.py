"""Benchmark tests for crypto analysis skills.

This module benchmarks the performance of crypto-related operations including:
- Price analysis calculations
- Portfolio operations
- Technical indicators
- Risk calculations
"""

import hashlib
import statistics

from tests.benchmarks.conftest import Benchmark, assert_performance


class TestCryptoSkillsBenchmarks:
    """Benchmark tests for crypto skills."""

    def test_benchmark_price_volatility_calculation(self, benchmark: Benchmark) -> None:
        """Benchmark price volatility calculation."""
        prices = [100.0 + (i * 0.5) - ((i % 10) * 0.3) for i in range(1000)]

        def calculate_volatility() -> float:
            mean_price = sum(prices) / len(prices)
            variance = sum((p - mean_price) ** 2 for p in prices) / len(prices)
            return variance**0.5

        result = benchmark.run(
            name="price_volatility",
            func=calculate_volatility,
            metadata={"category": "crypto", "prices_count": len(prices)},
        )

        assert_performance(result, max_mean_ms=10.0)

    def test_benchmark_moving_average_sma(self, benchmark: Benchmark) -> None:
        """Benchmark Simple Moving Average calculation."""
        prices = [100.0 + (i * 0.1) for i in range(2000)]

        def calculate_sma() -> list[float]:
            window = 50
            result: list[float] = []
            for i in range(window, len(prices)):
                avg = sum(prices[i - window : i]) / window
                result.append(avg)
            return result

        result = benchmark.run(
            name="sma_calculation",
            func=calculate_sma,
            metadata={"category": "crypto", "window": 50, "data_points": len(prices)},
        )

        assert_performance(result, max_mean_ms=50.0)

    def test_benchmark_moving_average_ema(self, benchmark: Benchmark) -> None:
        """Benchmark Exponential Moving Average calculation."""
        prices = [100.0 + (i * 0.1) - ((i % 20) * 0.05) for i in range(2000)]

        def calculate_ema() -> list[float]:
            window = 20
            multiplier = 2 / (window + 1)
            ema_values: list[float] = []

            # First EMA is just SMA
            first_sma = sum(prices[:window]) / window
            ema_values.append(first_sma)

            # Calculate EMA for rest of prices
            for i in range(window, len(prices)):
                ema = (prices[i] * multiplier) + (ema_values[-1] * (1 - multiplier))
                ema_values.append(ema)

            return ema_values

        result = benchmark.run(
            name="ema_calculation",
            func=calculate_ema,
            metadata={"category": "crypto", "window": 20, "data_points": len(prices)},
        )

        assert_performance(result, max_mean_ms=20.0)

    def test_benchmark_rsi_calculation(self, benchmark: Benchmark) -> None:
        """Benchmark RSI (Relative Strength Index) calculation."""
        prices = [100.0 + (i * 0.1) - ((i % 10) * 0.5) for i in range(500)]

        def calculate_rsi() -> list[float]:
            period = 14
            rsi_values: list[float] = []

            for i in range(period, len(prices)):
                gains: list[float] = []
                losses: list[float] = []

                for j in range(i - period + 1, i + 1):
                    change = prices[j] - prices[j - 1]
                    if change > 0:
                        gains.append(change)
                        losses.append(0.0)
                    else:
                        gains.append(0.0)
                        losses.append(abs(change))

                avg_gain = sum(gains) / period
                avg_loss = sum(losses) / period

                if avg_loss == 0:
                    rsi = 100.0
                else:
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))

                rsi_values.append(rsi)

            return rsi_values

        result = benchmark.run(
            name="rsi_calculation",
            func=calculate_rsi,
            metadata={"category": "crypto", "period": 14, "data_points": len(prices)},
        )

        assert_performance(result, max_mean_ms=100.0)

    def test_benchmark_bollinger_bands(self, benchmark: Benchmark) -> None:
        """Benchmark Bollinger Bands calculation."""
        prices = [100.0 + (i * 0.05) - ((i % 15) * 0.3) for i in range(1000)]

        def calculate_bollinger_bands() -> list[tuple[float, float, float]]:
            window = 20
            num_std = 2.0
            bands: list[tuple[float, float, float]] = []

            for i in range(window, len(prices)):
                window_prices = prices[i - window : i]
                middle = sum(window_prices) / window
                std_dev = statistics.stdev(window_prices)

                upper = middle + (std_dev * num_std)
                lower = middle - (std_dev * num_std)

                bands.append((upper, middle, lower))

            return bands

        result = benchmark.run(
            name="bollinger_bands",
            func=calculate_bollinger_bands,
            metadata={"category": "crypto", "window": 20, "data_points": len(prices)},
        )

        assert_performance(result, max_mean_ms=100.0)

    def test_benchmark_macd_calculation(self, benchmark: Benchmark) -> None:
        """Benchmark MACD indicator calculation."""
        prices = [100.0 + (i * 0.08) - ((i % 12) * 0.2) for i in range(500)]

        def calculate_macd() -> list[tuple[float, float, float]]:
            # EMA helper
            def ema(data: list[float], window: int) -> list[float]:
                multiplier = 2 / (window + 1)
                ema_values = [sum(data[:window]) / window]
                for i in range(window, len(data)):
                    new_ema = (data[i] * multiplier) + (ema_values[-1] * (1 - multiplier))
                    ema_values.append(new_ema)
                return ema_values

            ema_12 = ema(prices, 12)
            ema_26 = ema(prices, 26)

            # MACD line = EMA12 - EMA26
            min_len = min(len(ema_12), len(ema_26))
            macd_line = [ema_12[i] - ema_26[i] for i in range(min_len)]

            # Signal line = 9-period EMA of MACD line
            signal_line = ema(macd_line, 9)

            # Histogram = MACD - Signal
            result: list[tuple[float, float, float]] = []
            for i in range(len(signal_line)):
                if i < len(macd_line):
                    histogram = macd_line[i] - signal_line[i]
                    result.append((macd_line[i], signal_line[i], histogram))

            return result

        result = benchmark.run(
            name="macd_calculation",
            func=calculate_macd,
            metadata={"category": "crypto", "data_points": len(prices)},
        )

        assert_performance(result, max_mean_ms=50.0)


class TestPortfolioBenchmarks:
    """Benchmark tests for portfolio operations."""

    def test_benchmark_portfolio_value_calculation(self, benchmark: Benchmark) -> None:
        """Benchmark portfolio total value calculation."""
        holdings: list[dict[str, float | str]] = [
            {"symbol": f"COIN{i}", "amount": 10.0 + (i * 0.5), "price": 100.0 + (i * 25)}
            for i in range(100)
        ]

        def calculate_portfolio_value() -> dict[str, float]:
            total_value = 0.0
            positions: list[dict[str, float | str]] = []

            for holding in holdings:
                amount = float(holding["amount"])
                price = float(holding["price"])
                value = amount * price
                total_value += value
                positions.append(
                    {
                        "symbol": holding["symbol"],
                        "amount": amount,
                        "value": value,
                        "percentage": 0.0,  # Will be calculated after
                    }
                )

            # Calculate percentages
            for position in positions:
                position["percentage"] = (float(position["value"]) / total_value) * 100

            return {"total_value": total_value, "position_count": float(len(positions))}

        result = benchmark.run(
            name="portfolio_value_calculation",
            func=calculate_portfolio_value,
            metadata={"category": "portfolio", "holdings_count": len(holdings)},
        )

        assert_performance(result, max_mean_ms=5.0)

    def test_benchmark_portfolio_rebalancing(self, benchmark: Benchmark) -> None:
        """Benchmark portfolio rebalancing calculations."""
        current_holdings: list[dict[str, float | str]] = [
            {"symbol": f"COIN{i}", "amount": 10.0 + (i % 5), "price": 100.0 + (i * 10)}
            for i in range(20)
        ]
        target_allocations: dict[str, float] = {f"COIN{i}": 5.0 for i in range(20)}  # Equal 5% each

        def calculate_rebalancing() -> list[dict[str, float | str]]:
            # Calculate current total value
            total_value = sum(float(h["amount"]) * float(h["price"]) for h in current_holdings)

            # Calculate trades needed
            trades: list[dict[str, float | str]] = []

            for holding in current_holdings:
                symbol = str(holding["symbol"])
                amount = float(holding["amount"])
                price = float(holding["price"])
                current_value = amount * price
                current_pct = (current_value / total_value) * 100

                target_pct = target_allocations.get(symbol, 0.0)
                target_value = total_value * (target_pct / 100)

                diff_value = target_value - current_value
                diff_amount = diff_value / price

                diff_pct = target_pct - current_pct
                if abs(diff_pct) > 0.5:  # 0.5% threshold
                    trades.append(
                        {
                            "symbol": symbol,
                            "action": "buy" if diff_value > 0 else "sell",
                            "amount": abs(diff_amount),
                            "value": abs(diff_value),
                        }
                    )

            return trades

        result = benchmark.run(
            name="portfolio_rebalancing",
            func=calculate_rebalancing,
            metadata={"category": "portfolio", "holdings_count": len(current_holdings)},
        )

        assert_performance(result, max_mean_ms=5.0)

    def test_benchmark_portfolio_risk_metrics(self, benchmark: Benchmark) -> None:
        """Benchmark portfolio risk metrics calculation."""
        # Historical returns for portfolio
        returns = [(i % 10 - 5) / 100 for i in range(252)]  # ~1 year of daily returns

        def calculate_risk_metrics() -> dict[str, float]:
            # Mean return
            mean_return = sum(returns) / len(returns)

            # Standard deviation (volatility)
            variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
            volatility = variance**0.5

            # Annualized metrics (252 trading days)
            annual_return = mean_return * 252
            annual_volatility = volatility * (252**0.5)

            # Sharpe ratio (assuming 2% risk-free rate)
            risk_free_rate = 0.02
            sharpe_ratio = (
                (annual_return - risk_free_rate) / annual_volatility if annual_volatility > 0 else 0
            )

            # Max drawdown
            cumulative = 1.0
            peak = 1.0
            max_drawdown = 0.0
            for ret in returns:
                cumulative *= 1 + ret
                peak = max(peak, cumulative)
                drawdown = (peak - cumulative) / peak
                max_drawdown = max(max_drawdown, drawdown)

            # Sortino ratio (downside deviation)
            downside_returns = [r for r in returns if r < 0]
            downside_variance = (
                sum(r**2 for r in downside_returns) / len(downside_returns)
                if downside_returns
                else 0
            )
            downside_deviation = downside_variance**0.5 * (252**0.5)
            sortino_ratio = (
                (annual_return - risk_free_rate) / downside_deviation
                if downside_deviation > 0
                else 0
            )

            return {
                "annual_return": annual_return,
                "annual_volatility": annual_volatility,
                "sharpe_ratio": sharpe_ratio,
                "sortino_ratio": sortino_ratio,
                "max_drawdown": max_drawdown,
            }

        result = benchmark.run(
            name="portfolio_risk_metrics",
            func=calculate_risk_metrics,
            metadata={"category": "portfolio", "data_points": len(returns)},
        )

        assert_performance(result, max_mean_ms=10.0)


class TestSecurityBenchmarks:
    """Benchmark tests for security operations."""

    def test_benchmark_user_id_hashing(self, benchmark: Benchmark) -> None:
        """Benchmark user ID hashing for privacy."""
        user_ids = [f"user_{i}@example.com" for i in range(1000)]

        def hash_user_ids() -> list[str]:
            return [hashlib.sha256(uid.encode()).hexdigest() for uid in user_ids]

        result = benchmark.run(
            name="user_id_hashing",
            func=hash_user_ids,
            metadata={"category": "security", "user_count": len(user_ids)},
        )

        assert_performance(result, max_mean_ms=50.0)

    def test_benchmark_data_integrity_check(self, benchmark: Benchmark) -> None:
        """Benchmark data integrity verification."""
        data_blocks = [f"data_block_{i}_" + ("x" * 100) for i in range(100)]

        def verify_data_integrity() -> list[tuple[str, str]]:
            hashes: list[tuple[str, str]] = []
            for block in data_blocks:
                block_hash = hashlib.sha256(block.encode()).hexdigest()
                hashes.append((block[:20], block_hash))
            return hashes

        result = benchmark.run(
            name="data_integrity_check",
            func=verify_data_integrity,
            metadata={"category": "security", "block_count": len(data_blocks)},
        )

        assert_performance(result, max_mean_ms=20.0)

    def test_benchmark_hmac_generation(self, benchmark: Benchmark) -> None:
        """Benchmark HMAC generation for API signatures."""
        import hmac

        secret_key = b"super_secret_key_for_api_authentication"
        messages = [f"message_{i}_timestamp_{i * 1000}".encode() for i in range(500)]

        def generate_hmacs() -> list[str]:
            return [hmac.new(secret_key, msg, hashlib.sha256).hexdigest() for msg in messages]

        result = benchmark.run(
            name="hmac_generation",
            func=generate_hmacs,
            metadata={"category": "security", "message_count": len(messages)},
        )

        assert_performance(result, max_mean_ms=50.0)


class TestDataProcessingBenchmarks:
    """Benchmark tests for data processing operations."""

    def test_benchmark_price_data_normalization(self, benchmark: Benchmark) -> None:
        """Benchmark price data normalization."""
        raw_prices = [
            {
                "timestamp": i * 60000,
                "open": 100.0 + (i * 0.1),
                "high": 100.5 + (i * 0.1),
                "low": 99.5 + (i * 0.1),
                "close": 100.2 + (i * 0.1),
                "volume": 1000000 + (i * 1000),
            }
            for i in range(10000)
        ]

        def normalize_prices() -> list[dict[str, float]]:
            # Find min/max for normalization
            closes = [p["close"] for p in raw_prices]
            min_close = min(closes)
            max_close = max(closes)
            close_range = max_close - min_close

            volumes = [p["volume"] for p in raw_prices]
            min_vol = min(volumes)
            max_vol = max(volumes)
            vol_range = max_vol - min_vol

            normalized: list[dict[str, float]] = []
            for price in raw_prices:
                normalized.append(
                    {
                        "timestamp": price["timestamp"],
                        "close_norm": (
                            (price["close"] - min_close) / close_range if close_range > 0 else 0
                        ),
                        "volume_norm": (
                            (price["volume"] - min_vol) / vol_range if vol_range > 0 else 0
                        ),
                    }
                )
            return normalized

        result = benchmark.run(
            name="price_data_normalization",
            func=normalize_prices,
            metadata={"category": "data", "record_count": len(raw_prices)},
        )

        assert_performance(result, max_mean_ms=100.0)

    def test_benchmark_time_series_aggregation(self, benchmark: Benchmark) -> None:
        """Benchmark time series data aggregation."""
        # Minute-level data
        minute_data: list[dict[str, int | float]] = [
            {"timestamp": i, "price": 100.0 + (i % 60) * 0.1, "volume": 1000 + (i % 100)}
            for i in range(10000)
        ]

        def aggregate_to_hourly() -> list[dict[str, int | float]]:
            hourly: dict[int, list[dict[str, int | float]]] = {}

            for record in minute_data:
                hour = int(record["timestamp"]) // 60
                if hour not in hourly:
                    hourly[hour] = []
                hourly[hour].append(record)

            result: list[dict[str, int | float]] = []
            for hour, records in sorted(hourly.items()):
                prices: list[float] = [float(r["price"]) for r in records]
                volumes: list[int] = [int(r["volume"]) for r in records]
                result.append(
                    {
                        "hour": hour,
                        "open": prices[0],
                        "high": max(prices),
                        "low": min(prices),
                        "close": prices[-1],
                        "volume": sum(volumes),
                        "vwap": sum(p * v for p, v in zip(prices, volumes)) / sum(volumes),
                    }
                )

            return result

        result = benchmark.run(
            name="time_series_aggregation",
            func=aggregate_to_hourly,
            metadata={"category": "data", "input_records": len(minute_data)},
        )

        assert_performance(result, max_mean_ms=100.0)
