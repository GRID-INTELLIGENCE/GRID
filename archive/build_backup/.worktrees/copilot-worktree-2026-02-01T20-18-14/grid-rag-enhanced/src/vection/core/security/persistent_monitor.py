"""
Persistent Monitor - The "Behind the Curtain" Daemon.

Aggregates monitoring data across all security vectors and triggers
automated countermeasures when thresholds are crossed.
"""

from __future__ import annotations

import logging
from typing import Any

from cognition.patterns.security.pattern_deviation import get_pattern_deviation_monitor
from cognition.patterns.security.reinforcement_monitor import get_reinforcement_monitor
from cognition.patterns.security.velocity_anomaly import get_velocity_anomaly_detector

logger = logging.getLogger(__name__)


class PersistentMonitor:
    """
    Background aggregation and rule engine for cognitive security.
    """

    def __init__(self):
        self._is_running = False
        self._stats: dict[str, int] = {}
        self._events: list = []

    async def start(self):
        if self._is_running:
            return
        self._is_running = True
        logger.info("[Security] Persistent monitor daemon active behind the curtain")

    async def stop(self):
        self._is_running = False
        logger.info("[Security] Persistent monitor daemon stopped")

    def record_event(self, event_type: str, data: dict[str, Any]):
        """Record a generic security event for later correlation."""
        self._events.append({"type": event_type, "data": data, "timestamp": data.get("timestamp")})

        # Cap event history
        if len(self._events) > 1000:
            self._events = self._events[-500:]

    def record_debug_event(self, event_type: str, args: tuple):
        """Standardized entry point for 'harmless' looking debug signals."""
        # This is where we cross-reference debug signals with monitoring state
        pass

    def get_stats(self) -> dict[str, Any]:
        rm = get_reinforcement_monitor()
        pdm = get_pattern_deviation_monitor()
        vad = get_velocity_anomaly_detector()

        return {
            "is_running": self._is_running,
            "reinforcement_violations": len(rm._violations),
            "drift_events": pdm._drift_count,
            "velocity_anomalies": vad._anomaly_count,
            "total_captured_events": len(self._events),
        }


# Singleton
_monitor: PersistentMonitor | None = None


def get_persistent_monitor() -> PersistentMonitor:
    global _monitor
    if _monitor is None:
        _monitor = PersistentMonitor()
    return _monitor


async def start_monitoring_daemon():
    monitor = get_persistent_monitor()
    await monitor.start()
    return monitor


async def stop_monitoring_daemon():
    monitor = get_persistent_monitor()
    await monitor.stop()
