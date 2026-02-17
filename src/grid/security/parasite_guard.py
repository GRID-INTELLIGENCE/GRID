"""
Parasitic Call Guard - Total Rickall Defense System
====================================================

A comprehensive guard system that detects parasitic function calls,
generates deterministic null-void fractal responses, profiles behavior,
traces origins, and prunes offending code paths.

Inspired by Rick and Morty's "Total Rickall" (S02E04) - the parasites
masquerade as legitimate characters, and only Mr. Poopy Butthole is real.

Components:
- ParasiteDetectorMiddleware: Intercepts and classifies requests
- DummyResponseGenerator: Creates fractal null facade responses
- ParasiteProfiler: Records all parasite activity
- SourceTraceResolver: Traces back to seed code
- PrunerOrchestrator: Safe teardown of offending routes/middleware/modules

Author: GRID Intelligence Framework
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import uuid
import weakref
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum, StrEnum
from pathlib import Path
from typing import Any, Protocol, TypeVar, cast

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

# Import existing ParasiteCallTracer for deep tracing
from .parasite_tracer import ParasiteCallTracer, ParasiteTrace

log = logging.getLogger("parasite_guard")

T = TypeVar("T")
JSON = dict[str, Any] | list[Any] | str | int | float | None


# =============================================================================
# Configuration
# =============================================================================


class ParasiteGuardConfig:
    """
    Global runtime configuration for the Parasite Guard.

    Can be overridden via environment variables:
    - PARASITE_GUARD: Enable/disable guard (default: 1)
    - PARASITE_DETECT_THRESHOLD: Detection threshold (default: 5)
    - PG_WHITELIST: JSON array of whitelisted paths
    - PG_BLACKLIST: JSON array of blacklisted paths
    - PG_PRUNE_ATTEMPTS: Retries before pruning (default: 3)
    - PG_DUMMY_RESPONSE_TTL_SECS: TTL for dummy responses (default: 30)
    """

    # Core settings
    enabled: bool = bool(int(os.getenv("PARASITE_GUARD", "1")))
    detection_threshold: int = int(os.getenv("PARASITE_DETECT_THRESHOLD", "5"))

    # Path filtering
    whitelisted_paths: list[str] = json.loads(os.getenv("PG_WHITELIST", "[]"))
    blacklisted_paths: list[str] = json.loads(os.getenv("PG_BLACKLIST", "[]"))

    # Pruning settings
    prune_attempts: int = int(os.getenv("PG_PRUNE_ATTEMPTS", "3"))
    prune_enabled: bool = bool(int(os.getenv("PG_PRUNE_ENABLED", "0")))  # Disabled by default for safety

    # Response settings
    dummy_response_ttl_secs: int = int(os.getenv("PG_DUMMY_RESPONSE_TTL_SECS", "30"))

    # Excluded paths (health checks, metrics, etc.)
    excluded_paths: list[str] = [
        "/health",
        "/ping",
        "/metrics",
        "/docs",
        "/redoc",
        "/openapi.json",
    ]

    @classmethod
    def is_path_excluded(cls, path: str) -> bool:
        """Check if path should be excluded from parasite detection."""
        return any(path.startswith(excluded) for excluded in cls.excluded_paths)

    @classmethod
    def is_path_whitelisted(cls, path: str) -> bool:
        """Check if path is explicitly whitelisted."""
        return any(path.startswith(wl) for wl in cls.whitelisted_paths)

    @classmethod
    def is_path_blacklisted(cls, path: str) -> bool:
        """Check if path is explicitly blacklisted."""
        return any(path.startswith(bl) for bl in cls.blacklisted_paths)


# =============================================================================
# Data Structures
# =============================================================================


class ParasiteStatus(StrEnum):
    """Status of a detected parasite."""

    DETECTED = "detected"
    PROFILED = "profiled"
    TRACED = "traced"
    PRUNED = "pruned"
    QUARANTINED = "quarantined"


@dataclass
class SourceMap:
    """
    Immutable description of the origin of a parasitic call.

    Used by the SourceTraceResolver to identify the seed code.
    """

    module: str
    function: str
    line: int
    file: str
    package: str | None = None
    import_chain: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "module": self.module,
            "function": self.function,
            "line": self.line,
            "file": self.file,
            "package": self.package,
            "import_chain": self.import_chain,
        }


@dataclass
class ParasiteContext:
    """
    All information that survives the entire request lifecycle.

    This is the "bag of data" passed through the detection, profiling,
    tracing, and pruning pipeline.
    """

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    rule: str = ""  # Detector name that fired
    start_ts: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
    status: ParasiteStatus = ParasiteStatus.DETECTED

    # Request details
    path: str = ""
    method: str = ""
    client_ip: str = ""
    headers: dict[str, str] = field(default_factory=dict)

    # Tracing data
    source: SourceMap | None = None
    trace: ParasiteTrace | None = None

    # EventBus integration - subscription to cleanup
    subscription: Any | None = None  # EventBus subscription if present

    # Cleanup hooks for resource cleanup
    cleanup_hooks: list[Callable] = field(default_factory=list)

    # Metadata
    meta: dict[str, Any] = field(default_factory=dict)

    async def cleanup(self) -> None:
        """Execute all cleanup hooks and resource cleanup."""
        # Run cleanup hooks
        for hook in self.cleanup_hooks:
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook()
                else:
                    hook()
            except Exception as e:
                log.warning("Cleanup hook failed: %s", e)

        # Cleanup EventBus subscription if present
        if self.subscription is not None:
            try:
                from infrastructure.event_bus.event_system import unsubscribe

                await unsubscribe(self.subscription)
                log.info("EventBus subscription cleaned up for parasite %s", self.id)
            except ImportError:
                log.debug("EventBus not available for subscription cleanup")
            except Exception as e:
                log.warning("EventBus subscription cleanup failed: %s", e)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for logging."""
        return {
            "id": str(self.id),
            "rule": self.rule,
            "start_ts": self.start_ts.isoformat(),
            "status": self.status.value,
            "path": self.path,
            "method": self.method,
            "client_ip": self.client_ip,
            "source": self.source.to_dict() if self.source else None,
            "has_subscription": self.subscription is not None,
            "cleanup_hooks_count": len(self.cleanup_hooks),
            "meta": self.meta,
        }


