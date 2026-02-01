"""Streams activity events to Databricks with local SQLite fallback."""

import json
import logging
from typing import Any

from sqlalchemy import text

from application.mothership.db.databricks_connector import DatabricksConnector
from grid.skills.intelligence_inventory import IntelligenceInventory

logger = logging.getLogger(__name__)


class DatabaseStreamer:
    """Handles streaming of events to persistent storage."""

    def __init__(self, use_databricks: bool = True):
        self.use_databricks = use_databricks
        self.local_inventory = IntelligenceInventory.get_instance()
        self.databricks = None

        if use_databricks:
            try:
                self.databricks = DatabricksConnector()
                logger.info("DatabaseStreamer: Connected to Databricks")
            except Exception as e:
                logger.warning(f"DatabaseStreamer: Databricks connection failed, using local only: {e}")
                self.use_databricks = False

    def stream_events(self, events: list[Any]):
        """Stream a list of events to the database."""
        if not events:
            return

        # Always log to local for safety
        for event in events:
            self._log_to_local(event)

        # Stream to Databricks if available
        if self.use_databricks and self.databricks:
            try:
                self._stream_to_databricks(events)
            except Exception as e:
                logger.error(f"DatabaseStreamer: Failed to stream to Databricks: {e}")

    def _log_to_local(self, event: Any):
        """Log event to local Intelligence Inventory."""
        try:
            # Reusing the mechanism for storing "records" but tailored for activity
            # This is a bit of a shim but ensures persistence
            # In a real app, we'd have a dedicated 'activity' table
            self.local_inventory._get_connection().execute(
                "INSERT INTO intelligence_records (skill_id, decision_type, confidence, rationale, timestamp) "
                "VALUES (?, ?, ?, ?, ?)",
                ["codebase_tracker", event.event_type, 1.0, json.dumps(event.to_dict()), event.timestamp],
            )
            self.local_inventory._get_connection().commit()
        except Exception as e:
            logger.error(f"DatabaseStreamer: Local log failed: {e}")

    def _stream_to_databricks(self, events: list[Any]):
        """Stream events to Databricks SQL Warehouse."""
        engine = self.databricks.create_engine()
        with engine.begin() as conn:
            # Ensure table exists (Heist Aware Schema)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS codebase_activity (
                    timestamp TIMESTAMP,
                    event_type STRING,
                    path STRING,
                    details STRING,
                    severity STRING
                )
            """))

            # Insert events
            for event in events:
                conn.execute(
                    text(
                        "INSERT INTO codebase_activity (timestamp, event_type, path, details, severity) "
                        "VALUES (:ts, :type, :path, :details, :sev)"
                    ),
                    {
                        "ts": event.timestamp,
                        "type": event.event_type,
                        "path": event.path,
                        "details": json.dumps(event.details),
                        "sev": event.severity,
                    },
                )
        logger.info(f"DatabaseStreamer: Streamed {len(events)} events to Databricks")


if __name__ == "__main__":
    # Basic test
    from grid.security.codebase_tracker import ActivityEvent

    streamer = DatabaseStreamer(use_databricks=False)
    test_event = ActivityEvent("test_stream", "e:/grid", {"test": True})
    streamer.stream_events([test_event])
    print("Streamed test event locally.")
