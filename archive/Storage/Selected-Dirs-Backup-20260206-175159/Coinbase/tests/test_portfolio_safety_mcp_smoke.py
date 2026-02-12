"""
Smoke Tests for Portfolio Safety Lens MCP Server
=================================================
Quick validation that server starts and returns safe outputs.
"""

import json
from unittest.mock import Mock

import pytest


class TestMCPServerSmoke:
    """Smoke tests for Portfolio Safety Lens MCP server."""

    @pytest.fixture
    def server(self):
        """Create server instance."""
        try:
            from mcp_setup.server.portfolio_safety_mcp_server import PortfolioSafetyLensServer
        except ImportError:
            pytest.skip("mcp_setup module not available - requires grid repo")

        # Mock dependencies to avoid actual DB calls
        with (
            patch(
                "mcp_setup.server.portfolio_safety_mcp_server.get_portfolio_security"
            ) as mock_security,
            patch(
                "mcp_setup.server.portfolio_safety_mcp_server.get_portfolio_data_policy"
            ) as mock_policy,
            patch("mcp_setup.server.portfolio_safety_mcp_server.get_ai_safety") as mock_ai,
            patch("mcp_setup.server.portfolio_safety_mcp_server.get_audit_logger") as mock_audit,
            patch(
                "mcp_setup.server.portfolio_safety_mcp_server.get_ai_safe_analyzer"
            ) as mock_analyzer,
        ):

            mock_security.return_value = Mock()
            mock_policy.return_value = Mock()
            mock_ai.return_value = Mock()
            mock_audit.return_value = Mock()
            mock_analyzer.return_value = Mock()

            return PortfolioSafetyLensServer()

    def test_server_initializes(self, server):
        """Test that server initializes without errors."""
        assert server is not None
        assert server.server is not None

    @pytest.mark.asyncio
    async def test_list_tools_returns_four_tools(self, server):
        """Test that server returns exactly four tools."""
        result = await server.server.list_tools()

        assert result is not None
        assert len(result.tools) == 4

        tool_names = [tool.name for tool in result.tools]
        expected_tools = [
            "portfolio_summary_safe",
            "portfolio_risk_signal",
            "audit_log_tail",
            "governance_lint",
        ]

        for expected in expected_tools:
            assert expected in tool_names

    @pytest.mark.asyncio
    async def test_portfolio_summary_safe_tool_exists(self, server):
        """Test that portfolio_summary_safe tool is properly defined."""
        result = await server.server.list_tools()

        tool = next((t for t in result.tools if t.name == "portfolio_summary_safe"), None)
        assert tool is not None
        assert "sanitized" in tool.description.lower()
        assert "user_id" in tool.inputSchema["properties"]

    @pytest.mark.asyncio
    async def test_portfolio_risk_signal_tool_exists(self, server):
        """Test that portfolio_risk_signal tool is properly defined."""
        result = await server.server.list_tools()

        tool = next((t for t in result.tools if t.name == "portfolio_risk_signal"), None)
        assert tool is not None
        assert "risk" in tool.description.lower()
        assert "user_id" in tool.inputSchema["properties"]

    @pytest.mark.asyncio
    async def test_audit_log_tail_tool_exists(self, server):
        """Test that audit_log_tail tool is properly defined."""
        result = await server.server.list_tools()

        tool = next((t for t in result.tools if t.name == "audit_log_tail"), None)
        assert tool is not None
        assert "audit" in tool.description.lower()
        assert "limit" in tool.inputSchema["properties"]

    @pytest.mark.asyncio
    async def test_governance_lint_tool_exists(self, server):
        """Test that governance_lint tool is properly defined."""
        result = await server.server.list_tools()

        tool = next((t for t in result.tools if t.name == "governance_lint"), None)
        assert tool is not None
        assert "governance" in tool.description.lower() or "compliance" in tool.description.lower()
        assert "user_id" in tool.inputSchema["properties"]

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(self, server):
        """Test that calling unknown tool returns error."""
        result = await server.server.call_tool("unknown_tool", {})

        assert result.isError
        assert "Unknown tool" in result.content[0].text


