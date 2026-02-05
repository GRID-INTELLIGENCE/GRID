"""
Tests for Parasite Guard middleware and integration.

Tests the complete workflow: detection → response → sanitization.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from infrastructure.parasite_guard.config import GuardMode, ParasiteGuardConfig
from infrastructure.parasite_guard.middleware import ParasiteGuardMiddleware as ParasiteDetectorMiddleware
from infrastructure.parasite_guard.models import (
    DetectionResult,
    ParasiteContext,
    ParasiteSeverity,
)


@pytest.fixture
def config():
    """Create test configuration in dry-run mode."""
    config = ParasiteGuardConfig()
    config.enabled = True
    config.disabled = False
    config.global_mode = GuardMode.DRY_RUN
    return config


@pytest.fixture
def middleware(config):
    """Create middleware instance."""
    # Create mock app
    mock_app = MagicMock()

    return ParasiteDetectorMiddleware(mock_app, config)


# =============================================================================
# Middleware Tests
# =============================================================================


class TestParasiteDetectorMiddleware:
    """Tests for Parasite Detector Middleware."""

    @pytest.mark.asyncio
    async def test_bypass_when_disabled(self, config):
        """Test that middleware bypasses when disabled."""
        config.disabled = True
        mock_app = MagicMock()

        middleware = ParasiteDetectorMiddleware(mock_app, config)

        # Create ASGI scope
        scope = {"type": "http"}
        receive = MagicMock()
        send = MagicMock()

        # Run middleware
        await middleware(scope, receive, send)

        # Assert normal app was called
        mock_app.assert_called_once()

    @pytest.mark.asyncio
    async def test_dry_run_mode_continues_to_app(self, config):
        """Test that dry-run mode continues to normal app."""
        config.global_mode = GuardMode.DRY_RUN
        mock_app = MagicMock()

        middleware = ParasiteDetectorMiddleware(mock_app, config)

        # Mock detector chain to return detection
        with patch.object(
            middleware.detector_chain,
            "detect",
            return_value=DetectionResult(
                detected=True,
                context=ParasiteContext(
                    id="test-id",
                    component="websocket",
                    pattern="no_ack",
                    rule="test_rule",
                    severity=ParasiteSeverity.CRITICAL,
                ),
            ),
        ):
            scope = {"type": "http"}
            receive = MagicMock()
            send = MagicMock()

            await middleware(scope, receive, send)

            # Assert normal app was called (dry-run continues)
            mock_app.assert_called_once()

    @pytest.mark.asyncio
    async def test_detect_mode_continues_to_app(self, config):
        """Test that detect mode continues to normal app."""
        config.global_mode = GuardMode.DETECT
        mock_app = MagicMock()

        middleware = ParasiteDetectorMiddleware(mock_app, config)

        # Mock detector chain to return detection
        with patch.object(
            middleware.detector_chain,
            "detect",
            return_value=DetectionResult(
                detected=True,
                context=ParasiteContext(
                    id="test-id",
                    component="websocket",
                    pattern="no_ack",
                    rule="test_rule",
                    severity=ParasiteSeverity.CRITICAL,
                ),
            ),
        ):
            scope = {"type": "http"}
            receive = MagicMock()
            send = MagicMock()

            await middleware(scope, receive, send)

            # Assert normal app was called (detect mode continues)
            mock_app.assert_called_once()

    @pytest.mark.asyncio
    async def test_full_mode_sends_null_response(self, config):
        """Test that full mode sends null response and doesn't continue."""
        config.global_mode = GuardMode.FULL
        mock_app = MagicMock()

        middleware = ParasiteDetectorMiddleware(mock_app, config)

        # Mock detector chain to return detection
        with patch.object(
            middleware.detector_chain,
            "detect",
            return_value=DetectionResult(
                detected=True,
                context=ParasiteContext(
                    id="test-id",
                    component="websocket",
                    pattern="no_ack",
                    rule="test_rule",
                    severity=ParasiteSeverity.CRITICAL,
                ),
            ),
        ):
            scope = {"type": "http"}
            receive = MagicMock()
            send = MagicMock()

            await middleware(scope, receive, send)

            # Assert normal app was NOT called (full mode blocks)
            mock_app.assert_not_called()

            # Assert send was called (response sent)
            send.assert_called()

    @pytest.mark.asyncio
    async def test_no_detection_continues_to_app(self, config):
        """Test that no detection continues to normal app."""
        mock_app = MagicMock()

        middleware = ParasiteDetectorMiddleware(mock_app, config)

        # Mock detector chain to return no detection
        with patch.object(middleware.detector_chain, "detect", return_value=None):
            scope = {"type": "http"}
            receive = MagicMock()
            send = MagicMock()

            await middleware(scope, receive, send)

            # Assert normal app was called
            mock_app.assert_called_once()

    @pytest.mark.asyncio
    async def test_triggers_deferred_sanitization(self, config):
        """Test that full mode triggers deferred sanitization."""
        config.global_mode = GuardMode.FULL
        mock_app = MagicMock()

        middleware = ParasiteDetectorMiddleware(mock_app, config)

        # Mock detector chain to return detection
        detection_context = ParasiteContext(
            id="test-id",
            component="websocket",
            pattern="no_ack",
            rule="test_rule",
            severity=ParasiteSeverity.CRITICAL,
        )

        with (
            patch.object(
                middleware.detector_chain,
                "detect",
                return_value=DetectionResult(detected=True, context=detection_context),
            ),
            patch.object(
                middleware.deferred_sanitizer,
                "sanitize_async",
                return_value=None,  # Returns immediately (background task)
            ) as mock_sanitize,
        ):
            scope = {"type": "http"}
            receive = MagicMock()
            send = MagicMock()

            await middleware(scope, receive, send)

            # Assert sanitization was triggered
            mock_sanitize.assert_called_once_with(detection_context)

    @pytest.mark.asyncio
    async def test_generates_null_response(self, config):
        """Test that null response is generated for parasite."""
        config.global_mode = GuardMode.FULL
        mock_app = MagicMock()

        middleware = ParasiteDetectorMiddleware(mock_app, config)

        # Mock detector chain to return detection
        detection_context = ParasiteContext(
            id="test-id",
            component="websocket",
            pattern="no_ack",
            rule="test_rule",
            severity=ParasiteSeverity.CRITICAL,
        )

        with patch.object(
            middleware.detector_chain,
            "detect",
            return_value=DetectionResult(detected=True, context=detection_context),
        ):
            scope = {"type": "http"}
            receive = MagicMock()
            send = MagicMock()

            await middleware(scope, receive, send)

            # Assert send was called (response sent)
            send.assert_called_once()

            # Get the send call arguments
            send_call_args = send.call_args

            # Verify response start was sent
            assert send_call_args[0][0]["type"] == "http.response.start"

            # Verify response body was sent
            assert send_call_args[1][0]["type"] == "http.response.body"

            # Verify status code
            assert send_call_args[0][0]["status"] == 200


