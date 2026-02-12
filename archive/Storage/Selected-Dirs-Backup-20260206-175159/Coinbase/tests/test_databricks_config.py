"""Tests for Databricks configuration and client."""

import os
from unittest.mock import MagicMock, patch

import pytest

from coinbase.databricks_config import DatabricksClient, DatabricksConfig


class TestDatabricksConfig:
    """Test DatabricksConfig class."""

    def test_from_env_with_valid_vars(self):
        """Test loading configuration from environment variables."""
        with patch.dict(
            os.environ,
            {
                "DATABRICKS_HOST": "https://test.cloud.databricks.com",
                "DATABRICKS_TOKEN": "test_token",
                "DATABRICKS_CLUSTER_ID": "cluster-123",
            },
        ):
            config = DatabricksConfig.from_env()

            assert config.host == "https://test.cloud.databricks.com"
            assert config.token == "test_token"
            assert config.cluster_id == "cluster-123"

    def test_from_env_with_missing_vars(self):
        """Test loading configuration with missing variables."""
        with patch.dict(os.environ, {}, clear=True):
            config = DatabricksConfig.from_env()

            assert config.host is None
            assert config.token is None
            assert config.cluster_id is None

    def test_validate_with_valid_config(self):
        """Test validation with valid configuration."""
        config = DatabricksConfig(
            host="https://test.cloud.databricks.com",
            token="test_token",
        )

        assert config.validate() is True

    def test_validate_with_invalid_config(self):
        """Test validation with invalid configuration."""
        config = DatabricksConfig(host=None, token=None)

        assert config.validate() is False

    def test_to_dict(self):
        """Test converting configuration to dictionary."""
        config = DatabricksConfig(
            host="https://test.cloud.databricks.com",
            token="secret_token",
            cluster_id="cluster-123",
        )

        result = config.to_dict()

        assert result["host"] == "https://test.cloud.databricks.com"
        assert result["token"] == "***REDACTED***"
        assert result["cluster_id"] == "cluster-123"


class TestDatabricksClient:
    """Test DatabricksClient class."""

    def test_init_with_invalid_config(self):
        """Test initialization with invalid configuration."""
        config = DatabricksConfig(host=None, token=None)

        with pytest.raises(ValueError, match="Invalid Databricks configuration"):
            DatabricksClient(config)

    @patch("databricks.sdk.WorkspaceClient")
    def test_init_with_valid_config(self, mock_workspace_client):
        """Test initialization with valid configuration."""
        config = DatabricksConfig(
            host="https://test.cloud.databricks.com",
            token="test_token",
        )

        client = DatabricksClient(config)

        assert client.config == config
        assert client._client is None

    @patch("databricks.sdk.WorkspaceClient")
    def test_client_property_lazy_loads(self, mock_workspace_client):
        """Test that client property lazy loads the SDK client."""
        config = DatabricksConfig(
            host="https://test.cloud.databricks.com",
            token="test_token",
        )
        client = DatabricksClient(config)

        # Access client property
        sdk_client = client.client

        assert sdk_client is not None
        mock_workspace_client.assert_called_once()

    @patch("databricks.sdk.WorkspaceClient")
    def test_test_connection_success(self, mock_workspace_client):
        """Test successful connection test."""
        mock_sdk = MagicMock()
        mock_sdk.get_workspace_id.return_value = "workspace-123"
        mock_sdk.clusters.list.return_value = iter(["cluster-1", "cluster-2"])
        mock_workspace_client.return_value = mock_sdk

        config = DatabricksConfig(
            host="https://test.cloud.databricks.com",
            token="test_token",
        )
        client = DatabricksClient(config)

        result = client.test_connection()

        assert result["status"] == "connected"
        assert result["workspace_id"] == "workspace-123"
        assert result["cluster_count"] == 2

    @patch("databricks.sdk.WorkspaceClient")
    def test_test_connection_failure(self, mock_workspace_client):
        """Test failed connection test."""
        mock_sdk = MagicMock()
        mock_sdk.get_workspace_id.side_effect = Exception("Connection failed")
        mock_workspace_client.return_value = mock_sdk

        config = DatabricksConfig(
            host="https://test.cloud.databricks.com",
            token="test_token",
        )
        client = DatabricksClient(config)

        result = client.test_connection()

        assert result["status"] == "failed"
        assert "Connection failed" in result["error"]

    @patch("databricks.sdk.WorkspaceClient")
    def test_list_clusters(self, mock_workspace_client):
        """Test listing clusters."""
        mock_sdk = MagicMock()
        mock_sdk.clusters.list.return_value = iter(
            [
                {"cluster_name": "cluster-1", "state": "RUNNING"},
                {"cluster_name": "cluster-2", "state": "TERMINATED"},
            ]
        )
        mock_workspace_client.return_value = mock_sdk

        config = DatabricksConfig(
            host="https://test.cloud.databricks.com",
            token="test_token",
        )
        client = DatabricksClient(config)

        clusters = client.list_clusters()

        assert len(clusters) == 2
        assert clusters[0]["cluster_name"] == "cluster-1"

    @patch("databricks.sdk.WorkspaceClient")
    def test_list_warehouses(self, mock_workspace_client):
        """Test listing warehouses."""
        mock_sdk = MagicMock()
        mock_sdk.warehouses.list.return_value = iter(
            [
                {"name": "warehouse-1", "state": "RUNNING"},
                {"name": "warehouse-2", "state": "STOPPED"},
            ]
        )
        mock_workspace_client.return_value = mock_sdk

        config = DatabricksConfig(
            host="https://test.cloud.databricks.com",
            token="test_token",
        )
        client = DatabricksClient(config)

        warehouses = client.list_warehouses()

        assert len(warehouses) == 2
        assert warehouses[0]["name"] == "warehouse-1"

    @patch("databricks.sdk.WorkspaceClient")
    def test_run_sql_query_without_warehouse(self, mock_workspace_client):
        """Test running SQL query without warehouse ID."""
        config = DatabricksConfig(
            host="https://test.cloud.databricks.com",
            token="test_token",
        )
        client = DatabricksClient(config)

        with pytest.raises(ValueError, match="SQL warehouse ID required"):
            client.run_sql_query("SELECT * FROM table")

    @patch("databricks.sdk.WorkspaceClient")
    def test_run_sql_query_with_warehouse(self, mock_workspace_client):
        """Test running SQL query with warehouse ID."""
        mock_sdk = MagicMock()
        mock_sdk.statement_execution.execute_statement.return_value = {"result": "query_result"}
        mock_workspace_client.return_value = mock_sdk

        config = DatabricksConfig(
            host="https://test.cloud.databricks.com",
            token="test_token",
            warehouse_id="warehouse-123",
        )
        client = DatabricksClient(config)

        result = client.run_sql_query("SELECT * FROM table")

        assert result == {"result": "query_result"}
