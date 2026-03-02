"""Indexing pipeline for structured record ingestion."""

from .pipeline import IndexingPipeline
from .structured_store import StructuredFieldIndex

__all__ = ["IndexingPipeline", "StructuredFieldIndex"]
