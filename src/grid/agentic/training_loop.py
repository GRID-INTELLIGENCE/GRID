"""Training loop foundation for GRID agentic reinforcement learning.

Wires existing building blocks (RuntimeBehaviorTracer, OnlineLearningCoordinator,
AgentIntelligenceEvaluator) into an RL training loop skeleton. Policy optimization
(SAC/PPO) is stubbed for future implementation.

Reference: research/rl-datasheets.md, Datasheet 1
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import structlog
from pydantic import BaseModel, Field

from .intelligence_evaluator import AgentIntelligenceEvaluator
from .learning_coordinator import OnlineLearningCoordinator
from .reward_functions import RewardConfig, compute_agentic_reward
from .runtime_behavior_tracer import RuntimeBehaviorTracer

logger = structlog.get_logger(__name__)


# ── Data Models ──────────────────────────────────────────────────────────────


@dataclass
class Transition:
    """A single (s, a, r, s', done) transition within an episode."""

    state: dict
    action: dict
    reward: float
    next_state: dict
    done: bool
    info: dict = field(default_factory=dict)


@dataclass
class Episode:
    """One complete episode (user session) of agent-environment interaction.

    Constructed from RuntimeBehaviorTracer history. An episode must have at
    least `min_turns` transitions to be useful for training.
    """

    session_id: str
    transitions: list[Transition] = field(default_factory=list)
    total_reward: float = 0.0
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    metadata: dict = field(default_factory=dict)

    @property
    def num_turns(self) -> int:
        return len(self.transitions)


class TrainStepResult(BaseModel):
    """Result of a single training step."""

    step: int = 0
    episodes_used: int = 0
    mean_reward: float = 0.0
    policy_loss: float | None = None
    value_loss: float | None = None
    entropy: float | None = None
    duration_ms: float = 0.0
    status: str = "stub"

    model_config = {"frozen": True}


class EvalResult(BaseModel):
    """Result of policy evaluation."""

    episodes_evaluated: int = 0
    mean_reward: float = 0.0
    median_reward: float = 0.0
    success_rate: float = 0.0
    mean_latency_ms: float = 0.0
    status: str = "stub"

    model_config = {"frozen": True}


class TrainingConfig(BaseModel):
    """Configuration for the training loop."""

    reward_config: RewardConfig = Field(default_factory=RewardConfig)
    min_episode_turns: int = Field(default=3, ge=1, description="Minimum turns per episode (datasheet: drop < 3)")
    batch_size: int = Field(default=64, ge=1)
    learning_rate: float = Field(default=3e-4, gt=0)
    gamma: float = Field(default=0.95, ge=0, le=1, description="Discount factor from datasheet")
    max_episodes_per_step: int = Field(default=256, ge=1)

    model_config = {"frozen": True}


# ── Training Loop ────────────────────────────────────────────────────────────


class TrainingLoop:
    """RL training loop that wires existing GRID agentic components.

    Collects execution traces from RuntimeBehaviorTracer, converts them to
    episodes, computes rewards using the Datasheet 1 formula, and provides
    stub hooks for SAC/PPO policy optimization.

    Args:
        behavior_tracer: Source of execution behavior history.
        learning_coordinator: Source of skill performance statistics.
        evaluator: Optional evaluator for behavioral pattern detection.
        config: Training configuration.
    """

    def __init__(
        self,
        behavior_tracer: RuntimeBehaviorTracer,
        learning_coordinator: OnlineLearningCoordinator,
        evaluator: AgentIntelligenceEvaluator | None = None,
        config: TrainingConfig | None = None,
    ) -> None:
        self.behavior_tracer = behavior_tracer
        self.learning_coordinator = learning_coordinator
        self.evaluator = evaluator or AgentIntelligenceEvaluator()
        self.config = config or TrainingConfig()
        self._step_count = 0
        self._total_episodes_processed = 0

        logger.info(
            "training_loop_initialized",
            min_episode_turns=self.config.min_episode_turns,
            gamma=self.config.gamma,
            batch_size=self.config.batch_size,
        )

    def collect_episodes(self, min_turns: int = 3) -> list[Episode]:
        """Convert tracer history into structured episodes.

        Groups behavior traces by case_id (session proxy), filters by minimum
        turn count, and constructs Episode objects with state/action/reward
        transitions.

        Args:
            min_turns: Minimum number of turns for an episode to be included.
                Per datasheet Section 5: "Drop sessions < 3 turns".

        Returns:
            List of episodes meeting the minimum turn threshold.
        """
        raw_history = self.behavior_tracer.get_history(limit=self.config.max_episodes_per_step * 10)

        # Group traces by case_id (each case_id approximates a session)
        sessions: dict[str, list[dict]] = {}
        for trace_dict in raw_history:
            case_id = trace_dict.get("case_id", "unknown")
            sessions.setdefault(case_id, []).append(trace_dict)

        episodes: list[Episode] = []
        for session_id, traces in sessions.items():
            # Sort traces by start_time within the session
            traces.sort(key=lambda t: t.get("start_time", 0))

            if len(traces) < min_turns:
                continue

            episode = Episode(session_id=session_id)
            if traces:
                episode.start_time = traces[0].get("start_time", time.time())
                episode.end_time = traces[-1].get("end_time")

            for i, trace in enumerate(traces):
                done = i == len(traces) - 1
                state = self._extract_state(trace)
                action = self._extract_action(trace)
                next_state = self._extract_state(traces[i + 1]) if not done else state

                reward = compute_agentic_reward(trace, self.config.reward_config)

                transition = Transition(
                    state=state,
                    action=action,
                    reward=reward,
                    next_state=next_state,
                    done=done,
                    info={
                        "trace_id": trace.get("trace_id", ""),
                        "outcome": trace.get("outcome", ""),
                        "duration_ms": trace.get("duration_ms", 0),
                    },
                )
                episode.transitions.append(transition)
                episode.total_reward += reward

            episodes.append(episode)

        logger.info(
            "episodes_collected",
            total_sessions=len(sessions),
            episodes_kept=len(episodes),
            episodes_filtered=len(sessions) - len(episodes),
            min_turns=min_turns,
        )
        return episodes

    def compute_rewards(self, episodes: list[Episode]) -> list[float]:
        """Compute total discounted rewards for a batch of episodes.

        Applies the discount factor (gamma) from the datasheet to compute
        the return G_t = sum_{k=0}^{T-t} gamma^k * r_{t+k}.

        Args:
            episodes: List of episodes with populated transitions.

        Returns:
            List of total discounted returns, one per episode.
        """
        gamma = self.config.gamma
        returns: list[float] = []

        for episode in episodes:
            discounted_return = 0.0
            # Reverse accumulation for proper discounting
            for transition in reversed(episode.transitions):
                discounted_return = transition.reward + gamma * discounted_return
            returns.append(discounted_return)

        if returns:
            mean_return = sum(returns) / len(returns)
            logger.info(
                "rewards_computed",
                num_episodes=len(returns),
                mean_return=round(mean_return, 4),
                min_return=round(min(returns), 4),
                max_return=round(max(returns), 4),
            )

        return returns

    def train_step(self) -> TrainStepResult:
        """Execute one training step.

        TODO: Implement SAC or PPO policy update. Current implementation:
        1. Collects episodes from tracer history
        2. Computes rewards
        3. Returns stub result with episode statistics

        The actual policy gradient computation will be added when the
        policy network architecture is defined (see Datasheet 1, Section 6:
        recommended algorithms are SAC for mixed action space, PPO with
        action masking).
        """
        start = time.monotonic()
        self._step_count += 1

        episodes = self.collect_episodes(min_turns=self.config.min_episode_turns)
        if not episodes:
            logger.warning("train_step_no_episodes", step=self._step_count)
            return TrainStepResult(
                step=self._step_count,
                status="no_episodes",
                duration_ms=(time.monotonic() - start) * 1000,
            )

        returns = self.compute_rewards(episodes)
        mean_reward = sum(returns) / len(returns) if returns else 0.0

        self._total_episodes_processed += len(episodes)

        # TODO(SAC/PPO): Policy network forward pass, loss computation, optimizer step.
        # The stub returns episode-level statistics for validation.

        duration_ms = (time.monotonic() - start) * 1000
        result = TrainStepResult(
            step=self._step_count,
            episodes_used=len(episodes),
            mean_reward=round(mean_reward, 4),
            duration_ms=round(duration_ms, 2),
            status="stub_computed",
        )

        logger.info(
            "train_step_complete",
            step=result.step,
            episodes_used=result.episodes_used,
            mean_reward=result.mean_reward,
            duration_ms=result.duration_ms,
        )

        return result

    def evaluate(self) -> EvalResult:
        """Evaluate current policy performance.

        TODO: Implement proper evaluation with held-out episodes. Current
        implementation uses all available tracer history as a proxy.

        Per Datasheet 1, Section 4: use 80/10/10 train/eval/test split
        by session (not by transition).
        """
        episodes = self.collect_episodes(min_turns=self.config.min_episode_turns)
        if not episodes:
            logger.warning("evaluate_no_episodes")
            return EvalResult(status="no_episodes")

        returns = self.compute_rewards(episodes)
        sorted_returns = sorted(returns)

        # Count successful episodes (positive total reward)
        successes = sum(1 for ep in episodes if ep.total_reward > 0)

        # Mean latency across all transitions
        all_latencies = [
            t.info.get("duration_ms", 0) for ep in episodes for t in ep.transitions if t.info.get("duration_ms", 0) > 0
        ]
        mean_latency = sum(all_latencies) / len(all_latencies) if all_latencies else 0.0

        result = EvalResult(
            episodes_evaluated=len(episodes),
            mean_reward=round(sum(returns) / len(returns), 4),
            median_reward=round(sorted_returns[len(sorted_returns) // 2], 4),
            success_rate=round(successes / len(episodes), 4) if episodes else 0.0,
            mean_latency_ms=round(mean_latency, 2),
            status="stub_evaluated",
        )

        logger.info(
            "evaluation_complete",
            episodes=result.episodes_evaluated,
            mean_reward=result.mean_reward,
            success_rate=result.success_rate,
        )

        return result

    # ── Private helpers ──────────────────────────────────────────────────

    def _extract_state(self, trace: dict) -> dict:
        """Extract state representation from a behavior trace.

        Maps trace fields to the state space defined in Datasheet 1, Section 2.
        """
        return {
            "task_type": trace.get("task_type", "unknown"),
            "agent_role": trace.get("agent_role", "unknown"),
            "confidence": trace.get("confidence", 0.5),
            "fallback_used": trace.get("fallback_used", False),
            "skills_retrieved": trace.get("skills_retrieved", 0),
            "skills_used": trace.get("skills_used", 0),
            "llm_calls": trace.get("llm_calls", 0),
            "duration_ms": trace.get("duration_ms", 0),
        }

    def _extract_action(self, trace: dict) -> dict:
        """Extract action representation from a behavior trace.

        Maps trace fields to the action space defined in Datasheet 1, Section 2.
        """
        decisions = trace.get("decisions", [])
        last_decision = decisions[-1] if decisions else {}

        return {
            "decision_type": last_decision.get("decision_type", "route"),
            "confidence": last_decision.get("confidence", 1.0),
            "recovery_strategy": trace.get("recovery_strategy"),
            "skills_used": trace.get("skills_used", 0),
        }
