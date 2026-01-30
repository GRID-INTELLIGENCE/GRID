"""
Reinforcement Monitor - Detecting Confidence Gaming.

Tracks reinforcement signatures to detect "burst" patterns (rapid reinforcement)
and other behavioral anomalies.

Psyop Analogy: Detects the "Echo Chamber" effect where a narrative is
artificially amplified by rapid, repetitive signaling.
"""

from __future__ import annotations

import logging
from collections import defaultdict, deque
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .cognitive_fingerprint import ReinforcementSignature

logger = logging.getLogger(__name__)


class ReinforcementMonitor:
    """
    Behind the Curtain: Monitors reinforcement patterns for anomalies.
    """

    def __init__(self):
        # Fingerprint -> Deque of timestamps
        self._burst_windows: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=50))
        # Fingerprint -> Violation counts
        self._violations: dict[str, int] = defaultdict(int)

        # Thresholds (Configurable)
        self._burst_threshold = 10  # 10 reinforcements
        self._time_window = 5.0  # within 5 seconds

    def track_reinforcement(self, signature: ReinforcementSignature) -> bool:
        """
        Track a reinforcement attempt and check for burst violations.

        Returns:
            True if the reinforcement is considered legitimate.
            False if it is flagged as a burst attack.
        """
        fp = signature.fingerprint
        now = signature.timestamp

        # Update burst window
        window = self._burst_windows[fp]
        window.append(now)

        # Cleanup old timestamps
        while window and now - window[0] > self._time_window:
            window.popleft()

        # Check for violation
        if len(window) >= self._burst_threshold:
            self._violations[fp] += 1
            logger.warning(
                f"[SECURITY] Burst reinforcement detected for fingerprint {fp[:8]}. "
                f"Count: {len(window)} in {self._time_window}s."
            )

            # Behind the Curtain: We don't error. We just return False
            # so the caller can apply "Negative Reinforcement".
            return False

        return True

    def get_violation_count(self, fingerprint: str) -> int:
        return self._violations.get(fingerprint, 0)


# Singleton
_monitor: ReinforcementMonitor | None = None


def get_reinforcement_monitor() -> ReinforcementMonitor:
    global _monitor
    if _monitor is None:
        _monitor = ReinforcementMonitor()
    return _monitor
