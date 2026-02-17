"""Analyzes skill behavior patterns for optimization opportunities."""

import logging
import statistics
from dataclasses import dataclass
from enum import Enum
from typing import Any


class BehavioralPattern(str, Enum):
    ALWAYS_SUCCEEDS = "always_succeeds"
    ALWAYS_FAILS = "always_fails"
    SLOW_PERFORMANCE = "slow_performance"
    INCONSISTENT_CONFIDENCE = "inconsistent_confidence"
    HIGH_FALLBACK_RATE = "high_fallback_rate"


@dataclass
class BehavioralAnalysis:
    skill_id: str
    pattern: BehavioralPattern
    severity: float  # 0-1
    evidence: list[str]
    recommendation: str


class BehavioralAnalyzer:
    """Analyzes skill behavior patterns for optimization opportunities."""

    def __init__(self, execution_tracker: Any, intelligence_tracker: Any):
        self._execution_tracker = execution_tracker
        self._intelligence_tracker = intelligence_tracker
        self._logger = logging.getLogger(__name__)

    def analyze_skill_behavior(self, skill_id: str) -> list[BehavioralAnalysis]:
        """Analyze behavior patterns for a specific skill."""
        analyses = []

        # Get execution history
        executions = self._execution_tracker.get_execution_history(skill_id)
        if not executions:
            return analyses

        # Pattern 1: Always succeeds
        successes = [r for r in executions if r.status == "success"]
        success_rate = len(successes) / len(executions)
        if success_rate == 1.0 and len(executions) >= 10:
            analyses.append(
                BehavioralAnalysis(
                    skill_id=skill_id,
                    pattern=BehavioralPattern.ALWAYS_SUCCEEDS,
                    severity=0.1,  # Low severity - good pattern
                    evidence=[f"Success rate: {success_rate:.2f}"],
                    recommendation="Consider increasing confidence threshold or reducing logging for this stable skill",
                )
            )

        # Pattern 2: Always fails
        if success_rate == 0.0 and len(executions) >= 5:
            analyses.append(
                BehavioralAnalysis(
                    skill_id=skill_id,
                    pattern=BehavioralPattern.ALWAYS_FAILS,
                    severity=0.9,  # High severity
                    evidence=[f"Success rate: {success_rate:.2f}"],
                    recommendation="Investigate skill implementation or inputs immediately",
                )
            )

        # Pattern 3: Slow performance
        avg_latency = sum(r.execution_time_ms for r in executions) / len(executions)
        if avg_latency > 5000:  # >5 seconds
            analyses.append(
                BehavioralAnalysis(
                    skill_id=skill_id,
                    pattern=BehavioralPattern.SLOW_PERFORMANCE,
                    severity=0.7,
                    evidence=[f"Average latency: {avg_latency:.0f}ms"],
                    recommendation="Optimize skill implementation or increase timeout",
                )
            )

        # Pattern 4: Inconsistent confidence
        confidences = [r.confidence_score for r in executions if r.confidence_score is not None]
        if len(confidences) >= 5:
            std_dev = statistics.stdev(confidences) if len(confidences) > 1 else 0
            if std_dev > 0.3:  # High variance
                analyses.append(
                    BehavioralAnalysis(
                        skill_id=skill_id,
                        pattern=BehavioralPattern.INCONSISTENT_CONFIDENCE,
                        severity=0.5,
                        evidence=[f"Confidence std dev: {std_dev:.2f}"],
                        recommendation="Review confidence scoring logic for deterministic behavior",
                    )
                )

        # Pattern 5: High fallback rate
        fallback_rate = sum(1 for r in executions if r.fallback_used) / len(executions)
        if fallback_rate > 0.3:  # >30% fallback rate
            analyses.append(
                BehavioralAnalysis(
                    skill_id=skill_id,
                    pattern=BehavioralPattern.HIGH_FALLBACK_RATE,
                    severity=0.6,
                    evidence=[f"Fallback rate: {fallback_rate:.2f}"],
                    recommendation="Improve primary implementation or increase fallback threshold",
                )
            )

        return analyses

    def get_optimization_recommendations(self, skill_id: str) -> list[str]:
        """Get optimization recommendations for a skill."""
        analyses = self.analyze_skill_behavior(skill_id)
        recommendations = [a.recommendation for a in analyses if a.severity >= 0.5]

        # Add intelligence-based recommendations
        intelligence = self._intelligence_tracker.get_intelligence_patterns(skill_id)
        if intelligence and intelligence.get("avg_confidence", 1.0) < 0.7:
            recommendations.append("Improve decision confidence scoring based on intelligence patterns")

        return recommendations
