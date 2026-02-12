"""
Quick Motivation Function - Call this during your shift!

Usage:
    from grid.progress import check_momentum

    # Every 30 minutes during work:
    momentum = check_momentum()
    print(f"RPM: {momentum.rpm}, Tests: {momentum.test_passing}/{momentum.test_count}")
"""

import sys
from pathlib import Path

src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from grid.progress.motivator import MotivationEngine


def quick_check():
    """
    Ultra-simple momentum check - under 3 seconds.

    Shows:
    - Current RPM (0-10000)
    - Tests passing/total
    - Current gear
    - Time to next gear
    """
    engine = MotivationEngine()
    metrics = engine.measure_current_state()
    current = engine.current_gear(metrics.rpm)
    next_gear = engine.next_gear(metrics.rpm)

    print("\n" + "="*60)
    print("GRID MOMENTUM CHECK")
    print("="*60)
    print(f"\nCURRENT:  {current} Gear | {metrics.rpm:5d} RPM")
    print(f"TESTS:    {metrics.test_passing:3d}/{metrics.test_count:3d} passing ({metrics.test_pass_rate:5.1f}%)")
    print("\nERRORS:")
    print(f"  Syntax:   {metrics.syntax_errors:2d} {'BLOCKED' if metrics.syntax_errors > 0 else 'OK'}")
    print(f"  Imports:  {metrics.import_errors:2d} {'BLOCKED' if metrics.import_errors > 0 else 'OK'}")
    print(f"  MyPy:     {metrics.mypy_errors:2d}")
    print(f"  Ruff:     {metrics.ruff_issues:2d}")

    print(f"\nNEXT GEAR: {next_gear.upper()} ({engine.GEARS[next_gear]['rpm_min']} RPM)")

    # Progress bar
    current_specs = engine.GEARS[current]
    next_specs = engine.GEARS[next_gear]
    progress = ((metrics.rpm - current_specs["rpm_min"])
                / (next_specs["rpm_max"] - current_specs["rpm_min"]) * 100)
    progress = max(0, min(100, progress))

    bar = "=" * int(progress / 5) + "-" * (20 - int(progress / 5))
    print(f"\nPROGRESS: [{bar}] {progress:.0f}%")

    print("\n" + "="*60 + "\n")

    return metrics


if __name__ == "__main__":
    quick_check()
