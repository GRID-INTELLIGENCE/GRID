"""OpenAI-compatible LLM provider for RAG.

Calls any OpenAI-compatible chat completions endpoint (e.g. LiteLLM proxy, local server).
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator, Iterator

import httpx

from tools.rag.resilience import (
    create_async_resilient_client,
    get_circuit_breaker,
)

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class OpenAICompatibleLLM(BaseLLMProvider):
    """LLM provider for OpenAI-compatible endpoints (LiteLLM, custom)."""

    def __init__(
        self,
        model: str,
        api_base: str,
        api_key: str | None = None,
        timeout: float = 60.0,
    ):
        """Initialize OpenAI-compatible LLM provider.

        Args:
            model: Model name (as used by the endpoint).
            api_base: Base URL for the API (e.g. https://api.openai.com/v1 or http://localhost:4000).
            api_key: Optional API key (sent as Bearer if set).
            timeout: Request timeout in seconds.
        """
        self.model = model
        self.api_base = api_base.rstrip("/")
        self.api_key = (api_key or "").strip()
        self.timeout = timeout
        self._client: httpx.Client | None = None
        self._breaker = get_circuit_breaker("openai_compatible")

    def _url(self) -> str:
        return f"{self.api_base}/chat/completions"

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _sync_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=self.timeout, headers=self._headers())
        return self._client

    def _async_resilient_client(self):
        """Build a per-request async resilient client (use as ``async with``)."""
        return create_async_resilient_client(
            service="openai_compatible",
            timeout=self.timeout,
            headers=self._headers(),
        )

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate text via POST to .../chat/completions."""
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
            **kwargs,
        }
        with self._breaker:
            resp = self._sync_client().post(self._url(), json=payload)
            resp.raise_for_status()
        data = resp.json()
        choice = data.get("choices", [{}])[0]
        return (choice.get("message", {}).get("content") or "").strip()

    def stream(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> Iterator[str]:
        """Stream text via POST to .../chat/completions with stream=True."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
            **kwargs,
        }
        with self._breaker:
            with self._sync_client().stream("POST", self._url(), json=payload) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if not line or line.strip() == "data: [DONE]":
                        continue
                    if line.startswith("data: "):
                        try:
                            chunk = json.loads(line[6:])
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    async def async_generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate text (async) via POST to .../chat/completions."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
            **kwargs,
        }
        async with self._async_resilient_client() as client:
            resp = await client.post(self._url(), json=payload)
            resp.raise_for_status()
            data = resp.json()
            choice = data.get("choices", [{}])[0]
            return (choice.get("message", {}).get("content") or "").strip()

    async def async_stream(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream text (async) via POST to .../chat/completions with stream=True."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
            **kwargs,
        }
        async with self._async_resilient_client() as client:
            # Streaming needs the raw httpx client for .stream().
            # AsyncRateLimitedClient exposes it via _check_client();
            # plain httpx.AsyncClient (no-apiguard fallback) *is* the client.
            inner = client._check_client() if hasattr(client, "_check_client") else client  # noqa: SLF001
            async with inner.stream("POST", self._url(), json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line or line.strip() == "data: [DONE]":
                        continue
                    if line.startswith("data: "):
                        try:
                            chunk = json.loads(line[6:])
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
