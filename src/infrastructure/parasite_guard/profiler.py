"""
Profiling and logging for parasite detection lifecycle.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from .config import ParasiteGuardConfig
from .models import (
    DetectionResult,
    ParasiteContext,
    ParasiteLogEntry,
    SanitizationResult,
)

logger = logging.getLogger(__name__)


class ParasiteProfiler:
    """
    Records and profiles parasite detection events.

    Provides:
    - Structured logging
    - Metrics emission (optional Prometheus)
    - Event tracking across lifecycle
    """

    def __init__(self, config: ParasiteGuardConfig):
        self.config = config
        self._metrics_enabled = config.metrics_enabled
        self._metrics_prefix = config.metrics_prefix
        self._detection_count: dict[str, int] = defaultdict(int)
        self._sanitization_count: dict[str, int] = defaultdict(int)

    async def record_detection(self, result: DetectionResult, request: Any) -> None:
        """
        Record a parasite detection event.

        Args:
            result: DetectionResult from detector
            request: ASGI request object
        """
        if not result.detected or not result.context:
            return

        context = result.context

        # Update detection count
        self._detection_count[context.component] += 1

        # Create log entry
        entry = ParasiteLogEntry(
            parasite_id=str(context.id),
            event_type="detection",
            component=context.component,
            pattern=context.pattern,
            severity=context.severity.name,
            message=f"Parasite detected: {result.reason}",
            data={
                "rule": context.rule,
                "confidence": result.confidence,
                "request_path": getattr(request.url, "path", "unknown") if hasattr(request, "url") else "unknown",
                "request_method": getattr(request, "method", "unknown"),
                "client_ip": getattr(getattr(request, "client", None), "host", "unknown"),
                "detection_metadata": context.detection_metadata,
            },
        )

        # Emit structured log
        self._emit_log(entry)

        # Emit metrics if enabled
        if self._metrics_enabled:
            self._emit_detection_metrics(context, result.confidence)

    async def record_sanitization(self, context: ParasiteContext, result: SanitizationResult) -> None:
        """
        Record a parasite sanitization event.

        Args:
            context: ParasiteContext
            result: SanitizationResult from sanitizer
        """
        # Update sanitization count
        self._sanitization_count[context.component] += 1

        # Create log entry
        entry = ParasiteLogEntry(
            parasite_id=str(context.id),
            event_type="sanitization",
            component=context.component,
            pattern=context.pattern,
            severity="info",
            message=f"Sanitization {'succeeded' if result.success else 'failed'}",
            data={
                "success": result.success,
                "steps": result.steps,
                "error": result.error,
                "duration_ms": result.duration_ms,
                "metadata": result.metadata,
            },
        )

        # Emit structured log
        self._emit_log(entry)

        # Emit metrics if enabled
        if self._metrics_enabled:
            self._emit_sanitization_metrics(context, result)

    async def record_profiling(self, context: ParasiteContext, phase: str, metadata: dict[str, Any]) -> None:
        """
        Record profiling data for a phase of parasite handling.

        Args:
            context: ParasiteContext
            phase: Phase name (e.g., "tracing", "response_generation")
            metadata: Phase-specific metadata
        """
        entry = ParasiteLogEntry(
            parasite_id=str(context.id),
            event_type="profiling",
            component=context.component,
            pattern=context.pattern,
            severity="debug",
            message=f"Profiling phase: {phase}",
            data={
                "phase": phase,
                "metadata": metadata,
            },
        )

        self._emit_log(entry)

    def _emit_log(self, entry: ParasiteLogEntry) -> None:
        """Emit a structured log entry."""
        if self.config.log_structured:
            logger.info(
                entry.message,
                extra=entry.to_dict(),
            )
        else:
            logger.info(entry.message)

    def _emit_detection_metrics(self, context: ParasiteContext, confidence: float) -> None:
        """Emit detection metrics to Prometheus."""
        try:
            from prometheus_client import Counter

            # Get or create counter
            counter = Counter(
                f"{self._metrics_prefix}_detected_total",
                "Total parasite detections",
                ["component", "pattern", "severity"],
            )

            # Increment
            counter.labels(
                component=context.component,
                pattern=context.pattern,
                severity=context.severity.name,
            ).inc()

            # Confidence histogram
            confidence_histogram = Counter(
                f"{self._metrics_prefix}_detection_confidence",
                "Detection confidence distribution",
                ["component", "range"],
            )

            # Bucket confidence
            range_bucket = self._get_confidence_bucket(confidence)
            confidence_histogram.labels(
                component=context.component,
                range=range_bucket,
            ).inc()

        except ImportError:
            # Prometheus not installed, silently skip
            pass
        except Exception as e:
            logger.warning(f"Failed to emit metrics: {e}", exc_info=True)

    def _emit_sanitization_metrics(self, context: ParasiteContext, result: SanitizationResult) -> None:
        """Emit sanitization metrics to Prometheus."""
        try:
            from prometheus_client import Counter, Gauge

            # Success/failure counters
            counter = Counter(
                f"{self._metrics_prefix}_sanitized_total",
                "Total parasite sanitizations",
                ["component", "outcome"],
            )

            outcome = "success" if result.success else "failure"
            counter.labels(
                component=context.component,
                outcome=outcome,
            ).inc()

            # Active sanitizations gauge
            active_gauge = Gauge(
                f"{self._metrics_prefix}_active_sanitizations",
                "Currently active sanitization tasks",
                ["component"],
            )

            # This would need to be tracked at higher level
            # For now, we just emit a count
            active_gauge.labels(component=context.component).set(0)

        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"Failed to emit sanitization metrics: {e}", exc_info=True)

    def _get_confidence_bucket(self, confidence: float) -> str:
        """Get confidence bucket for metrics."""
        if confidence >= 0.95:
            return "0.95-1.00"
        elif confidence >= 0.90:
            return "0.90-0.95"
        elif confidence >= 0.80:
            return "0.80-0.90"
        elif confidence >= 0.70:
            return "0.70-0.80"
        else:
            return "0.00-0.70"

    def get_stats(self) -> dict[str, dict[str, int]]:
        """Get profiling statistics."""
        return {
            "detections": dict(self._detection_count),
            "sanitizations": dict(self._sanitization_count),
        }
