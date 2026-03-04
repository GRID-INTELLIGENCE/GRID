"""Tests for search.retrieval.structured, semantic, keyword retrievers."""

from abc import ABC

import pytest

from search.indexing.pipeline import IndexingPipeline
from search.indexing.structured_store import StructuredFieldIndex
from search.models import (
    Document,
    FieldSchema,
    FieldType,
    FilterClause,
    FilterOp,
    IndexSchema,
)
from search.retrieval.base import BaseRetriever
from search.retrieval.keyword import KeywordRetriever
from search.retrieval.semantic import SemanticRetriever
from search.retrieval.structured import StructuredRetriever


@pytest.fixture
def simple_schema():
    return IndexSchema(
        name="test",
        fields={
            "title": FieldSchema(type=FieldType.TEXT, searchable=True),
            "tag": FieldSchema(type=FieldType.KEYWORD, filterable=True),
        },
    )


@pytest.fixture
def indexed_pipeline(simple_schema, embedding_provider, vector_store):
    pipeline = IndexingPipeline(simple_schema, vector_store, embedding_provider)
    docs = [
        Document(id="a", fields={"title": "machine learning basics", "tag": "ml"}),
        Document(id="b", fields={"title": "deep learning neural networks", "tag": "ml"}),
        Document(id="c", fields={"title": "cooking recipes pasta", "tag": "food"}),
    ]
    pipeline.index_batch(docs)
    return pipeline


class TestBaseRetriever:
    def test_is_abstract(self):
        assert issubclass(BaseRetriever, ABC)
        with pytest.raises(TypeError):
            BaseRetriever()


class TestStructuredRetriever:
    def test_returns_matching_ids(self, indexed_pipeline):
        retriever = StructuredRetriever(indexed_pipeline.structured_index)
        results = retriever.retrieve([FilterClause(field="tag", op=FilterOp.EQ, value="ml")])
        ids = {r.doc_id for r in results}
        assert ids == {"a", "b"}

    def test_empty_filters_returns_empty(self, indexed_pipeline):
        retriever = StructuredRetriever(indexed_pipeline.structured_index)
        results = retriever.retrieve([])
        assert results == []


class TestSemanticRetriever:
    def test_returns_candidates(self, indexed_pipeline, embedding_provider, vector_store):
        retriever = SemanticRetriever(vector_store, embedding_provider)
        results = retriever.retrieve("machine learning")
        assert len(results) > 0
        assert all(r.source == "semantic" for r in results)

    def test_empty_query_returns_empty(self, indexed_pipeline, embedding_provider, vector_store):
        retriever = SemanticRetriever(vector_store, embedding_provider)
        results = retriever.retrieve("")
        assert results == []

    def test_allowed_ids_filters(self, indexed_pipeline, embedding_provider, vector_store):
        retriever = SemanticRetriever(vector_store, embedding_provider)
        results = retriever.retrieve("learning", allowed_ids={"a"})
        ids = {r.doc_id for r in results}
        assert ids <= {"a"}


class TestKeywordRetriever:
    def test_returns_scored_candidates(self, indexed_pipeline):
        retriever = KeywordRetriever()
        retriever.update(indexed_pipeline.bm25, indexed_pipeline.bm25_doc_ids)
        results = retriever.retrieve("machine learning")
        assert len(results) > 0
        assert all(r.source == "keyword" for r in results)
        assert all(r.score >= 0 for r in results)

    def test_no_bm25_returns_empty(self):
        retriever = KeywordRetriever()
        results = retriever.retrieve("anything")
        assert results == []

    def test_allowed_ids(self, indexed_pipeline):
        retriever = KeywordRetriever()
        retriever.update(indexed_pipeline.bm25, indexed_pipeline.bm25_doc_ids)
        results = retriever.retrieve("learning", allowed_ids={"b"})
        ids = {r.doc_id for r in results}
        assert ids <= {"b"}

    def test_allowed_ids_applied_before_result_cap(self):
        class _FakeBM25:
            @staticmethod
            def get_scores(tokens):
                return [10.0, 9.0, 8.0, 7.0]

        retriever = KeywordRetriever()
        retriever.update(_FakeBM25(), ["a", "b", "c", "d"])

        results = retriever.retrieve("query", n_results=2, allowed_ids={"d"})
        assert [r.doc_id for r in results] == ["d"]
