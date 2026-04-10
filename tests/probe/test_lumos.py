"""Tests for the lumos orchestrator — 6-phase ecosystem illumination pipeline."""

from __future__ import annotations

import pytest

from grid.probe.ecosystem import (
    AuditStatus,
    EcosystemBridge,
    LumosVerdict,
)
from grid.probe.lumos import (
    GateResult,
    LumosOrchestrator,
    LumosPhase,
    LumosResult,
    PathScore,
    ScoredEntity,
    SweepAction,
    SweepProtocol,
)
from grid.probe.models import ProbeReport

# ── Fixtures ──


@pytest.fixture
def healthy_bridge() -> EcosystemBridge:
    """Bridge with all-healthy ecosystem data."""
    bridge = EcosystemBridge()
    bridge.ingest_audit_events(
        [
            {
                "source": "grid-server",
                "tool": "validate_envelope",
                "status": "success",
                "timestamp": "2026-04-09T06:00:00Z",
                "durationMs": 10,
            },
            {
                "source": "seeds-server",
                "tool": "ecosystem_scan",
                "status": "success",
                "timestamp": "2026-04-09T06:01:00Z",
                "durationMs": 5,
            },
        ]
    )
    bridge.ingest_enforcement(
        {
            "status": "normal",
            "totalActive": 2,
            "byLevel": {"observed": 2, "flagged": 0, "restricted": 0, "blocked": 0},
            "recentPrecedents": [
                {
                    "id": "p1",
                    "source": "test",
                    "tool": "t",
                    "category": "c",
                    "occurrences": 1,
                    "level": "observed",
                    "lastSeen": "2026-04-09T00:00:00Z",
                },
            ],
        }
    )
    bridge.ingest_ecosystem(
        {
            "summary": {"overallScore": 88, "totalRepos": 5, "active": 5, "stale": 0},
            "repos": [
                {
                    "name": "GRID",
                    "healthScore": 90,
                    "branch": "main",
                    "uncommitted": 2,
                    "lastCommit": "1h ago",
                    "issues": [],
                    "stack": "Python",
                },
                {
                    "name": "afloat",
                    "healthScore": 100,
                    "branch": "hogsmade",
                    "uncommitted": 0,
                    "lastCommit": "1h ago",
                    "issues": [],
                    "stack": "TypeScript",
                },
                {
                    "name": "echoes",
                    "healthScore": 100,
                    "branch": "hogsmade",
                    "uncommitted": 0,
                    "lastCommit": "1h ago",
                    "issues": [],
                    "stack": "Python",
                },
            ],
        }
    )
    bridge.ingest_line_audit(
        {
            "clean": True,
            "errorCount": 0,
            "warningCount": 0,
            "fixableCount": 0,
            "fixedCount": 0,
            "summary": "Line is clean. 6 rules, 0 findings.",
        }
    )
    return bridge


@pytest.fixture
def degraded_bridge() -> EcosystemBridge:
    """Bridge with degraded ecosystem — failures, blocks, dirty line audit."""
    bridge = EcosystemBridge()
    bridge.ingest_audit_events(
        [
            {
                "source": "grid-server",
                "tool": "validate_envelope",
                "status": "failure",
                "timestamp": "2026-04-09T06:00:00Z",
            },
            {
                "source": "grid-server",
                "tool": "validate_envelope",
                "status": "failure",
                "timestamp": "2026-04-09T06:01:00Z",
            },
            {
                "source": "grid-server",
                "tool": "validate_envelope",
                "status": "error",
                "timestamp": "2026-04-09T06:02:00Z",
            },
            {
                "source": "seeds-server",
                "tool": "ecosystem_scan",
                "status": "success",
                "timestamp": "2026-04-09T06:03:00Z",
            },
        ]
    )
    bridge.ingest_enforcement(
        {
            "status": "elevated",
            "totalActive": 3,
            "byLevel": {"observed": 1, "flagged": 1, "restricted": 0, "blocked": 1},
            "recentPrecedents": [
                {
                    "id": "p-blocked",
                    "source": "grid-server",
                    "tool": "fail",
                    "category": "error",
                    "occurrences": 5,
                    "level": "blocked",
                    "lastSeen": "2026-04-09T00:00:00Z",
                },
            ],
        }
    )
    bridge.ingest_ecosystem(
        {
            "summary": {"overallScore": 45, "totalRepos": 4, "active": 2, "stale": 2},
            "repos": [
                {
                    "name": "GRID",
                    "healthScore": 60,
                    "branch": "main",
                    "uncommitted": 25,
                    "lastCommit": "3d ago",
                    "issues": ["25 uncommitted"],
                    "stack": "Python",
                },
                {
                    "name": "broken",
                    "healthScore": 20,
                    "branch": "main",
                    "uncommitted": 0,
                    "lastCommit": "30d ago",
                    "issues": ["No tests"],
                    "stack": "unknown",
                },
            ],
        }
    )
    bridge.ingest_line_audit(
        {
            "clean": False,
            "errorCount": 5,
            "warningCount": 3,
            "fixableCount": 4,
            "fixedCount": 0,
            "summary": "5 errors, 3 warnings, 4 fixable",
        }
    )
    return bridge


