"""
Integration Tests for Portfolio Safety Lens MCP Tools
======================================================
Tests MCP tool integration with full audit trails.
"""

import json
from unittest.mock import Mock

import pytest


class TestPortfolioSafetyLensMCPTools:
    """Integration tests for Portfolio Safety Lens MCP tools."""

    @pytest.fixture
    def mock_server(self):
        """Create mock MCP server with mocked dependencies."""
        try:
            from mcp_setup.server.portfolio_safety_mcp_server import PortfolioSafetyLensServer
        except ImportError:
            pytest.skip("mcp_setup module not available - requires grid repo")

        server = PortfolioSafetyLensServer()

        # Mock dependencies
        server.security = Mock()
        server.security.create_security_context = Mock()
        server.security.validate_access = Mock(return_value=True)

        server.policy = Mock()
        server.policy.validate_output_dict = Mock(side_effect=lambda x, **kwargs: x)

        server.ai_safety = Mock()
        server.ai_safety.validate_ai_access = Mock(return_value=True)
        server.ai_safety.sanitize_for_ai_output = Mock(side_effect=lambda x: x)

        server.audit_logger = Mock()
        server.audit_logger.log_event = Mock()
        server.audit_logger.get_logs = Mock(return_value=[])

        server.analyzer = Mock()
        server.analyzer.analyze_portfolio = Mock(
            return_value={
                "total_positions": 5,
                "total_value": 50000.0,
                "total_gain_loss": 2500.0,
                "gain_loss_percentage": 5.0,
                "positions": [
                    {"symbol": "AAPL", "quantity": 100, "current_value": 17500.0},
                    {"symbol": "GOOGL", "quantity": 50, "current_value": 15000.0},
                ],
            }
        )
        server.analyzer.get_concentration_risk = Mock(
            return_value={
                "risk_level": "MEDIUM",
                "top_position_percentage": 35.0,
                "top_3_percentage": 65.0,
                "recommendation": "Consider diversifying",
            }
        )
        server.analyzer.get_sector_allocation = Mock(
            return_value={"Technology": 60.0, "Finance": 25.0, "Healthcare": 15.0}
        )

        return server

    @pytest.mark.asyncio
    async def test_portfolio_summary_safe_no_raw_positions(self, mock_server):
        """Test that portfolio_summary_safe returns no raw positions."""
        result = await mock_server._portfolio_summary_safe({"user_id": "user123"})

        # Parse result
        content = result.content[0].text
        data = json.loads(content)

        # Verify no raw positions
        assert "positions" not in data
        assert "positions_count" in data
        assert data["positions_count"] == 5

        # Verify audit logging
        mock_server.audit_logger.log_event.assert_called_once()
        call_args = mock_server.audit_logger.log_event.call_args
        assert call_args[1]["action"] == "portfolio_summary_safe"

    @pytest.mark.asyncio
    async def test_portfolio_summary_safe_sanitized_metrics(self, mock_server):
        """Test that portfolio_summary_safe returns sanitized metrics."""
        result = await mock_server._portfolio_summary_safe({"user_id": "user123"})

        content = result.content[0].text
        data = json.loads(content)

        # Verify metrics are present
        assert "total_value" in data
        assert "total_gain_loss" in data
        assert "gain_loss_percentage" in data
        assert "timestamp" in data

        # Verify no sensitive fields
        assert "quantity" not in str(data)
        assert "purchase_price" not in str(data)

    @pytest.mark.asyncio
    async def test_portfolio_risk_signal_no_raw_data(self, mock_server):
        """Test that portfolio_risk_signal returns no raw data."""
        result = await mock_server._portfolio_risk_signal({"user_id": "user123"})

        content = result.content[0].text
        data = json.loads(content)

        # Verify risk scores only
        assert "risk_level" in data
        assert "concentration_risk" in data
        assert "diversification" in data

        # Verify no raw positions
        assert "positions" not in data
        assert "quantity" not in str(data)

        # Verify audit logging
        mock_server.audit_logger.log_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_audit_log_tail_hashed_ids_only(self, mock_server):
        """Test that audit_log_tail returns hashed IDs only."""
        # Setup mock logs
        from datetime import datetime

        from coinbase.security.audit_logger import AuditEvent

        mock_logs = [
            AuditEvent(
                timestamp=datetime.now(),
                event_type="READ",
                user_id="user123",
                action="get_positions",
                details={"symbol": "AAPL"},
            )
        ]
        mock_server.audit_logger.get_logs = Mock(return_value=mock_logs)

        result = await mock_server._audit_log_tail({"limit": 10})

        content = result.content[0].text
        data = json.loads(content)

        # Verify hashed IDs
        assert len(data) == 1
        assert "user_id_hash" in data[0]
        assert data[0]["user_id_hash"].endswith("...")
        assert "user123" not in data[0]["user_id_hash"]

    @pytest.mark.asyncio
    async def test_audit_log_tail_sanitized_details(self, mock_server):
        """Test that audit_log_tail sanitizes details."""
        from datetime import datetime

        from coinbase.security.audit_logger import AuditEvent

        mock_logs = [
            AuditEvent(
                timestamp=datetime.now(),
                event_type="READ",
                user_id="user123",
                action="get_positions",
                details={"symbol": "AAPL", "quantity": 100},
            )
        ]
        mock_server.audit_logger.get_logs = Mock(return_value=mock_logs)

        result = await mock_server._audit_log_tail({"limit": 10})

        content = result.content[0].text
        data = json.loads(content)

        # Verify details are not exposed
        assert "details_count" in data[0]
        assert "details" not in data[0]

    @pytest.mark.asyncio
    async def test_governance_lint_compliance_check(self, mock_server):
        """Test that governance_lint checks compliance."""
        result = await mock_server._governance_lint({"user_id": "user123"})

        content = result.content[0].text
        data = json.loads(content)

        # Verify compliance checks
        assert "user_id_hashed" in data
        assert "critical_data_protected" in data
        assert "audit_logging_enabled" in data
        assert "ai_safety_enforced" in data
        assert "output_sanitization" in data
        assert "policy_compliant" in data

        # All should be True
        assert all(data.values())

        # Verify audit logging
        mock_server.audit_logger.log_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_full_workflow_audit_trail(self, mock_server):
        """Test that full workflow creates complete audit trail."""
        # Call all tools
        await mock_server._portfolio_summary_safe({"user_id": "user123"})
        await mock_server._portfolio_risk_signal({"user_id": "user123"})
        await mock_server._audit_log_tail({"limit": 10})
        await mock_server._governance_lint({"user_id": "user123"})

        # Verify all calls logged
        assert mock_server.audit_logger.log_event.call_count == 4

        # Verify actions logged
        actions = [call[1]["action"] for call in mock_server.audit_logger.log_event.call_args_list]
        assert "portfolio_summary_safe" in actions
        assert "portfolio_risk_signal" in actions
        assert "audit_log_tail" in actions
        assert "governance_lint" in actions

    @pytest.mark.asyncio
    async def test_error_handling_missing_user_id(self, mock_server):
        """Test that missing user_id returns error."""
        result = await mock_server._portfolio_summary_safe({})

        assert result.isError
        assert "user_id is required" in result.content[0].text

    @pytest.mark.asyncio
    async def test_error_handling_exception(self, mock_server):
        """Test that exceptions are handled gracefully."""
        mock_server.analyzer.analyze_portfolio = Mock(side_effect=Exception("DB error"))

        result = await mock_server._portfolio_summary_safe({"user_id": "user123"})

        assert result.isError
        assert "Error:" in result.content[0].text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
