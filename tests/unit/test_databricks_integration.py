"""Unit tests for Databricks SDK integration with GRID."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, Mock, patch

import pytest

# Test imports from integration module
pytest.importorskip("databricks.sdk")

from src.integration.databricks.client import DatabricksClient
from src.integration.databricks.clusters import DatabricksClustersManager
from src.integration.databricks.jobs import DatabricksJobsManager
from src.integration.databricks.notebooks import DatabricksNotebooksManager


class TestDatabricksClientAuthentication:
    """Test DatabricksClient authentication mechanisms."""

    def test_client_requires_host_or_profile(self):
        """Client should require either host or profile."""
        with patch("src.integration.databricks.client.WorkspaceClient"):
            with patch.dict(os.environ, {"DATABRICKS_HOST": "", "databricks": "", "DATABRICKS_TOKEN": ""}, clear=False):
                with pytest.raises(ValueError):
                    DatabricksClient(token="test-token")

    def test_client_requires_token_or_profile(self):
        """Client should require either token or profile."""
        # Clear any environment variables that might provide a token
        with patch.dict(os.environ, {"databricks": "", "DATABRICKS_TOKEN": ""}, clear=False):
            with pytest.raises(ValueError):
                DatabricksClient(host="https://test.cloud.databricks.com")

    @patch.dict(os.environ, {"DATABRICKS_HOST": "https://test.cloud.databricks.com"})
    def test_client_uses_databricks_host_env_var(self):
        """Client should use DATABRICKS_HOST environment variable."""
        with patch("src.integration.databricks.client.WorkspaceClient") as mock_ws:
            # Mock the workspace client and its methods
            mock_client = MagicMock()
            mock_ws.return_value = mock_client
            mock_client.workspaces.get_status.return_value = Mock(workspace_name="test-workspace")

            client_instance = DatabricksClient(token="test-token")
            assert client_instance.host == "https://test.cloud.databricks.com"
            assert client_instance.token == "test-token"

    @patch.dict(os.environ, {"DATABRICKS_TOKEN": "env-token", "DATABRICKS_HOST": "https://test.cloud.databricks.com"})
    def test_client_uses_databricks_token_env_var(self):
        """Client should use DATABRICKS_TOKEN environment variable."""
        with patch("src.integration.databricks.client.WorkspaceClient") as mock_ws:
            mock_client = MagicMock()
            mock_ws.return_value = mock_client
            mock_client.workspaces.get_status.return_value = Mock(workspace_name="test-workspace")

            client = DatabricksClient()
            assert client.token == "env-token"

    @patch.dict(os.environ, {"DATABRICKS_HOST": "https://test.cloud.databricks.com", "databricks": "databricks-api-key", "DATABRICKS_TOKEN": ""})
    def test_client_uses_databricks_env_var(self):
        """Client should use generic 'databricks' environment variable for API key."""
        with patch("src.integration.databricks.client.WorkspaceClient") as mock_ws:
            mock_client = MagicMock()
            mock_ws.return_value = mock_client
            mock_client.workspaces.get_status.return_value = Mock(workspace_name="test-workspace")

            client_instance = DatabricksClient()
            assert client_instance.token == "databricks-api-key"

    @patch.dict(os.environ, {"DATABRICKS_HOST": "https://test.cloud.databricks.com", "DATABRICKS_TOKEN": "token-var", "databricks": "databricks-key"})
    def test_databricks_token_priority_over_generic_var(self):
        """DATABRICKS_TOKEN should take priority over generic 'databricks' env var."""
        with patch("src.integration.databricks.client.WorkspaceClient") as mock_ws:
            mock_client = MagicMock()
            mock_ws.return_value = mock_client
            mock_client.workspaces.get_status.return_value = Mock(workspace_name="test-workspace")

            client_instance = DatabricksClient()
            # DATABRICKS_TOKEN should be preferred
            assert client_instance.token == "token-var"

    @patch.dict(os.environ, {"DATABRICKS_HOST": "https://test.cloud.databricks.com", "DATABRICKS_TOKEN": "token"})
    def test_client_explicit_args_override_env_vars(self):
        """Explicit arguments should override environment variables."""
        with patch("src.integration.databricks.client.WorkspaceClient") as mock_ws:
            mock_client = MagicMock()
            mock_ws.return_value = mock_client
            mock_client.workspaces.get_status.return_value = Mock(workspace_name="test-workspace")

            client = DatabricksClient(
                host="https://override.cloud.databricks.com",
                token="override-token"
            )
            assert client.host == "https://override.cloud.databricks.com"
            assert client.token == "override-token"

    @patch.dict(os.environ, {"DATABRICKS_HOST": "https://test.cloud.databricks.com", "DATABRICKS_TOKEN": "token"})
    def test_client_profile_support(self):
        """Client should support Databricks CLI profile."""
        with patch("src.integration.databricks.client.WorkspaceClient") as mock_ws:
            mock_client = MagicMock()
            mock_ws.return_value = mock_client
            mock_client.workspaces.get_status.return_value = Mock(workspace_name="test-workspace")

            client = DatabricksClient(profile="my-profile")
            assert client.profile == "my-profile"
            # Verify WorkspaceClient was called with profile parameter
            mock_ws.assert_called_once_with(profile="my-profile")

    @patch.dict(os.environ, {"DATABRICKS_HOST": "https://test.cloud.databricks.com", "DATABRICKS_TOKEN": "token"})
    def test_client_connection_verification(self):
        """Client should verify connection on initialization."""
        with patch("src.integration.databricks.client.WorkspaceClient") as mock_ws:
            mock_client = MagicMock()
            mock_ws.return_value = mock_client
            # Updated to match current SDK API: workspace.get_status() instead of workspaces.get_status()
            mock_client.workspace.get_status.return_value = Mock(workspace_name="grid-workspace")

            client = DatabricksClient()
            mock_client.workspace.get_status.assert_called_once()

    @patch.dict(os.environ, {"DATABRICKS_HOST": "https://test.cloud.databricks.com", "DATABRICKS_TOKEN": "token"})
    def test_client_connection_failure_raises_error(self):
        """Client should raise error if connection fails."""
        with patch("src.integration.databricks.client.WorkspaceClient") as mock_ws:
            mock_client = MagicMock()
            mock_ws.return_value = mock_client
            # Updated to match current SDK API: workspace.get_status() instead of workspaces.get_status()
            mock_client.workspace.get_status.side_effect = Exception("Connection failed")

            with pytest.raises(Exception):
                DatabricksClient()


class TestDatabricksClientClusterOperations:
    """Test DatabricksClient cluster operations."""

    @patch.dict(os.environ, {"DATABRICKS_HOST": "https://test.cloud.databricks.com", "DATABRICKS_TOKEN": "token"})
    def test_list_clusters(self):
        """Test listing clusters."""
        with patch("src.integration.databricks.client.WorkspaceClient") as mock_ws:
            mock_client = MagicMock()
            mock_ws.return_value = mock_client
            mock_client.workspaces.get_status.return_value = Mock(workspace_name="test-workspace")

            # Mock cluster list
            mock_cluster1 = Mock(
                cluster_id="cluster-1",
                cluster_name="Cluster 1",
                state="RUNNING",
                num_workers=2,
                spark_version="10.4.x-scala2.12"
            )
            mock_cluster2 = Mock(
                cluster_id="cluster-2",
                cluster_name="Cluster 2",
                state="TERMINATED",
                num_workers=1,
                spark_version="10.4.x-scala2.12"
            )
            mock_client.clusters.list.return_value = [mock_cluster1, mock_cluster2]

            client = DatabricksClient()
            clusters = client.list_clusters()

            assert len(clusters) == 2
            assert clusters[0]["cluster_id"] == "cluster-1"
            assert clusters[0]["cluster_name"] == "Cluster 1"
            assert clusters[0]["state"] == "RUNNING"
            assert clusters[1]["cluster_id"] == "cluster-2"

    @patch.dict(os.environ, {"DATABRICKS_HOST": "https://test.cloud.databricks.com", "DATABRICKS_TOKEN": "token"})
    def test_get_cluster(self):
        """Test getting specific cluster."""
        with patch("src.integration.databricks.client.WorkspaceClient") as mock_ws:
            mock_client = MagicMock()
            mock_ws.return_value = mock_client
            mock_client.workspaces.get_status.return_value = Mock(workspace_name="test-workspace")

            # Mock cluster retrieval
            mock_cluster = Mock(
                cluster_id="cluster-1",
                cluster_name="Test Cluster",
                state="RUNNING",
                num_workers=2,
                spark_version="10.4.x-scala2.12",
                node_type_id="i3.xlarge",
                driver_node_type_id="i3.xlarge"
            )
            mock_client.clusters.get.return_value = mock_cluster

            client = DatabricksClient()
            cluster = client.get_cluster("cluster-1")

            assert cluster is not None
            assert cluster["cluster_id"] == "cluster-1"
            assert cluster["cluster_name"] == "Test Cluster"
            assert cluster["state"] == "RUNNING"
            assert cluster["num_workers"] == 2

    @patch.dict(os.environ, {"DATABRICKS_HOST": "https://test.cloud.databricks.com", "DATABRICKS_TOKEN": "token"})
    def test_get_cluster_not_found(self):
        """Test getting non-existent cluster returns None."""
        with patch("src.integration.databricks.client.WorkspaceClient") as mock_ws:
            mock_client = MagicMock()
            mock_ws.return_value = mock_client
            mock_client.workspaces.get_status.return_value = Mock(workspace_name="test-workspace")
            mock_client.clusters.get.side_effect = Exception("Cluster not found")

            client = DatabricksClient()
            cluster = client.get_cluster("non-existent")

            assert cluster is None


class TestDatabricksJobsManager:
    """Test DatabricksJobsManager."""

    @patch.dict(os.environ, {"DATABRICKS_HOST": "https://test.cloud.databricks.com", "DATABRICKS_TOKEN": "token"})
    def test_create_notebook_job(self):
        """Test creating a notebook job."""
        with patch("src.integration.databricks.client.WorkspaceClient") as mock_ws:
            mock_client = MagicMock()
            mock_ws.return_value = mock_client
            mock_client.workspaces.get_status.return_value = Mock(workspace_name="test-workspace")

            # Mock job creation
            mock_job_response = Mock(job_id="123")
            mock_client.jobs.create.return_value = mock_job_response

            client = DatabricksClient()
            jobs_manager = DatabricksJobsManager(client)

            job_id = jobs_manager.create_notebook_job(
                job_name="test-job",
                notebook_path="/Repos/user/repo/notebook.ipynb",
                cluster_id="cluster-1",
                base_parameters={"param1": "value1"}
            )

            assert job_id == "123"
            mock_client.jobs.create.assert_called_once()

    @patch.dict(os.environ, {"DATABRICKS_HOST": "https://test.cloud.databricks.com", "DATABRICKS_TOKEN": "token"})
    def test_run_job(self):
        """Test running a job."""
        with patch("src.integration.databricks.client.WorkspaceClient") as mock_ws:
            mock_client = MagicMock()
            mock_ws.return_value = mock_client
            mock_client.workspaces.get_status.return_value = Mock(workspace_name="test-workspace")

            # Mock job run
            mock_run_response = Mock(run_id=456)
            mock_client.jobs.run_now.return_value = mock_run_response

            client = DatabricksClient()
            jobs_manager = DatabricksJobsManager(client)

            run_id = jobs_manager.run_job("123", notebook_params={"param1": "value1"})

            assert run_id == 456
            mock_client.jobs.run_now.assert_called_once()

    @patch.dict(os.environ, {"DATABRICKS_HOST": "https://test.cloud.databricks.com", "DATABRICKS_TOKEN": "token"})
    def test_get_run_status(self):
        """Test getting job run status."""
        with patch("src.integration.databricks.client.WorkspaceClient") as mock_ws:
            mock_client = MagicMock()
            mock_ws.return_value = mock_client
            mock_client.workspaces.get_status.return_value = Mock(workspace_name="test-workspace")

            # Mock run status with proper structure
            mock_state = Mock(result_state="SUCCESS")
            mock_run = Mock(
                run_id=456,
                job_id="123",
                life_cycle_state="RUNNING",
                state=mock_state,
                start_time=1000,
                end_time=2000,
                setup_duration=100,
                execution_duration=800,
                cleanup_duration=100
            )
            mock_client.jobs.get_run.return_value = mock_run

            client = DatabricksClient()
            jobs_manager = DatabricksJobsManager(client)

            status = jobs_manager.get_run_status(456)

            assert status["run_id"] == 456
            assert status["job_id"] == "123"
            assert status["state"] == "RUNNING"
            assert status["result_state"] == "SUCCESS"


class TestDatabricksClustersManager:
    """Test DatabricksClustersManager."""

    @patch.dict(os.environ, {"DATABRICKS_HOST": "https://test.cloud.databricks.com", "DATABRICKS_TOKEN": "token"})
    def test_start_cluster(self):
        """Test starting a cluster."""
        with patch("src.integration.databricks.client.WorkspaceClient") as mock_ws:
            mock_client = MagicMock()
            mock_ws.return_value = mock_client
            mock_client.workspaces.get_status.return_value = Mock(workspace_name="test-workspace")

            client = DatabricksClient()
            clusters_manager = DatabricksClustersManager(client)

            clusters_manager.start_cluster("cluster-1")
            mock_client.clusters.start.assert_called_once_with(cluster_id="cluster-1")

    @patch.dict(os.environ, {"DATABRICKS_HOST": "https://test.cloud.databricks.com", "DATABRICKS_TOKEN": "token"})
    def test_stop_cluster(self):
        """Test stopping a cluster."""
        with patch("src.integration.databricks.client.WorkspaceClient") as mock_ws:
            mock_client = MagicMock()
            mock_ws.return_value = mock_client
            mock_client.workspaces.get_status.return_value = Mock(workspace_name="test-workspace")

            client = DatabricksClient()
            clusters_manager = DatabricksClustersManager(client)

            clusters_manager.stop_cluster("cluster-1")
            mock_client.clusters.stop.assert_called_once_with(cluster_id="cluster-1")


class TestDatabricksNotebooksManager:
    """Test DatabricksNotebooksManager."""

    @patch.dict(os.environ, {"DATABRICKS_HOST": "https://test.cloud.databricks.com", "DATABRICKS_TOKEN": "token"})
    def test_read_notebook(self):
        """Test reading a notebook."""
        with patch("src.integration.databricks.client.WorkspaceClient") as mock_ws:
            mock_workspace_client = MagicMock()
            mock_ws.return_value = mock_workspace_client
            mock_workspace_client.workspaces.get_status.return_value = Mock(workspace_name="test-workspace")

            # Mock notebook read
            mock_notebook = Mock(content="# Sample notebook\nprint('hello')")
            mock_workspace_client.read.return_value = mock_notebook

            client = DatabricksClient()

            notebooks_manager = DatabricksNotebooksManager(client)

            content = notebooks_manager.read_notebook("/Repos/user/repo/notebook.ipynb")

            assert content == "# Sample notebook\nprint('hello')"

    @patch.dict(os.environ, {"DATABRICKS_HOST": "https://test.cloud.databricks.com", "DATABRICKS_TOKEN": "token"})
    def test_write_notebook(self):
        """Test writing a notebook."""
        with patch("src.integration.databricks.client.WorkspaceClient") as mock_ws:
            mock_workspace_client = MagicMock()
            mock_ws.return_value = mock_workspace_client
            mock_workspace_client.workspaces.get_status.return_value = Mock(workspace_name="test-workspace")

            client = DatabricksClient()
            notebooks_manager = DatabricksNotebooksManager(client)

            notebooks_manager.write_notebook(
                "/Repos/user/repo/notebook.ipynb",
                "# Updated notebook"
            )

            mock_workspace_client.write.assert_called_once()
            # Verify the call was made with correct parameters
            call_args = mock_workspace_client.write.call_args
            assert call_args[1]["path"] == "/Repos/user/repo/notebook.ipynb"
            assert call_args[1]["content"] == "# Updated notebook"

    @patch.dict(os.environ, {"DATABRICKS_HOST": "https://test.cloud.databricks.com", "DATABRICKS_TOKEN": "token"})
    def test_list_directory(self):
        """Test listing directory contents."""
        with patch("src.integration.databricks.client.WorkspaceClient") as mock_ws:
            mock_workspace_client = MagicMock()
            mock_ws.return_value = mock_workspace_client
            mock_workspace_client.workspaces.get_status.return_value = Mock(workspace_name="test-workspace")

            # Mock directory listing
            mock_obj1 = Mock(path="/Repos/user/repo", object_type="DIRECTORY")
            mock_obj2 = Mock(path="/Repos/user/repo/notebook.ipynb", object_type="NOTEBOOK")
            mock_workspace_client.list.return_value = [mock_obj1, mock_obj2]

            client = DatabricksClient()
            notebooks_manager = DatabricksNotebooksManager(client)

            objects = notebooks_manager.list_directory("/Repos/user/repo")

            assert len(objects) == 2
            assert objects[0]["path"] == "/Repos/user/repo"
            assert objects[0]["object_type"] == "DIRECTORY"
            assert objects[1]["path"] == "/Repos/user/repo/notebook.ipynb"


class TestIntegrationArchitecturePlacement:
    """Test that Databricks integration fits properly in GRID architecture."""

    @patch.dict(os.environ, {"DATABRICKS_HOST": "https://test.cloud.databricks.com", "DATABRICKS_TOKEN": "token"})
    def test_client_is_stateless(self):
        """Client should be stateless (matches GRID architecture pattern)."""
        with patch("src.integration.databricks.client.WorkspaceClient") as mock_ws:
            mock_client = MagicMock()
            mock_ws.return_value = mock_client
            mock_client.workspaces.get_status.return_value = Mock(workspace_name="test-workspace")

            client = DatabricksClient()
            # Create multiple clients - should not affect each other
            client2 = DatabricksClient()

            assert client.host == client2.host
            assert client.token == client2.token

    def test_managers_depend_on_client(self):
        """Managers should depend on DatabricksClient (dependency injection)."""
        mock_client = Mock()

        jobs_manager = DatabricksJobsManager(mock_client)
        clusters_manager = DatabricksClustersManager(mock_client)
        notebooks_manager = DatabricksNotebooksManager(mock_client)

        assert jobs_manager.client is mock_client
        assert clusters_manager.client is mock_client
        assert notebooks_manager.client is mock_client

    @patch.dict(os.environ, {"DATABRICKS_HOST": "https://test.cloud.databricks.com", "DATABRICKS_TOKEN": "token"})
    def test_client_provides_workspace_client_property(self):
        """Client should expose WorkspaceClient via property."""
        with patch("src.integration.databricks.client.WorkspaceClient") as mock_ws:
            mock_client = MagicMock()
            mock_ws.return_value = mock_client
            mock_client.workspaces.get_status.return_value = Mock(workspace_name="test-workspace")

            client = DatabricksClient()
            assert client.workspace is mock_client


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