@pytest.fixture
def minimal_bridge() -> EcosystemBridge:
    """Bridge with no data ingested."""
    return EcosystemBridge()


# ── PathScore Tests ──


class TestPathScore:
    def test_to_dict(self):
        score = PathScore("health", 85.0, 0.30, 25.5, ("Evidence 1",))
        d = score.to_dict()
        assert d["dimension"] == "health"
        assert d["raw_value"] == 85.0
        assert d["weight"] == 0.30
        assert d["weighted"] == 25.5
        assert "Evidence 1" in d["evidence"]

    def test_rounding(self):
        score = PathScore("trust", 73.333333, 0.25, 18.333333)
        d = score.to_dict()
        assert d["raw_value"] == 73.33
        assert d["weighted"] == 18.33


# ── ScoredEntity Tests ──


class TestScoredEntity:
    def test_to_dict(self):
        entity = ScoredEntity(
            name="GRID",
            entity_type="repo",
            path_score=85.0,
            tier=LumosVerdict.FAST_CLEAR,
            dimensions=(),
            sweep_protocol=SweepProtocol.A_MONITOR,
        )
        d = entity.to_dict()
        assert d["name"] == "GRID"
        assert d["tier"] == "FAST_CLEAR"
        assert d["sweep_protocol"] == "A_MONITOR"

    def test_without_protocol(self):
        entity = ScoredEntity(
            name="test",
            entity_type="repo",
            path_score=50.0,
            tier=LumosVerdict.WATCH,
            dimensions=(),
        )
        d = entity.to_dict()
        assert "sweep_protocol" not in d


# ── SweepAction Tests ──


class TestSweepAction:
    def test_to_dict(self):
        action = SweepAction(
            target="broken-repo",
            protocol=SweepProtocol.E_STABILIZE,
            action="Fix critical failures",
            priority=1,
            depends_on=("other-repo",),
        )
        d = action.to_dict()
        assert d["target"] == "broken-repo"
        assert d["protocol"] == "E_STABILIZE"
        assert d["priority"] == 1
        assert "other-repo" in d["depends_on"]


# ── GateResult Tests ──


class TestGateResult:
    def test_passed(self):
        gate = GateResult("test_gate", True, "All good")
        assert gate.passed
        d = gate.to_dict()
        assert d["passed"] is True

    def test_failed(self):
        gate = GateResult("test_gate", False, "Something broke")
        assert not gate.passed


# ── LumosResult Tests ──


class TestLumosResult:
    def test_default_state(self):
        result = LumosResult()
        assert result.composite_score == 0.0
        assert result.verdict == LumosVerdict.FAST_CLEAR
        assert result.phases_completed == []
        assert result.evolution_eligible is False

    def test_to_dict(self):
        result = LumosResult()
        result.composite_score = 75.5
        result.verdict = LumosVerdict.FAST_CLEAR
        d = result.to_dict()
        assert d["composite_score"] == 75.5
        assert d["verdict"] == "FAST_CLEAR"


# ── LumosOrchestrator Tests — Healthy Path ──


