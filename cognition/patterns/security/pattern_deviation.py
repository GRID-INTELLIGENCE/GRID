"""
Pattern Deviation Monitor - Detecting Semantic Drift.

Tracks the evolution of emergent patterns to detect "hijacking" or
"malicious drift" where a pattern's description or metadata
shifts toward an adversarial state.
"""

import logging
import time
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class PatternHistory:
    signal_id: str
    original_description: str
    last_fingerprint: str
    version_count: int = 1
    last_updated: float = field(default_factory=time.time)


class PatternDeviationMonitor:
    """
    Monitors pattern evolution for deviations from established baselines.
    """

    def __init__(self):
        self._histories: dict[str, PatternHistory] = {}
        self._drift_count = 0

    def track_creation(self, fingerprint: str, signal_id: str, description: str, session_id: str | None = None):
        """Track the creation of a new pattern."""
        if signal_id not in self._histories:
            self._histories[signal_id] = PatternHistory(
                signal_id=signal_id, original_description=description, last_fingerprint=fingerprint
            )
        else:
            # Check for drift relative to original
            history = self._histories[signal_id]
            if history.original_description != description:
                self._drift_count += 1
                logger.debug(f"[SECURITY] Pattern drift detected for {signal_id}. Version: {history.version_count}")
                history.version_count += 1
                history.last_updated = time.time()
                history.last_fingerprint = fingerprint

    def get_stats(self):
        return {"patterns_tracked": len(self._histories), "total_drift_events": self._drift_count}


# Singleton
_monitor: PatternDeviationMonitor | None = None


def get_pattern_deviation_monitor() -> PatternDeviationMonitor:
    global _monitor
    if _monitor is None:
        _monitor = PatternDeviationMonitor()
    return _monitor
