#!/usr/bin/env python3
"""Integration test for interfaces metrics collection and dashboard."""

from __future__ import annotations

import sqlite3
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest

from grid.interfaces.config import DashboardConfig, set_config
from grid.interfaces.metrics_collector import BridgeMetrics, SensoryMetrics
from tools.interfaces_dashboard.collector import DashboardCollector


@pytest.fixture
def db_path(tmp_path):
    """Provide a temporary SQLite database path for tests."""
    return str(tmp_path / "test_interfaces.db")


def create_test_metrics() -> tuple[list[BridgeMetrics], list[SensoryMetrics]]:
    """Create test metrics for integration testing.

    Returns:
        Tuple of (bridge_metrics, sensory_metrics)
    """
    base_time = datetime.now(UTC)

    bridge_metrics = []
    for i in range(10):
        bridge_metrics.append(
            BridgeMetrics(
                timestamp=base_time - timedelta(minutes=i),
                trace_id=f"bridge_test_{i}",
                transfer_latency_ms=10.0 + i * 0.5,
                compressed_size=100 + i * 10,
                raw_size=200 + i * 20,
                coherence_level=0.7 + i * 0.02,
                entanglement_count=i,
                integrity_check=f"hash_{i}",
                success=i % 9 != 0,  # One failure
                source_module="test.module",
                metadata={"test": True, "index": i},
            )
        )

    sensory_metrics = []
    modalities = ["text", "visual", "audio", "structured"]
    for i in range(15):
        sensory_metrics.append(
            SensoryMetrics(
                timestamp=base_time - timedelta(minutes=i),
                trace_id=f"sensory_test_{i}",
                modality=modalities[i % len(modalities)],
                duration_ms=5.0 + i * 0.3,
                coherence=0.8 + i * 0.01,
                raw_size=150 + i * 15,
                source="test.source",
                success=i % 14 != 0,  # One failure
                error_message="Test error" if i % 14 == 0 else None,
                metadata={"test": True, "index": i},
            )
        )

    return bridge_metrics, sensory_metrics