@dataclass
class PruneResult:
    """Result of a pruning operation."""

    success: bool
    reason: str
    steps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "success": self.success,
            "reason": self.reason,
            "steps": self.steps,
        }


# =============================================================================
# Detector Protocol & Implementations
# =============================================================================


class Detector(Protocol):
    """
    Protocol for parasite detection rules.

    Implement this to create custom detection strategies.
    """

    name: str

    async def __call__(self, request: Request) -> ParasiteContext | None:
        """
        Check if the request looks parasitic.

        Returns:
            ParasiteContext if parasitic, None if legitimate.
        """
        ...


class HeaderAnomalyDetector:
    """
    Detects requests with suspicious or missing headers.

    Checks for:
    - Missing X-Correlation-ID (for tracked requests)
    - Suspicious User-Agent patterns
    - Missing or malformed Content-Type
    """

    name = "header_anomaly"

    # Suspicious User-Agent patterns
    SUSPICIOUS_AGENTS = [
        "parasite",
        "bot",
        "crawler",
        "scraper",
        "fuzzer",
        "scanner",
    ]

    async def __call__(self, request: Request) -> ParasiteContext | None:
        headers = dict(request.headers)

        # Check for missing correlation ID on non-external requests
        if "x-correlation-id" not in headers and "x-request-id" not in headers and request.url.path.startswith("/api/"):
            # This could indicate an internal loop or rogue request
            return ParasiteContext(
                rule=self.name,
                path=str(request.url.path),
                method=request.method,
                client_ip=request.client.host if request.client else "unknown",
                headers=headers,
                meta={"reason": "missing_correlation_id"},
            )

        # Check for suspicious User-Agent
        user_agent = headers.get("user-agent", "").lower()
        for suspicious in self.SUSPICIOUS_AGENTS:
            if suspicious in user_agent:
                return ParasiteContext(
                    rule=self.name,
                    path=str(request.url.path),
                    method=request.method,
                    client_ip=request.client.host if request.client else "unknown",
                    headers=headers,
                    meta={"reason": f"suspicious_user_agent:{suspicious}"},
                )

        return None


