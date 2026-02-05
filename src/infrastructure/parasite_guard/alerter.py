"""
Parasite Guard Alerter.

Handles alerting for critical parasites with escalation logic.
Supports multiple alert channels and integrates with the state machine.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from .config import ParasiteGuardConfig
from .contracts import Alert, AlertChannel, AlerterContract, Severity
from .models import ParasiteContext, ParasiteSeverity
from .state_machine import GuardState, ParasiteGuardStateMachine

logger = logging.getLogger(__name__)


# =============================================================================
# Alert Channels
# =============================================================================


class LoggingAlertChannel:
    """Alert channel that logs to the standard logger.

    This is the default channel and always enabled.
    """

    def __init__(self, level: int = logging.ERROR):
        self._level = level

    async def send(self, alert: Alert) -> bool:
        """Log the alert."""
        logger.log(
            self._level,
            f"[PARASITE ALERT] [{alert.severity.value.upper()}] "
            f"{alert.component}: {alert.message}",
            extra={
                "alert_id": alert.id,
                "component": alert.component,
                "pattern": alert.pattern,
                "severity": alert.severity.value,
                "timestamp": alert.timestamp.isoformat(),
                "metadata": alert.metadata,
            },
        )
        return True


class SecurityAuditChannel:
    """Alert channel that writes to security audit log.

    For compliance and incident tracking.
    """

    def __init__(self, audit_file: str = "security_audit.log"):
        self._audit_file = audit_file

    async def send(self, alert: Alert) -> bool:
        """Write alert to audit log."""
        try:
            import json

            audit_entry = {
                "timestamp": alert.timestamp.isoformat(),
                "type": "parasite_alert",
                "alert_id": alert.id,
                "severity": alert.severity.value,
                "component": alert.component,
                "pattern": alert.pattern,
                "message": alert.message,
                "context": alert.context.to_dict() if alert.context else None,
                "metadata": alert.metadata,
            }

            # Write to file (append mode)
            import aiofiles  # type: ignore[import-not-found,import-untyped]

            async with aiofiles.open(self._audit_file, "a") as f:
                await f.write(json.dumps(audit_entry) + "\n")

            return True
        except Exception as e:
            logger.warning(f"Failed to write to security audit log: {e}")
            return False


class WebhookAlertChannel:
    """Alert channel that sends to a webhook URL.

    For integration with Slack, PagerDuty, or other systems.
    """

    def __init__(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        timeout: float = 10.0,
    ):
        self._url = url
        self._headers = headers or {"Content-Type": "application/json"}
        self._timeout = timeout

    async def send(self, alert: Alert) -> bool:
        """Send alert to webhook."""
        try:
            import aiohttp

            payload = {
                "alert_id": alert.id,
                "severity": alert.severity.value,
                "component": alert.component,
                "pattern": alert.pattern,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "metadata": alert.metadata,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self._url,
                    json=payload,
                    headers=self._headers,
                    timeout=aiohttp.ClientTimeout(total=self._timeout),
                ) as response:
                    if response.status < 400:
                        return True
                    logger.warning(
                        f"Webhook returned status {response.status}: {await response.text()}"
                    )
                    return False

        except ImportError:
            logger.warning("aiohttp not installed, webhook alerting unavailable")
            return False
        except Exception as e:
            logger.warning(f"Failed to send webhook alert: {e}")
            return False


class InMemoryAlertChannel:
    """Alert channel that stores alerts in memory for testing.

    Useful for unit tests and development.
    """

    def __init__(self, max_alerts: int = 1000):
        self._alerts: list[Alert] = []
        self._max_alerts = max_alerts

    async def send(self, alert: Alert) -> bool:
        """Store alert in memory."""
        self._alerts.append(alert)

        # Trim if over limit
        if len(self._alerts) > self._max_alerts:
            self._alerts = self._alerts[-self._max_alerts :]

        return True

    @property
    def alerts(self) -> list[Alert]:
        """Get all stored alerts."""
        return list(self._alerts)

    def clear(self) -> None:
        """Clear all stored alerts."""
        self._alerts.clear()


# =============================================================================
# Alerter
# =============================================================================


@dataclass
class EscalationPolicy:
    """Policy for escalating alerts.

    Defines thresholds and rules for escalation.

    Attributes:
        critical_threshold: Number of alerts before escalating to critical.
        escalation_window_seconds: Time window for counting alerts.
        auto_escalate_patterns: Patterns that always escalate.
        notify_on_escalation: Whether to send additional notification on escalation.
    """

    critical_threshold: int = 3
    escalation_window_seconds: float = 300.0  # 5 minutes
    auto_escalate_patterns: list[str] = field(
        default_factory=lambda: ["security_breach", "data_leak", "injection"]
    )
    notify_on_escalation: bool = True


class ParasiteAlerter:
    """Handles alerting for critical parasites.

    Implements AlerterContract and integrates with the state machine.

    Features:
    - Multiple alert channels (logging, audit, webhook)
    - Escalation logic based on pattern and frequency
    - State machine integration for ALERTING state
    - Alert deduplication
    - Metrics tracking
    """

    def __init__(
        self,
        config: ParasiteGuardConfig,
        state_machine: ParasiteGuardStateMachine | None = None,
        escalation_policy: EscalationPolicy | None = None,
    ):
        """Initialize alerter.

        Args:
            config: Parasite guard configuration.
            state_machine: Optional state machine for state transitions.
            escalation_policy: Optional escalation policy.
        """
        self.config = config
        self._state_machine = state_machine
        self._escalation_policy = escalation_policy or EscalationPolicy()

        # Alert channels
        self._alert_channels: list[AlertChannel] = [LoggingAlertChannel()]

        # Alert tracking
        self._recent_alerts: list[Alert] = []
        self._alert_counts: dict[str, int] = {}  # pattern -> count
        self._escalated_patterns: set[str] = set()

        # Statistics
        self._stats = {
            "alerts_sent": 0,
            "escalations": 0,
            "channel_failures": 0,
        }

    def add_channel(self, channel: AlertChannel) -> None:
        """Add an alert channel.

        Args:
            channel: Alert channel to add.
        """
        self._alert_channels.append(channel)

    def remove_channel(self, channel: AlertChannel) -> bool:
        """Remove an alert channel.

        Args:
            channel: Alert channel to remove.

        Returns:
            True if removed, False if not found.
        """
        try:
            self._alert_channels.remove(channel)
            return True
        except ValueError:
            return False

    def set_state_machine(self, state_machine: ParasiteGuardStateMachine) -> None:
        """Set the state machine for state transitions.

        Args:
            state_machine: State machine instance.
        """
        self._state_machine = state_machine

    def _map_severity(self, parasite_severity: ParasiteSeverity) -> Severity:
        """Map ParasiteSeverity to alert Severity."""
        mapping = {
            ParasiteSeverity.CRITICAL: Severity.CRITICAL,
            ParasiteSeverity.HIGH: Severity.HIGH,
            ParasiteSeverity.MEDIUM: Severity.MEDIUM,
            ParasiteSeverity.LOW: Severity.LOW,
        }
        return mapping.get(parasite_severity, Severity.MEDIUM)

    def _should_escalate(self, context: ParasiteContext) -> bool:
        """Determine if an alert should be escalated.

        Args:
            context: Parasite context.

        Returns:
            True if should escalate.
        """
        # Auto-escalate for specific patterns
        if context.pattern in self._escalation_policy.auto_escalate_patterns:
            return True

        # Check frequency threshold
        pattern_count = self._alert_counts.get(context.pattern, 0)
        if pattern_count >= self._escalation_policy.critical_threshold:
            return True

        # Critical severity always escalates
        if context.severity == ParasiteSeverity.CRITICAL:
            return True

        return False

    def _create_alert(
        self,
        context: ParasiteContext,
        severity: Severity,
        is_escalation: bool = False,
    ) -> Alert:
        """Create an Alert from ParasiteContext.

        Args:
            context: Parasite context.
            severity: Alert severity.
            is_escalation: Whether this is an escalation alert.

        Returns:
            Alert object.
        """
        prefix = "[ESCALATION] " if is_escalation else ""

        return Alert(
            id=str(uuid.uuid4()),
            severity=severity,
            component=context.component,
            pattern=context.pattern,
            message=f"{prefix}Detected parasite: {context.pattern} in {context.component}",
            timestamp=datetime.now(timezone.utc),
            context=context,
            metadata={
                "rule": context.rule,
                "is_escalation": is_escalation,
                "detection_metadata": context.detection_metadata,
            },
        )

    async def alert(self, context: ParasiteContext, severity: Severity) -> None:
        """Send an alert for a detected parasite.

        Args:
            context: ParasiteContext with detection details.
            severity: Severity level for the alert.
        """
        # Track alert count
        self._alert_counts[context.pattern] = (
            self._alert_counts.get(context.pattern, 0) + 1
        )

        # Create alert
        alert = self._create_alert(context, severity)
        self._recent_alerts.append(alert)

        # Send to all channels
        send_tasks = [channel.send(alert) for channel in self._alert_channels]
        results = await asyncio.gather(*send_tasks, return_exceptions=True)

        # Track failures
        for result in results:
            if isinstance(result, Exception) or (isinstance(result, bool) and not result):
                self._stats["channel_failures"] += 1

        self._stats["alerts_sent"] += 1

        logger.info(
            f"Alert sent: {alert.id} ({alert.severity.value})",
            extra={
                "alert_id": alert.id,
                "component": context.component,
                "pattern": context.pattern,
            },
        )

        # Check for escalation
        if self._should_escalate(context) and context.pattern not in self._escalated_patterns:
            await self.escalate(context)

    async def escalate(self, context: ParasiteContext) -> None:
        """Escalate a critical issue requiring manual intervention.

        Args:
            context: ParasiteContext for the critical issue.
        """
        self._escalated_patterns.add(context.pattern)
        self._stats["escalations"] += 1

        # Create escalation alert
        escalation_alert = self._create_alert(
            context, Severity.CRITICAL, is_escalation=True
        )
        escalation_alert.message = (
            f"[ESCALATION] Critical parasite requires manual intervention: "
            f"{context.pattern} in {context.component}"
        )

        # Send escalation to all channels
        send_tasks = [channel.send(escalation_alert) for channel in self._alert_channels]
        await asyncio.gather(*send_tasks, return_exceptions=True)

        # Transition state machine to ALERTING if available
        if self._state_machine:
            try:
                if self._state_machine.state == GuardState.MITIGATING:
                    self._state_machine.transition(GuardState.ALERTING, confidence=0.95)
                    logger.warning(
                        f"State machine transitioned to ALERTING for {context.pattern}"
                    )
            except Exception as e:
                logger.error(f"Failed to transition state machine: {e}")

        logger.critical(
            f"ESCALATION: {context.component}/{context.pattern} requires manual intervention",
            extra={
                "escalation_id": escalation_alert.id,
                "component": context.component,
                "pattern": context.pattern,
                "rule": context.rule,
            },
        )

    def get_recent_alerts(self, limit: int = 100) -> list[Alert]:
        """Get recent alerts.

        Args:
            limit: Maximum number of alerts to return.

        Returns:
            List of recent Alert objects.
        """
        return list(self._recent_alerts[-limit:])

    def get_alert_counts(self) -> dict[str, int]:
        """Get alert counts by pattern.

        Returns:
            Dictionary of pattern -> count.
        """
        return dict(self._alert_counts)

    def get_stats(self) -> dict[str, int]:
        """Get alerter statistics.

        Returns:
            Dictionary of statistics.
        """
        return {
            **self._stats,
            "total_patterns": len(self._alert_counts),
            "escalated_patterns": len(self._escalated_patterns),
            "recent_alerts_count": len(self._recent_alerts),
        }

    def reset_escalations(self) -> None:
        """Reset escalation tracking.

        Call this when issues are resolved.
        """
        self._escalated_patterns.clear()
        logger.info("Escalation tracking reset")

    def clear_alerts(self) -> None:
        """Clear all alert tracking data."""
        self._recent_alerts.clear()
        self._alert_counts.clear()
        self._escalated_patterns.clear()
        logger.info("Alert tracking data cleared")
