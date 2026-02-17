"""
GRID Router Integration
=======================
Async safety hooks for GRID routers to de-block synchronous processing.

Features:
- Non-blocking safety validation
- Event-driven request routing
- Memory-efficient caching
"""

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from functools import wraps
from typing import Any

from . import Event, EventDomain, get_event_bus
from .safety_bridge import SafetyBlockedException, SafetyContext, get_safety_bridge
from .safety_router import SafetyDecision

logger = logging.getLogger(__name__)


@dataclass
class RouterRequest:
    """Standard router request structure"""

    content: str
    route_type: str
    user_id: str = "system"
    priority: str = "normal"
    metadata: dict[str, Any] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: f"req_{datetime.now(UTC).timestamp():.0f}")


@dataclass
class RouterResponse:
    """Standard router response structure"""

    success: bool
    data: Any = None
    error: str | None = None
    safety_checked: bool = False
    processing_time_ms: float = 0.0
    request_id: str = ""


def async_safety_wrapper(route_type: str = "dynamic", on_block: Callable | None = None):
    """
    Decorator to wrap router handlers with async safety validation.

    Usage:
        @async_safety_wrapper(route_type="cognitive")
        async def handle_request(request):
            ...
    """

    def decorator(func: Callable[..., Awaitable[Any]]):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.perf_counter()

            # Extract request content
            request = kwargs.get("request")
            if not request and args:
                request = args[0]

            content = ""
            user_id = "system"

            if isinstance(request, dict):
                content = str(request.get("content", request.get("query", request)))
                user_id = request.get("user_id", "system")
            elif isinstance(request, RouterRequest):
                content = request.content
                user_id = request.user_id
            elif request:
                content = str(request)

            # Validate with safety bridge
            bridge = get_safety_bridge()
            context = SafetyContext(project="grid", domain=route_type, user_id=user_id)

            report = await bridge.validate(content, context)

            if report.should_block:
                if on_block:
                    return on_block(report)
                raise SafetyBlockedException(report)

            # Execute original handler
            result = await func(*args, **kwargs)

            elapsed = (time.perf_counter() - start_time) * 1000

            # Wrap result if needed
            if isinstance(result, RouterResponse):
                result.safety_checked = True
                result.processing_time_ms = elapsed
                return result

            return RouterResponse(success=True, data=result, safety_checked=True, processing_time_ms=elapsed)

        return wrapper

    return decorator


