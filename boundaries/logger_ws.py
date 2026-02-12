"""
WebSocket-persistent logging for boundary, consent, and guardrail events.
Logs to file (persistent) and optionally broadcasts to WebSocket clients.
"""

from __future__ import annotations

import json
import os
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_global_logger: BoundaryEventLogger | None = None


class BoundaryEventLogger:
    """
    Persistent logger for boundary/consent/guardrail events.
    Writes to rotating log files and can push events to WebSocket subscribers.
    """

    EVENT_TYPES = frozenset(
        {
            "boundary_check",
            "boundary_violation",
            "consent_granted",
            "consent_denied",
            "consent_revoked",
            "refusal",
            "guardrail_triggered",
            "guardrail_overridden",
            "service_refused",
            "preparedness_gate",
            "overwatch_alert",
        }
    )

    def __init__(
        self,
        enabled: bool = True,
        persist_to_file: bool = True,
        log_dir: str | Path = "logs/boundaries",
        event_types: list[str] | None = None,
        ws_broadcast: Callable[[dict], Any] | None = None,
    ):
        self.enabled = enabled
        self.persist_to_file = persist_to_file
        self.log_dir = Path(log_dir)
        self._event_types = set(event_types) if event_types else self.EVENT_TYPES
        self._ws_broadcast = ws_broadcast
        if self.persist_to_file:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        self._file_handle = None
        self._today: str | None = None

    def _open_day_file(self) -> Path:
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        if self._today != today and self._file_handle:
            self._file_handle.close()
            self._file_handle = None
        self._today = today
        path = self.log_dir / f"boundary_events_{today}.ndjson"
        if self._file_handle is None:
            self._file_handle = open(path, "a", encoding="utf-8")
        return path

    def _emit(self, event: dict[str, Any]) -> None:
        if not self.enabled or event.get("eventType") not in self._event_types:
            return
        if self.persist_to_file:
            try:
                self._open_day_file()
                line = json.dumps(event, default=str) + "\n"
                self._file_handle.write(line)
                self._file_handle.flush()
            except OSError:
                pass
        if self._ws_broadcast:
            try:
                self._ws_broadcast(event)
            except Exception:
                pass

    def _event(
        self,
        event_type: str,
        severity: str,
        scope: str | None = None,
        actor_id: str | None = None,
        payload: dict | None = None,
    ) -> dict[str, Any]:
        return {
            "eventId": str(uuid.uuid4()),
            "timestamp": datetime.now(UTC).isoformat(),
            "eventType": event_type,
            "scope": scope,
            "actorId": actor_id,
            "payload": payload or {},
            "severity": severity,
        }

    def log_boundary_check(
        self, boundary_id: str, allowed: bool, scope: str | None = None, payload: dict | None = None
    ) -> None:
        self._emit(
            self._event(
                "boundary_check",
                "audit",
                scope=scope,
                payload={"boundaryId": boundary_id, "allowed": allowed, **(payload or {})},
            )
        )

    def log_boundary_violation(
        self, boundary_id: str, scope: str | None = None, actor_id: str | None = None, payload: dict | None = None
    ) -> None:
        self._emit(
            self._event(
                "boundary_violation",
                "warn",
                scope=scope,
                actor_id=actor_id,
                payload={"boundaryId": boundary_id, **(payload or {})},
            )
        )

    def log_consent_granted(self, consent_id: str, actor_id: str | None = None, payload: dict | None = None) -> None:
        self._emit(
            self._event(
                "consent_granted", "info", actor_id=actor_id, payload={"consentId": consent_id, **(payload or {})}
            )
        )

    def log_consent_denied(self, consent_id: str, actor_id: str | None = None, payload: dict | None = None) -> None:
        self._emit(
            self._event(
                "consent_denied", "audit", actor_id=actor_id, payload={"consentId": consent_id, **(payload or {})}
            )
        )

    def log_consent_revoked(self, consent_id: str, actor_id: str | None = None, payload: dict | None = None) -> None:
        self._emit(
            self._event(
                "consent_revoked", "info", actor_id=actor_id, payload={"consentId": consent_id, **(payload or {})}
            )
        )

    def log_refusal(
        self,
        refusal_id: str,
        scope: str | None = None,
        actor_id: str | None = None,
        trigger: str | None = None,
        reason: str | None = None,
        payload: dict | None = None,
    ) -> None:
        self._emit(
            self._event(
                "refusal",
                "audit",
                scope=scope,
                actor_id=actor_id,
                payload={
                    "refusalId": refusal_id,
                    "trigger": trigger,
                    "reason": reason,
                    **(payload or {}),
                },
            )
        )

    def log_service_refused(
        self, scope: str | None = None, actor_id: str | None = None, payload: dict | None = None
    ) -> None:
        self._emit(self._event("service_refused", "info", scope=scope, actor_id=actor_id, payload=payload or {}))

    def log_guardrail_triggered(
        self, guardrail_id: str, action: str, scope: str | None = None, payload: dict | None = None
    ) -> None:
        self._emit(
            self._event(
                "guardrail_triggered",
                "warn",
                scope=scope,
                payload={"guardrailId": guardrail_id, "action": action, **(payload or {})},
            )
        )

    def log_guardrail_overridden(
        self, guardrail_id: str, scope: str | None = None, actor_id: str | None = None, payload: dict | None = None
    ) -> None:
        self._emit(
            self._event(
                "guardrail_overridden",
                "audit",
                scope=scope,
                actor_id=actor_id,
                payload={"guardrailId": guardrail_id, **(payload or {})},
            )
        )

    def log_preparedness_gate(
        self,
        gate_id: str,
        action_required: str,
        risk_tier_id: str | None = None,
        scope: str | None = None,
        actor_id: str | None = None,
        payload: dict | None = None,
    ) -> None:
        self._emit(
            self._event(
                "preparedness_gate",
                "warn",
                scope=scope,
                actor_id=actor_id,
                payload={
                    "gateId": gate_id,
                    "actionRequired": action_required,
                    "riskTierId": risk_tier_id,
                    **(payload or {}),
                },
            )
        )

    def log_overwatch_alert(self, alert_type: str, scope: str | None = None, payload: dict | None = None) -> None:
        self._emit(
            self._event("overwatch_alert", "warn", scope=scope, payload={"alertType": alert_type, **(payload or {})})
        )

    def set_ws_broadcast(self, fn: Callable[[dict], Any] | None) -> None:
        self._ws_broadcast = fn

    def close(self) -> None:
        if self._file_handle:
            self._file_handle.close()
            self._file_handle = None


def get_logger() -> BoundaryEventLogger:
    """Return the global boundary event logger (creates with defaults if not set)."""
    global _global_logger
    if _global_logger is None:
        _global_logger = BoundaryEventLogger(
            enabled=True,
            persist_to_file=True,
            log_dir=os.environ.get("BOUNDARY_LOG_DIR", "logs/boundaries"),
        )
    return _global_logger


def set_global_logger(logger: BoundaryEventLogger | None) -> None:
    global _global_logger
    _global_logger = logger
