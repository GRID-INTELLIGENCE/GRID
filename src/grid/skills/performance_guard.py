"""Performance guard with regression detection and Prometheus metrics.

Features:
- Real-time regression detection after execution
- Configurable threshold (default 20% = 1.2x)
- Prometheus metrics export
- Alert deduplication window
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .intelligence_inventory import IntelligenceInventory

logger = logging.getLogger(__name__)

# Try to import Prometheus client
try:
    from prometheus_client import Counter, Gauge

    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False
    logger.debug("prometheus_client not available - metrics disabled")


@dataclass
class PerformanceAlert:
    """Performance regression alert."""

    skill_id: str
    severity: str  # "low", "medium", "high"
    metric: str
    baseline_value: float
    current_value: float
    degradation_pct: float
    timestamp: float


class SkillMetrics:
    """Prometheus metrics for skills monitoring."""

    _initialized = False

    @classmethod
    def initialize(cls):
        """Initialize Prometheus metrics."""
        if not HAS_PROMETHEUS or cls._initialized:
            return

        cls.EXECUTION_TIME = Gauge("grid_skill_execution_time_ms", "Skill execution time in milliseconds", ["skill_id"])
        cls.SUCCESS_RATE = Gauge("grid_skill_success_rate", "Skill success rate (0-1)", ["skill_id"])
        cls.REGRESSION_DETECTED = Gauge(
            "grid_skill_regression_detected", "Performance regression flag (1=regression)", ["skill_id", "severity"]
        )
        cls.TOTAL_EXECUTIONS = Counter("grid_skill_total_executions", "Total skill executions", ["skill_id", "status"])
        cls.CONFIDENCE_SCORE = Gauge("grid_skill_confidence_score", "Average confidence score", ["skill_id"])

        cls._initialized = True
        logger.info("Prometheus skill metrics initialized")


class PerformanceGuard:
    """Detects performance regressions and exports Prometheus metrics.

    Configuration:
    - GRID_SKILLS_REGRESSION_THRESHOLD: Degradation threshold (default: 1.2 = 20%)
    - GRID_SKILLS_ALERT_WINDOW: Dedupe window in seconds (default: 300 = 5 min)
    """

    _instance: PerformanceGuard | None = None

    REGRESSION_THRESHOLD = float(os.getenv("GRID_SKILLS_REGRESSION_THRESHOLD", "1.2"))
    ALERT_WINDOW = int(os.getenv("GRID_SKILLS_ALERT_WINDOW", "300"))

    def __init__(self):
        self._logger = logging.getLogger(__name__)

        # Lazy inventory connection
        self._inventory: IntelligenceInventory | None = None
        self._inventory_available = True

        # Alert deduplication
        self._recent_alerts: dict[str, float] = {}  # skill_id -> last_alert_time

        # Initialize Prometheus metrics
        SkillMetrics.initialize()

    @classmethod
    def get_instance(cls) -> PerformanceGuard:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _get_inventory(self) -> IntelligenceInventory | None:
        """Lazy load inventory connection."""
        if not self._inventory_available:
            return None

        if self._inventory is None:
            try:
                from .intelligence_inventory import IntelligenceInventory

                self._inventory = IntelligenceInventory.get_instance()
            except Exception as e:
                self._logger.warning(f"IntelligenceInventory unavailable: {e}")
                self._inventory_available = False
                return None

        return self._inventory

    def check_execution(
        self,
        skill_id: str,
        execution_time_ms: float,
        status: str = "success",
        confidence_score: float | None = None,
    ) -> PerformanceAlert | None:
        """Check if execution indicates performance regression.

        Args:
            skill_id: Skill identifier
            execution_time_ms: Execution time in milliseconds
            status: Execution status
            confidence_score: Optional confidence score

        Returns:
            PerformanceAlert if regression detected, None otherwise
        """
        # Update Prometheus metrics
        self._update_metrics(skill_id, execution_time_ms, status, confidence_score)

        # Check for regression
        inventory = self._get_inventory()
        if not inventory:
            return None

        current_metrics = {
            "p50_ms": execution_time_ms,
            "p95_ms": execution_time_ms,
            "p99_ms": execution_time_ms,
        }

        regression = inventory.check_regression(skill_id, current_metrics, self.REGRESSION_THRESHOLD)

        if not regression:
            return None

        # Find worst regression
        worst_metric = max(regression.keys(), key=lambda k: regression[k]["degradation_pct"])
        worst = regression[worst_metric]

        # Determine severity
        degradation = worst["degradation_pct"]
        if degradation >= 100:
            severity = "high"
        elif degradation >= 50:
            severity = "medium"
        else:
            severity = "low"

        # Check deduplication
        if self._is_deduplicated(skill_id):
            self._logger.debug(f"Alert deduplicated for {skill_id}")
            return None

        # Create alert
        alert = PerformanceAlert(
            skill_id=skill_id,
            severity=severity,
            metric=worst_metric,
            baseline_value=worst["baseline"],
            current_value=worst["current"],
            degradation_pct=degradation,
            timestamp=time.time(),
        )

        # Record alert and update metrics
        self._recent_alerts[skill_id] = time.time()
        self._report_regression(alert)

        self._logger.warning(
            f"Performance regression: {skill_id} {worst_metric} "
            f"{worst['baseline']:.1f}ms → {worst['current']:.1f}ms (+{degradation:.0f}%)"
        )

        return alert

    def _is_deduplicated(self, skill_id: str) -> bool:
        """Check if alert should be deduplicated."""
        last_alert = self._recent_alerts.get(skill_id)
        if not last_alert:
            return False

        return (time.time() - last_alert) < self.ALERT_WINDOW

    def _update_metrics(
        self,
        skill_id: str,
        execution_time_ms: float,
        status: str,
        confidence_score: float | None,
    ) -> None:
        """Update Prometheus metrics."""
        if not HAS_PROMETHEUS:
            return

        try:
            SkillMetrics.EXECUTION_TIME.labels(skill_id=skill_id).set(execution_time_ms)
            SkillMetrics.TOTAL_EXECUTIONS.labels(skill_id=skill_id, status=status).inc()

            if confidence_score is not None:
                SkillMetrics.CONFIDENCE_SCORE.labels(skill_id=skill_id).set(confidence_score)
        except Exception as e:
            self._logger.debug(f"Metrics update failed: {e}")

    def _report_regression(self, alert: PerformanceAlert) -> None:
        """Report regression to Prometheus."""
        if not HAS_PROMETHEUS:
            return

        try:
            SkillMetrics.REGRESSION_DETECTED.labels(skill_id=alert.skill_id, severity=alert.severity).set(1)
        except Exception as e:
            self._logger.debug(f"Regression metric update failed: {e}")

    def clear_regression_flag(self, skill_id: str) -> None:
        """Clear regression flag for a skill."""
        if not HAS_PROMETHEUS:
            return

        try:
            # Clear all severity levels
            for severity in ["low", "medium", "high"]:
                SkillMetrics.REGRESSION_DETECTED.labels(skill_id=skill_id, severity=severity).set(0)
        except Exception as e:
            self._logger.debug(f"Clear regression flag failed: {e}")

    def get_recent_alerts(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get recent performance alerts."""
        # Return skill_ids with recent alerts
        now = time.time()
        recent = [
            {"skill_id": sid, "last_alert": ts, "age_seconds": now - ts}
            for sid, ts in self._recent_alerts.items()
            if (now - ts) < 3600  # Last hour
        ]
        return sorted(recent, key=lambda x: x["last_alert"], reverse=True)[:limit]

    def cleanup_old_alerts(self) -> None:
        """Remove old alert records."""
        cutoff = time.time() - self.ALERT_WINDOW
        self._recent_alerts = {sid: ts for sid, ts in self._recent_alerts.items() if ts > cutoff}
