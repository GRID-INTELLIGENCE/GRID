"""Tests for search.models data types."""

import pytest
from pydantic import ValidationError

from search.models import (
    Document,
    FacetResult,
    FacetValue,
    FieldSchema,
    FieldType,
    FilterClause,
    FilterOp,
    IndexSchema,
    QueryIntent,
    ScoredCandidate,
    SearchHit,
    SearchQuery,
    SearchResponse,
)


class TestFieldSchema:
    def test_defaults(self):
        fs = FieldSchema(type=FieldType.TEXT)
        assert fs.searchable is False
        assert fs.filterable is False
        assert fs.facetable is False
        assert fs.weight == 1.0

    def test_weight_must_be_non_negative(self):
        with pytest.raises(ValidationError):
            FieldSchema(type=FieldType.TEXT, weight=-1.0)


class TestIndexSchema:
    def test_searchable_fields(self, product_schema):
        sf = product_schema.searchable_fields()
        assert "title" in sf
        assert "description" in sf
        assert "price" not in sf

    def test_filterable_fields(self, product_schema):
        ff = product_schema.filterable_fields()
        assert "price" in ff
        assert "category" in ff
        assert "title" not in ff

    def test_facetable_fields(self, product_schema):
        ff = product_schema.facetable_fields()
        assert "price" in ff
        assert "in_stock" in ff


class TestDataclasses:
    def test_filter_clause(self):
        fc = FilterClause(field="price", op=FilterOp.GT, value=100)
        assert fc.field == "price"
        assert fc.op == FilterOp.GT
        assert fc.value == 100

    def test_scored_candidate(self):
        sc = ScoredCandidate(doc_id="d1", score=0.95, source="semantic")
        assert sc.doc_id == "d1"
        assert sc.score == 0.95

    def test_search_query_defaults(self):
        sq = SearchQuery()
        assert sq.page == 1
        assert sq.size == 10
        assert sq.intent == QueryIntent.EXPLORATORY
        assert sq.filters == []
        assert sq.expanded_terms == []


class TestApiModels:
    def test_document_requires_id(self):
        with pytest.raises(ValidationError):
            Document(id="", fields={})

    def test_search_response_defaults(self):
        sr = SearchResponse()
        assert sr.total == 0
        assert sr.hits == []
        assert sr.facets == {}

    def test_search_hit_serialisation(self):
        doc = Document(id="x", fields={"a": 1})
        hit = SearchHit(document=doc, score=0.9)
        data = hit.model_dump()
        assert data["score"] == 0.9
        assert data["document"]["id"] == "x"

    def test_facet_result(self):
        fr = FacetResult(field="cat", values=[FacetValue(value="a", count=3)])
        assert fr.values[0].count == 3
