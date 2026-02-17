"""
Dynamic Request Gateway with Load Balancing and AI Safety Integration
====================================================================

This module implements the core dynamic routing system that transforms
the static broadband dial-up architecture into a responsive, scalable system.

Key Features:
- Dynamic request routing with load balancing
- AI Safety integration for content moderation
- Component pool management
- Real-time performance monitoring
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class RequestPriority(StrEnum):
    """Request priority levels for dynamic routing."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class SafetyLevel(StrEnum):
    """AI Safety evaluation levels."""

    SAFE = "safe"
    WARNING = "warning"
    DANGEROUS = "dangerous"
    BLOCKED = "blocked"


@dataclass
class SafetyScore:
    """AI Safety evaluation result."""

    level: SafetyLevel
    score: float  # 0.0 to 1.0
    reasons: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_safe(self) -> bool:
        return self.level in [SafetyLevel.SAFE, SafetyLevel.WARNING]

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level.value,
            "score": self.score,
            "reasons": self.reasons,
            "metadata": self.metadata,
            "timestamp": datetime.now(UTC).isoformat(),
        }


@dataclass
class WorkerMetrics:
    """Worker performance metrics."""

    worker_id: str
    active_requests: int
    total_processed: int
    avg_response_time: float
    error_rate: float
    last_activity: datetime
    cpu_usage: float
    memory_usage: float

    @property
    def is_available(self) -> bool:
        return self.active_requests < 10 and self.error_rate < 0.05

    @property
    def efficiency_score(self) -> float:
        """Calculate worker efficiency score."""
        load_factor = 1.0 - (self.active_requests / 10.0)
        speed_factor = 1.0 / (1.0 + self.avg_response_time)
        reliability_factor = 1.0 - self.error_rate

        return (load_factor + speed_factor + reliability_factor) / 3.0


class AISafetyInterface:
    """Interface for AI Safety evaluation."""

    async def evaluate_request(self, request: Request) -> SafetyScore:
        """Evaluate request for safety concerns."""
        # Mock implementation - would integrate with actual AI Safety system
        await self._extract_content(request)

        # Simulate safety analysis
        safety_score = SafetyScore(
            level=SafetyLevel.SAFE, score=0.95, reasons=["Content appears safe", "No policy violations detected"]
        )

        return safety_score

    async def _extract_content(self, request: Request) -> str:
        """Extract content from request for analysis."""
        try:
            if request.method == "POST":
                body = await request.body()
                return body.decode("utf-8", errors="ignore")
            return request.url.path
        except Exception as e:
            logger.warning(f"Failed to extract content: {e}")
            return ""


