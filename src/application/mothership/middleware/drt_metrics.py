"""DRT (Distributed Request Tracking) Metrics Collection.

Provides comprehensive metrics collection for DRT operations including:
- Violation detection metrics
- Escalation tracking
- Performance monitoring
- False positive analysis
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..middleware.drt_middleware import BehavioralSignature

logger = logging.getLogger(__name__)


@dataclass
class DRTMetrics:
    """Container for DRT metrics data."""

    # Violation metrics
    violations_total: int = 0
    violations_by_severity: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    violations_by_path: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    violations_by_method: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    # Escalation metrics
    escalations_total: int = 0
    escalated_endpoints_count: int = 0
    escalation_duration_avg: float = 0.0

    # Performance metrics
    processing_time_avg: float = 0.0
    processing_time_total: float = 0.0
    processing_count: int = 0

    # Behavioral data metrics
    behavioral_signatures_total: int = 0
    attack_vectors_total: int = 0

    # False positive metrics
    false_positives_marked: int = 0
    false_positive_rate: float = 0.0

    # System health metrics
    cleanup_operations: int = 0
    db_operation_errors: int = 0

    # Time-series data (rolling windows)
    violations_last_hour: int = 0
    violations_last_24h: int = 0
    escalations_last_hour: int = 0
    escalations_last_24h: int = 0

    # Similarity score distribution
    similarity_scores: list[float] = field(default_factory=list)

    # Timestamp tracking
    last_updated: float = field(default_factory=time.time)


class DRTMetricsCollector:
    """Collector for DRT metrics with Prometheus-style interface."""

    def __init__(self):
        self.metrics = DRTMetrics()
        self._start_time = time.time()

    def record_violation(
        self,
        similarity_score: float,
        attack_vector_severity: str,
        request_path: str,
        request_method: str,
        was_blocked: bool = False,
        processing_time: float | None = None,
    ) -> None:
        """Record a violation detection."""
        self.metrics.violations_total += 1
        self.metrics.violations_by_severity[attack_vector_severity] += 1
        self.metrics.violations_by_path[request_path] += 1
        self.metrics.violations_by_method[request_method] += 1

        # Update similarity score distribution (keep last 1000 scores)
        self.metrics.similarity_scores.append(similarity_score)
        if len(self.metrics.similarity_scores) > 1000:
            self.metrics.similarity_scores.pop(0)

        # Update processing time metrics
        if processing_time is not None:
            self._update_processing_time(processing_time)

        self.metrics.last_updated = time.time()
        logger.debug(
            f"DRT violation recorded: score={similarity_score:.3f}, "
            f"severity={attack_vector_severity}, path={request_path}"
        )

    def record_escalation(
        self,
        path: str,
        similarity_score: float,
        duration_minutes: int | None = None,
    ) -> None:
        """Record an endpoint escalation."""
        self.metrics.escalations_total += 1
        self.metrics.escalated_endpoints_count += 1

        if duration_minutes:
            # Simple moving average for escalation duration
            total_duration = self.metrics.escalation_duration_avg * (self.metrics.escalations_total - 1)
            self.metrics.escalation_duration_avg = (total_duration + duration_minutes) / self.metrics.escalations_total

        self.metrics.last_updated = time.time()
        logger.info(f"DRT escalation recorded: path={path}, score={similarity_score:.3f}")

    def record_deescalation(self, path: str) -> None:
        """Record an endpoint de-escalation."""
        if self.metrics.escalated_endpoints_count > 0:
            self.metrics.escalated_endpoints_count -= 1

        self.metrics.last_updated = time.time()
        logger.info(f"DRT de-escalation recorded: path={path}")

    def record_behavioral_signature(self, signature: BehavioralSignature) -> None:
        """Record a new behavioral signature."""
        self.metrics.behavioral_signatures_total += 1
        self.metrics.last_updated = time.time()

    def record_attack_vector(self, severity: str) -> None:
        """Record a new attack vector."""
        self.metrics.attack_vectors_total += 1
        self.metrics.last_updated = time.time()

    def record_false_positive(self) -> None:
        """Record a false positive marking."""
        self.metrics.false_positives_marked += 1
        self._update_false_positive_rate()
        self.metrics.last_updated = time.time()

    def record_cleanup_operation(self, duration: float | None = None) -> None:
        """Record a cleanup operation."""
        self.metrics.cleanup_operations += 1

        if duration is not None:
            self._update_processing_time(duration)

        self.metrics.last_updated = time.time()

    def record_db_error(self, operation: str) -> None:
        """Record a database operation error."""
        self.metrics.db_operation_errors += 1
        self.metrics.last_updated = time.time()
        logger.warning(f"DRT database error in operation: {operation}")

    def update_time_series_metrics(self) -> None:
        """Update rolling time-series metrics (should be called periodically)."""
        # In a real implementation, this would query the database for recent metrics
        # For now, we'll reset to zero and let the system accumulate
        current_time = time.time()
        if current_time - self._start_time > 3600:  # Reset every hour
            self.metrics.violations_last_hour = 0
            self.metrics.escalations_last_hour = 0
            self._start_time = current_time

        if current_time - self._start_time > 86400:  # Reset every 24 hours
            self.metrics.violations_last_24h = 0
            self.metrics.escalations_last_24h = 0

    def _update_processing_time(self, duration: float) -> None:
        """Update processing time metrics."""
        self.metrics.processing_count += 1
        total_time = self.metrics.processing_time_total + duration
        self.metrics.processing_time_total = total_time
        self.metrics.processing_time_avg = total_time / self.metrics.processing_count

    def _update_false_positive_rate(self) -> None:
        """Update false positive rate calculation."""
        if self.metrics.violations_total > 0:
            self.metrics.false_positive_rate = self.metrics.false_positives_marked / self.metrics.violations_total

    def get_metrics_dict(self) -> dict[str, Any]:
        """Get all metrics as a dictionary for Prometheus-style export."""
        return {
            # Violation metrics
            "drt_violations_total": self.metrics.violations_total,
            "drt_violations_by_severity": dict(self.metrics.violations_by_severity),
            "drt_violations_by_path": dict(self.metrics.violations_by_path),
            "drt_violations_by_method": dict(self.metrics.violations_by_method),
            # Escalation metrics
            "drt_escalations_total": self.metrics.escalations_total,
            "drt_escalated_endpoints_current": self.metrics.escalated_endpoints_count,
            "drt_escalation_duration_avg_minutes": self.metrics.escalation_duration_avg,
            # Performance metrics
            "drt_processing_time_avg_ms": self.metrics.processing_time_avg * 1000,
            "drt_processing_operations_total": self.metrics.processing_count,
            # Behavioral data metrics
            "drt_behavioral_signatures_total": self.metrics.behavioral_signatures_total,
            "drt_attack_vectors_total": self.metrics.attack_vectors_total,
            # False positive metrics
            "drt_false_positives_marked": self.metrics.false_positives_marked,
            "drt_false_positive_rate": self.metrics.false_positive_rate,
            # System health metrics
            "drt_cleanup_operations_total": self.metrics.cleanup_operations,
            "drt_db_operation_errors_total": self.metrics.db_operation_errors,
            # Time-series metrics
            "drt_violations_last_hour": self.metrics.violations_last_hour,
            "drt_violations_last_24h": self.metrics.violations_last_24h,
            "drt_escalations_last_hour": self.metrics.escalations_last_hour,
            "drt_escalations_last_24h": self.metrics.escalations_last_24h,
            # Similarity score statistics
            "drt_similarity_scores_count": len(self.metrics.similarity_scores),
            "drt_similarity_scores_avg": (
                sum(self.metrics.similarity_scores) / len(self.metrics.similarity_scores)
                if self.metrics.similarity_scores
                else 0.0
            ),
            "drt_similarity_scores_min": min(self.metrics.similarity_scores) if self.metrics.similarity_scores else 0.0,
            "drt_similarity_scores_max": max(self.metrics.similarity_scores) if self.metrics.similarity_scores else 0.0,
            # Metadata
            "drt_metrics_last_updated": self.metrics.last_updated,
            "drt_uptime_seconds": time.time() - self._start_time,
        }

    def get_prometheus_metrics(self) -> str:
        """Generate Prometheus-formatted metrics output."""
        lines = []
        metrics_dict = self.get_metrics_dict()

        for key, value in metrics_dict.items():
            if isinstance(value, dict):
                # Handle labeled metrics (e.g., violations by severity)
                for label_value, count in value.items():
                    lines.append(f"# HELP {key} DRT {key.replace('_', ' ')}")
                    lines.append(f"# TYPE {key} gauge")
                    lines.append(f'{key}{{label="{label_value}"}} {count}')
            elif isinstance(value, (int, float)):
                lines.append(f"# HELP {key} DRT {key.replace('_', ' ')}")
                lines.append(f"# TYPE {key} gauge")
                lines.append(f"{key} {value}")
            # Skip non-numeric values

        return "\n".join(lines)

    def reset_metrics(self) -> None:
        """Reset all metrics (useful for testing)."""
        self.metrics = DRTMetrics()
        self._start_time = time.time()


# Global metrics collector instance
_metrics_collector: DRTMetricsCollector | None = None


def get_drt_metrics_collector() -> DRTMetricsCollector:
    """Get the global DRT metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = DRTMetricsCollector()
    return _metrics_collector


def record_drt_violation(
    similarity_score: float,
    attack_vector_severity: str,
    request_path: str,
    request_method: str,
    was_blocked: bool = False,
    processing_time: float | None = None,
) -> None:
    """Convenience function to record a DRT violation."""
    collector = get_drt_metrics_collector()
    collector.record_violation(
        similarity_score=similarity_score,
        attack_vector_severity=attack_vector_severity,
        request_path=request_path,
        request_method=request_method,
        was_blocked=was_blocked,
        processing_time=processing_time,
    )


def record_drt_escalation(
    path: str,
    similarity_score: float,
    duration_minutes: int | None = None,
) -> None:
    """Convenience function to record a DRT escalation."""
    collector = get_drt_metrics_collector()
    collector.record_escalation(path=path, similarity_score=similarity_score, duration_minutes=duration_minutes)


def record_drt_deescalation(path: str) -> None:
    """Convenience function to record a DRT de-escalation."""
    collector = get_drt_metrics_collector()
    collector.record_deescalation(path)
