"""Unified native embedding client interface and implementations."""

from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, cast

logger = logging.getLogger(__name__)


class EmbeddingProvider(StrEnum):
    OLLAMA = "ollama"
    OPENAI = "openai"


@dataclass
class EmbeddingResponse:
    embeddings: list[list[float]]
    model: str
    latency_ms: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class EmbeddingClient(ABC):
    """Abstract base class for native async embedding clients."""

    @abstractmethod
    async def embed(self, texts: list[str], model: str | None = None) -> EmbeddingResponse:
        """Generate embeddings for a list of texts."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the service is available."""
        pass


class OllamaEmbeddingClient(EmbeddingClient):
    """Native Ollama embedding client using the ollama-python library."""

    def __init__(self, host: str = "http://localhost:11434"):
        import ollama

        self._client = ollama.AsyncClient(host=host)
        self._default_model = "nomic-embed-text"
        self._semaphore = asyncio.Semaphore(10)

    async def embed(self, texts: list[str], model: str | None = None) -> EmbeddingResponse:
        target_model = model or self._default_model
        start_time = time.time()

        async with self._semaphore:
            try:
                # Use embed() for sequence support
                response = await self._client.embed(model=target_model, input=texts)

                latency_ms = int((time.time() - start_time) * 1000)

                # Ollama's embed() returns 'embeddings' for list input
                embeddings = response.get("embeddings", [])

                return EmbeddingResponse(
                    embeddings=embeddings,
                    model=target_model,
                    latency_ms=latency_ms,
                    metadata=cast(dict[str, Any], response),
                )
            except Exception as e:
                logger.error(f"Ollama embedding failed: {e}")
                raise

    async def health_check(self) -> bool:
        try:
            await self._client.list()
            return True
        except Exception:
            return False
