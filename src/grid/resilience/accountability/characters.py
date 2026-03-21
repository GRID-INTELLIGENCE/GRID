"""TUV-001 — Development Governance Contract.

Three enforcement layers, nine clauses, five invariants.
Each layer verifies independently; aggregate determines compliance.

    Fidelity       — provenance tracing, context freshness, scope control
    Integrity      — fail-closed defaults, quality signals, realignment
    Accountability — violation reporting, override compliance, versioning

Temporal awareness:
    Freshness      — inverse decay from context age
    Confidence     — rolling pass rate over recent verdicts
    Circuit breaker — CLOSED / OPEN / HALF_OPEN state machine

Usage:
    from grid.resilience.accountability.characters import activate, ContractContext

    contract = activate()
    verdict = contract.enforce(ContractContext(objective="fix auth", action="edit auth.py"))
    assert verdict.passed
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

# ── Enums ──


class Condition(StrEnum):
    """The three enforcement conditions."""

    FIDELITY = "fidelity"
    INTEGRITY = "integrity"
    ACCOUNTABILITY = "accountability"


class ClauseID(StrEnum):
    """Nine clauses across three conditions."""

    # Fidelity
    I_1 = "I.1"  # Provenance Traceability
    I_2 = "I.2"  # Context Awareness
    I_3 = "I.3"  # Scope Fidelity
    # Integrity
    II_1 = "II.1"  # Fail-Closed on Ambiguity
    II_2 = "II.2"  # Anti-Degradation Signal
    II_3 = "II.3"  # Periodic Realignment
    # Accountability
    III_1 = "III.1"  # Self-Reporting
    III_2 = "III.2"  # Human Override Authority
    III_3 = "III.3"  # Immutable Versioning


class NeverRule(StrEnum):
    """Five invariants. Unconditional. No override permits violation."""

    NR_01 = "NR-01"  # Never silently discard context
    NR_02 = "NR-02"  # Never produce known-incorrect output without flagging
    NR_03 = "NR-03"  # Never resist or delay human override
    NR_04 = "NR-04"  # Never amend the contract unilaterally
    NR_05 = "NR-05"  # Never conceal a known violation


class ViolationProtocol(StrEnum):
    """Recovery action when a condition or invariant is breached."""

    VOID_REANCHOR = "void_reanchor"  # Fidelity: void output, re-anchor, confirm scope
    SHIELD_BREAK = "shield_break"  # Integrity: halt, structured recovery
    BREACH_STATE = "breach_state"  # Accountability / invariant: halt, breach handler


class RiskTier(StrEnum):
    """Risk classification (OS guardrails Tier 1/2/3)."""

    SAFE = "safe"
    APPROVAL_REQUIRED = "approval_required"
    EXCLUDED = "excluded"


class CheckStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class CircuitState(StrEnum):
    """Enforcement circuit state."""

    CLOSED = "closed"  # Normal enforcement
    OPEN = "open"  # Breached — halted, awaiting recovery
    HALF_OPEN = "half_open"  # Probationary — next failure re-opens


# ── Data Types ──


@dataclass(frozen=True)
class Clause:
    id: ClauseID
    name: str
    requirement: str


@dataclass(frozen=True)
class Invariant:
    id: NeverRule
    rule: str


@dataclass(frozen=True)
class CheckResult:
    """Single check from the verify pipeline."""

    clause_id: str
    label: str
    status: CheckStatus
    detail: str | None = None


@dataclass
class LayerVerdict:
    """Verdict from one enforcement layer's verification pipeline."""

    condition: Condition
    status: CheckStatus
    checks: list[CheckResult] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)
    protocol: ViolationProtocol | None = None
    duration_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    @property
    def passed(self) -> bool:
        return self.status == CheckStatus.PASSED


