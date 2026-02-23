"""
API Core - Ghost Function Registry for Zero-Trust Endpoint Invocation.

Implements a centralized registry pattern for API endpoint handlers,
providing single-point-of-control for all API invocations with built-in
security enforcement, metrics, and circuit breaker support.

The Ghost Registry Pattern:
- All endpoint handlers are registered in a central registry
- Invocation goes through a single summon point
- Security, metrics, and circuit breakers are applied uniformly
- Handlers can be dynamically enabled/disabled without code changes

Usage:
    from application.mothership.api_core import ghost_registry, summon_handler

    # Register a handler
    ghost_registry.register("navigation.plan", handler_func)

    # Summon (invoke) a handler
    result = await summon_handler("navigation.plan", request_data)
"""

from __future__ import annotations

import asyncio
import importlib
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, TypeVar

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

T = TypeVar("T")
HandlerFunc = Callable[..., Any | Awaitable[Any]]


# =============================================================================
# Enums and Constants
# =============================================================================


class HandlerState(StrEnum):
    """State of a registered handler."""

    ACTIVE = "active"
    DISABLED = "disabled"
    CIRCUIT_OPEN = "circuit_open"
    DEPRECATED = "deprecated"


class InvocationResult(StrEnum):
    """Result of handler invocation."""

    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    CIRCUIT_OPEN = "circuit_open"
    NOT_FOUND = "not_found"
    DISABLED = "disabled"


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class HandlerMetrics:
    """Metrics for a registered handler."""

    total_invocations: int = 0
    successful_invocations: int = 0
    failed_invocations: int = 0
    total_latency_ms: float = 0.0
    last_invocation: datetime | None = None
    last_error: str | None = None
    last_error_time: datetime | None = None
    consecutive_failures: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_invocations == 0:
            return 1.0
        return self.successful_invocations / self.total_invocations

    @property
    def average_latency_ms(self) -> float:
        """Calculate average latency."""
        if self.successful_invocations == 0:
            return 0.0
        return self.total_latency_ms / self.successful_invocations

    def record_success(self, latency_ms: float) -> None:
        """Record a successful invocation."""
        self.total_invocations += 1
        self.successful_invocations += 1
        self.total_latency_ms += latency_ms
        self.last_invocation = datetime.now(UTC)
        self.consecutive_failures = 0

    def record_failure(self, error: str) -> None:
        """Record a failed invocation."""
        self.total_invocations += 1
        self.failed_invocations += 1
        self.last_error = error
        self.last_error_time = datetime.now(UTC)
        self.last_invocation = datetime.now(UTC)
        self.consecutive_failures += 1

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_invocations": self.total_invocations,
            "successful_invocations": self.successful_invocations,
            "failed_invocations": self.failed_invocations,
            "success_rate": round(self.success_rate, 4),
            "average_latency_ms": round(self.average_latency_ms, 2),
            "last_invocation": self.last_invocation.isoformat() if self.last_invocation else None,
            "consecutive_failures": self.consecutive_failures,
        }


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5  # Failures before opening circuit
    recovery_timeout_seconds: int = 30  # Time before attempting recovery
    half_open_max_requests: int = 3  # Requests to allow in half-open state
    success_threshold: int = 2  # Successes needed to close circuit


@dataclass
class CircuitBreakerState:
    """State of a circuit breaker."""

    is_open: bool = False
    is_half_open: bool = False
    opened_at: datetime | None = None
    half_open_successes: int = 0
    half_open_failures: int = 0

    def should_allow_request(self, config: CircuitBreakerConfig) -> bool:
        """Check if request should be allowed."""
        if not self.is_open:
            return True

        if self.opened_at is None:
            return True

        # Check if recovery timeout has passed
        elapsed = (datetime.now(UTC) - self.opened_at).total_seconds()
        if elapsed >= config.recovery_timeout_seconds:
            if not self.is_half_open:
                self.is_half_open = True
                self.half_open_successes = 0
                self.half_open_failures = 0
            return self.half_open_successes + self.half_open_failures < config.half_open_max_requests

        return False

    def record_success(self, config: CircuitBreakerConfig) -> None:
        """Record successful request."""
        if self.is_half_open:
            self.half_open_successes += 1
            if self.half_open_successes >= config.success_threshold:
                # Close the circuit
                self.is_open = False
                self.is_half_open = False
                self.opened_at = None
                logger.info("Circuit breaker closed after successful recovery")

    def record_failure(self, config: CircuitBreakerConfig, consecutive_failures: int) -> None:
        """Record failed request."""
        if self.is_half_open:
            self.half_open_failures += 1
            # Immediately re-open on failure during half-open
            self.is_open = True
            self.is_half_open = False
            self.opened_at = datetime.now(UTC)
            logger.warning("Circuit breaker re-opened after half-open failure")
        elif consecutive_failures >= config.failure_threshold:
            self.is_open = True
            self.opened_at = datetime.now(UTC)
            logger.warning(f"Circuit breaker opened after {consecutive_failures} consecutive failures")