class WorkerPool:
    """Dynamic worker pool for request processing."""

    def __init__(self, min_workers: int = 2, max_workers: int = 20):
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.workers: dict[str, WorkerMetrics] = {}
        self.request_queue: asyncio.Queue = asyncio.Queue()
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Initialize the worker pool."""
        for i in range(self.min_workers):
            await self._add_worker(f"worker_{i}")

    async def get_optimal_worker(self) -> str | None:
        """Get the best available worker based on metrics."""
        async with self._lock:
            available_workers = [
                (worker_id, metrics) for worker_id, metrics in self.workers.items() if metrics.is_available
            ]

            if not available_workers:
                # Try to scale up if no workers available
                await self._scale_up_if_needed()
                available_workers = [
                    (worker_id, metrics) for worker_id, metrics in self.workers.items() if metrics.is_available
                ]

            if not available_workers:
                return None

            # Select worker with highest efficiency score
            best_worker = max(available_workers, key=lambda x: x[1].efficiency_score)
            return best_worker[0]

    async def process_request(self, worker_id: str, request: Request) -> dict[str, Any]:
        """Process request using specific worker."""
        async with self._lock:
            if worker_id not in self.workers:
                raise ValueError(f"Worker {worker_id} not found")

            worker = self.workers[worker_id]
            worker.active_requests += 1
            worker.last_activity = datetime.now(UTC)

        try:
            start_time = time.time()

            # Simulate request processing
            result = await self._simulate_processing(request)

            processing_time = time.time() - start_time

            async with self._lock:
                worker.active_requests -= 1
                worker.total_processed += 1
                worker.avg_response_time = (
                    worker.avg_response_time * (worker.total_processed - 1) + processing_time
                ) / worker.total_processed

            return result

        except Exception as e:
            async with self._lock:
                worker.active_requests -= 1
                # Update error rate
                worker.error_rate = (worker.error_rate * worker.total_processed + 1.0) / (worker.total_processed + 1.0)
            raise e

    async def _add_worker(self, worker_id: str):
        """Add a new worker to the pool."""
        self.workers[worker_id] = WorkerMetrics(
            worker_id=worker_id,
            active_requests=0,
            total_processed=0,
            avg_response_time=0.0,
            error_rate=0.0,
            last_activity=datetime.now(UTC),
            cpu_usage=0.0,
            memory_usage=0.0,
        )
        logger.info(f"Added worker {worker_id} to pool")

    async def _scale_up_if_needed(self):
        """Scale up worker pool if needed."""
        current_workers = len(self.workers)
        if current_workers < self.max_workers:
            new_worker_id = f"worker_{current_workers}"
            await self._add_worker(new_worker_id)

    async def _simulate_processing(self, request: Request) -> dict[str, Any]:
        """Simulate request processing."""
        # Simulate processing time
        await asyncio.sleep(0.1)

        return {
            "status": "processed",
            "timestamp": datetime.now(UTC).isoformat(),
            "request_path": request.url.path,
            "method": request.method,
        }

    def get_pool_stats(self) -> dict[str, Any]:
        """Get worker pool statistics."""
        total_active = sum(w.active_requests for w in self.workers.values())
        total_processed = sum(w.total_processed for w in self.workers.values())
        avg_response_time = (
            sum(w.avg_response_time for w in self.workers.values()) / len(self.workers) if self.workers else 0
        )

        return {
            "total_workers": len(self.workers),
            "active_requests": total_active,
            "total_processed": total_processed,
            "average_response_time": avg_response_time,
            "workers": {
                worker_id: {
                    "active_requests": metrics.active_requests,
                    "efficiency_score": metrics.efficiency_score,
                    "is_available": metrics.is_available,
                }
                for worker_id, metrics in self.workers.items()
            },
        }


class DynamicRouter:
    """
    Dynamic request router with AI Safety integration and load balancing.

    Transforms static broadband dial-up architecture into responsive system.
    """

    def __init__(self):
        self.ai_safety = AISafetyInterface()
        self.worker_pool = WorkerPool()
        self.request_stats = defaultdict(int)
        self._initialized = False

    async def initialize(self):
        """Initialize the dynamic router."""
        if self._initialized:
            return

        await self.worker_pool.initialize()
        self._initialized = True
        logger.info("Dynamic Router initialized successfully")

    async def route_request(self, request: Request) -> Response:
        """
        Route request through dynamic pipeline with AI Safety evaluation.

        Pipeline:
        1. AI Safety evaluation
        2. Request prioritization
        3. Load balancing
        4. Dynamic processing
        5. Response orchestration
        """
        if not self._initialized:
            await self.initialize()

        start_time = time.time()

        try:
            # Step 1: AI Safety evaluation
            safety_score = await self.ai_safety.evaluate_request(request)

            if not safety_score.is_safe():
                self.request_stats["blocked_requests"] += 1
                return self._create_safety_response(safety_score)

            # Step 2: Get optimal worker
            worker_id = await self.worker_pool.get_optimal_worker()

            if not worker_id:
                self.request_stats["no_workers_available"] += 1
                raise HTTPException(status_code=503, detail="No workers available to process request")

            # Step 3: Process request
            result = await self.worker_pool.process_request(worker_id, request)

            # Step 4: Create response
            response_time = time.time() - start_time
            self.request_stats["successful_requests"] += 1

            return JSONResponse(
                content={
                    "success": True,
                    "data": result,
                    "safety": safety_score.to_dict(),
                    "worker_id": worker_id,
                    "processing_time": response_time,
                }
            )

        except Exception as e:
            self.request_stats["failed_requests"] += 1
            logger.error(f"Request routing failed: {e}")
            raise HTTPException(status_code=500, detail="Internal routing error") from e

    def _create_safety_response(self, safety_score: SafetyScore) -> JSONResponse:
        """Create response for blocked requests."""
        status_code = 403 if safety_score.level == SafetyLevel.BLOCKED else 200

        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "safety": safety_score.to_dict(),
                "message": f"Request {safety_score.level.value} due to safety concerns",
            },
        )

    def get_router_stats(self) -> dict[str, Any]:
        """Get router statistics."""
        return {
            "request_stats": dict(self.request_stats),
            "worker_pool": self.worker_pool.get_pool_stats(),
            "initialized": self._initialized,
        }


# Singleton instance
_router: DynamicRouter | None = None


def get_dynamic_router() -> DynamicRouter:
    """Get the singleton DynamicRouter instance."""
    global _router
    if _router is None:
        _router = DynamicRouter()
    return _router
