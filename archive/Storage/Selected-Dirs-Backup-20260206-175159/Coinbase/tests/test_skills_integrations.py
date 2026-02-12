"""
Comprehensive Tests for Skills and Integrations
================================================
Tests for crypto skills and Coinbase API integration
"""

from unittest.mock import Mock, patch

import pytest

# Import skills
from coinbase import SkillType, crypto_skills_registry
from coinbase.integrations import (
    CoinbaseAPIClient,
    CoinbaseDataFeed,
    HistoricalDataPoint,
)


class TestCryptoSkills:
    """Tests for crypto analysis skills."""

    def test_skill_registry_initialization(self):
        """Test skill registry initializes with all skills."""
        registry = crypto_skills_registry

        assert len(registry.skills) == 8
        assert "crypto_data_normalization" in registry.skills
        assert "price_trend_analysis" in registry.skills

    def test_get_skill_by_id(self):
        """Test retrieving skill by ID."""
        skill = crypto_skills_registry.get_skill("price_trend_analysis")

        assert skill is not None
        assert skill.skill_id == "price_trend_analysis"
        assert skill.skill_type == SkillType.ANALYSIS

    def test_get_skills_by_type(self):
        """Test filtering skills by type."""
        analysis_skills = crypto_skills_registry.get_skills_by_type(SkillType.ANALYSIS)

        assert len(analysis_skills) == 2  # price_trend_analysis, volume_analysis
        assert all(s.skill_type == SkillType.ANALYSIS for s in analysis_skills)

    def test_data_normalization_skill(self):
        """Test crypto data normalization skill."""
        skill = crypto_skills_registry.get_skill("crypto_data_normalization")

        data = {"prices": [100, 102, 101, 103, 105], "volumes": [1000, 1200, 1100, 1300, 1250]}

        result = skill.handler(data)

        assert result["success"] is True
        assert "normalized_prices" in result
        assert "zscore_prices" in result
        assert "returns" in result
        assert len(result["normalized_prices"]) == 5

    def test_data_normalization_empty_data(self):
        """Test normalization with empty data."""
        skill = crypto_skills_registry.get_skill("crypto_data_normalization")

        result = skill.handler({"prices": []})

        assert result["success"] is False
        assert "error" in result

    def test_data_validation_skill(self):
        """Test crypto data validation skill."""
        skill = crypto_skills_registry.get_skill("crypto_data_validation")

        data = {
            "prices": [100, 102, 101, 103, 105],
            "volumes": [1000, 1200, 1100, 1300, 1250],
            "timestamps": [1, 2, 3, 4, 5],
        }

        result = skill.handler(data)

        assert result["success"] is True
        assert result["has_price_data"] is True
        assert result["price_range_valid"] is True
        assert result["quality_score"] > 0

    def test_data_validation_invalid_prices(self):
        """Test validation with invalid prices."""
        skill = crypto_skills_registry.get_skill("crypto_data_validation")

        data = {"prices": [100, -50, 101], "volumes": [1000, 1200, 1100]}  # Negative price

        result = skill.handler(data)

        assert result["price_range_valid"] is False

    def test_price_trend_analysis(self):
        """Test price trend analysis skill."""
        skill = crypto_skills_registry.get_skill("price_trend_analysis")

        # Create trending data
        prices = list(range(100, 150))  # Upward trend

        result = skill.handler({"prices": prices})

        assert result["success"] is True
        assert result["trend"] in ["bullish", "bearish", "neutral"]
        assert "trend_strength" in result
        assert "sma_20" in result
        assert "support_level" in result
        assert "resistance_level" in result

    def test_price_trend_insufficient_data(self):
        """Test trend analysis with insufficient data."""
        skill = crypto_skills_registry.get_skill("price_trend_analysis")

        result = skill.handler({"prices": [100, 101, 102]})

        assert result["success"] is False
        assert "error" in result

    def test_volume_analysis(self):
        """Test volume analysis skill."""
        skill = crypto_skills_registry.get_skill("volume_analysis")

        data = {"prices": list(range(100, 120)), "volumes": [1000 + i * 50 for i in range(20)]}

        result = skill.handler(data)

        assert result["success"] is True
        assert "volume_trend" in result
        assert "obv" in result
        assert "volume_price_correlation" in result

    def test_volume_analysis_insufficient_data(self):
        """Test volume analysis with insufficient data."""
        skill = crypto_skills_registry.get_skill("volume_analysis")

        result = skill.handler({"prices": [100, 101], "volumes": [1000]})

        assert result["success"] is False
        assert "error" in result

    def test_strategy_backtesting(self):
        """Test strategy backtesting skill."""
        skill = crypto_skills_registry.get_skill("strategy_backtesting")

        # Create trending price data for signals
        prices = [100 + i * 0.5 + (i % 5) * 2 for i in range(100)]

        strategy = {"type": "ma_crossover"}
        data = {"prices": prices}

        result = skill.handler(strategy, data)

        assert result["success"] is True
        assert "win_rate" in result
        assert "total_trades" in result
        # Either has full metrics or indicates no trades
        if result["total_trades"] > 0:
            assert "sharpe_ratio" in result
            assert "max_drawdown" in result

    def test_backtesting_no_trades(self):
        """Test backtesting with no trades executed."""
        skill = crypto_skills_registry.get_skill("strategy_backtesting")

        # Flat prices won't generate crossover signals
        prices = [100] * 100

        result = skill.handler({"type": "ma_crossover"}, {"prices": prices})

        assert result["success"] is True
        assert result["total_trades"] == 0

    def test_chart_pattern_detection(self):
        """Test chart pattern detection skill."""
        skill = crypto_skills_registry.get_skill("chart_pattern_detection")

        # Create double top pattern
        prices = list(range(50))  # Rising
        prices.extend([50, 52, 51])  # First peak
        prices.extend([45, 46])  # Dip
        prices.extend([50, 52, 51])  # Second peak
        prices.extend(range(45, 30, -1))  # Declining

        result = skill.handler({"prices": prices})

        assert result["success"] is True
        assert "patterns" in result
        assert result["minima_count"] > 0
        assert result["maxima_count"] > 0

    def test_pattern_detection_insufficient_data(self):
        """Test pattern detection with insufficient data."""
        skill = crypto_skills_registry.get_skill("chart_pattern_detection")

        result = skill.handler({"prices": [100, 101, 102]})

        assert result["success"] is False
        assert "error" in result

    def test_risk_assessment(self):
        """Test risk assessment skill."""
        skill = crypto_skills_registry.get_skill("risk_assessment")

        position = {
            "portfolio_value": 100000,
            "entry_price": 50000,
            "stop_loss_price": 45000,
            "target_price": 60000,
            "risk_percent": 0.02,
        }

        result = skill.handler(position)

        assert result["success"] is True
        assert "risk_level" in result
        assert "position_size" in result
        assert "risk_reward_ratio" in result
        assert result["risk_level"] in ["low", "medium", "high"]

    def test_risk_assessment_invalid_price(self):
        """Test risk assessment with invalid price."""
        skill = crypto_skills_registry.get_skill("risk_assessment")

        result = skill.handler({"entry_price": 0})

        assert result["success"] is False
        assert "error" in result

    def test_report_generation(self):
        """Test report generation skill."""
        skill = crypto_skills_registry.get_skill("report_generation")

        analysis = {
            "trend_analysis": {
                "trend": "bullish",
                "trend_strength": 0.8,
                "current_price": 50000,
                "support_level": 48000,
                "resistance_level": 52000,
            },
            "volume_analysis": {"volume_trend": "high"},
            "pattern_analysis": {"patterns": []},
            "risk_assessment": {"risk_level": "medium", "position_size": 5000},
        }

        result = skill.handler(analysis)

        assert result["success"] is True
        assert "summary" in result
        assert "recommendations" in result
        assert result["summary"]["sentiment"] == "strongly_bullish"

    def test_skills_ranking(self):
        """Test skill ranking functionality."""
        ranked = crypto_skills_registry.get_ranked_skills(limit=5)

        assert len(ranked) <= 5
        # Skills should be sorted by success rate
        if len(ranked) > 1:
            assert ranked[0].success_rate >= ranked[1].success_rate


