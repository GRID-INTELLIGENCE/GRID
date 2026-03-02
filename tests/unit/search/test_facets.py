"""Tests for search.facets.aggregator."""

import pytest

from search.facets.aggregator import FacetAggregator
from search.indexing.structured_store import StructuredFieldIndex
from search.models import FieldSchema, FieldType, IndexSchema


@pytest.fixture
def schema():
    return IndexSchema(
        name="test",
        fields={
            "category": FieldSchema(type=FieldType.KEYWORD, filterable=True, facetable=True),
            "price": FieldSchema(type=FieldType.FLOAT, filterable=True, facetable=True),
            "active": FieldSchema(type=FieldType.BOOLEAN, filterable=True, facetable=True),
        },
    )


@pytest.fixture
def populated_store(schema):
    store = StructuredFieldIndex(schema)
    store.add("d1", {"category": "books", "price": 10.0, "active": True})
    store.add("d2", {"category": "books", "price": 20.0, "active": True})
    store.add("d3", {"category": "electronics", "price": 99.0, "active": False})
    store.add("d4", {"category": "electronics", "price": 199.0, "active": True})
    return store


class TestKeywordFacet:
    def test_counts(self, schema, populated_store):
        agg = FacetAggregator(schema, populated_store)
        facets = agg.aggregate({"d1", "d2", "d3", "d4"}, ["category"])
        cat = facets["category"]
        values = {v.value: v.count for v in cat.values}
        assert values["books"] == 2
        assert values["electronics"] == 2

    def test_scoped_to_result_set(self, schema, populated_store):
        agg = FacetAggregator(schema, populated_store)
        facets = agg.aggregate({"d1", "d2"}, ["category"])
        cat = facets["category"]
        values = {v.value: v.count for v in cat.values}
        assert values == {"books": 2}


class TestNumericHistogram:
    def test_produces_buckets(self, schema, populated_store):
        agg = FacetAggregator(schema, populated_store, default_histogram_buckets=3)
        facets = agg.aggregate({"d1", "d2", "d3", "d4"}, ["price"])
        price = facets["price"]
        assert len(price.values) > 0
        assert all(v.count > 0 for v in price.values)

    def test_single_value(self, schema):
        store = StructuredFieldIndex(schema)
        store.add("d1", {"category": "x", "price": 50.0, "active": True})
        agg = FacetAggregator(schema, store)
        facets = agg.aggregate({"d1"}, ["price"])
        assert len(facets["price"].values) == 1
        assert facets["price"].values[0].count == 1


class TestBooleanFacet:
    def test_counts(self, schema, populated_store):
        agg = FacetAggregator(schema, populated_store)
        facets = agg.aggregate({"d1", "d2", "d3", "d4"}, ["active"])
        active = facets["active"]
        values = {v.value: v.count for v in active.values}
        assert values[True] == 3
        assert values[False] == 1


class TestNonFacetableField:
    def test_ignored(self, schema, populated_store):
        schema_no_facet = IndexSchema(
            name="test",
            fields={"category": FieldSchema(type=FieldType.KEYWORD, filterable=True, facetable=False)},
        )
        store = StructuredFieldIndex(schema_no_facet)
        store.add("d1", {"category": "x"})
        agg = FacetAggregator(schema_no_facet, store)
        facets = agg.aggregate({"d1"}, ["category"])
        assert "category" not in facets
