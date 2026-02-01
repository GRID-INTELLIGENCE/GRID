"""
NSR (Natural Skill Response) Tracker for GRID Skills System.
Tracks skill execution patterns and response characteristics.
"""

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class NSRMetrics:
    """Metrics for Natural Skill Response tracking."""

    skill_name: str
    execution_time: float
    success: bool
    response_length: int
    confidence_score: float
    timestamp: float
    user_satisfaction: float | None = None


class NSRTracker:
    """Tracks and analyzes skill execution patterns."""

    def __init__(self, storage_path: Path | None = None):
        self.storage_path = storage_path or Path("logs/nsr_metrics.json")
        self.metrics: list[NSRMetrics] = []
        self._load_metrics()

    def track_execution(
        self, skill_name: str, execution_time: float, success: bool, response_length: int, confidence_score: float
    ) -> NSRMetrics:
        """Track a skill execution."""
        metric = NSRMetrics(
            skill_name=skill_name,
            execution_time=execution_time,
            success=success,
            response_length=response_length,
            confidence_score=confidence_score,
            timestamp=time.time(),
        )

        self.metrics.append(metric)
        self._save_metrics()
        return metric

    def get_skill_stats(self, skill_name: str) -> dict[str, Any]:
        """Get statistics for a specific skill."""
        skill_metrics = [m for m in self.metrics if m.skill_name == skill_name]

        if not skill_metrics:
            return {"error": f"No metrics found for skill: {skill_name}"}

        success_rate = sum(1 for m in skill_metrics if m.success) / len(skill_metrics)
        avg_execution_time = sum(m.execution_time for m in skill_metrics) / len(skill_metrics)
        avg_confidence = sum(m.confidence_score for m in skill_metrics) / len(skill_metrics)

        return {
            "skill_name": skill_name,
            "total_executions": len(skill_metrics),
            "success_rate": success_rate,
            "avg_execution_time": avg_execution_time,
            "avg_confidence_score": avg_confidence,
            "last_execution": max(m.timestamp for m in skill_metrics),
        }

    def get_overall_stats(self) -> dict[str, Any]:
        """Get overall NSR statistics."""
        if not self.metrics:
            return {"error": "No metrics available"}

        total_executions = len(self.metrics)
        success_rate = sum(1 for m in self.metrics if m.success) / total_executions
        avg_execution_time = sum(m.execution_time for m in self.metrics) / total_executions

        # Skill breakdown
        skill_counts: dict[str, int] = {}
        for metric in self.metrics:
            skill_counts[metric.skill_name] = skill_counts.get(metric.skill_name, 0) + 1

        return {
            "total_executions": total_executions,
            "success_rate": success_rate,
            "avg_execution_time": avg_execution_time,
            "unique_skills": len(skill_counts),
            "skill_breakdown": skill_counts,
        }

    def _load_metrics(self) -> None:
        """Load metrics from storage."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path) as f:
                    data = json.load(f)
                    self.metrics = [NSRMetrics(**m) for m in data]
            except Exception:
                self.metrics = []

    def _save_metrics(self) -> None:
        """Save metrics to storage."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, "w") as f:
            json.dump([asdict(m) for m in self.metrics], f, indent=2)

    def clear_metrics(self) -> None:
        """Clear all metrics."""
        self.metrics = []
        self._save_metrics()
