"""Distributed document indexing via Databricks Spark jobs.

This module enables parallel document processing and embedding generation
across Databricks clusters for large-scale RAG corpus indexing.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


class DistributedSparkIndexerConfig:
    """Configuration for distributed Spark indexer."""

    def __init__(
        self,
        cluster_id: str | None = None,
        num_partitions: int = 8,
        batch_size: int = 100,
        embedding_model: str = "nomic-embed-text:latest",
        checkpoint_enabled: bool = True,
        checkpoint_path: str = ".databricks_indexing_checkpoint",
    ):
        """Initialize config.

        Args:
            cluster_id: Databricks cluster ID (if None, uses on-demand)
            num_partitions: Number of Spark partitions for parallelism
            batch_size: Documents per batch
            embedding_model: Ollama embedding model to use
            checkpoint_enabled: Enable checkpointing for resume-ability
            checkpoint_path: Path to store checkpoints
        """
        self.cluster_id = cluster_id
        self.num_partitions = num_partitions
        self.batch_size = batch_size
        self.embedding_model = embedding_model
        self.checkpoint_enabled = checkpoint_enabled
        self.checkpoint_path = checkpoint_path


class DistributedSparkIndexer:
    """Distributed document indexer using Databricks Spark.

    Enables:
    - Parallel document chunking across cluster
    - Distributed embedding generation
    - Checkpointing for large corpus indexing
    - Progress tracking and monitoring
    """

    def __init__(self, config: DistributedSparkIndexerConfig | None = None):
        """Initialize distributed indexer.

        Args:
            config: Indexer configuration
        """
        self.config = config or DistributedSparkIndexerConfig()

        # Verify Databricks connectivity
        self._verify_databricks_setup()

        logger.info(
            f"Initialized DistributedSparkIndexer: "
            f"partitions={self.config.num_partitions}, "
            f"batch_size={self.config.batch_size}"
        )

    def _verify_databricks_setup(self) -> None:
        """Verify Databricks is available and configured.

        Raises:
            RuntimeError: If Databricks is not properly configured
        """
        host = os.getenv("DATABRICKS_HOST") or os.getenv("DATABRICKS_SERVER_HOSTNAME")
        token = os.getenv("DATABRICKS_TOKEN") or os.getenv("DATABRICKS_ACCESS_TOKEN") or os.getenv("local_databricks")
        http_path = os.getenv("DATABRICKS_HTTP_PATH")

        if not all([host, token, http_path]):
            raise RuntimeError(
                "Databricks configuration incomplete. "
                "Required: DATABRICKS_HOST, DATABRICKS_TOKEN, DATABRICKS_HTTP_PATH"
            )

    def index_documents_distributed(
        self,
        documents: list[dict[str, Any]],
        output_table: str = "rag_chunks",
        document_table: str = "rag_documents",
    ) -> dict[str, Any]:
        """Index documents using distributed Spark processing.

        Args:
            documents: List of document dicts with 'id', 'text', 'path', 'metadata'
            output_table: Table to store embeddings
            document_table: Table to store document metadata

        Returns:
            Dictionary with indexing metrics:
            {
                'total_documents': int,
                'indexed_chunks': int,
                'failed': int,
                'duration_seconds': float,
                'avg_latency_ms': float
            }
        """
        start_time = datetime.now(UTC)
        logger.info(f"Starting distributed indexing of {len(documents)} documents")

        # Step 1: Submit Spark job to process documents
        # (Implementation would use databricks_jobs_manager to create/run job)
        metrics = {
            "total_documents": len(documents),
            "indexed_chunks": 0,
            "failed": 0,
            "start_time": start_time.isoformat(),
            "status": "queued",
            "job_id": None,
        }

        logger.info(f"Distributed indexing submitted. " f"Monitors status at: {metrics['status']}")

        return metrics

    def get_indexing_status(self, job_id: str) -> dict[str, Any]:
        """Get status of an ongoing indexing job.

        Args:
            job_id: Databricks job ID

        Returns:
            Status dictionary with progress information
        """
        # Implementation would query Databricks job API
        # For now, placeholder
        return {"job_id": job_id, "state": "pending", "progress": 0.0}

    def index_with_checkpoint(
        self,
        documents: list[dict[str, Any]],
        checkpoint_key: str | None = None,
    ) -> dict[str, Any]:
        """Index documents with checkpointing for resume-ability.

        Useful for large corpus indexing that might be interrupted.

        Args:
            documents: Documents to index
            checkpoint_key: Optional key for this indexing session

        Returns:
            Indexing metrics
        """
        if checkpoint_key is None:
            checkpoint_key = datetime.now(UTC).isoformat()

        logger.info(f"Starting checkpointed indexing: {checkpoint_key}")

        # Load previous checkpoint if exists
        checkpoint_data = self._load_checkpoint(checkpoint_key)
        processed_ids = set(checkpoint_data.get("processed_ids", []))

        # Filter to only unprocessed documents
        remaining_docs = [d for d in documents if d.get("id") not in processed_ids]

        if not remaining_docs:
            logger.info(f"Checkpoint {checkpoint_key} already complete")
            return checkpoint_data

        # Process remaining documents
        metrics = self.index_documents_distributed(remaining_docs)
        metrics["checkpoint_key"] = checkpoint_key
        metrics["processed_ids"] = list(processed_ids) + [d.get("id") for d in remaining_docs]

        # Save checkpoint
        self._save_checkpoint(checkpoint_key, metrics)

        return metrics

    def _load_checkpoint(self, key: str) -> dict[str, Any]:
        """Load indexing checkpoint data.

        Args:
            key: Checkpoint key

        Returns:
            Checkpoint data or empty dict if not found
        """
        if not self.config.checkpoint_enabled:
            return {}

        checkpoint_file = f"{self.config.checkpoint_path}/{key}.json"

        try:
            if os.path.exists(checkpoint_file):
                with open(checkpoint_file) as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load checkpoint {key}: {e}")

        return {}

    def _save_checkpoint(self, key: str, data: dict[str, Any]) -> None:
        """Save indexing checkpoint data.

        Args:
            key: Checkpoint key
            data: Data to save
        """
        if not self.config.checkpoint_enabled:
            return

        os.makedirs(self.config.checkpoint_path, exist_ok=True)
        checkpoint_file = f"{self.config.checkpoint_path}/{key}.json"

        try:
            with open(checkpoint_file, "w") as f:
                json.dump(data, f, indent=2, default=str)
            logger.debug(f"Saved checkpoint: {checkpoint_file}")
        except Exception as e:
            logger.error(f"Failed to save checkpoint {key}: {e}")

    @staticmethod
    def create_spark_job_notebook(
        documents_path: str,
        output_table: str,
        embedding_model: str = "nomic-embed-text:latest",
    ) -> str:
        """Generate Databricks notebook code for distributed indexing.

        Args:
            documents_path: DBFS path to documents (JSON lines)
            output_table: Target table for embeddings
            embedding_model: Ollama embedding model

        Returns:
            Python notebook code
        """
        notebook_code = f'''
# Databricks Distributed Document Indexer
# Auto-generated notebook for parallel embedding generation

import json
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf, struct
import requests

spark = SparkSession.builder.appName("grid-rag-indexer").getOrCreate()

# Load documents
df = spark.read.option("multiline", "true").json("{documents_path}")

# Define embedding UDF
@udf("array<float>")
def embed_text(text):
    """Generate embedding for text using local Ollama."""
    try:
        response = requests.post(
            "http://localhost:11434/api/embeddings",
            json={{"model": "{embedding_model}", "prompt": text}}
        )
        if response.status_code == 200:
            return response.json()["embedding"]
        return None
    except Exception as e:
        print(f"Embedding failed: {{e}}")
        return None

# Generate embeddings in parallel
df_with_embeddings = df.withColumn(
    "embedding",
    embed_text(col("text"))
)

# Write to Delta table
df_with_embeddings.write.mode("append").saveAsTable("{output_table}")

print(f"Indexed {{df_with_embeddings.count()}} documents")
'''
        return notebook_code.strip()
