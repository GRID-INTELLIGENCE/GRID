"""Tests for search.query.parser."""

from search.models import FilterOp
from search.query.parser import QueryParser


class TestQueryParser:
    def test_free_text_only(self, product_schema):
        parser = QueryParser(product_schema)
        q = parser.parse("laptop bag")
        assert q.text == "laptop bag"
        assert q.filters == []

    def test_field_filter_eq(self, product_schema):
        parser = QueryParser(product_schema)
        q = parser.parse("category:electronics")
        assert q.text == ""
        assert len(q.filters) == 1
        assert q.filters[0].field == "category"
        assert q.filters[0].op == FilterOp.EQ
        assert q.filters[0].value == "electronics"

    def test_range_filter_gt(self, product_schema):
        parser = QueryParser(product_schema)
        q = parser.parse("price:>100")
        assert len(q.filters) == 1
        assert q.filters[0].field == "price"
        assert q.filters[0].op == FilterOp.GT
        assert q.filters[0].value == 100.0

    def test_range_filter_lte(self, product_schema):
        parser = QueryParser(product_schema)
        q = parser.parse("price:<=50")
        assert q.filters[0].op == FilterOp.LTE
        assert q.filters[0].value == 50.0

    def test_mixed_text_and_filters(self, product_schema):
        parser = QueryParser(product_schema)
        q = parser.parse("laptop category:electronics price:<=500")
        assert q.text == "laptop"
        assert len(q.filters) == 2

    def test_non_filterable_field_ignored(self, product_schema):
        parser = QueryParser(product_schema)
        q = parser.parse("title:hello world")
        assert q.text == "title:hello world"
        assert q.filters == []

    def test_page_and_size(self, product_schema):
        parser = QueryParser(product_schema)
        q = parser.parse("test", page=3, size=25)
        assert q.page == 3
        assert q.size == 25

    def test_facet_fields(self, product_schema):
        parser = QueryParser(product_schema)
        q = parser.parse("test", facet_fields=["category", "price"])
        assert q.facet_fields == ["category", "price"]
