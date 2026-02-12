"""
GUARDIAN Pre-Check Integration Bridge

This module bridges the legacy pre_check.py to use the new GUARDIAN engine.
The original pre_check.py is preserved for backwards compatibility.

To migrate fully, replace imports of pre_check with pre_check_guardian.
"""

# Re-export the new GUARDIAN-based functions
from safety.detectors.pre_check_guardian import (
    evaluate_detailed,
    get_guardian_stats,
    quick_block,
    refresh_blocklist,
)

__all__ = [
    "quick_block",
    "evaluate_detailed",
    "get_guardian_stats",
    "refresh_blocklist",
]
