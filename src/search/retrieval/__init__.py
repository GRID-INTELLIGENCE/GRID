"""Retrieval layer: structured, semantic, keyword retrievers and RRF fusion."""

from .base import BaseRetriever
from .fusion import HybridFusion

__all__ = ["BaseRetriever", "HybridFusion"]
