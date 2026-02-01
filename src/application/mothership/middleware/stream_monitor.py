"""
Stream Monitoring Middleware.

Tracks performance metrics for streaming endpoints (SSE, WebSocket, etc.)
and logs anomalies.
"""

import time

try:
    from prometheus_client import Histogram  # type: ignore[import-not-found]

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

    # Mock Histogram for testing
    class Histogram:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def observe(self, value) -> None:
            pass

        def labels(self, **kwargs) -> "Histogram":
            return self


# Prometheus metrics
STREAM_DURATION = Histogram(
    "http_stream_duration_seconds",
    "Duration of HTTP streaming responses in seconds",
    ["endpoint"],
)
STREAM_BYTES_SENT = Histogram(
    "http_stream_bytes_sent",
    "Total bytes sent in streaming responses",
    ["endpoint"],
)


class StreamMonitorMiddleware:
    """ASGI middleware for monitoring streaming endpoints."""

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        """ASGI interface - receives scope, receive, send."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")

        # Only monitor streaming endpoints
        if "stream" not in path:
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        bytes_sent = 0

        async def monitored_send(message) -> None:
            nonlocal bytes_sent
            if message["type"] == "http.response.body":
                bytes_sent += len(message.get("body", b""))
            await send(message)

        try:
            await self.app(scope, receive, monitored_send)
        finally:
            duration = time.time() - start_time
            STREAM_DURATION.labels(endpoint=path).observe(duration)
            STREAM_BYTES_SENT.labels(endpoint=path).observe(bytes_sent)