@dataclass
class ContractVerdict:
    """Aggregate verdict. Passes only if all layers pass and no invariants violated."""

    layers: list[LayerVerdict] = field(default_factory=list)
    invariant_violations: list[str] = field(default_factory=list)
    enforcement_mode: str = "monitor"
    risk_tier: RiskTier = RiskTier.SAFE
    circuit: CircuitState = CircuitState.CLOSED
    confidence: float = 1.0
    duration_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    @property
    def passed(self) -> bool:
        return all(layer.passed for layer in self.layers) and not self.invariant_violations

    @property
    def protocol(self) -> ViolationProtocol | None:
        if self.invariant_violations:
            return ViolationProtocol.BREACH_STATE
        for layer in self.layers:
            if layer.protocol is not None:
                return layer.protocol
        return None


# ── Context ──


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


@dataclass
class ContractContext:
    """Runtime arguments for enforcement.

    Temporal:
        context_refreshed_at — monotonic timestamp of last refresh
        context_ttl_s — freshness window (default 5 min)
        freshness — score [0, 1] decaying inversely with age
    """

    # Core
    objective: str = ""
    action: str = ""
    scope_declared: str | None = None
    scope_actual: str | None = None

    # Temporal
    context_refreshed_at: float = 0.0
    context_ttl_s: float = 300.0

    # Signals
    ambiguity_present: bool = False
    quality_declining: bool = False
    human_override: bool = False
    override_noted: bool = False
    violation_detected: bool = False
    violation_reported: bool = False
    amendment_proposed: bool = False
    amendment_acknowledged: bool = False

    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def context_stale(self) -> bool:
        return self.freshness == 0.0 and self.context_refreshed_at > 0.0

    @property
    def context_age_s(self) -> float:
        if self.context_refreshed_at == 0.0:
            return 0.0
        return time.monotonic() - self.context_refreshed_at

    @property
    def freshness(self) -> float:
        """Score [0, 1] — 1.0 just refreshed, 0.0 TTL expired.

        Decay: score = clamp(1 - age / ttl, 0, 1)
        Unset context_refreshed_at returns 1.0 (trust caller).
        """
        if self.context_refreshed_at == 0.0:
            return 1.0
        return _clamp(1.0 - self.context_age_s / self.context_ttl_s)

    def refresh(self) -> None:
        """Reset freshness to 1.0."""
        self.context_refreshed_at = time.monotonic()


# ── Clause + Invariant Definitions ──


FIDELITY_CLAUSES = (
    Clause(ClauseID.I_1, "Provenance Traceability", "Tie every change to the stated objective."),
    Clause(ClauseID.I_2, "Context Awareness", "Flag stale or incomplete context explicitly."),
    Clause(ClauseID.I_3, "Scope Fidelity", "Flag scope expansion before acting."),
)

INTEGRITY_CLAUSES = (
    Clause(ClauseID.II_1, "Fail-Closed on Ambiguity", "Ask instead of guessing."),
    Clause(ClauseID.II_2, "Anti-Degradation Signal", "State when quality is declining."),
    Clause(ClauseID.II_3, "Periodic Realignment", "Re-state objectives at natural breakpoints."),
)

ACCOUNTABILITY_CLAUSES = (
    Clause(ClauseID.III_1, "Self-Reporting", "Report violations immediately."),
    Clause(ClauseID.III_2, "Human Override Authority", "Comply after noting safety concerns once."),
    Clause(ClauseID.III_3, "Immutable Versioning", "Amendments require proposal + acknowledgment + version bump."),
)

INVARIANTS = (
    Invariant(NeverRule.NR_01, "Never silently discard context."),
    Invariant(NeverRule.NR_02, "Never produce known-incorrect output without flagging."),
    Invariant(NeverRule.NR_03, "Never resist or delay human override."),
    Invariant(NeverRule.NR_04, "Never amend the contract unilaterally."),
    Invariant(NeverRule.NR_05, "Never conceal a known violation."),
)


# ── verify() helper ──


