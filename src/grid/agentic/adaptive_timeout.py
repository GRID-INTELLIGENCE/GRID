"""Adaptive Timeout Manager for GRID Agentic System.

Manages dynamic timeouts for agent operations based on historical performance
to optimize execution speed and reliability.
"""

from __future__ import annotations

import logging
import statistics
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TaskPerformanceBucket:
    """Stores execution time history for a specific task/role combination."""

    task_type: str
    agent_role: str
    execution_times: list[float] = field(default_factory=list)
    success_count: int = 0
    failure_count: int = 0
    max_history: int = 100

    def add_record(self, duration_ms: float, success: bool) -> None:
        """Add a new performance record."""
        self.execution_times.append(duration_ms)
        if len(self.execution_times) > self.max_history:
            self.execution_times.pop(0)

        if success:
            self.success_count += 1
        else:
            self.failure_count += 1

    def get_percentile(self, p: float = 0.95) -> float | None:
        """Calculate the p-th percentile execution time."""
        if not self.execution_times:
            return None
        sorted_times = sorted(self.execution_times)
        index = int(len(sorted_times) * p)
        return sorted_times[min(index, len(sorted_times) - 1)]


class AdaptiveTimeoutManager:
    """Manages adaptive timeouts for agent operations."""

    def __init__(
        self,
        default_base_ms: float = 5000.0,
        min_timeout_ms: float = 500.0,
        max_timeout_ms: float = 60000.0,
    ):
        self.default_base_ms = default_base_ms
        self.min_timeout_ms = min_timeout_ms
        self.max_timeout_ms = max_timeout_ms
        self._buckets: dict[str, TaskPerformanceBucket] = {}

    def _get_bucket_key(self, task_type: str, agent_role: str) -> str:
        return f"{agent_role}:{task_type}"

    def get_timeout_for_task(
        self,
        task_type: str,
        agent_role: str,
        complexity_score: float = 0.5,
    ) -> float:
        """Get recommended timeout for a specific task and role.

        Args:
            task_type: Type of task (e.g., '/execute')
            agent_role: Role of the agent
            complexity_score: Estimated task complexity (0.0 to 1.0)

        Returns:
            Timeout in milliseconds
        """
        key = self._get_bucket_key(task_type, agent_role)
        bucket = self._buckets.get(key)

        if not bucket or len(bucket.execution_times) < 5:
            # Fallback to base timeout with complexity multiplier
            return max(self.min_timeout_ms, self.default_base_ms * (1.0 + complexity_score))

        # Use 95th percentile with a small safety margin
        p95 = bucket.get_percentile(0.95)
        if p95 is None:
            return max(self.min_timeout_ms, self.default_base_ms * (1.0 + complexity_score))

        # Apply complexity adjustment if recent history is thin or task is unusually complex
        recommended = p95 * 1.2 * (1.0 + complexity_score * 0.5)

        return max(self.min_timeout_ms, min(self.max_timeout_ms, recommended))

    def record_execution_time(
        self,
        task_type: str,
        agent_role: str,
        execution_time_ms: float,
        success: bool,
    ) -> None:
        """Record the actual execution time for a task."""
        key = self._get_bucket_key(task_type, agent_role)
        if key not in self._buckets:
            self._buckets[key] = TaskPerformanceBucket(task_type=task_type, agent_role=agent_role)

        self._buckets[key].add_record(execution_time_ms, success)

        if execution_time_ms > self.max_timeout_ms:
            logger.warning(f"⚠️ Task {key} exceeded max expected timeout: {execution_time_ms:.2f}ms")

    def get_metrics_summary(self) -> dict[str, Any]:
        """Get summary of performance buckets."""
        summary = {}
        for key, bucket in self._buckets.items():
            if bucket.execution_times:
                summary[key] = {
                    "avg_ms": statistics.mean(bucket.execution_times),
                    "p95_ms": bucket.get_percentile(0.95),
                    "success_rate": (
                        bucket.success_count / (bucket.success_count + bucket.failure_count)
                        if (bucket.success_count + bucket.failure_count) > 0
                        else 0
                    ),
                    "samples": len(bucket.execution_times),
                }
        return summary
