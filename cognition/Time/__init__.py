"""
Time Module

Provides temporal context and timing mechanisms for cognitive processing.
Handles time-aware operations and temporal pattern analysis.
"""

import logging
import threading
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class TimeUnit(Enum):
    """Time units for temporal operations."""

    MILLISECONDS = "ms"
    SECONDS = "s"
    MINUTES = "min"
    HOURS = "hr"
    DAYS = "day"


class TemporalState(Enum):
    """States in temporal processing."""

    PAST = "past"
    PRESENT = "present"
    FUTURE = "future"
    TIMELESS = "timeless"


@dataclass
class TimeWindow:
    """Represents a time window with start and end times."""

    window_id: str
    start_time: float
    end_time: float | None = None
    duration: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.end_time is None and self.duration is not None:
            self.end_time = self.start_time + self.duration
        elif self.end_time is not None and self.duration is None:
            self.duration = self.end_time - self.start_time

    def contains(self, timestamp: float) -> bool:
        """Check if a timestamp falls within this window."""
        end_time = self.end_time or float("inf")
        return self.start_time <= timestamp <= end_time

    def is_active(self) -> bool:
        """Check if this window is currently active."""
        now = time.time()
        return self.contains(now)

    def overlaps(self, other: "TimeWindow") -> bool:
        """Check if this window overlaps with another."""
        self_end = self.end_time or float("inf")
        other_end = other.end_time or float("inf")
        return (self.start_time <= other_end) and (other.start_time <= self_end)


@dataclass
class TemporalContext:
    """Temporal context for cognitive operations."""

    context_id: str
    current_time: float = field(default_factory=time.time)
    timezone_offset: float = 0.0  # Hours from UTC
    time_windows: list[TimeWindow] = field(default_factory=list)
    temporal_patterns: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_window(self, window: TimeWindow) -> None:
        """Add a time window to this context."""
        self.time_windows.append(window)

    def get_active_windows(self) -> list[TimeWindow]:
        """Get all currently active time windows."""
        return [w for w in self.time_windows if w.is_active()]

    def get_windows_by_metadata(self, key: str, value: Any) -> list[TimeWindow]:
        """Get windows matching metadata criteria."""
        return [w for w in self.time_windows if w.metadata.get(key) == value]

    def get_local_time(self) -> datetime:
        """Get local time considering timezone offset."""
        utc_time = datetime.fromtimestamp(self.current_time)
        return utc_time + timedelta(hours=self.timezone_offset)

    def update_time(self, new_time: float | None = None) -> None:
        """Update the current time."""
        self.current_time = new_time or time.time()


class TemporalProcessor(ABC):
    """Abstract base class for temporal processors."""

    @abstractmethod
    def process_temporal_event(self, event: dict[str, Any], context: TemporalContext) -> dict[str, Any]:
        """Process a temporal event."""
        pass

    @abstractmethod
    def can_process(self, event_type: str) -> bool:
        """Check if this processor can handle the event type."""
        pass


class TimeWindowManager:
    """Manages time windows and temporal scheduling."""

    def __init__(self):
        self.windows: dict[str, TimeWindow] = {}
        self.active_callbacks: dict[str, list[Callable]] = {}
        self.logger = logging.getLogger(f"{__name__}.TimeWindowManager")
        self._running = False
        self._thread: threading.Thread | None = None

    def create_window(self, window_id: str, start_time: float, duration: float, **metadata) -> TimeWindow:
        """Create a new time window."""
        if window_id in self.windows:
            raise ValueError(f"Window {window_id} already exists")

        window = TimeWindow(window_id=window_id, start_time=start_time, duration=duration, metadata=metadata)

        self.windows[window_id] = window
        self.logger.info(f"Created window {window_id}: duration {duration}s")
        return window

    def get_window(self, window_id: str) -> TimeWindow | None:
        """Get a window by ID."""
        return self.windows.get(window_id)

    def delete_window(self, window_id: str) -> bool:
        """Delete a time window."""
        if window_id in self.windows:
            del self.windows[window_id]
            if window_id in self.active_callbacks:
                del self.active_callbacks[window_id]
            self.logger.info(f"Deleted window {window_id}")
            return True
        return False

    def add_callback(self, window_id: str, callback: Callable[[TimeWindow], None]) -> None:
        """Add a callback for when a window becomes active."""
        if window_id not in self.active_callbacks:
            self.active_callbacks[window_id] = []
        self.active_callbacks[window_id].append(callback)

    def check_active_windows(self) -> list[TimeWindow]:
        """Check and return all currently active windows."""
        active_windows = []
        time.time()

        for window in self.windows.values():
            if window.is_active():
                active_windows.append(window)

                # Trigger callbacks if newly activated
                if window.window_id in self.active_callbacks:
                    for callback in self.active_callbacks[window.window_id]:
                        try:
                            callback(window)
                        except Exception as e:
                            self.logger.error(f"Callback failed for window {window.window_id}: {e}")

        return active_windows

    def start_monitoring(self, interval: float = 1.0) -> None:
        """Start monitoring time windows in a background thread."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, args=(interval,))
        self._thread.daemon = True
        self._thread.start()
        self.logger.info("Started time window monitoring")

    def stop_monitoring(self) -> None:
        """Stop monitoring time windows."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        self.logger.info("Stopped time window monitoring")

    def _monitor_loop(self, interval: float) -> None:
        """Background monitoring loop."""
        while self._running:
            try:
                self.check_active_windows()
                time.sleep(interval)
            except Exception as e:
                self.logger.error(f"Monitor loop error: {e}")


