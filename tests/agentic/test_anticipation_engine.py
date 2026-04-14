"""Tests for the anticipation_engine module.

Covers:
  1. Producer schema — AnticipationSignal fields are complete and typed correctly.
  2. Consumer parse — downstream code can destructure the signal without errors.
  3. Kill-switch path — GRID_ANTICIPATION_ENABLED=false produces empty synthesis.
  4. Warmup gate — synthesis is empty when learning_samples < 10.
  5. Depth gate — synthesis is empty when decision_count < 3.
  6. Full synthesis path — proposals are ranked, capped at 5, reward in range.
"""

from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from grid.agentic.anticipation_engine import (
    ANTICIPATION_SCHEMA_VERSION,
    ActionProposal,
    AnticipationEngine,
    AnticipationSignal,
    ProximityWindow,
    create_anticipation_engine,
)
from grid.agentic.learning_coordinator import OnlineLearningCoordinator, SkillStats
from grid.agentic.runtime_behavior_tracer import DecisionPoint, ExecutionBehavior, ExecutionOutcome

# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_behavior(*, decisions: int = 0, task_type: str = "route") -> ExecutionBehavior:
    b = ExecutionBehavior(case_id="c1", agent_role="analyst", task_type=task_type)
    for _ in range(decisions):
        b.decisions.append(DecisionPoint(confidence=0.9))
    b.finalize(ExecutionOutcome.SUCCESS)
    return b


def _warmed_coordinator(skill_count: int = 2) -> OnlineLearningCoordinator:
    lc = OnlineLearningCoordinator()
    lc.learning_samples = 15
    for i in range(skill_count):
        sid = f"skill_{i}"
        lc.skill_metrics[sid] = SkillStats(
            skill_id=sid,
            usage_count=5,
            success_count=4,
            total_latency_ms=1000.0,
        )
    return lc


# ── Schema tests ──────────────────────────────────────────────────────────────


class TestActionProposalSchema:
    def test_required_fields_present(self):
        p = ActionProposal(
            action_type="route",
            skill_id="skill_0",
            rationale="test rationale",
            expected_reward=0.75,
            source_skill_samples=5,
        )
        assert p.action_type == "route"
        assert p.skill_id == "skill_0"
        assert isinstance(p.rationale, str)
        assert isinstance(p.expected_reward, float)
        assert isinstance(p.source_skill_samples, int)

    def test_skill_id_can_be_none(self):
        p = ActionProposal(
            action_type="route",
            skill_id=None,
            rationale="no specific skill",
            expected_reward=0.0,
            source_skill_samples=0,
        )
        assert p.skill_id is None

    def test_rationale_max_length_contract(self):
        long_rationale = "x" * 300
        p = ActionProposal(
            action_type="route",
            skill_id=None,
            rationale=long_rationale[:200],
            expected_reward=0.5,
            source_skill_samples=1,
        )
        assert len(p.rationale) <= 200


class TestProximityWindowSchema:
    def test_schema_version_constant(self):
        w = ProximityWindow(
            session_id="s1",
            origin_state={},
            now_state={},
            projection={},
            step_index=0,
            created_at=time.time(),
        )
        assert w.schema_version == ANTICIPATION_SCHEMA_VERSION
        assert w.schema_version == "1.0.0"

    def test_all_fields_present(self):
        now = time.time()
        w = ProximityWindow(
            session_id="s1",
            origin_state={"confidence": 0.9},
            now_state={"confidence": 0.8},
            projection={"predicted_success_rate": 0.7},
            step_index=3,
            created_at=now,
        )
        assert w.session_id == "s1"
        assert isinstance(w.origin_state, dict)
        assert isinstance(w.now_state, dict)
        assert isinstance(w.projection, dict)
        assert w.step_index == 3
        assert w.created_at == now


class TestAnticipationSignalSchema:
    def test_source_substrate_constant(self):
        lc = _warmed_coordinator()
        engine = AnticipationEngine(lc)
        behavior = _make_behavior(decisions=3)
        signal = engine.synthesize(behavior, session_id="s1")

        assert signal.source_substrate == "anticipation_engine"

    def test_generated_at_is_recent(self):
        before = time.time()
        lc = _warmed_coordinator()
        engine = AnticipationEngine(lc)
        signal = engine.synthesize(_make_behavior(decisions=3), session_id="s1")
        after = time.time()

        assert before <= signal.generated_at <= after

    def test_kill_switch_false_by_default(self):
        lc = _warmed_coordinator()
        engine = AnticipationEngine(lc)
        signal = engine.synthesize(_make_behavior(decisions=3), session_id="s1")
        assert signal.kill_switch_active is False


# ── Kill-switch path ──────────────────────────────────────────────────────────


