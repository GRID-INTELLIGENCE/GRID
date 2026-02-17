"""Progress tracking utilities for indexing."""

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class IndexProgress:
    """Tracks indexing progress and estimates ETA."""

    start_time: float = field(default_factory=time.time)
    last_report_time: float = field(default_factory=time.time)
    completed: int = 0
    total: int = 0
    report_interval: int = 5  # Report every N items

    # Rolling window for rate estimation - deque for O(1) operations
    window_size: int = 10
    recent_times: deque[float] = field(default_factory=lambda: deque(maxlen=10))

    def __post_init__(self) -> None:
        """Re-initialize deque with correct maxlen after dataclass init."""
        if not isinstance(self.recent_times, deque) or self.recent_times.maxlen != self.window_size:
            self.recent_times = deque(self.recent_times, maxlen=self.window_size)

    def start(self, total: int) -> None:
        """Initialize progress with total items."""
        self.total = total
        self.completed = 0
        self.start_time = time.time()
        self.last_report_time = self.start_time
        self.recent_times.clear()

    def tick(self, increment: int = 1) -> None:
        """Mark items as completed."""
        now = time.time()
        self.recent_times.append(now)  # Auto-pops oldest when at maxlen
        self.completed += increment

    def should_report(self) -> bool:
        """Check if it's time to emit a progress update."""
        return self.completed % self.report_interval == 0 or self.completed == self.total

    def rate(self) -> float:
        """Calculate current rate (items/sec) using a rolling window."""
        if len(self.recent_times) < 2:
            return 0.0
        elapsed = self.recent_times[-1] - self.recent_times[0]
        if elapsed <= 0:
            return 0.0
        # Number of items in window = len(recent_times) - 1 (since we store timestamps)
        items = len(self.recent_times) - 1
        return items / elapsed

    def eta_seconds(self) -> float | None:
        """Estimate remaining time in seconds."""
        if self.total <= 0 or self.completed <= 0:
            return None
        remaining = self.total - self.completed
        rate = self.rate()
        if rate <= 0:
            return None
        return remaining / rate

    def percent(self) -> float:
        """Return completion percentage (0-100)."""
        if self.total <= 0:
            return 0.0
        return min(100.0, (self.completed / self.total) * 100.0)

    def summary(self) -> dict[str, Any]:
        """Return a structured summary."""
        eta = self.eta_seconds()
        return {
            "completed": self.completed,
            "total": self.total,
            "percent": round(self.percent(), 2),
            "rate_items_per_sec": round(self.rate(), 2),
            "eta_seconds": round(eta) if eta is not None else None,
            "elapsed_seconds": round(time.time() - self.start_time, 2),
        }

    def format(self) -> str:
        """Human-readable progress line."""
        pct = self.percent()
        rate = self.rate()
        eta = self.eta_seconds()
        parts = [
            f"{self.completed}/{self.total}",
            f"{pct:.1f}%",
            f"{rate:.1f}/s",
        ]
        if eta is not None:
            if eta < 60:
                parts.append(f"ETA {eta:.0f}s")
            else:
                parts.append(f"ETA {eta / 60:.1f}m")
        return " | ".join(parts)
