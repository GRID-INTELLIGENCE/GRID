"""
Motivator: Progress tracking and momentum building for GRID shifts.

This module provides real-time progress metrics and motivational milestones
to keep momentum during the shift from 2nd → 3rd → 4th gear.
"""

import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class GearMetrics:
    """Current state metrics for gear progress."""

    timestamp: str
    rpm: int  # Realistic Progress Momentum
    test_pass_rate: float  # 0-100%
    test_count: int
    test_passing: int
    test_failing: int
    import_errors: int
    syntax_errors: int
    mypy_errors: int
    ruff_issues: int
    type_coverage: float  # 0-100%

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MotivationEngine:
    """Tracks progress and provides motivational milestones."""

    # Gear definitions (RPM thresholds)
    GEARS: dict[str, dict[str, Any]] = {
        "2nd": {"rpm_min": 0, "rpm_max": 2500, "status": "Stalled - Starting repairs"},
        "3rd": {"rpm_min": 2500, "rpm_max": 5000, "status": "Climbing - Building momentum"},
        "4th": {"rpm_min": 5000, "rpm_max": 8000, "status": "Flying - Production ready"},
        "5th": {"rpm_min": 8000, "rpm_max": 10000, "status": "Maximum - Enterprise scale"},
    }

    MILESTONES = {
        "2nd": [
            ("🔧 Diagnostic complete", "Test collection works"),
            ("⚡ Critical fixes applied", "Syntax errors resolved"),
            ("📦 Imports stabilized", "Top 3 paths clear"),
        ],
        "3rd": [
            ("✅ Test execution enabled", "Can run pytest"),
            ("🎯 50% tests passing", "Framework validates"),
            ("🧹 Code quality rising", "Type checking works"),
            ("📊 Benchmarks established", "Performance baseline set"),
        ],
        "4th": [
            ("🚀 90%+ tests passing", "Comprehensive coverage"),
            ("⚡ Sub-100ms latency", "Performance optimized"),
            ("🏗️ Multi-tenant ready", "Enterprise architecture"),
            ("📈 Observability complete", "Full monitoring suite"),
        ],
    }

    def __init__(self, project_root: Path | None = None):
        """Initialize the motivation engine."""
        self.project_root = project_root or Path(__file__).parent.parent.parent.parent

    def measure_current_state(self) -> GearMetrics:
        """Measure current project metrics."""

        # Test metrics
        test_passing, test_failing, test_count = self._count_tests()
        test_pass_rate = (test_passing / test_count * 100) if test_count > 0 else 0

        # Error metrics
        import_errors = self._count_errors("ImportError|ModuleNotFoundError")
        syntax_errors = self._count_errors("SyntaxError")

        # Code quality
        mypy_errors = self._count_mypy_errors()
        ruff_issues = self._count_ruff_issues()

        # Type coverage (estimated from error ratio)
        type_coverage = max(0, 100 - (mypy_errors * 2))

        # Calculate RPM
        rpm = self._calculate_rpm(test_pass_rate, import_errors, syntax_errors, mypy_errors, ruff_issues)

        return GearMetrics(
            timestamp=datetime.now().isoformat(),
            rpm=rpm,
            test_pass_rate=test_pass_rate,
            test_count=test_count,
            test_passing=test_passing,
            test_failing=test_failing,
            import_errors=import_errors,
            syntax_errors=syntax_errors,
            mypy_errors=mypy_errors,
            ruff_issues=ruff_issues,
            type_coverage=type_coverage,
        )

    def _count_tests(self) -> tuple[int, int, int]:
        """Count passing and failing tests."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=no"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60,
            )

            output = result.stdout + result.stderr

            # Parse pytest output
            passing = output.count(" passed")
            failing = output.count(" failed")
            errors = output.count(" error")

            total = passing + failing + errors

            return passing, failing + errors, total if total > 0 else 200  # Assume 200 tests exist

        except Exception:
            return 0, 200, 200

    def _count_errors(self, pattern: str) -> int:
        """Count specific error types in test output."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "--collect-only", "-q"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30,
            )

            output = result.stdout + result.stderr
            import re

            matches = re.findall(pattern, output)
            return len(matches)

        except Exception:
            return 0

    def _count_mypy_errors(self) -> int:
        """Count MyPy type checking errors."""
        try:
            result = subprocess.run(
                ["mypy", "src/", "--ignore-missing-imports"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30,
            )

            output = result.stdout
            # MyPy reports "X error in Y files" at the end
            import re

            matches = re.findall(r"(\d+) error", output)
            return int(matches[0]) if matches else 0

        except Exception:
            return 0

    def _count_ruff_issues(self) -> int:
        """Count Ruff linting issues."""
        try:
            result = subprocess.run(
                ["ruff", "check", "src/"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30,
            )

            output = result.stdout
            # Count lines (each issue is one line)
            return len([l for l in output.split("\n") if l.strip()])

        except Exception:
            return 0

    def _calculate_rpm(
        self,
        test_pass_rate: float,
        import_errors: int,
        syntax_errors: int,
        mypy_errors: int,
        ruff_issues: int,
    ) -> int:
        """Calculate Realistic Progress Momentum."""

        # Base score from test pass rate
        base_rpm = int(test_pass_rate * 50)  # 0-50 from tests

        # Subtract for errors
        error_penalty = min(
            2500,
            (import_errors * 10) + (syntax_errors * 25) + (mypy_errors * 2) + (ruff_issues * 1),
        )

        rpm = max(0, base_rpm - error_penalty)

        # Cap based on test pass rate
        if test_pass_rate < 5:
            rpm = min(rpm, 500)
        elif test_pass_rate < 25:
            rpm = min(rpm, 1500)
        elif test_pass_rate < 50:
            rpm = min(rpm, 3000)

        return rpm

    def current_gear(self, rpm: int) -> str:
        """Determine current gear based on RPM."""
        for gear, specs in self.GEARS.items():
            if specs["rpm_min"] <= rpm < specs["rpm_max"]:
                return gear
        return "5th"

    def next_gear(self, current_rpm: int) -> str:
        """Get next gear target."""
        gears_list = ["2nd", "3rd", "4th", "5th"]
        current = self.current_gear(current_rpm)

        try:
            idx = gears_list.index(current)
            return gears_list[idx + 1] if idx < len(gears_list) - 1 else "5th"
        except ValueError:
            return "5th"

    def generate_report(self, metrics: GearMetrics) -> str:
        """Generate motivational progress report."""

        current = self.current_gear(metrics.rpm)
        next_gear_target = self.next_gear(metrics.rpm)

        # Calculate progress toward next gear
        current_specs = self.GEARS[current]
        next_specs = self.GEARS[next_gear_target]

        progress_to_next = (
            (metrics.rpm - current_specs["rpm_min"]) / (next_specs["rpm_max"] - current_specs["rpm_min"]) * 100
        )
        progress_to_next = max(0, min(100, progress_to_next))

        # Build report
        report = []
        report.append("\n" + "=" * 70)
        report.append(f"🏁 GRID MOTIVATOR - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 70)

        # Current gear status
        report.append(f"\n🎯 CURRENT GEAR: {current}")
        report.append(f"   Status: {self.GEARS[current]['status']}")
        report.append(f"   RPM: {metrics.rpm} / {self.GEARS[current]['rpm_max']}")

        # Progress bar
        bar_length = 50
        filled = int(bar_length * progress_to_next / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        report.append(f"\n📊 PROGRESS TO {next_gear_target.upper()} GEAR:")
        report.append(f"   [{bar}] {progress_to_next:.1f}%")

        # Metrics snapshot
        report.append("\n📈 METRICS SNAPSHOT:")
        report.append(
            f"   ✅ Tests Passing:    {metrics.test_passing:3d}/{metrics.test_count:3d} ({metrics.test_pass_rate:5.1f}%)"
        )
        report.append(f"   ❌ Tests Failing:    {metrics.test_failing:3d}")
        report.append(f"   🚨 Import Errors:    {metrics.import_errors:3d}")
        report.append(f"   💥 Syntax Errors:    {metrics.syntax_errors:3d}")
        report.append(f"   ⚠️  MyPy Errors:      {metrics.mypy_errors:3d}")
        report.append(f"   🧹 Ruff Issues:      {metrics.ruff_issues:3d}")
        report.append(f"   🔒 Type Coverage:    {metrics.type_coverage:5.1f}%")

        # Milestones for current gear
        report.append(f"\n🎖️  MILESTONES - {current.upper()} GEAR:")
        for milestone, description in self.MILESTONES[current]:
            status = "✅" if "100%" in description or "complete" in description else "🔄"
            report.append(f"   {status} {milestone}")
            report.append(f"      → {description}")

        # Next gear teaser
        report.append(f"\n🚀 NEXT GEAR ({next_gear_target.upper()}) UNLOCKS:")
        for milestone, description in self.MILESTONES[next_gear_target][:2]:
            report.append(f"   🎯 {milestone}")
            report.append(f"      → {description}")

        # Actionable next steps
        report.append("\n💪 YOUR NEXT MOVE:")
        report.append(self._get_actionable_steps(metrics, current))

        # Motivational message
        report.append(f"\n{self._get_motivational_message(metrics.rpm, progress_to_next)}")

        report.append("\n" + "=" * 70 + "\n")

        return "\n".join(report)

    def _get_actionable_steps(self, metrics: GearMetrics, current: str) -> str:
        """Get actionable next steps based on current state."""

        steps = []

        if metrics.syntax_errors > 0:
            steps.append(f"   1️⃣  Fix {metrics.syntax_errors} syntax error(s) - BLOCKING!")
        if metrics.import_errors > 0:
            steps.append(f"   2️⃣  Resolve {metrics.import_errors} import error(s) - BLOCKING!")
        if metrics.test_pass_rate < 50:
            target = int(metrics.test_pass_rate) + 10
            steps.append(f"   3️⃣  Get {target}% of tests passing")
        if metrics.mypy_errors > 20:
            steps.append(f"   4️⃣  Reduce MyPy errors from {metrics.mypy_errors} → 10")
        if metrics.ruff_issues > 100:
            steps.append(f"   5️⃣  Clean Ruff issues: {metrics.ruff_issues} → 50")

        if not steps:
            return "   🎉 You're on track! Keep momentum going. Run this command again in 30 minutes."

        return "\n".join(steps[:3]) if len(steps) > 3 else "\n".join(steps)

    def _get_motivational_message(self, rpm: int, progress: float) -> str:
        """Get motivational message based on progress."""

        messages = {
            "critical_low": (
                "⚠️  STUCK IN THE MUD\n"
                "   Code isn't running yet. This is PHASE 0 - focus on unblocking.\n"
                "   You're 30 minutes away from 1000 RPM. Push through! 💪"
            ),
            "climbing": (
                "📈 CLIMBING THE HILL\n"
                "   You're making progress! Tests are starting to pass.\n"
                "   Keep fixing those imports - the road ahead is clearer. 🚗"
            ),
            "halfway": (
                "⚡ YOU'RE HALFWAY THERE\n"
                "   Amazing progress! You're at the shift point.\n"
                "   Time to engage 3rd gear and hit the accelerator. 🏎️"
            ),
            "accelerating": (
                "🚀 ACCELERATING!\n"
                "   3rd gear is ENGAGED. You're in the zone now.\n"
                "   4th gear is within sight. Don't lose momentum! 🔥"
            ),
            "flying": (
                "🛸 YOU'RE FLYING!\n"
                "   4th gear achieved! Production-ready code.\n"
                "   Keep pushing - there's always room to grow. 💫"
            ),
        }

        if rpm < 1000:
            return messages["critical_low"]
        elif rpm < 2500:
            return messages["climbing"]
        elif rpm < 3500 and progress < 50:
            return messages["halfway"]
        elif rpm < 5000:
            return messages["accelerating"]
        else:
            return messages["flying"]


async def motivate() -> GearMetrics:
    """
    Quick motivational check - call this frequently during the shift.

    Returns the current metrics so you can track progress.
    """
    engine = MotivationEngine()
    metrics = engine.measure_current_state()
    return metrics


def print_motivation() -> None:
    """Print motivational report to console."""
    engine = MotivationEngine()
    metrics = engine.measure_current_state()
    print(engine.generate_report(metrics))


def save_progress(metrics: GearMetrics, filepath: Path | None = None) -> None:
    """Save metrics to JSON for historical tracking."""
    if filepath is None:
        filepath = Path(__file__).parent.parent.parent.parent / "progress_history.json"

    history = []
    if filepath.exists():
        with open(filepath) as f:
            history = json.load(f)

    history.append(metrics.to_dict())

    # Keep last 100 records
    history = history[-100:]

    with open(filepath, "w") as f:
        json.dump(history, f, indent=2)

    return filepath


if __name__ == "__main__":
    print_motivation()
