"""Structured retriever: filters the StructuredFieldIndex by parsed filter clauses."""

from __future__ import annotations

from ..indexing.structured_store import StructuredFieldIndex
from ..models import FilterClause, ScoredCandidate


class StructuredRetriever:
    """Applies structured filters and returns matching doc IDs.

    Unlike the text-based retrievers this does not implement BaseRetriever
    because its interface is filter-driven rather than query-driven.
    It acts as a mandatory pre-filter when filter clauses are present.
    """

    def __init__(self, structured_index: StructuredFieldIndex) -> None:
        self.structured_index = structured_index

    def retrieve(self, filters: list[FilterClause]) -> list[ScoredCandidate]:
        if not filters:
            return []

        matching_ids = self.structured_index.filter(filters)
        return [ScoredCandidate(doc_id=doc_id, score=1.0, source="structured") for doc_id in matching_ids]
