import asyncio
import logging
import re
from abc import ABC, abstractmethod

import httpx

logger = logging.getLogger(__name__)


class BaseReranker(ABC):
    """Base class for rerankers."""

    @abstractmethod
    def rerank(self, query: str, documents: list[str], top_k: int = 5) -> list[tuple[int, float]]:
        """Rerank documents by relevance to query."""
        pass

    @abstractmethod
    async def async_rerank(self, query: str, documents: list[str], top_k: int = 5) -> list[tuple[int, float]]:
        """Rerank documents asynchronously."""
        pass


class OllamaReranker(BaseReranker):
    """Uses Ollama LLM to score query-document relevance with connection pooling."""

    MAX_CANDIDATES = 20
    TIMEOUT = 10.0

    def __init__(
        self,
        model: str = "mistral-nemo:latest",
        base_url: str = "http://localhost:11434",
        max_candidates: int | None = None,
    ):
        self.model = model
        self.base_url = base_url
        self.max_candidates = max_candidates or self.MAX_CANDIDATES
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create shared async client for connection pooling."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.TIMEOUT,
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            )
        return self._client

    async def _async_score_document(self, client: httpx.AsyncClient, query: str, document: str) -> float:
        """Score a single document asynchronously."""
        try:
            doc_text = document[:500] if len(document) > 500 else document
            prompt = (
                f"Rate 0-10 how relevant this document is to the query. "
                f"Output ONLY a number.\n\n"
                f"Query: {query}\n\n"
                f"Document: {doc_text}\n\n"
                f"Score:"
            )

            resp = await client.post(
                "/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.0},
                },
            )

            if resp.status_code == 200:
                response_text = resp.model_dump_json().get("response", "0").strip()
                match = re.search(r"\d+(?:\.\d+)?", response_text)
                if match:
                    return min(max(float(match.group()), 0), 10)
            return 0.0
        except Exception as e:
            logger.debug(f"Rerank score error: {e}")
            return 0.0

    async def async_rerank(self, query: str, documents: list[str], top_k: int = 5) -> list[tuple[int, float]]:
        """Rerank documents in parallel using the shared client."""
        candidates = documents[: self.max_candidates]
        if not candidates:
            return []

        client = self._get_client()
        tasks = [self._async_score_document(client, query, doc) for doc in candidates]

        # Run all scoring tasks in parallel
        scores = await asyncio.gather(*tasks)

        indexed_scores = [(i, float(score)) for i, score in enumerate(scores)]
        return sorted(indexed_scores, key=lambda x: x[1], reverse=True)[:top_k]

    def rerank(self, query: str, documents: list[str], top_k: int = 5) -> list[tuple[int, float]]:
        """Synchronous wrapper for async_rerank."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # This is tricky if already in an event loop
                import nest_asyncio

                nest_asyncio.apply()
            return loop.run_until_complete(self.async_rerank(query, documents, top_k))
        except Exception:
            return asyncio.run(self.async_rerank(query, documents, top_k))

    async def close(self):
        """Close the underlying HTTP client."""
        if self._client:
            await self._client.aclose()


class NoOpReranker(BaseReranker):
    """Passthrough reranker."""

    async def async_rerank(self, query: str, documents: list[str], top_k: int = 5) -> list[tuple[int, float]]:
        return [(i, 1.0 / (i + 1)) for i in range(min(len(documents), top_k))]

    def rerank(self, query: str, documents: list[str], top_k: int = 5) -> list[tuple[int, float]]:
        return [(i, 1.0 / (i + 1)) for i in range(min(len(documents), top_k))]


def create_reranker(config=None) -> BaseReranker | None:
    """Factory function."""
    if config is None:
        from .config import RAGConfig

        config = RAGConfig.from_env()

    if not config.use_reranker:
        return None

    return OllamaReranker(
        model=config.llm_model_local, base_url=config.ollama_base_url, max_candidates=config.reranker_top_k
    )