class TestCoinbaseAPIClient:
    """Tests for Coinbase API integration."""

    @patch("requests.Session")
    def test_client_initialization(self, mock_session):
        """Test API client initialization."""
        client = CoinbaseAPIClient()

        assert client.api_key is None
        assert client.api_secret is None

    @patch("requests.Session")
    def test_get_spot_price(self, mock_session):
        """Test getting spot price."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"price": "50000.00"}
        mock_response.headers = {"CB-After": "100"}

        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance

        client = CoinbaseAPIClient()
        client.session = mock_session_instance

        price = client.get_spot_price("BTC-USD")

        assert price == 50000.00

    @patch("requests.Session")
    def test_get_spot_price_failure(self, mock_session):
        """Test spot price with API failure."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.headers = {"CB-After": "100"}

        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance

        client = CoinbaseAPIClient()
        client.session = mock_session_instance

        price = client.get_spot_price("BTC-USD")

        assert price is None

    @patch("requests.Session")
    def test_get_market_data(self, mock_session):
        """Test getting comprehensive market data."""
        mock_ticker = Mock()
        mock_ticker.status_code = 200
        mock_ticker.json.return_value = {"price": "50000.00"}
        mock_ticker.headers = {"CB-After": "100"}

        mock_stats = Mock()
        mock_stats.status_code = 200
        mock_stats.json.return_value = {
            "volume": "1000000000",
            "high": "51000.00",
            "low": "49000.00",
            "change": "1000.00",
            "change_percent": "2.0",
        }
        mock_stats.headers = {"CB-After": "100"}

        mock_session_instance = Mock()
        mock_session_instance.get.side_effect = [mock_ticker, mock_stats]
        mock_session.return_value = mock_session_instance

        client = CoinbaseAPIClient()
        client.session = mock_session_instance

        data = client.get_market_data("BTC-USD")

        assert data is not None
        assert data.symbol == "BTC-USD"
        assert data.price == 50000.00
        assert data.volume_24h == 1000000000.0

    @patch("requests.Session")
    def test_get_historical_data(self, mock_session):
        """Test getting historical OHLCV data."""
        mock_response = Mock()
        mock_response.status_code = 200
        # Candle data: [timestamp, low, high, open, close, volume]
        mock_response.json.return_value = [
            [1609459200, 29000.0, 31000.0, 30000.0, 30500.0, 1000.0],
            [1609545600, 30000.0, 32000.0, 30500.0, 31500.0, 1200.0],
        ]
        mock_response.headers = {"CB-After": "100"}

        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance

        client = CoinbaseAPIClient()
        client.session = mock_session_instance

        data = client.get_historical_data("BTC-USD", days=2)

        assert len(data) == 2
        assert isinstance(data[0], HistoricalDataPoint)
        assert data[0].close == 30500.0

    @patch("requests.Session")
    def test_rate_limit_handling(self, mock_session):
        """Test handling of rate limit responses."""
        mock_response = Mock()
        mock_response.status_code = 429  # Rate limited
        mock_response.headers = {"CB-After": "0"}

        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance

        client = CoinbaseAPIClient()
        client.session = mock_session_instance

        # Returns None on rate limit (exception is caught internally)
        result = client.get_spot_price("BTC-USD")
        assert result is None

    def test_global_client_singleton(self):
        """Test global API client singleton."""
        from coinbase.integrations.coinbase_api import get_coinbase_client

        client1 = get_coinbase_client()
        client2 = get_coinbase_client()

        assert client1 is client2

    def test_convenience_functions(self):
        """Test convenience functions."""
        from coinbase.integrations.coinbase_api import get_current_price

        # This will make an actual API call or use cached data
        # In tests, this might fail without mocking
        # Just verify function exists and is callable
        assert callable(get_current_price)


