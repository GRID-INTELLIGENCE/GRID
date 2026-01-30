"""
Temporal Intelligence - Time-Based Pattern Analysis.

Provides temporal intelligence capabilities:
- Optimal timing prediction for tasks
- Work pattern detection
- Time-based scheduling optimization
- Temporal trend analysis
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class TimePeriod(Enum):
    """Time period classifications."""

    MORNING = "morning"  # 6-12
    AFTERNOON = "afternoon"  # 12-17
    EVENING = "evening"  # 17-21
    NIGHT = "night"  # 21-6


class DayType(Enum):
    """Day type classifications."""

    WEEKDAY = "weekday"
    WEEKEND = "weekend"
    MONDAY = "monday"
    FRIDAY = "friday"


class TaskComplexity(Enum):
    """Task complexity levels."""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    INTENSIVE = "intensive"


@dataclass
class WorkPattern:
    """Represents a detected work pattern."""

    pattern_id: str
    pattern_type: str
    time_period: TimePeriod
    day_type: DayType
    frequency: float  # occurrences per week
    avg_duration_minutes: float
    productivity_score: float
    confidence: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type,
            "time_period": self.time_period.value,
            "day_type": self.day_type.value,
            "frequency": self.frequency,
            "avg_duration_minutes": self.avg_duration_minutes,
            "productivity_score": self.productivity_score,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


@dataclass
class TimingRecommendation:
    """Recommendation for optimal timing."""

    task_type: str
    recommended_period: TimePeriod
    recommended_days: list[str]
    optimal_hour: int
    rationale: str
    confidence: float
    alternatives: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_type": self.task_type,
            "recommended_period": self.recommended_period.value,
            "recommended_days": self.recommended_days,
            "optimal_hour": self.optimal_hour,
            "rationale": self.rationale,
            "confidence": self.confidence,
            "alternatives": self.alternatives,
        }


class TemporalIntelligence:
    """
    Temporal intelligence system for time-based optimization.

    Provides:
    - Optimal timing predictions for different task types
    - Work pattern detection and analysis
    - Temporal trend analysis
    - Schedule optimization recommendations
    """

    # Productivity multipliers by time period
    DEFAULT_PRODUCTIVITY = {
        TimePeriod.MORNING: {
            TaskComplexity.SIMPLE: 0.9,
            TaskComplexity.MODERATE: 1.0,
            TaskComplexity.COMPLEX: 1.2,
            TaskComplexity.INTENSIVE: 1.1,
        },
        TimePeriod.AFTERNOON: {
            TaskComplexity.SIMPLE: 1.0,
            TaskComplexity.MODERATE: 0.9,
            TaskComplexity.COMPLEX: 0.8,
            TaskComplexity.INTENSIVE: 0.7,
        },
        TimePeriod.EVENING: {
            TaskComplexity.SIMPLE: 0.8,
            TaskComplexity.MODERATE: 0.7,
            TaskComplexity.COMPLEX: 0.6,
            TaskComplexity.INTENSIVE: 0.5,
        },
        TimePeriod.NIGHT: {
            TaskComplexity.SIMPLE: 0.5,
            TaskComplexity.MODERATE: 0.4,
            TaskComplexity.COMPLEX: 0.3,
            TaskComplexity.INTENSIVE: 0.2,
        },
    }

    def __init__(self):
        self._activity_log: list[dict[str, Any]] = []
        self._detected_patterns: list[WorkPattern] = []
        self._productivity_scores: dict[str, list[float]] = defaultdict(list)
        self._custom_productivity: dict[str, dict] = {}
        self._stats = defaultdict(int)

    def predict_optimal_timing(
        self,
        task_type: str,
        complexity: TaskComplexity = TaskComplexity.MODERATE,
        duration_minutes: int = 30,
        constraints: dict[str, Any] | None = None,
    ) -> TimingRecommendation:
        """
        Predict the optimal timing for a specific task type.

        Args:
            task_type: Type of task (e.g., "analysis", "coding", "meeting")
            complexity: Task complexity level
            duration_minutes: Expected task duration
            constraints: Optional constraints (e.g., "must_be_morning": True)

        Returns:
            TimingRecommendation with optimal timing details
        """
        constraints = constraints or {}
        datetime.now()

        # Get productivity scores for each period
        scores = {}
        for period in TimePeriod:
            base_score = self.DEFAULT_PRODUCTIVITY[period].get(complexity, 0.5)

            # Apply learned patterns
            learned_multiplier = self._get_learned_multiplier(task_type, period)
            scores[period] = base_score * learned_multiplier

        # Apply constraints
        if constraints.get("must_be_morning"):
            scores = {k: v for k, v in scores.items() if k == TimePeriod.MORNING}
        elif constraints.get("no_afternoon"):
            scores.pop(TimePeriod.AFTERNOON, None)

        # Find optimal period
        if not scores:
            optimal_period = TimePeriod.MORNING
            confidence = 0.3
        else:
            optimal_period = max(scores, key=scores.get)
            max_score = max(scores.values())
            confidence = min(0.95, max_score)

        # Determine optimal hour
        optimal_hour = self._get_optimal_hour(optimal_period, complexity)

        # Get recommended days
        recommended_days = self._get_recommended_days(task_type, complexity)

        # Build rationale
        rationale = self._build_timing_rationale(task_type, complexity, optimal_period, confidence)

        # Build alternatives
        alternatives = []
        for period, score in sorted(scores.items(), key=lambda x: -x[1]):
            if period != optimal_period:
                alternatives.append(
                    {
                        "period": period.value,
                        "score": score,
                        "hour": self._get_optimal_hour(period, complexity),
                    }
                )
                if len(alternatives) >= 2:
                    break

        self._stats["timing_predictions"] += 1

        return TimingRecommendation(
            task_type=task_type,
            recommended_period=optimal_period,
            recommended_days=recommended_days,
            optimal_hour=optimal_hour,
            rationale=rationale,
            confidence=confidence,
            alternatives=alternatives,
        )

    def detect_work_patterns(self) -> list[WorkPattern]:
        """
        Analyze activity log to detect work patterns.

        Returns:
            List of detected work patterns
        """
        if len(self._activity_log) < 10:
            return []

        patterns = []

        # Group activities by time period and day
        grouped = defaultdict(list)
        for activity in self._activity_log:
            timestamp = activity.get("timestamp")
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)

            period = self._get_time_period(timestamp.hour)
            day_type = self._get_day_type(timestamp.weekday())
            key = (period, day_type)
            grouped[key].append(activity)

        # Analyze each group
        for (period, day_type), activities in grouped.items():
            if len(activities) < 3:
                continue

            # Calculate frequency (per week)
            first_ts = min(a["timestamp"] for a in activities)
            last_ts = max(a["timestamp"] for a in activities)
            if isinstance(first_ts, str):
                first_ts = datetime.fromisoformat(first_ts)
            if isinstance(last_ts, str):
                last_ts = datetime.fromisoformat(last_ts)

            weeks = max(1, (last_ts - first_ts).days / 7)
            frequency = len(activities) / weeks

            # Calculate average duration
            durations = [a.get("duration_minutes", 30) for a in activities]
            avg_duration = sum(durations) / len(durations)

            # Calculate productivity score
            success_rate = sum(1 for a in activities if a.get("success", True)) / len(activities)

            pattern = WorkPattern(
                pattern_id=f"pattern_{period.value}_{day_type.value}",
                pattern_type="activity_cluster",
                time_period=period,
                day_type=day_type,
                frequency=frequency,
                avg_duration_minutes=avg_duration,
                productivity_score=success_rate,
                confidence=min(0.9, len(activities) / 20),
            )
            patterns.append(pattern)

        self._detected_patterns = patterns
        self._stats["pattern_detections"] += 1

        return patterns

    def log_activity(
        self,
        task_type: str,
        timestamp: datetime | None = None,
        duration_minutes: int = 30,
        success: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Log an activity for pattern learning.

        Args:
            task_type: Type of task
            timestamp: When the activity occurred
            duration_minutes: How long it took
            success: Whether it was successful
            metadata: Additional metadata
        """
        timestamp = timestamp or datetime.now()

        activity = {
            "task_type": task_type,
            "timestamp": timestamp.isoformat(),
            "duration_minutes": duration_minutes,
            "success": success,
            "hour": timestamp.hour,
            "weekday": timestamp.weekday(),
            "metadata": metadata or {},
        }

        self._activity_log.append(activity)

        # Limit log size
        if len(self._activity_log) > 1000:
            self._activity_log = self._activity_log[-1000:]

        # Update productivity scores
        period = self._get_time_period(timestamp.hour)
        key = f"{task_type}_{period.value}"
        score = 1.0 if success else 0.5
        self._productivity_scores[key].append(score)

        self._stats["activities_logged"] += 1

    def get_current_period(self) -> TimePeriod:
        """Get the current time period."""
        return self._get_time_period(datetime.now().hour)

    def get_current_day_type(self) -> DayType:
        """Get the current day type."""
        return self._get_day_type(datetime.now().weekday())

    def _get_time_period(self, hour: int) -> TimePeriod:
        """Get time period for an hour."""
        if 6 <= hour < 12:
            return TimePeriod.MORNING
        elif 12 <= hour < 17:
            return TimePeriod.AFTERNOON
        elif 17 <= hour < 21:
            return TimePeriod.EVENING
        else:
            return TimePeriod.NIGHT

    def _get_day_type(self, weekday: int) -> DayType:
        """Get day type for a weekday (0=Monday)."""
        if weekday == 0:
            return DayType.MONDAY
        elif weekday == 4:
            return DayType.FRIDAY
        elif weekday < 5:
            return DayType.WEEKDAY
        else:
            return DayType.WEEKEND

    def _get_learned_multiplier(self, task_type: str, period: TimePeriod) -> float:
        """Get learned productivity multiplier."""
        key = f"{task_type}_{period.value}"
        scores = self._productivity_scores.get(key, [])

        if len(scores) < 5:
            return 1.0

        return sum(scores[-10:]) / len(scores[-10:])

    def _get_optimal_hour(self, period: TimePeriod, complexity: TaskComplexity) -> int:
        """Get optimal hour within a period."""
        base_hours = {
            TimePeriod.MORNING: 9,
            TimePeriod.AFTERNOON: 14,
            TimePeriod.EVENING: 18,
            TimePeriod.NIGHT: 22,
        }

        hour = base_hours[period]

        # Adjust for complexity
        if complexity == TaskComplexity.COMPLEX:
            hour = base_hours.get(TimePeriod.MORNING, 9)
        elif complexity == TaskComplexity.SIMPLE:
            hour += 1

        return hour

    def _get_recommended_days(self, task_type: str, complexity: TaskComplexity) -> list[str]:
        """Get recommended days for a task type."""
        if complexity == TaskComplexity.INTENSIVE:
            return ["Tuesday", "Wednesday", "Thursday"]
        elif complexity == TaskComplexity.COMPLEX:
            return ["Monday", "Tuesday", "Wednesday", "Thursday"]
        else:
            return ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    def _build_timing_rationale(
        self,
        task_type: str,
        complexity: TaskComplexity,
        period: TimePeriod,
        confidence: float,
    ) -> str:
        """Build human-readable rationale for timing."""
        parts = []

        parts.append(f"{period.value.capitalize()} is optimal for {complexity.value} tasks")

        if period == TimePeriod.MORNING:
            parts.append("due to higher cognitive freshness and fewer interruptions")
        elif period == TimePeriod.AFTERNOON:
            parts.append("suitable for collaborative and routine work")
        elif period == TimePeriod.EVENING:
            parts.append("better for focused individual work when office is quiet")
        else:
            parts.append("only recommended for urgent or time-sensitive tasks")

        if confidence > 0.8:
            parts.append("(high confidence based on historical patterns)")
        elif confidence > 0.5:
            parts.append("(moderate confidence)")
        else:
            parts.append("(low confidence - more data needed)")

        return " ".join(parts)

    def get_stats(self) -> dict[str, Any]:
        """Get temporal intelligence statistics."""
        return {
            **dict(self._stats),
            "activities_in_log": len(self._activity_log),
            "detected_patterns": len(self._detected_patterns),
            "current_period": self.get_current_period().value,
            "current_day_type": self.get_current_day_type().value,
        }

    def get_patterns(self) -> list[dict[str, Any]]:
        """Get detected work patterns."""
        return [p.to_dict() for p in self._detected_patterns]


# Singleton instance
_temporal: TemporalIntelligence | None = None


def get_temporal_intelligence() -> TemporalIntelligence:
    """Get the singleton TemporalIntelligence instance."""
    global _temporal
    if _temporal is None:
        _temporal = TemporalIntelligence()
    return _temporal
