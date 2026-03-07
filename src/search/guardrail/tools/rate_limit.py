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


_default_limiter = InMemoryRateLimiter()


def rate_limit_tool(ctx: GuardrailContext) -> GuardrailToolResult:
    """Enforce rate limit for the caller.

    Uses identity or IP as key. BLOCK if over limit.
    """
    config = ctx.config
    limit = getattr(config, "guardrail_rate_limit_per_minute", 60) if config else 60
    rl = None
    if config is not None:
        rl = getattr(config, "_search_rate_limiter", None)
        if not isinstance(rl, InMemoryRateLimiter) or rl.requests_per_minute != limit:
            rl = InMemoryRateLimiter(limit)
            object.__setattr__(config, "_search_rate_limiter", rl)
    else:
        global _default_limiter
        if _default_limiter.requests_per_minute != limit:
            _default_limiter = InMemoryRateLimiter(limit)
        rl = _default_limiter

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
