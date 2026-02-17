"""
XAI Threading Framework for GRID
Provides thread pooling, task management, and concurrent XAI operations.
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TaskInfo:
    """Information about a queued task."""

    task_id: str
    task_type: str
    priority: int
    created_at: datetime
    coroutine: Callable | None = None
    result: Any = None
    error: Exception | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass
class WorkerStats:
    """Statistics for a worker thread."""

    worker_id: int
    tasks_completed: int = 0
    total_processing_time: float = 0.0
    average_processing_time: float = 0.0
    active_task: str | None = None
    last_activity: datetime = None

    def update_stats(self, processing_time: float):
        """Update worker statistics."""
        self.tasks_completed += 1
        self.total_processing_time += processing_time
        self.average_processing_time = self.total_processing_time / self.tasks_completed
        self.last_activity = datetime.now()


class WorkerThread:
    """Managed worker thread for XAI operations."""

    def __init__(self, worker_id: int):
        self.worker_id = worker_id
        self.stats = WorkerStats(worker_id=worker_id)
        self.current_task: TaskInfo | None = None
        self.is_running = True
        self._loop = None

    async def run(self):
        """Main worker loop."""
        self._loop = asyncio.get_running_loop()

        while self.is_running:
            try:
                # Wait for task assignment
                task = await self._wait_for_task()
                if not task:
                    continue

                self.current_task = task
                self.stats.active_task = task.task_id
                self.stats.last_activity = datetime.now()

                start_time = datetime.now()
                task.started_at = start_time

                # Execute task
                try:
                    if task.coroutine:
                        result = await task.coroutine()
                    else:
                        result = await self._execute_default_task(task)

                    task.result = result
                    processing_time = (datetime.now() - start_time).total_seconds()
                    self.stats.update_stats(processing_time)

                except Exception as e:
                    task.error = e
                    logger.error(f"Worker {self.worker_id} task {task.task_id} failed: {e}")

                task.completed_at = datetime.now()
                self.current_task = None
                self.stats.active_task = None

                # Signal task completion
                await self._signal_task_completion(task)

            except asyncio.CancelledError:
                logger.info(f"Worker {self.worker_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {self.worker_id} error: {e}")
                break

    async def _wait_for_task(self) -> TaskInfo | None:
        """Wait for task assignment (to be implemented by pool)."""
        # This is a placeholder - would be connected to task queue
        await asyncio.sleep(0.1)
        return None

    async def _execute_default_task(self, task: TaskInfo) -> Any:
        """Default task execution logic."""
        # Simulate XAI operation
        await asyncio.sleep(0.1)
        return f"Task {task.task_id} result"

    async def _signal_task_completion(self, task: TaskInfo):
        """Signal task completion (to be implemented by pool)."""
        # Placeholder for task completion signaling
        pass


class XAIThreadPool:
    """
    Thread pool for managing concurrent XAI operations.
    """

    def __init__(self, max_workers: int = 10, max_queue_size: int = 1000):
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        self.task_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self.workers: list[WorkerThread] = []
        self.task_subscribers: list[Callable] = []
        self.worker_count = 0
        self.is_running = False

    async def submit_task(
        self, task_type: str, task_coroutine: Callable | None = None, priority: int = 0, **task_kwargs
    ) -> str:
        """
        Submit a task for execution.

        Returns:
            Task ID
        """
        task_id = f"task_{len(self.task_queue._queue)}"
        task = TaskInfo(
            task_id=task_id, task_type=task_type, priority=priority, created_at=datetime.now(), coroutine=task_coroutine
        )

        # Add task-specific kwargs
        for key, value in task_kwargs.items():
            setattr(task, key, value)

        try:
            await self.task_queue.put(task)
        except asyncio.QueueFull as e:
            logger.warning("Task queue is full, dropping task")
            raise RuntimeError("Task queue is full") from e

        logger.info(f"Submitted task {task_id} of type {task_type}")
        return task_id

    def subscribe_to_tasks(self, callback: Callable[[str, TaskInfo], None]):
        """Subscribe to task lifecycle events."""
        self.task_subscribers.append(callback)

    async def start(self):
        """Start the thread pool."""
        if self.is_running:
            return

        self.is_running = True
        logger.info(f"Starting XAI thread pool with {self.max_workers} workers")

        # Create and start workers
        self.workers = [WorkerThread(i) for i in range(self.max_workers)]

        # Start worker tasks
        worker_tasks = [asyncio.create_task(worker.run()) for worker in self.workers]

        # Notify task subscribers
        for subscriber in self.task_subscribers:
            try:
                await subscriber("pool_started", None)
            except Exception as e:
                logger.error(f"Task subscriber error: {e}")

        # Wait for all workers to complete
        await asyncio.gather(*worker_tasks, return_exceptions=True)

        logger.info("XAI thread pool stopped")

    async def stop(self):
        """Stop the thread pool."""
        if not self.is_running:
            return

        self.is_running = False
        logger.info("Stopping XAI thread pool")

        # Signal workers to stop
        for worker in self.workers:
            worker.is_running = False

        # Wait for workers to finish
        await asyncio.sleep(0.1)  # Give workers time to stop

        logger.info("XAI thread pool stopped")

    def get_queue_status(self) -> dict[str, Any]:
        """Get current queue and worker status."""
        queue_size = self.task_queue.qsize()
        active_workers = sum(1 for worker in self.workers if worker.is_running)

        worker_stats = []
        for worker in self.workers:
            stats = {
                "worker_id": worker.worker_id,
                "is_active": worker.is_running,
                "active_task": worker.stats.active_task,
                "tasks_completed": worker.stats.tasks_completed,
                "average_processing_time": worker.stats.average_processing_time,
                "last_activity": worker.stats.last_activity.isoformat() if worker.stats.last_activity else None,
            }
            worker_stats.append(stats)

        return {
            "queue_size": queue_size,
            "active_workers": active_workers,
            "max_workers": self.max_workers,
            "worker_stats": worker_stats,
            "is_running": self.is_running,
        }

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get overall performance metrics."""
        if not self.workers:
            return {
                "total_workers": 0,
                "total_tasks_completed": 0,
                "average_processing_time": 0.0,
                "queue_size": 0,
                "is_running": False,
            }

        total_completed = sum(worker.stats.tasks_completed for worker in self.workers)
        total_time = sum(worker.stats.total_processing_time for worker in self.workers)
        avg_time = total_time / total_completed if total_completed > 0 else 0.0

        return {
            "total_workers": len(self.workers),
            "total_tasks_completed": total_completed,
            "average_processing_time": avg_time,
            "queue_size": self.task_queue.qsize(),
            "is_running": self.is_running,
        }

    async def get_task_result(self, task_id: str) -> Any | None:
        """
        Get result of a specific task (if available).

        This would require tracking task completion and storing results.
        """
        # Implementation would need to track completed tasks
        # For now, return None
        return None

    async def wait_for_task(self, task_id: str, timeout: float = 30.0) -> Any | None:
        """
        Wait for a specific task to complete.

        Args:
            task_id: Task identifier
            timeout: Maximum wait time in seconds

        Returns:
            Task result or None if timeout
        """
        # This would require task tracking infrastructure
        # For now, simulate waiting
        start_time = datetime.now()

        while (datetime.now() - start_time).total_seconds() < timeout:
            # Check if task is completed (this would need task tracking)
            await asyncio.sleep(0.1)

            # Placeholder - would check actual task status
            # if task_is_completed(task_id):
            #     return get_task_result(task_id)

        logger.warning(f"Task {task_id} timeout after {timeout}s")
        return None


