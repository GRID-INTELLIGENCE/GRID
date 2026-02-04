"""
Shift Dashboard - Real-time momentum tracker.

Run this during your shift to watch progress in real-time.

Usage:
    python -m grid.progress.dashboard

    Or import in your test/fix scripts:
    from grid.progress.dashboard import ShiftDashboard

    dashboard = ShiftDashboard()
    dashboard.log_milestone("Fixed syntax error in simple.py")
    dashboard.print_status()
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from grid.progress.motivator import MotivationEngine


class ShiftDashboard:
    """Real-time dashboard for tracking shift progress."""

    def __init__(self, project_root: Path | None = None):
        """Initialize dashboard."""
        self.project_root = project_root or Path(__file__).parent.parent.parent.parent
        self.engine = MotivationEngine(self.project_root)
        self.milestones: list[dict[str, Any]] = []
        self._load_milestones()

    def _load_milestones(self) -> None:
        """Load existing milestones from history."""
        history_file = self.project_root / "progress_history.json"
        if history_file.exists():
            with open(history_file) as f:
                try:
                    data = json.load(f)
                    if isinstance(data, list) and data:
                        self.milestones = data
                except (json.JSONDecodeError, ValueError):
                    pass

    def log_milestone(self, description: str) -> None:
        """Log a milestone during the shift."""
        milestone = {
            "timestamp": datetime.now().isoformat(),
            "description": description,
            "metrics": self.engine.measure_current_state().to_dict(),
        }
        self.milestones.append(milestone)
        self._save_milestones()

    def _save_milestones(self) -> None:
        """Save milestones to file."""
        history_file = self.project_root / "progress_history.json"
        with open(history_file, "w") as f:
            json.dump(self.milestones, f, indent=2)

    def print_status(self) -> None:
        """Print current dashboard status."""
        metrics = self.engine.measure_current_state()

        print("\n" + "=" * 80)
        print("📊 SHIFT DASHBOARD")
        print("=" * 80)

        # Timeline
        print(f"\n⏱️  Started: {self.milestones[0]['timestamp'] if self.milestones else 'Now'}")
        print(f"   Time elapsed: {self._calculate_elapsed()}")
        print(f"   Milestones completed: {len(self.milestones)}")

        # Current metrics
        current_gear = self.engine.current_gear(metrics.rpm)
        print(f"\n🎯 CURRENT STATUS: {current_gear} GEAR ({metrics.rpm} RPM)")
        print(
            f"\n   Test Pass Rate:     {metrics.test_passing:3d}/{metrics.test_count:3d} ({metrics.test_pass_rate:5.1f}%) ",
            end="",
        )
        self._print_bar(metrics.test_pass_rate)
        print(f"   Type Coverage:      {metrics.type_coverage:5.1f}% ", end="")
        self._print_bar(metrics.type_coverage)

        # Error status
        print("\n   🚨 Blockers:")
        print(f"      Syntax Errors: {metrics.syntax_errors:3d} {'✅' if metrics.syntax_errors == 0 else '❌'}")
        print(f"      Import Errors: {metrics.import_errors:3d} {'✅' if metrics.import_errors == 0 else '❌'}")
        print(f"      MyPy Errors:   {metrics.mypy_errors:3d} {'✅' if metrics.mypy_errors == 0 else '⚠️'}")
        print(f"      Ruff Issues:   {metrics.ruff_issues:3d} {'✅' if metrics.ruff_issues == 0 else '⚠️'}")

        # Recent milestones
        if self.milestones:
            print("\n✅ Recent Milestones:")
            for m in self.milestones[-3:]:
                time = m.get("timestamp", "").split("T")[1][:5] if "timestamp" in m else "?"
                desc = m.get("description", "Progress check")
                print(f"   [{time}] {desc}")

        # Shift estimate
        print("\n📈 Gear Progression:")
        rpm_needed = self.engine.GEARS["3rd"]["rpm_min"]
        print(f"   3rd Gear (Shift): {metrics.rpm}/{rpm_needed} RPM ({int(metrics.rpm / rpm_needed * 100)}%)")

        print("\n" + "=" * 80 + "\n")

    def _calculate_elapsed(self) -> str:
        """Calculate elapsed time since first milestone."""
        if not self.milestones:
            return "Just started"

        start = datetime.fromisoformat(self.milestones[0]["timestamp"])
        elapsed = datetime.now() - start

        hours = elapsed.seconds // 3600
        minutes = (elapsed.seconds % 3600) // 60

        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    def _print_bar(self, percentage: float):
        """Print a progress bar."""
        bar_length = 30
        filled = int(bar_length * percentage / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"[{bar}]")


def print_dashboard():
    """Print dashboard to console."""
    dashboard = ShiftDashboard()
    dashboard.print_status()


if __name__ == "__main__":
    print_dashboard()
