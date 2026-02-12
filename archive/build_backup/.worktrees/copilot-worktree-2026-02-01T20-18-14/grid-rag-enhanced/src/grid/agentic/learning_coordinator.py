"""Online Learning Coordinator for GRID Agentic System.

Coordinates real-time learning from agent execution outcomes to improve
future task routing and skill selection.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from .runtime_behavior_tracer import ExecutionBehavior, ExecutionOutcome

logger = logging.getLogger(__name__)


@dataclass
class SkillStats:
    """Historical performance metrics for a specific skill."""

    skill_id: str
    usage_count: int = 0
    success_count: int = 0
    total_latency_ms: float = 0.0
    last_used: float = field(default_factory=time.time)

    @property
    def success_rate(self) -> float:
        return self.success_count / self.usage_count if self.usage_count > 0 else 0.0

    @property
    def avg_latency_ms(self) -> float:
        return self.total_latency_ms / self.usage_count if self.usage_count > 0 else 0.0


class OnlineLearningCoordinator:
    """Coordinates learning from agent execution in real-time."""

    def __init__(self):
        self.skill_metrics: dict[str, SkillStats] = {}
        self.learning_samples = 0
        self.min_samples_before_adaptation = 10

    async def record_execution_outcome(self, case_id: str, behavior_trace: ExecutionBehavior) -> None:
        """Record the outcome of an execution to update model weights/stats."""
        self.learning_samples += 1

        # Update skill metrics
        retrieved_skills = behavior_trace.metadata.get("retrieved_skill_ids", [])
        outcome = behavior_trace.outcome
        latency = behavior_trace.duration_ms

        for skill_id in retrieved_skills:
            if skill_id not in self.skill_metrics:
                self.skill_metrics[skill_id] = SkillStats(skill_id=skill_id)

            stats = self.skill_metrics[skill_id]
            stats.usage_count += 1
            stats.last_used = time.time()
            stats.total_latency_ms += latency

            if outcome == ExecutionOutcome.SUCCESS:
                stats.success_count += 1

        if self.learning_samples % 10 == 0:
            logger.info(f"🎓 Online Learning Checkpoint: processed {self.learning_samples} execution samples.")

    def get_skill_recommendations(self, skill_ids: list[str]) -> list[str]:
        """Rank and filter skills based on historical effectiveness."""
        if self.learning_samples < self.min_samples_before_adaptation:
            return skill_ids  # Not enough data to rank

        # Sort by success rate then avg latency
        ranked = sorted(
            skill_ids,
            key=lambda sid: (
                self.skill_metrics.get(sid, SkillStats(sid)).success_rate,
                -self.skill_metrics.get(sid, SkillStats(sid)).avg_latency_ms,
            ),
            reverse=True,
        )
        return ranked

    def get_personalized_agent_config(self, agent_role: str, case_category: str) -> dict[str, Any]:
        """Generate optimized config for an agent based on past performance."""
        # Placeholder for dynamic parameter adjustment logic
        return {
            "temperature": 0.7 if case_category == "creative" else 0.1,
            "max_iterations": 5,
            "enable_multi_step_reasoning": True,
        }
