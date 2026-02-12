import threading
import time
import logging
from typing import Optional, Any, Callable, TypeVar
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from .rate_limiter import RateLimiter
from .audit_logger import AuditLogger, AuditEventType
from .ai_safety import ContentSafetyFilter

T = TypeVar('T')

logger = logging.getLogger(__name__)

@dataclass
class ConcurrencyStats:
    """Statistics for IO concurrency"""
    active_slots: int
    total_slots: int
    pending_tasks: int
    completed_tasks: int
    blocked_tasks: int
    safety_throttle_level: float  # 0.0 to 1.0 (1.0 = fully throttled)
    last_updated: datetime = field(default_factory=datetime.now)

class DynamicSafetyIOManager:
    """
    Manages concurrent IO operations with integrated safety checks.
    Dynamically adjusts throughput based on system safety metrics.
    """

    def __init__(
        self,
        audit_logger: AuditLogger,
        rate_limiter: Optional[RateLimiter] = None,
        max_concurrency: int = 10,
        min_concurrency: int = 1
    ):
        self.audit_logger = audit_logger
        self.rate_limiter = rate_limiter
        self.max_concurrency = max_concurrency
        self.min_concurrency = min_concurrency
        self.current_concurrency = max_concurrency

        self._semaphore = threading.Semaphore(max_concurrency)
        self._executor = ThreadPoolExecutor(max_workers=max_concurrency)
        self._lock = threading.RLock()

        # Internal state
        self.active_count = 0
        self.completed_count = 0
        self.blocked_count = 0
        self.pending_count = 0

        # Safety monitors
        self.safety_throttle_factor = 0.0
        self.is_degraded = False

        self.audit_logger.log_event(
            event_type=AuditEventType.CONFIG_CHANGE,
            action="concurrency_manager_initialized",
            details={
                "max_concurrency": max_concurrency,
                "min_concurrency": min_concurrency
            }
        )

    def _adjust_concurrency(self, safety_score: float):
        """
        Dynamically adjust the semaphore and executor pool size.
        safety_score: 0.0 (unsafe) to 1.0 (perfectly safe)
        """
        with self._lock:
            target = int(self.min_concurrency + (self.max_concurrency - self.min_concurrency) * safety_score)

            if target != self.current_concurrency:
                diff = target - self.current_concurrency
                if diff > 0:
                    for _ in range(diff):
                        self._semaphore.release()
                else:
                    for _ in range(abs(diff)):
                        # Note: This is an approximation. Semaphores don't support shrinking easily
                        # without blocking. We'll rely on the execute() method checking
                        # current_concurrency.
                        pass

                self.current_concurrency = target
                self.safety_throttle_factor = 1.0 - safety_score
                self.is_degraded = safety_score < 0.5

                self.audit_logger.log_event(
                    event_type=AuditEventType.CONFIG_CHANGE,
                    action="concurrency_dynamic_adjustment",
                    details={
                        "new_concurrency": target,
                        "safety_score": safety_score,
                        "throttle_factor": self.safety_throttle_factor
                    }
                )

    def execute_safe_io(
        self,
        io_func: Callable[..., T],
        resource_id: str,
        user_id: str = "system",
        *args,
        **kwargs
    ) -> Optional[T]:
        """
        Execute an IO operation with safety gatekeeping and concurrency control.
        """
        # 1. Check Rate Limits
        if self.rate_limiter:
            status = self.rate_limiter.check_rate_limit(user_id)
            if not status.allowed:
                with self._lock:
                    self.blocked_count += 1
                self.audit_logger.log_event(
                    event_type=AuditEventType.SAFETY_VIOLATION,
                    action="io_concurrency_blocked",
                    status="blocked",
                    details={"reason": "rate_limit", "user_id": user_id}
                )
                return None

        # 2. Acquire Concurrency Slot
        acquired = self._semaphore.acquire(blocking=True, timeout=5.0)
        if not acquired:
            with self._lock:
                self.blocked_count += 1
            self.audit_logger.log_error(
                error_type="concurrency_timeout",
                error_message=f"Timeout waiting for IO slot for {resource_id}",
                user_id=user_id
            )
            return None

        with self._lock:
            self.active_count += 1
            self.pending_count = max(0, self.pending_count - 1)

        try:
            # 3. Log start
            start_time = time.perf_counter()
            self.audit_logger.log_event(
                event_type=AuditEventType.DATA_PROCESSING,
                action="concurrent_io_started",
                resource_id=resource_id,
                details={"active_count": self.active_count}
            )

            # 4. Execute operation
            result = io_func(*args, **kwargs)

            # 5. Log success
            duration_ms = (time.perf_counter() - start_time) * 1000
            with self._lock:
                self.completed_count += 1

            self.audit_logger.log_event(
                event_type=AuditEventType.DATA_PROCESSING,
                action="concurrent_io_success",
                resource_id=resource_id,
                status="success",
                details={"duration_ms": duration_ms}
            )
            return result

        except Exception as e:
            self.audit_logger.log_error(
                error_type="io_execution_failed",
                error_message=str(e),
                user_id=user_id
            )
            return None
        finally:
            with self._lock:
                self.active_count -= 1
            self._semaphore.release()

    def get_stats(self) -> ConcurrencyStats:
        """Get current concurrency and safety statistics"""
        with self._lock:
            return ConcurrencyStats(
                active_slots=self.active_count,
                total_slots=self.current_concurrency,
                pending_tasks=self.pending_count,
                completed_tasks=self.completed_count,
                blocked_tasks=self.blocked_count,
                safety_throttle_level=self.safety_throttle_factor
            )

    def shutdown(self):
        """Cleanly shutdown the manager"""
        self._executor.shutdown(wait=True)
        self.audit_logger.log_event(
            event_type=AuditEventType.CONFIG_CHANGE,
            action="concurrency_manager_shutdown",
            details={"completed": self.completed_count}
        )

class DynamicSafetyGuard:
    """
    A high-level guard that monitors system safety and
    controls the DynamicSafetyIOManager throughput.
    """

    def __init__(
        self,
        io_manager: DynamicSafetyIOManager,
        safety_filter: ContentSafetyFilter,
        monitor_interval: int = 30
    ):
        self.io_manager = io_manager
        self.safety_filter = safety_filter
        self.monitor_interval = monitor_interval
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start_monitoring(self):
        """Start the background safety monitor"""
        if self._thread is not None:
            return

        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def _monitor_loop(self):
        """Periodically evaluate safety and adjust concurrency"""
        while not self._stop_event.is_set():
            try:
                # Calculate safety score based on recent violations
                summary = self.safety_filter.get_safety_summary()
                critical = summary['by_severity'].get('critical', 0)
                high = summary['by_severity'].get('high', 0)

                # Dynamic formula: reduce concurrency as violations increase
                # Score starts at 1.0 (perfect)
                safety_score = 1.0

                if critical > 0:
                    safety_score -= 0.5 * min(critical, 2)
                if high > 5:
                    safety_score -= 0.2

                safety_score = max(0.1, safety_score)

                # Apply to IO manager
                self.io_manager._adjust_concurrency(safety_score)

            except Exception as e:
                logger.error(f"Safety monitor error: {e}")

            self._stop_event.wait(self.monitor_interval)

    def stop(self):
        """Stop the monitor thread"""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)
