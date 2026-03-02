"""Tests for search.indexing.pipeline."""

import pytest

from search.config import SearchConfig
from search.indexing.pipeline import IndexingPipeline
from search.models import Document, FieldSchema, FieldType, IndexSchema
from tools.rag.embeddings.test_provider import DeterministicEmbeddingProvider
from tools.rag.vector_store.in_memory_dense import InMemoryDenseStore


@pytest.fixture
def schema():
    return IndexSchema(
        name="test",
        fields={
            "title": FieldSchema(type=FieldType.TEXT, searchable=True, weight=2.0),
            "body": FieldSchema(type=FieldType.TEXT, searchable=True),
            "score": FieldSchema(type=FieldType.INTEGER, filterable=True),
        },
    )


@pytest.fixture
def pipeline(schema, embedding_provider, vector_store):
    return IndexingPipeline(schema, vector_store, embedding_provider)


class TestBuildSearchText:
    def test_weighted_repetition(self, pipeline):
        doc = Document(id="d1", fields={"title": "hello", "body": "world", "score": 5})
        text = pipeline.build_search_text(doc)
        assert text == "hello hello world"

    def test_missing_field_skipped(self, pipeline):
        doc = Document(id="d1", fields={"title": "hello"})
        text = pipeline.build_search_text(doc)
        assert text == "hello hello"


class TestIndexBatch:
    def test_returns_count(self, pipeline):
        docs = [
            Document(id="d1", fields={"title": "alpha", "body": "first", "score": 1}),
            Document(id="d2", fields={"title": "beta", "body": "second", "score": 2}),
        ]
        count = pipeline.index_batch(docs)
        assert count == 2

    def test_populates_structured_index(self, pipeline):
        docs = [Document(id="d1", fields={"title": "x", "body": "y", "score": 10})]
        pipeline.index_batch(docs)
        assert pipeline.structured_index.doc_count() == 1

    def test_builds_bm25(self, pipeline):
        docs = [Document(id="d1", fields={"title": "word", "body": "text", "score": 1})]
        pipeline.index_batch(docs)
        assert pipeline.bm25 is not None
        assert pipeline.bm25_doc_ids == ["d1"]

    def test_empty_searchable_text_skipped(self, pipeline):
        doc = Document(id="d1", fields={"score": 5})
        count = pipeline.index_batch([doc])
        assert count == 0


class TestValidation:
    def test_coerces_integer(self, pipeline):
        doc = Document(id="d1", fields={"title": "t", "body": "b", "score": "42"})
        pipeline.index_batch([doc])
        assert doc.fields["score"] == 42

    def test_rejects_invalid_integer(self, pipeline):
        doc = Document(id="d1", fields={"title": "t", "body": "b", "score": "not_a_number"})
        with pytest.raises(ValueError, match="expects integer"):
            pipeline.index_batch([doc])


class TestRemove:
    def test_remove_cleans_all_stores(self, pipeline):
        docs = [Document(id="d1", fields={"title": "x", "body": "y", "score": 1})]
        pipeline.index_batch(docs)
        assert pipeline.doc_count() == 1
        pipeline.remove("d1")
        assert pipeline.doc_count() == 0
        assert pipeline.bm25_doc_ids == []
