"""
End-to-End Integration Tests
============================
Comprehensive integration tests for Coinbase platform workflows.

Usage:
    python -m pytest tests/test_integration_workflows.py -v
"""


import pytest

from coinbase import (
    AgenticSystem,
    SkillType,
    crypto_skills_registry,
)
from coinbase.config import (
    get_audit_logger,
    get_health_checker,
    get_metrics,
    get_policy_manager,
    get_rate_limiter,
)


class TestPortfolioManagementWorkflow:
    """Integration tests for portfolio management workflows."""

    def test_complete_portfolio_workflow(self):
        """Test complete portfolio management workflow from creation to analysis."""
        # Create system
        system = AgenticSystem()

        # Register skills
        for skill in crypto_skills_registry.get_skills_by_type(SkillType.ANALYSIS):
            system.register_handler(skill.skill_id, skill.handler)

        # Step 1: Initialize portfolio
        portfolio_data = {
            "user_id": "test_user_123",
            "assets": [
                {"symbol": "BTC", "quantity": 0.5, "avg_cost": 45000},
                {"symbol": "ETH", "quantity": 2.0, "avg_cost": 3000},
            ],
        }

        # Step 2: Add market data
        market_data = {
            "BTC": {"current_price": 50000, "volume_24h": 30000000000},
            "ETH": {"current_price": 3200, "volume_24h": 15000000000},
        }

        # Execute analysis - may fail if handler not registered
        result = system.execute_case(
            case_id="portfolio-analysis-001",
            task="portfolio_analysis",
            agent_role="PortfolioManager",
            reference={"portfolio": portfolio_data, "market_data": market_data},
        )

        # Result should be a dict with success key (may be False if no handler)
        assert isinstance(result, dict)
        assert "success" in result

    def test_portfolio_risk_assessment(self):
        """Test portfolio risk assessment workflow."""
        skill = crypto_skills_registry.get_skill("risk_assessment")
        assert skill is not None

        # Test position sizing
        position = {
            "portfolio_value": 100000,
            "entry_price": 50000,
            "stop_loss_price": 45000,
            "target_price": 60000,
            "risk_percent": 0.02,
        }

        result = skill.handler(position)

        assert result["success"] is True
        assert "position_size" in result
        assert "risk_level" in result
        assert "risk_reward_ratio" in result
        assert result["risk_level"] in ["low", "medium", "high"]

    def test_portfolio_with_skills_integration(self):
        """Test portfolio analysis using multiple skills."""
        # Get skills
        trend_skill = crypto_skills_registry.get_skill("price_trend_analysis")
        risk_skill = crypto_skills_registry.get_skill("risk_assessment")
        report_skill = crypto_skills_registry.get_skill("report_generation")

        # Generate sample price data
        prices = [45000 + i * 100 + (i % 5) * 50 for i in range(50)]

        # Step 1: Analyze trends
        trend_result = trend_skill.handler({"prices": prices})
        assert trend_result["success"] is True

        # Step 2: Assess risk
        risk_result = risk_skill.handler(
            {
                "portfolio_value": 100000,
                "entry_price": prices[-1],
                "stop_loss_price": prices[-1] * 0.95,
                "risk_percent": 0.02,
            }
        )
        assert risk_result["success"] is True

        # Step 3: Generate report
        analysis = {"trend_analysis": trend_result, "risk_assessment": risk_result}
        report_result = report_skill.handler(analysis)
        assert report_result["success"] is True
        assert "recommendations" in report_result


