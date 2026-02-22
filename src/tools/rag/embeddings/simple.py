"""Simple fallback embedding provider."""

import math
import re

import numpy as np

from .base import BaseEmbeddingProvider


class SimpleEmbedding(BaseEmbeddingProvider):
    """Simple word frequency-based embedding (fallback only).

    This is a basic fallback that should not be used for production.
    Use nomic-embed-text-v2 instead.
    """

    def __init__(self, use_tfidf: bool = True, embedding_dim: int = 100):
        """Initialize simple embedding provider.

        Args:
            use_tfidf: Whether to use TF-IDF weighting
            embedding_dim: Dimension of embeddings (default 100)
        """
        self.use_tfidf = use_tfidf
        self.embedding_dim = embedding_dim
        self.doc_freqs: dict[str, int] = {}
        self.num_docs = 0

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into words.

        Args:
            text: Input text (should be lowercase)

        Returns:
            List of word tokens
        """
        # Simple word tokenization - split on non-alphanumeric characters
        words = re.findall(r"\b[a-z]+\b", text)
        # Filter out very short words
        return [w for w in words if len(w) > 1]

    def embed(self, text: str) -> list[float] | np.ndarray:
        """Generate simple word-based embedding.

        Args:
            text: Input text

        Returns:
            Sparse-like embedding as dense vector (limited vocabulary)
        """
        # Tokenize
        words = self._tokenize(text.lower())

        if not words:
            return np.zeros(self.embedding_dim, dtype=float).tolist()

        # Count word frequencies
        word_counts: dict[str, int] = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1

        if not self.use_tfidf:
            # Hash-based frequency vector: same word always maps to same dimension
            vocab_size = self.embedding_dim
            embedding = [0.0] * vocab_size
            for word, count in word_counts.items():
                idx = hash(word) % vocab_size
                embedding[idx] += float(count) / len(words)
            return np.array(embedding, dtype=float)

        # TF-IDF (simplified)
        tfidf_scores: dict[str, float] = {}
        for word, count in word_counts.items():
            tf = count / len(words)
            # Ensure ratio is always > 0 to avoid math.log domain error
            doc_count = max(1, self.num_docs)
            idf = math.log(doc_count / (self.doc_freqs.get(word, 0) + 1) + 1)
            tfidf_scores[word] = tf * idf

        # Hash-based placement: same word always maps to same dimension
        vocab_size = self.embedding_dim
        embedding = [0.0] * vocab_size
        for word, score in tfidf_scores.items():
            idx = hash(word) % vocab_size
            embedding[idx] += score

        return np.array(embedding, dtype=float)

    def embed_batch(self, texts: list[str]) -> list[list[float]] | np.ndarray:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of input texts

        Returns:
            List of dense embedding vectors
        """
        return [self.embed(text) for text in texts]

    def embed_documents(self, texts: list[str]) -> list[list[float]] | np.ndarray:
        """Alias for embed_batch for API compatibility.

        Args:
            texts: List of input texts

        Returns:
            List of dense embedding vectors
        """
        return self.embed_batch(texts)

    async def async_embed(self, text: str) -> list[float]:
        """Generate embedding for text (async).

        Args:
            text: Input text

        Returns:
            Dense embedding vector
        """
        # Simple synchronous implementation wrapped in async
        return self.embed(text)

    @property
    def dimension(self) -> int:
        """Return embedding dimension."""
        return self.embedding_dim


# Backward compatibility alias
SimpleEmbeddings = SimpleEmbedding
