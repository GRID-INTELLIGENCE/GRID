"""Online learning coordinator for skill ranking and recommendation."""

from dataclasses import dataclass
from typing import Any

from .tracer import ExecutionOutcome


@dataclass
class SkillStats:
    """Statistics for skill usage tracking."""

    skill_id: str
    usage_count: int = 0
    success_count: int = 0
    total_latency_ms: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.usage_count == 0:
            return 0.0
        return self.success_count / self.usage_count

    @property
    def avg_latency_ms(self) -> float:
        """Calculate average latency."""
        if self.usage_count == 0:
            return 0.0
        return self.total_latency_ms / self.usage_count


class LearningCoordinator:
    """Tracks skill usage and provides recommendations based on success rates."""

    def __init__(self) -> None:
        self.skill_metrics: dict[str, SkillStats] = {}
        self.learning_samples: int = 0

    def handle_execution_completed(self, event: dict[str, Any]) -> None:
        """Handle execution completed event."""
        case_id = event.get("case_id")
        trace_id = event.get("trace_id")
        outcome = event.get("outcome")
        duration_ms = event.get("duration_ms", 0)

        if case_id and trace_id and outcome:
            self.record_execution_outcome(
                case_id=case_id, trace_id=trace_id, outcome=outcome, duration_ms=duration_ms
            )

    def record_execution_outcome(
        self, case_id: str, trace_id: str, outcome: ExecutionOutcome, duration_ms: int
    ) -> None:
        """Record the outcome of an execution for learning."""
        # Use case_id as skill_id for tracking
        skill_id = case_id

        if skill_id not in self.skill_metrics:
            self.skill_metrics[skill_id] = SkillStats(skill_id=skill_id)

        stats = self.skill_metrics[skill_id]
        stats.usage_count += 1
        stats.total_latency_ms += duration_ms

        if outcome == ExecutionOutcome.SUCCESS:
            stats.success_count += 1

        self.learning_samples += 1

        # Log checkpoint every 10 samples
        if self.learning_samples % 10 == 0:
            print(
                f"🎓 Online Learning Checkpoint: processed {self.learning_samples} execution samples"
            )

    def get_ranked_skills(self, limit: int = 10) -> list[tuple[str, SkillStats]]:
        """Get skills ranked by success rate and latency."""
        ranked = sorted(
            self.skill_metrics.items(),
            key=lambda item: (item[1].success_rate, -item[1].avg_latency_ms),
            reverse=True,
        )
        return ranked[:limit]

    def recommend_skills(self, task_type: str | None = None, limit: int = 5) -> list[str]:
        """Recommend skills based on historical success rates."""
        ranked = self.get_ranked_skills(limit)
        return [skill_id for skill_id, _ in ranked]

    def get_skill_stats(self, skill_id: str) -> SkillStats | None:
        """Get statistics for a specific skill."""
        return self.skill_metrics.get(skill_id)

    def get_learning_summary(self) -> dict[str, Any]:
        """Get summary of learning progress."""
        if not self.skill_metrics:
            return {"total_skills": 0, "total_executions": 0}

        total_usage = sum(s.usage_count for s in self.skill_metrics.values())
        total_success = sum(s.success_count for s in self.skill_metrics.values())
        overall_success_rate = total_success / total_usage if total_usage > 0 else 0.0

        return {
            "total_skills": len(self.skill_metrics),
            "total_executions": total_usage,
            "overall_success_rate": overall_success_rate,
            "learning_samples": self.learning_samples,
        }