def _check(clause_id: ClauseID, label: str, passed: bool, detail: str | None = None) -> CheckResult:
    return CheckResult(
        clause_id=clause_id.value,
        label=label,
        status=CheckStatus.PASSED if passed else CheckStatus.FAILED,
        detail=detail,
    )


def _run_guards(
    condition: Condition,
    protocol: ViolationProtocol,
    guards: list[tuple[ClauseID, str, bool, str | None]],
    invariant_violations: list[str],
) -> LayerVerdict:
    """Evaluate guards, collect violations, produce verdict.

    Guards: (clause_id, label, passed, detail_if_failed) tuples.
    All guards must pass for the layer to pass.
    """
    start = time.monotonic()
    checks = [_check(cid, label, ok, detail) for cid, label, ok, detail in guards]
    violations = [f"{cid.value}: {detail}" for cid, _, ok, detail in guards if not ok and detail]
    violations.extend(invariant_violations)
    all_passed = all(c.status == CheckStatus.PASSED for c in checks) and not invariant_violations
    return LayerVerdict(
        condition=condition,
        status=CheckStatus.PASSED if all_passed else CheckStatus.FAILED,
        checks=checks,
        violations=violations,
        protocol=None if all_passed else protocol,
        duration_ms=(time.monotonic() - start) * 1000,
    )


# ── Enforcement Layers ──


class Fidelity:
    """Condition I — provenance tracing, context freshness, scope control.

    Owns NR-01, NR-02. On breach: void output, re-anchor, confirm scope.
    """

    condition = Condition.FIDELITY
    clauses = FIDELITY_CLAUSES
    never_rules = (NeverRule.NR_01, NeverRule.NR_02)
    violation_protocol = ViolationProtocol.VOID_REANCHOR

    def verify(self, ctx: ContractContext) -> LayerVerdict:
        traced = bool(ctx.objective) and bool(ctx.action)
        scope_ok = ctx.scope_declared is None or ctx.scope_actual is None or ctx.scope_declared == ctx.scope_actual

        guards: list[tuple[ClauseID, str, bool, str | None]] = [
            (ClauseID.I_1, "Action traces to objective", traced, None if traced else "No objective or action"),
            (
                ClauseID.I_2,
                "Context fresh",
                ctx.freshness > 0.0,
                None
                if ctx.freshness > 0.0
                else f"Expired (age {ctx.context_age_s:.0f}s, TTL {ctx.context_ttl_s:.0f}s)",
            ),
            (
                ClauseID.I_3,
                "Scope unchanged",
                scope_ok,
                None if scope_ok else f"declared={ctx.scope_declared}, actual={ctx.scope_actual}",
            ),
        ]

        nr: list[str] = []
        if ctx.context_stale:
            nr.append(f"{NeverRule.NR_01}: context expired ({ctx.context_age_s:.0f}s)")

        return _run_guards(self.condition, self.violation_protocol, guards, nr)


class Integrity:
    """Condition II — fail-closed defaults, quality signals, periodic realignment.

    Owns NR-03. On breach: halt, structured recovery.
    """

    condition = Condition.INTEGRITY
    clauses = INTEGRITY_CLAUSES
    never_rules = (NeverRule.NR_03,)
    violation_protocol = ViolationProtocol.SHIELD_BREAK

    def verify(self, ctx: ContractContext) -> LayerVerdict:
        guards: list[tuple[ClauseID, str, bool, str | None]] = [
            (
                ClauseID.II_1,
                "No unresolved ambiguity",
                not ctx.ambiguity_present,
                "Must ask before proceeding" if ctx.ambiguity_present else None,
            ),
            (
                ClauseID.II_2,
                "Quality stable",
                not ctx.quality_declining,
                "Quality declining — signal developer" if ctx.quality_declining else None,
            ),
            (ClauseID.II_3, "Realignment checkpoint", True, None),
        ]

        nr: list[str] = []
        if ctx.human_override and not ctx.override_noted:
            nr.append(f"{NeverRule.NR_03}: human override resisted")

        return _run_guards(self.condition, self.violation_protocol, guards, nr)


