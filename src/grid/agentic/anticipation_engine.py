"""Anticipation Engine for GRID Agentic System.

Synthesises next-action proposals from skill performance history and the
current execution window.  Output is data-only: ActionProposal objects carry
no execution authority.  Human-gated downstream consumers decide whether to
act on any proposal.

Kill switch: set GRID_ANTICIPATION_ENABLED=false to disable output entirely.
Schema version: 1.0.0  (bump ANTICIPATION_SCHEMA_VERSION when fields change)
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import structlog

from .learning_coordinator import OnlineLearningCoordinator, SkillStats
from .reward_functions import RewardConfig, compute_agentic_reward

if TYPE_CHECKING:
    from .runtime_behavior_tracer import ExecutionBehavior

logger = structlog.get_logger(__name__)

ANTICIPATION_SCHEMA_VERSION = "1.0.0"

_MIN_WARMUP_SAMPLES = 10
_MIN_DECISION_DEPTH = 3
_MAX_PROPOSALS = 5


# ── Contract dataclasses ──────────────────────────────────────────────────────


@dataclass
class ActionProposal:
    """A single ranked next-action proposal.

    Fields are sourced exclusively from confirmed ExecutionBehavior / SkillStats
    attributes — no placeholder or inferred-but-undefined values.
    """

    action_type: str
    skill_id: str | None
    rationale: str
    expected_reward: float
    source_skill_samples: int


@dataclass
class ProximityWindow:
    """Dual-marker state window: origin → now → projection.

    Captures where the execution started, where it is now, and where skill
    history predicts it will end.  Persisted in AnticipationSignal.metadata
    by downstream consumers that need longitudinal tracking.
    """

    session_id: str
    origin_state: dict
    now_state: dict
    projection: dict
    step_index: int
    created_at: float
    schema_version: str = ANTICIPATION_SCHEMA_VERSION


@dataclass
class AnticipationSignal:
    """Emitted contract from AnticipationEngine.synthesize().

    synthesis is ranked descending by expected_reward, capped at _MAX_PROPOSALS.
    kill_switch_active=True means synthesis is always an empty list.
    """

    window: ProximityWindow
    synthesis: list[ActionProposal]
    anticipation_score: float
    source_substrate: str
    session_id: str
    generated_at: float
    kill_switch_active: bool
    ecosystem_baseline_score: float | None = None


# ── Signal store ─────────────────────────────────────────────────────────────


class AnticipationStore:
    """Append-only NDJSON log for AnticipationSignal persistence.

    Provides query_signals() for operational retrieval of synthesis output.
    Default path: ~/.grid/anticipation/signals.ndjson
    Override via GRID_ANTICIPATION_STORE env var.
    """

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or Path(
            os.environ.get(
                "GRID_ANTICIPATION_STORE",
                str(Path.home() / ".grid" / "anticipation" / "signals.ndjson"),
            )
        )

    @property
    def path(self) -> Path:
        return self._path

    def append(self, signal: AnticipationSignal) -> None:
        """Persist one AnticipationSignal as a NDJSON line."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self._path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(asdict(signal)) + "\n")
        except Exception:
            logger.warning("anticipation.store_write_failed", path=str(self._path))

    def query_signals(
        self,
        *,
        session_id: str | None = None,
        task_type: str | None = None,
        min_score: float | None = None,
        since: float | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """Return matching signals from the store, most-recent-first.

        Args:
            session_id: filter to one session
            task_type: filter by window.origin_state.task_type
            min_score: only return signals with anticipation_score >= min_score
            since: only return signals with generated_at >= since (unix timestamp)
            limit: max records to return
        """
        if not self._path.exists():
            return []
        results: list[dict] = []
        try:
            with self._path.open(encoding="utf-8") as fh:
                for raw in fh:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        record = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    if session_id and record.get("session_id") != session_id:
                        continue
                    if task_type:
                        rec_task = record.get("window", {}).get("origin_state", {}).get("task_type")
                        if rec_task != task_type:
                            continue
                    if min_score is not None and record.get("anticipation_score", 0.0) < min_score:
                        continue
                    if since is not None and record.get("generated_at", 0.0) < since:
                        continue
                    results.append(record)
        except Exception:
            logger.warning("anticipation.store_read_failed", path=str(self._path))
        results.sort(key=lambda r: r.get("generated_at", 0.0), reverse=True)
        return results[:limit]


# ── Engine ────────────────────────────────────────────────────────────────────


class AnticipationEngine:
    """Proactive next-action synthesiser.

    Does not execute proposals.  Wraps OnlineLearningCoordinator to derive
    skill-based proposals from accumulated performance history.
    """

    def __init__(
        self,
        learning_coordinator: OnlineLearningCoordinator,
        reward_config: RewardConfig | None = None,
        min_warmup_samples: int = _MIN_WARMUP_SAMPLES,
        min_decision_depth: int = _MIN_DECISION_DEPTH,
        store: AnticipationStore | None = None,
    ) -> None:
        self._lc = learning_coordinator
        self._reward_cfg = reward_config or RewardConfig()
        self._min_warmup = min_warmup_samples
        self._min_depth = min_decision_depth
        self._store = store or AnticipationStore()

    def _is_kill_switched(self) -> bool:
        val = os.environ.get("GRID_ANTICIPATION_ENABLED", "true").strip().lower()
        return val in ("false", "0", "no", "off")

    def _build_state_snapshot(self, behavior: ExecutionBehavior) -> dict:
        """Extract a serialisable state dict from an ExecutionBehavior."""
        end = behavior.end_time or time.time()
        elapsed_ms = (end - behavior.start_time) * 1000.0
        return {
            "case_id": behavior.case_id,
            "agent_role": behavior.agent_role,
            "task_type": behavior.task_type,
            "confidence": behavior.confidence,
            "llm_calls": behavior.llm_calls,
            "total_tokens": behavior.total_tokens,
            "skills_retrieved": behavior.skills_retrieved,
            "skills_used": behavior.skills_used,
            "decision_count": len(behavior.decisions),
            "fallback_used": behavior.fallback_used,
            "outcome": behavior.outcome.value if hasattr(behavior.outcome, "value") else str(behavior.outcome),
            "elapsed_ms": round(elapsed_ms, 2),
        }

    def _build_projection(self, task_type: str, skill_metrics: dict[str, SkillStats]) -> dict:
        """Estimate end-state from aggregated skill history for this task_type."""
        relevant = [s for s in skill_metrics.values() if s.usage_count > 0]
        if not relevant:
            return {"predicted_success_rate": 0.0, "predicted_latency_ms": 0.0, "skill_count": 0}

        avg_success = sum(s.success_rate for s in relevant) / len(relevant)
        avg_latency = sum(s.avg_latency_ms for s in relevant) / len(relevant)
        return {
            "predicted_success_rate": round(avg_success, 4),
            "predicted_latency_ms": round(avg_latency, 2),
            "skill_count": len(relevant),
            "task_type_hint": task_type,
        }

    def _proposal_from_stats(self, stats: SkillStats, task_type: str) -> ActionProposal:
        """Derive an ActionProposal from a SkillStats entry."""
        simulated_trace = {
            "outcome": "success" if stats.success_rate >= 0.5 else "failure",
            "duration_ms": stats.avg_latency_ms,
            "confidence": min(stats.success_rate + 0.1, 1.0),
            "user_satisfaction_proxy": stats.success_rate,
        }
        reward = compute_agentic_reward(simulated_trace, self._reward_cfg)
        rationale = f"skill '{stats.skill_id}' success_rate={stats.success_rate:.2f} over {stats.usage_count} samples"
        return ActionProposal(
            action_type=task_type,
            skill_id=stats.skill_id,
            rationale=rationale[:200],
            expected_reward=round(reward, 4),
            source_skill_samples=stats.usage_count,
        )

    def _compute_anticipation_score(self, now_state: dict, projection: dict) -> float:
        """Scalar divergence of projection from now_state, normalised to [0, 1]."""
        now_success = now_state.get("confidence", 0.5)
        pred_success = projection.get("predicted_success_rate", 0.0)
        return round(abs(now_success - pred_success), 4)

    def synthesize(
        self,
        behavior: ExecutionBehavior,
        session_id: str,
        step_index: int = 0,
        ecosystem_baseline_score: float | None = None,
    ) -> AnticipationSignal:
        """Synthesise an AnticipationSignal for the current execution state.

        Returns a signal with synthesis=[] and kill_switch_active=True when the
        environment flag is disabled.  Returns synthesis=[] (non-error) when
        warmup threshold is not yet met.
        """
        generated_at = time.time()
        kill_switch_active = self._is_kill_switched()

        origin_state = self._build_state_snapshot(behavior)
        now_state = dict(origin_state)
        projection = self._build_projection(behavior.task_type, self._lc.skill_metrics)

        window = ProximityWindow(
            session_id=session_id,
            origin_state=origin_state,
            now_state=now_state,
            projection=projection,
            step_index=step_index,
            created_at=generated_at,
        )

        if kill_switch_active:
            logger.info("anticipation.kill_switch_active", session_id=session_id)
            return AnticipationSignal(
                window=window,
                synthesis=[],
                anticipation_score=0.0,
                source_substrate="anticipation_engine",
                session_id=session_id,
                generated_at=generated_at,
                kill_switch_active=True,
                ecosystem_baseline_score=ecosystem_baseline_score,
            )

        warmup_ok = self._lc.learning_samples >= self._min_warmup
        depth_ok = len(behavior.decisions) >= self._min_depth

        if not warmup_ok:
            logger.info(
                "anticipation.warmup_skip",
                learning_samples=self._lc.learning_samples,
                required=self._min_warmup,
                session_id=session_id,
            )
            _sig = AnticipationSignal(
                window=window,
                synthesis=[],
                anticipation_score=0.0,
                source_substrate="anticipation_engine",
                session_id=session_id,
                generated_at=generated_at,
                kill_switch_active=False,
                ecosystem_baseline_score=ecosystem_baseline_score,
            )
            self._store.append(_sig)
            return _sig

        if not depth_ok:
            logger.debug(
                "anticipation.depth_skip",
                decision_count=len(behavior.decisions),
                required=self._min_depth,
                session_id=session_id,
            )
            _sig = AnticipationSignal(
                window=window,
                synthesis=[],
                anticipation_score=0.0,
                source_substrate="anticipation_engine",
                session_id=session_id,
                generated_at=generated_at,
                kill_switch_active=False,
                ecosystem_baseline_score=ecosystem_baseline_score,
            )
            self._store.append(_sig)
            return _sig

        proposals: list[ActionProposal] = [
            self._proposal_from_stats(stats, behavior.task_type)
            for stats in self._lc.skill_metrics.values()
            if stats.usage_count > 0
        ]

        proposals.sort(key=lambda p: p.expected_reward, reverse=True)
        proposals = proposals[:_MAX_PROPOSALS]

        if not proposals:
            logger.warning(
                "anticipation.empty_synthesis",
                task_type=behavior.task_type,
                skill_count=len(self._lc.skill_metrics),
                session_id=session_id,
            )

        anticipation_score = self._compute_anticipation_score(now_state, projection)

        logger.info(
            "anticipation.synthesized",
            proposal_count=len(proposals),
            anticipation_score=anticipation_score,
            top_reward=proposals[0].expected_reward if proposals else None,
            session_id=session_id,
        )

        _sig = AnticipationSignal(
            window=window,
            synthesis=proposals,
            anticipation_score=anticipation_score,
            source_substrate="anticipation_engine",
            session_id=session_id,
            generated_at=generated_at,
            kill_switch_active=False,
            ecosystem_baseline_score=ecosystem_baseline_score,
        )
        self._store.append(_sig)
        return _sig


# ── Module-level factory ──────────────────────────────────────────────────────


def create_anticipation_engine(
    learning_coordinator: OnlineLearningCoordinator,
    reward_config: RewardConfig | None = None,
    store: AnticipationStore | None = None,
) -> AnticipationEngine:
    """Convenience factory.  Preferred entry-point for wiring in AgentExecutor."""
    return AnticipationEngine(learning_coordinator=learning_coordinator, reward_config=reward_config, store=store)
