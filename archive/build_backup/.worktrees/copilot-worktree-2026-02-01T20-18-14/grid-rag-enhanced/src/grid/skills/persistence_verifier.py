"""Persistence verifier for data integrity checks.

Features:
- Execution record integrity
- Intelligence record integrity
- Baseline consistency
- Schema version verification
- Foreign key validation
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PersistenceCheck:
    """Result of a persistence integrity check."""

    check_name: str
    passed: bool
    details: str
    records_checked: int = 0
    records_failed: int = 0


class PersistenceVerifier:
    """Verifies data integrity across all persistence layers."""

    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def run_all_checks(self) -> dict[str, PersistenceCheck]:
        """Run comprehensive persistence verification."""
        checks = {}

        checks["execution_integrity"] = self._check_execution_integrity()
        checks["intelligence_integrity"] = self._check_intelligence_integrity()
        checks["baseline_consistency"] = self._check_baseline_consistency()
        checks["schema_version"] = self._check_schema_version()
        checks["foreign_keys"] = self._check_foreign_keys()
        checks["data_freshness"] = self._check_data_freshness()

        return checks

    def _check_execution_integrity(self) -> PersistenceCheck:
        """Verify execution records have valid required fields."""
        try:
            from .intelligence_inventory import IntelligenceInventory

            inv = IntelligenceInventory.get_instance()
            conn = inv._get_connection()

            total = conn.execute("SELECT COUNT(*) FROM execution_records").fetchone()[0]

            null_count = conn.execute(
                """
                SELECT COUNT(*) FROM execution_records
                WHERE skill_id IS NULL OR timestamp IS NULL
                OR status IS NULL OR execution_time_ms IS NULL
            """
            ).fetchone()[0]

            if null_count > 0:
                return PersistenceCheck(
                    check_name="execution_integrity",
                    passed=False,
                    details=f"Found {null_count} records with null required fields",
                    records_checked=total,
                    records_failed=null_count,
                )

            return PersistenceCheck(
                check_name="execution_integrity",
                passed=True,
                details=f"All {total} execution records valid",
                records_checked=total,
            )
        except Exception as e:
            return PersistenceCheck(check_name="execution_integrity", passed=False, details=f"Check failed: {e}")

    def _check_intelligence_integrity(self) -> PersistenceCheck:
        """Verify intelligence records have valid required fields."""
        try:
            from .intelligence_inventory import IntelligenceInventory

            inv = IntelligenceInventory.get_instance()
            conn = inv._get_connection()

            total = conn.execute("SELECT COUNT(*) FROM intelligence_records").fetchone()[0]

            null_count = conn.execute(
                """
                SELECT COUNT(*) FROM intelligence_records
                WHERE skill_id IS NULL OR decision_type IS NULL
                OR confidence IS NULL OR timestamp IS NULL
            """
            ).fetchone()[0]

            if null_count > 0:
                return PersistenceCheck(
                    check_name="intelligence_integrity",
                    passed=False,
                    details=f"Found {null_count} records with null fields",
                    records_checked=total,
                    records_failed=null_count,
                )

            return PersistenceCheck(
                check_name="intelligence_integrity",
                passed=True,
                details=f"All {total} intelligence records valid",
                records_checked=total,
            )
        except Exception as e:
            return PersistenceCheck(check_name="intelligence_integrity", passed=False, details=f"Check failed: {e}")

    def _check_baseline_consistency(self) -> PersistenceCheck:
        """Verify baselines have valid metrics."""
        try:
            from .intelligence_inventory import IntelligenceInventory

            inv = IntelligenceInventory.get_instance()
            conn = inv._get_connection()

            total = conn.execute("SELECT COUNT(*) FROM performance_baselines").fetchone()[0]

            # Check for invalid (negative/zero) latencies - allow NULL for optional fields
            invalid = conn.execute(
                """
                SELECT COUNT(*) FROM performance_baselines
                WHERE (p50_ms IS NOT NULL AND p50_ms <= 0)
            """
            ).fetchone()[0]

            if invalid > 0:
                return PersistenceCheck(
                    check_name="baseline_consistency",
                    passed=False,
                    details=f"Found {invalid} baselines with invalid metrics",
                    records_checked=total,
                    records_failed=invalid,
                )

            return PersistenceCheck(
                check_name="baseline_consistency",
                passed=True,
                details=f"All {total} baselines valid",
                records_checked=total,
            )
        except Exception as e:
            return PersistenceCheck(check_name="baseline_consistency", passed=False, details=f"Check failed: {e}")

    def _check_schema_version(self) -> PersistenceCheck:
        """Verify database schema version."""
        try:
            from .intelligence_inventory import IntelligenceInventory

            inv = IntelligenceInventory.get_instance()
            conn = inv._get_connection()

            version = conn.execute("PRAGMA user_version").fetchone()[0]

            if version >= 2:
                return PersistenceCheck(
                    check_name="schema_version",
                    passed=True,
                    details=f"Schema version {version} is current",
                    records_checked=1,
                )
            else:
                return PersistenceCheck(
                    check_name="schema_version",
                    passed=False,
                    details=f"Schema version {version} is outdated (expected 2)",
                    records_checked=1,
                    records_failed=1,
                )
        except Exception as e:
            return PersistenceCheck(check_name="schema_version", passed=False, details=f"Check failed: {e}")

    def _check_foreign_keys(self) -> PersistenceCheck:
        """Verify foreign key references are valid."""
        try:
            from .intelligence_inventory import IntelligenceInventory

            inv = IntelligenceInventory.get_instance()
            conn = inv._get_connection()

            # Orphaned execution records
            orphaned_exec = conn.execute(
                """
                SELECT COUNT(*) FROM execution_records e
                WHERE NOT EXISTS (SELECT 1 FROM skill_metadata s WHERE s.skill_id = e.skill_id)
            """
            ).fetchone()[0]

            # Orphaned intelligence records
            orphaned_intel = conn.execute(
                """
                SELECT COUNT(*) FROM intelligence_records i
                WHERE NOT EXISTS (SELECT 1 FROM skill_metadata s WHERE s.skill_id = i.skill_id)
            """
            ).fetchone()[0]

            total_orphaned = orphaned_exec + orphaned_intel

            if total_orphaned > 0:
                return PersistenceCheck(
                    check_name="foreign_keys",
                    passed=False,
                    details=f"Found {total_orphaned} orphaned records",
                    records_checked=total_orphaned,
                    records_failed=total_orphaned,
                )

            return PersistenceCheck(check_name="foreign_keys", passed=True, details="All foreign key references valid")
        except Exception as e:
            return PersistenceCheck(check_name="foreign_keys", passed=False, details=f"Check failed: {e}")

    def _check_data_freshness(self) -> PersistenceCheck:
        """Verify data has been recently updated."""
        try:
            from .intelligence_inventory import IntelligenceInventory

            inv = IntelligenceInventory.get_instance()
            conn = inv._get_connection()

            latest_exec = conn.execute("SELECT MAX(timestamp) FROM execution_records").fetchone()[0] or 0

            latest_intel = conn.execute("SELECT MAX(timestamp) FROM intelligence_records").fetchone()[0] or 0

            now = time.time()
            latest = max(latest_exec, latest_intel)
            age_seconds = int(now - latest) if latest else -1

            if latest == 0:
                return PersistenceCheck(check_name="data_freshness", passed=True, details="No data recorded yet")
            elif age_seconds < 3600:  # Less than 1 hour
                return PersistenceCheck(
                    check_name="data_freshness",
                    passed=True,
                    details=f"Data is fresh ({age_seconds}s ago)",
                    records_checked=1,
                )
            else:
                return PersistenceCheck(
                    check_name="data_freshness",
                    passed=True,  # Informational, not failure
                    details=f"Data is stale ({age_seconds // 3600}h ago)",
                    records_checked=1,
                )
        except Exception as e:
            return PersistenceCheck(check_name="data_freshness", passed=False, details=f"Check failed: {e}")

    def print_report(self, checks: dict[str, PersistenceCheck]) -> None:
        """Print formatted verification report."""
        print("\n" + "=" * 60)
        print("PERSISTENCE INTEGRITY VERIFICATION")
        print("=" * 60 + "\n")

        passed = 0
        failed = 0

        for name, check in checks.items():
            icon = "✅" if check.passed else "❌"
            print(f"{icon} {name}")
            print(f"   {check.details}")

            if check.passed:
                passed += 1
            else:
                failed += 1

        print("\n" + "-" * 60)
        print(f"Total: {len(checks)} checks | {passed} passed | {failed} failed")
        print("=" * 60 + "\n")

        return failed == 0