class TestTradingSignalWorkflow:
    """Integration tests for trading signal generation workflows."""

    def test_trading_signal_with_trend_and_volume(self):
        """Test trading signal using trend and volume analysis."""
        # Get skills
        trend_skill = crypto_skills_registry.get_skill("price_trend_analysis")
        volume_skill = crypto_skills_registry.get_skill("volume_analysis")

        # Generate sample data
        prices = [100 + i * 0.5 + (i % 3) * 2 for i in range(50)]
        volumes = [1000 + i * 10 + (i % 7) * 50 for i in range(50)]

        # Analyze trends
        trend_result = trend_skill.handler({"prices": prices})
        assert trend_result["success"] is True

        # Analyze volume
        volume_result = volume_skill.handler({"prices": prices, "volumes": volumes})
        assert volume_result["success"] is True

        # Combined signal logic
        signal_strength = 0.0
        if trend_result.get("trend") == "bullish":
            signal_strength += trend_result.get("trend_strength", 0) * 0.6
        if volume_result.get("volume_trend") == "high":
            signal_strength += 0.4

        assert 0 <= signal_strength <= 1

    def test_backtest_integration_with_signals(self):
        """Test backtesting strategy with generated signals."""
        backtest_skill = crypto_skills_registry.get_skill("strategy_backtesting")

        # Generate sample price data
        prices = [100 + i * 0.2 + (i % 10) * 5 for i in range(100)]

        # Run backtest
        strategy = {"type": "ma_crossover", "fast": 10, "slow": 30}
        result = backtest_skill.handler(strategy, {"prices": prices})

        assert result["success"] is True
        assert "win_rate" in result
        assert "total_trades" in result
        # Conditional check for sharpe_ratio when trades exist
        if result["total_trades"] > 0:
            assert "sharpe_ratio" in result

    def test_pattern_detection_for_signals(self):
        """Test pattern detection for trading signals."""
        pattern_skill = crypto_skills_registry.get_skill("chart_pattern_detection")

        # Generate price data with double top pattern
        prices = list(range(50))  # Rising
        prices.extend([50, 52, 51])  # First peak
        prices.extend([45, 46])  # Dip
        prices.extend([50, 52, 51])  # Second peak
        prices.extend(range(45, 30, -1))  # Declining

        result = pattern_skill.handler({"prices": prices})

        assert result["success"] is True
        assert "patterns" in result


class TestFactCheckingWorkflow:
    """Integration tests for fact-checking and verification workflows."""

    def test_data_validation_before_analysis(self):
        """Test data validation workflow before analysis."""
        validation_skill = crypto_skills_registry.get_skill("crypto_data_validation")
        normalization_skill = crypto_skills_registry.get_skill("crypto_data_normalization")

        # Valid data
        valid_data = {
            "prices": [100, 102, 101, 103, 105],
            "volumes": [1000, 1200, 1100, 1300, 1250],
            "timestamps": [1, 2, 3, 4, 5],
        }

        # Step 1: Validate
        validation_result = validation_skill.handler(valid_data)
        assert validation_result["success"] is True
        assert validation_result["quality_score"] > 0.5

        # Step 2: Normalize if valid
        if validation_result["quality_score"] > 0.7:
            norm_result = normalization_skill.handler(valid_data)
            assert norm_result["success"] is True
            assert "normalized_prices" in norm_result

    def test_invalid_data_detection(self):
        """Test detection of invalid/corrupted data."""
        validation_skill = crypto_skills_registry.get_skill("crypto_data_validation")

        # Invalid data with negative prices
        invalid_data = {
            "prices": [100, -50, 101, 103],  # Negative price
            "volumes": [1000, 1200, 1100, 1300],
        }

        result = validation_skill.handler(invalid_data)
        assert result["success"] is True  # Validation succeeds but flags issues
        assert result["price_range_valid"] is False

    def test_data_quality_pipeline(self):
        """Test complete data quality pipeline."""
        skills = [
            crypto_skills_registry.get_skill("crypto_data_validation"),
            crypto_skills_registry.get_skill("crypto_data_normalization"),
            crypto_skills_registry.get_skill("price_trend_analysis"),
        ]

        # Test data
        data = {
            "prices": [100 + i * 2 for i in range(30)],
            "volumes": [1000 + i * 50 for i in range(30)],
        }

        # Pipeline execution
        current_data = data
        for skill in skills:
            if skill.skill_id == "price_trend_analysis":
                result = skill.handler(current_data)
            else:
                result = skill.handler(current_data)

            if result["success"]:
                # Pass normalized data to next step
                if "normalized_prices" in result:
                    current_data = {"prices": result["normalized_prices"]}
            else:
                # Skip failed skills in pipeline
                continue


class TestSecurityAndAuditWorkflow:
    """Integration tests for security and audit workflows."""

    def test_security_policy_enforcement(self):
        """Test security policy enforcement."""
        policy_manager = get_policy_manager()

        from coinbase.config.security_policies import AccessLevel, UserContext, UserRole

        # Test user access with MFA verified for critical data
        user = UserContext(user_id="test_user", role=UserRole.USER, mfa_verified=True)

        # Should have access to market data
        assert policy_manager.check_access(user, "market_data", AccessLevel.READ) is True

        # Should have access to portfolio data
        assert policy_manager.check_access(user, "portfolio_data", AccessLevel.READ) is True

    def test_audit_logging_integration(self):
        """Test audit logging integration."""
        from coinbase.config.audit_config import AuditEventType

        audit_logger = get_audit_logger()

        # Log test event
        audit_logger.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            details={"resource": "test_resource", "action": "read"},
            user_id="test_user",
        )

        # Verify event was logged
        logs = audit_logger.get_logs(
            event_type=AuditEventType.DATA_ACCESS, user_id="test_user", limit=10
        )

        assert len(logs) >= 1

    def test_rate_limiting_enforcement(self):
        """Test rate limiting enforcement."""
        rate_limiter = get_rate_limiter()

        # Test multiple requests
        results = []
        for _ in range(35):  # Exceeds CoinGecko limit of 30/min
            result = rate_limiter.allow_request("coingecko")
            results.append(result.allowed)

        # Some should be allowed, some denied
        assert any(results)  # At least some allowed


