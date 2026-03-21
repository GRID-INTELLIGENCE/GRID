"""Hugging Face embedding provider using sentence-transformers."""

from typing import cast

import numpy as np

from .base import BaseEmbeddingProvider


class HuggingFaceEmbeddingProvider(BaseEmbeddingProvider):
    """Hugging Face embedding provider using sentence-transformers library.

    This provider runs locally using the sentence-transformers package.
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-en-v1.5",
        device: str = "cpu",
        allow_download: bool = False,
    ):
        """Initialize Hugging Face provider.

        Args:
            model_name: Hugging Face model identifier
            device: Device to run on ('cpu', 'cuda', etc.)
            allow_download: If False, block outbound HuggingFace Hub model downloads (local-first policy)
        """
        import logging
        import os

        logger = logging.getLogger(__name__)

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. Please install with: uv add sentence-transformers"
            ) from None

        self.model_name = model_name
        self.device = device

        # Enforce local-first egress policy: block HuggingFace Hub downloads unless explicitly allowed
        prev_offline = os.environ.get("HF_HUB_OFFLINE")
        if not allow_download:
            os.environ["HF_HUB_OFFLINE"] = "1"
            logger.info("HuggingFace egress blocked (HF_HUB_OFFLINE=1) — using cached models only")

        try:
            self._model = SentenceTransformer(model_name, device=device)
        except OSError as e:
            raise RuntimeError(
                f"HuggingFace embedding model '{model_name}' not found in local cache and downloads "
                f"are disabled (RAG_RERANKER_ALLOW_DOWNLOAD=false). Either pre-download the model or "
                f"set RAG_RERANKER_ALLOW_DOWNLOAD=true to allow HuggingFace Hub egress. "
                f"Original error: {e}"
            ) from e
        finally:
            if prev_offline is None:
                os.environ.pop("HF_HUB_OFFLINE", None)
            else:
                os.environ["HF_HUB_OFFLINE"] = prev_offline

        self._dimension = self._model.get_sentence_embedding_dimension()

    def embed(self, text: str) -> list[float] | np.ndarray:
        """Generate embedding for text.

        Args:
            text: Input text to embed

        Returns:
            Dense embedding vector
        """
        return cast(list[float] | np.ndarray, self._model.encode(text, convert_to_numpy=True))

    def embed_batch(self, texts: list[str]) -> list[list[float] | np.ndarray]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of input texts

        Returns:
            List of dense embedding vectors
        """
        return cast(list[list[float] | np.ndarray], self._model.encode(texts, convert_to_numpy=True))

    async def async_embed(self, text: str) -> list[float] | np.ndarray:
        """Generate embedding for text (async)."""
        import asyncio

        return await asyncio.to_thread(self.embed, text)

    async def async_embed_batch(self, texts: list[str]) -> list[list[float] | np.ndarray]:
        """Generate embeddings for multiple texts (async)."""
        import asyncio

        return await asyncio.to_thread(self.embed_batch, texts)

    @property
    def dimension(self) -> int:
        """Return the dimension of embeddings produced by this provider."""
        return cast(int, self._dimension)
