"""Integration tests for SearchEngine end-to-end pipeline."""

import pytest

from search.engine import SearchEngine
from search.models import FieldSchema, FieldType, IndexSchema


class TestIndexManagement:
    def test_create_index(self, search_engine, product_schema):
        search_engine.create_index(product_schema)
        assert "products" in search_engine.list_indices()

    def test_duplicate_index_raises(self, search_engine, product_schema):
        search_engine.create_index(product_schema)
        with pytest.raises(ValueError, match="already exists"):
            search_engine.create_index(product_schema)

    def test_delete_index(self, indexed_engine):
        indexed_engine.delete_index("products")
        assert "products" not in indexed_engine.list_indices()

    def test_delete_nonexistent_raises(self, search_engine):
        with pytest.raises(KeyError):
            search_engine.delete_index("nope")

    def test_index_stats(self, indexed_engine):
        stats = indexed_engine.get_index_stats("products")
        assert stats["doc_count"] == 5
        assert stats["field_count"] == 5
        assert "title" in stats["fields"]


class TestSearch:
    def test_basic_search(self, indexed_engine):
        response = indexed_engine.search("products", "headphones")
        assert response.total > 0
        assert len(response.hits) > 0
        assert response.took_ms > 0

    def test_search_returns_documents(self, indexed_engine):
        response = indexed_engine.search("products", "keyboard")
        for hit in response.hits:
            assert hit.document.id
            assert hit.score >= 0

    def test_search_with_filter(self, indexed_engine):
        response = indexed_engine.search("products", "category:electronics")
        assert response.total > 0
        for hit in response.hits:
            assert hit.document.fields["category"] == "electronics"

    def test_search_with_facets(self, indexed_engine):
        indexed_engine.config.search_full_pipeline = True
        response = indexed_engine.search("products", "cable", facet_fields=["category"])
        assert "category" in response.facets

    def test_pagination(self, indexed_engine):
        page1 = indexed_engine.search("products", "the", size=2, page=1)
        page2 = indexed_engine.search("products", "the", size=2, page=2)
        if page1.total > 2:
            p1_ids = {h.document.id for h in page1.hits}
            p2_ids = {h.document.id for h in page2.hits}
            assert p1_ids.isdisjoint(p2_ids)

    def test_search_returns_scores(self, indexed_engine):
        response = indexed_engine.search("products", "headphones wireless")
        assert response.total > 0
        for hit in response.hits:
            assert hit.score >= 0

    def test_search_hits_do_not_mutate_indexed_documents(self, indexed_engine):
        response = indexed_engine.search("products", "headphones")
        assert response.hits

        hit = response.hits[0]
        hit.document.fields["title"] = "mutated title"

        indexed_doc = indexed_engine._indices["products"].documents[hit.document.id]
        assert indexed_doc.fields["title"] != "mutated title"

    def test_search_nonexistent_index_raises(self, search_engine):
        with pytest.raises(KeyError):
            search_engine.search("nope", "query")


class TestIndexDocuments:
    def test_returns_count(self, search_engine, product_schema, sample_documents):
        search_engine.create_index(product_schema)
        count = search_engine.index_documents("products", sample_documents)
        assert count == 5