class TestMCPToolOutputSafety:
    """Tests that MCP tool outputs are safe and sanitized."""

    @pytest.fixture
    def mock_server(self):
        """Create mock server with mocked dependencies."""
        try:
            from mcp_setup.server.portfolio_safety_mcp_server import PortfolioSafetyLensServer
        except ImportError:
            pytest.skip("mcp_setup module not available - requires grid repo")

        server = PortfolioSafetyLensServer()

        # Mock all dependencies
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
                "positions": [],
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

        return server

    @pytest.mark.asyncio
    async def test_portfolio_summary_safe_output_structure(self, mock_server):
        """Test that portfolio_summary_safe returns proper structure."""
        result = await mock_server._portfolio_summary_safe({"user_id": "user123"})

        assert not result.isError

        content = result.content[0].text
        data = json.loads(content)

        # Verify structure
        assert isinstance(data, dict)
        assert "total_positions" in data
        assert "total_value" in data
        assert "timestamp" in data

        # Verify no raw positions
        assert "positions" not in data

    @pytest.mark.asyncio
    async def test_portfolio_risk_signal_output_structure(self, mock_server):
        """Test that portfolio_risk_signal returns proper structure."""
        result = await mock_server._portfolio_risk_signal({"user_id": "user123"})

        assert not result.isError

        content = result.content[0].text
        data = json.loads(content)

        # Verify structure
        assert isinstance(data, dict)
        assert "risk_level" in data
        assert "concentration_risk" in data
        assert "diversification" in data

        # Verify no raw data
        assert "positions" not in data

    @pytest.mark.asyncio
    async def test_audit_log_tail_output_structure(self, mock_server):
        """Test that audit_log_tail returns proper structure."""
        result = await mock_server._audit_log_tail({"limit": 10})

        assert not result.isError

        content = result.content[0].text
        data = json.loads(content)

        # Verify structure
        assert isinstance(data, list)

        # Verify hashed IDs
        if data:
            assert "user_id_hash" in data[0]
            assert data[0]["user_id_hash"].endswith("...")

    @pytest.mark.asyncio
    async def test_governance_lint_output_structure(self, mock_server):
        """Test that governance_lint returns proper structure."""
        result = await mock_server._governance_lint({"user_id": "user123"})

        assert not result.isError

        content = result.content[0].text
        data = json.loads(content)

        # Verify structure
        assert isinstance(data, dict)
        assert "policy_compliant" in data
        assert "user_id_hashed" in data
        assert "audit_logging_enabled" in data


class TestMCPToolErrorHandling:
    """Tests error handling in MCP tools."""

    @pytest.fixture
    def mock_server(self):
        """Create mock server."""
        try:
            from mcp_setup.server.portfolio_safety_mcp_server import PortfolioSafetyLensServer
        except ImportError:
            pytest.skip("mcp_setup module not available - requires grid repo")

        server = PortfolioSafetyLensServer()
        server.security = Mock()
        server.policy = Mock()
        server.ai_safety = Mock()
        server.audit_logger = Mock()
        server.analyzer = Mock()

        return server

    @pytest.mark.asyncio
    async def test_portfolio_summary_safe_missing_user_id(self, mock_server):
        """Test error when user_id is missing."""
        result = await mock_server._portfolio_summary_safe({})

        assert result.isError
        assert "user_id is required" in result.content[0].text

    @pytest.mark.asyncio
    async def test_portfolio_risk_signal_missing_user_id(self, mock_server):
        """Test error when user_id is missing."""
        result = await mock_server._portfolio_risk_signal({})

        assert result.isError
        assert "user_id is required" in result.content[0].text

    @pytest.mark.asyncio
    async def test_governance_lint_missing_user_id(self, mock_server):
        """Test error when user_id is missing."""
        result = await mock_server._governance_lint({})

        assert result.isError
        assert "user_id is required" in result.content[0].text

    @pytest.mark.asyncio
    async def test_exception_handling(self, mock_server):
        """Test that exceptions are handled gracefully."""
        mock_server.analyzer.analyze_portfolio = Mock(side_effect=Exception("Test error"))

        result = await mock_server._portfolio_summary_safe({"user_id": "user123"})

        assert result.isError
        assert "Error:" in result.content[0].text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
