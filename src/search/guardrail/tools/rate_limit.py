"""Rate limit guardrail tool: enforces per-identity request limits."""

from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock

from .base import GuardrailContext, GuardrailToolResult, ToolResult


class InMemoryRateLimiter:
    """In-memory sliding-window rate limiter."""

    def __init__(self, requests_per_minute: int = 60) -> None:
        self.requests_per_minute = requests_per_minute
        self._counts: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def check(self, key: str) -> bool:
        """Return True if under limit, False if over."""
        now = time.monotonic()
        window_start = now - 60.0  # 1 minute window
        with self._lock:
            timestamps = self._counts[key]
            timestamps[:] = [t for t in timestamps if t > window_start]
            if len(timestamps) >= self.requests_per_minute:
                return False
            timestamps.append(now)
            return True


_limiters: dict[int, InMemoryRateLimiter] = {}


def rate_limit_tool(ctx: GuardrailContext) -> GuardrailToolResult:
    """Enforce rate limit for the caller.

    Uses identity or IP as key. BLOCK if over limit.
    """
    config = ctx.config
    limit = getattr(config, "guardrail_rate_limit_per_minute", 60) if config else 60
    limiter_id = id(config) if config else 0
    if limiter_id not in _limiters:
        _limiters[limiter_id] = InMemoryRateLimiter(limit)
    rl = _limiters[limiter_id]

    key = ctx.request.identity or ctx.request.ip_address or "anonymous"
    if not rl.check(key):
        return GuardrailToolResult(
            tool_name="rate_limit",
            result=ToolResult.BLOCK,
            message="Rate limit exceeded",
        )
    return GuardrailToolResult(
        tool_name="rate_limit",
        result=ToolResult.ALLOW,
    )