class TimeManager:
    """Manages temporal context and timing operations."""

    def __init__(self):
        self.contexts: dict[str, TemporalContext] = {}
        self.processors: list[TemporalProcessor] = []
        self.window_manager = TimeWindowManager()
        self.logger = logging.getLogger(f"{__name__}.TimeManager")

        # Start window monitoring
        self.window_manager.start_monitoring()

    def create_context(self, context_id: str, timezone_offset: float = 0.0, **metadata) -> TemporalContext:
        """Create a new temporal context."""
        if context_id in self.contexts:
            raise ValueError(f"Context {context_id} already exists")

        context = TemporalContext(context_id=context_id, timezone_offset=timezone_offset, metadata=metadata)

        self.contexts[context_id] = context
        self.logger.info(f"Created context {context_id}")
        return context

    def get_context(self, context_id: str) -> TemporalContext | None:
        """Get a context by ID."""
        return self.contexts.get(context_id)

    def register_processor(self, processor: TemporalProcessor) -> None:
        """Register a temporal processor."""
        self.processors.append(processor)
        self.logger.debug(f"Registered processor: {processor.__class__.__name__}")

    def process_event(self, context_id: str, event: dict[str, Any]) -> dict[str, Any]:
        """Process a temporal event in a specific context."""
        context = self.get_context(context_id)
        if not context:
            return {"error": f"Context {context_id} not found"}

        # Update context time
        if "timestamp" in event:
            context.current_time = event["timestamp"]
        else:
            event["timestamp"] = context.current_time

        # Process with appropriate processor
        event_type = event.get("event_type", "unknown")
        for processor in self.processors:
            if processor.can_process(event_type):
                try:
                    result = processor.process_temporal_event(event, context)
                    self.logger.debug(f"Processed {event_type} with {processor.__class__.__name__}")
                    return result
                except Exception as e:
                    self.logger.error(f"Processor failed for {event_type}: {e}")

        # Default processing
        return {"processed": True, "event_type": event_type}

    def create_recurring_window(
        self, context_id: str, window_id: str, start_time: float, interval: float, duration: float, **metadata
    ) -> TimeWindow:
        """Create a recurring time window."""
        context = self.get_context(context_id)
        if not context:
            raise ValueError(f"Context {context_id} not found")

        # Create initial window
        window = self.window_manager.create_window(
            window_id=window_id, start_time=start_time, duration=duration, **metadata
        )

        # Add to context
        context.add_window(window)

        # Set up recurrence callback
        def recreate_window(window: TimeWindow):
            # Calculate next start time
            next_start = window.start_time + interval
            next_end = next_start + duration

            # Update window
            window.start_time = next_start
            window.end_time = next_end
            window.duration = duration

            self.logger.debug(f"Recreated window {window_id} for next cycle")

        self.window_manager.add_callback(window_id, recreate_window)
        return window

    def get_context_statistics(self, context_id: str) -> dict[str, Any]:
        """Get statistics for a temporal context."""
        context = self.get_context(context_id)
        if not context:
            return {}

        active_windows = context.get_active_windows()

        return {
            "context_id": context.context_id,
            "current_time": context.current_time,
            "local_time": context.get_local_time().isoformat(),
            "timezone_offset": context.timezone_offset,
            "total_windows": len(context.time_windows),
            "active_windows": len(active_windows),
            "temporal_patterns": list(context.temporal_patterns.keys()),
        }

    def cleanup(self) -> None:
        """Clean up resources."""
        self.window_manager.stop_monitoring()


