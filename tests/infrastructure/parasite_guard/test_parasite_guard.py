import uuid
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from infrastructure.parasite_guard.config import ParasiteGuardConfig
from infrastructure.parasite_guard.detectors import Detector
from infrastructure.parasite_guard.middleware import ParasiteDetectorMiddleware
from infrastructure.parasite_guard.models import DetectionResult, ParasiteContext, ParasiteSeverity


class MockDetector(Detector):
    def __init__(self, trigger: bool = False, severity: ParasiteSeverity = ParasiteSeverity.HIGH):
        self.trigger = trigger
        self.severity = severity
        self.name = "mock_detector"
        self.component = "test"

    async def __call__(self, request: Any, **kwargs) -> DetectionResult:
        if self.trigger:
            context = ParasiteContext(
                id=uuid.uuid4(),
                component=self.component,
                pattern="test_pattern",
                rule=self.name,
                severity=self.severity
            )
            return DetectionResult(detected=True, context=context, reason="triggered")
        return DetectionResult(detected=False)

@pytest.mark.asyncio
async def test_middleware_passthrough():
    """Test middleware passes request when no parasite detected."""
    app = AsyncMock()
    config = ParasiteGuardConfig(enabled=True)

    detector = MockDetector(trigger=False)

    # We need to mock _create_detector_chain to use our MockDetector
    with patch("infrastructure.metrics.REGISTRY"):
        middleware = ParasiteDetectorMiddleware(app, config)
        middleware.detector_chain.detect = AsyncMock(return_value=DetectionResult(detected=False))

        scope = {"type": "http", "method": "GET", "path": "/"}
        receive = AsyncMock()
        send = AsyncMock()

        await middleware(scope, receive, send)

        # Should call the next app
        app.assert_awaited_once()

@pytest.mark.asyncio
async def test_middleware_blocking():
    """Test middleware blocks request when parasite detected."""
    app = AsyncMock()
    config = ParasiteGuardConfig(enabled=True)

    with patch("infrastructure.metrics.REGISTRY"):
        middleware = ParasiteDetectorMiddleware(app, config)

        # Mock detection result
        context = ParasiteContext(
            id=uuid.uuid4(),
            component="test",
            pattern="test",
            rule="test",
            severity=ParasiteSeverity.CRITICAL
        )
        middleware.detector_chain.detect = AsyncMock(return_value=DetectionResult(detected=True, context=context))

        # Mock response generation (avoid real ASGI sending for simple assert)
        middleware.response_generator.make = AsyncMock()

        scope = {"type": "http", "method": "GET", "path": "/"}
        receive = AsyncMock()
        send = AsyncMock()

        await middleware(scope, receive, send)

        # Should NOT call the next app
        app.assert_not_called()
        # Should call response generator
        middleware.response_generator.make.assert_awaited_once()
