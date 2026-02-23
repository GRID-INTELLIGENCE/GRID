import asyncio
import json
import logging
import math
import re
import subprocess

from grid.services.embeddings.embedding_client import OllamaEmbeddingClient

logger = logging.getLogger(__name__)

from .types import EmbeddingProvider, EmbeddingProviderError


class OllamaEmbedding(EmbeddingProvider):
    """Wrapper for Ollama's embedding models."""

    def __init__(self, model: str = "nomic-embed-text"):
        self.model = model
        self._native_client = None

    def _get_native_client(self):
        if self._native_client is None:
            self._native_client = OllamaEmbeddingClient()
        return self._native_client

    def embed(self, text: str) -> dict[str, float]:
        """Get embeddings using Ollama (sync version)."""
        try:
            result = subprocess.run(  # noqa: S603 subprocess call is intentional
                ["ollama", "run", self.model, text],
                capture_output=True,
                text=True,
                check=True,
                timeout=30,  # noqa: S607 partial path is intentional
            )
            # Parse dense vector from output
            vector = json.loads(result.stdout)
            # Convert to sparse dict (keep only significant values)
            return {str(i): v for i, v in enumerate(vector) if abs(v) > 0.01}
        except Exception as e:
            logger.error(f"Ollama embedding failed: {e}")
            raise EmbeddingProviderError(f"Failed to generate embedding using Ollama model {self.model}: {e}") from e

    async def _async_subprocess_embed(self, text: str) -> dict[str, float]:
        """Get embeddings using Ollama via async subprocess."""
        try:
            # Safe: asyncio.create_subprocess_exec (no dynamic code; argv from code)
            proc = await asyncio.create_subprocess_exec(
                "ollama",
                "run",
                self.model,
                text,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            async with asyncio.timeout(30):
                stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                raise RuntimeError(f"Ollama failed: {stderr.decode()}")

            # Parse dense vector from output
            vector = json.loads(stdout.decode())
            # Convert to sparse dict (keep only significant values)
            return {str(i): v for i, v in enumerate(vector) if abs(v) > 0.01}
        except TimeoutError:
            raise RuntimeError("Ollama embedding timed out after 30s") from None

    async def async_embed(self, text: str) -> dict[str, float]:
        """Get embeddings using Ollama (native async)."""
        try:
            client = self._get_native_client()
            resp = await client.embed([text], model=self.model)
            if not resp.embeddings:
                raise EmbeddingProviderError("Ollama returned empty embeddings")
            vector = resp.embeddings[0]
            # Convert to sparse dict (keep only significant values)
            return {str(i): v for i, v in enumerate(vector) if abs(v) > 0.01}
        except EmbeddingProviderError:
            raise
        except Exception as e:
            logger.debug(f"Ollama Native embedding error: {e}, trying async subprocess...")
            try:
                return await self._async_subprocess_embed(text)
            except Exception as e2:
                logger.error(f"Ollama async subprocess also failed: {e2}")
                raise EmbeddingProviderError(
                    f"Failed to generate embedding using Ollama model {self.model}: {e2}"
                ) from e2

    def embed_batch(self, texts: list[str]) -> list[dict[str, float]]:
        """Get embeddings for multiple texts (sync fallback to individual)."""
        return [self.embed(t) for t in texts]

    async def async_embed_batch(self, texts: list[str]) -> list[dict[str, float]]:
        """Get embeddings for multiple texts (native async batch)."""
        try:
            client = self._get_native_client()
            resp = await client.embed(texts, model=self.model)

            results = [{str(i): v for i, v in enumerate(vector) if abs(v) > 0.01} for vector in resp.embeddings]
            return results
        except Exception as e:
            logger.error(f"Ollama batch embedding failed: {e}")
            raise EmbeddingProviderError(
                f"Failed to generate batch embeddings using Ollama model {self.model}: {e}"
            ) from e


class SimpleEmbedding(EmbeddingProvider):
    """Simple word frequency and TF-IDF based embedding."""

    def __init__(self, use_tfidf: bool = True):
        self.use_tfidf = use_tfidf
        self.doc_freqs = {}  # For TF-IDF
        self.num_docs = 0

    def embed(self, text: str) -> dict[str, float]:
        """Generate simple word-based embedding."""
        # Preprocess text
        words = self._tokenize(text.lower())

        if not words:
            return {}

        # Count word frequencies
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1

        if not self.use_tfidf:
            # Simple frequency
            return word_counts

        # TF-IDF scoring
        if self.num_docs == 0:
            # Initialize with some reasonable IDF values
            # Common words have lower scores
            common_words = {
                "the",
                "a",
                "an",
                "and",
                "or",
                "but",
                "in",
                "on",
                "at",
                "to",
                "for",
                "of",
                "with",
                "by",
                "is",
                "are",
                "was",
                "were",
                "be",
                "been",
                "have",
                "has",
                "had",
                "do",
                "does",
                "did",
                "will",
                "would",
                "could",
                "should",
            }
            self.doc_freqs = dict.fromkeys(common_words, 100)
            self.num_docs = 1000

        # Calculate TF-IDF
        tfidf_scores = {}
        for word, count in word_counts.items():
            tf = count / len(words)  # Term frequency
            idf = math.log(self.num_docs / (self.doc_freqs.get(word, 1) + 1))  # Inverse doc frequency
            tfidf_scores[word] = tf * idf

        return tfidf_scores

    def _tokenize(self, text: str) -> list[str]:
        """Simple tokenization."""
        # Split on non-word characters
        tokens = re.findall(r"\b\w+\b", text)
        # Filter out very short tokens
        return [t for t in tokens if len(t) > 2]

    def embed_batch(self, texts: list[str]) -> list[dict[str, float]]:
        """Get embeddings for multiple texts."""
        return [self.embed(t) for t in texts]

    async def async_embed(self, text: str) -> dict[str, float]:
        """Async version of embed."""
        return self.embed(text)

    async def async_embed_batch(self, texts: list[str]) -> list[dict[str, float]]:
        """Async version of embed_batch."""
        return self.embed_batch(texts)

    def update_doc_freqs(self, docs: list[str]) -> None:
        """Update document frequencies for better TF-IDF."""
        self.doc_freqs = {}
        self.num_docs = len(docs)

        for doc in docs:
            words = set(self._tokenize(doc.lower()))
            for word in words:
                self.doc_freqs[word] = self.doc_freqs.get(word, 0) + 1


class OpenAIEmbedding(EmbeddingProvider):
    """Wrapper for OpenAI's embedding API."""

    def __init__(self, model: str = "text-embedding-ada-002", api_key: str | None = None):
        self.model = model
        self.api_key = api_key

    def embed(self, text: str) -> dict[str, float]:
        """Get embeddings using OpenAI API."""
        try:
            from openai import OpenAI  # type: ignore[import-untyped]
        except ImportError as e:
            raise EmbeddingProviderError("OpenAI library not installed. Install with: uv add openai") from e

        if not self.api_key:
            raise EmbeddingProviderError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable.")

        try:
            client = OpenAI(api_key=self.api_key)
            response = client.embeddings.create(model=self.model, input=text)
            vector = response.data[0].embedding
            # Convert to sparse dict
            return {str(i): v for i, v in enumerate(vector) if abs(v) > 0.01}
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            raise EmbeddingProviderError(f"Failed to generate embedding using OpenAI model {self.model}: {e}") from e

    def embed_batch(self, texts: list[str]) -> list[dict[str, float]]:
        """Get embeddings for multiple texts."""
        return [self.embed(t) for t in texts]

    async def async_embed(self, text: str) -> dict[str, float]:
        """Async version of embed."""
        return self.embed(text)

    async def async_embed_batch(self, texts: list[str]) -> list[dict[str, float]]:
        """Async version of embed_batch."""
        return self.embed_batch(texts)


class HuggingFaceEmbedding(EmbeddingProvider):
    """Wrapper for Hugging Face sentence transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self._load_model()

    def _load_model(self) -> None:
        """Load the Hugging Face model."""
        try:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(self.model_name)
        except ImportError:
            logger.warning("sentence_transformers not installed. Use: pip install sentence-transformers")
            self.model = None
        except Exception as e:
            logger.warning(f"Failed to load Hugging Face model: {e}")
            self.model = None

    def embed(self, text: str) -> dict[str, float]:
        """Get embeddings using Hugging Face model."""
        if self.model is None:
            raise EmbeddingProviderError(
                f"HuggingFace model '{self.model_name}' failed to load. "
                "Ensure sentence-transformers is installed: uv add sentence-transformers"
            )

        try:
            vector = self.model.encode(text).tolist()
            # Convert to sparse dict
            return {str(i): v for i, v in enumerate(vector) if abs(v) > 0.01}
        except Exception as e:
            logger.error(f"Hugging Face embedding failed: {e}")
            raise EmbeddingProviderError(
                f"Failed to generate embedding using HuggingFace model {self.model_name}: {e}"
            ) from e

    def embed_batch(self, texts: list[str]) -> list[dict[str, float]]:
        """Get embeddings for multiple texts."""
        return [self.embed(t) for t in texts]

    async def async_embed(self, text: str) -> dict[str, float]:
        """Async version of embed."""
        return self.embed(text)

    async def async_embed_batch(self, texts: list[str]) -> list[dict[str, float]]:
        """Async version of embed_batch."""
        return self.embed_batch(texts)


def get_embedding_provider(provider_type: str = "simple", **kwargs) -> EmbeddingProvider:
    """Get an embedding provider by type.

    Args:
        provider_type: Type of provider ("simple", "ollama", "openai", "huggingface")
        **kwargs: Additional arguments for the provider

    Returns:
        EmbeddingProvider instance
    """
    providers = {
        "simple": SimpleEmbedding,
        "ollama": OllamaEmbedding,
        "openai": OpenAIEmbedding,
        "huggingface": HuggingFaceEmbedding,
    }

    if provider_type not in providers:
        raise ValueError(f"Unknown provider type: {provider_type}")

    return providers[provider_type](**kwargs)
