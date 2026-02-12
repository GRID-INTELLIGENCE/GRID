"""Databricks-backed manifest tracking for incremental RAG indexing.

This stores file-level state in a Delta table so we can skip unchanged files,
remove deleted files, and keep indexing fast across machines.
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class DatabricksFileState:
    repo: str
    path: str
    file_hash: str
    file_size: int
    mtime_ms: int
    chunk_count: int


class DatabricksManifestTracker:
    def __init__(
        self,
        *,
        schema: str = "default",
        table: str = "rag_file_manifest",
        repo: str,
    ) -> None:
        self.schema = schema
        self.table = f"{schema}.{table}" if schema and schema != "default" else table
        self.repo = repo

        self._host = os.getenv("DATABRICKS_HOST", "").strip() or os.getenv("DATABRICKS_SERVER_HOSTNAME", "").strip()
        self._http_path = os.getenv("DATABRICKS_HTTP_PATH", "").strip()
        self._token = (
            os.getenv("DATABRICKS_TOKEN", "").strip()
            or os.getenv("DATABRICKS_ACCESS_TOKEN", "").strip()
            or os.getenv("local_databricks", "").strip()
        )
        self._token = self._normalize_token(self._token)

        if self._host.startswith("https://"):
            self._host = self._host.replace("https://", "")
        if self._host.startswith("http://"):
            self._host = self._host.replace("http://", "")

        if not self._host:
            raise ValueError("DATABRICKS_HOST (or DATABRICKS_SERVER_HOSTNAME) is required")
        if not self._http_path:
            raise ValueError("DATABRICKS_HTTP_PATH is required")
        if not self._token:
            raise ValueError("DATABRICKS_TOKEN (or DATABRICKS_ACCESS_TOKEN) is required")

        self._ensure_table()

    def _connect(self):
        from databricks import sql

        return sql.connect(server_hostname=self._host, http_path=self._http_path, access_token=self._token)

    @staticmethod
    def _normalize_token(token: str) -> str:
        t = (token or "").strip()
        if not t:
            return ""

        if "Header Parameter" in t and "Authorization" in t:
            lines = [ln.strip() for ln in t.splitlines() if ln.strip()]
            last = lines[-1] if lines else ""
            if "," in last:
                last = last.split(",")[-1].strip()
            t = last

        if t.lower().startswith("bearer "):
            t = t[7:].strip()

        t = "".join(t.splitlines()).strip()
        return t

    @staticmethod
    def _esc(s: str) -> str:
        return s.replace("'", "''")

    def _ensure_table(self) -> None:
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.table} (
            repo STRING,
            path STRING,
            file_hash STRING,
            file_size BIGINT,
            mtime_ms BIGINT,
            chunk_count INT,
            indexed_at TIMESTAMP
        ) USING DELTA
        """

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(create_sql)

    def fetch_all(self) -> dict[str, DatabricksFileState]:
        sql_txt = f"""
        SELECT repo, path, file_hash, file_size, mtime_ms, chunk_count
        FROM {self.table}
        WHERE repo = '{self._esc(self.repo)}'
        """

        out: dict[str, DatabricksFileState] = {}
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql_txt)
                rows = cur.fetchall() or []

        for r in rows:
            state = DatabricksFileState(
                repo=str(r[0]),
                path=str(r[1]),
                file_hash=str(r[2] or ""),
                file_size=int(r[3] or 0),
                mtime_ms=int(r[4] or 0),
                chunk_count=int(r[5] or 0),
            )
            out[state.path] = state
        return out

    def delete_paths(self, paths: Iterable[str]) -> int:
        paths = list(paths)
        if not paths:
            return 0

        deleted = 0
        batch_size = 200
        for i in range(0, len(paths), batch_size):
            batch = paths[i : i + batch_size]
            in_list = ",".join(f"'{self._esc(p)}'" for p in batch)
            sql_txt = f"""
            DELETE FROM {self.table}
            WHERE repo = '{self._esc(self.repo)}' AND path IN ({in_list})
            """
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql_txt)
            deleted += len(batch)

        return deleted

    def upsert_states(self, states: list[DatabricksFileState]) -> int:
        if not states:
            return 0

        now = datetime.now(UTC).isoformat()
        upserted = 0
        batch_size = 200

        for i in range(0, len(states), batch_size):
            batch = states[i : i + batch_size]

            rows = []
            for s in batch:
                rows.append(
                    "SELECT "
                    f"'{self._esc(s.repo)}' AS repo, "
                    f"'{self._esc(s.path)}' AS path, "
                    f"'{self._esc(s.file_hash)}' AS file_hash, "
                    f"{int(s.file_size)} AS file_size, "
                    f"{int(s.mtime_ms)} AS mtime_ms, "
                    f"{int(s.chunk_count)} AS chunk_count, "
                    f"CAST('{now}' AS TIMESTAMP) AS indexed_at"
                )

            source_sql = "\nUNION ALL\n".join(rows)

            sql_txt = f"""
            MERGE INTO {self.table} AS target
            USING (
                {source_sql}
            ) AS source
            ON target.repo = source.repo AND target.path = source.path
            WHEN MATCHED THEN
              UPDATE SET
                file_hash = source.file_hash,
                file_size = source.file_size,
                mtime_ms = source.mtime_ms,
                chunk_count = source.chunk_count,
                indexed_at = source.indexed_at
            WHEN NOT MATCHED THEN
              INSERT (repo, path, file_hash, file_size, mtime_ms, chunk_count, indexed_at)
              VALUES (source.repo, source.path, source.file_hash, source.file_size, source.mtime_ms, source.chunk_count, source.indexed_at)
            """

            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql_txt)

            upserted += len(batch)

        return upserted
