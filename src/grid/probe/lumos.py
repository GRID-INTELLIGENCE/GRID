"""Lumos orchestrator — 6-phase ecosystem illumination pipeline.

Implements the lumos command routine as a programmatic Python pipeline
that can be executed from the probe API or invoked by MCP tooling.

Phases:
1. PROBE   — read-only signal collection from ecosystem bridge
2. QUANTIFY — compute PATH scores (health, trust, drift, fail, momentum)
3. SORT    — rank entities and assign tiers (CLEAR, WATCH, ACT, URGENT)
4. GUIDE   — generate tier-specific sweep protocols
5. EXECUTE — dependency-ordered sweep with verification gates
6. EVOLVE  — evolution cycle advancement if all gates pass

The lumos orchestrator merges three parallel data streams:
- Probe internal: governance entity map, coverage scores, findings
- Echoes process: audit events, enforcement state, precedent tracking
- Seeds process: repo health scores, ecosystem snapshots
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from grid.probe.ecosystem import (
    EcosystemBridge,
    LumosVerdict,
)
from grid.probe.models import ProbeReport

logger = logging.getLogger(__name__)


# ── PATH Score Weights (from lumos.md) ──

PATH_WEIGHTS = {
    "health": 0.30,
    "trust": 0.25,
    "drift": 0.20,
    "fail": 0.15,
    "momentum": 0.10,
}


class LumosPhase(StrEnum):
    """Execution phases of the lumos pipeline."""

    PROBE = "probe"
    QUANTIFY = "quantify"
    SORT = "sort"
    GUIDE = "guide"
    EXECUTE = "execute"
    EVOLVE = "evolve"


class SweepProtocol(StrEnum):
    """Tier-specific sweep protocols from lumos GUIDE phase."""

    A_MONITOR = "A_MONITOR"  # CLEAR tier: light-touch monitoring
    B_WATCH = "B_WATCH"  # WATCH tier: active monitoring
    C_TRIAGE = "C_TRIAGE"  # ACT tier: targeted triage
    D_REMEDIATE = "D_REMEDIATE"  # ACT tier: active remediation
    E_STABILIZE = "E_STABILIZE"  # URGENT tier: stabilization
    F_EMERGENCY = "F_EMERGENCY"  # URGENT tier: emergency response


# ── Data Models ──


@dataclass(frozen=True, slots=True)
class PathScore:
    """A single PATH dimension score."""

    dimension: str
    raw_value: float  # 0-100
    weight: float
    weighted: float  # raw_value * weight
    evidence: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension": self.dimension,
            "raw_value": round(self.raw_value, 2),
            "weight": self.weight,
            "weighted": round(self.weighted, 2),
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True, slots=True)
class ScoredEntity:
    """An entity (repo, server, cluster) with its computed PATH score."""

    name: str
    entity_type: str  # "repo", "mcp-server", "cluster"
    path_score: float  # 0-100 composite
    tier: LumosVerdict
    dimensions: tuple[PathScore, ...]
    sweep_protocol: SweepProtocol | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "name": self.name,
            "entity_type": self.entity_type,
            "path_score": round(self.path_score, 2),
            "tier": self.tier.value,
            "dimensions": [d.to_dict() for d in self.dimensions],
        }
        if self.sweep_protocol:
            result["sweep_protocol"] = self.sweep_protocol.value
        return result


@dataclass(frozen=True, slots=True)
class SweepAction:
    """A concrete action from the GUIDE phase."""

    target: str
    protocol: SweepProtocol
    action: str
    priority: int  # 1=highest
    depends_on: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "protocol": self.protocol.value,
            "action": self.action,
            "priority": self.priority,
            "depends_on": list(self.depends_on),
        }


@dataclass(frozen=True, slots=True)
class GateResult:
    """Result of a verification gate in the EXECUTE phase."""

    gate_name: str
    passed: bool
    message: str
    timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_name": self.gate_name,
            "passed": self.passed,
            "message": self.message,
            "timestamp": self.timestamp or datetime.now().isoformat(),
        }


@dataclass(slots=True)
class LumosResult:
    """Complete result of a lumos pipeline execution."""

    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""
    phases_completed: list[LumosPhase] = field(default_factory=list)

    # Phase 1: PROBE
    probe_report: ProbeReport | None = None
    ecosystem_state: dict[str, Any] = field(default_factory=dict)

    # Phase 2: QUANTIFY
    composite_score: float = 0.0
    path_scores: list[PathScore] = field(default_factory=list)

    # Phase 3: SORT
    verdict: LumosVerdict = LumosVerdict.FAST_CLEAR
    scored_entities: list[ScoredEntity] = field(default_factory=list)

    # Phase 4: GUIDE
    sweep_actions: list[SweepAction] = field(default_factory=list)

    # Phase 5: EXECUTE
    gate_results: list[GateResult] = field(default_factory=list)
    execution_log: list[str] = field(default_factory=list)

    # Phase 6: EVOLVE
    evolution_eligible: bool = False
    evolution_message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at,
            "completed_at": self.completed_at or datetime.now().isoformat(),
            "phases_completed": [p.value for p in self.phases_completed],
            "composite_score": round(self.composite_score, 2),
            "verdict": self.verdict.value,
            "path_scores": [s.to_dict() for s in self.path_scores],
            "scored_entities": [e.to_dict() for e in self.scored_entities],
            "sweep_actions": [a.to_dict() for a in self.sweep_actions],
            "gate_results": [g.to_dict() for g in self.gate_results],
            "execution_log": self.execution_log,
            "evolution_eligible": self.evolution_eligible,
            "evolution_message": self.evolution_message,
            "ecosystem_state": self.ecosystem_state,
        }


# ── Orchestrator ──


class LumosOrchestrator:
    """6-phase lumos pipeline orchestrator.

    Usage:
        bridge = EcosystemBridge()
        # ... ingest data into bridge ...
        orchestrator = LumosOrchestrator(bridge)
        result = orchestrator.run_full()
        # or step-by-step:
        orchestrator.phase_probe(probe_report)
        orchestrator.phase_quantify()
        orchestrator.phase_sort()
        orchestrator.phase_guide()
        orchestrator.phase_execute()
        orchestrator.phase_evolve()
        result = orchestrator.result
    """

    def __init__(self, bridge: EcosystemBridge) -> None:
        self.bridge = bridge
        self.result = LumosResult()

    def run_full(self, probe_report: ProbeReport | None = None) -> LumosResult:
        """Execute the full 6-phase lumos pipeline.

        Args:
            probe_report: Optional pre-computed probe report. If None,
                a minimal report placeholder is used.

        Returns:
            Complete LumosResult with all phases.
        """
        logger.info("Starting lumos pipeline")
        self.phase_probe(probe_report)
        self.phase_quantify()
        self.phase_sort()
        self.phase_guide()
        self.phase_execute()
        self.phase_evolve()
        self.result.completed_at = datetime.now().isoformat()
        logger.info(
            "Lumos complete: score=%.1f, verdict=%s, %d actions",
            self.result.composite_score,
            self.result.verdict.value,
            len(self.result.sweep_actions),
        )
        return self.result

    # ── Phase 1: PROBE ──

    def phase_probe(self, probe_report: ProbeReport | None = None) -> None:
        """Phase 1: Read-only signal collection.

        Collects probe report + ecosystem bridge state into a unified
        signal set for scoring.
        """
        self.result.probe_report = probe_report
        self.result.ecosystem_state = self.bridge.to_dict()
        self.result.phases_completed.append(LumosPhase.PROBE)
        logger.info("Phase PROBE complete — signals collected")

    # ── Phase 2: QUANTIFY ──

    def phase_quantify(self) -> None:
        """Phase 2: Compute PATH scores.

        Formula: health×0.30 + trust×0.25 + (1-drift)×0.20 + (1-fail)×0.15 + momentum×0.10
        Each dimension scored 0-100.
        """
        health = self._score_health()
        trust = self._score_trust()
        drift = self._score_drift()
        fail = self._score_fail()
        momentum = self._score_momentum()

        scores = [health, trust, drift, fail, momentum]
        self.result.path_scores = scores
        self.result.composite_score = sum(s.weighted for s in scores)
        self.result.phases_completed.append(LumosPhase.QUANTIFY)
        logger.info("Phase QUANTIFY complete — composite=%.1f", self.result.composite_score)

    def _score_health(self) -> PathScore:
        """Health dimension: ecosystem overall score."""
        raw = 50.0  # default if no ecosystem data
        evidence: list[str] = []

        if self.bridge.ecosystem:
            raw = float(self.bridge.ecosystem.overall_score)
            evidence.append(f"Ecosystem overall: {self.bridge.ecosystem.overall_score}/100")
            evidence.append(f"Active repos: {self.bridge.ecosystem.active_repos}/{self.bridge.ecosystem.total_repos}")

        if self.result.probe_report:
            probe_score = self.result.probe_report.aggregate_score * 100
            # Blend: 60% ecosystem, 40% probe
            raw = raw * 0.6 + probe_score * 0.4
            evidence.append(f"Probe score: {probe_score:.0f}/100")

        weight = PATH_WEIGHTS["health"]
        return PathScore("health", raw, weight, raw * weight, tuple(evidence))

    def _score_trust(self) -> PathScore:
        """Trust dimension: enforcement state + line audit cleanliness."""
        raw = 50.0
        evidence: list[str] = []

        if self.bridge.enforcement:
            enf = self.bridge.enforcement
            if enf.has_blocks:
                raw = 20.0
                evidence.append("BLOCKED precedents present")
            elif enf.has_restrictions:
                raw = 40.0
                evidence.append("RESTRICTED precedents present")
            elif enf.status == "normal":
                raw = 85.0
                evidence.append(f"Enforcement normal, {enf.total_active} observed")
            else:
                raw = 60.0
                evidence.append(f"Enforcement status: {enf.status}")

        if self.bridge.line_audit:
            if self.bridge.line_audit.clean:
                raw = min(raw + 10, 100)
                evidence.append("Line audit: CLEAN")
            else:
                penalty = min(self.bridge.line_audit.error_count * 10, 40)
                raw = max(raw - penalty, 0)
                evidence.append(
                    f"Line audit: {self.bridge.line_audit.error_count} errors, "
                    f"{self.bridge.line_audit.warning_count} warnings"
                )

        weight = PATH_WEIGHTS["trust"]
        return PathScore("trust", raw, weight, raw * weight, tuple(evidence))

    def _score_drift(self) -> PathScore:
        """Drift dimension: (1 - drift) — low drift is good."""
        drift_raw = 0.0
        evidence: list[str] = []

        # Structural drift from line audit
        if self.bridge.line_audit and not self.bridge.line_audit.clean:
            drift_raw += min(self.bridge.line_audit.error_count * 15, 50)
            evidence.append(f"Structural drift: {self.bridge.line_audit.error_count} findings")

        # Uncommitted changes drift
        if self.bridge.ecosystem:
            total_uncommitted = sum(r.uncommitted for r in self.bridge.ecosystem.repos)
            if total_uncommitted > 20:
                drift_raw += 20
                evidence.append(f"High uncommitted: {total_uncommitted} changes")
            elif total_uncommitted > 5:
                drift_raw += 10
                evidence.append(f"Moderate uncommitted: {total_uncommitted} changes")
            else:
                evidence.append(f"Low uncommitted: {total_uncommitted} changes")

        raw = max(100 - drift_raw, 0)  # Invert: low drift → high score
        weight = PATH_WEIGHTS["drift"]
        return PathScore("drift", raw, weight, raw * weight, tuple(evidence))

    def _score_fail(self) -> PathScore:
        """Fail dimension: (1 - fail_rate) — low failures is good."""
        fail_raw = 0.0
        evidence: list[str] = []

        stats = self.bridge.compute_audit_stats()
        total = stats.get("total", 0)
        if total > 0:
            fail_rate = stats["fail_rate"]
            fail_raw = fail_rate * 100
            evidence.append(f"Audit fail rate: {fail_rate:.1%} ({total} events)")
        else:
            evidence.append("No audit events — assuming clean")

        # Blocked precedents are high-severity failures
        blocked = self.bridge.get_blocked_precedents()
        if blocked:
            fail_raw = min(fail_raw + len(blocked) * 20, 100)
            evidence.append(f"{len(blocked)} blocked/restricted precedents")

        raw = max(100 - fail_raw, 0)  # Invert: low failure → high score
        weight = PATH_WEIGHTS["fail"]
        return PathScore("fail", raw, weight, raw * weight, tuple(evidence))

    def _score_momentum(self) -> PathScore:
        """Momentum dimension: activity signals showing forward progress."""
        raw = 50.0
        evidence: list[str] = []

        if self.bridge.ecosystem:
            # Recent activity boosts momentum
            active = self.bridge.ecosystem.active_repos
            total = self.bridge.ecosystem.total_repos
            if total > 0:
                activity_ratio = active / total
                raw = activity_ratio * 100
                evidence.append(f"Active repos: {active}/{total}")

        # Having a probe report means active development
        if self.result.probe_report:
            raw = min(raw + 10, 100)
            evidence.append("Probe report generated (active development)")

        weight = PATH_WEIGHTS["momentum"]
        return PathScore("momentum", raw, weight, raw * weight, tuple(evidence))

    # ── Phase 3: SORT ──

    def phase_sort(self) -> None:
        """Phase 3: Rank entities and assign tiers.

        Tiers: FAST_CLEAR (65-100), WATCH (50-64), ACT (35-49), URGENT (0-34)
        """
        # Global verdict from composite score
        self.result.verdict = self._classify_verdict(self.result.composite_score)

        # Score individual repos if ecosystem data available
        if self.bridge.ecosystem:
            for repo in self.bridge.ecosystem.repos:
                scored = self._score_repo_entity(repo)
                self.result.scored_entities.append(scored)

        # Sort by score ascending (worst first)
        self.result.scored_entities.sort(key=lambda e: e.path_score)
        self.result.phases_completed.append(LumosPhase.SORT)
        logger.info(
            "Phase SORT complete — verdict=%s, %d entities ranked",
            self.result.verdict.value,
            len(self.result.scored_entities),
        )

    def _score_repo_entity(self, repo: Any) -> ScoredEntity:
        """Score a single repo as a lumos entity."""
        # Simplified per-entity scoring
        health_raw = float(repo.health_score)
        uncommitted_penalty = min(repo.uncommitted * 2, 20)
        issue_penalty = len(repo.issues) * 5
        score = max(health_raw - uncommitted_penalty - issue_penalty, 0)

        tier = self._classify_verdict(score)
        protocol = self._tier_to_protocol(tier)

        dimensions = (
            PathScore("health", health_raw, 1.0, health_raw, (f"Score: {repo.health_score}",)),
            PathScore(
                "uncommitted",
                float(100 - uncommitted_penalty),
                1.0,
                float(100 - uncommitted_penalty),
                (f"{repo.uncommitted} uncommitted",),
            ),
        )

        return ScoredEntity(
            name=repo.name,
            entity_type="repo",
            path_score=score,
            tier=tier,
            dimensions=dimensions,
            sweep_protocol=protocol,
        )

    @staticmethod
    def _classify_verdict(score: float) -> LumosVerdict:
        """Map a 0-100 score to a lumos verdict tier."""
        if score >= 65:
            return LumosVerdict.FAST_CLEAR
        if score >= 50:
            return LumosVerdict.WATCH
        if score >= 35:
            return LumosVerdict.ACT
        return LumosVerdict.URGENT

    @staticmethod
    def _tier_to_protocol(tier: LumosVerdict) -> SweepProtocol:
        """Map verdict tier to default sweep protocol."""
        return {
            LumosVerdict.FAST_CLEAR: SweepProtocol.A_MONITOR,
            LumosVerdict.WATCH: SweepProtocol.B_WATCH,
            LumosVerdict.ACT: SweepProtocol.C_TRIAGE,
            LumosVerdict.URGENT: SweepProtocol.E_STABILIZE,
        }[tier]

    # ── Phase 4: GUIDE ──

    def phase_guide(self) -> None:
        """Phase 4: Generate tier-specific sweep actions.

        Creates concrete, prioritized actions based on entity scores
        and sweep protocols.
        """
        priority = 1
        for entity in self.result.scored_entities:
            if entity.tier == LumosVerdict.URGENT:
                self.result.sweep_actions.append(
                    SweepAction(
                        target=entity.name,
                        protocol=SweepProtocol.E_STABILIZE,
                        action=f"Stabilize {entity.name}: investigate failing health ({entity.path_score:.0f})",
                        priority=priority,
                    )
                )
                priority += 1
            elif entity.tier == LumosVerdict.ACT:
                self.result.sweep_actions.append(
                    SweepAction(
                        target=entity.name,
                        protocol=SweepProtocol.C_TRIAGE,
                        action=f"Triage {entity.name}: address degraded score ({entity.path_score:.0f})",
                        priority=priority,
                    )
                )
                priority += 1
            elif entity.tier == LumosVerdict.WATCH:
                self.result.sweep_actions.append(
                    SweepAction(
                        target=entity.name,
                        protocol=SweepProtocol.B_WATCH,
                        action=f"Monitor {entity.name}: watchlist score ({entity.path_score:.0f})",
                        priority=priority,
                    )
                )
                priority += 1

        self.result.phases_completed.append(LumosPhase.GUIDE)
        logger.info("Phase GUIDE complete — %d sweep actions", len(self.result.sweep_actions))

    # ── Phase 5: EXECUTE ──

    def phase_execute(self) -> None:
        """Phase 5: Dependency-ordered sweep execution with verification gates.

        In programmatic mode, this validates that sweep actions are
        properly ordered and all verification gates pass. Actual
        remediation is deferred to the MCP tool layer.
        """
        # Gate 1: Composite score sanity
        self.result.gate_results.append(
            GateResult(
                gate_name="composite_score_valid",
                passed=0 <= self.result.composite_score <= 100,
                message=f"Composite score {self.result.composite_score:.1f} in valid range",
            )
        )

        # Gate 2: No blocked precedents
        blocked = self.bridge.get_blocked_precedents()
        self.result.gate_results.append(
            GateResult(
                gate_name="no_blocked_precedents",
                passed=len(blocked) == 0,
                message=f"{len(blocked)} blocked precedents" if blocked else "No blocked precedents",
            )
        )

        # Gate 3: Ecosystem health above minimum
        min_health = 35
        ecosystem_ok = True
        if self.bridge.ecosystem:
            ecosystem_ok = self.bridge.ecosystem.overall_score >= min_health
        self.result.gate_results.append(
            GateResult(
                gate_name="ecosystem_minimum_health",
                passed=ecosystem_ok,
                message=f"Ecosystem score {self.bridge.ecosystem.overall_score if self.bridge.ecosystem else 'N/A'} "
                f">= {min_health}",
            )
        )

        # Gate 4: Line audit clean
        line_ok = self.bridge.line_audit is None or self.bridge.line_audit.clean
        self.result.gate_results.append(
            GateResult(
                gate_name="line_audit_clean",
                passed=line_ok,
                message=self.bridge.line_audit.summary if self.bridge.line_audit else "No line audit data",
            )
        )

        # Log execution results
        all_passed = all(g.passed for g in self.result.gate_results)
        self.result.execution_log.append(
            f"Executed {len(self.result.gate_results)} verification gates: "
            f"{'ALL PASSED' if all_passed else 'SOME FAILED'}"
        )

        self.result.phases_completed.append(LumosPhase.EXECUTE)
        logger.info(
            "Phase EXECUTE complete — %d gates, %s",
            len(self.result.gate_results),
            "all passed" if all_passed else "failures detected",
        )

    # ── Phase 6: EVOLVE ──

    def phase_evolve(self) -> None:
        """Phase 6: Evolution cycle advancement.

        Checks if all conditions are met for evolution promotion:
        - All verification gates passed
        - Composite score >= 65 (FAST_CLEAR tier)
        - No URGENT entities
        """
        all_gates_pass = all(g.passed for g in self.result.gate_results)
        score_sufficient = self.result.composite_score >= 65
        no_urgent = not any(e.tier == LumosVerdict.URGENT for e in self.result.scored_entities)

        eligible = all_gates_pass and score_sufficient and no_urgent

        self.result.evolution_eligible = eligible
        if eligible:
            self.result.evolution_message = (
                f"Evolution eligible: score={self.result.composite_score:.1f}, "
                f"verdict={self.result.verdict.value}, all gates passed"
            )
        else:
            reasons = []
            if not all_gates_pass:
                failed = [g.gate_name for g in self.result.gate_results if not g.passed]
                reasons.append(f"failed gates: {', '.join(failed)}")
            if not score_sufficient:
                reasons.append(f"score {self.result.composite_score:.1f} < 65")
            if not no_urgent:
                urgent = [e.name for e in self.result.scored_entities if e.tier == LumosVerdict.URGENT]
                reasons.append(f"urgent entities: {', '.join(urgent)}")
            self.result.evolution_message = f"Evolution blocked: {'; '.join(reasons)}"

        self.result.phases_completed.append(LumosPhase.EVOLVE)
        logger.info("Phase EVOLVE complete — eligible=%s", eligible)
