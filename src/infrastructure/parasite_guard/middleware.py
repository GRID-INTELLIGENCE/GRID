"""
FastAPI middleware for parasite detection and response generation.

Intercepts all requests, runs detector chain, returns null
responses for parasites, and triggers deferred sanitization.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable

from .config import GuardMode, ParasiteGuardConfig
from .detectors import Detector, DetectorChain
from .models import DetectionResult, ParasiteContext
from .profiler import ParasiteProfiler
from .response import DummyResponseGenerator
from .sanitizer import DeferredSanitizer
from .tracer import SourceTraceResolver

logger = logging.getLogger(__name__)


class ParasiteGuardMiddleware:
    """
    ASGI middleware that intercepts all requests.

    Workflow:
    1. Check if parasite guard is enabled
    2. Run detector chain on request
    3. If parasite detected:
       - Generate null response
       - Send response to client
       - Trigger deferred sanitization (background)
       - Return without continuing
    4. If no parasite:
       - Continue to normal application handling
    """

    def __init__(self, app: Any, config: ParasiteGuardConfig):
        self.app = app
        self.config = config
        self.event_bus = None

        # Initialize detector chain
        self.detector_chain = self._create_detector_chain()

        # Initialize response generator
        self.response_generator = DummyResponseGenerator(config)

        # Initialize profiler
        self.profiler = ParasiteProfiler(config)

        # Initialize source tracer
        self.source_tracer = SourceTraceResolver(config)

        # Initialize deferred sanitizer
        self.deferred_sanitizer = DeferredSanitizer(config)

    def _create_detector_chain(self) -> DetectorChain:
        """Create detector chain with all detectors."""
        detectors: list[Detector] = []

        # Import and register detectors
        from .detectors import (
            DBConnectionOrphanDetector,
            EventSubscriptionLeakDetector,
            WebSocketNoAckDetector,
        )

        detectors.append(WebSocketNoAckDetector(self.config))
        detectors.append(EventSubscriptionLeakDetector(self.config))
        detectors.append(DBConnectionOrphanDetector(self.config))

        return DetectorChain(detectors, self.config)

    def wire_event_bus(self, event_bus: Any) -> None:
        """
        Wire EventBus to the EventSubscriptionLeakDetector.

        This must be called after middleware initialization to enable
        subscription leak detection on the actual EventBus instance.

        Args:
            event_bus: The EventBus instance to monitor
        """
        self.event_bus = event_bus
        logger.info("Wired EventBus to ParasiteGuardMiddleware")

        # Find EventSubscriptionLeakDetector and wire the event bus
        # Note: DetectorChain stores detectors in .detectors (not ._detectors)
        for detector in self.detector_chain.detectors:
            if hasattr(detector, "set_event_bus"):
                detector.set_event_bus(event_bus)
                logger.info(f"Wired EventBus to {detector.name} detector")
                break
        else:
            logger.warning("EventSubscriptionLeakDetector not found in detector chain")

        # Also wire to sanitizer
        if hasattr(self.deferred_sanitizer, "set_event_bus"):
            self.deferred_sanitizer.set_event_bus(event_bus)
            logger.info("Wired EventBus to DeferredSanitizer")

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        """
        ASGI middleware entry point.

        Intercepts all requests and applies parasite detection.
        """
        # Check if guard is enabled
        if self.config.disabled or not self.config.enabled:
            # Normal path: bypass detection
            await self.app(scope, receive, send)
            return

        # Build request abstraction
        request = self._asgi_to_request(scope, receive)

        # Run detection
        detection_result = await self.detector_chain.detect(request)

        if not detection_result or not detection_result.detected:
            # No parasite: normal processing
            await self.app(scope, receive, send)
            return

        # PARASITE DETECTED!
        context = detection_result.context
        logger.info(
            f"Parasite detected: {context.component} - {context.pattern}",
            extra={
                "parasite_id": str(context.id),
                "component": context.component,
                "pattern": context.pattern,
                "rule": context.rule,
                "severity": context.severity.name,
                "confidence": detection_result.confidence,
                "reason": detection_result.reason,
            },
        )

        # Get current mode
        mode = self.config.get_component_mode(context.component)

        if mode == GuardMode.DRY_RUN:
            # Dry-run: Continue to normal app, just log
            logger.info(
                f"DRY RUN mode: continuing to normal app for parasite {context.id}",
                extra={"parasite_id": str(context.id)},
            )
            await self.app(scope, receive, send)
            return

        if mode == GuardMode.DETECT:
            # Detect mode: Log and continue
            await self.profiler.record_detection(detection_result, request)
            await self.app(scope, receive, send)
            return

        # FULL mode: Generate null response and sanitize
        await self._handle_parasite(context, request, scope, receive, send)

    async def _handle_parasite(
        self,
        context: ParasiteContext,
        request: Any,
        scope: dict,
        receive: Callable,
        send: Callable,
    ) -> None:
        """
        Handle detected parasite.

        Generates null response and triggers deferred sanitization.
        """
        # Record detection
        await self.profiler.record_detection(DetectionResult(detected=True, context=context), request)

        # Emit security event
        if self.event_bus:
            try:
                # Create event payload
                event_data = {
                    "parasite_id": str(context.id),
                    "component": context.component,
                    "pattern": context.pattern,
                    "severity": context.severity.name,
                    "client_ip": request.client.host,
                    "path": request.url.path,
                    "timestamp": context.timestamp.isoformat(),
                }

                # Publish event (fire and forget via create_task to avoid blocking response)
                from infrastructure.event_bus import Event

                event = Event(topic="system.security.parasite_detected", data=event_data, source="parasite_guard")

                asyncio.create_task(self.event_bus.publish(event), name=f"emit_parasite_event_{context.id}")
            except Exception as e:
                logger.error(f"Failed to emit parasite event: {e}")

        # Resolve source (async but fire-and-forget)
        asyncio.create_task(
            self._resolve_source(context),
            name=f"resolve_source_{context.id}",
        )

        # Generate null response
        response = await self.response_generator.make(context, request)

        # Send response to client
        await self._send_asgi_response(response, scope, receive, send)

        # Trigger deferred sanitization (background, non-blocking)
        asyncio.create_task(
            self.deferred_sanitizer.sanitize_async(context),
            name=f"sanitize_parasite_{context.id}",
        )

    async def _resolve_source(self, context: ParasiteContext) -> None:
        """Resolve source of parasite in background."""
        try:
            source_map = await self.source_tracer.resolve(context)
            if source_map:
                context.source = source_map
                logger.debug(
                    f"Source resolved for parasite {context.id}: {source_map.module}.{source_map.function}:{source_map.line}",
                    extra={"parasite_id": str(context.id), "source_map": source_map.__dict__},
                )
        except Exception as e:
            logger.warning(f"Source resolution failed: {e}", exc_info=True)

    def _asgi_to_request(self, scope: dict, receive: Callable) -> Any:
        """
        Create a minimal request abstraction from ASGI scope.

        Provides attributes expected by detectors:
        - url: with .path and .method
        - method: HTTP method
        - client: with .host
        - state: For custom attributes
        """

        class RequestWrapper:
            def __init__(self, scope, receive):
                self.scope = scope
                self.receive = receive
                self.state = {}
                self.url = type(
                    "URL",
                    (),
                    {
                        "path": scope.get("path", ""),
                        "method": scope.get("method", ""),
                    },
                )
                self.method = scope.get("method", "")

                # Parse client
                client = scope.get("client", (None, None))
                self.client = type(
                    "Client",
                    (),
                    {
                        "host": client[0] if client else None,
                        "port": client[1] if client else None,
                    },
                )()

        return RequestWrapper(scope, receive)

    async def _send_asgi_response(
        self,
        response: Any,
        scope: dict,
        receive: Callable,
        send: Callable,
    ) -> None:
        """
        Send ASGI response from FastAPI response object.

        Handles the conversion from FastAPI response to ASGI messages.
        """
        try:
            # Get response body
            if hasattr(response, "body"):
                body = response.body
                if callable(body):
                    body = await body() if asyncio.iscoroutinefunction(body) else body()
                headers = list(response.headers.items())
            else:
                # Build ASGI response manually
                body = b'{"error": "Parasite detected and handled"}'
                headers = [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode()),
                ]

            # Send response start
            await send(
                {
                    "type": "http.response.start",
                    "status": getattr(response, "status_code", 200),
                    "headers": headers,
                }
            )

            # Send body
            await send(
                {
                    "type": "http.response.body",
                    "body": body,
                    "more_body": False,
                }
            )

        except Exception as e:
            logger.error(f"Failed to send ASGI response: {e}", exc_info=True)
            # Try to send error response
            try:
                await send(
                    {
                        "type": "http.response.start",
                        "status": 500,
                        "headers": [(b"content-type", b"text/plain")],
                    }
                )
                await send(
                    {
                        "type": "http.response.body",
                        "body": b"Internal Server Error",
                        "more_body": False,
                    }
                )
            except:
                pass
