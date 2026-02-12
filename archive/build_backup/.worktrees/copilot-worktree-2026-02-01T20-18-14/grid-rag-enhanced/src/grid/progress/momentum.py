"""
Quick motivational check - designed to be called frequently during shifts.

Example usage:
    from grid.progress import check_momentum

    momentum = check_momentum()
    print(f"Current RPM: {momentum.rpm}")
    print(f"Tests: {momentum.test_passing}/{momentum.test_count}")
"""

import sys
from pathlib import Path

try:
    from .motivator import GearMetrics, MotivationEngine
except ImportError:
    # Fallback for direct execution
    src_path = Path(__file__).parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    from grid.progress.motivator import GearMetrics, MotivationEngine


def check_momentum() -> GearMetrics:
    """
    Quick 3-second momentum check during your shift.

    Returns current metrics including:
    - RPM (Realistic Progress Momentum)
    - Test pass rate
    - Error counts
    - Progress toward next gear

    Call this every 30-60 minutes to track progress.

    Returns:
        GearMetrics: Current system state
    """
    engine = MotivationEngine()
    return engine.measure_current_state()


def get_momentum_report() -> str:
    """
    Get full motivational report as string.

    Perfect for logging to file or displaying in CI/CD.

    Returns:
        str: Formatted motivation report
    """
    engine = MotivationEngine()
    metrics = engine.measure_current_state()
    return engine.generate_report(metrics)


if __name__ == "__main__":
    metrics = check_momentum()
    print(f"\n✅ RPM: {metrics.rpm}")
    print(f"📈 Tests: {metrics.test_passing}/{metrics.test_count} ({metrics.test_pass_rate:.1f}%)")
    print(f"🔧 Current gear: {MotivationEngine().current_gear(metrics.rpm)}")
    print(f"🎯 Next milestone: {MotivationEngine().next_gear(metrics.rpm)} gear\n")