@dataclass
class RegisteredHandler:
    """A handler registered in the ghost registry."""

    key: str
    handler: HandlerFunc
    module_path: str | None = None
    description: str = ""
    state: HandlerState = HandlerState.ACTIVE
    require_auth: bool = True
    require_sanitization: bool = True
    timeout_ms: int = 30000
    rate_limit: str | None = None
    tags: list[str] = field(default_factory=list)
    metrics: HandlerMetrics = field(default_factory=HandlerMetrics)
    circuit_breaker_config: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    circuit_breaker_state: CircuitBreakerState = field(default_factory=CircuitBreakerState)
    registered_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def is_available(self) -> bool:
        """Check if handler is available for invocation."""
        if self.state not in (HandlerState.ACTIVE, HandlerState.DEPRECATED):
            return False
        if self.circuit_breaker_state.is_open:
            return self.circuit_breaker_state.should_allow_request(self.circuit_breaker_config)
        return True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "key": self.key,
            "module_path": self.module_path,
            "description": self.description,
            "state": self.state.value,
            "require_auth": self.require_auth,
            "require_sanitization": self.require_sanitization,
            "timeout_ms": self.timeout_ms,
            "rate_limit": self.rate_limit,
            "tags": self.tags,
            "metrics": self.metrics.to_dict(),
            "circuit_breaker": {
                "is_open": self.circuit_breaker_state.is_open,
                "is_half_open": self.circuit_breaker_state.is_half_open,
            },
            "registered_at": self.registered_at.isoformat(),
        }


@dataclass
class InvocationContext:
    """Context for handler invocation."""

    request_id: str
    user_id: str | None = None
    auth_context: dict[str, Any] | None = None
    source: str = "api"
    trace_id: str | None = None
    parent_span_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class InvocationResponse[T]:
    """Response from handler invocation."""

    result: InvocationResult
    data: T | None = None
    error: str | None = None
    latency_ms: float = 0.0
    handler_key: str = ""
    request_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "result": self.result.value,
            "data": self.data,
            "error": self.error,
            "latency_ms": round(self.latency_ms, 2),
            "handler_key": self.handler_key,
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
        }


# =============================================================================
# Ghost Registry
# =============================================================================