# Basic processor implementations
class DeadlineProcessor(TemporalProcessor):
    """Processes deadline events."""

    def can_process(self, event_type: str) -> bool:
        return event_type == "deadline"

    def process_temporal_event(self, event: dict[str, Any], context: TemporalContext) -> dict[str, Any]:
        """Process deadline event."""
        deadline_time = event.get("deadline_time", 0)
        current_time = context.current_time

        time_remaining = deadline_time - current_time
        is_overdue = time_remaining < 0

        return {
            "deadline_time": deadline_time,
            "time_remaining": time_remaining,
            "is_overdue": is_overdue,
            "urgency": "high" if time_remaining < 3600 else "medium" if time_remaining < 86400 else "low",
        }


class IntervalProcessor(TemporalProcessor):
    """Processes interval-based events."""

    def can_process(self, event_type: str) -> bool:
        return event_type == "interval"

    def process_temporal_event(self, event: dict[str, Any], context: TemporalContext) -> dict[str, Any]:
        """Process interval event."""
        interval = event.get("interval", 0)
        last_occurrence = event.get("last_occurrence", 0)

        next_occurrence = last_occurrence + interval
        is_due = context.current_time >= next_occurrence

        return {
            "interval": interval,
            "last_occurrence": last_occurrence,
            "next_occurrence": next_occurrence,
            "is_due": is_due,
        }


