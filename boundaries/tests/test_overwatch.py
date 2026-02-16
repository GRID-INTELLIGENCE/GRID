"""Unit tests for Overwatch: ingest_event, escalation, persistAlerts, wrap_logger_with_overwatch."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from boundaries.logger_ws import BoundaryEventLogger
from boundaries.overwatch import Overwatch, wrap_logger_with_overwatch


def _overwatch_config(
    enabled: bool = True,
    alert_on: list[str] | None = None,
    threshold_count: int = 3,
    window_minutes: int = 60,
    persist_alerts: bool = True,
    log_dir: str | None = None,
) -> dict:
    if log_dir is None:
        log_dir = tempfile.mkdtemp(prefix="overwatch_test_")
    return {
        "overwatch": {
            "enabled": enabled,
            "logDir": log_dir,
            "alertOn": alert_on
            or [
                "boundary_violation",
                "guardrail_triggered",
                "preparedness_gate",
                "service_refused",
            ],
            "escalation": {
                "thresholdCount": threshold_count,
                "windowMinutes": window_minutes,
                "notifyChannels": [],
            },
            "persistAlerts": persist_alerts,
        },
    }


class TestOverwatchIngestEvent(unittest.TestCase):
    @patch("boundaries.overwatch.get_logger")
    def test_disabled_ignores_events(self, mock_get_logger: MagicMock) -> None:
        mock_get_logger.return_value = MagicMock()
        config = _overwatch_config(enabled=False, persist_alerts=False)
        ow = Overwatch(config)
        alerts: list[dict] = []
        ow.register_handler(alerts.append)
        ow.ingest_event({"eventType": "preparedness_gate", "eventId": "e1", "payload": {}})
        self.assertEqual(len(alerts), 0)

    @patch("boundaries.overwatch.get_logger")
    def test_skips_overwatch_alert_feedback(self, mock_get_logger: MagicMock) -> None:
        mock_get_logger.return_value = MagicMock()
        config = _overwatch_config(persist_alerts=False)
        ow = Overwatch(config)
        alerts: list[dict] = []
        ow.register_handler(alerts.append)
        ow.ingest_event({"eventType": "overwatch_alert", "payload": {}})
        self.assertEqual(len(alerts), 0)

    @patch("boundaries.overwatch.get_logger")
    def test_ignores_event_type_not_in_alert_on(self, mock_get_logger: MagicMock) -> None:
        mock_get_logger.return_value = MagicMock()
        config = _overwatch_config(alert_on=["boundary_violation"], persist_alerts=False)
        ow = Overwatch(config)
        alerts: list[dict] = []
        ow.register_handler(alerts.append)
        ow.ingest_event({"eventType": "consent_granted", "eventId": "e1"})
        self.assertEqual(len(alerts), 0)

    @patch("boundaries.overwatch.get_logger")
    def test_emits_single_alert_for_alert_on_type(self, mock_get_logger: MagicMock) -> None:
        mock_get_logger.return_value = MagicMock()
        config = _overwatch_config(persist_alerts=False)
        ow = Overwatch(config)
        alerts: list[dict] = []
        ow.register_handler(alerts.append)
        ow.ingest_event(
            {
                "eventType": "preparedness_gate",
                "eventId": "e1",
                "scope": "exp",
                "actorId": "model",
                "payload": {"x": 1},
            }
        )
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].get("eventType"), "overwatch_alert")
        self.assertEqual(alerts[0]["payload"]["alertType"], "single")
        self.assertEqual(alerts[0]["payload"]["sourceEventType"], "preparedness_gate")
        self.assertEqual(alerts[0]["payload"]["scope"], "exp")
        self.assertEqual(alerts[0]["payload"]["payload"], {"x": 1})

    @patch("boundaries.overwatch.get_logger")
    def test_escalation_after_threshold(self, mock_get_logger: MagicMock) -> None:
        mock_get_logger.return_value = MagicMock()
        config = _overwatch_config(threshold_count=2, window_minutes=60, persist_alerts=False)
        ow = Overwatch(config)
        alerts: list[dict] = []
        ow.register_handler(alerts.append)
        ow.ingest_event({"eventType": "boundary_violation", "eventId": "e1"})
        ow.ingest_event({"eventType": "boundary_violation", "eventId": "e2"})
        single_alerts = [a for a in alerts if a.get("payload", {}).get("alertType") == "single"]
        escalation_alerts = [a for a in alerts if a.get("payload", {}).get("alertType") == "escalation"]
        self.assertEqual(len(single_alerts), 2)
        self.assertEqual(len(escalation_alerts), 1)
        self.assertEqual(escalation_alerts[0]["payload"]["sourceEventType"], "boundary_violation")
        self.assertEqual(escalation_alerts[0]["payload"]["count"], 2)
        self.assertEqual(escalation_alerts[0]["payload"]["windowMinutes"], 60)


class TestOverwatchPersistAlerts(unittest.TestCase):
    @patch("boundaries.overwatch.get_logger")
    def test_persists_single_alert_when_enabled(self, mock_get_logger: MagicMock) -> None:
        mock_get_logger.return_value = MagicMock()
        with tempfile.TemporaryDirectory(prefix="overwatch_test_") as tmp:
            config = _overwatch_config(log_dir=tmp, persist_alerts=True)
            ow = Overwatch(config)
            ow.ingest_event({"eventType": "service_refused", "eventId": "ev-123", "payload": {}})
            alerts_dir = Path(tmp) / "overwatch_alerts"
            self.assertTrue(alerts_dir.is_dir())
            files = list(alerts_dir.glob("alert_*.json"))
            self.assertEqual(len(files), 1)
            self.assertIn("ev-123", files[0].name)


class TestWrapLoggerWithOverwatch(unittest.TestCase):
    @patch("boundaries.overwatch.get_logger")
    def test_emit_forwards_to_overwatch(self, mock_get_logger: MagicMock) -> None:
        mock_get_logger.return_value = MagicMock()
        config = _overwatch_config(persist_alerts=False)
        ow = Overwatch(config)
        ingested: list[dict] = []
        ow.register_handler(lambda a: ingested.append(a))
        logger = BoundaryEventLogger(enabled=True, persist_to_file=False, log_dir=Path(tempfile.gettempdir()))
        wrap_logger_with_overwatch(logger, ow)
        event = {
            "eventId": "x",
            "timestamp": "2020-01-01T00:00:00Z",
            "eventType": "preparedness_gate",
            "severity": "warn",
            "payload": {},
        }
        logger._emit(event)
        self.assertEqual(len(ingested), 1)
        self.assertEqual(ingested[0]["payload"]["sourceEventType"], "preparedness_gate")

    @patch("boundaries.overwatch.get_logger")
    def test_emit_still_writes_to_file_when_persist_to_file_true(self, mock_get_logger: MagicMock) -> None:
        mock_get_logger.return_value = MagicMock()
        config = _overwatch_config(persist_alerts=False)
        ow = Overwatch(config)
        with tempfile.TemporaryDirectory() as tmp:
            log_dir = Path(tmp) / "boundary_logs"
            logger = BoundaryEventLogger(enabled=True, persist_to_file=True, log_dir=log_dir)
            wrap_logger_with_overwatch(logger, ow)
            event = {
                "eventId": "y",
                "timestamp": "2020-01-01T00:00:00Z",
                "eventType": "boundary_check",
                "severity": "audit",
                "payload": {},
            }
            logger._emit(event)
            logger.close()
            ndjson_files = list(log_dir.glob("*.ndjson"))
            self.assertEqual(len(ndjson_files), 1)
            content = ndjson_files[0].read_text()
            self.assertIn("boundary_check", content)
            self.assertIn("y", content)


if __name__ == "__main__":
    unittest.main()
