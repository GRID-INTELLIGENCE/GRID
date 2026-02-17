"""FastAPI endpoints for observability and error metrics.

Exposes retry/fallback metrics, health checks, and operational status via REST API.
"""

from typing import Any

from fastapi import APIRouter, HTTPException

from grid.resilience.metrics import get_metrics_collector

__all__ = ["create_metrics_router"]


def create_metrics_router() -> APIRouter:
    """Create FastAPI router with metrics endpoints.

    Returns:
        APIRouter with /metrics and related endpoints.
    """
    router = APIRouter(prefix="/metrics", tags=["observability"])

    @router.get("/health", summary="Health check")
    async def health_check() -> dict[str, str]:
        """Quick health check endpoint.

        Returns:
            Status information.
        """
        return {"status": "healthy"}

    @router.get("/retry", summary="Get retry/fallback metrics")
    async def get_retry_metrics() -> dict[str, Any]:
        """Get aggregated retry and fallback metrics.

        Returns:
            Retry metrics in JSON format:
            - timestamp: ISO 8601 timestamp
            - aggregate_success_rate_pct: Overall success rate
            - aggregate_fallback_rate_pct: Overall fallback rate
            - total_operations_tracked: Unique operations with metrics
            - operations: Per-operation breakdown
        """
        collector = get_metrics_collector()
        metrics = collector.get_metrics()
        return metrics.to_dict()

    @router.get("/retry/export", summary="Export metrics for monitoring systems")
    async def export_metrics() -> dict[str, Any]:
        """Export metrics in monitoring-friendly format.

        Suitable for Prometheus, DataDog, New Relic, etc.

        Returns:
            Metrics with system uptime and reset information.
        """
        collector = get_metrics_collector()
        return collector.export_for_monitoring()

    @router.get("/retry/{operation_name}", summary="Get metrics for specific operation")
    async def get_operation_metrics(operation_name: str) -> dict[str, Any]:
        """Get metrics for a specific operation.

        Args:
            operation_name: Operation identifier (e.g., 'network.fetch_api').

        Returns:
            Operation-specific metrics.

        Raises:
            HTTPException: If operation not found.
        """
        collector = get_metrics_collector()
        metric = collector.get_operation_metric(operation_name)
        if metric is None:
            raise HTTPException(status_code=404, detail=f"No metrics for {operation_name}")
        return metric.to_dict()

    @router.post("/retry/reset", summary="Reset metrics")
    async def reset_metrics(minutes_before: int = 0) -> dict[str, str]:
        """Reset metrics, optionally only older than a certain age.

        Args:
            minutes_before: Reset only metrics older than this many minutes.
                           If 0, reset all metrics.

        Returns:
            Confirmation with count reset.
        """
        collector = get_metrics_collector()
        if minutes_before > 0:
            from datetime import timedelta

            count = collector.reset_metrics(older_than=timedelta(minutes=minutes_before))
        else:
            count = collector.reset_metrics()
        return {"status": "reset", "metrics_cleared": count}

    return router