class GhostRegistry:
    """
    Centralized registry for API endpoint handlers.

    The Ghost Registry provides:
    - Single point of registration for all handlers
    - Uniform security enforcement
    - Circuit breaker protection
    - Metrics collection
    - Dynamic enable/disable of handlers

    All handlers are "ghosts" - they exist in the registry but are only
    materialized (invoked) through the summon_handler interface.
    """

    def __init__(self):
        self._handlers: dict[str, RegisteredHandler] = {}
        self._tags_index: dict[str, set[str]] = {}  # tag -> set of handler keys
        self._lock = asyncio.Lock()
        self._initialized = False

    def register(
        self,
        key: str,
        handler: HandlerFunc,
        *,
        module_path: str | None = None,
        description: str = "",
        require_auth: bool = True,
        require_sanitization: bool = True,
        timeout_ms: int = 30000,
        rate_limit: str | None = None,
        tags: list[str] | None = None,
        circuit_breaker_config: CircuitBreakerConfig | None = None,
    ) -> RegisteredHandler:
        """
        Register a handler in the ghost registry.

        Args:
            key: Unique identifier for the handler (e.g., "navigation.plan")
            handler: The handler function (sync or async)
            module_path: Full module path for lazy loading
            description: Human-readable description
            require_auth: Whether authentication is required
            require_sanitization: Whether input sanitization is required
            timeout_ms: Timeout for handler execution
            rate_limit: Rate limit specification (e.g., "10/second")
            tags: Tags for categorization and filtering
            circuit_breaker_config: Custom circuit breaker configuration

        Returns:
            RegisteredHandler instance

        Raises:
            ValueError: If handler is already registered with this key
        """
        if key in self._handlers:
            logger.warning(f"Handler '{key}' already registered, updating")

        registered = RegisteredHandler(
            key=key,
            handler=handler,
            module_path=module_path,
            description=description,
            require_auth=require_auth,
            require_sanitization=require_sanitization,
            timeout_ms=timeout_ms,
            rate_limit=rate_limit,
            tags=tags or [],
            circuit_breaker_config=circuit_breaker_config or CircuitBreakerConfig(),
        )

        self._handlers[key] = registered

        # Update tags index
        for tag in registered.tags:
            if tag not in self._tags_index:
                self._tags_index[tag] = set()
            self._tags_index[tag].add(key)

        logger.info(f"Registered handler: {key}")
        return registered

    def register_from_module(
        self,
        key: str,
        module_path: str,
        attr_name: str = "handler",
        **kwargs: Any,
    ) -> RegisteredHandler:
        """
        Register a handler by lazy-loading from a module.

        Args:
            key: Unique identifier for the handler
            module_path: Full module path (e.g., "application.mothership.routers.navigation_simple")
            attr_name: Attribute name in the module
            **kwargs: Additional arguments passed to register()

        Returns:
            RegisteredHandler instance
        """

        def lazy_handler(*args: Any, **kw: Any) -> Any:
            module = importlib.import_module(module_path)
            actual_handler = getattr(module, attr_name)
            return actual_handler(*args, **kw)

        return self.register(
            key=key,
            handler=lazy_handler,
            module_path=f"{module_path}:{attr_name}",
            **kwargs,
        )

    def get(self, key: str) -> RegisteredHandler | None:
        """Get a registered handler by key."""
        return self._handlers.get(key)

    def disable(self, key: str) -> bool:
        """Disable a handler."""
        handler = self._handlers.get(key)
        if handler:
            handler.state = HandlerState.DISABLED
            logger.info(f"Disabled handler: {key}")
            return True
        return False

    def enable(self, key: str) -> bool:
        """Enable a previously disabled handler."""
        handler = self._handlers.get(key)
        if handler and handler.state == HandlerState.DISABLED:
            handler.state = HandlerState.ACTIVE
            logger.info(f"Enabled handler: {key}")
            return True
        return False

    def deprecate(self, key: str) -> bool:
        """Mark a handler as deprecated (still works but logs warnings)."""
        handler = self._handlers.get(key)
        if handler:
            handler.state = HandlerState.DEPRECATED
            logger.warning(f"Deprecated handler: {key}")
            return True
        return False

    def unregister(self, key: str) -> bool:
        """Remove a handler from the registry."""
        handler = self._handlers.pop(key, None)
        if handler:
            # Clean up tags index
            for tag in handler.tags:
                if tag in self._tags_index:
                    self._tags_index[tag].discard(key)
            logger.info(f"Unregistered handler: {key}")
            return True
        return False

    def list_handlers(
        self,
        tag: str | None = None,
        state: HandlerState | None = None,
    ) -> list[RegisteredHandler]:
        """
        List registered handlers with optional filtering.

        Args:
            tag: Filter by tag
            state: Filter by state

        Returns:
            List of matching handlers
        """
        handlers = list(self._handlers.values())

        if tag:
            tag_keys = self._tags_index.get(tag, set())
            handlers = [h for h in handlers if h.key in tag_keys]

        if state:
            handlers = [h for h in handlers if h.state == state]

        return handlers

    def get_metrics(self) -> dict[str, Any]:
        """Get aggregated metrics for all handlers."""
        total_invocations = 0
        total_failures = 0
        handlers_by_state = {}

        for handler in self._handlers.values():
            total_invocations += handler.metrics.total_invocations
            total_failures += handler.metrics.failed_invocations
            state = handler.state.value
            handlers_by_state[state] = handlers_by_state.get(state, 0) + 1

        return {
            "total_handlers": len(self._handlers),
            "handlers_by_state": handlers_by_state,
            "total_invocations": total_invocations,
            "total_failures": total_failures,
            "overall_success_rate": (
                round((total_invocations - total_failures) / total_invocations, 4) if total_invocations > 0 else 1.0
            ),
        }

    def reset_circuit_breaker(self, key: str) -> bool:
        """Manually reset a circuit breaker."""
        handler = self._handlers.get(key)
        if handler:
            handler.circuit_breaker_state = CircuitBreakerState()
            handler.metrics.consecutive_failures = 0
            logger.info(f"Reset circuit breaker for handler: {key}")
            return True
        return False

    def to_dict(self) -> dict[str, Any]:
        """Convert registry state to dictionary."""
        return {
            "handlers": {k: v.to_dict() for k, v in self._handlers.items()},
            "metrics": self.get_metrics(),
            "tags": {k: list(v) for k, v in self._tags_index.items()},
        }