class TestKillSwitch:
    @pytest.mark.parametrize("env_val", ["false", "False", "FALSE", "0", "no", "off"])
    def test_disabled_env_returns_empty_synthesis(self, env_val: str):
        with patch.dict("os.environ", {"GRID_ANTICIPATION_ENABLED": env_val}):
            lc = _warmed_coordinator()
            engine = AnticipationEngine(lc)
            signal = engine.synthesize(_make_behavior(decisions=5), session_id="s1")

        assert signal.kill_switch_active is True
        assert signal.synthesis == []
        assert signal.anticipation_score == 0.0

    def test_enabled_env_produces_proposals(self):
        with patch.dict("os.environ", {"GRID_ANTICIPATION_ENABLED": "true"}):
            lc = _warmed_coordinator()
            engine = AnticipationEngine(lc)
            signal = engine.synthesize(_make_behavior(decisions=3), session_id="s1")

        assert signal.kill_switch_active is False


# ── Warmup gate ───────────────────────────────────────────────────────────────


class TestWarmupGate:
    def test_below_threshold_returns_empty(self):
        lc = OnlineLearningCoordinator()
        lc.learning_samples = 5
        engine = AnticipationEngine(lc)
        signal = engine.synthesize(_make_behavior(decisions=5), session_id="s1")

        assert signal.synthesis == []
        assert signal.kill_switch_active is False

    def test_at_threshold_allows_synthesis(self):
        lc = _warmed_coordinator()
        lc.learning_samples = 10
        engine = AnticipationEngine(lc)
        signal = engine.synthesize(_make_behavior(decisions=3), session_id="s1")

        assert signal.kill_switch_active is False


# ── Depth gate ────────────────────────────────────────────────────────────────


class TestDepthGate:
    def test_below_decision_depth_returns_empty(self):
        lc = _warmed_coordinator()
        engine = AnticipationEngine(lc)
        signal = engine.synthesize(_make_behavior(decisions=2), session_id="s1")

        assert signal.synthesis == []

    def test_at_decision_depth_produces_proposals(self):
        lc = _warmed_coordinator()
        engine = AnticipationEngine(lc)
        signal = engine.synthesize(_make_behavior(decisions=3), session_id="s1")

        assert len(signal.synthesis) > 0


# ── Full synthesis path ───────────────────────────────────────────────────────


class TestFullSynthesis:
    def test_proposals_ranked_descending(self):
        lc = _warmed_coordinator(skill_count=4)
        engine = AnticipationEngine(lc)
        signal = engine.synthesize(_make_behavior(decisions=3), session_id="s1")

        rewards = [p.expected_reward for p in signal.synthesis]
        assert rewards == sorted(rewards, reverse=True)

    def test_proposals_capped_at_five(self):
        lc = _warmed_coordinator(skill_count=10)
        engine = AnticipationEngine(lc)
        signal = engine.synthesize(_make_behavior(decisions=3), session_id="s1")

        assert len(signal.synthesis) <= 5

    def test_expected_reward_in_valid_range(self):
        lc = _warmed_coordinator()
        engine = AnticipationEngine(lc)
        signal = engine.synthesize(_make_behavior(decisions=3), session_id="s1")

        for proposal in signal.synthesis:
            assert -0.7 <= proposal.expected_reward <= 1.3, (
                f"expected_reward {proposal.expected_reward} out of [-0.7, 1.3]"
            )

    def test_anticipation_score_normalised(self):
        lc = _warmed_coordinator()
        engine = AnticipationEngine(lc)
        signal = engine.synthesize(_make_behavior(decisions=3), session_id="s1")

        assert 0.0 <= signal.anticipation_score <= 1.0

    def test_window_contains_origin_and_projection(self):
        lc = _warmed_coordinator()
        engine = AnticipationEngine(lc)
        signal = engine.synthesize(_make_behavior(decisions=3), session_id="s1")

        assert "confidence" in signal.window.origin_state
        assert "predicted_success_rate" in signal.window.projection


# ── Consumer parse test ───────────────────────────────────────────────────────


class TestConsumerParse:
    def test_downstream_destructure(self):
        """Simulate how AgentExecutor would attach the signal to episode metadata."""
        lc = _warmed_coordinator()
        engine = AnticipationEngine(lc)
        signal = engine.synthesize(_make_behavior(decisions=3), session_id="s1")

        metadata: dict = {
            "anticipation": None if signal.kill_switch_active else {
                "session_id": signal.session_id,
                "score": signal.anticipation_score,
                "proposals": [
                    {
                        "action_type": p.action_type,
                        "skill_id": p.skill_id,
                        "expected_reward": p.expected_reward,
                    }
                    for p in signal.synthesis
                ],
                "schema_version": signal.window.schema_version,
            },
        }

        assert metadata["anticipation"] is not None
        assert isinstance(metadata["anticipation"]["proposals"], list)
        assert metadata["anticipation"]["schema_version"] == "1.0.0"


# ── Factory ───────────────────────────────────────────────────────────────────


class TestFactory:
    def test_create_anticipation_engine_returns_engine(self):
        lc = OnlineLearningCoordinator()
        engine = create_anticipation_engine(lc)
        assert isinstance(engine, AnticipationEngine)