# Future extension points
class AdvancedTimeManager(TimeManager):
    """Advanced time manager with additional capabilities."""

    def __init__(self):
        super().__init__()
        self.temporal_patterns: dict[str, dict[str, Any]] = {}
        self.prediction_enabled = False

    def enable_prediction(self) -> None:
        """Enable temporal pattern prediction."""
        self.prediction_enabled = True

    def detect_temporal_pattern(self, context_id: str, events: list[dict[str, Any]]) -> dict[str, Any]:
        """Detect patterns in temporal events.

        Identifies temporal patterns including:
        - Fixed intervals (periodic patterns)
        - Event sequences
        - Time-of-day clustering
        """
        if len(events) < 3:
            return {"pattern_detected": False, "reason": "insufficient_events"}

        # Sort events by timestamp
        sorted_events = sorted(events, key=lambda e: e.get("timestamp", 0))
        timestamps = [e.get("timestamp", 0) for e in sorted_events]

        # Calculate intervals between consecutive events
        intervals = [timestamps[i] - timestamps[i - 1] for i in range(1, len(timestamps))]

        if not intervals:
            return {"pattern_detected": False, "reason": "no_intervals"}

        # Detect fixed interval pattern (periodicity)
        avg_interval = sum(intervals) / len(intervals)
        variance = sum((i - avg_interval) ** 2 for i in intervals) / len(intervals)
        std_dev = variance**0.5

        # Check if intervals are consistent (low coefficient of variation)
        if avg_interval > 0 and std_dev / avg_interval < 0.2:
            self.temporal_patterns[context_id] = {
                "type": "periodic",
                "interval": avg_interval,
                "std_dev": std_dev,
                "events": len(events),
            }
            return {
                "pattern_detected": True,
                "pattern_type": "periodic",
                "interval_seconds": round(avg_interval, 2),
                "variance": round(variance, 2),
                "confidence": round(1 - (std_dev / avg_interval), 2),
            }

        # Check for time-of-day clustering
        hours = [datetime.fromtimestamp(ts).hour for ts in timestamps]
        hour_counts: dict[int, int] = {}
        for h in hours:
            hour_counts[h] = hour_counts.get(h, 0) + 1

        max_hour_count = max(hour_counts.values())
        if max_hour_count >= len(events) * 0.5:
            peak_hour = max(hour_counts.items(), key=lambda x: x[1])[0]
            self.temporal_patterns[context_id] = {
                "type": "time_of_day",
                "peak_hour": peak_hour,
                "event_count": max_hour_count,
            }
            return {
                "pattern_detected": True,
                "pattern_type": "time_of_day",
                "peak_hour": peak_hour,
                "peak_hour_frequency": max_hour_count,
                "confidence": round(max_hour_count / len(events), 2),
            }

        return {"pattern_detected": False, "reason": "no_significant_pattern"}

    def predict_next_event(self, context_id: str) -> dict[str, Any] | None:
        """Predict the next likely event based on patterns.

        Uses detected temporal patterns to forecast next event time.
        """
        if not self.prediction_enabled:
            return None

        pattern = self.temporal_patterns.get(context_id)
        if not pattern:
            return None

        current_time = time.time()

        if pattern["type"] == "periodic":
            interval = pattern["interval"]
            std_dev = pattern.get("std_dev", interval * 0.1)
            next_event_time = current_time + interval
            confidence = round(1 - (std_dev / interval), 2) if interval > 0 else 0.5

            return {
                "predicted_time": next_event_time,
                "predicted_datetime": datetime.fromtimestamp(next_event_time).isoformat(),
                "pattern_type": "periodic",
                "interval": round(interval, 2),
                "confidence": min(1.0, max(0.0, confidence)),
                "time_until": round(interval, 2),
            }

        elif pattern["type"] == "time_of_day":
            peak_hour = pattern["peak_hour"]
            now = datetime.now()
            next_occurrence = now.replace(hour=peak_hour, minute=0, second=0, microsecond=0)

            if next_occurrence <= now:
                next_occurrence = next_occurrence + timedelta(days=1)

            return {
                "predicted_time": next_occurrence.timestamp(),
                "predicted_datetime": next_occurrence.isoformat(),
                "pattern_type": "time_of_day",
                "peak_hour": peak_hour,
                "confidence": round(pattern.get("event_count", 1) / (pattern.get("event_count", 1) + 2), 2),
                "time_until": round((next_occurrence.timestamp() - current_time), 2),
            }

        return None

    def analyze_temporal_distribution(self, context_id: str) -> dict[str, Any]:
        """Analyze the distribution of events over time.

        Performs statistical analysis on temporal events including:
        - Hourly distribution
        - Daily distribution
        - Inter-event timing statistics
        - Event frequency trends
        """
        context = self.get_context(context_id)
        if not context:
            return {}

        # Get events from context metadata or patterns
        events = context.temporal_patterns.get("events", [])
        if not events:
            return {"analysis": "temporal_distribution", "events_analyzed": 0}

        # Sort events by timestamp
        sorted_events = sorted(events, key=lambda e: e.get("timestamp", 0))
        timestamps = [e.get("timestamp", 0) for e in sorted_events]

        if len(timestamps) < 2:
            return {
                "analysis": "temporal_distribution",
                "events_analyzed": len(timestamps),
                "note": "insufficient_data",
            }

        # Calculate intervals
        intervals = [timestamps[i] - timestamps[i - 1] for i in range(1, len(timestamps))]

        # Basic statistics
        total_duration = timestamps[-1] - timestamps[0]
        avg_interval = sum(intervals) / len(intervals)
        min_interval = min(intervals)
        max_interval = max(intervals)

        # Variance and standard deviation
        variance = sum((i - avg_interval) ** 2 for i in intervals) / len(intervals)
        std_dev = variance**0.5

        # Hourly distribution
        hours: dict[int, int] = {}
        for ts in timestamps:
            hour = datetime.fromtimestamp(ts).hour
            hours[hour] = hours.get(hour, 0) + 1

        # Daily distribution (day of week: 0=Monday)
        days: dict[int, int] = {}
        for ts in timestamps:
            day = datetime.fromtimestamp(ts).weekday()
            days[day] = days.get(day, 0) + 1

        # Peak hour calculation
        peak_hour = max(hours.items(), key=lambda x: x[1])[0] if hours else None
        peak_hour_count = hours.get(peak_hour, 0) if peak_hour else 0

        # Event frequency (events per hour)
        frequency = len(timestamps) / (total_duration / 3600) if total_duration > 0 else 0

        return {
            "analysis": "temporal_distribution",
            "events_analyzed": len(timestamps),
            "time_range": {
                "start": timestamps[0],
                "end": timestamps[-1],
                "duration_hours": round(total_duration / 3600, 2),
            },
            "interval_statistics": {
                "average_seconds": round(avg_interval, 2),
                "min_seconds": round(min_interval, 2),
                "max_seconds": round(max_interval, 2),
                "std_dev_seconds": round(std_dev, 2),
                "variance": round(variance, 2),
            },
            "hourly_distribution": dict(sorted(hours.items())),
            "daily_distribution": {k: v for k, v in sorted(days.items())},
            "peak_hour": {"hour": peak_hour, "count": peak_hour_count},
            "event_frequency_per_hour": round(frequency, 2),
            "burstiness": round(std_dev / avg_interval if avg_interval > 0 else 0, 2),
        }
