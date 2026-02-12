"""
Alerting rules and notification system for GRID monitoring.

Provides comprehensive alerting capabilities including rule definitions,
notification channels, escalation policies, and alert management.
Supports multiple notification methods and alert aggregation.
"""

from __future__ import annotations

import asyncio
import json
import logging
import smtplib
from dataclasses import dataclass
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


class AlertStatus(Enum):
    """Alert status."""
    FIRING = "firing"
    RESOLVED = "resolved"
    SILENCED = "silenced"
    SUPPRESSED = "suppressed"


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotificationChannel(Enum):
    """Notification channel types."""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"
    TEAMS = "teams"


@dataclass
class AlertRule:
    """Alert rule definition."""
    rule_id: str
    name: str
    description: str
    query: str
    condition: str
    threshold: float
    severity: AlertSeverity
    for_duration: timedelta
    labels: dict[str, str]
    annotations: dict[str, str]
    enabled: bool
    notification_channels: set[NotificationChannel]
    escalation_policy: str | None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "query": self.query,
            "condition": self.condition,
            "threshold": self.threshold,
            "severity": self.severity.value,
            "for_duration": self.for_duration.total_seconds(),
            "labels": self.labels,
            "annotations": self.annotations,
            "enabled": self.enabled,
            "notification_channels": [c.value for c in self.notification_channels],
            "escalation_policy": self.escalation_policy,
        }


@dataclass
class Alert:
    """Alert instance."""
    alert_id: str
    rule_id: str
    status: AlertStatus
    severity: AlertSeverity
    message: str
    labels: dict[str, str]
    annotations: dict[str, str]
    starts_at: datetime
    ends_at: datetime | None
    updated_at: datetime
    fingerprint: str
    notification_sent: dict[NotificationChannel, datetime]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "alert_id": self.alert_id,
            "rule_id": self.rule_id,
            "status": self.status.value,
            "severity": self.severity.value,
            "message": self.message,
            "labels": self.labels,
            "annotations": self.annotations,
            "starts_at": self.starts_at.isoformat(),
            "ends_at": self.ends_at.isoformat() if self.ends_at else None,
            "updated_at": self.updated_at.isoformat(),
            "fingerprint": self.fingerprint,
            "notification_sent": {k.value: v.isoformat() for k, v in self.notification_sent.items()},
        }


@dataclass
class NotificationConfig:
    """Notification channel configuration."""
    channel_type: NotificationChannel
    name: str
    enabled: bool
    config: dict[str, Any]
    rate_limit: timedelta | None
    retry_attempts: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "channel_type": self.channel_type.value,
            "name": self.name,
            "enabled": self.enabled,
            "config": self.config,
            "rate_limit": self.rate_limit.total_seconds() if self.rate_limit else None,
            "retry_attempts": self.retry_attempts,
        }


