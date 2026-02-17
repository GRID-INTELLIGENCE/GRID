import json
import logging
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


class ResonanceQueryEngine:
    """
    Relational Query Engine for Resonance Telemetry.
    Enables SQL-based investigation and transformation of system state.
    """

    def __init__(self, db_path: str = "resonance_data.db"):
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self):
        """Ensure the schema is ready for querying."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS activity_log (
                    id TEXT PRIMARY KEY,
                    type TEXT,
                    query TEXT,
                    state TEXT,
                    created_at TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS telemetry_events (
                    id TEXT PRIMARY KEY,
                    activity_id TEXT,
                    event_type TEXT,
                    impact REAL,
                    payload_json TEXT,
                    created_at TIMESTAMP,
                    FOREIGN KEY (activity_id) REFERENCES activity_log (id)
                );
            """)

    def execute_query(self, sql: str) -> pd.DataFrame:
        """
        Execute a SQL query and return results as a Dataframe.
        Supports full SQLite syntax including Window Functions and CTEs.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query(sql, conn)
                return df
        except Exception as e:
            logger.error(f"SQL Execution Error: {e}")
            raise

    def ingest_batch(self, events: list[dict]):
        """Ingest a batch of events from the Bridge or WAL."""
        with sqlite3.connect(self.db_path) as conn:
            for event in events:
                conn.execute(
                    "INSERT OR IGNORE INTO telemetry_events VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        event.get("id", str(uuid.uuid4())),
                        event.get("activity_id"),
                        event.get("type"),
                        event.get("impact", 0.5),
                        json.dumps(event.get("data", {})),
                        event.get("timestamp", datetime.now(UTC).isoformat()),
                    ),
                )
            conn.commit()


# Example Investigative SQLs
QUERIES = {
    "impact_distribution": """
        SELECT event_type, AVG(impact) as mean_impact, COUNT(*) as count
        FROM telemetry_events
        GROUP BY event_type
        ORDER BY mean_impact DESC
    """,
    "hot_activities": """
        SELECT activity_id, COUNT(*) as event_density
        FROM telemetry_events
        GROUP BY activity_id
        HAVING event_density > 10
        ORDER BY event_density DESC
    """,
    "temporal_flow": """
        SELECT
            event_type,
            created_at,
            impact,
            AVG(impact) OVER (ORDER BY created_at ROWS BETWEEN 5 PRECEDING AND CURRENT ROW) as rolling_impact
        FROM telemetry_events
        WHERE activity_id = ?
    """,
}