class TestLumosOrchestratorHealthy:
    def test_full_pipeline(self, healthy_bridge):
        orch = LumosOrchestrator(healthy_bridge)
        result = orch.run_full()
        assert len(result.phases_completed) == 6
        assert LumosPhase.PROBE in result.phases_completed
        assert LumosPhase.EVOLVE in result.phases_completed

    def test_composite_score_in_range(self, healthy_bridge):
        orch = LumosOrchestrator(healthy_bridge)
        result = orch.run_full()
        assert 0 <= result.composite_score <= 100

    def test_healthy_verdict_is_clear(self, healthy_bridge):
        orch = LumosOrchestrator(healthy_bridge)
        result = orch.run_full()
        assert result.verdict == LumosVerdict.FAST_CLEAR

    def test_all_path_dimensions_present(self, healthy_bridge):
        orch = LumosOrchestrator(healthy_bridge)
        result = orch.run_full()
        dims = {s.dimension for s in result.path_scores}
        assert dims == {"health", "trust", "drift", "fail", "momentum"}

    def test_entities_sorted_ascending(self, healthy_bridge):
        orch = LumosOrchestrator(healthy_bridge)
        result = orch.run_full()
        scores = [e.path_score for e in result.scored_entities]
        assert scores == sorted(scores)

    def test_healthy_all_gates_pass(self, healthy_bridge):
        orch = LumosOrchestrator(healthy_bridge)
        result = orch.run_full()
        assert all(g.passed for g in result.gate_results)

    def test_healthy_evolution_eligible(self, healthy_bridge):
        orch = LumosOrchestrator(healthy_bridge)
        result = orch.run_full()
        assert result.evolution_eligible

    def test_no_urgent_entities(self, healthy_bridge):
        orch = LumosOrchestrator(healthy_bridge)
        result = orch.run_full()
        assert not any(e.tier == LumosVerdict.URGENT for e in result.scored_entities)


# ── LumosOrchestrator Tests — Degraded Path ──


class TestLumosOrchestratorDegraded:
    def test_full_pipeline_completes(self, degraded_bridge):
        orch = LumosOrchestrator(degraded_bridge)
        result = orch.run_full()
        assert len(result.phases_completed) == 6

    def test_lower_composite_score(self, degraded_bridge):
        orch = LumosOrchestrator(degraded_bridge)
        result = orch.run_full()
        # Degraded ecosystem should have lower score
        assert result.composite_score < 65

    def test_not_fast_clear(self, degraded_bridge):
        orch = LumosOrchestrator(degraded_bridge)
        result = orch.run_full()
        assert result.verdict != LumosVerdict.FAST_CLEAR

    def test_has_sweep_actions(self, degraded_bridge):
        orch = LumosOrchestrator(degraded_bridge)
        result = orch.run_full()
        assert len(result.sweep_actions) > 0

    def test_some_gates_fail(self, degraded_bridge):
        orch = LumosOrchestrator(degraded_bridge)
        result = orch.run_full()
        # Should fail the blocked precedents and/or line audit gate
        failed_gates = [g for g in result.gate_results if not g.passed]
        assert len(failed_gates) > 0

    def test_evolution_not_eligible(self, degraded_bridge):
        orch = LumosOrchestrator(degraded_bridge)
        result = orch.run_full()
        assert not result.evolution_eligible
        assert "blocked" in result.evolution_message.lower() or "score" in result.evolution_message.lower()

    def test_urgent_entity_present(self, degraded_bridge):
        orch = LumosOrchestrator(degraded_bridge)
        result = orch.run_full()
        # "broken" repo with health 20 should be URGENT
        urgent = [e for e in result.scored_entities if e.tier == LumosVerdict.URGENT]
        assert len(urgent) >= 1


# ── LumosOrchestrator Tests — Minimal/Empty ──


class TestLumosOrchestratorMinimal:
    def test_empty_bridge_runs(self, minimal_bridge):
        orch = LumosOrchestrator(minimal_bridge)
        result = orch.run_full()
        assert len(result.phases_completed) == 6

    def test_empty_has_default_scores(self, minimal_bridge):
        orch = LumosOrchestrator(minimal_bridge)
        result = orch.run_full()
        assert result.composite_score > 0  # defaults kick in

    def test_empty_no_entities(self, minimal_bridge):
        orch = LumosOrchestrator(minimal_bridge)
        result = orch.run_full()
        assert len(result.scored_entities) == 0

    def test_empty_no_sweep_actions(self, minimal_bridge):
        orch = LumosOrchestrator(minimal_bridge)
        result = orch.run_full()
        assert len(result.sweep_actions) == 0


# ── Phase-by-Phase Tests ──


