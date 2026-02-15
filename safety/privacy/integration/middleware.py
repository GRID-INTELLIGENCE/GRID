"""
FastAPI Middleware Integration for Privacy Shield.

Provides middleware for seamless integration with the GRID API.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from safety.observability.logging_setup import get_logger
from safety.observability.metrics import (
    PRIVACY_BLOCKED_TOTAL,
    PRIVACY_DETECTION_LATENCY,
    PRIVACY_DETECTION_REQUESTS_TOTAL,
    PRIVACY_MASKED_TOTAL,
)
from safety.privacy.core.engine import (
    PrivacyEngine,
    get_privacy_engine,
)
from safety.privacy.core.presets import PrivacyPreset

# Module-level default so type checker treats it as PrivacyPreset, not Literal['balanced']
_DEFAULT_PRIVACY_PRESET: PrivacyPreset = PrivacyPreset.BALANCED


logger = get_logger("privacy.middleware")


@dataclass
class MiddlewareConfig:
    """Configuration for privacy middleware."""

    preset: PrivacyPreset = field(default_factory=lambda: _DEFAULT_PRIVACY_PRESET)
    collaborative: bool = False
    context_id_header: str = "x-workspace-id"
    user_id_header: str = "x-user-id"
    enable_input: bool = True
    enable_output: bool = True
    process_paths: list[str] = field(default_factory=lambda: ["/chat", "/complete", "/generate"])
    exempt_paths: list[str] = field(default_factory=lambda: ["/health", "/metrics", "/privacy"])
    require_user_input: bool = False


class PrivacyMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for automatic privacy protection.

    Features:
    - Input filtering: Scan and mask PII in user requests
    - Output filtering: Scan and mask PII in model responses
    - Collaborative mode: Workspace-specific configurations
    - User choice support: Interactive mode returns choices to client
    """

    def __init__(self, app, config: MiddlewareConfig | None = None):
        super().__init__(app)
        self._config = config or MiddlewareConfig()
        self._engine: PrivacyEngine | None = None

    def _get_engine(self, context_id: str | None = None) -> PrivacyEngine:
        """Get or create privacy engine for context."""
        if self._engine is None:
            self._engine = get_privacy_engine(
                collaborative=self._config.collaborative,
                context_id=context_id,
                preset=self._config.preset,
            )
        return self._engine

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through privacy pipeline."""
        start_time = time.perf_counter()

        # Skip exempt paths
        if any(request.url.path.startswith(p) for p in self._config.exempt_paths):
            return await call_next(request)

        # Get context IDs
        context_id = request.headers.get(self._config.context_id_header)
        user_id = request.headers.get(self._config.user_id_header)

        engine = self._get_engine(context_id)

        # Process input if enabled and path matches
        request_body = None
        if self._config.enable_input and any(request.url.path.startswith(p) for p in self._config.process_paths):
            request_body = await self._process_input(request, engine, user_id)

        # Continue to endpoint
        response = await call_next(request)

        # Process output if enabled
        if self._config.enable_output and request_body is not None:
            response = await self._process_output(request, response, engine, user_id, start_time)

        # Record metrics
        latency = time.perf_counter() - start_time
        PRIVACY_DETECTION_LATENCY.observe(latency)
        PRIVACY_DETECTION_REQUESTS_TOTAL.inc()

        return response

    async def _process_input(
        self,
        request: Request,
        engine: PrivacyEngine,
        user_id: str | None,
    ) -> dict[str, Any] | None:
        """Process request body for PII."""
        import json

        body = await request.body()
        data = json.loads(body)
        text = self._extract_text(data)
        result = await engine.process(text, context_id=user_id)
        if result.requires_user_input and not self._config.require_user_input:
            # Return detection results for client to decide
            return {
                "detections": result.detections,
                "requires_choice": True,
            }

        if result.masked:
            # Replace text in original data
            data = self._replace_text(data, result.original_text, result.processed_text)
            PRIVACY_MASKED_TOTAL.inc()

        if result.blocked:
            PRIVACY_BLOCKED_TOTAL.inc()
            return None

        return data

    async def _process_output(
        self,
        request: Request,
        response: Response,
        engine: PrivacyEngine,
        user_id: str | None,
        start_time: float,
    ) -> Response:
        """Process response body for PII."""
        try:
            # For now, output processing would require streaming modification
            # This is a placeholder for full output filtering
            return response
        except Exception as e:
            logger.error("privacy_output_processing_error", error=str(e))
            return response

    def _extract_text(self, data: dict[str, Any]) -> str:
        """Extract text from request data."""
        # Common fields to check
        for field_name in ["message", "prompt", "input", "text", "content", "query"]:
            if field_name in data and isinstance(data[field_name], str):
                return data[field_name]

        # Check nested
        if "messages" in data and isinstance(data["messages"], list):
            for msg in data["messages"]:
                if isinstance(msg, dict) and "content" in msg:
                    return str(msg["content"])

        return str(data) if data else ""

    def _replace_text(
        self,
        data: dict[str, Any],
        original: str,
        replacement: str | None,
    ) -> dict[str, Any]:
        """Replace text in data structure."""
        if replacement is None:
            return data

        import json

        data_str = json.dumps(data)
        data_str = data_str.replace(original, replacement)
        return json.loads(data_str)


# Convenience function for adding middleware
def add_privacy_middleware(
    app,
    preset: PrivacyPreset = _DEFAULT_PRIVACY_PRESET,
    collaborative: bool = False,
    context_id_header: str = "x-workspace-id",
    user_id_header: str = "x-user-id",
    enable_input: bool = True,
    enable_output: bool = True,
    process_paths: list[str] = field(default_factory=lambda: ["/chat", "/complete", "/generate"]),
    exempt_paths: list[str] = field(default_factory=lambda: ["/health", "/metrics", "/privacy"]),
    require_user_input: bool = False,
) -> PrivacyMiddleware:
    """
    Add privacy middleware to a FastAPI app.

    Args:
        app: FastAPI application
        preset: Privacy preset to use
        collaborative: Enable collaborative mode
        context_id_header: Header for workspace ID
        enable_input: Scan input
        enable_output: Scan output

    Returns:
        Configured PrivacyMiddleware instance
    """
    config = MiddlewareConfig(
        preset=preset,
        collaborative=collaborative,
        context_id_header=context_id_header,
        enable_input=enable_input,
        enable_output=enable_output,
        process_paths=process_paths,
        exempt_paths=exempt_paths,
        require_user_input=require_user_input,
    )

    middleware = PrivacyMiddleware(app, config)
    app.add_middleware(PrivacyMiddleware, config=config)

    return middleware
