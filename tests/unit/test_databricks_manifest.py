"""Tests for DatabricksManifestTracker SQL injection prevention.

Validates that all SQL operations use parameterized queries and
that identifier injection is blocked.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tools.rag.databricks_manifest import DatabricksFileState, DatabricksManifestTracker

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_databricks_env():
    """Mock Databricks environment variables."""
    with patch.dict(
        "os.environ",
        {
            "DATABRICKS_HOST": "test.databricks.com",
            "DATABRICKS_HTTP_PATH": "/sql/1.0/warehouses/test",
            "DATABRICKS_TOKEN": "test_token",
        },
    ):
        yield


@pytest.fixture
def mock_connection(mock_databricks_env):
    """Mock Databricks SQL connection."""
    with patch("tools.rag.databricks_manifest.DatabricksManifestTracker._connect") as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=None)
        mock_connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_connect.return_value.__exit__ = MagicMock(return_value=None)
        yield mock_connect, mock_conn, mock_cursor


# ============================================================================
# Test Group 1: Identifier Validation (SQL Injection Prevention)
# ============================================================================


def test_sql_injection_via_table_name(mock_databricks_env):
    """Test that SQL injection via table name is prevented."""
    with patch.object(DatabricksManifestTracker, "_ensure_table"):
        with pytest.raises(ValueError, match="Invalid table"):
            DatabricksManifestTracker(repo="test-repo", table="manifest; DROP TABLE users; --")


def test_sql_injection_via_schema_name(mock_databricks_env):
    """Test that SQL injection via schema name is prevented."""
    with patch.object(DatabricksManifestTracker, "_ensure_table"):
        with pytest.raises(ValueError, match="Invalid schema"):
            DatabricksManifestTracker(repo="test-repo", schema="default'; DROP TABLE manifest; --")


def test_valid_identifier_accepted(mock_databricks_env):
    """Test that valid identifiers are accepted."""
    with patch.object(DatabricksManifestTracker, "_ensure_table"):
        # Should not raise
        tracker = DatabricksManifestTracker(repo="test-repo", schema="my_schema", table="rag_manifest_v2")
        assert tracker.table == "my_schema.rag_manifest_v2"


# ============================================================================
# Test Group 2: Parameterized Query Operations
# ============================================================================


def test_fetch_all_uses_parameters(mock_connection):
    """Test that fetch_all uses parameterized queries."""
    mock_connect, mock_conn, mock_cursor = mock_connection

    with patch.object(DatabricksManifestTracker, "_ensure_table"):
        tracker = DatabricksManifestTracker(repo="test-repo")

        # Mock fetch results
        mock_cursor.fetchall.return_value = [("test-repo", "/path/file.py", "abc123", 1024, 12345, 5)]

        tracker.fetch_all()

        # Verify parameterized call
        mock_cursor.execute.assert_called()
        call_args = mock_cursor.execute.call_args
        assert ":repo" in call_args[0][0]  # SQL contains parameter placeholder
        assert call_args[0][1] == {"repo": "test-repo"}  # Parameters passed separately


def test_delete_paths_uses_parameters(mock_connection):
    """Test that delete_paths uses parameterized queries."""
    mock_connect, mock_conn, mock_cursor = mock_connection

    with patch.object(DatabricksManifestTracker, "_ensure_table"):
        tracker = DatabricksManifestTracker(repo="test-repo")

        # Delete with SQL injection attempt in path
        paths_to_delete = [
            "/normal/path.py",
            "'; DROP TABLE manifest; --",
        ]

        tracker.delete_paths(paths_to_delete)

        # Verify parameterized call
        mock_cursor.execute.assert_called()
        call_args = mock_cursor.execute.call_args
        sql = call_args[0][0]
        params = call_args[0][1]

        # SQL should contain parameter placeholders, not raw values
        assert ":repo" in sql
        assert ":path_0" in sql
        assert ":path_1" in sql
        # Injection attempt should be in params, not SQL
        assert "'; DROP TABLE manifest; --" in params.values()
        assert "DROP TABLE" not in sql


def test_upsert_states_uses_parameters(mock_connection):
    """Test that upsert_states uses parameterized queries."""
    mock_connect, mock_conn, mock_cursor = mock_connection

    with patch.object(DatabricksManifestTracker, "_ensure_table"):
        tracker = DatabricksManifestTracker(repo="test-repo")

        states = [
            DatabricksFileState(
                repo="test-repo",
                path="/path/to/file.py",
                file_hash="abc123",
                file_size=1024,
                mtime_ms=12345,
                chunk_count=5,
            ),
            DatabricksFileState(
                repo="test-repo",
                path="'; DROP TABLE manifest; --.py",  # Injection attempt
                file_hash="def456",
                file_size=2048,
                mtime_ms=67890,
                chunk_count=10,
            ),
        ]

        tracker.upsert_states(states)

        # Verify parameterized call
        mock_cursor.execute.assert_called()
        call_args = mock_cursor.execute.call_args
        sql = call_args[0][0]
        call_args[0][1]

        # SQL should use parameter placeholders
        assert ":repo_0" in sql
        assert ":path_0" in sql
        assert ":repo_1" in sql
        assert ":path_1" in sql

        # Injection attempt should be safely in params
        assert "DROP TABLE" not in sql


# ============================================================================
# Test Group 3: Edge Cases
# ============================================================================


def test_empty_delete_paths(mock_connection):
    """Test delete_paths with empty list returns 0."""
    mock_connect, mock_conn, mock_cursor = mock_connection

    with patch.object(DatabricksManifestTracker, "_ensure_table"):
        tracker = DatabricksManifestTracker(repo="test-repo")

        deleted = tracker.delete_paths([])

        assert deleted == 0
        mock_cursor.execute.assert_not_called()


def test_empty_upsert_states(mock_connection):
    """Test upsert_states with empty list returns 0."""
    mock_connect, mock_conn, mock_cursor = mock_connection

    with patch.object(DatabricksManifestTracker, "_ensure_table"):
        tracker = DatabricksManifestTracker(repo="test-repo")

        upserted = tracker.upsert_states([])

        assert upserted == 0
        mock_cursor.execute.assert_not_called()
