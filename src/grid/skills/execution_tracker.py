"""Tracks all skill executions with detailed metrics and persistent storage.

Features:
- In-memory deque for recent history
- Batch persistence to SQLite (configurable)
- Emergency flush on errors
- Graceful degradation when inventory unavailable
"""

from __future__ import annotations

import atexit
import logging
import os
import threading
import time
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .intelligence_inventory import IntelligenceInventory

logger = logging.getLogger(__name__)


class ExecutionStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    PARTIAL = "partial"


@dataclass
class SkillExecutionRecord:
    skill_id: str
    timestamp: float
    status: ExecutionStatus
    input_args: dict[str, Any]
    output: Any
    error: str | None
    execution_time_ms: float
    confidence_score: float | None
    fallback_used: bool


class SkillExecutionTracker:
    """Tracks all skill executions with batch persistence to SQLite.

    Configuration via environment variables:
    - GRID_SKILLS_BATCH_SIZE: Records per batch (default: 10)
    - GRID_SKILLS_FLUSH_INTERVAL: Seconds between flushes (default: 30)
    - GRID_SKILLS_PERSIST_MODE: batch|immediate|off (default: batch)
    """

    _instance: SkillExecutionTracker | None = None
    _lock = threading.Lock()

    # Configuration defaults
    BATCH_SIZE = int(os.getenv("GRID_SKILLS_BATCH_SIZE", "10"))
    FLUSH_INTERVAL = int(os.getenv("GRID_SKILLS_FLUSH_INTERVAL", "30"))
    PERSIST_MODE = os.getenv("GRID_SKILLS_PERSIST_MODE", "batch")

    def __init__(self, max_history: int = 1000):
        self._history: deque[SkillExecutionRecord] = deque(maxlen=max_history)
        self._max_history = max_history
        self._logger = logging.getLogger(__name__)

        # Batch persistence state
        self._batch_buffer: list[SkillExecutionRecord] = []
        self._last_flush_time = time.time()
        self._flush_lock = threading.Lock()

        # FIXED: Dead-letter queue for failed persistence
        self._dead_letter: list[SkillExecutionRecord] = []
        self._dead_letter_lock = threading.Lock()
        self._max_dead_letter_size = 10000

        # Lazy inventory connection
        self._inventory: IntelligenceInventory | None = None
        self._inventory_available = True  # Assume available until proven otherwise

        # Register shutdown handler
        atexit.register(self._shutdown_flush)

        # Start background flush timer if batch mode
        if self.PERSIST_MODE == "batch":
            self._start_flush_timer()

    @classmethod
    def get_instance(cls) -> SkillExecutionTracker:
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def _get_inventory(self) -> IntelligenceInventory | None:
        """Lazy load inventory connection."""
        if not self._inventory_available:
            return None

        if self._inventory is None:
            try:
                from .intelligence_inventory import IntelligenceInventory

                self._inventory = IntelligenceInventory.get_instance()
                self._logger.debug("Connected to IntelligenceInventory")
            except Exception as e:
                self._logger.warning(f"IntelligenceInventory unavailable: {e}")
                self._inventory_available = False
                return None

        return self._inventory

    def _start_flush_timer(self) -> None:
        """Start background timer for periodic flushes."""

        def flush_loop() -> None:
            while True:
                time.sleep(self.FLUSH_INTERVAL)
                try:
                    self._time_based_flush()
                except Exception as e:
                    self._logger.error(f"Flush timer error: {e}")

        timer = threading.Thread(target=flush_loop, daemon=True)
        timer.start()
        self._logger.debug(f"Flush timer started ({self.FLUSH_INTERVAL}s interval)")

    def track_execution(
        self,
        skill_id: str,
        input_args: dict[str, Any],
        output: Any,
        error: str | None = None,
        status: ExecutionStatus = ExecutionStatus.SUCCESS,
        confidence_score: float | None = None,
        fallback_used: bool = False,
        execution_time_ms: float | None = None,
    ) -> SkillExecutionRecord:
        """Track a skill execution with batch persistence."""
        timestamp = time.time()

        record = SkillExecutionRecord(
            skill_id=skill_id,
            timestamp=timestamp,
            status=status,
            input_args=input_args,
            output=output,
            error=error,
            execution_time_ms=execution_time_ms or 0,
            confidence_score=confidence_score,
            fallback_used=fallback_used,
        )

        # Add to in-memory history
        self._history.append(record)

        # Handle persistence based on mode
        if self.PERSIST_MODE == "off":
            pass  # No persistence
        elif self.PERSIST_MODE == "immediate":
            self._immediate_persist(record)
        else:  # batch mode
            self._add_to_batch(record)

            # Emergency flush on errors
            if error:
                self._emergency_flush()

        self._logger.debug(f"Tracked {skill_id}: {status.value} in {record.execution_time_ms}ms")
        return record

    def _add_to_batch(self, record: SkillExecutionRecord) -> None:
        """Add record to batch buffer and maybe flush."""
        with self._flush_lock:
            self._batch_buffer.append(record)

            # Size-based flush
            if len(self._batch_buffer) >= self.BATCH_SIZE:
                self._flush_batch()

    def _time_based_flush(self) -> None:
        """Flush if interval has passed."""
        with self._flush_lock:
            if self._batch_buffer and (time.time() - self._last_flush_time) >= self.FLUSH_INTERVAL:
                self._flush_batch()

    def _emergency_flush(self) -> None:
        """Immediately persist on error events."""
        with self._flush_lock:
            if self._batch_buffer:
                self._logger.debug("Emergency flush triggered")
                self._flush_batch()

    def _flush_batch(self) -> None:
        """
        Flush batch buffer to inventory with dead-letter queue fallback.

        FIXED: Records that fail to persist are moved to dead-letter queue
        for later retry instead of being silently dropped.
        """
        if not self._batch_buffer:
            return

        inventory = self._get_inventory()

        # If inventory unavailable, move all to dead-letter
        if not inventory:
            with self._dead_letter_lock:
                self._dead_letter.extend(self._batch_buffer)
                # Trim dead-letter if too large
                if len(self._dead_letter) > self._max_dead_letter_size:
                    self._dead_letter = self._dead_letter[-self._max_dead_letter_size :]
            self._logger.warning(f"Inventory unavailable, moved {len(self._batch_buffer)} records to dead-letter")
            self._batch_buffer.clear()
            return

        # Attempt to flush with retry
        failed_records = []
        max_retries = 3

        for attempt in range(max_retries):
            try:
                for record in self._batch_buffer:
                    inventory.store_execution(record)

                inventory.flush_all()
                count = len(self._batch_buffer)
                self._batch_buffer.clear()
                self._last_flush_time = time.time()
                self._logger.debug(f"Flushed {count} execution records")
                return  # Success - exit early

            except Exception as e:
                self._logger.error(f"Batch flush failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2**attempt)  # Exponential backoff
                else:
                    # Final failure - move to dead-letter
                    failed_records = self._batch_buffer.copy()

        # Move failed records to dead-letter queue
        if failed_records:
            with self._dead_letter_lock:
                self._dead_letter.extend(failed_records)
                # Trim dead-letter if too large
                if len(self._dead_letter) > self._max_dead_letter_size:
                    self._dead_letter = self._dead_letter[-self._max_dead_letter_size :]
            self._logger.error(
                f"Moved {len(failed_records)} failed records to dead-letter after {max_retries} attempts"
            )
            self._batch_buffer.clear()

    def _immediate_persist(self, record: SkillExecutionRecord) -> None:
        """Persist single record immediately."""
        inventory = self._get_inventory()
        if inventory:
            try:
                inventory.store_execution(record)
                inventory.flush_all()
            except Exception as e:
                self._logger.error(f"Immediate persist failed: {e}")

    def _shutdown_flush(self) -> None:
        """Best-effort flush on shutdown."""
        if not self._batch_buffer:
            return
        try:
            with self._flush_lock:
                # Use print instead of logger if handles might be closed
                print(f"SkillExecutionTracker: Shutdown flush of {len(self._batch_buffer)} records...")
                self._flush_batch()
        except Exception:
            # Silent fail on shutdown to avoid I/O errors on closed loggers
            pass

    def get_execution_history(self, skill_id: str | None = None, limit: int = 100) -> list[SkillExecutionRecord]:
        """Get execution history from memory."""
        if skill_id:
            return [r for r in self._history if r.skill_id == skill_id][-limit:]
        return list(self._history)[-limit:]

    def get_skill_performance(self, skill_id: str) -> dict[str, Any]:
        """Get performance metrics for a skill from memory."""
        executions = [r for r in self._history if r.skill_id == skill_id]

        if not executions:
            return {"error": "No executions found"}

        successes = [r for r in executions if r.status == ExecutionStatus.SUCCESS]
        success_rate = len(successes) / len(executions)
        avg_latency = sum(r.execution_time_ms for r in executions) / len(executions)
        error_rate = sum(1 for r in executions if r.status != ExecutionStatus.SUCCESS) / len(executions)

        return {
            "skill_id": skill_id,
            "total_executions": len(executions),
            "success_rate": success_rate,
            "error_rate": error_rate,
            "avg_latency_ms": avg_latency,
            "p50_latency_ms": self._calculate_percentile(executions, 0.5),
            "p95_latency_ms": self._calculate_percentile(executions, 0.95),
            "p99_latency_ms": self._calculate_percentile(executions, 0.99),
            "fallback_rate": sum(1 for r in executions if r.fallback_used) / len(executions),
            "avg_confidence": (
                sum(r.confidence_score or 0 for r in executions) / len(executions)
                if any(r.confidence_score is not None for r in executions)
                else None
            ),
        }

    def _calculate_percentile(self, executions: list[SkillExecutionRecord], percentile: float) -> float:
        """Calculate percentile latency."""
        latencies = sorted([r.execution_time_ms for r in executions])
        if not latencies:
            return 0
        import math

        index = min(len(latencies) - 1, math.floor(percentile * len(latencies)))
        return latencies[index]

    def get_error_patterns(self, skill_id: str) -> dict[str, int]:
        """Get error patterns for a specific skill."""
        executions = [r for r in self._history if r.skill_id == skill_id and r.error]
        error_counts: dict[str, int] = {}

        for record in executions:
            error = record.error or "unknown"
            error_counts[error] = error_counts.get(error, 0) + 1

        return dict(sorted(error_counts.items(), key=lambda x: x[1], reverse=True))

    def export_history(self, format: str = "json") -> str:
        """Export execution history."""
        if format == "json":
            import json

            def serialize_record(r: SkillExecutionRecord) -> dict[str, Any]:
                d = r.__dict__.copy()
                d["status"] = d["status"].value
                return d

            return json.dumps([serialize_record(r) for r in self._history], indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def get_pending_count(self) -> int:
        """Get count of pending records in batch buffer."""
        return len(self._batch_buffer)

    def force_flush(self) -> None:
        """Force immediate flush of batch buffer."""
        with self._flush_lock:
            self._flush_batch()
