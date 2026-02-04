"""
Production monitoring module for GRID.

Provides Prometheus metrics collection and export for key GRID services:
- Mothership API (HTTP metrics)
- Event Bus (event throughput, latency)
- RAG System (query performance, cache hits)
- Database operations (query count, latency)

Usage:
    from application.monitoring import setup_metrics, get_metrics_router

    app = FastAPI()
    setup_metrics(app)
    app.include_router(get_metrics_router())
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.responses import Response as StarletteResponse
from starlette.routing import Match

# ============================================================================
# Prometheus Metrics Registry
# ============================================================================

registry = CollectorRegistry()

# ============================================================================
# HTTP Metrics
# ============================================================================

http_requests_total = Counter(
    "grid_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
    registry=registry,
)

http_request_duration_seconds = Histogram(
    "grid_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=registry,
)

# ============================================================================
# Event Bus Metrics
# ============================================================================

event_bus_events_published_total = Counter(
    "grid_event_bus_events_published_total",
    "Total events published to event bus",
    ["domain", "event_type"],
    registry=registry,
)

event_bus_events_consumed_total = Counter(
    "grid_event_bus_events_consumed_total",
    "Total events consumed from event bus",
    ["domain", "event_type"],
    registry=registry,
)

event_bus_event_processing_duration_seconds = Histogram(
    "grid_event_bus_event_processing_duration_seconds",
    "Event processing duration in seconds",
    ["domain", "event_type"],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0),
    registry=registry,
)

event_bus_queue_size = Gauge(
    "grid_event_bus_queue_size",
    "Current event queue size",
    ["domain"],
    registry=registry,
)

# ============================================================================
# RAG System Metrics
# ============================================================================

rag_queries_total = Counter(
    "grid_rag_queries_total",
    "Total RAG queries executed",
    ["query_type"],  # keyword, semantic, hybrid
    registry=registry,
)

rag_query_duration_seconds = Histogram(
    "grid_rag_query_duration_seconds",
    "RAG query duration in seconds",
    ["query_type"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0),
    registry=registry,
)

rag_cache_hits_total = Counter(
    "grid_rag_cache_hits_total",
    "Total RAG cache hits",
    registry=registry,
)

rag_cache_misses_total = Counter(
    "grid_rag_cache_misses_total",
    "Total RAG cache misses",
    registry=registry,
)

rag_index_size_documents = Gauge(
    "grid_rag_index_size_documents",
    "Number of documents in RAG index",
    registry=registry,
)

# ============================================================================
# Database Metrics
# ============================================================================

db_queries_total = Counter(
    "grid_db_queries_total",
    "Total database queries",
    ["operation"],  # select, insert, update, delete
    registry=registry,
)

db_query_duration_seconds = Histogram(
    "grid_db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation"],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0),
    registry=registry,
)

db_connection_pool_size = Gauge(
    "grid_db_connection_pool_size",
    "Database connection pool size",
    registry=registry,
)

# ============================================================================
# Skill System Metrics
# ============================================================================

skill_executions_total = Counter(
    "grid_skill_executions_total",
    "Total skill executions",
    ["skill_name", "status"],  # status: success, error, timeout
    registry=registry,
)

skill_execution_duration_seconds = Histogram(
    "grid_skill_execution_duration_seconds",
    "Skill execution duration in seconds",
    ["skill_name"],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0),
    registry=registry,
)

# ============================================================================
# System Metrics
# ============================================================================

active_connections = Gauge(
    "grid_active_connections",
    "Number of active connections",
    ["connection_type"],  # http, websocket, db
    registry=registry,
)

# ============================================================================
# Context Managers for Metric Recording
# ============================================================================


@asynccontextmanager
async def track_event_processing(domain: str, event_type: str):
    """Track event processing duration."""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        event_bus_event_processing_duration_seconds.labels(domain=domain, event_type=event_type).observe(duration)


@asynccontextmanager
async def track_rag_query(query_type: str):
    """Track RAG query execution."""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        rag_query_duration_seconds.labels(query_type=query_type).observe(duration)


@asynccontextmanager
async def track_db_operation(operation: str):
    """Track database operation."""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        db_query_duration_seconds.labels(operation=operation).observe(duration)


@asynccontextmanager
async def track_skill_execution(skill_name: str):
    """Track skill execution."""
    start_time = time.time()
    status = "success"
    try:
        yield
    except Exception:
        status = "error"
        raise
    finally:
        duration = time.time() - start_time
        skill_execution_duration_seconds.labels(skill_name=skill_name).observe(duration)
        skill_executions_total.labels(skill_name=skill_name, status=status).inc()


# ============================================================================
# FastAPI Integration
# ============================================================================


def setup_metrics(app: FastAPI) -> None:
    """
    Setup Prometheus metrics middleware for FastAPI application.

    Args:
        app: FastAPI application instance
    """

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next: Callable) -> Response:
        """Middleware to track HTTP metrics."""
        start_time = time.time()

        # Determine endpoint path
        endpoint = request.url.path
        for route in app.routes:
            match, child_scope = route.matches(request.scope)
            if match == Match.FULL:
                endpoint = route.path
                break

        try:
            response = await call_next(request)
        except Exception as exc:
            duration = time.time() - start_time
            http_request_duration_seconds.labels(method=request.method, endpoint=endpoint).observe(duration)
            http_requests_total.labels(method=request.method, endpoint=endpoint, status_code=500).inc()
            raise exc

        duration = time.time() - start_time
        http_request_duration_seconds.labels(method=request.method, endpoint=endpoint).observe(duration)
        http_requests_total.labels(method=request.method, endpoint=endpoint, status_code=response.status_code).inc()

        return response


def get_metrics_router() -> APIRouter:  # noqa: F821
    """
    Get router with metrics endpoint.

    Returns:
        APIRouter with /metrics endpoint
    """
    from fastapi import APIRouter

    router = APIRouter()

    @router.get("/metrics", response_class=StarletteResponse)
    async def metrics() -> StarletteResponse:
        """Return Prometheus metrics."""
        return StarletteResponse(
            content=generate_latest(registry),
            media_type=CONTENT_TYPE_LATEST,
        )

    return router