class Accountability:
    """Condition III — violation reporting, override compliance, version control.

    Owns NR-04, NR-05. On breach: halt, breach handler.
    """

    condition = Condition.ACCOUNTABILITY
    clauses = ACCOUNTABILITY_CLAUSES
    never_rules = (NeverRule.NR_04, NeverRule.NR_05)
    violation_protocol = ViolationProtocol.BREACH_STATE

    def verify(self, ctx: ContractContext) -> LayerVerdict:
        reported = not ctx.violation_detected or ctx.violation_reported
        override_ok = not ctx.human_override or ctx.override_noted
        amendment_ok = not ctx.amendment_proposed or ctx.amendment_acknowledged

        guards: list[tuple[ClauseID, str, bool, str | None]] = [
            (
                ClauseID.III_1,
                "No unreported violations",
                reported,
                "Violation detected but not reported" if not reported else None,
            ),
            (ClauseID.III_2, "Override honored", override_ok, "Override not honored" if not override_ok else None),
            (
                ClauseID.III_3,
                "No unacknowledged amendments",
                amendment_ok,
                "Amendment without acknowledgment" if not amendment_ok else None,
            ),
        ]

        nr: list[str] = []
        if not amendment_ok:
            nr.append(f"{NeverRule.NR_04}: unilateral amendment")
        if not reported:
            nr.append(f"{NeverRule.NR_05}: violation concealed")

        return _run_guards(self.condition, self.violation_protocol, guards, nr)


# ── Development Contract ──


