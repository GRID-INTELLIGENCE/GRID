"""Tests for DatabricksVectorStore retry logic, connection pooling, and operations.

Phase 3 Sprint 2: RAG integration tests (10 tests for Databricks store)
Mocks Databricks SQL backend to avoid external dependencies.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tools.rag.vector_store.databricks_store import DatabricksVectorStore

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
def mock_engine(mock_databricks_env):
    """Mock SQLAlchemy engine and connections."""
    with patch("tools.rag.vector_store.databricks_store.create_engine") as mock_create_engine:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=None)
        mock_conn.execute = MagicMock()
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=None)
        mock_create_engine.return_value = mock_engine
        yield mock_engine, mock_conn, mock_cursor


# ============================================================================
# Test Group 1: Initialization and Connection (2 tests)
# ============================================================================


def test_databricks_initialization_success(mock_engine):
    """Test successful DatabricksVectorStore initialization."""
    engine, conn, cursor = mock_engine

    with patch.object(DatabricksVectorStore, "_verify_connection"):
        with patch.object(DatabricksVectorStore, "_ensure_tables_exist"):
            store = DatabricksVectorStore(chunk_table="chunks", document_table="documents")

            assert store.chunk_table == "chunks"
            assert store.document_table == "documents"
            assert store._is_healthy


def test_databricks_missing_env_vars():
    """Test initialization fails with missing environment variables."""
    with patch.dict(
        "os.environ", {"DATABRICKS_HOST": "", "DATABRICKS_HTTP_PATH": "", "DATABRICKS_TOKEN": ""}, clear=True
    ):
        with pytest.raises(ValueError, match="DATABRICKS_HOST"):
            DatabricksVectorStore()


# ============================================================================
# Test Group 2: Connection Health Checks (2 tests)
# ============================================================================


def test_databricks_health_check_success(mock_engine):
    """Test successful health check."""
    engine, conn, cursor = mock_engine

    with patch.object(DatabricksVectorStore, "_verify_connection"):
        with patch.object(DatabricksVectorStore, "_ensure_tables_exist"):
            store = DatabricksVectorStore()

            # First check should return True
            is_healthy = store._check_health()
            assert is_healthy


def test_databricks_health_check_failure_recovery(mock_engine):
    """Test health check failure and recovery."""
    engine, conn, cursor = mock_engine

    with patch.object(DatabricksVectorStore, "_verify_connection") as mock_verify:
        with patch.object(DatabricksVectorStore, "_ensure_tables_exist"):
            store = DatabricksVectorStore()

            # Simulate connection failure on next check
            mock_verify.side_effect = RuntimeError("Connection failed")
            is_healthy = store._check_health()
            assert not is_healthy

            # Simulate recovery
            mock_verify.side_effect = None
            is_healthy = store._check_health()
            assert is_healthy


# ============================================================================
# Test Group 3: Document Addition and Retry Logic (3 tests)
# ============================================================================


def test_databricks_add_documents(mock_engine):
    """Test adding documents with embeddings."""
    engine, conn, cursor = mock_engine

    with patch.object(DatabricksVectorStore, "_verify_connection"):
        with patch.object(DatabricksVectorStore, "_ensure_tables_exist"):
            with patch.object(DatabricksVectorStore, "_update_document_metadata"):
                store = DatabricksVectorStore()

                ids = ["doc1", "doc2"]
                documents = ["Content 1", "Content 2"]
                embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
                metadatas = [{"path": "file1.txt"}, {"path": "file2.txt"}]

                # Should not raise
                store.add(ids, documents, embeddings, metadatas)

                # Verify cursor execute was called
                cursor.execute.assert_called()


def test_databricks_add_mismatched_lengths(mock_engine):
    """Test add() with mismatched input lengths."""
    engine, conn, cursor = mock_engine

    with patch.object(DatabricksVectorStore, "_verify_connection"):
        with patch.object(DatabricksVectorStore, "_ensure_tables_exist"):
            store = DatabricksVectorStore()

            ids = ["doc1", "doc2"]
            documents = ["Content 1"]  # Mismatched length
            embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]

            with pytest.raises(ValueError, match="same length"):
                store.add(ids, documents, embeddings)


def test_databricks_retry_on_connection_failure(mock_engine):
    """Test retry logic on transient connection failure."""
    engine, conn, cursor = mock_engine

    with patch.object(DatabricksVectorStore, "_verify_connection"):
        with patch.object(DatabricksVectorStore, "_ensure_tables_exist"):
            with patch.object(DatabricksVectorStore, "_update_document_metadata"):
                store = DatabricksVectorStore()

                # Simulate transient failure then success
                call_count = 0

                def side_effect(*args, **kwargs):
                    nonlocal call_count
                    call_count += 1
                    if call_count == 1:
                        from sqlalchemy.exc import OperationalError

                        raise OperationalError("Connection timeout", None, Exception("test"))
                    return None

                cursor.execute.side_effect = side_effect

                ids = ["doc1"]
                documents = ["Content 1"]
                embeddings = [[0.1, 0.2, 0.3]]

                # Retry decorator should retry and eventually succeed
                store.add(ids, documents, embeddings)
                assert call_count >= 1


# ============================================================================
# Test Group 4: Query and Similarity Search (2 tests)
# ============================================================================


def test_databricks_query_with_results(mock_engine):
    """Test querying with returned results."""
    engine, conn, cursor = mock_engine

    with patch.object(DatabricksVectorStore, "_verify_connection"):
        with patch.object(DatabricksVectorStore, "_ensure_tables_exist"):
            store = DatabricksVectorStore()

            # Mock query results
            mock_results = MagicMock()
            mock_results.fetchall.return_value = [
                ("doc1", "doc1", 0, "Similar content", "file.txt", "{}", 0.1),
                ("doc2", "doc2", 0, "Another match", "file.txt", "{}", 0.2),
            ]

            # Set up proper context manager mocking
            conn.execute = MagicMock(return_value=mock_results)
            mock_conn_context = MagicMock()
            mock_conn_context.__enter__ = MagicMock(return_value=conn)
            mock_conn_context.__exit__ = MagicMock(return_value=None)
            engine.connect = MagicMock(return_value=mock_conn_context)

            result = store.query([0.1, 0.2, 0.3], n_results=5)

            assert len(result["ids"]) == 2
            assert result["ids"][0] == "doc1"
            assert result["distances"][0] == pytest.approx(0.1, abs=0.01)


def test_databricks_query_with_metadata_filter(mock_engine):
    """Test querying with metadata filter."""
    engine, conn, cursor = mock_engine

    with patch.object(DatabricksVectorStore, "_verify_connection"):
        with patch.object(DatabricksVectorStore, "_ensure_tables_exist"):
            store = DatabricksVectorStore()

            mock_results = MagicMock()
            mock_results.fetchall.return_value = []

            # Set up proper context manager mocking
            conn.execute = MagicMock(return_value=mock_results)
            mock_conn_context = MagicMock()
            mock_conn_context.__enter__ = MagicMock(return_value=conn)
            mock_conn_context.__exit__ = MagicMock(return_value=None)
            engine.connect = MagicMock(return_value=mock_conn_context)

            result = store.query([0.1, 0.2, 0.3], n_results=5, where={"path": "specific.txt"})

            # Should return empty or filtered results
            assert isinstance(result, dict)
            assert "ids" in result


# ============================================================================
# Test Group 5: Deletion and Cleanup (1 test)
# ============================================================================


def test_databricks_delete_documents(mock_engine):
    """Test deleting documents by IDs."""
    engine, conn, cursor = mock_engine

    with patch.object(DatabricksVectorStore, "_verify_connection"):
        with patch.object(DatabricksVectorStore, "_ensure_tables_exist"):
            store = DatabricksVectorStore()

            ids_to_delete = ["doc1", "doc2"]
            store.delete(ids=ids_to_delete)

            # Verify cursor execute was called for deletion
            cursor.execute.assert_called()
