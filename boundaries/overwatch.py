"""
Overwatch: continuous monitoring and alerting on boundary, consent, guardrail, and preparedness events.
Consumes persistent logs (or WebSocket stream), applies escalation rules, and can persist alerts.
"""

from __future__ import annotations

import json
import threading
import time
from collections import deque
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from boundaries.logger_ws import get_logger


class Overwatch:
    """
    Monitors boundary/consent/guardrail/preparedness events, triggers alerts when
    configured event types occur, and escalates when threshold counts are exceeded in a time window.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        config = config or {}
        ow = config.get("overwatch") or {}
        self.enabled = ow.get("enabled", True)
        self.log_dir = Path(ow.get("logDir", "logs/boundaries"))
        self.alert_on = set(
            ow.get("alertOn")
            or [
                "boundary_violation",
                "guardrail_triggered",
                "preparedness_gate",
                "service_refused",
            ]
        )
        esc = ow.get("escalation") or {}
        self.threshold_count = esc.get("thresholdCount", 3)
        self.window_minutes = esc.get("windowMinutes", 60)
        self.notify_channels = list(esc.get("notifyChannels") or [])
        self.persist_alerts = ow.get("persistAlerts", True)
        self._logger = get_logger()
        self._event_buffer: deque[tuple[float, dict[str, Any]]] = deque(maxlen=10_000)
        self._alert_handlers: list[Callable[[dict[str, Any]], None]] = []
        self._alerts_dir: Path | None = None
        if self.persist_alerts:
            self._alerts_dir = self.log_dir / "overwatch_alerts"
            self._alerts_dir.mkdir(parents=True, exist_ok=True)

    def register_handler(self, fn: Callable[[dict[str, Any]], None]) -> None:
        """Register a callback for every overwatch alert (e.g. send to Slack, PagerDuty)."""
        self._alert_handlers.append(fn)

    def ingest_event(self, event: dict[str, Any]) -> None:
        """Ingest one boundary log event; check alert and escalation rules."""
        if not self.enabled:
            return
        event_type = event.get("eventType")
        if event_type == "overwatch_alert":
            return  # avoid re-ingesting our own alerts
        if event_type not in self.alert_on:
            return
        now = time.time()
        self._event_buffer.append((now, event))
        self._maybe_alert(event)
        self._maybe_escalate(event_type, now)

    def _maybe_alert(self, event: dict[str, Any]) -> None:
        """Emit a single-event overwatch alert and persist if configured."""
        alert = {
            "eventId": event.get("eventId"),
            "timestamp": datetime.now(UTC).isoformat(),
            "eventType": "overwatch_alert",
            "severity": "warn",
            "payload": {
                "alertType": "single",
                "sourceEventType": event.get("eventType"),
                "scope": event.get("scope"),
                "actorId": event.get("actorId"),
                "payload": event.get("payload"),
            },
        }
        self._logger.log_overwatch_alert("single", scope=event.get("scope"), payload=alert.get("payload"))
        if self.persist_alerts and self._alerts_dir:
            try:
                path = self._alerts_dir / f"alert_{event.get('eventId', '')}.json"
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(alert, f, default=str, indent=2)
            except OSError:
                pass
        for h in self._alert_handlers:
            try:
                h(alert)
            except Exception:
                pass

    def _maybe_escalate(self, event_type: str, now: float) -> None:
        """If same event_type occurs >= threshold_count in window_minutes, emit escalation alert."""
        window_sec = self.window_minutes * 60
        cutoff = now - window_sec
        count = sum(1 for t, e in self._event_buffer if t >= cutoff and e.get("eventType") == event_type)
        if count < self.threshold_count:
            return
        alert = {
            "eventId": None,
            "timestamp": datetime.now(UTC).isoformat(),
            "eventType": "overwatch_alert",
            "severity": "error",
            "payload": {
                "alertType": "escalation",
                "sourceEventType": event_type,
                "count": count,
                "windowMinutes": self.window_minutes,
                "notifyChannels": self.notify_channels,
            },
        }
        self._logger.log_overwatch_alert("escalation", payload=alert.get("payload"))
        if self.persist_alerts and self._alerts_dir:
            try:
                ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
                path = self._alerts_dir / f"escalation_{event_type}_{ts}.json"
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(alert, f, default=str, indent=2)
            except OSError:
                pass
        for h in self._alert_handlers:
            try:
                h(alert)
            except Exception:
                pass

    def start_tailing_logs(self, poll_interval_sec: float = 5.0) -> None:
        """
        Start a background thread that tails the latest NDJSON log file in log_dir
        and ingests new events into overwatch. Call from main after logger is configured.
        """
        if not self.enabled:
            return

        def tail():
            last_size = 0
            current_path: Path | None = None
            while True:
                try:
                    today = datetime.now(UTC).strftime("%Y-%m-%d")
                    path = self.log_dir / f"boundary_events_{today}.ndjson"
                    if not path.exists():
                        time.sleep(poll_interval_sec)
                        continue
                    if path != current_path:
                        current_path = path
                        last_size = 0
                    with open(path, encoding="utf-8") as f:
                        f.seek(last_size)
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                event = json.loads(line)
                                self.ingest_event(event)
                            except json.JSONDecodeError:
                                pass
                        last_size = f.tell()
                except OSError:
                    pass
                time.sleep(poll_interval_sec)

        thread = threading.Thread(target=tail, daemon=True)
        thread.start()


def wrap_logger_with_overwatch(logger: Any, overwatch: Overwatch) -> None:
    """
    After BoundaryEventLogger emits an event, also feed it to overwatch.
    Call this once after creating both logger and overwatch; then use the logger as usual.
    """
    original_emit = logger._emit

    def emit(event: dict[str, Any]) -> None:
        original_emit(event)
        overwatch.ingest_event(event)

    logger._emit = emit