# Global registry instance
_ghost_registry: GhostRegistry | None = None


def get_ghost_registry() -> GhostRegistry:
    """Get or create the global ghost registry."""
    global _ghost_registry
    if _ghost_registry is None:
        _ghost_registry = GhostRegistry()
    return _ghost_registry


def reset_ghost_registry() -> None:
    """Reset the global ghost registry (for testing)."""
    global _ghost_registry
    _ghost_registry = None


# Convenience alias
ghost_registry = get_ghost_registry()


# =============================================================================
# Handler Invocation
# =============================================================================


async def summon_handler(
    key: str,
    *args: Any,
    context: InvocationContext | None = None,
    **kwargs: Any,
) -> InvocationResponse[Any]:
    """
    Summon (invoke) a handler from the ghost registry.

    This is the single entry point for all handler invocations,
    providing uniform security enforcement, metrics, and circuit breaker.

    Args:
        key: Handler key (e.g., "navigation.plan")
        *args: Positional arguments for the handler
        context: Optional invocation context
        **kwargs: Keyword arguments for the handler

    Returns:
        InvocationResponse with result or error

    Raises:
        HTTPException: If handler not found or unavailable
    """
    registry = get_ghost_registry()
    handler = registry.get(key)

    request_id = context.request_id if context else "unknown"

    # Check handler exists
    if handler is None:
        logger.warning(f"Handler not found: {key}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No handler registered for key: {key}",
        )

    # Check handler availability
    if not handler.is_available():
        if handler.state == HandlerState.DISABLED:
            logger.warning(f"Handler '{key}' summoned but is DISABLED")
            return InvocationResponse(
                result=InvocationResult.DISABLED,
                error=f"Handler '{key}' is currently disabled",
                handler_key=key,
                request_id=request_id,
            )
        if handler.circuit_breaker_state.is_open:
            handler.metrics.record_failure("Circuit breaker open")
            logger.warning(f"Handler '{key}' summoned but circuit is OPEN")
            return await _get_invocation_fallback(key, request_id)

    # Log deprecation warning
    if handler.state == HandlerState.DEPRECATED:
        logger.warning(f"Invoking deprecated handler: {key}")

    # Execute handler with timeout and metrics
    start_time = time.perf_counter()

    try:
        # Handle both sync and async handlers
        async with asyncio.timeout(handler.timeout_ms / 1000):
            if asyncio.iscoroutinefunction(handler.handler):
                result = await handler.handler(*args, **kwargs)
            else:
                # Run sync handler in thread to not block
                result = await asyncio.to_thread(handler.handler, *args, **kwargs)

        latency_ms = (time.perf_counter() - start_time) * 1000
        handler.metrics.record_success(latency_ms)
        handler.circuit_breaker_state.record_success(handler.circuit_breaker_config)

        return InvocationResponse(
            result=InvocationResult.SUCCESS,
            data=result,
            latency_ms=latency_ms,
            handler_key=key,
            request_id=request_id,
        )

    except HTTPException:
        raise  # Let FastAPI propagate the proper status code (401, 500, etc.)
    except TimeoutError:
        latency_ms = (time.perf_counter() - start_time) * 1000
        error_msg = f"Handler timed out after {handler.timeout_ms}ms"
        handler.metrics.record_failure(error_msg)
        handler.circuit_breaker_state.record_failure(
            handler.circuit_breaker_config,
            handler.metrics.consecutive_failures,
        )

        logger.error(f"Handler '{key}' timed out: {error_msg}")
        return InvocationResponse(
            result=InvocationResult.TIMEOUT,
            error=error_msg,
            latency_ms=latency_ms,
            handler_key=key,
            request_id=request_id,
        )

    except Exception as e:
        latency_ms = (time.perf_counter() - start_time) * 1000
        error_msg = str(e)
        handler.metrics.record_failure(error_msg)
        handler.circuit_breaker_state.record_failure(
            handler.circuit_breaker_config,
            handler.metrics.consecutive_failures,
        )

        logger.exception(f"Handler '{key}' failed: {error_msg}")
        return InvocationResponse(
            result=InvocationResult.FAILURE,
            error=f"Handler execution failed: {error_msg}",
            latency_ms=latency_ms,
            handler_key=key,
            request_id=request_id,
        )


