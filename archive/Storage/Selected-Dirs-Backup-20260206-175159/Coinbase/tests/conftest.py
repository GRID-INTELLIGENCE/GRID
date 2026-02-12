"""
Pytest configuration for Coinbase tests.
Sets up environment variables and fixtures for test isolation.
"""

import pytest


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """
    Set up test environment variables.
    This runs automatically for all tests.
    """
    # Enable offline mode for Databricks tests
    monkeypatch.setenv("DATABRICKS_OFFLINE", "1")

    # Mock other environment variables if needed
    monkeypatch.setenv("DATABRICKS_HOST", "test-host")
    monkeypatch.setenv("DATABRICKS_HTTP_PATH", "test-path")
    monkeypatch.setenv("DATABRICKS_TOKEN", "test-token")


@pytest.fixture
def mcp_server_mock():
    """
    Mock MCP server for tests that require it.
    Skips tests if mcp_setup module is not available.
    """
    try:
        from mcp_setup.server.portfolio_safety_mcp_server import PortfolioSafetyLensServer

        return PortfolioSafetyLensServer
    except ImportError:
        pytest.skip("mcp_setup module not available - requires grid repo")
