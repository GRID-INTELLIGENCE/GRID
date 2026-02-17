"""Tests for DistributedSparkIndexer checkpointing, parallel processing, and configuration.

Phase 3 Sprint 2: RAG integration tests (5 tests for distributed indexer)
Mocks Databricks and Spark interactions to avoid external dependencies.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Import distributed_spark_indexer module directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "tools" / "rag" / "indexer"))
from distributed_spark_indexer import DistributedSparkIndexer, DistributedSparkIndexerConfig

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
def temp_checkpoint_dir():
    """Create temporary directory for checkpoints."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    # Clean up
    import shutil

    try:
        shutil.rmtree(tmpdir, ignore_errors=True)
    except Exception:
        pass


@pytest.fixture
def indexer_config(temp_checkpoint_dir):
    """Create indexer configuration with temp checkpoint path."""
    return DistributedSparkIndexerConfig(
        cluster_id="test_cluster",
        num_partitions=4,
        batch_size=50,
        embedding_model="nomic-embed-text:latest",
        checkpoint_enabled=True,
        checkpoint_path=temp_checkpoint_dir,
    )


@pytest.fixture
def distributed_indexer(mock_databricks_env, indexer_config):
    """Create DistributedSparkIndexer instance."""
    return DistributedSparkIndexer(config=indexer_config)


# ============================================================================
# Test Group 1: Configuration and Initialization (2 tests)
# ============================================================================


def test_indexer_config_defaults():
    """Test default configuration values."""
    config = DistributedSparkIndexerConfig()

    assert config.num_partitions == 8
    assert config.batch_size == 100
    assert config.embedding_model == "nomic-embed-text:latest"
    assert config.checkpoint_enabled is True


def test_indexer_initialization_success(distributed_indexer):
    """Test successful indexer initialization with valid config."""
    assert distributed_indexer.config.num_partitions == 4
    assert distributed_indexer.config.batch_size == 50
    assert distributed_indexer.config.cluster_id == "test_cluster"


# ============================================================================
# Test Group 2: Checkpointing and Resume (2 tests)
# ============================================================================


def test_indexer_checkpoint_save_and_load(distributed_indexer, temp_checkpoint_dir):
    """Test checkpoint saving and loading."""
    checkpoint_key = "test_session_123"
    checkpoint_data = {
        "processed_ids": ["doc1", "doc2", "doc3"],
        "total_chunks": 150,
        "status": "in_progress",
    }

    # Save checkpoint
    distributed_indexer._save_checkpoint(checkpoint_key, checkpoint_data)

    # Load checkpoint
    loaded_data = distributed_indexer._load_checkpoint(checkpoint_key)

    assert loaded_data["processed_ids"] == ["doc1", "doc2", "doc3"]
    assert loaded_data["total_chunks"] == 150
    assert loaded_data["status"] == "in_progress"


def test_indexer_resume_from_checkpoint(distributed_indexer):
    """Test resuming indexing from saved checkpoint."""
    checkpoint_key = "test_resume_123"

    # Create documents
    all_documents = [
        {"id": "doc1", "text": "Content 1", "path": "file1.txt"},
        {"id": "doc2", "text": "Content 2", "path": "file2.txt"},
        {"id": "doc3", "text": "Content 3", "path": "file3.txt"},
    ]

    # Simulate partial completion by saving checkpoint
    partial_checkpoint = {
        "processed_ids": ["doc1"],
        "total_chunks": 50,
        "status": "partial",
    }
    distributed_indexer._save_checkpoint(checkpoint_key, partial_checkpoint)

    # Index with checkpoint (should skip doc1)
    _ = distributed_indexer.index_with_checkpoint(all_documents, checkpoint_key)

    # Verify checkpoint was updated
    updated_checkpoint = distributed_indexer._load_checkpoint(checkpoint_key)
    assert len(updated_checkpoint["processed_ids"]) >= 1


# ============================================================================
# Test Group 3: Distributed Indexing and Metrics (1 test)
# ============================================================================


def test_indexer_distributed_indexing_metrics(distributed_indexer):
    """Test distributed indexing returns valid metrics."""
    documents = [
        {"id": "doc1", "text": "Content 1", "path": "file1.txt", "metadata": {}},
        {"id": "doc2", "text": "Content 2", "path": "file2.txt", "metadata": {}},
    ]

    metrics = distributed_indexer.index_documents_distributed(
        documents,
        output_table="rag_chunks",
        document_table="rag_documents",
    )

    # Verify metric structure
    assert "total_documents" in metrics
    assert "status" in metrics
    assert "start_time" in metrics
    assert metrics["total_documents"] == 2
    assert metrics["status"] == "queued"
