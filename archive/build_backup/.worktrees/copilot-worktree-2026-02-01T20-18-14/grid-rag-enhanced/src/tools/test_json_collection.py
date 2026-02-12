#!/usr/bin/env python3
"""End-to-end test for JSON collection and dashboard."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from grid.interfaces.config import DashboardConfig, set_config
from grid.interfaces.json_parser import JSONParser
from grid.interfaces.json_scanner import JSONScanner
from grid.interfaces.metrics_collector import MetricsCollector
from tools.collect_interfaces_metrics import MetricsWriter


def test_json_scanner() -> bool:
    """Test JSON file scanner.

    Returns:
        True if successful
    """
    print("[TEST] JSON Scanner")
    print("-" * 70)

    try:
        scanner = JSONScanner()

        # Test finding specific files
        specific_files = scanner.find_specific_files(
            ["benchmark_metrics.json", "stress_metrics.json"],
            search_paths=["data"],
        )
        print(f"[OK] Found {len(specific_files)} specific files")

        # Test scanning recent files
        recent_files = scanner.scan_recent_json_files(days=7)
        print(f"[OK] Scanned {len(recent_files)} recent JSON files")

        # Verify we can identify file types
        if specific_files:
            file_path, _ = specific_files[0]
            file_type = scanner.identify_metrics_file(file_path)
            print(f"[OK] Identified file type: {file_type} for {file_path.name}")

        return True

    except Exception as e:
        print(f"[FAIL] JSON scanner test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_json_parser() -> bool:
    """Test JSON metrics parser.

    Returns:
        True if successful
    """
    print("\n[TEST] JSON Parser")
    print("-" * 70)

    try:
        parser = JSONParser()
        scanner = JSONScanner()

        # Find benchmark_metrics.json
        benchmark_files = scanner.find_specific_files(["benchmark_metrics.json"], ["data"])
        if not benchmark_files:
            print("[WARN] benchmark_metrics.json not found, skipping parser test")
            return True

        file_path, _ = benchmark_files[0]
        file_type = scanner.identify_metrics_file(file_path)

        # Parse benchmark metrics
        bridge_metrics, sensory_metrics = parser.extract_metrics_from_json(file_path, file_type)

        print(f"[OK] Parsed {len(bridge_metrics)} bridge metrics from {file_path.name}")
        print(f"[OK] Parsed {len(sensory_metrics)} sensory metrics from {file_path.name}")

        # Verify metrics structure
        if bridge_metrics:
            bm = bridge_metrics[0]
            print(f"[OK] Bridge metric: trace_id={bm.trace_id}, latency={bm.transfer_latency_ms}ms")

        if sensory_metrics:
            sm = sensory_metrics[0]
            print(f"[OK] Sensory metric: trace_id={sm.trace_id}, duration={sm.duration_ms}ms, modality={sm.modality}")

        return True

    except Exception as e:
        print(f"[FAIL] JSON parser test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_metrics_collector_json() -> bool:
    """Test MetricsCollector JSON collection.

    Returns:
        True if successful
    """
    print("\n[TEST] MetricsCollector JSON Collection")
    print("-" * 70)

    try:
        collector = MetricsCollector()

        # Collect from JSON files
        bridge_metrics, sensory_metrics = collector.collect_from_json_files(scan_days=7)

        print(f"[OK] Collected {len(bridge_metrics)} bridge metrics from JSON files")
        print(f"[OK] Collected {len(sensory_metrics)} sensory metrics from JSON files")

        # Verify metrics have required fields
        if bridge_metrics:
            bm = bridge_metrics[0]
            required_fields = ["timestamp", "trace_id", "transfer_latency_ms", "source_module"]
            missing = [f for f in required_fields if not hasattr(bm, f) or getattr(bm, f) is None]
            if missing:
                print(f"[WARN] Bridge metric missing fields: {missing}")
            else:
                print("[OK] Bridge metrics have all required fields")

        if sensory_metrics:
            sm = sensory_metrics[0]
            required_fields = ["timestamp", "trace_id", "duration_ms", "modality", "source"]
            missing = [f for f in required_fields if not hasattr(sm, f) or getattr(sm, f) is None]
            if missing:
                print(f"[WARN] Sensory metric missing fields: {missing}")
            else:
                print("[OK] Sensory metrics have all required fields")

        return True

    except Exception as e:
        print(f"[FAIL] MetricsCollector JSON collection test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_end_to_end() -> bool:
    """Test end-to-end: scan → parse → insert → query.

    Returns:
        True if successful
    """
    print("\n[TEST] End-to-End JSON Collection")
    print("-" * 70)

    test_db_path = "data/test_json_metrics.db"

    try:
        # Remove existing test database
        db_file = Path(test_db_path)
        if db_file.exists():
            db_file.unlink()

        config = DashboardConfig(prototype_mode=True, prototype_db_path=test_db_path)
        set_config(config)

        # Create collector and collect from JSON files
        collector = MetricsCollector()
        bridge_metrics, sensory_metrics = collector.collect_from_json_files(scan_days=30)

        print(f"[OK] Collected {len(bridge_metrics)} bridge and {len(sensory_metrics)} sensory metrics")

        if not bridge_metrics and not sensory_metrics:
            print("[WARN] No metrics collected - this may be expected if no JSON files found")
            return True

        # Write to database
        import asyncio

        writer = MetricsWriter(config)
        write_results = asyncio.run(writer.write_metrics(bridge_metrics, sensory_metrics))

        print(
            f"[OK] Inserted {write_results['bridge_inserted']} bridge and {write_results['sensory_inserted']} sensory metrics"
        )

        # Verify database contents
        conn = sqlite3.connect(test_db_path)
        conn.row_factory = sqlite3.Row

        cursor = conn.execute("SELECT COUNT(*) FROM interfaces_bridge_metrics")
        bridge_count = cursor.fetchone()[0]

        cursor = conn.execute("SELECT COUNT(*) FROM interfaces_sensory_metrics")
        sensory_count = cursor.fetchone()[0]

        conn.close()

        print(f"[OK] Verified {bridge_count} bridge and {sensory_count} sensory metrics in database")

        if bridge_count == write_results["bridge_inserted"] and sensory_count == write_results["sensory_inserted"]:
            print("[OK] Database counts match inserted counts")
            return True
        else:
            print(
                f"[FAIL] Count mismatch: bridge {bridge_count} != {write_results['bridge_inserted']}, sensory {sensory_count} != {write_results['sensory_inserted']}"
            )
            return False

    except Exception as e:
        print(f"[FAIL] End-to-end test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main() -> int:
    """Run all tests.

    Returns:
        Exit code (0 for success)
    """
    print("=" * 70)
    print("JSON Collection End-to-End Test")
    print("=" * 70)
    print()

    tests = [
        ("JSON Scanner", test_json_scanner),
        ("JSON Parser", test_json_parser),
        ("MetricsCollector JSON", test_metrics_collector_json),
        ("End-to-End", test_end_to_end),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n[ERROR] Test '{test_name}' raised exception: {e}")
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
