"""Advanced Time Manager.

Implements temporal pattern analysis with:
- detect_temporal_pattern: Detect patterns in temporal data
- predict_next_event: Predict next likely event based on patterns
- analyze_temporal_distribution: Analyze distribution of events over time
"""

from __future__ import annotations

import logging
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any, Callable
from statistics import mean, stdev
from itertools import groupby

logger = logging.getLogger(__name__)


class TemporalPattern(str, Enum):
    """Types of temporal patterns."""

    REGULAR = "regular"
    SEASONAL = "seasonal"
    TRENDING = "trending"
    CYCLICAL = "cyclic"
    RANDOM = "random"
    BURST = "burst"
    GAP = "gap"


class EventFrequency(str, Enum):
    """Frequency levels for events."""

    CONSTANT = "constant"
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VARIABLE = "variable"


@dataclass
class TemporalEvent:
    """A temporal event for analysis."""

    timestamp: datetime
    event_type: str
    value: float | None = None
    duration_seconds: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TemporalPatternDetection:
    """Result of temporal pattern detection."""

    pattern_type: TemporalPattern
    pattern_name: str
    confidence: float  # 0.0 to 1.0
    frequency: EventFrequency
    period_seconds: float | None = None
    amplitude: float | None = None
    trend_slope: float | None = None  # -1.0 to 1.0
    phase: float | None = None  # Phase in cycle (0 to 2*pi)
    description: str = ""
    features: dict[str, Any] = field(default_factory=dict)
    predictions: list[str] = field(default_factory=list)


@dataclass
class TemporalDistribution:
    """Analysis of temporal event distribution."""

    total_events: int
    time_span_seconds: float
    event_frequency: float  # events per second
    by_hour: dict[int, int] = field(default_factory=dict)
    by_day_of_week: dict[int, int] = field(default_factory=dict)
    peak_hour: int
    peak_count: int
    quiet_hours: list[int]
    variance: float = 0.0
    trend: str = "stable"


