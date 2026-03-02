"""Tests for search.indexing.structured_store."""

import pytest

from search.indexing.structured_store import StructuredFieldIndex
from search.models import FieldSchema, FieldType, FilterClause, FilterOp, IndexSchema


@pytest.fixture
def schema():
    return IndexSchema(
        name="test",
        fields={
            "category": FieldSchema(type=FieldType.KEYWORD, filterable=True, facetable=True),
            "price": FieldSchema(type=FieldType.FLOAT, filterable=True, facetable=True),
            "active": FieldSchema(type=FieldType.BOOLEAN, filterable=True, facetable=True),
            "name": FieldSchema(type=FieldType.TEXT, searchable=True),
        },
    )


@pytest.fixture
def store(schema):
    idx = StructuredFieldIndex(schema)
    idx.add("d1", {"category": "Electronics", "price": 99.99, "active": True, "name": "Widget"})
    idx.add("d2", {"category": "Books", "price": 19.99, "active": True, "name": "Novel"})
    idx.add("d3", {"category": "Electronics", "price": 249.99, "active": False, "name": "Gadget"})
    return idx


class TestAddRemove:
    def test_doc_count(self, store):
        assert store.doc_count() == 3

    def test_remove(self, store):
        store.remove("d2")
        assert store.doc_count() == 2
        result = store.filter([FilterClause(field="category", op=FilterOp.EQ, value="books")])
        assert result == set()


class TestFilters:
    def test_eq(self, store):
        result = store.filter([FilterClause(field="category", op=FilterOp.EQ, value="electronics")])
        assert result == {"d1", "d3"}

    def test_neq(self, store):
        result = store.filter([FilterClause(field="category", op=FilterOp.NEQ, value="electronics")])
        assert result == {"d2"}

    def test_gt(self, store):
        result = store.filter([FilterClause(field="price", op=FilterOp.GT, value=50)])
        assert result == {"d1", "d3"}

    def test_gte(self, store):
        result = store.filter([FilterClause(field="price", op=FilterOp.GTE, value=99.99)])
        assert result == {"d1", "d3"}

    def test_lt(self, store):
        result = store.filter([FilterClause(field="price", op=FilterOp.LT, value=100)])
        assert result == {"d1", "d2"}

    def test_lte(self, store):
        result = store.filter([FilterClause(field="price", op=FilterOp.LTE, value=19.99)])
        assert result == {"d2"}

    def test_in(self, store):
        result = store.filter([FilterClause(field="category", op=FilterOp.IN, value=["electronics", "books"])])
        assert result == {"d1", "d2", "d3"}

    def test_intersection(self, store):
        result = store.filter(
            [
                FilterClause(field="category", op=FilterOp.EQ, value="electronics"),
                FilterClause(field="price", op=FilterOp.GT, value=100),
            ]
        )
        assert result == {"d3"}

    def test_empty_result(self, store):
        result = store.filter([FilterClause(field="category", op=FilterOp.EQ, value="nonexistent")])
        assert result == set()

    def test_no_clauses_returns_all(self, store):
        result = store.filter([])
        assert result == {"d1", "d2", "d3"}


class TestFacetHelpers:
    def test_get_field_values_all(self, store):
        counts = store.get_field_values("category")
        assert counts["electronics"] == 2
        assert counts["books"] == 1

    def test_get_field_values_scoped(self, store):
        counts = store.get_field_values("category", doc_ids={"d1"})
        assert counts == {"electronics": 1}

    def test_get_numeric_values(self, store):
        vals = store.get_numeric_values("price")
        assert sorted(vals) == pytest.approx([19.99, 99.99, 249.99])

    def test_get_numeric_values_scoped(self, store):
        vals = store.get_numeric_values("price", doc_ids={"d2"})
        assert vals == pytest.approx([19.99])
