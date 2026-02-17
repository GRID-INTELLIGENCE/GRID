"""
Distributed tracing module for GRID using OpenTelemetry and Jaeger.

Provides trace instrumentation for:
- HTTP requests (FastAPI)
- Database operations (SQLAlchemy)
- Event bus processing (Unified Fabric)
- Async operations
- External API calls

Usage:
    from application.tracing import setup_tracing

    setup_tracing(
        service_name="grid-mothership",
        jaeger_host="localhost",
        jaeger_port=6831,
    )
"""

from __future__ import annotations

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# ============================================================================
# Tracer Setup
# ============================================================================


def setup_tracing(
    service_name: str = "grid-service",
    jaeger_host: str = "localhost",
    jaeger_port: int = 4317,
    environment: str = "development",
    enable_logs: bool = True,
) -> TracerProvider:
    """
    Setup OpenTelemetry tracing with OTLP exporter (Jaeger compatible).

    Args:
        service_name: Name of the service
        jaeger_host: OTLP collector host
        jaeger_port: OTLP collector gRPC port (4317 for Jaeger)
        environment: Environment name (development, staging, production)
        enable_logs: Enable log instrumentation

    Returns:
        TracerProvider instance
    """

    # Create OTLP exporter (works with Jaeger)
    otlp_exporter = OTLPSpanExporter(
        endpoint=f"http://{jaeger_host}:{jaeger_port}",
        insecure=True,
    )

    # Create tracer provider with resource attributes
    trace_provider = TracerProvider(
        resource=Resource.create(
            {
                "service.name": service_name,
                "service.version": "2.2.0",
                "deployment.environment": environment,
            }
        )
    )
    trace_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    # Set global tracer provider
    trace.set_tracer_provider(trace_provider)

    # Instrument common libraries
    FastAPIInstrumentor().instrument()
    RequestsInstrumentor().instrument()
    HTTPXClientInstrumentor().instrument()

    # Instrument SQLAlchemy if available
    try:
        SQLAlchemyInstrumentor().instrument(engine_hook=lambda engine: True)
    except Exception:
        pass  # SQLAlchemy not installed or already instrumented

    # Instrument logging
    if enable_logs:
        LoggingInstrumentor().instrument(
            set_logging_format=True,
            capture_source_code_attributes=True,
        )

    # Add resource attributes
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("service_startup") as span:
        span.set_attribute("service.name", service_name)
        span.set_attribute("service.version", "2.2.0")
        span.set_attribute("deployment.environment", environment)
        span.set_attribute("telemetry.sdk.name", "opentelemetry")
        span.set_attribute("telemetry.sdk.language", "python")

    return trace_provider


# ============================================================================
# FastAPI Integration
# ============================================================================


def setup_fastapi_tracing(app: FastAPI, service_name: str) -> None:
    """
    Setup OpenTelemetry tracing for FastAPI application.

    Args:
        app: FastAPI application instance
        service_name: Name of the service
    """
    FastAPIInstrumentor.instrument_app(app)


# ============================================================================
# Span Helpers
# ============================================================================


def get_tracer(module_name: str) -> trace.Tracer:
    """
    Get a tracer instance for a module.

    Args:
        module_name: Module name (typically __name__)

    Returns:
        Tracer instance
    """
    return trace.get_tracer(module_name)


def add_span_event(
    span_name: str,
    attributes: dict | None = None,
    event_name: str = "event",
) -> None:
    """
    Add an event to the current span.

    Args:
        span_name: Name of the span
        attributes: Event attributes
        event_name: Name of the event
    """
    current_span = trace.get_current_span()
    if current_span:
        current_span.add_event(event_name, attributes or {})


def set_span_attribute(key: str, value) -> None:
    """
    Set an attribute on the current span.

    Args:
        key: Attribute key
        value: Attribute value
    """
    current_span = trace.get_current_span()
    if current_span:
        current_span.set_attribute(key, value)


# ============================================================================
# Span Context
# ============================================================================


class SpanContext:
    """Context manager for creating and managing spans."""

    def __init__(self, tracer: trace.Tracer, span_name: str, attributes: dict | None = None):
        """
        Initialize span context.

        Args:
            tracer: Tracer instance
            span_name: Name of the span
            attributes: Initial span attributes
        """
        self.tracer = tracer
        self.span_name = span_name
        self.attributes = attributes or {}
        self.span = None

    def __enter__(self) -> trace.Span:
        """Enter context."""
        self.span = self.tracer.start_span(self.span_name)
        for key, value in self.attributes.items():
            self.span.set_attribute(key, value)
        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context."""
        if exc_type:
            self.span.set_attribute("error.type", exc_type.__name__)
            self.span.set_attribute("error.message", str(exc_val))
        self.span.end()


# ============================================================================
# Jaeger Docker Compose
# ============================================================================

JAEGER_DOCKER_COMPOSE = """
jaeger:
  image: jaegertracing/all-in-one:latest
  container_name: grid-jaeger
  ports:
    - "16686:16686"  # UI
    - "14268:14268"  # Collector HTTP
    - "14250:14250"  # Collector gRPC
    - "6831:6831/udp"  # Agent Thrift
    - "6832:6832/udp"  # Agent Thrift Compact
  environment:
    - COLLECTOR_OTLP_ENABLED=true
  healthcheck:
    test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:16686/"]
    interval: 10s
    timeout: 5s
    retries: 3
"""
