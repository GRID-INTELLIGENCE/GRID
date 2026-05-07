"""Training loop foundation for GRID agentic reinforcement learning.

Wires existing building blocks (RuntimeBehaviorTracer, OnlineLearningCoordinator,
AgentIntelligenceEvaluator) into an RL training loop skeleton. Policy optimization
(SAC/PPO) is stubbed for future implementation.

Reference: research/rl-datasheets.md, Datasheet 1
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import structlog
from pydantic import BaseModel, Field

from .intelligence_evaluator import AgentIntelligenceEvaluator
from .learning_coordinator import OnlineLearningCoordinator
from .reward_functions import RewardConfig, compute_agentic_reward
from .runtime_behavior_tracer import RuntimeBehaviorTracer

if TYPE_CHECKING:
    pass

logger = structlog.get_logger(__name__)

# ── Optional torch import (graceful degradation) ─────────────────────────────
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim

    _TORCH_AVAILABLE = True
except ImportError:  # pragma: no cover
    _TORCH_AVAILABLE = False
    torch = None  # type: ignore[assignment]
    nn = None  # type: ignore[assignment]
    optim = None  # type: ignore[assignment]

# ── State encoding constants (Datasheet 1, Section 2) ────────────────────────
# State vector dimension after encoding:
#   task_type (12 one-hot) + agent_role (8 one-hot) + confidence (1) +
#   fallback_used (1) + skills_retrieved (1) + skills_used (1) +
#   llm_calls (1) + duration_ms_log (1) = 26
_TASK_TYPES = [
    "code_gen", "code_review", "analysis", "writing", "research",
    "planning", "debugging", "testing", "documentation", "qa",
    "conversation", "unknown",
]
_AGENT_ROLES = [
    "coordinator", "researcher", "reviewer", "writer",
    "debugger", "planner", "executor", "unknown",
]
_STATE_DIM = len(_TASK_TYPES) + len(_AGENT_ROLES) + 6  # 26

# Action dimension: 1 discrete (skill index, mapped to [0,1] via softmax head)
# + 1 temperature R[0,2] + 1 autonomy R[0,0.95] + 1 recovery Binary
_ACTION_DIM = 4

_HIDDEN_DIM = 64


# ── State / Action encoding ───────────────────────────────────────────────────


def _encode_state(state: dict) -> list[float]:
    """Convert a state dict to a fixed-length float vector (length _STATE_DIM).

    Encoding:
    - task_type  → one-hot (12)
    - agent_role → one-hot (8)
    - confidence → scalar in [0, 1]
    - fallback_used → 0.0/1.0
    - skills_retrieved → log1p-normalised
    - skills_used → log1p-normalised
    - llm_calls → log1p-normalised
    - duration_ms → log1p(x / 1000) normalised
    """
    task_type = str(state.get("task_type", "unknown")).lower()
    agent_role = str(state.get("agent_role", "unknown")).lower()

    task_oh = [1.0 if t == task_type else 0.0 for t in _TASK_TYPES]
    role_oh = [1.0 if r == agent_role else 0.0 for r in _AGENT_ROLES]

    # Scalar features
    scalars = [
        float(state.get("confidence", 0.5)),
        1.0 if state.get("fallback_used") else 0.0,
        math.log1p(float(state.get("skills_retrieved", 0))),
        math.log1p(float(state.get("skills_used", 0))),
        math.log1p(float(state.get("llm_calls", 0))),
        math.log1p(float(state.get("duration_ms", 0)) / 1000.0),
    ]

    return task_oh + role_oh + scalars


# ── Policy Network ────────────────────────────────────────────────────────────


if _TORCH_AVAILABLE:

    class PolicyNetwork(nn.Module):  # type: ignore[misc]
        """Lightweight MLP policy + baseline value network for REINFORCE.

        Architecture (Datasheet 1, Section 6):
        - Shared encoder: Linear(_STATE_DIM → _HIDDEN_DIM) + ReLU
        - Policy head: Linear(_HIDDEN_DIM → _ACTION_DIM) — outputs un-normalised
          log-probabilities over a discretised action space
        - Value head: Linear(_HIDDEN_DIM → 1) — baseline for variance reduction

        The action space is treated as a single categorical over _ACTION_DIM
        buckets (a simplification of the mixed action space; full SAC with
        separate continuous heads is the recommended next step once this
        foundation is validated).
        """

        def __init__(self, state_dim: int = _STATE_DIM, hidden_dim: int = _HIDDEN_DIM, action_dim: int = _ACTION_DIM) -> None:
            super().__init__()
            self.encoder = nn.Sequential(
                nn.Linear(state_dim, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, hidden_dim),
                nn.ReLU(),
            )
            self.policy_head = nn.Linear(hidden_dim, action_dim)
            self.value_head = nn.Linear(hidden_dim, 1)

        def forward(self, state_tensor: "torch.Tensor") -> "tuple[torch.Tensor, torch.Tensor]":
            """Return (action_logits, state_value)."""
            h = self.encoder(state_tensor)
            return self.policy_head(h), self.value_head(h).squeeze(-1)

        def action_log_probs(self, state_tensor: "torch.Tensor") -> "torch.Tensor":
            """Return log-softmax action probabilities."""
            logits, _ = self.forward(state_tensor)
            return torch.log_softmax(logits, dim=-1)

else:  # pragma: no cover

    class PolicyNetwork:  # type: ignore[no-redef]
        """Stub when torch is not installed."""

        def __init__(self, *args: object, **kwargs: object) -> None:
            raise RuntimeError("torch is required for PolicyNetwork. Install torch>=2.0.")


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

        # Initialise policy network and optimiser when torch is available.
        if _TORCH_AVAILABLE:
            self._policy: PolicyNetwork | None = PolicyNetwork()
            self._optimizer: optim.Adam | None = optim.Adam(  # type: ignore[union-attr]
                self._policy.parameters(),
                lr=self.config.learning_rate,
            )
        else:  # pragma: no cover
            self._policy = None
            self._optimizer = None
            logger.warning("training_loop_no_torch", msg="torch not installed; policy updates disabled")

        logger.info(
            "training_loop_initialized",
            min_episode_turns=self.config.min_episode_turns,
            gamma=self.config.gamma,
            batch_size=self.config.batch_size,
            policy_network="enabled" if _TORCH_AVAILABLE else "disabled",
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
                # Carry anticipation signal from final trace into episode for downstream RL
                last_anticipation = traces[-1].get("metadata", {}).get("anticipation")
                if last_anticipation is not None:
                    episode.metadata["anticipation"] = last_anticipation

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
        """Execute one REINFORCE policy gradient training step.

        Algorithm (Datasheet 1, Section 6 — PPO/REINFORCE foundation):
        1. Collect episodes from tracer history.
        2. Compute discounted returns G_t per episode.
        3. Encode states into fixed-length tensors.
        4. Forward pass through PolicyNetwork → action log-probs + state values.
        5. Compute policy loss = -mean(log_π(a|s) * advantage) with entropy bonus.
        6. Compute value loss = MSE(V(s), G_t) for baseline regression.
        7. Combined loss backward + optimizer step.

        Falls back to stub_computed when torch is unavailable.
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

        policy_loss: float | None = None
        value_loss: float | None = None
        entropy: float | None = None
        status = "stub_computed"

        if _TORCH_AVAILABLE and self._policy is not None and self._optimizer is not None:
            policy_loss, value_loss, entropy = self._reinforce_update(episodes, returns)
            status = "reinforce_computed"

        duration_ms = (time.monotonic() - start) * 1000
        result = TrainStepResult(
            step=self._step_count,
            episodes_used=len(episodes),
            mean_reward=round(mean_reward, 4),
            policy_loss=round(policy_loss, 6) if policy_loss is not None else None,
            value_loss=round(value_loss, 6) if value_loss is not None else None,
            entropy=round(entropy, 6) if entropy is not None else None,
            duration_ms=round(duration_ms, 2),
            status=status,
        )

        logger.info(
            "train_step_complete",
            step=result.step,
            episodes_used=result.episodes_used,
            mean_reward=result.mean_reward,
            policy_loss=result.policy_loss,
            value_loss=result.value_loss,
            entropy=result.entropy,
            duration_ms=result.duration_ms,
            status=result.status,
        )

        return result

    def evaluate(self) -> EvalResult:
        """Evaluate current policy on the held-out eval split.

        Implements 80/10/10 train/eval/test split by session as specified in
        Datasheet 1, Section 4. Sessions are sorted by start_time so that
        the eval split always covers the most recent 10% of sessions
        (chronological hold-out, not random).
        """
        episodes = self.collect_episodes(min_turns=self.config.min_episode_turns)
        if not episodes:
            logger.warning("evaluate_no_episodes")
            return EvalResult(status="no_episodes")

        # Sort by start_time for chronological 80/10/10 split
        episodes_sorted = sorted(episodes, key=lambda e: e.start_time)
        n = len(episodes_sorted)
        eval_start = int(n * 0.80)
        eval_end = int(n * 0.90)

        # Fall back to using all episodes when too few for a proper split
        if eval_end <= eval_start:
            eval_episodes = episodes_sorted
        else:
            eval_episodes = episodes_sorted[eval_start:eval_end]

        returns = self.compute_rewards(eval_episodes)
        sorted_returns = sorted(returns)

        # Count successful episodes (positive total reward)
        successes = sum(1 for ep in eval_episodes if ep.total_reward > 0)

        # Mean latency across all transitions
        all_latencies = [
            t.info.get("duration_ms", 0)
            for ep in eval_episodes
            for t in ep.transitions
            if t.info.get("duration_ms", 0) > 0
        ]
        mean_latency = sum(all_latencies) / len(all_latencies) if all_latencies else 0.0

        result = EvalResult(
            episodes_evaluated=len(eval_episodes),
            mean_reward=round(sum(returns) / len(returns), 4),
            median_reward=round(sorted_returns[len(sorted_returns) // 2], 4),
            success_rate=round(successes / len(eval_episodes), 4) if eval_episodes else 0.0,
            mean_latency_ms=round(mean_latency, 2),
            status="evaluated",
        )

        logger.info(
            "evaluation_complete",
            total_episodes=n,
            eval_split=f"{eval_start}:{eval_end}",
            episodes_evaluated=result.episodes_evaluated,
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

    def _reinforce_update(
        self,
        episodes: list[Episode],
        returns: list[float],
    ) -> tuple[float, float, float]:
        """Run one REINFORCE gradient update over the episode batch.

        REINFORCE with baseline (Williams, 1992):
        - Advantage: A_t = G_t - V(s_t)  (reduces variance vs raw return)
        - Policy loss: -E[log π(a|s) * A_t]  (gradient ascent on expected return)
        - Value loss: MSE(V(s_t), G_t)  (train baseline towards actual return)
        - Entropy bonus: -E[H(π)] regularises against premature convergence

        Args:
            episodes: Episodes collected this step.
            returns: Discounted total return per episode (pre-computed by compute_rewards).

        Returns:
            (policy_loss, value_loss, mean_entropy) as Python floats.
        """
        assert _TORCH_AVAILABLE and self._policy is not None and self._optimizer is not None

        # Normalise returns for training stability
        returns_t = torch.tensor(returns, dtype=torch.float32)
        if returns_t.std() > 1e-8:
            returns_t = (returns_t - returns_t.mean()) / (returns_t.std() + 1e-8)

        all_log_probs: list[torch.Tensor] = []
        all_values: list[torch.Tensor] = []
        all_advantages: list[torch.Tensor] = []
        all_entropies: list[torch.Tensor] = []

        for ep, ret_norm in zip(episodes, returns_t.tolist()):
            for transition in ep.transitions:
                state_vec = _encode_state(transition.state)
                s = torch.tensor(state_vec, dtype=torch.float32).unsqueeze(0)

                logits, value = self._policy(s)
                log_probs = torch.log_softmax(logits, dim=-1).squeeze(0)
                probs = log_probs.exp()

                # Pseudo-action: map decision_type to an action index
                action_idx = self._action_to_index(transition.action)
                log_prob = log_probs[action_idx]

                advantage = torch.tensor(ret_norm - value.item(), dtype=torch.float32)
                ep_entropy = -(probs * log_probs).sum()

                all_log_probs.append(log_prob)
                all_values.append(value.squeeze(0))
                all_advantages.append(advantage)
                all_entropies.append(ep_entropy)

        if not all_log_probs:
            return 0.0, 0.0, 0.0

        log_probs_t = torch.stack(all_log_probs)
        values_t = torch.stack(all_values)
        advantages_t = torch.stack(all_advantages)
        entropies_t = torch.stack(all_entropies)

        # Build target returns per-transition by repeating per-episode returns
        target_returns: list[float] = []
        for ep, ret in zip(episodes, returns_t.tolist()):
            target_returns.extend([ret] * len(ep.transitions))
        targets_t = torch.tensor(target_returns, dtype=torch.float32)

        policy_loss_t = -(log_probs_t * advantages_t).mean()
        value_loss_t = torch.nn.functional.mse_loss(values_t, targets_t)
        entropy_t = entropies_t.mean()

        # Entropy regularisation coefficient (encourages exploration)
        _ENTROPY_COEFF = 0.01
        loss = policy_loss_t + 0.5 * value_loss_t - _ENTROPY_COEFF * entropy_t

        self._optimizer.zero_grad()
        loss.backward()
        # Gradient clipping for stability
        torch.nn.utils.clip_grad_norm_(self._policy.parameters(), max_norm=1.0)
        self._optimizer.step()

        return (
            policy_loss_t.item(),
            value_loss_t.item(),
            entropy_t.item(),
        )

    @staticmethod
    def _action_to_index(action: dict) -> int:
        """Map an action dict to a discrete action index [0, _ACTION_DIM).

        Mapping (Datasheet 1, Section 2 action space):
        0 = route      1 = retrieve     2 = recover      3 = other
        """
        dt = str(action.get("decision_type", "route")).lower()
        mapping = {"route": 0, "retrieve": 1, "recover": 2}
        return mapping.get(dt, 3)