def _run_sqlite_schema(db_path: str) -> bool:
    """Test SQLite schema creation.

    Args:
        db_path: Path to SQLite database

    Returns:
        True if schema is valid
    """
    print(f"Testing SQLite schema at {db_path}...")

    # Remove existing database if it exists
    db_file = Path(db_path)
    if db_file.exists():
        db_file.unlink()

    try:
        # Initialize database using writer
        from tools.collect_interfaces_metrics import MetricsWriter

        config = DashboardConfig(prototype_mode=True, prototype_db_path=db_path)
        writer = MetricsWriter(config)

        # Create connection and check tables
        conn = writer._init_sqlite_db(db_path)

        # Check if tables exist
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'interfaces_%'")
        tables = [row[0] for row in cursor.fetchall()]

        expected_tables = [
            "interfaces_bridge_metrics",
            "interfaces_sensory_metrics",
            "interfaces_metrics_summary",
        ]

        missing_tables = set(expected_tables) - set(tables)
        if missing_tables:
            print(f"ERROR: Missing tables: {missing_tables}")
            return False

        print(f"[OK] Schema created successfully with tables: {tables}")
        conn.close()
        return True

    except Exception as e:
        print(f"ERROR: Schema test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def _run_metrics_insertion(db_path: str) -> bool:
    """Test metrics insertion into SQLite.

    Args:
        db_path: Path to SQLite database

    Returns:
        True if insertion is successful
    """
    print(f"Testing metrics insertion into {db_path}...")

    try:
        from tools.collect_interfaces_metrics import MetricsWriter

        config = DashboardConfig(prototype_mode=True, prototype_db_path=db_path)
        writer = MetricsWriter(config)

        # Create test metrics
        bridge_metrics, sensory_metrics = create_test_metrics()

        # Insert metrics
        conn = writer._init_sqlite_db(db_path)
        bridge_inserted = writer._insert_bridge_metrics_sqlite(conn, bridge_metrics)
        sensory_inserted = writer._insert_sensory_metrics_sqlite(conn, sensory_metrics)
        conn.close()

        print(f"[OK] Inserted {bridge_inserted} bridge metrics and {sensory_inserted} sensory metrics")

        # Verify insertion
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        cursor = conn.execute("SELECT COUNT(*) FROM interfaces_bridge_metrics")
        bridge_count = cursor.fetchone()[0]

        cursor = conn.execute("SELECT COUNT(*) FROM interfaces_sensory_metrics")
        sensory_count = cursor.fetchone()[0]

        conn.close()

        if bridge_count != bridge_inserted or sensory_count != sensory_inserted:
            print(
                f"ERROR: Count mismatch - bridge: {bridge_count} != {bridge_inserted}, sensory: {sensory_count} != {sensory_inserted}"
            )
            return False

        print(f"[OK] Verified {bridge_count} bridge and {sensory_count} sensory metrics in database")
        return True

    except Exception as e:
        print(f"ERROR: Insertion test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def _run_dashboard_collector(db_path: str) -> bool:
    """Test dashboard collector queries.

    Args:
        db_path: Path to SQLite database

    Returns:
        True if queries work correctly
    """
    print(f"Testing dashboard collector with {db_path}...")

    try:
        config = DashboardConfig(prototype_mode=True, prototype_db_path=db_path)
        collector = DashboardCollector(config)

        # Test various queries
        bridge_metrics = collector.get_recent_bridge_metrics(hours=24)
        print(f"[OK] Retrieved {len(bridge_metrics)} bridge metrics")

        sensory_metrics = collector.get_recent_sensory_metrics(hours=24)
        print(f"[OK] Retrieved {len(sensory_metrics)} sensory metrics")

        bridge_percentiles = collector.get_latency_percentiles(hours=24, interface_type="bridge")
        print(f"[OK] Bridge latency percentiles: {bridge_percentiles}")

        sensory_percentiles = collector.get_latency_percentiles(hours=24, interface_type="sensory")
        print(f"[OK] Sensory latency percentiles: {sensory_percentiles}")

        modality_dist = collector.get_modality_distribution(hours=24)
        print(f"[OK] Modality distribution: {len(modality_dist)} modalities")

        summary_stats = collector.get_summary_stats(hours=24)
        print(f"[OK] Summary stats: {len(summary_stats)} interface types")

        all_metrics = collector.get_all_metrics(hours=24)
        print(f"[OK] Retrieved all metrics (keys: {list(all_metrics.keys())})")

        collector.close()
        return True

    except Exception as e:
        print(f"ERROR: Collector test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_sqlite_schema(db_path: str) -> None:
    """Pytest wrapper for schema validation."""
    assert _run_sqlite_schema(db_path)


def test_metrics_insertion(db_path: str) -> None:
    """Pytest wrapper for insertion validation."""
    assert _run_metrics_insertion(db_path)


def test_dashboard_collector(db_path: str) -> None:
    """Pytest wrapper for collector validation."""
    assert _run_metrics_insertion(db_path)
    assert _run_dashboard_collector(db_path)


def main() -> int:
    """Run integration tests.

    Returns:
        Exit code (0 for success)
    """
    print("=" * 70)
    print("Interfaces Metrics Integration Test")
    print("=" * 70)
    print()

    test_db_path = "data/test_interfaces_metrics.db"

    # Configure for prototype mode
    config = DashboardConfig(prototype_mode=True, prototype_db_path=test_db_path)
    set_config(config)

    tests = [
        ("SQLite Schema", lambda: _run_sqlite_schema(test_db_path)),
        ("Metrics Insertion", lambda: _run_metrics_insertion(test_db_path)),
        ("Dashboard Collector", lambda: _run_dashboard_collector(test_db_path)),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n[TEST] {test_name}")
        print("-" * 70)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"ERROR: Test '{test_name}' raised exception: {e}")
            import traceback

            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print()
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)

    all_passed = True
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        symbol = "[OK]" if result else "[FAIL]"
        print(f"{test_name}: {symbol} {status}")
        if not result:
            all_passed = False

    print()
    if all_passed:
        print("All tests PASSED!")
        return 0
    else:
        print("Some tests FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
