"""Cross-encoder reranker using sentence-transformers.

More accurate and faster than LLM-based reranking.
"""

import logging
from typing import Optional

from .reranker import BaseReranker

logger = logging.getLogger(__name__)

# Cross-encoder is optional
try:
    from sentence_transformers import CrossEncoder

    HAS_CROSS_ENCODER = True
except ImportError:
    HAS_CROSS_ENCODER = False
    CrossEncoder = None  # type: ignore


class CrossEncoderReranker(BaseReranker):
    """Reranker using sentence-transformers cross-encoder.

    Uses ms-marco-MiniLM-L6-v2 by default - fast and accurate.
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L6-v2",
        max_candidates: int = 20,
        device: str | None = None,
    ):
        if not HAS_CROSS_ENCODER:
            raise ImportError(
                "sentence-transformers required for CrossEncoderReranker. Install with: uv add sentence-transformers"
            )

        self.model = CrossEncoder(model_name, device=device)
        self.max_candidates = max_candidates
        self.model_name = model_name

    def rerank(self, query: str, documents: list[str], top_k: int = 5) -> list[tuple[int, float]]:
        """Rerank documents using cross-encoder scoring."""
        if not documents:
            return []

        # Limit candidates for efficiency
        candidates = documents[: self.max_candidates]

        # Create query-document pairs
        pairs = [[query, doc] for doc in candidates]

        # Score all pairs at once (efficient batch processing)
        scores = self.model.predict(pairs)

        # Create indexed scores and sort by descending score
        indexed_scores = [(i, float(score)) for i, score in enumerate(scores)]
        return sorted(indexed_scores, key=lambda x: x[1], reverse=True)[:top_k]

    async def async_rerank(self, query: str, documents: list[str], top_k: int = 5) -> list[tuple[int, float]]:
        """Async wrapper - cross-encoder is CPU-bound, so we run in executor."""
        import asyncio

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.rerank, query, documents, top_k)


def create_cross_encoder_reranker(
    config=None,
) -> Optional["CrossEncoderReranker"]:
    """Factory function for cross-encoder reranker."""
    if not HAS_CROSS_ENCODER:
        logger.warning("Cross-encoder reranker requested but sentence-transformers not installed.")
        return None

    model_name = "cross-encoder/ms-marco-MiniLM-L6-v2"
    max_candidates = 20

    if config:
        max_candidates = getattr(config, "reranker_top_k", 20)
        # Check for model in environment or config
        model_overide = getattr(config, "cross_encoder_model", None)
        if model_overide:
            model_name = model_overide

    return CrossEncoderReranker(
        model_name=model_name,
        max_candidates=max_candidates,
    )
