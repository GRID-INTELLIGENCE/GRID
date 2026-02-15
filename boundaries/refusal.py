"""
Right to refuse: preserve the right to say no or refuse service at any instance.
Refusal can be exercised per-request, per-session, per-feature, per-service, or globally.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from boundaries.logger_ws import get_logger


class RefusalScope(StrEnum):
    REQUEST = "request"
    SESSION = "session"
    FEATURE = "feature"
    SERVICE = "service"
    GLOBAL = "global"


@dataclass
class RefusalRecord:
    """Record of a refusal event (right to say no)."""

    refusal_id: str
    scope: str
    actor_id: str | None
    trigger: str | None
    reason: str | None
    timestamp: str
    payload: dict[str, Any]


@dataclass
class RefusalRights:
    """
    Encodes the preserved right to refuse service at any instance.
    No justification is required when noJustificationRequired is True.
    """

    preserved: bool = True
    scope: str = "global"
    refusal_triggers: list[str] = field(default_factory=list)
    no_justification_required: bool = True
    _active_refusals: dict[str, RefusalRecord] = field(default_factory=dict, repr=False)

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> RefusalRights:
        rt = config.get("rightToRefuse") or {}
        return cls(
            preserved=rt.get("preserved", True),
            scope=rt.get("scope", "global"),
            refusal_triggers=rt.get("refusalTriggers") or [],
            no_justification_required=rt.get("noJustificationRequired", True),
        )

    def refuse_service(
        self,
        *,
        scope: str | None = None,
        actor_id: str | None = None,
        trigger: str | None = None,
        reason: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> RefusalRecord:
        """
        Exercise the right to refuse service. Call at any instance to refuse.
        Returns the refusal record and logs a service_refused event.
        """
        if not self.preserved:
            raise RuntimeError("Right to refuse is not preserved in current configuration.")
        refusal_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()
        record = RefusalRecord(
            refusal_id=refusal_id,
            scope=scope or self.scope,
            actor_id=actor_id,
            trigger=trigger,
            reason=reason if not self.no_justification_required else None,
            timestamp=now,
            payload=payload or {},
        )
        self._active_refusals[refusal_id] = record
        logger = get_logger()
        logger.log_refusal(
            refusal_id=refusal_id,
            scope=record.scope,
            actor_id=actor_id,
            trigger=trigger,
            reason=reason,
            payload=payload,
        )
        return record

    def check_refusal(self, trigger: str | None = None, scope: str | None = None) -> RefusalRecord | None:
        """Check if there is an active refusal for the given trigger/scope."""
        scope = scope or self.scope
        for r in self._active_refusals.values():
            if (trigger and r.trigger == trigger) or (r.scope == scope and not trigger):
                return r
        return None

    def clear_refusal(self, refusal_id: str) -> bool:
        """Clear a specific refusal (e.g. after session end)."""
        if refusal_id in self._active_refusals:
            del self._active_refusals[refusal_id]
            return True
        return False


def refuse_service(
    scope: str | None = None,
    actor_id: str | None = None,
    trigger: str | None = None,
    reason: str | None = None,
    payload: dict[str, Any] | None = None,
    rights: RefusalRights | None = None,
) -> RefusalRecord:
    """
    Convenience: exercise right to refuse service using global or provided RefusalRights.
    """
    if rights is None:
        rights = RefusalRights()
    return rights.refuse_service(
        scope=scope,
        actor_id=actor_id,
        trigger=trigger,
        reason=reason,
        payload=payload,
    )


def check_refusal(
    trigger: str | None = None, scope: str | None = None, rights: RefusalRights | None = None
) -> RefusalRecord | None:
    """Check if service was refused for the given trigger/scope."""
    if rights is None:
        rights = RefusalRights()
    return rights.check_refusal(trigger=trigger, scope=scope)
