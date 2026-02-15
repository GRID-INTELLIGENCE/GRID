"""
Boundary engine: enforce boundaries, consent, and guardrails.
Integrates with refusal rights (right to say no) and WebSocket logging.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from boundaries.logger_ws import get_logger
from boundaries.refusal import RefusalRights, check_refusal


@dataclass
class Boundary:
    id: str
    name: str
    type: str
    enforcement: str  # hard, soft, audit
    rule: dict[str, Any] | None = None
    refusable: bool = True

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Boundary:
        return cls(
            id=d["id"],
            name=d.get("name", d["id"]),
            type=d["type"],
            enforcement=d.get("enforcement", "hard"),
            rule=d.get("rule"),
            refusable=d.get("refusable", True),
        )


@dataclass
class Consent:
    id: str
    name: str
    scope: str
    required: bool = False
    revocable_at_any_time: bool = True
    default_state: str = "pending"

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Consent:
        return cls(
            id=d["id"],
            name=d.get("name", d["id"]),
            scope=d["scope"],
            required=d.get("required", False),
            revocable_at_any_time=d.get("revocableAtAnyTime", True),
            default_state=d.get("defaultState", "pending"),
        )


@dataclass
class Guardrail:
    id: str
    name: str
    kind: str
    action: str  # block, warn, redact, log, require_consent
    condition: str | None = None
    overridable_by_refusal: bool = False

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Guardrail:
        return cls(
            id=d["id"],
            name=d.get("name", d["id"]),
            kind=d["kind"],
            action=d["action"],
            condition=d.get("condition"),
            overridable_by_refusal=d.get("overridableByRefusal", False),
        )


class BoundaryEngine:
    """
    Enforces boundaries, consent, and guardrails. Respects right to refuse:
    - Before enforcing a boundary/guardrail, check for refusal; if user refused, honour it where refusable.
    - Consent can be denied/revoked at any time (service can be refused by withholding/revoking consent).
    """

    def __init__(self, config: dict[str, Any] | None = None):
        config = config or {}
        self.refusal_rights = RefusalRights.from_config(config)
        self.boundaries: list[Boundary] = [Boundary.from_dict(b) for b in config.get("boundaries") or []]
        self.consents: list[Consent] = [Consent.from_dict(c) for c in config.get("consents") or []]
        self.guardrails: list[Guardrail] = [Guardrail.from_dict(g) for g in config.get("guardrails") or []]
        self._consent_state: dict[str, str] = {}  # consent_id -> granted | denied | revoked
        for c in self.consents:
            self._consent_state.setdefault(c.id, c.default_state)
        self._logger = get_logger()

    def check_boundary(
        self,
        boundary_id: str,
        subject: str,
        *,
        scope: str | None = None,
        actor_id: str | None = None,
    ) -> bool:
        """
        Check if subject is within boundary. Returns True if allowed.
        If boundary is refusable and user has refused, treat as allowed (honour refusal).
        """
        ref = check_refusal(trigger=boundary_id, scope=scope, rights=self.refusal_rights)
        if ref is not None:
            self._logger.log_boundary_check(
                boundary_id, allowed=True, scope=scope, payload={"reason": "refusal_honoured"}
            )
            return True
        boundary = next((b for b in self.boundaries if b.id == boundary_id), None)
        if not boundary:
            # Fail-closed: unknown boundary IDs are denied, not allowed.
            # This prevents typos or removed configs from silently granting access.
            self._logger.log_boundary_check(
                boundary_id, allowed=False, scope=scope,
                payload={"reason": "unknown_boundary_id"},
            )
            return False
        allowed = self._evaluate_rule(boundary.rule, subject)
        self._logger.log_boundary_check(boundary_id, allowed, scope=scope, payload={"subject": subject})
        if not allowed and boundary.enforcement == "hard":
            self._logger.log_boundary_violation(
                boundary_id, scope=scope, actor_id=actor_id, payload={"subject": subject}
            )
        return allowed

    def _evaluate_rule(self, rule: dict[str, Any] | None, subject: str) -> bool:
        if not rule:
            return True
        if rule.get("deny") and subject in (rule["deny"] or []):
            return False
        if rule.get("allow"):
            return subject in (rule["allow"] or [])
        return True

    def get_consent_state(self, consent_id: str) -> str:
        return self._consent_state.get(consent_id, "pending")

    def grant_consent(self, consent_id: str, actor_id: str | None = None) -> None:
        self._consent_state[consent_id] = "granted"
        self._logger.log_consent_granted(consent_id, actor_id=actor_id)

    def deny_consent(self, consent_id: str, actor_id: str | None = None) -> None:
        self._consent_state[consent_id] = "denied"
        self._logger.log_consent_denied(consent_id, actor_id=actor_id)

    def revoke_consent(self, consent_id: str, actor_id: str | None = None) -> None:
        self._consent_state[consent_id] = "revoked"
        self._logger.log_consent_revoked(consent_id, actor_id=actor_id)

    def require_consent(self, consent_id: str, *, actor_id: str | None = None) -> bool:
        """
        Require consent for an action. Returns True if consent is granted.
        Denial or revocation = service can be refused (returns False).
        """
        state = self.get_consent_state(consent_id)
        if state == "granted":
            return True
        return False

    def check_guardrail(
        self,
        guardrail_id: str,
        context: dict[str, Any] | None = None,
        *,
        scope: str | None = None,
        actor_id: str | None = None,
    ) -> tuple[str, bool]:
        """
        Check guardrail. Returns (action, overridden).
        If overridable_by_refusal and user refused, return (action, True) to indicate override.
        """
        guardrail = next((g for g in self.guardrails if g.id == guardrail_id), None)
        if not guardrail:
            # Fail-closed: unknown guardrail IDs trigger block, not silent pass.
            self._logger.log_guardrail_triggered(
                guardrail_id, "block", scope=scope,
                payload={"reason": "unknown_guardrail_id"},
            )
            return ("block", False)
        ref = check_refusal(trigger=guardrail_id, scope=scope, rights=self.refusal_rights)
        if ref is not None and guardrail.overridable_by_refusal:
            self._logger.log_guardrail_overridden(guardrail_id, scope=scope, actor_id=actor_id, payload=context)
            return (guardrail.action, True)
        self._logger.log_guardrail_triggered(guardrail_id, guardrail.action, scope=scope, payload=context)
        return (guardrail.action, False)
