"""Tests for search.retrieval.fusion."""

from unittest.mock import MagicMock

from search.models import QueryIntent, ScoredCandidate, SearchQuery
from search.retrieval.fusion import INTENT_WEIGHTS, HybridFusion


def _make_fusion():
    structured = MagicMock()
    structured.retrieve.return_value = []

    semantic = MagicMock()
    keyword = MagicMock()

    return HybridFusion(structured, semantic, keyword, rrf_k=60), structured, semantic, keyword


class TestRRFFusion:
    def test_merges_keyword_and_semantic(self):
        fusion, _, semantic, keyword = _make_fusion()
        keyword.retrieve.return_value = [
            ScoredCandidate(doc_id="a", score=5.0, source="keyword"),
            ScoredCandidate(doc_id="b", score=3.0, source="keyword"),
        ]
        semantic.retrieve.return_value = [
            ScoredCandidate(doc_id="b", score=0.9, source="semantic"),
            ScoredCandidate(doc_id="c", score=0.8, source="semantic"),
        ]

        query = SearchQuery(text="test")
        results = fusion.fuse(query)
        ids = [r.doc_id for r in results]
        assert "b" in ids
        assert len(results) == 3

    def test_all_candidates_have_fusion_source(self):
        fusion, _, semantic, keyword = _make_fusion()
        keyword.retrieve.return_value = [ScoredCandidate(doc_id="a", score=1.0, source="keyword")]
        semantic.retrieve.return_value = [ScoredCandidate(doc_id="a", score=0.5, source="semantic")]

        results = fusion.fuse(SearchQuery(text="x"))
        assert all(r.source == "fusion" for r in results)

    def test_structured_filter_restricts(self):
        fusion, structured, semantic, keyword = _make_fusion()
        structured.retrieve.return_value = [
            ScoredCandidate(doc_id="a", score=1.0, source="structured"),
        ]

        def sem_with_filter(query_text, n_results=100, allowed_ids=None):
            candidates = [
                ScoredCandidate(doc_id="a", score=0.9, source="semantic"),
                ScoredCandidate(doc_id="b", score=0.8, source="semantic"),
            ]
            if allowed_ids is not None:
                candidates = [c for c in candidates if c.doc_id in allowed_ids]
            return candidates

        semantic.retrieve.side_effect = sem_with_filter
        keyword.retrieve.return_value = []

        from search.models import FilterClause, FilterOp

        query = SearchQuery(text="x", filters=[FilterClause(field="f", op=FilterOp.EQ, value="v")])
        results = fusion.fuse(query)
        ids = {r.doc_id for r in results}
        assert ids <= {"a"}

    def test_empty_structured_result_returns_empty(self):
        fusion, structured, semantic, keyword = _make_fusion()
        structured.retrieve.return_value = []
        from search.models import FilterClause, FilterOp

        query = SearchQuery(text="x", filters=[FilterClause(field="f", op=FilterOp.EQ, value="v")])
        results = fusion.fuse(query)
        assert results == []

    def test_intent_weights_exist(self):
        assert QueryIntent.NAVIGATIONAL in INTENT_WEIGHTS
        assert QueryIntent.EXPLORATORY in INTENT_WEIGHTS
        assert QueryIntent.ANALYTICAL in INTENT_WEIGHTS
