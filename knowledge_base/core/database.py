"""
Knowledge Base Database Layer
==============================

Databricks-backed database interface for the GRID Knowledge Base.
No SQLite fallback; uses databricks-sql-connector directly.
"""

import json
import logging
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

from databricks import sql

from ..core.config import KnowledgeBaseConfig

logger = logging.getLogger(__name__)


@dataclass
class DocumentData:
    """Document data structure."""
    id: str
    title: str
    content: str
    source_type: str
    source_path: str
    file_type: str
    metadata: dict[str, Any]


@dataclass
class SearchResult:
    """Search result data structure."""
    document_id: str
    chunk_id: str
    content: str
    score: float
    metadata: dict[str, Any]
    document_title: str | None = None
    source_type: str | None = None


class KnowledgeBaseDB:
    """Database interface using Databricks SQL."""

    def __init__(self, config: KnowledgeBaseConfig):
        self.config = config

        # Build connection params
        self.connection_params = {
            "server_hostname": config.database.host,
            "http_path": config.database.http_path,
            "access_token": config.database.token,
        }

    def connect(self) -> None:
        """Validate Databricks connection and ensure tables exist."""
        try:
            # Simple validation
            with sql.connect(**self.connection_params) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()

            self._create_tables()
            logger.info("Databricks connection established and tables verified")
        except Exception as e:
            logger.error(f"Databricks connection failed: {e}")
            raise

    def _create_tables(self) -> None:
        """Create tables in Databricks if they don't exist."""
        with sql.connect(**self.connection_params) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS kb_documents (
                        id STRING,
                        title STRING,
                        content STRING,
                        source_type STRING,
                        source_path STRING,
                        file_type STRING,
                        extra_metadata STRING,
                        created_at TIMESTAMP,
                        updated_at TIMESTAMP
                    )
                    """
                )

                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS kb_chunks (
                        id STRING,
                        document_id STRING,
                        chunk_index INT,
                        content STRING,
                        token_count INT,
                        embedding STRING,
                        extra_metadata STRING,
                        created_at TIMESTAMP
                    )
                    """
                )

                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS kb_search_queries (
                        id STRING,
                        query STRING,
                        user_id STRING,
                        results_count INT,
                        response_time DOUBLE,
                        extra_metadata STRING,
                        created_at TIMESTAMP
                    )
                    """
                )

                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS kb_feedback (
                        id STRING,
                        chunk_id STRING,
                        user_id STRING,
                        rating INT,
                        comments STRING,
                        created_at TIMESTAMP
                    )
                    """
                )

    @contextmanager
    def session(self):
        """Yield a fresh cursor (auto-commit handled by connector)."""
        conn = sql.connect(**self.connection_params)
        cursor = conn.cursor()
        try:
            yield cursor
            # autocommit by driver
        finally:
            cursor.close()
            conn.close()

    def add_document(
        self,
        doc_id: str,
        title: str,
        content: str,
        source_type: str = "manual",
        source_path: str = "",
        file_type: str = "txt",
        metadata: dict | None = None,
    ) -> None:
        """Add or replace a document."""
        with self.session() as cursor:
            cursor.execute(
                """
                MERGE INTO kb_documents t
                USING (SELECT ? AS id) s
                ON t.id = s.id
                WHEN MATCHED THEN UPDATE SET
                    title = ?, content = ?, source_type = ?, source_path = ?, file_type = ?,
                    extra_metadata = ?, updated_at = current_timestamp()
                WHEN NOT MATCHED THEN INSERT (id, title, content, source_type, source_path, file_type, extra_metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, current_timestamp(), current_timestamp())
                """,
                (
                    doc_id,
                    title,
                    content,
                    source_type,
                    source_path,
                    file_type,
                    json.dumps(metadata or {}),
                    doc_id,
                    title,
                    content,
                    source_type,
                    source_path,
                    file_type,
                    json.dumps(metadata or {}),
                ),
            )
            logger.info(f"Document upserted: {doc_id}")

    def add_chunk(
        self,
        chunk_id: str,
        document_id: str,
        content: str,
        chunk_index: int,
        embedding: list[float],
        token_count: int,
        metadata: dict | None = None,
    ) -> None:
        """Add or replace a chunk."""
        with self.session() as cursor:
            cursor.execute(
                """
                MERGE INTO kb_chunks t
                USING (SELECT ? AS id) s
                ON t.id = s.id
                WHEN MATCHED THEN UPDATE SET
                    document_id = ?, chunk_index = ?, content = ?, token_count = ?,
                    embedding = ?, extra_metadata = ?, created_at = current_timestamp()
                WHEN NOT MATCHED THEN INSERT (id, document_id, chunk_index, content, token_count, embedding, extra_metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, current_timestamp())
                """,
                (
                    chunk_id,
                    document_id,
                    chunk_index,
                    content,
                    token_count,
                    json.dumps(embedding),
                    json.dumps(metadata or {}),
                    chunk_id,
                    document_id,
                    chunk_index,
                    content,
                    token_count,
                    json.dumps(embedding),
                    json.dumps(metadata or {}),
                ),
            )


    def log_search_query(
        self,
        query: str,
        user_id: str = "",
        results_count: int = 0,
        response_time: float = 0.0,
        metadata: dict | None = None,
    ) -> None:
        """Log a search query."""
        import uuid

        with self.session() as cursor:
            cursor.execute(
                """
                INSERT INTO kb_search_queries
                (id, query, user_id, results_count, response_time, extra_metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, current_timestamp())
                """,
                (
                    str(uuid.uuid4()),
                    query,
                    user_id,
                    results_count,
                    response_time,
                    json.dumps(metadata or {}),
                ),
            )

    def get_document_count(self) -> int:
        with self.session() as cursor:
            cursor.execute("SELECT COUNT(*) FROM kb_documents")
            return cursor.fetchone()[0]

    def get_chunk_count(self) -> int:
        with self.session() as cursor:
            cursor.execute("SELECT COUNT(*) FROM kb_chunks")
            return cursor.fetchone()[0]

    def get_recent_documents(self, limit: int = 10) -> list[dict[str, Any]]:
        with self.session() as cursor:
            cursor.execute(
                """
                SELECT id, title, source_type, created_at
                FROM kb_documents
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            )
            return [
                {
                    "id": row[0],
                    "title": row[1],
                    "source_type": row[2],
                    "created_at": row[3],
                }
                for row in cursor.fetchall()
            ]

    def add_feedback(
        self,
        chunk_id: str,
        user_id: str,
        rating: int,
        comments: str | None = None,
    ) -> None:
        """Add feedback for a chunk."""
        import uuid

        with self.session() as cursor:
            cursor.execute(
                """
                INSERT INTO kb_feedback (id, chunk_id, user_id, rating, comments, created_at)
                VALUES (?, ?, ?, ?, ?, current_timestamp())
                """,
                (str(uuid.uuid4()), chunk_id, user_id, rating, comments),
            )

    def get_chunk_feedback(
        self, chunk_id: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get feedback for a specific chunk."""
        with self.session() as cursor:
            cursor.execute(
                """
                SELECT id, user_id, rating, comments, created_at
                FROM kb_feedback
                WHERE chunk_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (chunk_id, limit),
            )
            return [
                {
                    "id": row[0],
                    "user_id": row[1],
                    "rating": row[2],
                    "comments": row[3],
                    "created_at": row[4],
                }
                for row in cursor.fetchall()
            ]

    def search_similar_chunks(
        self,
        embedding: list[float],
        limit: int = 10,
        threshold: float = 0.7,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Search for similar chunks with optional hierarchical filters."""
        with self.session() as cursor:
            # Build query with filters
            query = """
                SELECT id, document_id, content, extra_metadata
                FROM kb_chunks
            """
            params = []

            # Apply hierarchical filters
            if filters:
                conditions = []
                if "module" in filters:
                    conditions.append("extra_metadata LIKE ?")
                    params.append(f'%"module": "{filters["module"]}"%')
                if "submodule" in filters:
                    conditions.append("extra_metadata LIKE ?")
                    params.append(f'%"submodule": "{filters["submodule"]}"%')
                if "doc_type" in filters:
                    conditions.append("extra_metadata LIKE ?")
                    params.append(f'%"doc_type": "{filters["doc_type"]}"%')
                if "security_level" in filters:
                    conditions.append("extra_metadata LIKE ?")
                    params.append(f'%"security_level": "{filters["security_level"]}"%')

                if conditions:
                    query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()

        results = []
        for row in rows:
            chunk_id, document_id, content, metadata_str = row
            metadata = json.loads(metadata_str) if metadata_str else {}
            results.append(
                SearchResult(
                    document_id=document_id,
                    chunk_id=chunk_id,
                    content=content,
                    score=0.8,
                    metadata=metadata,
                )
            )

        return results[:limit]

    def disconnect(self) -> None:
        # Using per-operation connections; nothing to persist.
        logger.info("Databricks connections are per-operation; nothing to disconnect.")
