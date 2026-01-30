"""
Velocity Anomaly Detector - Detecting Momentum Manipulation.

Detects non-monotonic timestamps, artificial jitter, and momentum spikes
in cognitive velocity vectors.

DevOp Analogy: Like a "flapping" check in nagios or a "timestamp drift"
detection in a distributed database.
"""

import logging

logger = logging.getLogger(__name__)


class VelocityAnomalyDetector:
    """
    Detects anomalies in velocity-tracking timestamp sequences.
    """

    def __init__(self):
        self._anomaly_count = 0

    def validate_timestamp_integrity(self, timestamps: list[float]) -> bool:
        """
        Check if a sequence of timestamps is monotonic and free of
        artificial manipulation.
        """
        if len(timestamps) < 2:
            return True

        is_valid = True

        # Check monotonicity
        for i in range(1, len(timestamps)):
            if timestamps[i] < timestamps[i - 1]:
                # Non-monotonic! Likely manual insertion or clock manipulation.
                is_valid = False
                break

        # Check for "Ultra-Burst" (too close for human or natural system behavior)
        if len(timestamps) >= 5:
            duration = timestamps[-1] - timestamps[-5]
            if duration < 0.01:  # 5 events in 10ms is highly suspicious
                is_valid = False

        if not is_valid:
            self._anomaly_count += 1
            logger.debug(f"[SECURITY] Velocity anomaly detected (non-monotonic or burst). Count: {self._anomaly_count}")
            return False

        return True


# Singleton
_detector: VelocityAnomalyDetector | None = None


def get_velocity_anomaly_detector() -> VelocityAnomalyDetector:
    global _detector
    if _detector is None:
        _detector = VelocityAnomalyDetector()
    return _detector
