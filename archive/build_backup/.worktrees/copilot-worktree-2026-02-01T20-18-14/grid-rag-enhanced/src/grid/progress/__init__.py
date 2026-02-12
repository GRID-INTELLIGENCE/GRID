"""Progress tracking and motivation engine for GRID shifts.

Quick start:
    from grid.progress import quick_check
    quick_check()  # Shows RPM, tests, errors, progress

    from grid.progress import check_momentum
    momentum = check_momentum()  # Get metrics programmatically

During your shift, run:
    python src/grid/progress/quick.py  # Every 30 minutes
"""

from .momentum import (
    check_momentum,
    get_momentum_report,
)
from .motivator import (
    GearMetrics,
    MotivationEngine,
    motivate,
    print_motivation,
    save_progress,
)
from .quick import quick_check

__all__ = [
    "MotivationEngine",
    "GearMetrics",
    "motivate",
    "print_motivation",
    "save_progress",
    "check_momentum",
    "get_momentum_report",
    "quick_check",
]
