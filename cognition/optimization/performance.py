"""
Performance Optimizer - Cognitive Load and Efficiency Optimization.

Provides performance optimization capabilities:
- Cognitive load optimization
- Break scheduling
- Efficiency analysis
- Resource allocation recommendations
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class LoadLevel(Enum):
    """Cognitive load levels."""

    MINIMAL = "minimal"  # 0-2
    LOW = "low"  # 2-4
    OPTIMAL = "optimal"  # 4-6
    HIGH = "high"  # 6-8
    OVERLOAD = "overload"  # 8-10


class BreakType(Enum):
    """Types of cognitive breaks."""

    MICRO = "micro"  # 1-2 minutes
    SHORT = "short"  # 5-10 minutes
    MEDIUM = "medium"  # 15-20 minutes
    LONG = "long"  # 30+ minutes


@dataclass
class BreakSuggestion:
    """Suggestion for a cognitive break."""

    break_type: BreakType
    duration_minutes: int
    reason: str
    urgency: str  # low, medium, high
    activities: list[str]
    postpone_max_minutes: int = 30

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "break_type": self.break_type.value,
            "duration_minutes": self.duration_minutes,
            "reason": self.reason,
            "urgency": self.urgency,
            "activities": self.activities,
            "postpone_max_minutes": self.postpone_max_minutes,
        }


@dataclass
class OptimizationResult:
    """Result of cognitive load optimization."""

    original_load: float
    optimized_load: float
    reduction_percent: float
    strategies_applied: list[str]
    break_suggestion: BreakSuggestion | None
    recommendations: list[str]
    processing_time_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "original_load": self.original_load,
            "optimized_load": self.optimized_load,
            "reduction_percent": self.reduction_percent,
            "strategies_applied": self.strategies_applied,
            "break_suggestion": self.break_suggestion.to_dict() if self.break_suggestion else None,
            "recommendations": self.recommendations,
            "processing_time_ms": self.processing_time_ms,
        }


@dataclass
class EfficiencyMetrics:
    """Efficiency tracking metrics."""

    session_start: datetime
    tasks_completed: int = 0
    tasks_deferred: int = 0
    breaks_taken: int = 0
    average_task_duration: float = 0.0
    peak_load_reached: float = 0.0
    time_in_optimal: float = 0.0  # percentage
    time_in_overload: float = 0.0  # percentage

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_start": self.session_start.isoformat(),
            "tasks_completed": self.tasks_completed,
            "tasks_deferred": self.tasks_deferred,
            "breaks_taken": self.breaks_taken,
            "average_task_duration": self.average_task_duration,
            "peak_load_reached": self.peak_load_reached,
            "time_in_optimal": self.time_in_optimal,
            "time_in_overload": self.time_in_overload,
        }


class PerformanceOptimizer:
    """
    Cognitive performance optimization system.

    Provides:
    - Real-time cognitive load optimization
    - Break scheduling and suggestions
    - Efficiency tracking and analysis
    - Resource allocation recommendations
    """

    # Break thresholds
    BREAK_THRESHOLDS = {
        BreakType.MICRO: {"load": 6.0, "duration": 45},  # 45 min work
        BreakType.SHORT: {"load": 7.0, "duration": 90},  # 90 min work
        BreakType.MEDIUM: {"load": 8.0, "duration": 120},  # 2 hours work
        BreakType.LONG: {"load": 9.0, "duration": 180},  # 3 hours work
    }

    # Break activities by type
    BREAK_ACTIVITIES = {
        BreakType.MICRO: ["Deep breathing", "Eye rest", "Quick stretch"],
        BreakType.SHORT: ["Walk around", "Drink water", "Look outside"],
        BreakType.MEDIUM: ["Coffee break", "Short walk", "Light exercise"],
        BreakType.LONG: ["Lunch break", "Power nap", "Extended walk"],
    }

    def __init__(self):
        self._current_load = 0.0
        self._load_history: list[tuple[datetime, float]] = []
        self._last_break: datetime | None = None
        self._session_start = datetime.now()
        self._efficiency = EfficiencyMetrics(session_start=self._session_start)
        self._stats = defaultdict(int)

    def optimize_cognitive_load(self, current_load: float) -> OptimizationResult:
        """
        Optimize the current cognitive load.

        Args:
            current_load: Current cognitive load (0-10 scale)

        Returns:
            OptimizationResult with optimization details
        """
        start_time = datetime.now()
        strategies = []
        recommendations = []
        optimized_load = current_load

        # Record load
        self._current_load = current_load
        self._load_history.append((datetime.now(), current_load))
        self._efficiency.peak_load_reached = max(self._efficiency.peak_load_reached, current_load)

        # Get load level
        load_level = self._get_load_level(current_load)

        # Apply optimization strategies based on load level
        if load_level == LoadLevel.OVERLOAD:
            strategies.append("activate_load_shedding")
            recommendations.append("Defer non-critical tasks immediately")
            recommendations.append("Switch to simplified processing mode")
            optimized_load -= 2.0

        elif load_level == LoadLevel.HIGH:
            strategies.append("reduce_complexity")
            recommendations.append("Consider deferring complex analyses")
            recommendations.append("Enable batch processing for notifications")
            optimized_load -= 1.0

        elif load_level == LoadLevel.OPTIMAL:
            strategies.append("maintain_flow")
            recommendations.append("Current load is optimal - maintain pace")

        elif load_level == LoadLevel.LOW:
            strategies.append("capacity_available")
            recommendations.append("Capacity available for complex tasks")
            recommendations.append("Consider pulling work from backlog")

        else:  # MINIMAL
            strategies.append("underutilized")
            recommendations.append("System underutilized - consider consolidating")

        # Check if break is needed
        break_suggestion = self._check_break_needed(current_load)
        if break_suggestion:
            strategies.append("break_recommended")
            recommendations.insert(0, f"Take a {break_suggestion.break_type.value} break")

        # Clamp optimized load
        optimized_load = max(0.0, min(10.0, optimized_load))

        # Calculate reduction
        reduction = ((current_load - optimized_load) / current_load * 100) if current_load > 0 else 0

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        self._stats["optimizations"] += 1

        return OptimizationResult(
            original_load=current_load,
            optimized_load=optimized_load,
            reduction_percent=reduction,
            strategies_applied=strategies,
            break_suggestion=break_suggestion,
            recommendations=recommendations,
            processing_time_ms=processing_time,
        )

    def suggest_breaks(self, current_load: float | None = None) -> list[BreakSuggestion]:
        """
        Suggest cognitive breaks based on current state.

        Args:
            current_load: Current cognitive load (uses stored if not provided)

        Returns:
            List of break suggestions
        """
        load = current_load if current_load is not None else self._current_load
        suggestions = []

        # Check time since last break
        if self._last_break:
            minutes_since_break = (datetime.now() - self._last_break).total_seconds() / 60
        else:
            minutes_since_break = (datetime.now() - self._session_start).total_seconds() / 60

        # Determine break type based on load and time
        for break_type, threshold in self.BREAK_THRESHOLDS.items():
            if load >= threshold["load"] or minutes_since_break >= threshold["duration"]:
                urgency = "high" if load >= 8.0 else "medium" if load >= 6.0 else "low"

                suggestion = BreakSuggestion(
                    break_type=break_type,
                    duration_minutes=self._get_break_duration(break_type),
                    reason=self._get_break_reason(load, minutes_since_break, break_type),
                    urgency=urgency,
                    activities=self.BREAK_ACTIVITIES[break_type],
                    postpone_max_minutes=15 if urgency == "high" else 30,
                )
                suggestions.append(suggestion)

                if urgency == "high":
                    break  # Only suggest one high-urgency break

        self._stats["break_suggestions"] += len(suggestions)
        return suggestions

    def record_break_taken(self, break_type: BreakType) -> None:
        """Record that a break was taken."""
        self._last_break = datetime.now()
        self._efficiency.breaks_taken += 1
        self._stats["breaks_recorded"] += 1

        # Reduce load after break
        reductions = {
            BreakType.MICRO: 0.5,
            BreakType.SHORT: 1.0,
            BreakType.MEDIUM: 2.0,
            BreakType.LONG: 3.0,
        }
        self._current_load = max(0.0, self._current_load - reductions.get(break_type, 1.0))

    def record_task_completion(self, duration_minutes: float = 30) -> None:
        """Record a completed task."""
        self._efficiency.tasks_completed += 1

        # Update average duration
        total = self._efficiency.average_task_duration * (self._efficiency.tasks_completed - 1) + duration_minutes
        self._efficiency.average_task_duration = total / self._efficiency.tasks_completed

    def record_task_deferred(self) -> None:
        """Record a deferred task."""
        self._efficiency.tasks_deferred += 1

    def get_efficiency_report(self) -> dict[str, Any]:
        """Generate an efficiency report for the current session."""
        # Calculate time distribution
        total_time = (datetime.now() - self._session_start).total_seconds()
        if total_time > 0 and self._load_history:
            optimal_time = (
                sum(1 for _, load in self._load_history if 4.0 <= load <= 6.0) / len(self._load_history) * 100
            )

            overload_time = sum(1 for _, load in self._load_history if load > 8.0) / len(self._load_history) * 100

            self._efficiency.time_in_optimal = optimal_time
            self._efficiency.time_in_overload = overload_time

        # Build report
        report = {
            "session_duration_minutes": total_time / 60,
            "efficiency_metrics": self._efficiency.to_dict(),
            "current_load": self._current_load,
            "current_load_level": self._get_load_level(self._current_load).value,
            "recommendations": self._generate_efficiency_recommendations(),
        }

        return report

    def _get_load_level(self, load: float) -> LoadLevel:
        """Get load level for a given load value."""
        if load <= 2.0:
            return LoadLevel.MINIMAL
        elif load <= 4.0:
            return LoadLevel.LOW
        elif load <= 6.0:
            return LoadLevel.OPTIMAL
        elif load <= 8.0:
            return LoadLevel.HIGH
        else:
            return LoadLevel.OVERLOAD

    def _check_break_needed(self, load: float) -> BreakSuggestion | None:
        """Check if a break is needed and return suggestion."""
        suggestions = self.suggest_breaks(load)
        return suggestions[0] if suggestions else None

    def _get_break_duration(self, break_type: BreakType) -> int:
        """Get duration in minutes for a break type."""
        durations = {
            BreakType.MICRO: 2,
            BreakType.SHORT: 10,
            BreakType.MEDIUM: 20,
            BreakType.LONG: 45,
        }
        return durations.get(break_type, 10)

    def _get_break_reason(self, load: float, minutes_worked: float, break_type: BreakType) -> str:
        """Generate reason for break suggestion."""
        reasons = []

        if load >= 8.0:
            reasons.append("cognitive load is very high")
        elif load >= 6.0:
            reasons.append("cognitive load is elevated")

        if minutes_worked >= 120:
            reasons.append(f"worked {int(minutes_worked)} minutes without break")
        elif minutes_worked >= 60:
            reasons.append(f"worked {int(minutes_worked)} minutes")

        if not reasons:
            reasons.append("preventive rest recommended")

        return " and ".join(reasons).capitalize()

    def _generate_efficiency_recommendations(self) -> list[str]:
        """Generate recommendations based on efficiency metrics."""
        recommendations = []

        if self._efficiency.time_in_overload > 20:
            recommendations.append("Spending too much time in overload - consider better task distribution")

        if self._efficiency.breaks_taken < self._efficiency.tasks_completed / 5:
            recommendations.append("Taking too few breaks - schedule regular rest periods")

        if self._efficiency.tasks_deferred > self._efficiency.tasks_completed:
            recommendations.append("High deferral rate - review task prioritization")

        if self._efficiency.time_in_optimal > 60:
            recommendations.append("Excellent! Maintaining optimal cognitive load most of the time")

        if not recommendations:
            recommendations.append("Session performance is within normal parameters")

        return recommendations

    def reset_session(self) -> None:
        """Reset session data."""
        self._session_start = datetime.now()
        self._efficiency = EfficiencyMetrics(session_start=self._session_start)
        self._load_history.clear()
        self._last_break = None
        self._current_load = 0.0

    def get_stats(self) -> dict[str, Any]:
        """Get optimizer statistics."""
        return {
            **dict(self._stats),
            "current_load": self._current_load,
            "load_level": self._get_load_level(self._current_load).value,
            "session_duration_minutes": (datetime.now() - self._session_start).total_seconds() / 60,
            "load_history_size": len(self._load_history),
        }


# Singleton instance
_optimizer: PerformanceOptimizer | None = None


def get_performance_optimizer() -> PerformanceOptimizer:
    """Get the singleton PerformanceOptimizer instance."""
    global _optimizer
    if _optimizer is None:
        _optimizer = PerformanceOptimizer()
    return _optimizer