class AdvancedTimeManager:
    """Advanced time manager for temporal pattern analysis.

    Features:
    - Temporal pattern detection
    - Next event prediction
    - Temporal distribution analysis
    - Anomaly detection
    - Seasonal decomposition
    """

    def __init__(self):
        self._events: list[TemporalEvent] = []
        self._window_size = 100  # Rolling window for analysis
        self._event_patterns: defaultdict(int) = defaultdict(int)

    def add_event(self, event: TemporalEvent) -> None:
        """Add an event for temporal analysis.

        Args:
            event: Temporal event to add
        """
        self._events.append(event)
        if len(self._events) > 10000:
            # Keep only recent events
            self._events = self._events[-10000:]

    def detect_temporal_pattern(self, min_events: int = 10) -> TemporalPatternDetection:
        """Detect temporal patterns in the event data.

        Args:
            min_events: Minimum events required for analysis

        Returns:
            Temporal pattern detection result
        """
        if len(self._events) < min_events:
            logger.warning(f"Insufficient events for pattern detection: {len(self._events)} < {min_events}")
            return TemporalPatternDetection(
                pattern_type=TemporalPattern.RANDOM,
                pattern_name="insufficient_data",
                confidence=0.0,
                frequency=EventFrequency.VARIABLE,
                description=f"Need at least {min_events} events",
            )

        # Calculate inter-event intervals
        intervals = []
        for i in range(1, len(self._events)):
            prev_event = self._events[i - 1]
            interval_seconds = (self._events[i].timestamp - prev_event.timestamp).total_seconds()
            if interval_seconds > 0 and interval_seconds < 86400:  # Ignore gaps > 24 hours
                intervals.append(interval_seconds)

        if not intervals:
            return TemporalPatternDetection(
                pattern_type=TemporalPattern.RANDOM,
                pattern_name="no_valid_intervals",
                confidence=0.0,
                frequency=EventFrequency.VARIABLE,
                description="No valid time intervals found",
            )

        # Analyze interval frequency
        interval_counts = Counter(round(i) for i in intervals)
        most_common_interval = interval_counts.most_common(1)[0]
        interval_mode = self._determine_frequency_mode(interval_counts)

        # Calculate amplitude (for regularity)
        if len(intervals) >= 5:
            interval_values = [intervals[i] for i in range(5)]
            amplitude = max(interval_values) - min(interval_values)
        else:
            amplitude = 0.0

        # Check for trend
        if len(intervals) >= 3:
            # Simple linear regression
            x_indices = list(range(len(intervals)))
            y_values = intervals
            try:
                slope, intercept = self._calculate_trend_slope(x_indices, y_values)
            except Exception:
                slope, intercept = 0.0, 0.0
        else:
            slope, intercept = 0.0, 0.0

        # Determine pattern type
        pattern_type, pattern_name, confidence = self._classify_pattern(
            interval_mode, most_common_interval, amplitude, slope
        )

        # Calculate phase (for cyclic patterns)
        phase = None
        if pattern_type == TemporalPattern.CYCLICAL:
            if slope > 0.05:
                phase = 0.5  # First half of cycle
            elif slope < -0.05:
                phase = 1.5  # Second half
            else:
                # More observations needed for phase detection
                phase = None

        return TemporalPatternDetection(
            pattern_type=pattern_type,
            pattern_name=pattern_name,
            confidence=confidence,
            frequency=EventFrequency(interval_mode),
            period_seconds=most_common_interval,
            amplitude=amplitude,
            trend_slope=slope,
            trend_direction=self._get_trend_direction(slope),
            phase=phase,
            description=self._generate_pattern_description(interval_mode, most_common_interval, amplitude, slope, phase),
            features={
                "interval_stats": {
                    "mean_interval_seconds": mean(intervals),
                    "most_common_interval": most_common_interval,
                    "interval_variance": stdev(intervals) if len(intervals) >= 2 else 0.0,
                },
            },
            predictions=[],
        )

    def _determine_frequency_mode(self, interval_counts: Counter) -> EventFrequency:
        """Determine if events are at regular, increasing, decreasing, stable, or variable."""
        counts = list(interval_counts.values())

        if len(counts) == 1:
            return EventFrequency.CONSTANT

        # Check variance
        if len(counts) >= 2:
            variance = stdev(counts) if len(counts) > 1 else 0.0

            # Mean to variance ratio
            mean_interval = sum(counts) / len(counts)
            if mean_interval > 0:
                cv = variance / mean_interval
            else:
                cv = 0.0

            if cv < 0.1:
                return EventFrequency.STABLE
            elif cv > 0.3:
                return EventFrequency.VARIABLE
            else:
                return EventFrequency.VARIABLE

        return EventFrequency.INCREASING if counts[0] < counts[-1] else EventFrequency.DECREASING

    def _classify_pattern(
        self,
        interval_mode: EventFrequency,
        most_common_interval: float,
        amplitude: float,
        slope: float,
    ) -> tuple[TemporalPattern, str, float]:
        """Classify the temporal pattern type and return confidence."""
        confidence = 0.5

        # Check for cyclic pattern
        if interval_mode == EventFrequency.STABLE and amplitude > 0:
            pattern_type = TemporalPattern.CYCLICAL
            pattern_name = "cyclic_stable"
            confidence = 0.9

        elif interval_mode == EventFrequency.CONSTANT:
            pattern_type = TemporalPattern.REGULAR
            pattern_name = "regular_constant"
            confidence = 0.95

        elif interval_mode in [EventFrequency.INCREASING, EventFrequency.DECREASING]:
            if amplitude < 0.1:
                pattern_type = TemporalPattern.TRENDING
                pattern_name = "trending_up" if slope > 0 else "trending_down"
                confidence = 0.7
            elif amplitude > 0.3:
                pattern_type = TemporalPattern.BURST
                pattern_name = "burst_up" if slope > 0 else "burst_down"
                confidence = 0.8
            else:
                pattern_type = TemporalPattern.TRENDING
                pattern_name = "trending_flat" if abs(slope) < 0.05 else "trending"
                confidence = 0.6

        elif interval_mode == EventFrequency.VARIABLE:
            pattern_type = TemporalPattern.RANDOM
            pattern_name = "irregular"
            confidence = 0.3

        else:
            pattern_type = TemporalPattern.CYCLICAL
            pattern_name = "semi_cyclic"
            confidence = 0.6

        return pattern_type, pattern_name, confidence

    def _get_trend_direction(self, slope: float) -> str:
        """Get trend direction description."""
        if slope > 0.1:
            return "increasing"
        elif slope < -0.1:
            return "decreasing"
        elif abs(slope) < 0.05:
            return "stable"
        else:
            return "flat"

    def _generate_pattern_description(
        self,
        interval_mode: EventFrequency,
        most_common_interval: float,
        amplitude: float,
        slope: float,
        phase: float | None = None,
    ) -> str:
        """Generate human-readable pattern description."""
        parts = []

        if interval_mode == EventFrequency.CONSTANT:
            parts.append(f"Events occur every {most_common_interval:.1f} seconds consistently.")
        elif interval_mode == EventFrequency.STABLE:
            parts.append(f"Stable rhythm with {most_common_interval:.1f}s intervals, amplitude {amplitude:.2f}.")
        elif interval_mode == EventFrequency.INCREASING:
            parts.append("Time between events is increasing.")
        elif interval_mode == EventFrequency.DECREASING:
            parts.append("Time between events is decreasing.")
        else:
            parts.append("Variable timing patterns.")

        if slope:
            parts.append(f"{'Trend direction': self._get_trend_direction(slope)}.")
        if amplitude:
            parts.append(f"Amplitude: {amplitude:.2f}x magnitude.")

        if phase is not None:
            parts.append(f"Cycle phase: {phase:.2f}π.")

        return ". ".join(parts)

    def predict_next_event(self, lookahead_seconds: int = 60) -> datetime | None:
        """Predict the next likely event time.

        Args:
            lookahead_seconds: How far ahead to look (in seconds)

        Returns:
            Predicted timestamp or None if no pattern detected
        """
        if len(self._events) < 2:
            return None

        # Use last known interval as prediction
        last_interval = self._events[-1].timestamp - self._events[-2].timestamp
        prediction = self._events[-1].timestamp + timedelta(seconds=last_interval.total_seconds())
        return prediction

    def analyze_temporal_distribution(self) -> TemporalDistribution:
        """Analyze the distribution of events over time.

        Returns:
            Temporal distribution analysis
        """
        if not self._events:
            return TemporalDistribution(
                total_events=0,
                time_span_seconds=0.0,
                event_frequency=0.0,
                by_hour={},
                by_day_of_week={},
                peak_hour=0,
                peak_count=0,
                quiet_hours=[],
                variance=0.0,
                trend="stable",
            )

        # Calculate time span
        first_event = self._events[0].timestamp
        last_event = self._events[-1].timestamp
        time_span_seconds = (last_event - first_event).total_seconds()

        # Count events by hour
        hour_counts: defaultdict(int)
        for event in self._events:
            hour = event.timestamp.hour
            hour_counts[hour] += 1

        # Count events by day of week
        day_counts = defaultdict(int)
        for event in self._events:
            day_of_week = event.timestamp.weekday()  # 0=Monday, 6=Sunday
            day_counts[day_of_week] += 1

        # Find peak hour
        peak_hour = max(hour_counts.items(), key=lambda x: x[1])[0]

        # Find quiet hours (hours with < 10% of peak)
        quiet_hours = [
            h for h, count in sorted(hour_counts.items())
            if count < peak_count * 0.1
        ]

        # Calculate variance
        hourly_values = list(hour_counts.values())
        variance = stdev(hourly_values) if len(hourly_values) > 1 else 0.0

        # Determine trend
        if len(hourly_values) >= 7:
            # Check for weekly trend
            avg_first = mean(hourly_values[:3])
            avg_last = mean(hourly_values[-3:])
            if avg_last > avg_first * 1.1:
                trend = "increasing_weekly"
            elif avg_last < avg_first * 0.9:
                trend = "decreasing_weekly"
            else:
                trend = "stable_weekly"
        else:
            trend = "insufficient_data"

        return TemporalDistribution(
            total_events=len(self._events),
            time_span_seconds=time_span_seconds,
            event_frequency=len(self._events) / time_span_seconds,
            by_hour=hour_counts,
            by_day_of_week=day_counts,
            peak_hour=peak_hour,
            peak_count=peak_count,
            quiet_hours=quiet_hours,
            variance=variance,
            trend=trend,
        )
