import time

from prometheus_client import Histogram

# Pre-hook: Initialize metrics
STREAM_DURATION = Histogram("stream_duration_seconds", "Stream connection duration")


class StreamMonitorMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Check for stream in path
        path = scope["path"]
        # Handle string path (standard Starlette) vs bytes (user snippet implication)
        is_stream = "stream" in path if isinstance(path, str) else b"stream" in path

        if is_stream:
            start_time = time.time()
            bytes_sent = 0

            async def monitored_send(message):
                nonlocal bytes_sent
                if message["type"] == "http.response.body":
                    bytes_sent += len(message.get("body", b""))
                await send(message)

            await self.app(scope, receive, monitored_send)
            duration = time.time() - start_time
            STREAM_DURATION.observe(duration)
        else:
            await self.app(scope, receive, send)