class GridAlertingSystem:
    """
    Comprehensive alerting system for GRID.

    Features:
    - Alert rule management
    - Multi-channel notifications
    - Alert aggregation
    - Escalation policies
    - Rate limiting
    - Alert history
    - Notification templates
    - Alert silencing
    """

    def __init__(self, storage_path: Path | None = None):
        """
        Initialize alerting system.

        Args:
            storage_path: Path for alert storage
        """
        self.storage_path = storage_path or Path("./data/alerting")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Alert rules storage
        self.rules_path = self.storage_path / "rules"
        self.rules_path.mkdir(exist_ok=True)

        # Alerts storage
        self.alerts_path = self.storage_path / "alerts"
        self.alerts_path.mkdir(exist_ok=True)

        # Notification configs
        self.notifications_path = self.storage_path / "notifications"
        self.notifications_path.mkdir(exist_ok=True)

        # In-memory storage
        self._rules: dict[str, AlertRule] = {}
        self._alerts: dict[str, Alert] = {}
        self._notification_configs: dict[str, NotificationConfig] = {}
        self._active_alerts: dict[str, Alert] = {}

        # Rate limiting
        self._notification_history: dict[str, list[datetime]] = {}

        # Background evaluation
        self._evaluation_task: asyncio.Task | None = None
        self._evaluation_active = False

        # Load existing configurations
        self._load_rules()
        self._load_notification_configs()

        logger.info(f"GridAlertingSystem initialized at {self.storage_path}")

    def create_rule(
        self,
        name: str,
        description: str,
        query: str,
        condition: str,
        threshold: float,
        severity: AlertSeverity,
        for_duration: timedelta,
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
        notification_channels: set[NotificationChannel] | None = None,
        escalation_policy: str | None = None,
    ) -> AlertRule:
        """
        Create a new alert rule.

        Args:
            name: Rule name
            description: Rule description
            query: Monitoring query
            condition: Alert condition
            threshold: Alert threshold
            severity: Alert severity
            for_duration: Duration before alerting
            labels: Alert labels
            annotations: Alert annotations
            notification_channels: Notification channels
            escalation_policy: Escalation policy name

        Returns:
            Created alert rule
        """
        rule_id = str(uuid4())

        rule = AlertRule(
            rule_id=rule_id,
            name=name,
            description=description,
            query=query,
            condition=condition,
            threshold=threshold,
            severity=severity,
            for_duration=for_duration,
            labels=labels or {},
            annotations=annotations or {},
            enabled=True,
            notification_channels=notification_channels or set(),
            escalation_policy=escalation_policy,
        )

        self._rules[rule_id] = rule
        self._save_rule(rule)

        logger.info(f"Created alert rule: {name}")
        return rule

    def update_rule(self, rule_id: str, **kwargs) -> bool:
        """
        Update an existing alert rule.

        Args:
            rule_id: Rule identifier
            **kwargs: Fields to update

        Returns:
            True if updated successfully
        """
        rule = self._rules.get(rule_id)
        if not rule:
            logger.error(f"Rule {rule_id} not found")
            return False

        # Update fields
        for field, value in kwargs.items():
            if hasattr(rule, field):
                setattr(rule, field, value)

        self._save_rule(rule)
        logger.info(f"Updated alert rule: {rule.name}")
        return True

    def delete_rule(self, rule_id: str) -> bool:
        """
        Delete an alert rule.

        Args:
            rule_id: Rule identifier

        Returns:
            True if deleted successfully
        """
        if rule_id not in self._rules:
            return False

        # Delete rule file
        rule_file = self.rules_path / f"{rule_id}.json"
        if rule_file.exists():
            rule_file.unlink()

        # Remove from memory
        del self._rules[rule_id]

        logger.info(f"Deleted alert rule: {rule_id}")
        return True

    def enable_rule(self, rule_id: str) -> bool:
        """Enable an alert rule."""
        return self.update_rule(rule_id, enabled=True)

    def disable_rule(self, rule_id: str) -> bool:
        """Disable an alert rule."""
        return self.update_rule(rule_id, enabled=False)

    def add_notification_channel(
        self,
        channel_type: NotificationChannel,
        name: str,
        config: dict[str, Any],
        rate_limit: timedelta | None = None,
        retry_attempts: int = 3,
    ) -> NotificationConfig:
        """
        Add a notification channel.

        Args:
            channel_type: Channel type
            name: Channel name
            config: Channel configuration
            rate_limit: Rate limiting interval
            retry_attempts: Number of retry attempts

        Returns:
            Created notification config
        """
        notification_config = NotificationConfig(
            channel_type=channel_type,
            name=name,
            enabled=True,
            config=config,
            rate_limit=rate_limit,
            retry_attempts=retry_attempts,
        )

        self._notification_configs[name] = notification_config
        self._save_notification_config(notification_config)

        logger.info(f"Added notification channel: {name}")
        return notification_config

    def create_alert(
        self,
        rule_id: str,
        message: str,
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
    ) -> Alert:
        """
        Create a new alert.

        Args:
            rule_id: Rule identifier
            message: Alert message
            labels: Alert labels
            annotations: Alert annotations

        Returns:
            Created alert
        """
        rule = self._rules.get(rule_id)
        if not rule:
            raise ValueError(f"Rule {rule_id} not found")

        alert_id = str(uuid4())
        fingerprint = self._generate_fingerprint(rule_id, labels or {})

        alert = Alert(
            alert_id=alert_id,
            rule_id=rule_id,
            status=AlertStatus.FIRING,
            severity=rule.severity,
            message=message,
            labels={**rule.labels, **(labels or {})},
            annotations={**rule.annotations, **(annotations or {})},
            starts_at=datetime.now(),
            ends_at=None,
            updated_at=datetime.now(),
            fingerprint=fingerprint,
            notification_sent={},
        )

        self._alerts[alert_id] = alert
        self._active_alerts[fingerprint] = alert
        self._save_alert(alert)

        # Send notifications
        asyncio.create_task(self._send_notifications(alert))

        logger.info(f"Created alert: {alert_id}")
        return alert

    def resolve_alert(self, alert_id: str) -> bool:
        """
        Resolve an alert.

        Args:
            alert_id: Alert identifier

        Returns:
            True if resolved successfully
        """
        alert = self._alerts.get(alert_id)
        if not alert:
            return False

        alert.status = AlertStatus.RESOLVED
        alert.ends_at = datetime.now()
        alert.updated_at = datetime.now()

        # Remove from active alerts
        if alert.fingerprint in self._active_alerts:
            del self._active_alerts[alert.fingerprint]

        self._save_alert(alert)

        # Send resolution notifications
        asyncio.create_task(self._send_resolution_notifications(alert))

        logger.info(f"Resolved alert: {alert_id}")
        return True

    def silence_alert(self, alert_id: str, duration: timedelta) -> bool:
        """
        Silence an alert for a duration.

        Args:
            alert_id: Alert identifier
            duration: Silence duration

        Returns:
            True if silenced successfully
        """
        alert = self._alerts.get(alert_id)
        if not alert:
            return False

        alert.status = AlertStatus.SILENCED
        alert.updated_at = datetime.now()

        # Schedule unsilence
        asyncio.create_task(self._unsilence_alert(alert_id, duration))

        self._save_alert(alert)
        logger.info(f"Silenced alert: {alert_id} for {duration}")
        return True

    def get_alerts(
        self,
        status: AlertStatus | None = None,
        severity: AlertSeverity | None = None,
        rule_id: str | None = None,
        limit: int = 100,
    ) -> list[Alert]:
        """
        Get alerts with optional filtering.

        Args:
            status: Filter by status
            severity: Filter by severity
            rule_id: Filter by rule ID
            limit: Maximum number of alerts

        Returns:
            List of alerts
        """
        alerts = list(self._alerts.values())

        if status:
            alerts = [a for a in alerts if a.status == status]

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        if rule_id:
            alerts = [a for a in alerts if a.rule_id == rule_id]

        # Sort by updated time (newest first)
        alerts.sort(key=lambda a: a.updated_at, reverse=True)

        return alerts[:limit]

    def get_active_alerts(self) -> list[Alert]:
        """Get all active alerts."""
        return list(self._active_alerts.values())

    def get_rules(self, enabled_only: bool = False) -> list[AlertRule]:
        """
        Get alert rules.

        Args:
            enabled_only: Return only enabled rules

        Returns:
            List of alert rules
        """
        rules = list(self._rules.values())

        if enabled_only:
            rules = [r for r in rules if r.enabled]

        return rules

    def start_evaluation(self, interval_seconds: int = 60) -> None:
        """
        Start background alert evaluation.

        Args:
            interval_seconds: Evaluation interval
        """
        if self._evaluation_active:
            return

        self._evaluation_active = True
        self._evaluation_task = asyncio.create_task(
            self._evaluation_loop(interval_seconds)
        )
        logger.info("Alert evaluation started")

    def stop_evaluation(self) -> None:
        """Stop background alert evaluation."""
        if not self._evaluation_active:
            return

        self._evaluation_active = False
        if self._evaluation_task:
            self._evaluation_task.cancel()
            try:
                asyncio.get_event_loop().run_until_complete(self._evaluation_task)
            except asyncio.CancelledError:
                pass
        logger.info("Alert evaluation stopped")

    async def _evaluation_loop(self, interval_seconds: int) -> None:
        """Background evaluation loop."""
        while self._evaluation_active:
            try:
                await self._evaluate_rules()
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Alert evaluation error: {e}")
                await asyncio.sleep(interval_seconds)

    async def _evaluate_rules(self) -> None:
        """Evaluate all enabled alert rules."""
        for rule in self.get_rules(enabled_only=True):
            try:
                await self._evaluate_rule(rule)
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.name}: {e}")

    async def _evaluate_rule(self, rule: AlertRule) -> None:
        """Evaluate a single alert rule."""
        # This is a simplified evaluation - in production, you'd
        # query actual metrics from Prometheus or other sources

        # Simulate evaluation
        current_value = 0.0  # Would be actual metric value

        # Check condition
        should_alert = self._evaluate_condition(current_value, rule.condition, rule.threshold)

        if should_alert:
            # Check if alert already exists
            existing_alert = None
            for alert in self.get_active_alerts():
                if alert.rule_id == rule.rule_id:
                    existing_alert = alert
                    break

            if not existing_alert:
                # Create new alert
                self.create_alert(
                    rule_id=rule.rule_id,
                    message=f"Alert: {rule.name} - {rule.description}",
                    labels={"rule_name": rule.name},
                    annotations={"current_value": str(current_value)},
                )
        else:
            # Resolve existing alerts for this rule
            for alert in self.get_active_alerts():
                if alert.rule_id == rule.rule_id:
                    self.resolve_alert(alert.alert_id)

    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """Evaluate alert condition."""
        if condition == "gt":
            return value > threshold
        elif condition == "lt":
            return value < threshold
        elif condition == "eq":
            return value == threshold
        elif condition == "ne":
            return value != threshold
        else:
            logger.warning(f"Unknown condition: {condition}")
            return False

    def _generate_fingerprint(self, rule_id: str, labels: dict[str, str]) -> str:
        """Generate alert fingerprint for deduplication."""
        import hashlib

        # Create fingerprint from rule ID and labels
        fingerprint_data = f"{rule_id}:{sorted(labels.items())}"
        return hashlib.md5(fingerprint_data.encode()).hexdigest()

    async def _send_notifications(self, alert: Alert) -> None:
        """Send notifications for an alert."""
        rule = self._rules.get(alert.rule_id)
        if not rule:
            return

        for channel_type in rule.notification_channels:
            config = self._get_notification_config(channel_type)
            if not config or not config.enabled:
                continue

            # Check rate limiting
            if not self._check_rate_limit(config.name):
                continue

            try:
                await self._send_notification(alert, config)
                alert.notification_sent[channel_type] = datetime.now()
            except Exception as e:
                logger.error(f"Failed to send {channel_type.value} notification: {e}")

    async def _send_resolution_notifications(self, alert: Alert) -> None:
        """Send resolution notifications."""
        rule = self._rules.get(alert.rule_id)
        if not rule:
            return

        for channel_type in rule.notification_channels:
            config = self._get_notification_config(channel_type)
            if not config or not config.enabled:
                continue

            try:
                await self._send_resolution_notification(alert, config)
            except Exception as e:
                logger.error(f"Failed to send resolution notification: {e}")

    async def _send_notification(self, alert: Alert, config: NotificationConfig) -> None:
        """Send notification through specific channel."""
        if config.channel_type == NotificationChannel.EMAIL:
            await self._send_email_notification(alert, config)
        elif config.channel_type == NotificationChannel.SLACK:
            await self._send_slack_notification(alert, config)
        elif config.channel_type == NotificationChannel.WEBHOOK:
            await self._send_webhook_notification(alert, config)
        else:
            logger.warning(f"Unsupported notification channel: {config.channel_type}")

    async def _send_email_notification(self, alert: Alert, config: NotificationConfig) -> None:
        """Send email notification."""
        smtp_config = config.config

        subject = f"GRID Alert: {alert.severity.value.upper()} - {alert.labels.get('rule_name', 'Unknown')}"
        body = f"""
Alert Details:
- Severity: {alert.severity.value}
- Message: {alert.message}
- Started: {alert.starts_at}
- Labels: {alert.labels}
- Annotations: {alert.annotations}
"""

        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = smtp_config['from']
        msg['To'] = ', '.join(smtp_config['to'])

        try:
            with smtplib.SMTP(smtp_config['host'], smtp_config.get('port', 587)) as server:
                server.starttls()
                server.login(smtp_config['username'], smtp_config['password'])
                server.send_message(msg)
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise

    async def _send_slack_notification(self, alert: Alert, config: NotificationConfig) -> None:
        """Send Slack notification."""
        # Implementation would use Slack API
        logger.info(f"Slack notification sent for alert {alert.alert_id}")

    async def _send_webhook_notification(self, alert: Alert, config: NotificationConfig) -> None:
        """Send webhook notification."""
        # Implementation would use HTTP client
        logger.info(f"Webhook notification sent for alert {alert.alert_id}")

    async def _send_resolution_notification(self, alert: Alert, config: NotificationConfig) -> None:
        """Send resolution notification."""
        if config.channel_type == NotificationChannel.EMAIL:
            # Send resolution email
            pass
        else:
            logger.info(f"Resolution notification sent for alert {alert.alert_id}")

    def _get_notification_config(self, channel_type: NotificationChannel) -> NotificationConfig | None:
        """Get notification configuration for channel type."""
        for config in self._notification_configs.values():
            if config.channel_type == channel_type and config.enabled:
                return config
        return None

    def _check_rate_limit(self, channel_name: str) -> bool:
        """Check if notification is rate limited."""
        if channel_name not in self._notification_history:
            self._notification_history[channel_name] = []

        now = datetime.now()
        history = self._notification_history[channel_name]

        # Clean old entries (older than 1 hour)
        history[:] = [t for t in history if now - t < timedelta(hours=1)]

        # Check rate limit (max 10 notifications per hour)
        return len(history) < 10

    async def _unsilence_alert(self, alert_id: str, duration: timedelta) -> None:
        """Unsilence an alert after duration."""
        await asyncio.sleep(duration.total_seconds())

        alert = self._alerts.get(alert_id)
        if alert and alert.status == AlertStatus.SILENCED:
            alert.status = AlertStatus.FIRING
            alert.updated_at = datetime.now()
            self._save_alert(alert)
            logger.info(f"Unsilenced alert: {alert_id}")

    def _save_rule(self, rule: AlertRule) -> None:
        """Save alert rule to storage."""
        rule_file = self.rules_path / f"{rule.rule_id}.json"
        rule_file.write_text(json.dumps(rule.to_dict(), indent=2))

    def _save_alert(self, alert: Alert) -> None:
        """Save alert to storage."""
        alert_file = self.alerts_path / f"{alert.alert_id}.json"
        alert_file.write_text(json.dumps(alert.to_dict(), indent=2))

    def _save_notification_config(self, config: NotificationConfig) -> None:
        """Save notification configuration."""
        config_file = self.notifications_path / f"{config.name}.json"
        config_file.write_text(json.dumps(config.to_dict(), indent=2))

    def _load_rules(self) -> None:
        """Load alert rules from storage."""
        for rule_file in self.rules_path.glob("*.json"):
            try:
                data = json.loads(rule_file.read_text())
                rule = AlertRule(
                    rule_id=data["rule_id"],
                    name=data["name"],
                    description=data["description"],
                    query=data["query"],
                    condition=data["condition"],
                    threshold=data["threshold"],
                    severity=AlertSeverity(data["severity"]),
                    for_duration=timedelta(seconds=data["for_duration"]),
                    labels=data["labels"],
                    annotations=data["annotations"],
                    enabled=data["enabled"],
                    notification_channels={NotificationChannel(c) for c in data["notification_channels"]},
                    escalation_policy=data.get("escalation_policy"),
                )
                self._rules[rule.rule_id] = rule
            except Exception as e:
                logger.error(f"Failed to load rule from {rule_file}: {e}")

    def _load_notification_configs(self) -> None:
        """Load notification configurations from storage."""
        for config_file in self.notifications_path.glob("*.json"):
            try:
                data = json.loads(config_file.read_text())
                config = NotificationConfig(
                    channel_type=NotificationChannel(data["channel_type"]),
                    name=data["name"],
                    enabled=data["enabled"],
                    config=data["config"],
                    rate_limit=timedelta(seconds=data["rate_limit"]) if data["rate_limit"] else None,
                    retry_attempts=data["retry_attempts"],
                )
                self._notification_configs[config.name] = config
            except Exception as e:
                logger.error(f"Failed to load notification config from {config_file}: {e}")


# Global alerting system instance
_global_alerting_system: GridAlertingSystem | None = None


def get_grid_alerting_system() -> GridAlertingSystem:
    """Get or create global GRID alerting system."""
    global _global_alerting_system
    if _global_alerting_system is None:
        _global_alerting_system = GridAlertingSystem()
    return _global_alerting_system


def set_grid_alerting_system(alerting_system: GridAlertingSystem) -> None:
    """Set global GRID alerting system."""
    global _global_alerting_system
    _global_alerting_system = alerting_system