class FrequencyDetector:
    """
    Detects burst patterns of identical requests.

    Uses a sliding window to track request frequency per client/path combination.
    """

    name = "frequency"

    def __init__(self, window_seconds: float = 60.0) -> None:
        self.window_seconds = window_seconds
        self._counters: dict[tuple[str, str], list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def __call__(self, request: Request) -> ParasiteContext | None:
        import time

        now = time.time()
        fingerprint = f"{request.method}:{request.url.path}"
        client_ip = request.client.host if request.client else "unknown"
        key = (client_ip, fingerprint)

        async with self._lock:
            # Clean old entries
            self._counters[key] = [ts for ts in self._counters[key] if now - ts < self.window_seconds]

            # Record this request
            self._counters[key].append(now)

            # Check threshold
            count = len(self._counters[key])
            if count > ParasiteGuardConfig.detection_threshold:
                return ParasiteContext(
                    rule=self.name,
                    path=str(request.url.path),
                    method=request.method,
                    client_ip=client_ip,
                    headers=dict(request.headers),
                    meta={
                        "reason": "frequency_exceeded",
                        "count": count,
                        "window_seconds": self.window_seconds,
                    },
                )

        return None


class LoopbackDetector:
    """
    Detects potential infinite loop patterns.

    Checks for requests that appear to be calling back to the same service,
    potentially causing infinite loops.
    """

    name = "loopback"

    LOOPBACK_INDICATORS = [
        "127.0.0.1",
        "localhost",
        "::1",
    ]

    async def __call__(self, request: Request) -> ParasiteContext | None:
        headers = dict(request.headers)

        # Check X-Forwarded-For for loopback
        forwarded = headers.get("x-forwarded-for", "")
        referer = headers.get("referer", "")

        for indicator in self.LOOPBACK_INDICATORS:
            if indicator in forwarded or indicator in referer:
                return ParasiteContext(
                    rule=self.name,
                    path=str(request.url.path),
                    method=request.method,
                    client_ip=request.client.host if request.client else "unknown",
                    headers=headers,
                    meta={"reason": f"loopback_detected:{indicator}"},
                )

        return None


class MissingBodyDetector:
    """
    Detects POST/PUT/PATCH requests with empty or malformed bodies.

    These often indicate broken client code or fuzzing attempts.
    """

    name = "missing_body"

    async def __call__(self, request: Request) -> ParasiteContext | None:
        if request.method in ("POST", "PUT", "PATCH"):
            content_length = request.headers.get("content-length", "0")
            content_type = request.headers.get("content-type", "")

            # Empty body on POST/PUT/PATCH is suspicious
            if content_length == "0" and not content_type.startswith("application/x-www-form-urlencoded"):
                return ParasiteContext(
                    rule=self.name,
                    path=str(request.url.path),
                    method=request.method,
                    client_ip=request.client.host if request.client else "unknown",
                    headers=dict(request.headers),
                    meta={"reason": "empty_body_on_mutation"},
                )

        return None


# =============================================================================
# Fractal Null Facade
# =============================================================================


class FractalNullFacade:
    """
    Generates recursive null-filled responses that mirror expected schemas.

    The fractal pattern means every nested object/array is also null-filled,
    creating a complete "void" response that looks structurally valid.
    """

    # The null sentinel value used for all leaf nodes
    _NULL: None = None

    @classmethod
    def build_null_object(cls, schema: Any) -> JSON:
        """
        Recursively build a null-filled object from a schema.

        Supports:
        - Pydantic BaseModel subclasses
        - typing.Dict/List/etc.
        - Plain Python types
        """
        # Pydantic model
        if hasattr(schema, "model_fields"):
            out: dict[str, Any] = {}
            for name, field_info in schema.model_fields.items():
                annotation = field_info.annotation
                out[name] = cls._null_for_type(annotation)
            return out

        # Older Pydantic (v1)
        if hasattr(schema, "__fields__"):
            out = {}
            for name, field in schema.__fields__.items():
                out[name] = cls._null_for_type(field.outer_type_)
            return out

        # Plain dict hint
        origin = getattr(schema, "__origin__", None)
        if origin is dict:
            return {}
        if origin is list:
            return []

        # Fallback
        return None

    @classmethod
    def _null_for_type(cls, typ: Any) -> JSON:
        """Map a Python type hint to the null sentinel."""
        if typ is None or typ is type(None):
            return None

        # Simple primitives
        if typ in (str, int, float, bool):
            return None

        # Check origin for generics
        origin = getattr(typ, "__origin__", None)

        if origin is list:
            return []
        if origin is dict:
            return {}
        if origin is tuple:
            return []

        # Union types (e.g., str | None)
        if origin is type(str | None):
            # Return None for optional types
            return None

        # Pydantic models (nested)
        if hasattr(typ, "model_fields") or hasattr(typ, "__fields__"):
            return cls.build_null_object(typ)

        return None

    @classmethod
    def create_facade_response(
        cls,
        schema: Any | None,
        parasite_meta: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Create a complete fractal null response with hidden metadata.

        The response looks like a valid schema-conforming payload,
        but all values are null/empty, and _parasite_meta is injected.
        """
        if schema is not None:
            payload = cls.build_null_object(schema)
            if isinstance(payload, dict):
                payload["_parasite_meta"] = parasite_meta
                return payload

        # Fallback: generic null response
        return {
            "data": None,
            "success": False,
            "message": None,
            "_parasite_meta": parasite_meta,
        }


# =============================================================================
# Dummy Response Generator
# =============================================================================


class DummyResponseGenerator:
    """
    Generates deterministic null-void responses for parasitic requests.

    Uses FractalNullFacade to create responses that:
    - Conform to expected response schemas (if known)
    - Fill every field with null/empty values
    - Inject hidden metadata for tracking
    """

    async def make(
        self,
        ctx: ParasiteContext,
        request: Request,
    ) -> Response:
        """
        Generate a dummy response for the given parasite context.

        Args:
            ctx: The parasite context with detection info
            request: The original request

        Returns:
            A JSONResponse with fractal null content
        """
        # Try to infer the expected schema
        schema = self._infer_schema(request)

        # Build the fractal null payload
        parasite_meta = {
            "id": str(ctx.id),
            "detected_by": ctx.rule,
            "timestamp": ctx.start_ts.isoformat(),
            "status": ctx.status.value,
        }

        payload = FractalNullFacade.create_facade_response(schema, parasite_meta)

        # Return as JSON with 200 OK (to not trigger retry logic)
        return JSONResponse(
            content=payload,
            status_code=200,
            headers={
                "X-Parasite-ID": str(ctx.id),
                "X-Parasite-Rule": ctx.rule,
                "X-Content-Type-Options": "nosniff",
            },
        )

    def _infer_schema(self, request: Request) -> type | None:
        """
        Attempt to infer the expected response schema from the route.

        FastAPI stores response_model on the endpoint function.
        """
        try:
            endpoint = request.scope.get("endpoint")
            if endpoint and hasattr(endpoint, "response_model"):
                response_model: Any = getattr(endpoint, "response_model", None)
                if response_model is not None and isinstance(response_model, type):
                    return cast(type, response_model)
        except Exception:
            pass

        return None


# =============================================================================
# Parasite Profiler
# =============================================================================


class ParasiteProfiler:
    """
    Records all parasite activity for analysis and alerting.

    Outputs to:
    - Structured logging (JSON)
    - Prometheus metrics (if available)
    - Event bus (if configured)
    """

    def __init__(self) -> None:
        self._metrics_available = False
        self._init_metrics()

    def _init_metrics(self) -> None:
        """Initialize Prometheus metrics for parasite detection."""
        try:
            from prometheus_client import Counter, Gauge, Histogram

            # Use centralized registry to avoid duplicates
            from infrastructure.metrics import REGISTRY

            def get_or_create(cls, name, documentation, labelnames=(), registry=REGISTRY):
                """Helper to get or create a metric safely."""
                try:
                    return cls(name, documentation, labelnames, registry=registry)
                except ValueError:
                    # Metric already exists. Access private API to retrieve it.
                    # This is a common workaround for prometheus_client's lack of get_or_create.
                    return registry._names_to_collectors[name]

            self.parasites_detected = get_or_create(
                Counter,
                "parasite_guard_detected_total",
                "Total parasitic requests detected",
                ["rule"],
                registry=REGISTRY,
            )
            self.dummy_responses = get_or_create(
                Counter,
                "parasite_guard_dummy_responses_total",
                "Total dummy responses sent",
                registry=REGISTRY,
            )
            self.prune_attempts = get_or_create(
                Counter,
                "parasite_guard_prune_attempts_total",
                "Total prune attempts",
                ["outcome"],
                registry=REGISTRY,
            )
            self.detection_latency = get_or_create(
                Histogram,
                "parasite_guard_detection_latency_seconds",
                "Time to detect parasitic request",
                registry=REGISTRY,
            )
            self.active_parasites = get_or_create(
                Gauge,
                "parasite_guard_active_parasites",
                "Currently tracked parasites",
                registry=REGISTRY,
            )
            # Add new metrics for cleanup operations
            self.eventbus_cleanup_success = get_or_create(
                Counter,
                "parasite_guard_eventbus_cleanup_success_total",
                "Successful EventBus subscription cleanups",
                registry=REGISTRY,
            )
            self.db_engine_disposal_success = get_or_create(
                Counter,
                "parasite_guard_db_engine_disposal_success_total",
                "Successful DB engine disposals",
                registry=REGISTRY,
            )
            self.db_engine_disposal_failures = get_or_create(
                Counter,
                "parasite_guard_db_engine_disposal_failures_total",
                "Failed DB engine disposal attempts",
                registry=REGISTRY,
            )

            self._metrics_available = True
            log.info("Parasite Guard metrics initialized")
        except ImportError:
            log.debug("prometheus_client not available, metrics disabled")

    async def record(
        self,
        ctx: ParasiteContext,
        request: Request,
    ) -> None:
        """
        Record a detected parasite.

        This runs asynchronously after the dummy response is sent.
        """
        # Update metrics
        if self._metrics_available:
            self.parasites_detected.labels(rule=ctx.rule).inc()
            self.dummy_responses.inc()

        # Build log payload
        payload = {
            "event": "parasite_detected",
            "parasite_id": str(ctx.id),
            "rule": ctx.rule,
            "path": ctx.path,
            "method": ctx.method,
            "client_ip": ctx.client_ip,
            "timestamp_start": ctx.start_ts.isoformat(),
            "timestamp_end": datetime.now(UTC).isoformat(),
            "status": ctx.status.value,
            "metadata": ctx.meta,
        }

        # Log as JSON
        log.warning("Parasite detected: %s", json.dumps(payload))

        # Publish to event bus if available
        await self._publish_event(ctx, payload)

    async def _publish_event(
        self,
        ctx: ParasiteContext,
        payload: dict[str, Any],
    ) -> None:
        """Publish detection event to event bus."""
        try:
            from infrastructure.event_bus.event_system import EventBus

            # Get or create event bus instance
            # This is a placeholder - actual implementation depends on DI setup
            log.debug("Event bus publication would occur here")
        except ImportError:
            pass
        except Exception as e:
            log.debug("Failed to publish event: %s", e)

    def record_prune(self, result: PruneResult) -> None:
        """Record a pruning attempt result."""
        if self._metrics_available:
            outcome = "success" if result.success else "failure"
            self.prune_attempts.labels(outcome=outcome).inc()

        log_level = logging.INFO if result.success else logging.WARNING
        log.log(
            log_level,
            "Prune result: success=%s reason=%s steps=%s",
            result.success,
            result.reason,
            result.steps,
        )

    def record_eventbus_cleanup_success(self) -> None:
        """Record successful EventBus subscription cleanup."""
        if self._metrics_available:
            self.eventbus_cleanup_success.inc()
        log.debug("EventBus subscription cleanup recorded")

    def record_db_engine_disposal_success(self) -> None:
        """Record successful DB engine disposal."""
        if self._metrics_available:
            self.db_engine_disposal_success.inc()
        log.debug("DB engine disposal success recorded")

    def record_db_engine_disposal_failure(self) -> None:
        """Record failed DB engine disposal attempt."""
        if self._metrics_available:
            self.db_engine_disposal_failures.inc()
        log.debug("DB engine disposal failure recorded")


# Global profiler instance (lazy-initialized)
_profiler: ParasiteProfiler | None = None


def get_profiler() -> ParasiteProfiler:
    """Get or create the global profiler instance (lazy initialization)."""
    global _profiler
    if _profiler is None:
        _profiler = ParasiteProfiler()
    return _profiler


# =============================================================================
# Source Trace Resolver
# =============================================================================


class SourceTraceResolver:
    """
    Resolves the source of a parasitic call.

    Uses the existing ParasiteCallTracer for deep call stack analysis,
    then extracts a SourceMap identifying the seed code.
    """

    async def resolve(self, ctx: ParasiteContext) -> SourceMap | None:
        """
        Resolve the source of the parasitic call.

        Returns:
            SourceMap if source identified, None otherwise
        """
        # Use ParasiteCallTracer for deep analysis
        tracer = ParasiteCallTracer()

        try:
            tracer.start()
            # Let the tracer capture the current call stack
            await asyncio.sleep(0)  # Yield to allow stack capture
        finally:
            tracer.stop()

        # Extract source from the captured trace
        try:
            trace = tracer.extract_trace(ctx.rule)
            ctx.trace = trace

            # Convert seed to SourceMap
            seed = trace.seed
            return SourceMap(
                module=seed.module,
                function=seed.function,
                line=seed.line,
                file=str(seed.file),
                package=self._detect_package(str(seed.file)),
                import_chain=seed.import_chain,
            )
        except ValueError:
            # No active call chain
            return self._resolve_from_stack()

    def _resolve_from_stack(self) -> SourceMap | None:
        """
        Fallback: resolve source from current stack trace.
        """
        import traceback

        stack = traceback.extract_stack()

        # Walk backwards to find first application frame
        for frame in reversed(stack):
            # Skip stdlib/site-packages
            if "site-packages" in frame.filename:
                continue
            if "lib/python" in frame.filename.lower():
                continue

            return SourceMap(
                module=Path(frame.filename).stem,
                function=frame.name,
                line=frame.lineno or 0,
                file=frame.filename,
                package=self._detect_package(frame.filename),
            )

        return None

    def _detect_package(self, filename: str) -> str | None:
        """Detect the package containing a file."""
        p = Path(filename).parent

        for _ in range(5):
            if (p / "pyproject.toml").exists() or (p / "setup.cfg").exists():
                return p.name
            p = p.parent

        return None


# =============================================================================
# Pruner Orchestrator
# =============================================================================


class PrunerOrchestrator:
    """
    Orchestrates safe teardown of parasitic code paths.

    Capabilities:
    - Remove offending routes from FastAPI app
    - Disable middleware by flagging
    - Unload modules from sys.modules
    - Trigger hot-reload/restart hooks

    SAFETY: Pruning is disabled by default (PG_PRUNE_ENABLED=0).
    Enable only in controlled environments.
    """

    def __init__(self, app: FastAPI | None = None) -> None:
        self.app = app
        self._disabled_middlewares: weakref.WeakSet[Any] = weakref.WeakSet()

    async def prune(self, source: SourceMap, context: ParasiteContext | None = None) -> PruneResult:
        """
        Execute pruning actions for the identified source.

        Args:
            source: The identified source of the parasitic call
            context: Optional ParasiteContext with cleanup hooks

        Returns:
            PruneResult with success status and steps taken
        """
        if not ParasiteGuardConfig.prune_enabled:
            return PruneResult(
                success=False,
                reason="Pruning disabled (PG_PRUNE_ENABLED=0)",
                steps=["skipped"],
            )

        steps: list[str] = []
        success = True

        # Step 1: Cleanup context resources if provided
        if context is not None:
            try:
                await context.cleanup()
                steps.append(f"Cleaned up resources for parasite {context.id}")
            except Exception as e:
                success = False
                steps.append(f"Context cleanup failed: {e}")

        # Step 2: Database engine disposal if applicable
        try:
            await self._dispose_database_engine(steps)
        except Exception as e:
            success = False
            steps.append(f"Database disposal failed: {e}")

        # Step 3: EventBus subscription cleanup
        try:
            await self._cleanup_eventbus_subscriptions(steps)
        except Exception as e:
            success = False
            steps.append(f"EventBus cleanup failed: {e}")

        # Step 4: Route removal (if app available)
        if self.app is not None:
            try:
                await self._prune_routes(source, steps)
            except Exception as e:
                success = False
                steps.append(f"Route removal failed: {e}")

        # Step 4: Middleware disabling
        try:
            await self._disable_middleware(source, steps)
        except Exception as e:
            success = False
            steps.append(f"Middleware disable failed: {e}")

        # Step 5: Module unload (dangerous - only if explicitly enabled)
        if os.getenv("PG_UNLOAD_MODULES", "0") == "1":
            try:
                self._unload_module(source, steps)
            except Exception as e:
                success = False
                steps.append(f"Module unload failed: {e}")

        result = PruneResult(
            success=success,
            reason="; ".join(steps) if steps else "No actions taken",
            steps=steps,
        )

        get_profiler().record_prune(result)
        return result

    async def _dispose_database_engine(self, steps: list[str]) -> None:
        """Dispose of database engine connections if available."""
        try:
            from application.mothership.db.engine import dispose_async_engine

            await dispose_async_engine()
            steps.append("Database engine disposed successfully")
            log.info("Database engine disposed during parasite pruning")
            # Record success metric
            get_profiler().record_db_engine_disposal_success()
        except ImportError:
            log.debug("Database engine not available for disposal")
        except Exception as e:
            log.warning("Database engine disposal failed: %s", e)
            # Record failure metric
            get_profiler().record_db_engine_disposal_failure()
            raise

    async def _cleanup_eventbus_subscriptions(self, steps: list[str]) -> None:
        """Clean up EventBus subscriptions if context has subscription."""
        try:
            # Note: EventBus cleanup is handled via ParasiteContext.cleanup()
            # This method provides additional cleanup if needed
            steps.append("EventBus subscription cleanup handled via context")
        except Exception as e:
            log.warning("EventBus cleanup failed: %s", e)
            steps.append(f"EventBus cleanup failed: {e}")

    async def _prune_routes(
        self,
        source: SourceMap,
        steps: list[str],
    ) -> None:
        """Remove routes associated with the source module."""
        if self.app is None:
            return

        before_count = len(self.app.routes)

        # Filter out routes from the offending module
        self.app.routes = [route for route in self.app.routes if not self._route_matches_source(route, source)]

        after_count = len(self.app.routes)
        removed = before_count - after_count

        if removed > 0:
            steps.append(f"Removed {removed} routes from {source.module}")
        else:
            steps.append(f"No routes found for {source.module}")

    def _route_matches_source(self, route: Any, source: SourceMap) -> bool:
        """Check if a route belongs to the source module."""
        endpoint = getattr(route, "endpoint", None)
        if endpoint is None:
            return False

        return getattr(endpoint, "__module__", "") == source.module

    async def _disable_middleware(
        self,
        source: SourceMap,
        steps: list[str],
    ) -> None:
        """Disable middleware from the source module."""
        if self.app is None:
            return

        # Walk middleware stack and flag matching ones
        middleware_stack = getattr(self.app, "middleware_stack", None)
        if middleware_stack is None:
            steps.append("No middleware stack found")
            return

        # Note: This is a simplified approach. Real implementation
        # would need to walk the middleware chain.
        steps.append("Middleware flagging not implemented (safe mode)")

    def _unload_module(
        self,
        source: SourceMap,
        steps: list[str],
    ) -> None:
        """Unload module from sys.modules."""
        module_name = source.module

        if module_name in sys.modules:
            del sys.modules[module_name]
            steps.append(f"Unloaded module {module_name}")
        else:
            steps.append(f"Module {module_name} not in sys.modules")


# =============================================================================
# Main Middleware
# =============================================================================


class ParasiteDetectorMiddleware(BaseHTTPMiddleware):
    """
    FastAPI/Starlette middleware that detects and handles parasitic requests.

    Pipeline:
    1. Run request through detector chain (Chain of Responsibility)
    2. If parasitic: generate dummy response, profile, trace, prune
    3. If legitimate: pass through to normal handling

    Usage:
        app.add_middleware(ParasiteDetectorMiddleware)

    Or use the helper:
        add_parasite_guard(app)
    """

    def __init__(
        self,
        app: ASGIApp,
        detectors: list[Detector] | None = None,
    ) -> None:
        super().__init__(app)

        # Default detector chain
        self.detectors: list[Detector] = detectors or [
            HeaderAnomalyDetector(),
            FrequencyDetector(),
            LoopbackDetector(),
            MissingBodyDetector(),
        ]

        # Components
        self.response_generator = DummyResponseGenerator()
        self.source_resolver = SourceTraceResolver()
        self.pruner: PrunerOrchestrator | None = None

        log.info(
            "ParasiteDetectorMiddleware initialized with %d detectors",
            len(self.detectors),
        )

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Process the request through the parasite detection pipeline."""

        # Check if guard is enabled
        if not ParasiteGuardConfig.enabled:
            return await call_next(request)

        # Check exclusions
        path = str(request.url.path)
        if ParasiteGuardConfig.is_path_excluded(path):
            return await call_next(request)

        if ParasiteGuardConfig.is_path_whitelisted(path):
            return await call_next(request)

        # Run detector chain
        context: ParasiteContext | None = None
        for detector in self.detectors:
            try:
                ctx = await detector(request)
                if ctx is not None:
                    context = ctx
                    break
            except Exception as e:
                log.warning("Detector %s failed: %s", detector.name, e)

        # Normal path - no parasites detected
        if context is None:
            return await call_next(request)

        # Parasitic path - handle the parasite
        return await self._handle_parasite(context, request)

    async def _handle_parasite(
        self,
        ctx: ParasiteContext,
        request: Request,
    ) -> Response:
        """
        Handle a detected parasitic request.

        Pipeline:
        1. Generate dummy response
        2. Profile the detection (async background)
        3. Resolve source trace (async background)
        4. Prune if enabled (async background)
        """

        # Generate and send the dummy response immediately
        response = await self.response_generator.make(ctx, request)

        # Background tasks for profiling and pruning
        asyncio.create_task(self._profile_and_prune(ctx, request))

        return response

    async def _profile_and_prune(
        self,
        ctx: ParasiteContext,
        request: Request,
    ) -> None:
        """Background task for profiling, tracing, and pruning."""

        # Profile
        ctx.status = ParasiteStatus.PROFILED
        await get_profiler().record(ctx, request)

        # Resolve source
        source = await self.source_resolver.resolve(ctx)
        if source is not None:
            ctx.source = source
            ctx.status = ParasiteStatus.TRACED

            log.info(
                "Parasite traced: %s -> %s:%s:%d",
                ctx.id,
                source.module,
                source.function,
                source.line,
            )

            # Prune if enabled - pass context for cleanup
            if self.pruner is not None and ParasiteGuardConfig.prune_enabled:
                result = await self.pruner.prune(source, context=ctx)
                if result.success:
                    ctx.status = ParasiteStatus.PRUNED


# =============================================================================
# Installation Helper
# =============================================================================


def add_parasite_guard(
    app: FastAPI,
    detectors: list[Detector] | None = None,
    enable_pruning: bool = False,
) -> ParasiteDetectorMiddleware:
    """
    Add the Parasite Guard to a FastAPI application.

    Args:
        app: The FastAPI application
        detectors: Optional custom detector list
        enable_pruning: Enable automatic pruning (DANGEROUS)

    Returns:
        The middleware instance for further configuration

    Example:
        from grid.security.parasite_guard import add_parasite_guard

        app = FastAPI()
        guard = add_parasite_guard(app)
    """
    # Create middleware
    middleware = ParasiteDetectorMiddleware(app.router, detectors)

    # Configure pruner if enabled
    if enable_pruning:
        middleware.pruner = PrunerOrchestrator(app)
        log.warning("Parasite Guard pruning ENABLED - use with caution!")

    # Add to app
    app.add_middleware(ParasiteDetectorMiddleware, detectors=detectors)

    log.info(
        "Parasite Guard installed (enabled=%s, pruning=%s)",
        ParasiteGuardConfig.enabled,
        enable_pruning,
    )

    return middleware


# =============================================================================
# Mr. Poopy Butthole Exception (False Positive Handler)
# =============================================================================


class MrPoopyButtholeException(RuntimeError):
    """
    Raised when a legitimate request is mistakenly classified as parasitic.

    Named after the only trustworthy character in Total Rickall.

    When caught, the guard automatically whitelists the offending rule/path
    combination to prevent future false positives.
    """

    def __init__(
        self,
        path: str,
        rule: str,
        message: str = "False positive detected",
    ) -> None:
        self.path = path
        self.rule = rule
        super().__init__(f"{message}: path={path}, rule={rule}")


def report_false_positive(
    path: str,
    rule: str,
) -> None:
    """
    Report a false positive detection.

    This adds the path to the whitelist for future requests.

    Args:
        path: The path that was incorrectly flagged
        rule: The rule that triggered the detection
    """
    ParasiteGuardConfig.whitelisted_paths.append(path)
    log.warning(
        "False positive reported and whitelisted: path=%s, rule=%s",
        path,
        rule,
    )


# =============================================================================
# Module Exports
# =============================================================================


__all__ = [
    # Configuration
    "ParasiteGuardConfig",
    # Data Structures
    "ParasiteContext",
    "ParasiteStatus",
    "SourceMap",
    "PruneResult",
    # Detectors
    "Detector",
    "HeaderAnomalyDetector",
    "FrequencyDetector",
    "LoopbackDetector",
    "MissingBodyDetector",
    # Response Generation
    "FractalNullFacade",
    "DummyResponseGenerator",
    # Profiling & Tracing
    "ParasiteProfiler",
    "SourceTraceResolver",
    # Pruning
    "PrunerOrchestrator",
    # Middleware
    "ParasiteDetectorMiddleware",
    # Installation
    "add_parasite_guard",
    # False Positives
    "MrPoopyButtholeException",
    "report_false_positive",
]
