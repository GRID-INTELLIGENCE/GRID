"""Unified native LLM client interface and implementations."""

from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, cast

logger = logging.getLogger(__name__)


class LLMProvider(StrEnum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MISTRAL = "mistral"


@dataclass
class LLMMessage:
    role: str
    content: str


@dataclass
class LLMResponse:
    content: str
    finish_reason: str
    model: str
    tokens_used: int = 0
    latency_ms: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMConfig:
    provider: LLMProvider = LLMProvider.OLLAMA
    model: str = "mistral-nemo:latest"
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout_ms: int = 60000
    stop: list[str] | None = None


class LLMClient(ABC):
    """Abstract base class for native async LLM clients."""

    @abstractmethod
    async def generate(self, prompt: str, config: LLMConfig | None = None) -> LLMResponse:
        """Generate a completion for a prompt."""
        pass

    @abstractmethod
    async def chat(self, messages: list[LLMMessage], config: LLMConfig | None = None) -> LLMResponse:
        """Generate a chat response for a list of messages."""
        pass

    @abstractmethod
    def stream(self, prompt: str, config: LLMConfig | None = None) -> AsyncIterator[str]:
        """Stream completion chunks for a prompt."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the service is available."""
        pass


class OllamaNativeClient(LLMClient):
    """Native Ollama client using the ollama-python library."""

    def __init__(self, host: str = "http://localhost:11434"):
        import ollama

        self._client = ollama.AsyncClient(host=host)
        self._semaphore = asyncio.Semaphore(10)  # Limit concurrent requests

    async def generate(self, prompt: str, config: LLMConfig | None = None) -> LLMResponse:
        cfg = config or LLMConfig()
        start_time = time.time()

        async with self._semaphore:
            try:
                response = await self._client.generate(
                    model=cfg.model,
                    prompt=prompt,
                    options={"temperature": cfg.temperature, "num_predict": cfg.max_tokens, "stop": cfg.stop},
                )

                latency_ms = int((time.time() - start_time) * 1000)

                return LLMResponse(
                    content=response.get("response", ""),
                    finish_reason="stop",
                    model=cfg.model,
                    tokens_used=response.get("eval_count", 0),
                    latency_ms=latency_ms,
                    metadata=cast(dict[str, Any], response),
                )
            except Exception as e:
                logger.error(f"Ollama generate failed: {e}")
                raise

    async def chat(self, messages: list[LLMMessage], config: LLMConfig | None = None) -> LLMResponse:
        cfg = config or LLMConfig()
        start_time = time.time()

        formatted_messages = [{"role": m.role, "content": m.content} for m in messages]

        async with self._semaphore:
            try:
                response = await self._client.chat(
                    model=cfg.model,
                    messages=formatted_messages,
                    options={"temperature": cfg.temperature, "num_predict": cfg.max_tokens, "stop": cfg.stop},
                )

                latency_ms = int((time.time() - start_time) * 1000)

                return LLMResponse(
                    content=response.get("message", {}).get("content", ""),
                    finish_reason="stop",
                    model=cfg.model,
                    tokens_used=response.get("eval_count", 0),
                    latency_ms=latency_ms,
                    metadata=cast(dict[str, Any], response),
                )
            except Exception as e:
                logger.error(f"Ollama chat failed: {e}")
                raise

    async def stream(self, prompt: str, config: LLMConfig | None = None) -> AsyncIterator[str]:
        cfg = config or LLMConfig()

        async with self._semaphore:
            async for chunk in await self._client.generate(
                model=cfg.model,
                prompt=prompt,
                stream=True,
                options={"temperature": cfg.temperature, "num_predict": cfg.max_tokens, "stop": cfg.stop},
            ):
                yield chunk.get("response", "")

    async def health_check(self) -> bool:
        try:
            await self._client.list()
            return True
        except Exception:
            return False


class MistralNativeClient(LLMClient):
    """Native Mistral AI client using the mistralai SDK."""

    def __init__(self, api_key: str | None = None, server_url: str | None = None):
        self._api_key = api_key
        self._server_url = server_url
        self._client = None
        self._semaphore = asyncio.Semaphore(10)

    def _get_client(self):
        if self._client is None:
            from mistralai import Mistral

            kwargs: dict = {"async_client": True}
            if self._api_key:
                kwargs["api_key"] = self._api_key
            if self._server_url:
                kwargs["server_url"] = self._server_url
            self._client = Mistral(**kwargs)
        return self._client

    async def generate(self, prompt: str, config: LLMConfig | None = None) -> LLMResponse:
        cfg = config or LLMConfig()
        client = self._get_client()
        start_time = time.time()

        async with self._semaphore:
            try:
                response = await client.chat.complete_async(
                    model=cfg.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=cfg.temperature,
                    max_tokens=cfg.max_tokens,
                )
                latency_ms = int((time.time() - start_time) * 1000)
                return LLMResponse(
                    content=response.choices[0].message.content or "",
                    finish_reason="stop",
                    model=cfg.model,
                    tokens_used=0,
                    latency_ms=latency_ms,
                )
            except Exception as e:
                logger.error(f"Mistral generate failed: {e}")
                raise

    async def chat(self, messages: list[LLMMessage], config: LLMConfig | None = None) -> LLMResponse:
        cfg = config or LLMConfig()
        client = self._get_client()
        start_time = time.time()

        formatted_messages = [{"role": m.role, "content": m.content} for m in messages]

        async with self._semaphore:
            try:
                response = await client.chat.complete_async(
                    model=cfg.model,
                    messages=formatted_messages,
                    temperature=cfg.temperature,
                    max_tokens=cfg.max_tokens,
                )
                latency_ms = int((time.time() - start_time) * 1000)
                return LLMResponse(
                    content=response.choices[0].message.content or "",
                    finish_reason="stop",
                    model=cfg.model,
                    tokens_used=0,
                    latency_ms=latency_ms,
                )
            except Exception as e:
                logger.error(f"Mistral chat failed: {e}")
                raise

    async def stream(self, prompt: str, config: LLMConfig | None = None) -> AsyncIterator[str]:
        cfg = config or LLMConfig()
        client = self._get_client()

        async with self._semaphore:
            try:
                stream = await client.chat.stream_async(
                    model=cfg.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=cfg.temperature,
                    max_tokens=cfg.max_tokens,
                )
                async for chunk in stream:
                    if chunk.data.choices[0].delta.content:
                        yield chunk.data.choices[0].delta.content
            except Exception as e:
                logger.error(f"Mistral stream failed: {e}")
                raise

    async def health_check(self) -> bool:
        try:
            client = self._get_client()
            await client.list_models()
            return True
        except Exception:
            return False