# =============================================================================
# Request Wrapper Tests
# =============================================================================


class TestRequestWrapper:
    """Tests for ASGI request wrapper."""

    def test_creates_url_wrapper(self, middleware):
        """Test that request wrapper creates URL with path and method."""
        scope = {
            "type": "http",
            "path": "/test/path",
            "method": "GET",
        }
        receive = MagicMock()

        wrapper = middleware._asgi_to_request(scope, receive)

        # Assert URL wrapper
        assert wrapper.url.path == "/test/path"
        assert wrapper.url.method == "GET"

    def test_creates_client_wrapper(self, middleware):
        """Test that request wrapper creates client with host."""
        scope = {
            "type": "http",
            "client": ("127.0.0.1", 8080),
        }
        receive = MagicMock()

        wrapper = middleware._asgi_to_request(scope, receive)

        # Assert client wrapper
        assert wrapper.client.host == "127.0.0.1"
        assert wrapper.client.port == 8080

    def test_handles_missing_client(self, middleware):
        """Test that request wrapper handles missing client."""
        scope = {
            "type": "http",
            "path": "/test",
            "method": "GET",
        }
        receive = MagicMock()

        wrapper = middleware._asgi_to_request(scope, receive)

        # Assert client is None wrapper
        assert wrapper.client.host is None
        assert wrapper.client.port is None


# =============================================================================
# ASGI Response Tests
# =============================================================================


class TestASGIResponse:
    """Tests for ASGI response sending."""

    @pytest.mark.asyncio
    async def test_sends_response_start(self, config):
        """Test that ASGI response start is sent correctly."""
        config.global_mode = GuardMode.FULL
        mock_app = MagicMock()

        middleware = ParasiteDetectorMiddleware(mock_app, config)

        detection_context = ParasiteContext(
            id="test-id",
            component="websocket",
            pattern="no_ack",
            rule="test_rule",
            severity=ParasiteSeverity.CRITICAL,
        )

        with patch.object(
            middleware.detector_chain,
            "detect",
            return_value=DetectionResult(detected=True, context=detection_context),
        ):
            scope = {"type": "http"}
            receive = MagicMock()
            send = MagicMock()

            await middleware(scope, receive, send)

            # Verify send was called
            send.assert_called()

    @pytest.mark.asyncio
    async def test_handles_response_exception(self, config):
        """Test that middleware handles response exception gracefully."""
        config.global_mode = GuardMode.FULL
        mock_app = MagicMock()

        middleware = ParasiteDetectorMiddleware(mock_app, config)

        # Mock response generator to raise exception
        with (
            patch.object(
                middleware.response_generator,
                "make",
                side_effect=Exception("Response generation failed"),
            ),
            patch.object(
                middleware.detector_chain,
                "detect",
                return_value=DetectionResult(
                    detected=True,
                    context=ParasiteContext(
                        id="test-id",
                        component="websocket",
                        pattern="no_ack",
                        rule="test_rule",
                        severity=ParasiteSeverity.CRITICAL,
                    ),
                ),
            ),
        ):
            scope = {"type": "http"}
            receive = MagicMock()
            send = MagicMock()

            # Should not raise exception
            await middleware(scope, receive, send)

            # Assert error response was sent as fallback
            send.assert_called()


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