class TestPhaseByPhase:
    def test_phase_probe(self, healthy_bridge):
        orch = LumosOrchestrator(healthy_bridge)
        report = ProbeReport()
        orch.phase_probe(report)
        assert LumosPhase.PROBE in orch.result.phases_completed
        assert orch.result.probe_report is report
        assert orch.result.ecosystem_state is not None

    def test_phase_quantify(self, healthy_bridge):
        orch = LumosOrchestrator(healthy_bridge)
        orch.phase_probe(None)
        orch.phase_quantify()
        assert LumosPhase.QUANTIFY in orch.result.phases_completed
        assert len(orch.result.path_scores) == 5

    def test_phase_sort(self, healthy_bridge):
        orch = LumosOrchestrator(healthy_bridge)
        orch.phase_probe(None)
        orch.phase_quantify()
        orch.phase_sort()
        assert LumosPhase.SORT in orch.result.phases_completed
        assert orch.result.verdict in list(LumosVerdict)

    def test_phase_guide(self, healthy_bridge):
        orch = LumosOrchestrator(healthy_bridge)
        orch.phase_probe(None)
        orch.phase_quantify()
        orch.phase_sort()
        orch.phase_guide()
        assert LumosPhase.GUIDE in orch.result.phases_completed

    def test_phase_execute(self, healthy_bridge):
        orch = LumosOrchestrator(healthy_bridge)
        orch.phase_probe(None)
        orch.phase_quantify()
        orch.phase_sort()
        orch.phase_guide()
        orch.phase_execute()
        assert LumosPhase.EXECUTE in orch.result.phases_completed
        assert len(orch.result.gate_results) == 4  # 4 standard gates

    def test_phase_evolve(self, healthy_bridge):
        orch = LumosOrchestrator(healthy_bridge)
        orch.phase_probe(None)
        orch.phase_quantify()
        orch.phase_sort()
        orch.phase_guide()
        orch.phase_execute()
        orch.phase_evolve()
        assert LumosPhase.EVOLVE in orch.result.phases_completed


# ── Verdict Classification Tests ──


class TestVerdictClassification:
    def test_fast_clear(self):
        assert LumosOrchestrator._classify_verdict(100) == LumosVerdict.FAST_CLEAR
        assert LumosOrchestrator._classify_verdict(65) == LumosVerdict.FAST_CLEAR
        assert LumosOrchestrator._classify_verdict(80) == LumosVerdict.FAST_CLEAR

    def test_watch(self):
        assert LumosOrchestrator._classify_verdict(64) == LumosVerdict.WATCH
        assert LumosOrchestrator._classify_verdict(50) == LumosVerdict.WATCH

    def test_act(self):
        assert LumosOrchestrator._classify_verdict(49) == LumosVerdict.ACT
        assert LumosOrchestrator._classify_verdict(35) == LumosVerdict.ACT

    def test_urgent(self):
        assert LumosOrchestrator._classify_verdict(34) == LumosVerdict.URGENT
        assert LumosOrchestrator._classify_verdict(0) == LumosVerdict.URGENT


# ── Tier-to-Protocol Tests ──


class TestTierToProtocol:
    def test_clear_to_monitor(self):
        assert LumosOrchestrator._tier_to_protocol(LumosVerdict.FAST_CLEAR) == SweepProtocol.A_MONITOR

    def test_watch_to_watch(self):
        assert LumosOrchestrator._tier_to_protocol(LumosVerdict.WATCH) == SweepProtocol.B_WATCH

    def test_act_to_triage(self):
        assert LumosOrchestrator._tier_to_protocol(LumosVerdict.ACT) == SweepProtocol.C_TRIAGE

    def test_urgent_to_stabilize(self):
        assert LumosOrchestrator._tier_to_protocol(LumosVerdict.URGENT) == SweepProtocol.E_STABILIZE


# ── Serialization Tests ──


class TestSerialization:
    def test_full_result_serializable(self, healthy_bridge):
        orch = LumosOrchestrator(healthy_bridge)
        result = orch.run_full()
        d = result.to_dict()
        # Should be fully JSON-serializable
        import json

        json_str = json.dumps(d)
        assert len(json_str) > 100  # Non-trivial output
        parsed = json.loads(json_str)
        assert parsed["verdict"] == result.verdict.value

    def test_degraded_result_serializable(self, degraded_bridge):
        orch = LumosOrchestrator(degraded_bridge)
        result = orch.run_full()
        import json

        d = result.to_dict()
        json_str = json.dumps(d)
        parsed = json.loads(json_str)
        assert "sweep_actions" in parsed
        assert len(parsed["gate_results"]) == 4