class XAIResourceManager:
    """
    Resource manager for XAI operations with load balancing and monitoring.
    """

    def __init__(self):
        self.resource_limits = {
            "max_concurrent_explanations": 10,
            "max_memory_usage_mb": 1024,
            "max_cpu_usage_percent": 80.0,
        }
        self.current_usage = {"active_explanations": 0, "memory_usage_mb": 0.0, "cpu_usage_percent": 0.0}
        self.usage_history: list[dict[str, Any]] = []

    def can_accept_task(self, task_type: str) -> bool:
        """
        Check if a new task can be accepted based on current resource usage.
        """
        if self.current_usage["active_explanations"] >= self.resource_limits["max_concurrent_explanations"]:
            return False

        # Simple heuristic for CPU/memory intensive tasks
        intensive_tasks = ["large_explanation", "complex_analysis", "batch_processing"]
        if task_type in intensive_tasks:
            if self.current_usage["cpu_usage_percent"] > 60.0 or self.current_usage["memory_usage_mb"] > 512:
                return False

        return True

    def allocate_resources(self, task_type: str) -> bool:
        """
        Allocate resources for a task.
        """
        if not self.can_accept_task(task_type):
            return False

        # Simulate resource allocation
        if task_type in ["large_explanation", "complex_analysis"]:
            self.current_usage["memory_usage_mb"] += 256
            self.current_usage["cpu_usage_percent"] += 10.0

        self.current_usage["active_explanations"] += 1

        return True

    def release_resources(self, task_type: str):
        """
        Release resources after task completion.
        """
        if task_type in ["large_explanation", "complex_analysis"]:
            self.current_usage["memory_usage_mb"] = max(0, self.current_usage["memory_usage_mb"] - 256)
            self.current_usage["cpu_usage_percent"] = max(0, self.current_usage["cpu_usage_percent"] - 10.0)

        self.current_usage["active_explanations"] = max(0, self.current_usage["active_explanations"] - 1)

        # Log usage
        self.usage_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "action": "resource_release",
                "task_type": task_type,
                "current_usage": self.current_usage.copy(),
            }
        )

    def get_resource_status(self) -> dict[str, Any]:
        """
        Get current resource usage and limits.
        """
        return {
            "current_usage": self.current_usage,
            "resource_limits": self.resource_limits,
            "usage_history": self.usage_history[-10:],  # Last 10 entries
            "is_overloaded": (
                self.current_usage["active_explanations"] >= self.resource_limits["max_concurrent_explanations"]
                or self.current_usage["memory_usage_mb"] > self.resource_limits["max_memory_usage_mb"]
                or self.current_usage["cpu_usage_percent"] > self.resource_limits["max_cpu_usage_percent"]
            ),
        }


# Global instances for convenience
# Delay instantiation to avoid circular imports during module load
# stream_adapter and thread_pool will be created lazily when accessed

_stream_adapter = None
_thread_pool = None
_resource_manager = None


def get_stream_adapter():
    """Get or create stream adapter instance."""
    global _stream_adapter
    if _stream_adapter is None:
        from .stream_adapter import XAIStreamAdapter

        _stream_adapter = XAIStreamAdapter()
    return _stream_adapter


def get_thread_pool():
    """Get or create thread pool instance."""
    global _thread_pool
    if _thread_pool is None:
        _thread_pool = XAIThreadPool()
    return _thread_pool


def get_resource_manager():
    """Get or create resource manager instance."""
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = XAIResourceManager()
    return _resource_manager


# Backward compatibility - create at module level if possible
try:
    from .stream_adapter import XAIStreamAdapter

    stream_adapter = XAIStreamAdapter()
    thread_pool = XAIThreadPool()
    resource_manager = XAIResourceManager()
except ImportError:
    stream_adapter = None
    thread_pool = None
    resource_manager = None
