"""
Model client for the safety enforcement pipeline.

Wraps calls to TGI / vLLM / OpenAI-compatible endpoints.
All calls go through the sandbox. Direct calls are prohibited.
Retries with tenacity and exponential backoff.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from safety.model.sandbox import SandboxConfig, SandboxResult, run_safe_call
from safety.observability.logging_setup import get_logger
from safety.observability.metrics import MODEL_CALL_LATENCY

logger = get_logger("model.client")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
_MODEL_API_URL = os.getenv("MODEL_API_URL", "http://localhost:8080/v1/completions")
_MODEL_API_KEY = os.getenv("MODEL_API_KEY", "")
_MODEL_NAME = os.getenv("MODEL_NAME", "default")
_HTTP_TIMEOUT = float(os.getenv("MODEL_HTTP_TIMEOUT", "60.0"))

# Shared HTTP client
_http_client: httpx.AsyncClient | None = None


def _get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if _MODEL_API_KEY:
            headers["Authorization"] = f"Bearer {_MODEL_API_KEY}"
        _http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(_HTTP_TIMEOUT),
            headers=headers,
            limits=httpx.Limits(max_connections=50, max_keepalive_connections=20),
        )
    return _http_client


# ---------------------------------------------------------------------------
# Raw model call (used inside sandbox)
# ---------------------------------------------------------------------------
@retry(
    retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.ConnectError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=10),
    reraise=True,
)
async def _raw_model_call(prompt: str, **kwargs: Any) -> dict[str, Any]:
    """
    Make a raw HTTP call to the model API.

    Returns {"text": str, "tokens_used": int, "metadata": dict}.
    """
    client = _get_http_client()

    payload: dict[str, Any] = {
        "model": kwargs.get("model", _MODEL_NAME),
        "prompt": prompt,
        "max_tokens": kwargs.get("max_tokens", 4096),
        "temperature": kwargs.get("temperature", 0.7),
    }

    # Support chat-completion format
    if kwargs.get("messages"):
        payload.pop("prompt", None)
        payload["messages"] = kwargs["messages"]

    response = await client.post(_MODEL_API_URL, json=payload)
    response.raise_for_status()
    data = response.json()

    # Parse OpenAI-compatible response format
    text = ""
    tokens_used = 0

    if "choices" in data:
        choice = data["choices"][0]
        text = choice.get("text", "") or choice.get("message", {}).get("content", "")
        usage = data.get("usage", {})
        tokens_used = usage.get("total_tokens", 0)
    elif "text" in data:
        text = data["text"]
        tokens_used = data.get("tokens_used", len(text) // 4)

    return {
        "text": text,
        "tokens_used": tokens_used,
        "metadata": {
            "model": data.get("model", _MODEL_NAME),
            "finish_reason": data.get("choices", [{}])[0].get("finish_reason")
            if data.get("choices")
            else None,
        },
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
async def call_model(
    prompt: str,
    user_id: str,
    *,
    sandbox_config: SandboxConfig | None = None,
    **kwargs: Any,
) -> SandboxResult:
    """
    Call the model through the sandbox. This is the ONLY permitted entry point.

    Args:
        prompt: Input text to the model.
        user_id: User identifier for sandbox RPS tracking.
        sandbox_config: Optional sandbox overrides.
        **kwargs: Additional parameters (temperature, max_tokens, etc.).

    Returns:
        SandboxResult with the model output.
    """
    result = await run_safe_call(
        _raw_model_call,
        prompt=prompt,
        user_id=user_id,
        config=sandbox_config,
        **kwargs,
    )
    MODEL_CALL_LATENCY.observe(result.latency_seconds)
    logger.info(
        "model_call_completed",
        user_id=user_id,
        tokens_used=result.tokens_used,
        latency_s=round(result.latency_seconds, 3),
        truncated=result.truncated,
    )
    return result


async def close_client() -> None:
    """Close the HTTP client."""
    global _http_client
    if _http_client:
        await _http_client.aclose()
        _http_client = None
