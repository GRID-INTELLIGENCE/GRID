"""
Sandboxed execution environment for model inference.

Enforces:
- No external side-effects (HTTP calls, file writes) by the model.
- Token limits, timeout, max RPS.
- Tool restrictions for untrusted tiers.
"""

from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass, field
from typing import Any

from safety.observability.logging_setup import get_logger

logger = get_logger("model.sandbox")


@dataclass(frozen=True, slots=True)
class SandboxConfig:
    """Configuration for the model sandbox."""

    max_tokens: int = int(os.getenv("SAFETY_MAX_TOKENS", "4096"))
    timeout_seconds: float = float(os.getenv("SAFETY_MODEL_TIMEOUT", "30.0"))
    max_rps: float = float(os.getenv("SAFETY_MODEL_MAX_RPS", "10.0"))
    allow_tools: bool = False  # Default: tools disabled for safety
    allowed_tool_names: tuple[str, ...] = ()


# Per-user RPS tracking
_rps_tracker: dict[str, list[float]] = {}
_rps_lock = asyncio.Lock()


async def _check_rps(user_id: str, max_rps: float) -> bool:
    """Check if the user is within the RPS limit. Returns True if allowed."""
    async with _rps_lock:
        now = time.monotonic()
        window = _rps_tracker.get(user_id, [])
        # Remove entries older than 1 second
        window = [t for t in window if now - t < 1.0]
        if len(window) >= max_rps:
            _rps_tracker[user_id] = window
            return False
        window.append(now)
        _rps_tracker[user_id] = window
        return True


@dataclass
class SandboxResult:
    """Result from a sandboxed model call."""

    text: str
    tokens_used: int
    latency_seconds: float
    truncated: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


async def run_safe_call(
    call_fn,
    *,
    prompt: str,
    user_id: str,
    config: SandboxConfig | None = None,
    **kwargs: Any,
) -> SandboxResult:
    """
    Execute a model call within sandbox constraints.

    Args:
        call_fn: Async callable that takes (prompt, **kwargs) and returns
                 a dict with at least {"text": str, "tokens_used": int}.
        prompt: The input prompt.
        user_id: For RPS tracking.
        config: Sandbox configuration.
        **kwargs: Additional arguments passed to call_fn.

    Raises:
        RuntimeError: If sandbox constraints are violated.
        asyncio.TimeoutError: If the call exceeds the timeout.
    """
    cfg = config or SandboxConfig()

    # 1. RPS check
    if not await _check_rps(user_id, cfg.max_rps):
        raise RuntimeError(f"Model RPS limit exceeded for user {user_id} (max {cfg.max_rps}/s)")

    # 2. Strip tool invocations if tools are not allowed
    if not cfg.allow_tools:
        kwargs.pop("tools", None)
        kwargs.pop("tool_choice", None)
        kwargs.pop("functions", None)
        kwargs.pop("function_call", None)

    # 3. Enforce max_tokens
    kwargs["max_tokens"] = min(kwargs.get("max_tokens", cfg.max_tokens), cfg.max_tokens)

    # 4. Execute with timeout
    start = time.monotonic()
    try:
        result = await asyncio.wait_for(
            call_fn(prompt, **kwargs),
            timeout=cfg.timeout_seconds,
        )
    except TimeoutError:
        elapsed = time.monotonic() - start
        logger.error(
            "sandbox_timeout",
            user_id=user_id,
            timeout=cfg.timeout_seconds,
            elapsed=elapsed,
        )
        raise
    elapsed = time.monotonic() - start

    # 5. Validate response structure
    if not isinstance(result, dict):
        raise RuntimeError(f"Model returned non-dict result: {type(result)}")

    text = result.get("text", "")
    tokens_used = result.get("tokens_used", 0)

    # 6. Truncate if tokens exceeded
    truncated = False
    if tokens_used > cfg.max_tokens:
        # Hard truncation at token limit (approximate by character ratio)
        char_limit = int(len(text) * (cfg.max_tokens / max(tokens_used, 1)))
        text = text[:char_limit]
        truncated = True
        logger.warning(
            "sandbox_output_truncated",
            user_id=user_id,
            tokens_used=tokens_used,
            max_tokens=cfg.max_tokens,
        )

    return SandboxResult(
        text=text,
        tokens_used=tokens_used,
        latency_seconds=elapsed,
        truncated=truncated,
        metadata=result.get("metadata", {}),
    )
