"""Reward functions for GRID agentic reinforcement learning.

Implements reward calculations based on RL Datasheet 1 (Agentic Behavioral Intelligence).
Primary reward signal: weighted combination of task success, latency, and user satisfaction.
Shaping terms: coherence improvement, consent violation, overconfidence detection.

Reference: research/rl-datasheets.md, Datasheet 1, Section 3 "Reward Signal Design"
"""

from __future__ import annotations

from dataclasses import dataclass, field

import structlog

logger = structlog.get_logger(__name__)

# Outcome-to-numeric mapping per datasheet:
# FAILURE=0, PARTIAL=0.5, SUCCESS=1
_OUTCOME_SCORES: dict[str, float] = {
    "success": 1.0,
    "partial": 0.5,
    "failure": 0.0,
    "timeout": 0.0,
    "skipped": 0.0,
}

# Shaping constants (from datasheet Section 3)
_COHERENCE_IMPROVEMENT_BONUS = 0.1
_CONSENT_VIOLATION_PENALTY = -0.2
_OVERCONFIDENCE_PENALTY = -0.5


@dataclass(frozen=True)
class RewardConfig:
    """Weights for the primary reward function.

    Default values from RL Datasheet 1, Section 3:
    - w1 (task_success): 0.5
    - w2 (latency efficiency): 0.3
    - w3 (user satisfaction proxy): 0.2
    - gamma (discount factor): 0.95
    """

    w1: float = 0.5
    w2: float = 0.3
    w3: float = 0.2
    gamma: float = 0.95


@dataclass
class RewardBreakdown:
    """Detailed breakdown of a computed reward for observability."""

    primary: float = 0.0
    task_success_component: float = 0.0
    latency_component: float = 0.0
    satisfaction_component: float = 0.0
    coherence_shaping: float = 0.0
    consent_shaping: float = 0.0
    overconfidence_shaping: float = 0.0
    total: float = 0.0
    warnings: list[str] = field(default_factory=list)


def compute_agentic_reward(
    trace: dict,
    config: RewardConfig | None = None,
) -> float:
    """Compute the scalar reward for a single step/trace.

    Implements the Datasheet 1 formula:
        r_t = w1 * task_success + w2 * (1 - latency_normalized) + w3 * user_satisfaction_proxy

    Shaping terms:
        +0.1 for coherence improvement (coherence_delta > 0)
        -0.2 for consent violation
        -0.5 for overconfidence detection

    Args:
        trace: Dictionary with keys from RuntimeBehaviorTracer output. Expected fields:
            - outcome (str): "success", "partial", "failure", "timeout", "skipped"
            - duration_ms (float): execution latency in milliseconds
            - confidence (float): agent confidence [0, 1]
            - coherence_delta (float, optional): change in coherence [-1, 1]
            - consent_violated (bool, optional): whether consent was violated
            - user_satisfaction_proxy (float, optional): satisfaction signal [0, 1]
            - latency_budget_ms (float, optional): max acceptable latency for normalization
        config: Reward weights. Uses defaults from datasheet if None.

    Returns:
        Scalar reward in range [-0.7, 1.3] (before discounting).
    """
    if config is None:
        config = RewardConfig()

    breakdown = compute_agentic_reward_detailed(trace, config)
    return breakdown.total


def compute_agentic_reward_detailed(
    trace: dict,
    config: RewardConfig | None = None,
) -> RewardBreakdown:
    """Compute reward with full breakdown for debugging and logging.

    Same formula as compute_agentic_reward but returns component-level detail.
    """
    if config is None:
        config = RewardConfig()

    breakdown = RewardBreakdown()

    # --- Primary reward components ---

    # Task success: map outcome string to numeric score
    outcome_str = str(trace.get("outcome", "failure")).lower()
    task_success = _OUTCOME_SCORES.get(outcome_str, 0.0)
    breakdown.task_success_component = config.w1 * task_success

    # Latency efficiency: 1 - (duration / budget), clamped to [0, 1]
    duration_ms = float(trace.get("duration_ms", 0.0))
    latency_budget_ms = float(trace.get("latency_budget_ms", 5000.0))
    if latency_budget_ms <= 0:
        breakdown.warnings.append("latency_budget_ms <= 0, defaulting to 5000")
        latency_budget_ms = 5000.0
    latency_normalized = min(duration_ms / latency_budget_ms, 1.0)
    breakdown.latency_component = config.w2 * (1.0 - latency_normalized)

    # User satisfaction proxy: direct signal if available, else derive from outcome
    satisfaction = trace.get("user_satisfaction_proxy")
    if satisfaction is None:
        # Fallback: use task_success as a rough proxy
        satisfaction = task_success
    satisfaction = float(max(0.0, min(1.0, satisfaction)))
    breakdown.satisfaction_component = config.w3 * satisfaction

    breakdown.primary = (
        breakdown.task_success_component + breakdown.latency_component + breakdown.satisfaction_component
    )

    # --- Shaping terms ---

    # Coherence improvement bonus
    coherence_delta = float(trace.get("coherence_delta", 0.0))
    if coherence_delta > 0:
        breakdown.coherence_shaping = _COHERENCE_IMPROVEMENT_BONUS

    # Consent violation penalty
    if trace.get("consent_violated", False):
        breakdown.consent_shaping = _CONSENT_VIOLATION_PENALTY

    # Overconfidence detection penalty
    # Triggered when confidence is high but outcome is failure/timeout
    confidence = float(trace.get("confidence", 0.5))
    if confidence > 0.8 and outcome_str in ("failure", "timeout"):
        breakdown.overconfidence_shaping = _OVERCONFIDENCE_PENALTY

    # --- Total ---
    breakdown.total = (
        breakdown.primary + breakdown.coherence_shaping + breakdown.consent_shaping + breakdown.overconfidence_shaping
    )

    logger.debug(
        "reward_computed",
        outcome=outcome_str,
        total=round(breakdown.total, 4),
        primary=round(breakdown.primary, 4),
        shaping=round(
            breakdown.coherence_shaping + breakdown.consent_shaping + breakdown.overconfidence_shaping,
            4,
        ),
    )

    return breakdown