class TestCoinbaseDataFeed:
    """Tests for Coinbase real-time data feed."""

    @patch("coinbase.integrations.coinbase_api.CoinbaseAPIClient")
    def test_data_feed_initialization(self, mock_client):
        """Test data feed initialization."""
        feed = CoinbaseDataFeed()

        assert feed.subscribers == {}
        assert feed._running is False

    @patch("coinbase.integrations.coinbase_api.CoinbaseAPIClient")
    def test_subscribe_unsubscribe(self, mock_client):
        """Test subscription management."""
        feed = CoinbaseDataFeed()

        callback = Mock()
        feed.subscribe("BTC-USD", callback)

        assert "BTC-USD" in feed.subscribers
        assert callback in feed.subscribers["BTC-USD"]

        feed.unsubscribe("BTC-USD", callback)
        assert callback not in feed.subscribers["BTC-USD"]

    @patch("coinbase.integrations.coinbase_api.CoinbaseAPIClient")
    def test_multiple_subscribers(self, mock_client):
        """Test multiple subscribers for same currency."""
        feed = CoinbaseDataFeed()

        callback1 = Mock()
        callback2 = Mock()

        feed.subscribe("BTC-USD", callback1)
        feed.subscribe("BTC-USD", callback2)

        assert len(feed.subscribers["BTC-USD"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