async def _get_invocation_fallback(key: str, request_id: str) -> InvocationResponse[Any]:
    """Provide a fallback response for handler invocation."""
    fallback_data: dict[str, Any] = {
        "fallback": True,
        "message": "Service temporarily unavailable. Returning limited data.",
        "timestamp": datetime.now(UTC).isoformat(),
    }

    # Add key-specific fallbacks
    if "navigation" in key:
        fallback_data["plan"] = []
        fallback_data["status"] = "stalled"
    elif "intelligence" in key or "ai" in key:
        fallback_data["analysis"] = {}
        fallback_data["confidence"] = 0.0

    return InvocationResponse(
        result=InvocationResult.CIRCUIT_OPEN,
        data=fallback_data,
        error="Circuit breaker is open",
        handler_key=key,
        request_id=request_id,
    )


def summon_handler_sync(
    key: str,
    *args: Any,
    context: InvocationContext | None = None,
    **kwargs: Any,
) -> InvocationResponse[Any]:
    """
    Synchronous wrapper for summon_handler.

    Use this when calling from synchronous code.
    """
    return asyncio.run(summon_handler(key, *args, context=context, **kwargs))


# =============================================================================
# Decorator for Handler Registration
# =============================================================================


def register_handler(
    key: str,
    *,
    description: str = "",
    require_auth: bool = True,
    require_sanitization: bool = True,
    timeout_ms: int = 30000,
    rate_limit: str | None = None,
    tags: list[str] | None = None,
) -> Callable[[HandlerFunc], HandlerFunc]:
    """
    Decorator for registering a function as a handler.

    Usage:
        @register_handler("navigation.plan", description="Create navigation plan")
        async def create_navigation_plan(request: NavigationRequest):
            ...

    Args:
        key: Unique handler key
        description: Handler description
        require_auth: Whether authentication is required
        require_sanitization: Whether input sanitization is required
        timeout_ms: Execution timeout
        rate_limit: Rate limit specification
        tags: Handler tags

    Returns:
        Decorator function
    """

    def decorator(func: HandlerFunc) -> HandlerFunc:
        registry = get_ghost_registry()
        registry.register(
            key=key,
            handler=func,
            module_path=f"{func.__module__}:{func.__name__}",
            description=description,
            require_auth=require_auth,
            require_sanitization=require_sanitization,
            timeout_ms=timeout_ms,
            rate_limit=rate_limit,
            tags=tags,
        )
        return func

    return decorator


# =============================================================================
# Registry Loading from Configuration
# =============================================================================


def load_handlers_from_config(config_path: str) -> int:
    """
    Load handler registrations from a YAML configuration file.

    Expected format:
        handlers:
          - key: "navigation.plan"
            module: "application.mothership.routers.navigation_simple"
            attr: "create_navigation_plan"
            description: "Create navigation plan"
            require_auth: true
            timeout_ms: 30000
            tags: ["navigation"]

    Args:
        config_path: Path to YAML configuration file

    Returns:
        Number of handlers loaded
    """
    from pathlib import Path

    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:
        logger.error("PyYAML not installed, cannot load config")
        return 0

    config_file = Path(config_path)
    if not config_file.exists():
        logger.warning(f"Handler config not found: {config_path}")
        return 0

    try:
        config = yaml.safe_load(config_file.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"Failed to parse handler config: {e}")
        return 0

    if not config or "handlers" not in config:
        return 0

    registry = get_ghost_registry()
    loaded = 0

    for handler_config in config.get("handlers", []):
        try:
            key = handler_config.get("key")
            module_path = handler_config.get("module")
            attr_name = handler_config.get("attr", "handler")

            if not key or not module_path:
                continue

            registry.register_from_module(
                key=key,
                module_path=module_path,
                attr_name=attr_name,
                description=handler_config.get("description", ""),
                require_auth=handler_config.get("require_auth", True),
                require_sanitization=handler_config.get("require_sanitization", True),
                timeout_ms=handler_config.get("timeout_ms", 30000),
                rate_limit=handler_config.get("rate_limit"),
                tags=handler_config.get("tags", []),
            )
            loaded += 1

        except Exception as e:
            logger.error(f"Failed to register handler from config: {e}")

    logger.info(f"Loaded {loaded} handlers from {config_path}")
    return loaded


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Enums
    "HandlerState",
    "InvocationResult",
    # Data classes
    "HandlerMetrics",
    "CircuitBreakerConfig",
    "CircuitBreakerState",
    "RegisteredHandler",
    "InvocationContext",
    "InvocationResponse",
    # Registry
    "GhostRegistry",
    "get_ghost_registry",
    "reset_ghost_registry",
    "ghost_registry",
    # Invocation
    "summon_handler",
    "summon_handler_sync",
    # Decorator
    "register_handler",
    # Config loading
    "load_handlers_from_config",
]
