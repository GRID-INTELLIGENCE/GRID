"""Agent Intelligence Evaluator for GRID Agentic System.

Analyzes execution patterns and behavioral traces to improve agent decision
quality, task routing, and skill effectiveness.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from .runtime_behavior_tracer import ExecutionBehavior, ExecutionOutcome

logger = logging.getLogger(__name__)


@dataclass
class BehavioralPattern:
    """Detected pattern in an agent's behavior."""

    pattern_id: str
    agent_role: str
    description: str
    occurrences: int
    confidence_impact: float  # +/- impact on decision confidence


@dataclass
class AgentPerformanceMetrics:
    """Consolidated performance metrics for an agent role."""

    success_rate: float
    average_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    error_rate: float
    common_errors: list[str]
    skill_effectiveness: float  # 0.0 to 1.0


class AgentIntelligenceEvaluator:
    """Analyzes agent behavior to improve future decisions."""

    def __init__(self, history_provider: Any = None):
        self.history_provider = history_provider
        self._patterns: list[BehavioralPattern] = []

    def evaluate_agent_performance(self, agent_role: str, traces: list[ExecutionBehavior]) -> AgentPerformanceMetrics:
        """Analyze a list of traces to generate performance metrics."""
        role_traces = [t for t in traces if t.agent_role == agent_role]
        if not role_traces:
            return AgentPerformanceMetrics(0, 0, 0, 0, 0, [], 0)

        successes = [t for t in role_traces if t.outcome == ExecutionOutcome.SUCCESS]
        latencies = [t.duration_ms for t in role_traces]
        sorted_latencies = sorted(latencies)

        # Calculate error categories
        errors = [t.error_category for t in role_traces if t.error_category]
        error_counts = {}
        for err in errors:
            error_counts[err] = error_counts.get(err, 0) + 1
        common_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        # Skill effectiveness: ratio of skills used vs retrieved in successful tasks
        skill_usage_ratios = [t.skills_used / t.skills_retrieved if t.skills_retrieved > 0 else 0 for t in successes]
        avg_skill_eff = sum(skill_usage_ratios) / len(skill_usage_ratios) if skill_usage_ratios else 0

        return AgentPerformanceMetrics(
            success_rate=len(successes) / len(role_traces),
            average_latency_ms=sum(latencies) / len(latencies),
            p50_latency_ms=sorted_latencies[len(sorted_latencies) // 2],
            p95_latency_ms=sorted_latencies[int(len(sorted_latencies) * 0.95)],
            error_rate=(len(role_traces) - len(successes)) / len(role_traces),
            common_errors=[e[0] for e in common_errors],
            skill_effectiveness=avg_skill_eff,
        )

    def detect_behavioral_patterns(
        self, agent_role: str, traces: list[ExecutionBehavior], min_occurrences: int = 5
    ) -> list[BehavioralPattern]:
        """Detect recurring behavioral patterns from traces."""
        patterns = []
        role_traces = [t for t in traces if t.agent_role == agent_role]

        # Pattern 1: High confidence but failure (Overconfidence)
        overconfident_failures = [
            t for t in role_traces if t.outcome == ExecutionOutcome.FAILURE and t.confidence > 0.8
        ]
        if len(overconfident_failures) >= min_occurrences:
            patterns.append(
                BehavioralPattern(
                    pattern_id="overconfidence",
                    agent_role=agent_role,
                    description="High confidence in failing tasks",
                    occurrences=len(overconfident_failures),
                    confidence_impact=-0.2,
                )
            )

        # Pattern 2: Success requiring multiple fallbacks
        fallback_successes = [t for t in role_traces if t.outcome == ExecutionOutcome.SUCCESS and t.fallback_used]
        if len(fallback_successes) >= min_occurrences:
            patterns.append(
                BehavioralPattern(
                    pattern_id="fallback_reliability",
                    agent_role=agent_role,
                    description="Consistently succeeds only after using fallback strategies",
                    occurrences=len(fallback_successes),
                    confidence_impact=0.1,
                )
            )

        return patterns

    def recommend_task_routing(
        self, case_metadata: dict[str, Any], historical_stats: dict[str, AgentPerformanceMetrics]
    ) -> str:
        """Recommend the best agent role for a task based on historical performance."""
        # Simple heuristic: Success Rate / Average Latency
        scores = {}
        for role, stats in historical_stats.items():
            if stats.success_rate > 0:
                # Latency in seconds for normalization
                scores[role] = stats.success_rate / (stats.average_latency_ms / 1000.0)
            else:
                scores[role] = 0.0

        if not scores:
            return "Analyst"  # Default fallback

        return max(scores.items(), key=lambda x: x[1])[0]
