"""Priority queue and heuristic routing for GRID kernel."""

from __future__ import annotations

import heapq
from typing import Any


class PriorityQueue:
    """Priority queue with max-heap behavior (higher priority = first out)."""

    def __init__(self) -> None:
        self._items: list[tuple[int, int, Any]] = []
        self._counter = 0

    def put(self, item: Any, priority: int = 0) -> None:
        """Add item with priority (higher = more important)."""
        heapq.heappush(self._items, (-priority, self._counter, item))
        self._counter += 1

    def get(self) -> Any | None:
        """Get highest priority item, or None if empty."""
        if self._items:
            _, _, item = heapq.heappop(self._items)
            return item
        return None

    def empty(self) -> bool:
        """Check if queue is empty."""
        return len(self._items) == 0


class HeuristicRouter:
    """Route items based on priority heuristics, optionally publishing to a pipeline."""

    def __init__(self, pipeline: Any | None = None) -> None:
        self.queue = PriorityQueue()
        self.pipeline = pipeline

    def route(self, item: Any, priority: int = 0) -> None:
        """Route item into the priority queue."""
        self.queue.put(item, priority)

    def get_next(self) -> Any | None:
        """Get the next highest-priority item."""
        return self.queue.get()

    def process_all(self) -> None:
        """Process all queued items in priority order, publishing to pipeline if set."""
        while not self.queue.empty():
            item = self.queue.get()
            if self.pipeline:
                self.pipeline.publish_sync(item)
