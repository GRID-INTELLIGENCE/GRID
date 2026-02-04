#!/usr/bin/env python3
"""Collect interfaces metrics and push to Databricks/SQLite.

Main script to collect performance metrics from grid/interfaces/
and push them to Databricks tables (or SQLite for prototype).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sqlite3
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from pathlib import Path as PathType
from typing import Any

# Add project root to path
project_root = PathType(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession

from grid.interfaces.config import DashboardConfig, get_config
from grid.interfaces.metrics_collector import BridgeMetrics, MetricsCollector, SensoryMetrics

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class MetricsWriter:
    """Writes metrics to database (Databricks or SQLite)."""

    def __init__(self, config: DashboardConfig):
        """Initialize metrics writer.

        Args:
            config: Dashboard configuration
        """
        self.config = config
        self._databricks_engine: Engine | None = None

    def _get_databricks_engine(self) -> Engine:
        """Get Databricks engine.

        Returns:
            SQLAlchemy engine for Databricks
        """
        if self._databricks_engine is not None:
            return self._databricks_engine

        from application.mothership.db.databricks_connector import create_databricks_engine

        self._databricks_engine = create_databricks_engine()
        return self._databricks_engine

    def _insert_bridge_metrics_databricks(self, metrics: list[BridgeMetrics]) -> int:
        """Insert bridge metrics into Databricks.

        Args:
            metrics: List of bridge metrics

        Returns:
            Number of records inserted
        """
        if not metrics:
            return 0

        engine = self._get_databricks_engine()
        table_name = self.config.get_bridge_table_name()

        inserted = 0
        batch_size = self.config.batch_size

        for i in range(0, len(metrics), batch_size):
            batch = metrics[i : i + batch_size]
            values = []

            for m in batch:
                values.append(
                    f"("
                    f"'{m.timestamp.isoformat()}', "
                    f"'{m.trace_id}', "
                    f"{m.transfer_latency_ms}, "
                    f"{m.compressed_size}, "
                    f"{m.raw_size}, "
                    f"{m.compression_ratio}, "
                    f"{m.coherence_level}, "
                    f"{m.entanglement_count}, "
                    f"'{m.integrity_check}', "
                    f"{1 if m.success else 0}, "
                    f"'{m.source_module}', "
                    f"'{json.dumps(m.metadata).replace(chr(39), chr(39) + chr(39))}'"
                    f")"
                )

            sql = f"""
            INSERT INTO {table_name} (
                timestamp, trace_id, transfer_latency_ms, compressed_size, raw_size,
                compression_ratio, coherence_level, entanglement_count, integrity_check,
                success, source_module, metadata
            )
            VALUES {",".join(values)}
            """

            try:
                with engine.connect() as conn:
                    conn.execute(text(sql))
                    conn.commit()
                    inserted += len(batch)
                    logger.info(f"Inserted {len(batch)} bridge metrics (total: {inserted})")
            except Exception as e:
                logger.error(f"Failed to insert bridge metrics batch: {e}")
                continue

        return inserted

    def _insert_sensory_metrics_databricks(self, metrics: list[SensoryMetrics]) -> int:
        """Insert sensory metrics into Databricks.

        Args:
            metrics: List of sensory metrics

        Returns:
            Number of records inserted
        """
        if not metrics:
            return 0

        engine = self._get_databricks_engine()
        table_name = self.config.get_sensory_table_name()

        inserted = 0
        batch_size = self.config.batch_size

        for i in range(0, len(metrics), batch_size):
            batch = metrics[i : i + batch_size]
            values = []

            for m in batch:
                if m.error_message:
                    error_msg = m.error_message.replace(chr(39), chr(39) + chr(39))
                    error_sql = f"'{error_msg}'"
                else:
                    error_sql = "NULL"

                metadata_json = json.dumps(m.metadata).replace(chr(39), chr(39) + chr(39))

                values.append(
                    f"("
                    f"'{m.timestamp.isoformat()}', "
                    f"'{m.trace_id}', "
                    f"'{m.modality}', "
                    f"{m.duration_ms}, "
                    f"{m.coherence}, "
                    f"{m.raw_size}, "
                    f"'{m.source}', "
                    f"{1 if m.success else 0}, "
                    f"{error_sql}, "
                    f"'{metadata_json}'"
                    f")"
                )

            sql = f"""
            INSERT INTO {table_name} (
                timestamp, trace_id, modality, duration_ms, coherence, raw_size,
                source, success, error_message, metadata
            )
            VALUES {",".join(values)}
            """

            try:
                with engine.connect() as conn:
                    conn.execute(text(sql))
                    conn.commit()
                    inserted += len(batch)
                    logger.info(f"Inserted {len(batch)} sensory metrics (total: {inserted})")
            except Exception as e:
                logger.error(f"Failed to insert sensory metrics batch: {e}")
                continue

        return inserted

    def _init_sqlite_db(self, db_path: str) -> sqlite3.Connection:
        """Initialize SQLite database with schema.

        Args:
            db_path: Path to SQLite database

        Returns:
            SQLite connection
        """
        db_file = Path(db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        # Read and execute schema
        schema_file = Path(__file__).parent.parent / "grid" / "interfaces" / "prototype_schema.sql"
        if schema_file.exists():
            with open(schema_file) as f:
                schema_sql = f.read()

            # SQLite doesn't support CREATE INDEX IF NOT EXISTS in same statement
            # Split statements
            statements = [s.strip() for s in schema_sql.split(";") if s.strip()]

            for statement in statements:
                if statement:
                    try:
                        conn.execute(statement)
                    except sqlite3.OperationalError as e:
                        # Ignore "table already exists" errors
                        if "already exists" not in str(e).lower():
                            logger.warning(f"Schema statement failed: {e}")

            conn.commit()

        return conn

    def _insert_bridge_metrics_sqlite(self, conn: sqlite3.Connection, metrics: list[BridgeMetrics]) -> int:
        """Insert bridge metrics into SQLite.

        Args:
            conn: SQLite connection
            metrics: List of bridge metrics

        Returns:
            Number of records inserted
        """
        if not metrics:
            return 0

        table_name = "interfaces_bridge_metrics"
        inserted = 0

        for m in metrics:
            try:
                conn.execute(
                    f"""
                    INSERT INTO {table_name} (
                        timestamp, trace_id, transfer_latency_ms, compressed_size, raw_size,
                        compression_ratio, coherence_level, entanglement_count, integrity_check,
                        success, source_module, metadata
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        m.timestamp.isoformat(),
                        m.trace_id,
                        m.transfer_latency_ms,
                        m.compressed_size,
                        m.raw_size,
                        m.compression_ratio,
                        m.coherence_level,
                        m.entanglement_count,
                        m.integrity_check,
                        1 if m.success else 0,
                        m.source_module,
                        json.dumps(m.metadata),
                    ),
                )
                inserted += 1
            except Exception as e:
                logger.warning(f"Failed to insert bridge metric {m.trace_id}: {e}")
                continue

        conn.commit()
        return inserted

    def _insert_sensory_metrics_sqlite(self, conn: sqlite3.Connection, metrics: list[SensoryMetrics]) -> int:
        """Insert sensory metrics into SQLite.

        Args:
            conn: SQLite connection
            metrics: List of sensory metrics

        Returns:
            Number of records inserted
        """
        if not metrics:
            return 0

        table_name = "interfaces_sensory_metrics"
        inserted = 0

        for m in metrics:
            try:
                conn.execute(
                    f"""
                    INSERT INTO {table_name} (
                        timestamp, trace_id, modality, duration_ms, coherence, raw_size,
                        source, success, error_message, metadata
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        m.timestamp.isoformat(),
                        m.trace_id,
                        m.modality,
                        m.duration_ms,
                        m.coherence,
                        m.raw_size,
                        m.source,
                        1 if m.success else 0,
                        m.error_message,
                        json.dumps(m.metadata),
                    ),
                )
                inserted += 1
            except Exception as e:
                logger.warning(f"Failed to insert sensory metric {m.trace_id}: {e}")
                continue

        conn.commit()
        return inserted

    async def write_metrics(
        self,
        bridge_metrics: list[BridgeMetrics],
        sensory_metrics: list[SensoryMetrics],
    ) -> dict[str, int]:
        """Write metrics to database.

        Args:
            bridge_metrics: List of bridge metrics
            sensory_metrics: List of sensory metrics

        Returns:
            Dictionary with insertion counts
        """
        results = {"bridge_inserted": 0, "sensory_inserted": 0}

        if self.config.use_databricks and not self.config.prototype_mode:
            # Write to Databricks
            logger.info(
                f"Writing {len(bridge_metrics)} bridge and {len(sensory_metrics)} sensory metrics to Databricks"
            )
            results["bridge_inserted"] = self._insert_bridge_metrics_databricks(bridge_metrics)
            results["sensory_inserted"] = self._insert_sensory_metrics_databricks(sensory_metrics)
        else:
            # Write to SQLite (prototype)
            logger.info(
                f"Writing {len(bridge_metrics)} bridge and {len(sensory_metrics)} sensory metrics to SQLite prototype"
            )
            conn = self._init_sqlite_db(self.config.prototype_db_path)
            try:
                results["bridge_inserted"] = self._insert_bridge_metrics_sqlite(conn, bridge_metrics)
                results["sensory_inserted"] = self._insert_sensory_metrics_sqlite(conn, sensory_metrics)
            finally:
                conn.close()

        return results


async def collect_and_write(
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    config: DashboardConfig | None = None,
    session: AsyncSession | None = None,
    from_json: bool = False,
    json_days: int = 7,
    json_files: list[Path] | None = None,
) -> dict[str, Any]:
    """Collect metrics and write to database.

    Args:
        start_time: Start time for collection (default: 7 days ago)
        end_time: End time for collection (default: now)
        config: Dashboard configuration (default: from environment)
        session: Database session for audit logs (optional)
        from_json: If True, collect from JSON files instead of audit logs/traces
        json_days: Number of days to scan back for JSON files (default: 7)
        json_files: Optional list of specific JSON files to process

    Returns:
        Dictionary with collection and write results
    """
    if config is None:
        config = get_config()

    if start_time is None:
        start_time = datetime.now(UTC) - config.get_time_window_delta()
    if end_time is None:
        end_time = datetime.now(UTC)

    # Create collector
    collector = MetricsCollector(session=session)

    bridge_metrics = []
    sensory_metrics = []

    if from_json:
        # Collect from JSON files
        logger.info(f"Collecting metrics from JSON files (last {json_days} days)")
        bridge_metrics, sensory_metrics = collector.collect_from_json_files(
            json_files=json_files,
            scan_days=json_days,
        )
    else:
        # Collect from audit logs and traces
        logger.info(f"Collecting metrics from audit logs and traces ({start_time} to {end_time})")
        bridge_metrics, sensory_metrics = await collector.collect_all(
            start_time=start_time,
            end_time=end_time,
            trace_limit=config.trace_limit,
        )

    logger.info(f"Collected {len(bridge_metrics)} bridge metrics and {len(sensory_metrics)} sensory metrics")

    # Write metrics
    writer = MetricsWriter(config)
    write_results = await writer.write_metrics(bridge_metrics, sensory_metrics)

    return {
        "bridge_collected": len(bridge_metrics),
        "sensory_collected": len(sensory_metrics),
        "bridge_inserted": write_results["bridge_inserted"],
        "sensory_inserted": write_results["sensory_inserted"],
        "start_time": start_time.isoformat() if start_time else None,
        "end_time": end_time.isoformat() if end_time else None,
        "from_json": from_json,
    }


async def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success)
    """
    parser = argparse.ArgumentParser(description="Collect interfaces metrics and push to Databricks/SQLite")
    parser.add_argument(
        "--days",
        type=int,
        default=None,
        help="Number of days to collect (default: from config)",
    )
    parser.add_argument(
        "--start-time",
        type=str,
        default=None,
        help="Start time (ISO format, default: N days ago)",
    )
    parser.add_argument(
        "--end-time",
        type=str,
        default=None,
        help="End time (ISO format, default: now)",
    )
    parser.add_argument(
        "--prototype",
        action="store_true",
        help="Use SQLite prototype mode",
    )
    parser.add_argument(
        "--databricks",
        action="store_true",
        help="Use Databricks (overrides prototype)",
    )
    parser.add_argument(
        "--from-json",
        action="store_true",
        help="Collect metrics from JSON files instead of audit logs/traces",
    )
    parser.add_argument(
        "--json-days",
        type=int,
        default=7,
        help="Number of days to scan back for JSON files (default: 7)",
    )
    parser.add_argument(
        "--json-files",
        type=str,
        nargs="+",
        default=None,
        help="Specific JSON files to process (overrides scan)",
    )

    args = parser.parse_args()

    config = get_config()

    # Override config based on args
    if args.databricks:
        config.prototype_mode = False
        config.use_databricks = True
    elif args.prototype:
        config.prototype_mode = True
        config.use_databricks = False

    # Parse time window
    start_time = None
    end_time = None

    if args.start_time:
        start_time = datetime.fromisoformat(args.start_time.replace("Z", "+00:00"))
    elif args.days:
        start_time = datetime.now(UTC) - timedelta(days=args.days)

    if args.end_time:
        end_time = datetime.fromisoformat(args.end_time.replace("Z", "+00:00"))

    # Get database session if needed
    session = None
    if not config.prototype_mode and config.use_databricks:
        # For Databricks, we don't need async session (sync engine)
        pass
    else:
        # For audit log collection, we might need a session
        # For now, we'll skip audit logs in prototype mode
        pass

    # Parse JSON files if provided
    json_files = None
    if args.json_files:
        json_files = [Path(f) for f in args.json_files]

    try:
        results = await collect_and_write(
            start_time=start_time,
            end_time=end_time,
            config=config,
            session=session,
            from_json=args.from_json,
            json_days=args.json_days,
            json_files=json_files,
        )
        logger.info("Collection complete:")
        logger.info(f"  Bridge metrics: {results['bridge_collected']} collected, {results['bridge_inserted']} inserted")
        logger.info(
            f"  Sensory metrics: {results['sensory_collected']} collected, {results['sensory_inserted']} inserted"
        )
        if results.get("from_json"):
            logger.info(f"  Data source: JSON files (scanned last {args.json_days} days)")
        return 0
    except Exception as e:
        logger.error(f"Collection failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
