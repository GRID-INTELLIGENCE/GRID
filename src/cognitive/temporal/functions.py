import time
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any


def with_temporal_context(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator that adds temporal context to function execution.
    Measures execution time and applies time-based adaptations.
    """

    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()

        # Extract temporal context if available
        temporal_ctx = kwargs.get("temporal_context", {})
        time_sensitivity = temporal_ctx.get("time_sensitivity", 0.5)

        # Execute function
        result = func(*args, **kwargs)

        # Calculate execution duration
        end_time = time.perf_counter()
        duration = end_time - start_time

        # Apply time compression/expansion based on sensitivity
        if time_sensitivity > 0.7:
            # Compress time-sensitive results
            if isinstance(result, dict):
                result["time_compression"] = True
                result["original_duration"] = duration
                result["compressed_duration"] = duration * 0.7

        elif time_sensitivity < 0.3:
            # Expand time-insensitive results
            if isinstance(result, dict):
                result["time_expansion"] = True
                result["original_duration"] = duration
                result["expanded_duration"] = duration * 1.3

        return result

    return wrapper


def detect_temporal_pattern(events: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Detect temporal patterns in event sequences.
    Identifies cycles, intervals, and anomalies.
    """
    if len(events) < 3:
        return {"pattern": "insufficient_data"}

    # Calculate intervals
    timestamps = [e["timestamp"] for e in events if "timestamp" in e]
    intervals = [(timestamps[i] - timestamps[i - 1]).total_seconds() for i in range(1, len(timestamps))]

    # Calculate statistics
    avg_interval = sum(intervals) / len(intervals)
    max_interval = max(intervals)
    min_interval = min(intervals)

    # Detect patterns
    if max_interval - min_interval < avg_interval * 0.1:
        return {"pattern": "regular", "interval": avg_interval}
    elif any(i > avg_interval * 3 for i in intervals):
        return {"pattern": "bursty", "max_interval": max_interval}
    else:
        return {"pattern": "irregular"}


def apply_time_shift(data: Any, shift: timedelta) -> Any:
    """
    Apply time shift to temporal data structures.
    Handles datetime objects, time series, and temporal sequences.
    """
    if isinstance(data, datetime):
        return data + shift
    elif isinstance(data, list):
        return [apply_time_shift(item, shift) for item in data]
    elif isinstance(data, dict):
        return {k: apply_time_shift(v, shift) for k, v in data.items()}
    else:
        return data
