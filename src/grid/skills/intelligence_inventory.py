"""Persistent SQLite-backed intelligence inventory for skills.

Stores skill metadata, execution records, intelligence decisions, and performance baselines.
Uses WAL mode for concurrent read/write safety.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .execution_tracker import SkillExecutionRecord
    from .intelligence_tracker import IntelligenceRecord

logger = logging.getLogger(__name__)


@dataclass
class SkillIntelligenceSummary:
    """Aggregated intelligence summary for a skill."""

    skill_id: str
    total_executions: int
    success_rate: float
    avg_confidence: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    avg_complexity: int
    last_updated: float


class IntelligenceInventory:
    """Persistent inventory of skill intelligence data using SQLite.

    Features:
    - WAL mode for concurrent access
    - Batch inserts for performance
    - Configurable retention (default 90 days)
    - Performance regression detection
    """

    _instance: IntelligenceInventory | None = None
    _connection_pool: dict[int, sqlite3.Connection] = {}

    def __init__(
        self,
        storage_path: Path | None = None,
        retention_days: int = 90,
        batch_size: int = 10,
    ):
        """Initialize inventory.

        Args:
            storage_path: Path to SQLite database file
            retention_days: Days to retain records (default 90)
            batch_size: Records per batch insert
        """
        if storage_path is None:
            storage_path = Path(os.getenv("GRID_SKILLS_INVENTORY_PATH", "./data/skills_intelligence.db"))

        self._storage_path = storage_path
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._retention_days = int(os.getenv("GRID_SKILLS_RETENTION_DAYS", str(retention_days)))
        self._batch_size = int(os.getenv("GRID_SKILLS_BATCH_SIZE", str(batch_size)))

        # Pending records for batch insert
        self._pending_executions: list[dict] = []
        self._pending_intelligence: list[dict] = []

        # Initialize database
        self._init_schema()
        logger.info(f"IntelligenceInventory initialized: {self._storage_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local connection with WAL mode."""
        import threading

        tid = threading.get_ident()

        if tid not in self._connection_pool:
            conn = sqlite3.connect(str(self._storage_path), check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")
            conn.row_factory = sqlite3.Row
            self._connection_pool[tid] = conn

        return self._connection_pool[tid]

    def _init_schema(self) -> None:
        """Initialize database schema with version management."""
        conn = self._get_connection()

        # Check current schema version
        cursor = conn.execute("PRAGMA user_version")
        current_version = cursor.fetchone()[0]

        if current_version == 0:
            # Fresh database or Phase 1 (no version set)
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()

            if not tables:
                # Fresh setup - create all tables
                self._create_schema_v2(conn)
            else:
                # Phase 1 -> Phase 2 migration
                logger.info("Migrating schema from Phase 1 to Phase 2...")
                self._migrate_phase1_to_phase2(conn)

            conn.execute("PRAGMA user_version = 2")
            conn.commit()

        elif current_version < 2:
            # Future migration path
            self._migrate_phase1_to_phase2(conn)
            conn.execute("PRAGMA user_version = 2")
            conn.commit()

        # Create indexes if missing
        self._ensure_indexes(conn)

    def _create_schema_v2(self, conn: sqlite3.Connection) -> None:
        """Create Phase 2 schema from scratch."""
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS skill_metadata (
                skill_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                version TEXT,
                category TEXT,
                subcategory TEXT,
                tags TEXT,
                complexity_score INTEGER DEFAULT 0,
                performance_profile TEXT DEFAULT 'unknown',
                file_path TEXT,
                current_version TEXT,
                version_history TEXT,
                last_updated REAL
            );

            CREATE TABLE IF NOT EXISTS execution_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_id TEXT NOT NULL,
                timestamp REAL NOT NULL,
                status TEXT NOT NULL,
                execution_time_ms REAL,
                confidence_score REAL,
                error TEXT,
                input_args_hash TEXT,
                fallback_used INTEGER DEFAULT 0,
                FOREIGN KEY (skill_id) REFERENCES skill_metadata(skill_id)
            );

            CREATE TABLE IF NOT EXISTS intelligence_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_id TEXT NOT NULL,
                decision_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                rationale TEXT,
                alternatives TEXT,
                outcome TEXT,
                timestamp REAL NOT NULL,
                FOREIGN KEY (skill_id) REFERENCES skill_metadata(skill_id)
            );

            CREATE TABLE IF NOT EXISTS performance_baselines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_id TEXT NOT NULL,
                skill_version TEXT,
                p50_ms REAL,
                p95_ms REAL,
                p99_ms REAL,
                avg_ms REAL,
                sample_count INTEGER,
                captured_reason TEXT DEFAULT 'manual',
                captured_at REAL NOT NULL,
                FOREIGN KEY (skill_id) REFERENCES skill_metadata(skill_id)
            );
        """)
        conn.commit()
        logger.info("Created Phase 2 schema")

    def _migrate_phase1_to_phase2(self, conn: sqlite3.Connection) -> None:
        """Migrate Phase 1 schema to Phase 2, preserving data."""
        # Add new columns to performance_baselines if they don't exist
        try:
            conn.execute("ALTER TABLE performance_baselines ADD COLUMN skill_version TEXT")
            logger.debug("Added skill_version column")
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            conn.execute("ALTER TABLE performance_baselines ADD COLUMN captured_reason TEXT DEFAULT 'manual'")
            logger.debug("Added captured_reason column")
        except sqlite3.OperationalError:
            pass  # Column already exists

        conn.commit()
        logger.info("Phase 1 -> Phase 2 migration complete")

    def _ensure_indexes(self, conn: sqlite3.Connection) -> None:
        """Ensure all indexes exist."""
        conn.executescript("""
            CREATE INDEX IF NOT EXISTS idx_exec_skill ON execution_records(skill_id);
            CREATE INDEX IF NOT EXISTS idx_exec_time ON execution_records(timestamp);
            CREATE INDEX IF NOT EXISTS idx_intel_skill ON intelligence_records(skill_id);
            CREATE INDEX IF NOT EXISTS idx_baseline_skill ON performance_baselines(skill_id);
            CREATE INDEX IF NOT EXISTS idx_baseline_version ON performance_baselines(skill_id, skill_version);
        """)
        conn.commit()

    @classmethod
    def get_instance(cls) -> IntelligenceInventory:
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register_skill(
        self,
        skill_id: str,
        name: str,
        description: str = "",
        version: str = "1.0.0",
        category: str = "misc",
        subcategory: str = "generic",
        tags: list[str] | None = None,
        complexity_score: int = 0,
        performance_profile: str = "unknown",
        file_path: str = "",
    ) -> None:
        """Register or update skill metadata."""
        conn = self._get_connection()

        # Get existing version history
        cursor = conn.execute(
            "SELECT version_history, current_version FROM skill_metadata WHERE skill_id=?", [skill_id]
        )
        row = cursor.fetchone()

        version_history = []
        if row and row["version_history"]:
            version_history = json.loads(row["version_history"])

        # Add current version to history if different
        if row and row["current_version"] and row["current_version"] != version:
            version_history.append({"version": row["current_version"], "timestamp": time.time()})

        conn.execute(
            """
            INSERT OR REPLACE INTO skill_metadata
            (skill_id, name, description, version, category, subcategory, tags,
             complexity_score, performance_profile, file_path, current_version,
             version_history, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            [
                skill_id,
                name,
                description,
                version,
                category,
                subcategory,
                json.dumps(tags or []),
                complexity_score,
                performance_profile,
                file_path,
                version,
                json.dumps(version_history),
                time.time(),
            ],
        )
        conn.commit()
        logger.debug(f"Registered skill: {skill_id} v{version}")

    def store_execution(self, record: SkillExecutionRecord) -> None:
        """Store execution record (batched)."""
        import hashlib

        # Hash input args to avoid storing large data
        args_hash = hashlib.md5(json.dumps(record.input_args, sort_keys=True, default=str).encode()).hexdigest()[:12]

        self._pending_executions.append(
            {
                "skill_id": record.skill_id,
                "timestamp": record.timestamp,
                "status": record.status.value if hasattr(record.status, "value") else str(record.status),
                "execution_time_ms": record.execution_time_ms,
                "confidence_score": record.confidence_score,
                "error": record.error,
                "input_args_hash": args_hash,
                "fallback_used": 1 if record.fallback_used else 0,
            }
        )

        if len(self._pending_executions) >= self._batch_size:
            self._flush_executions()

    def _flush_executions(self) -> None:
        """Flush pending execution records to database."""
        if not self._pending_executions:
            return

        conn = self._get_connection()
        conn.executemany(
            """
            INSERT INTO execution_records
            (skill_id, timestamp, status, execution_time_ms, confidence_score,
             error, input_args_hash, fallback_used)
            VALUES (:skill_id, :timestamp, :status, :execution_time_ms,
                    :confidence_score, :error, :input_args_hash, :fallback_used)
        """,
            self._pending_executions,
        )
        conn.commit()

        count = len(self._pending_executions)
        self._pending_executions.clear()
        logger.debug(f"Flushed {count} execution records")

    def store_intelligence(self, record: IntelligenceRecord) -> None:
        """Store intelligence record (batched)."""
        self._pending_intelligence.append(
            {
                "skill_id": record.skill_id,
                "decision_type": (
                    record.decision_type.value if hasattr(record.decision_type, "value") else str(record.decision_type)
                ),
                "confidence": record.confidence,
                "rationale": record.rationale,
                "alternatives": json.dumps(record.alternatives),
                "outcome": record.outcome,
                "timestamp": record.timestamp,
            }
        )

        if len(self._pending_intelligence) >= self._batch_size:
            self._flush_intelligence()

    def _flush_intelligence(self) -> None:
        """Flush pending intelligence records to database."""
        if not self._pending_intelligence:
            return

        conn = self._get_connection()
        conn.executemany(
            """
            INSERT INTO intelligence_records
            (skill_id, decision_type, confidence, rationale, alternatives, outcome, timestamp)
            VALUES (:skill_id, :decision_type, :confidence, :rationale,
                    :alternatives, :outcome, :timestamp)
        """,
            self._pending_intelligence,
        )
        conn.commit()

        count = len(self._pending_intelligence)
        self._pending_intelligence.clear()
        logger.debug(f"Flushed {count} intelligence records")

    def flush_all(self) -> None:
        """Flush all pending records."""
        self._flush_executions()
        self._flush_intelligence()

    def capture_baseline(self, skill_id: str, metrics: dict[str, float], sample_count: int = 0) -> None:
        """Capture performance baseline snapshot."""
        conn = self._get_connection()
        conn.execute(
            """
            INSERT INTO performance_baselines
            (skill_id, p50_ms, p95_ms, p99_ms, avg_ms, sample_count, captured_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            [
                skill_id,
                metrics.get("p50_ms", 0),
                metrics.get("p95_ms", 0),
                metrics.get("p99_ms", 0),
                metrics.get("avg_ms", 0),
                sample_count,
                time.time(),
            ],
        )
        conn.commit()
        logger.info(f"Captured baseline for {skill_id}: p50={metrics.get('p50_ms', 0):.1f}ms")

    def get_skill_summary(self, skill_id: str) -> SkillIntelligenceSummary | None:
        """Get aggregated intelligence summary for a skill."""
        conn = self._get_connection()

        # Get metadata
        cursor = conn.execute("SELECT * FROM skill_metadata WHERE skill_id=?", [skill_id])
        metadata = cursor.fetchone()
        if not metadata:
            return None

        # Get execution stats
        cursor = conn.execute(
            """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) as successes,
                AVG(execution_time_ms) as avg_time,
                AVG(confidence_score) as avg_confidence
            FROM execution_records
            WHERE skill_id=?
        """,
            [skill_id],
        )
        exec_stats = cursor.fetchone()

        total = exec_stats["total"] or 0
        if total == 0:
            return SkillIntelligenceSummary(
                skill_id=skill_id,
                total_executions=0,
                success_rate=0.0,
                avg_confidence=0.0,
                p50_latency_ms=0.0,
                p95_latency_ms=0.0,
                p99_latency_ms=0.0,
                avg_complexity=metadata["complexity_score"] or 0,
                last_updated=metadata["last_updated"] or 0.0,
            )

        success_rate = (exec_stats["successes"] or 0) / total

        # Calculate percentiles
        cursor = conn.execute(
            """
            SELECT execution_time_ms
            FROM execution_records
            WHERE skill_id=? AND execution_time_ms IS NOT NULL
            ORDER BY execution_time_ms
        """,
            [skill_id],
        )
        latencies = [row["execution_time_ms"] for row in cursor.fetchall()]

        p50, p95, p99 = 0.0, 0.0, 0.0
        if latencies:
            p50 = latencies[int(len(latencies) * 0.5)]
            p95 = latencies[min(len(latencies) - 1, int(len(latencies) * 0.95))]
            p99 = latencies[min(len(latencies) - 1, int(len(latencies) * 0.99))]

        return SkillIntelligenceSummary(
            skill_id=skill_id,
            total_executions=total,
            success_rate=success_rate,
            avg_confidence=exec_stats["avg_confidence"] or 0.0,
            p50_latency_ms=p50,
            p95_latency_ms=p95,
            p99_latency_ms=p99,
            avg_complexity=metadata["complexity_score"] or 0,
            last_updated=metadata["last_updated"] or 0.0,
        )

    def check_regression(
        self,
        skill_id: str,
        current_metrics: dict[str, float],
        threshold: float = 1.2,
    ) -> dict[str, Any] | None:
        """Check for performance regression against baseline.

        Args:
            skill_id: Skill to check
            current_metrics: Current p50_ms, p95_ms, p99_ms values
            threshold: Regression threshold (1.2 = 20% degradation)

        Returns:
            Dict of regressions if found, None otherwise
        """
        threshold = float(os.getenv("GRID_SKILLS_REGRESSION_THRESHOLD", str(threshold)))

        conn = self._get_connection()
        cursor = conn.execute(
            """
            SELECT p50_ms, p95_ms, p99_ms, avg_ms
            FROM performance_baselines
            WHERE skill_id=?
            ORDER BY captured_at DESC
            LIMIT 1
        """,
            [skill_id],
        )

        baseline = cursor.fetchone()
        if not baseline:
            return None

        regressions = {}
        for metric in ["p50_ms", "p95_ms", "p99_ms"]:
            baseline_val = baseline[metric]
            current_val = current_metrics.get(metric, 0)

            if baseline_val and current_val > baseline_val * threshold:
                regressions[metric] = {
                    "baseline": baseline_val,
                    "current": current_val,
                    "degradation_pct": ((current_val / baseline_val) - 1) * 100,
                }

        return regressions if regressions else None

    def cleanup_old_records(self) -> int:
        """Delete records older than retention period. Returns count deleted."""
        cutoff = time.time() - (self._retention_days * 86400)

        conn = self._get_connection()
        cursor = conn.execute("DELETE FROM execution_records WHERE timestamp < ?", [cutoff])
        exec_deleted = cursor.rowcount

        cursor = conn.execute("DELETE FROM intelligence_records WHERE timestamp < ?", [cutoff])
        intel_deleted = cursor.rowcount

        conn.commit()

        total = exec_deleted + intel_deleted
        if total > 0:
            logger.info(f"Cleaned up {total} old records (>{self._retention_days} days)")

        return total

    def get_all_skill_ids(self) -> list[str]:
        """Get all registered skill IDs."""
        conn = self._get_connection()
        cursor = conn.execute("SELECT skill_id FROM skill_metadata ORDER BY skill_id")
        return [row["skill_id"] for row in cursor.fetchall()]

    def export_inventory(self, format: str = "json") -> str:
        """Export full inventory as JSON."""
        self.flush_all()

        skills_data = {}
        for skill_id in self.get_all_skill_ids():
            summary = self.get_skill_summary(skill_id)
            if summary:
                skills_data[skill_id] = asdict(summary)

        return json.dumps(
            {
                "exported_at": time.time(),
                "total_skills": len(skills_data),
                "retention_days": self._retention_days,
                "skills": skills_data,
            },
            indent=2,
        )

    def close(self) -> None:
        """Flush and close all connections."""
        self.flush_all()
        for conn in self._connection_pool.values():
            conn.close()
        self._connection_pool.clear()
        logger.info("IntelligenceInventory closed")
