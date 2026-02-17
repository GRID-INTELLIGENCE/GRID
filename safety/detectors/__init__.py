"""
Safety detectors package.

The primary pre-check API is ``quick_block`` from ``pre_check.py``.
The middleware uses ``SafetyRuleManager`` (via ``safety.rules.manager``)
which wraps GUARDIAN internally.
"""

from safety.detectors.pre_check import PreCheckResult, quick_block

__all__ = [
    "quick_block",
    "PreCheckResult",
]