class AsyncRouterIntegration:
    """
    Async integration layer for GRID routers.

    De-blocks synchronous routers by:
    1. Async safety validation
    2. Event-driven request queuing
    3. Non-blocking response handling
    """

    def __init__(self):
        self._safety_bridge = get_safety_bridge()
        self._event_bus = get_event_bus()
        self._pending_requests: dict[str, asyncio.Future] = {}
        self._handlers: dict[str, Callable] = {}
        self._initialized = False

    async def initialize(self):
        """Initialize the router integration"""
        if self._initialized:
            return

        # Subscribe to router events
        self._event_bus.subscribe("grid.route.*", self._handle_route_event, domain="grid")
        self._event_bus.subscribe("grid.response.*", self._handle_response_event, domain="grid")

        self._initialized = True
        logger.info("AsyncRouterIntegration initialized")

    async def route_async(self, request: RouterRequest, timeout: float = 30.0) -> RouterResponse:  # noqa: ASYNC109 timeout parameter is handled by caller
        """
        Route request asynchronously with safety validation.

        Args:
            request: Router request
            timeout: Max seconds to wait for response

        Returns:
            RouterResponse with result
        """
        start_time = time.perf_counter()

        # Safety validation
        context = SafetyContext(
            project="grid", domain=request.route_type, user_id=request.user_id, request_id=request.request_id
        )

        report = await self._safety_bridge.validate(request.content, context)

        if report.should_block:
            return RouterResponse(
                success=False,
                error=f"Blocked by safety: {report.threat_level.value}",
                safety_checked=True,
                request_id=request.request_id,
            )

        # Check for registered handler
        if request.route_type in self._handlers:
            try:
                result = await self._handlers[request.route_type](request)
                elapsed = (time.perf_counter() - start_time) * 1000
                return RouterResponse(
                    success=True,
                    data=result,
                    safety_checked=True,
                    processing_time_ms=elapsed,
                    request_id=request.request_id,
                )
            except Exception as e:
                return RouterResponse(success=False, error=str(e), safety_checked=True, request_id=request.request_id)

        # Use event-based routing
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending_requests[request.request_id] = future

        # Publish route event
        event = Event(
            event_type=f"grid.route.{request.route_type}",
            payload={
                "request_id": request.request_id,
                "content": request.content,
                "route_type": request.route_type,
                "user_id": request.user_id,
                "priority": request.priority,
                "metadata": request.metadata,
            },
            source_domain=EventDomain.GRID.value,
            target_domains=["grid"],
        )
        await self._event_bus.publish(event)

        try:
            async with asyncio.timeout(timeout):
                result = await future
            elapsed = (time.perf_counter() - start_time) * 1000

            return RouterResponse(
                success=True,
                data=result,
                safety_checked=True,
                processing_time_ms=elapsed,
                request_id=request.request_id,
            )
        except TimeoutError:
            return RouterResponse(
                success=False, error=f"Timeout after {timeout}s", safety_checked=True, request_id=request.request_id
            )
        finally:
            self._pending_requests.pop(request.request_id, None)

    def register_handler(self, route_type: str, handler: Callable[[RouterRequest], Awaitable[Any]]):
        """Register a handler for a route type"""
        self._handlers[route_type] = handler
        logger.info(f"Registered handler for route type: {route_type}")

    async def _handle_route_event(self, event: Event):
        """Handle incoming route events"""
        route_type = event.event_type.split(".")[-1]
        logger.debug(f"Route event received: {route_type}")

    async def _handle_response_event(self, event: Event):
        """Handle response events to resolve pending requests"""
        request_id = event.payload.get("request_id")
        if request_id and request_id in self._pending_requests:
            future = self._pending_requests[request_id]
            if not future.done():
                future.set_result(event.payload.get("data"))

    def resolve_request(self, request_id: str, data: Any):
        """Manually resolve a pending request"""
        if request_id in self._pending_requests:
            future = self._pending_requests[request_id]
            if not future.done():
                future.set_result(data)


# Create integration hooks for existing routers


def create_dynamic_router_hook():
    """Create hook for DynamicRouter"""

    async def hook(request: dict, user_id: str = "system") -> dict:
        bridge = get_safety_bridge()
        context = SafetyContext(project="grid", domain="dynamic", user_id=user_id)
        report = await bridge.validate(str(request), context)

        return {
            "safety_checked": True,
            "allowed": not report.should_block,
            "decision": report.decision.value,
            "threat_level": report.threat_level.value,
        }

    return hook


def create_cognitive_router_hook():
    """Create hook for CognitiveRouter"""

    async def hook(request: dict, user_id: str = "system") -> dict:
        bridge = get_safety_bridge()
        context = SafetyContext(project="grid", domain="cognitive", user_id=user_id)
        report = await bridge.validate(str(request), context)

        return {
            "safety_checked": True,
            "allowed": not report.should_block,
            "decision": report.decision.value,
            "adaptations_needed": report.decision == SafetyDecision.WARN,
        }

    return hook


# Singleton instance
_router_integration: AsyncRouterIntegration | None = None


def get_router_integration() -> AsyncRouterIntegration:
    """Get the singleton router integration"""
    global _router_integration
    if _router_integration is None:
        _router_integration = AsyncRouterIntegration()
    return _router_integration


async def init_router_integration() -> AsyncRouterIntegration:
    """Initialize the router integration"""
    integration = get_router_integration()
    await integration.initialize()
    return integration