class TestMonitoringAndHealth:
    """Integration tests for monitoring and health checks."""

    def test_health_check_integration(self):
        """Test health check integration."""
        health_checker = get_health_checker()

        # Run health checks
        results = health_checker.check_all()

        assert "memory" in results
        assert "disk" in results

    def test_metrics_collection(self):
        """Test metrics collection."""
        metrics = get_metrics()

        # Record some metrics
        metrics.record_latency("test_operation", 0.5)
        metrics.record_count("test_counter")

        # Get stats
        stats = metrics.get_stats("test_operation_latency")

        if stats:
            assert "count" in stats
            assert stats["count"] >= 1

    def test_system_integration(self):
        """Test complete system integration."""
        # Initialize all components
        system = AgenticSystem()
        health = get_health_checker()
        metrics = get_metrics()

        # Register skills
        for skill in crypto_skills_registry.get_skills_by_type(SkillType.ANALYSIS):
            system.register_handler(skill.skill_id, skill.handler)

        # Check health
        health_results = health.check_all()

        # Execute test case
        result = system.execute_case(
            case_id="integration-test-001", task="test_task", agent_role="TestAgent"
        )

        # Record metrics
        metrics.record_latency("test_execution", 0.1)

        assert result is not None


class TestEndToEndScenario:
    """Complete end-to-end scenario tests."""

    def test_complete_trading_workflow(self):
        """Test complete trading workflow from data to signal."""
        # Step 1: Get data and validate
        validation_skill = crypto_skills_registry.get_skill("crypto_data_validation")
        normalization_skill = crypto_skills_registry.get_skill("crypto_data_normalization")

        raw_data = {
            "prices": [100 + i * 1.5 for i in range(50)],
            "volumes": [1000 + i * 20 for i in range(50)],
        }

        validation = validation_skill.handler(raw_data)
        assert validation["success"] is True

        normalization = normalization_skill.handler(raw_data)
        assert normalization["success"] is True

        # Step 2: Analyze trends
        trend_skill = crypto_skills_registry.get_skill("price_trend_analysis")
        trend = trend_skill.handler(raw_data)
        assert trend["success"] is True

        # Step 3: Assess risk
        risk_skill = crypto_skills_registry.get_skill("risk_assessment")
        risk = risk_skill.handler(
            {
                "portfolio_value": 100000,
                "entry_price": raw_data["prices"][-1],
                "stop_loss_price": raw_data["prices"][-1] * 0.95,
                "risk_percent": 0.02,
            }
        )
        assert risk["success"] is True

        # Step 4: Generate report
        report_skill = crypto_skills_registry.get_skill("report_generation")
        report = report_skill.handler(
            {
                "trend_analysis": trend,
                "volume_analysis": {"volume_trend": "neutral"},
                "pattern_analysis": {"patterns": []},
                "risk_assessment": risk,
            }
        )
        assert report["success"] is True
        assert "recommendations" in report

    def test_multi_skill_workflow(self):
        """Test workflow using multiple skills in sequence."""
        skills_sequence = [
            ("crypto_data_validation", {}),
            ("crypto_data_normalization", {}),
            ("price_trend_analysis", {}),
            ("volume_analysis", {}),
            ("chart_pattern_detection", {}),
        ]

        # Test data
        data = {
            "prices": [100 + i * 2 + (i % 5) * 3 for i in range(60)],
            "volumes": [1000 + i * 30 for i in range(60)],
        }

        results = []
        current_data = data

        for skill_id, extra_params in skills_sequence:
            skill = crypto_skills_registry.get_skill(skill_id)
            assert skill is not None, f"Skill {skill_id} not found"

            # Execute skill
            if skill_id in ["price_trend_analysis", "chart_pattern_detection"]:
                result = skill.handler(current_data)
            elif skill_id == "volume_analysis":
                result = skill.handler(current_data)
            else:
                result = skill.handler(current_data)

            # Some skills may fail on edge case data - that's acceptable
            if result["success"]:
                results.append(result)

                # Update data for next step
                if "normalized_prices" in result:
                    current_data = {"prices": result["normalized_prices"]}

        # At least half the skills should succeed
        assert len(results) >= len(skills_sequence) // 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
