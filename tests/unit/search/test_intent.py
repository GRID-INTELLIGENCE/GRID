"""Tests for search.query.intent."""

from search.models import FilterClause, FilterOp, QueryIntent, SearchQuery
from search.query.intent import SearchIntentClassifier


class TestRuleBasedIntent:
    def test_exploratory_free_text(self):
        clf = SearchIntentClassifier(use_rag_classifier=False)
        q = SearchQuery(text="laptop bag")
        result = clf.classify(q)
        assert result.intent == QueryIntent.EXPLORATORY
        assert result.confidence == 0.7

    def test_analytical_numeric_filters(self):
        clf = SearchIntentClassifier(use_rag_classifier=False)
        q = SearchQuery(
            text="shoes",
            filters=[
                FilterClause(field="price", op=FilterOp.GT, value=50),
                FilterClause(field="price", op=FilterOp.LT, value=200),
            ],
        )
        result = clf.classify(q)
        assert result.intent == QueryIntent.ANALYTICAL

    def test_mixed_filters_below_threshold(self):
        clf = SearchIntentClassifier(use_rag_classifier=False)
        q = SearchQuery(
            text="shoes",
            filters=[
                FilterClause(field="category", op=FilterOp.EQ, value="footwear"),
                FilterClause(field="price", op=FilterOp.GT, value=50),
            ],
        )
        result = clf.classify(q)
        assert result.intent in (QueryIntent.ANALYTICAL, QueryIntent.EXPLORATORY)

    def test_empty_query(self):
        clf = SearchIntentClassifier(use_rag_classifier=False)
        q = SearchQuery()
        result = clf.classify(q)
        assert result.intent == QueryIntent.EXPLORATORY
        assert result.confidence == 0.5

    def test_navigational_with_field_values(self, embedding_provider):
        clf = SearchIntentClassifier(
            embedding_provider=embedding_provider,
            similarity_threshold=0.0,
            use_rag_classifier=False,
        )
        clf.register_field_values("category", ["electronics"])
        q = SearchQuery(text="electronics")
        result = clf.classify(q)
        assert result.intent == QueryIntent.NAVIGATIONAL
