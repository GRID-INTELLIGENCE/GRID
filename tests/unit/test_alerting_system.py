"""
Unit tests for GRID Alerting System.

Tests cover:
- Alert rule management
- Alert creation and lifecycle
- Notification channels
- Alert aggregation and deduplication
- Rate limiting
- Alert evaluation

Note: These tests require the infrastructure.monitoring module.
Tests are skipped if the module is not available.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest

# Skip entire module if infrastructure.monitoring is not available
try:
    from infrastructure.monitoring.alerting_system import (  # type: ignore[import-not-found]
        Alert,
        AlertRule,
        AlertSeverity,
        AlertStatus,
        GridAlertingSystem,
        NotificationChannel,
        get_grid_alerting_system,
    )
except ImportError:
    pytest.skip(
        "infrastructure.monitoring module not available - skipping alerting tests",
        allow_module_level=True,
    )


class TestAlertRule:
    """Tests for alert rule management."""

    def test_create_rule(self):
        """Should create alert rule with all fields."""
        system = GridAlertingSystem(storage_path=Path("./test_alerting"))
        rule = system.create_rule(
            name="test_rule",
            description="Test alert rule",
            query="up == 0",
            condition="eq",
            threshold=0.0,
            severity=AlertSeverity.WARNING,
            for_duration=timedelta(minutes=5),
        )

        assert rule.name == "test_rule"
        assert rule.severity == AlertSeverity.WARNING
        assert rule.enabled is True

    def test_update_rule(self):
        """Should update existing rule."""
        system = GridAlertingSystem(storage_path=Path("./test_alerting"))
        rule = system.create_rule(
            name="test_rule",
            description="Original",
            query="up == 0",
            condition="eq",
            threshold=0.0,
            severity=AlertSeverity.WARNING,
            for_duration=timedelta(minutes=5),
        )

        updated = system.update_rule(rule.rule_id, description="Updated")
        assert updated is True
        assert system._rules[rule.rule_id].description == "Updated"

    def test_delete_rule(self):
        """Should delete rule."""
        system = GridAlertingSystem(storage_path=Path("./test_alerting"))
        rule = system.create_rule(
            name="test_rule",
            description="Test",
            query="up == 0",
            condition="eq",
            threshold=0.0,
            severity=AlertSeverity.WARNING,
            for_duration=timedelta(minutes=5),
        )

        deleted = system.delete_rule(rule.rule_id)
        assert deleted is True
        assert rule.rule_id not in system._rules

    def test_enable_disable_rule(self):
        """Should enable and disable rules."""
        system = GridAlertingSystem(storage_path=Path("./test_alerting"))
        rule = system.create_rule(
            name="test_rule",
            description="Test",
            query="up == 0",
            condition="eq",
            threshold=0.0,
            severity=AlertSeverity.WARNING,
            for_duration=timedelta(minutes=5),
        )

        system.disable_rule(rule.rule_id)
        assert system._rules[rule.rule_id].enabled is False

        system.enable_rule(rule.rule_id)
        assert system._rules[rule.rule_id].enabled is True


class TestAlertLifecycle:
    """Tests for alert creation and lifecycle."""

    def test_create_alert(self):
        """Should create alert from rule."""
        system = GridAlertingSystem(storage_path=Path("./test_alerting"))
        rule = system.create_rule(
            name="test_rule",
            description="Test",
            query="up == 0",
            condition="eq",
            threshold=0.0,
            severity=AlertSeverity.WARNING,
            for_duration=timedelta(minutes=5),
        )

        alert = system.create_alert(
            rule_id=rule.rule_id,
            message="Test alert",
            labels={"service": "test"},
        )

        assert alert.status == AlertStatus.FIRING
        assert alert.severity == AlertSeverity.WARNING
        assert alert.fingerprint is not None

    def test_resolve_alert(self):
        """Should resolve alert."""
        system = GridAlertingSystem(storage_path=Path("./test_alerting"))
        rule = system.create_rule(
            name="test_rule",
            description="Test",
            query="up == 0",
            condition="eq",
            threshold=0.0,
            severity=AlertSeverity.WARNING,
            for_duration=timedelta(minutes=5),
        )

        alert = system.create_alert(rule_id=rule.rule_id, message="Test")
        resolved = system.resolve_alert(alert.alert_id)

        assert resolved is True
        assert system._alerts[alert.alert_id].status == AlertStatus.RESOLVED

    def test_silence_alert(self):
        """Should silence alert for duration."""
        system = GridAlertingSystem(storage_path=Path("./test_alerting"))
        rule = system.create_rule(
            name="test_rule",
            description="Test",
            query="up == 0",
            condition="eq",
            threshold=0.0,
            severity=AlertSeverity.WARNING,
            for_duration=timedelta(minutes=5),
        )

        alert = system.create_alert(rule_id=rule.rule_id, message="Test")
        silenced = system.silence_alert(alert.alert_id, timedelta(seconds=1))

        assert silenced is True
        assert system._alerts[alert.alert_id].status == AlertStatus.SILENCED

    def test_alert_deduplication(self):
        """Should deduplicate alerts with same fingerprint."""
        system = GridAlertingSystem(storage_path=Path("./test_alerting"))
        rule = system.create_rule(
            name="test_rule",
            description="Test",
            query="up == 0",
            condition="eq",
            threshold=0.0,
            severity=AlertSeverity.WARNING,
            for_duration=timedelta(minutes=5),
        )

        alert1 = system.create_alert(
            rule_id=rule.rule_id,
            message="Test",
            labels={"service": "test"},
        )
        alert2 = system.create_alert(
            rule_id=rule.rule_id,
            message="Test",
            labels={"service": "test"},
        )

        # Should have same fingerprint
        assert alert1.fingerprint == alert2.fingerprint

        # Only one active alert
        active = system.get_active_alerts()
        assert len(active) == 1


class TestNotificationChannels:
    """Tests for notification channel management."""

    def test_add_notification_channel(self):
        """Should add notification channel."""
        system = GridAlertingSystem(storage_path=Path("./test_alerting"))
        config = system.add_notification_channel(
            channel_type=NotificationChannel.EMAIL,
            name="test_email",
            config={"host": "smtp.example.com", "from": "alerts@example.com", "to": ["admin@example.com"]},
        )

        assert config.name == "test_email"
        assert config.channel_type == NotificationChannel.EMAIL

    def test_get_alerts_filtered(self):
        """Should filter alerts by status and severity."""
        system = GridAlertingSystem(storage_path=Path("./test_alerting"))
        rule = system.create_rule(
            name="test_rule",
            description="Test",
            query="up == 0",
            condition="eq",
            threshold=0.0,
            severity=AlertSeverity.WARNING,
            for_duration=timedelta(minutes=5),
        )

        alert1 = system.create_alert(rule_id=rule.rule_id, message="Warning")
        system.resolve_alert(alert1.alert_id)

        system.create_alert(rule_id=rule.rule_id, message="Active")

        firing = system.get_alerts(status=AlertStatus.FIRING)
        resolved = system.get_alerts(status=AlertStatus.RESOLVED)

        assert len(firing) == 1
        assert len(resolved) == 1


class TestAlertEvaluation:
    """Tests for alert rule evaluation."""

    def test_evaluate_condition_gt(self):
        """Should evaluate greater-than condition."""
        system = GridAlertingSystem(storage_path=Path("./test_alerting"))
        result = system._evaluate_condition(10.0, "gt", 5.0)
        assert result is True

    def test_evaluate_condition_lt(self):
        """Should evaluate less-than condition."""
        system = GridAlertingSystem(storage_path=Path("./test_alerting"))
        result = system._evaluate_condition(5.0, "lt", 10.0)
        assert result is True

    def test_evaluate_condition_eq(self):
        """Should evaluate equals condition."""
        system = GridAlertingSystem(storage_path=Path("./test_alerting"))
        result = system._evaluate_condition(5.0, "eq", 5.0)
        assert result is True

    def test_evaluate_condition_ne(self):
        """Should evaluate not-equals condition."""
        system = GridAlertingSystem(storage_path=Path("./test_alerting"))
        result = system._evaluate_condition(5.0, "ne", 10.0)
        assert result is True

    def test_fingerprint_generation(self):
        """Should generate consistent fingerprints."""
        system = GridAlertingSystem(storage_path=Path("./test_alerting"))
        fp1 = system._generate_fingerprint("rule1", {"service": "api", "env": "prod"})
        fp2 = system._generate_fingerprint("rule1", {"service": "api", "env": "prod"})
        fp3 = system._generate_fingerprint("rule1", {"service": "web", "env": "prod"})

        assert fp1 == fp2
        assert fp1 != fp3


class TestRateLimiting:
    """Tests for rate limiting."""

    def test_rate_limit_check(self):
        """Should enforce rate limits."""
        system = GridAlertingSystem(storage_path=Path("./test_alerting"))

        # First 10 notifications should pass
        for _ in range(10):
            assert system._check_rate_limit("test_channel") is True

        # 11th should fail
        assert system._check_rate_limit("test_channel") is False


class TestAlertPersistence:
    """Tests for alert persistence."""

    def test_rule_persistence(self):
        """Should save and load rules."""
        system = GridAlertingSystem(storage_path=Path("./test_alerting"))
        rule = system.create_rule(
            name="test_rule",
            description="Test",
            query="up == 0",
            condition="eq",
            threshold=0.0,
            severity=AlertSeverity.WARNING,
            for_duration=timedelta(minutes=5),
        )

        # Create new system instance to test loading
        system2 = GridAlertingSystem(storage_path=Path("./test_alerting"))
        loaded_rule = system2._rules.get(rule.rule_id)

        assert loaded_rule is not None
        assert loaded_rule.name == "test_rule"


class TestFactoryFunctions:
    """Tests for factory functions."""

    def test_get_grid_alerting_system_singleton(self):
        """Should return singleton instance."""
        system1 = get_grid_alerting_system()
        system2 = get_grid_alerting_system()
        assert system1 is system2


class TestAlertSerialization:
    """Tests for alert serialization."""

    def test_alert_to_dict(self):
        """Should serialize alert to dict."""
        alert = Alert(
            alert_id="test_id",
            rule_id="rule_id",
            status=AlertStatus.FIRING,
            severity=AlertSeverity.WARNING,
            message="Test alert",
            labels={"service": "test"},
            annotations={"description": "test"},
            starts_at=datetime.now(),
            ends_at=None,
            updated_at=datetime.now(),
            fingerprint="fp123",
            notification_sent={},
        )

        alert_dict = alert.to_dict()
        assert alert_dict["alert_id"] == "test_id"
        assert alert_dict["status"] == "firing"
        assert alert_dict["severity"] == "warning"

    def test_rule_to_dict(self):
        """Should serialize rule to dict."""
        rule = AlertRule(
            rule_id="rule_id",
            name="test_rule",
            description="Test rule",
            query="up == 0",
            condition="eq",
            threshold=0.0,
            severity=AlertSeverity.WARNING,
            for_duration=timedelta(minutes=5),
            labels={"service": "test"},
            annotations={"description": "test"},
            enabled=True,
            notification_channels=set(),
            escalation_policy=None,
        )

        rule_dict = rule.to_dict()
        assert rule_dict["rule_id"] == "rule_id"
        assert rule_dict["name"] == "test_rule"
        assert rule_dict["severity"] == "warning"
