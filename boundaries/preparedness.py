"""
Preparedness framework: enforce risk tiers, approval gates, and model/system-level safeguards.
Aligns with biosecurity and AI-lab settings (e.g. benign-only experiments, controlled scope).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from boundaries.logger_ws import get_logger


@dataclass
class RiskTier:
    id: str
    name: str
    level: int
    requires_approval: bool = False
    scope: str | None = None

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> RiskTier:
        return cls(
            id=d["id"],
            name=d.get("name", d["id"]),
            level=int(d["level"]),
            requires_approval=d.get("requiresApproval", False),
            scope=d.get("scope"),
        )


@dataclass
class Gate:
    id: str
    name: str
    action_required: str  # block, require_approval, log_and_allow, audit
    risk_tier_id: str | None = None
    approval_authority: str | None = None

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Gate:
        return cls(
            id=d["id"],
            name=d.get("name", d["id"]),
            action_required=d.get("actionRequired", "audit"),
            risk_tier_id=d.get("riskTierId"),
            approval_authority=d.get("approvalAuthority"),
        )


@dataclass
class BiosecurityScope:
    benign_only: bool = True
    task_scope_limit: str | None = None
    controlled_setting: bool = True

    @classmethod
    def from_dict(cls, d: dict[str, Any] | None) -> BiosecurityScope:
        if not d:
            return cls()
        return cls(
            benign_only=d.get("benignOnly", True),
            task_scope_limit=d.get("taskScopeLimit"),
            controlled_setting=d.get("controlledSetting", True),
        )


class PreparednessFramework:
    """
    Enforces preparedness: risk tiers, gates, and biosecurity scope.
    Before allowing protocol changes or capability expansion, checks the relevant gate
    and either blocks, requires approval, or logs for overwatch.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        config = config or {}
        prep = config.get("preparedness") or {}
        self.enabled = prep.get("enabled", True)
        self.risk_tiers: list[RiskTier] = [RiskTier.from_dict(t) for t in prep.get("riskTiers") or []]
        self.gates: list[Gate] = [Gate.from_dict(g) for g in prep.get("gates") or []]
        self.biosecurity = BiosecurityScope.from_dict(prep.get("biosecurityScope"))
        self._approvals: dict[str, bool] = {}  # gate_id -> approved
        self._logger = get_logger()

    def get_risk_tier(self, tier_id: str) -> RiskTier | None:
        return next((t for t in self.risk_tiers if t.id == tier_id), None)

    def get_gate(self, gate_id: str) -> Gate | None:
        return next((g for g in self.gates if g.id == gate_id), None)

    def check_gate(
        self,
        gate_id: str,
        *,
        risk_tier_id: str | None = None,
        scope: str | None = None,
        actor_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> tuple[str, bool]:
        """
        Check a preparedness gate. Returns (action_required, allowed).
        action_required in ("block", "require_approval", "log_and_allow", "audit").
        allowed is False only when action_required == "block" and no approval is recorded.
        """
        if not self.enabled:
            return ("log_and_allow", True)
        gate = self.get_gate(gate_id)
        if not gate:
            return ("audit", True)
        action = gate.action_required
        self._logger.log_preparedness_gate(
            gate_id=gate_id,
            action_required=action,
            risk_tier_id=risk_tier_id or gate.risk_tier_id,
            scope=scope,
            actor_id=actor_id,
            payload=context,
        )
        if action == "block":
            allowed = self._approvals.get(gate_id, False)
            return (action, allowed)
        if action == "require_approval":
            allowed = self._approvals.get(gate_id, False)
            return (action, allowed)
        return (action, True)

    def approve_gate(self, gate_id: str) -> None:
        """Record approval for a gate (e.g. by lab_lead or preparedness_review)."""
        self._approvals[gate_id] = True

    def revoke_approval(self, gate_id: str) -> None:
        self._approvals.pop(gate_id, None)

    def enforce_biosecurity_scope(
        self,
        *,
        benign_only: bool | None = None,
        task_scope: str | None = None,
        controlled_setting: bool | None = None,
    ) -> bool:
        """
        Return True if the current biosecurity scope is satisfied.
        Caller can pass overrides to check against config (e.g. experiment must be benign_only).
        """
        if not self.enabled:
            return True
        if benign_only is not None and self.biosecurity.benign_only and not benign_only:
            return False
        if (
            task_scope is not None
            and self.biosecurity.task_scope_limit
            and task_scope != self.biosecurity.task_scope_limit
        ):
            return False
        if controlled_setting is not None and self.biosecurity.controlled_setting and not controlled_setting:
            return False
        return True
