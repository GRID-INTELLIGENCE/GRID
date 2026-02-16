"""
Enhanced Safety Monitoring and Alerting

Provides structured logging of safety events and real-time monitoring with alert triggering.
"""

import asyncio
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger("safety.monitoring")


@dataclass
class SafetyEvent:
    event_type: str  # e.g., "safety_violation", "rate_limit_exceeded"
    severity: str  # "info", "warning", "error", "critical"
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    user_id: str | None = None
    session_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    stack_trace: str | None = None
    environment: str = os.getenv("GRID_ENV", "development")

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "severity": self.severity,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "metadata": self.metadata,
            "environment": self.environment,
            "service": "ai_safety_engine",
        }


class EnhancedSafetyMonitor:
    def __init__(self, alert_thresholds: dict[str, tuple[int, int]] = None):
        # thresholds: key -> (count_threshold, time_window_seconds)
        self.alert_thresholds = alert_thresholds or {
            "safety_violation": (5, 300),  # 5 violations in 5 minutes
            "rate_limit_exceeded": (10, 600),  # 10 rate limits in 10 minutes
            "content_violation": (3, 3600),  # 3 content violations in 1 hour
        }
        self.events: list[SafetyEvent] = []
        self.metrics: dict[str, int] = {}
        self.alert_handlers: list[Callable[[dict[str, Any]], None]] = []

    def add_alert_handler(self, handler: Callable[[dict[str, Any]], None]):
        """Add a custom alert handler (e.g., Slack, PagerDuty)"""
        self.alert_handlers.append(handler)

    def record_event(self, event: SafetyEvent):
        """Record and process a safety event"""
        self.events.append(event)
        self._update_metrics(event)
        self._check_alert_conditions(event)

    def _update_metrics(self, event: SafetyEvent):
        """Update metrics based on event type and severity"""
        type_key = f"{event.event_type}_count"
        self.metrics[type_key] = self.metrics.get(type_key, 0) + 1

        severity_key = f"{event.severity}_severity_count"
        self.metrics[severity_key] = self.metrics.get(severity_key, 0) + 1

    def _check_alert_conditions(self, event: SafetyEvent):
        """Check if any alert conditions are met for the current event type"""
        if event.event_type not in self.alert_thresholds:
            return

        count_threshold, time_window = self.alert_thresholds[event.event_type]
        now = time.time()

        recent_events = [
            e for e in self.events if e.event_type == event.event_type and now - e.timestamp <= time_window
        ]

        if len(recent_events) >= count_threshold:
            self._trigger_alert(
                alert_type=f"{event.event_type}_threshold_exceeded",
                event_count=len(recent_events),
                time_window=time_window,
                events=[e.to_dict() for e in recent_events],
            )

    def _trigger_alert(self, alert_type: str, **kwargs):
        """Trigger alert through all registered handlers"""
        alert = {
            "alert_id": str(uuid.uuid4()),
            "alert_type": alert_type,
            "timestamp": time.time(),
            "metrics": self.metrics.copy(),
            "environment": os.getenv("GRID_ENV", "development"),
            **kwargs,
        }

        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {str(e)}")

        logger.warning(f"Safety Alert Triggered: {alert_type}", extra={"alert": alert})

    async def start(self):
        """Start background monitoring task."""
        asyncio.create_task(self._monitor_safety_metrics())

    async def _monitor_safety_metrics(self):
        """Background loop: periodically check system health."""
        while True:
            try:
                await self._check_system_health()
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                logger.info("Safety monitor background task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in safety monitor loop: {e}")
                await asyncio.sleep(5)

    async def _check_system_health(self):
        """Minimal system health check (event counts, log)."""
        total_events = len(self.events)
        logger.debug(
            "safety_monitor_health",
            total_events=total_events,
            metrics_keys=len(self.metrics),
        )


# Singleton for app-wide use (started from main lifespan)
_monitor_instance: EnhancedSafetyMonitor | None = None


def get_safety_monitor() -> EnhancedSafetyMonitor:
    """Return the shared EnhancedSafetyMonitor instance."""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = EnhancedSafetyMonitor()
    return _monitor_instance


async def monitor_user_session(user_id: str, monitor: EnhancedSafetyMonitor):
    """
    Background task loop for proactive safety monitoring and intervention.
    """
    from safety.ai_workflow_safety import get_ai_workflow_safety_engine

    engine = await get_ai_workflow_safety_engine(user_id)
    logger.info(f"Background monitor started for user {user_id}")

    try:
        while True:
            metrics = engine.get_safety_metrics()

            # 1. Alert if cognitive load is critical
            if metrics["cognitive_load"] == "critical":
                monitor.record_event(
                    SafetyEvent(
                        event_type="high_cognitive_load",
                        severity="error",
                        user_id=user_id,
                        metadata={"metrics": metrics},
                    )
                )
                # Auto-pause for 5 minutes if load is critical
                await engine.pause_interaction(reason="Critical cognitive load detected", duration=300)

            # 2. Check for session duration limits (Rule override)
            if metrics["session_duration"] > 3600:  # 1 hour
                await engine.pause_interaction(
                    reason="Maximum session duration reached",
                    duration=600,  # 10 minute break
                )
                monitor.record_event(
                    SafetyEvent(event_type="session_limit_intervention", severity="warning", user_id=user_id)
                )

            # 3. Check for high heat
            if metrics["heat"] > 40.0:  # Close to threshold
                monitor.record_event(
                    SafetyEvent(
                        event_type="high_heat_warning",
                        severity="warning",
                        user_id=user_id,
                        metadata={"heat": metrics["heat"]},
                    )
                )

            await asyncio.sleep(60)  # Check every minute
    except asyncio.CancelledError:
        logger.info(f"Background monitor for user {user_id} cancelled")
    except Exception as e:
        logger.error(f"Error in monitor_user_session for {user_id}: {str(e)}")
