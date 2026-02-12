"""Comprehensive diagnostics for GRID Skills system.

Features:
- Component health checks
- Performance metrics
- Error counting
- Recommendations engine
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class DiagnosticReport:
    """Complete diagnostic report for skills system."""

    timestamp: float
    component_statuses: dict[str, str] = field(default_factory=dict)
    performance_metrics: dict[str, float] = field(default_factory=dict)
    error_counts: dict[str, int] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)


class SkillsDiagnostics:
    """Comprehensive diagnostics for GRID Skills system."""

    def __init__(self, reports_dir: Path | None = None):
        self._logger = logging.getLogger(__name__)
        self._reports_dir = reports_dir or Path("./data/skills_diagnostics")
        self._reports_dir.mkdir(parents=True, exist_ok=True)

    def run_full_diagnostics(self) -> DiagnosticReport:
        """Run comprehensive diagnostic suite."""
        report = DiagnosticReport(
            timestamp=time.time(),
            component_statuses=self._check_components(),
            performance_metrics=self._measure_performance(),
            error_counts=self._count_errors(),
            recommendations=[],
        )

        # Generate recommendations based on findings
        report.recommendations = self._generate_recommendations(report)

        # Save report
        self._save_report(report)

        return report

    def _check_components(self) -> dict[str, str]:
        """Check status of all components."""
        statuses = {}

        # Check registry
        try:
            from .registry import default_registry

            count = default_registry.count()
            statuses["registry"] = f"healthy ({count} skills)"
        except Exception as e:
            statuses["registry"] = f"error: {e}"

        # Check execution tracker
        try:
            from .execution_tracker import SkillExecutionTracker

            tracker = SkillExecutionTracker.get_instance()
            pending = tracker.get_pending_count()
            statuses["execution_tracker"] = f"healthy ({pending} pending)"
        except Exception as e:
            statuses["execution_tracker"] = f"error: {e}"

        # Check intelligence tracker
        try:
            from .intelligence_tracker import IntelligenceTracker

            IntelligenceTracker.get_instance()
            statuses["intelligence_tracker"] = "healthy"
        except Exception as e:
            statuses["intelligence_tracker"] = f"error: {e}"

        # Check inventory
        try:
            from .intelligence_inventory import IntelligenceInventory

            inv = IntelligenceInventory.get_instance()
            skills = len(inv.get_all_skill_ids())
            statuses["inventory"] = f"healthy ({skills} skills)"
        except Exception as e:
            statuses["inventory"] = f"error: {e}"

        # Check performance guard
        try:
            from .performance_guard import PerformanceGuard

            PerformanceGuard.get_instance()
            statuses["performance_guard"] = "healthy"
        except Exception as e:
            statuses["performance_guard"] = f"error: {e}"

        return statuses

    def _measure_performance(self) -> dict[str, float]:
        """Measure key performance metrics."""
        metrics = {}

        # Inventory query latency
        try:
            from .intelligence_inventory import IntelligenceInventory

            inv = IntelligenceInventory.get_instance()

            start = time.perf_counter()
            for _ in range(10):
                inv.get_skill_summary("nonexistent_placeholder")
            latency_ms = (time.perf_counter() - start) * 100  # ms per query
            metrics["inventory_query_latency_ms"] = round(latency_ms, 2)
        except Exception:
            metrics["inventory_query_latency_ms"] = -1

        # Tracker overhead
        try:
            from .execution_tracker import SkillExecutionTracker

            tracker = SkillExecutionTracker.get_instance()

            start = time.perf_counter()
            for i in range(10):
                tracker.track_execution(
                    skill_id="_diagnostics_test", input_args={"i": i}, output={}, execution_time_ms=1
                )
            latency_ms = (time.perf_counter() - start) * 100
            metrics["tracking_overhead_ms"] = round(latency_ms, 2)
        except Exception:
            metrics["tracking_overhead_ms"] = -1

        return metrics

    def _count_errors(self) -> dict[str, int]:
        """Count recent errors in all components."""
        counts = {}

        try:
            from .execution_tracker import ExecutionStatus, SkillExecutionTracker

            tracker = SkillExecutionTracker.get_instance()
            history = tracker.get_execution_history(limit=1000)

            counts["total_executions"] = len(history)
            counts["failed_executions"] = sum(1 for r in history if r.status != ExecutionStatus.SUCCESS)
            counts["error_executions"] = sum(1 for r in history if r.error)
        except Exception:
            counts["execution_error"] = -1

        try:
            from .intelligence_inventory import IntelligenceInventory

            inv = IntelligenceInventory.get_instance()
            counts["registered_skills"] = len(inv.get_all_skill_ids())
        except Exception:
            counts["inventory_error"] = -1

        return counts

    def _generate_recommendations(self, report: DiagnosticReport) -> list[str]:
        """Generate recommendations based on diagnostics."""
        recs = []

        # Check component health
        for comp, status in report.component_statuses.items():
            if "error" in status.lower():
                recs.append(f"Fix {comp}: {status}")

        # Check performance
        if report.performance_metrics.get("inventory_query_latency_ms", 0) > 50:
            recs.append("High inventory latency. Consider query optimization.")
        if report.performance_metrics.get("tracking_overhead_ms", 0) > 10:
            recs.append("High tracking overhead. Consider batch size increase.")

        # Check error rates
        total = report.error_counts.get("total_executions", 0)
        failed = report.error_counts.get("failed_executions", 0)
        if total > 0 and (failed / total) > 0.1:
            recs.append(f"High failure rate ({failed/total:.1%}). Review errors.")

        return recs

    def _save_report(self, report: DiagnosticReport) -> Path:
        """Save diagnostic report to disk."""
        filename = f"diagnostic_{int(report.timestamp)}.json"
        path = self._reports_dir / filename

        with open(path, "w") as f:
            json.dump(asdict(report), f, indent=2)

        self._logger.info(f"Diagnostic report saved: {path}")
        return path

    def get_latest_report(self) -> DiagnosticReport | None:
        """Get the most recent diagnostic report."""
        reports = sorted(self._reports_dir.glob("diagnostic_*.json"))
        if not reports:
            return None

        with open(reports[-1]) as f:
            data = json.load(f)

        return DiagnosticReport(**data)

    def print_report(self, report: DiagnosticReport) -> None:
        """Print formatted diagnostic report."""
        print("\n" + "=" * 60)
        print("GRID SKILLS DIAGNOSTIC REPORT")
        print("=" * 60)
        print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(report.timestamp))}")

        print("\n" + "COMPONENT STATUS".center(60, "-"))
        for comp, status in report.component_statuses.items():
            icon = "✅" if "healthy" in status else "❌"
            print(f"  {icon} {comp}: {status}")

        print("\n" + "PERFORMANCE METRICS".center(60, "-"))
        for metric, value in report.performance_metrics.items():
            print(f"  {metric}: {value:.2f}" if value >= 0 else f"  {metric}: ERROR")

        print("\n" + "COUNTS".center(60, "-"))
        for key, count in report.error_counts.items():
            print(f"  {key}: {count}")

        print("\n" + "RECOMMENDATIONS".center(60, "-"))
        if report.recommendations:
            for rec in report.recommendations:
                print(f"  💡 {rec}")
        else:
            print("  No recommendations - system looks healthy!")

        print("\n" + "=" * 60)