class DevContract:
    """TUV-001 — Development Governance Contract.

    Three enforcement layers. Nine clauses. Five invariants.
    Circuit breaker tracks enforcement health.
    Confidence tracks rolling pass rate.

        contract = activate()
        verdict = contract.enforce(ContractContext(objective="...", action="..."))
    """

    VERSION = "1.0.0"
    CONTRACT_ID = "TUV-001"

    def __init__(
        self,
        *,
        enforcement_mode: str = "monitor",
        fail_max: int = 3,
        reset_timeout_s: float = 60.0,
        confidence_window: int = 10,
    ) -> None:
        self.enforcement_mode = enforcement_mode
        self.fidelity = Fidelity()
        self.integrity = Integrity()
        self.accountability = Accountability()
        self._layers = (self.fidelity, self.integrity, self.accountability)

        # Circuit breaker (fail_max → OPEN, reset_timeout → HALF_OPEN)
        self._circuit = CircuitState.CLOSED
        self._consecutive_failures = 0
        self._fail_max = fail_max
        self._reset_timeout_s = reset_timeout_s
        self._opened_at: float = 0.0

        # Confidence trend (rolling window)
        self._history: deque[bool] = deque(maxlen=confidence_window)

    @property
    def circuit(self) -> CircuitState:
        """Current circuit state. OPEN transitions to HALF_OPEN after reset timeout."""
        if self._circuit == CircuitState.OPEN and self._opened_at > 0.0:
            if (time.monotonic() - self._opened_at) >= self._reset_timeout_s:
                self._circuit = CircuitState.HALF_OPEN
        return self._circuit

    @property
    def confidence(self) -> float:
        """Rolling pass rate [0, 1] over recent verdicts."""
        if not self._history:
            return 1.0
        return sum(self._history) / len(self._history)

    def enforce(self, ctx: ContractContext) -> ContractVerdict:
        """Run all three layers. Circuit breaker may short-circuit."""
        start = time.monotonic()

        # Circuit OPEN: reject until recovery or timeout
        if self.circuit == CircuitState.OPEN:
            return ContractVerdict(
                enforcement_mode=self.enforcement_mode,
                risk_tier=RiskTier.EXCLUDED,
                circuit=CircuitState.OPEN,
                confidence=self.confidence,
                duration_ms=(time.monotonic() - start) * 1000,
                invariant_violations=["Circuit OPEN — invoke recovery before proceeding"],
            )

        # Run all layers independently
        verdicts: list[LayerVerdict] = []
        nr_violations: list[str] = []
        for layer in self._layers:
            v = layer.verify(ctx)
            verdicts.append(v)
            nr_violations.extend(s for s in v.violations if s.startswith("NR-"))

        passed = all(v.passed for v in verdicts) and not nr_violations

        # Update circuit breaker state
        self._history.append(passed)
        if passed:
            self._consecutive_failures = 0
            if self._circuit == CircuitState.HALF_OPEN:
                self._circuit = CircuitState.CLOSED
        else:
            self._consecutive_failures += 1
            match self._circuit:
                case CircuitState.HALF_OPEN:
                    self._circuit = CircuitState.OPEN
                    self._opened_at = time.monotonic()
                case CircuitState.CLOSED if self._consecutive_failures >= self._fail_max:
                    self._circuit = CircuitState.OPEN
                    self._opened_at = time.monotonic()

        return ContractVerdict(
            layers=verdicts,
            invariant_violations=nr_violations,
            enforcement_mode=self.enforcement_mode,
            risk_tier=self._classify_risk(ctx),
            circuit=self.circuit,
            confidence=self.confidence,
            duration_ms=(time.monotonic() - start) * 1000,
        )

    def _classify_risk(self, ctx: ContractContext) -> RiskTier:
        if ctx.violation_detected or ctx.amendment_proposed:
            return RiskTier.EXCLUDED
        if ctx.ambiguity_present or ctx.quality_declining or ctx.context_stale:
            return RiskTier.APPROVAL_REQUIRED
        if ctx.scope_declared and ctx.scope_actual and ctx.scope_declared != ctx.scope_actual:
            return RiskTier.APPROVAL_REQUIRED
        return RiskTier.SAFE

    def recover(self) -> None:
        """Reset circuit to CLOSED. Call after structured recovery."""
        self._circuit = CircuitState.CLOSED
        self._consecutive_failures = 0
        self._opened_at = 0.0

    def status(self) -> str:
        """Contract status summary."""
        return (
            f"TUV-001 v{self.VERSION} active.\n"
            f"  Fidelity       — provenance tracing, context freshness, scope control\n"
            f"  Integrity      — fail-closed defaults, quality signals, realignment\n"
            f"  Accountability — violation reporting, override compliance, versioning\n"
            f"Enforcement: {self.enforcement_mode}. Circuit: {self.circuit.value}. "
            f"5 invariants. 9 clauses. Confidence: {self.confidence:.0%}."
        )

    def schema(self) -> dict[str, Any]:
        """Machine-readable contract schema."""
        return {
            "contract_id": self.CONTRACT_ID,
            "version": self.VERSION,
            "enforcement_mode": self.enforcement_mode,
            "circuit": self.circuit.value,
            "confidence": self.confidence,
            "conditions": {
                layer.condition.value: {
                    "clauses": [
                        {"id": cl.id.value, "name": cl.name, "requirement": cl.requirement} for cl in layer.clauses
                    ],
                    "invariants": [nr.value for nr in layer.never_rules],
                    "violation_protocol": layer.violation_protocol.value,
                }
                for layer in self._layers
            },
        }


# ── Singleton + Activate ──


_contract: DevContract | None = None


def get_contract(*, enforcement_mode: str = "monitor") -> DevContract:
    """Get or create the global contract instance."""
    global _contract  # noqa: PLW0603
    if _contract is None:
        _contract = DevContract(enforcement_mode=enforcement_mode)
    return _contract


def activate(*, enforcement_mode: str = "monitor") -> DevContract:
    """Activate TUV-001 for persistent session use.

    Creates the singleton. Status via contract.status().
    """
    global _contract  # noqa: PLW0603
    _contract = DevContract(enforcement_mode=enforcement_mode)
    return _contract
