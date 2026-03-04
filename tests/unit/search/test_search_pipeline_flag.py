import pytest

from search.config import SearchConfig
from search.engine import SearchEngine
from search.models import Document, FieldSchema, FieldType, IndexSchema


@pytest.fixture
def engine_basic():
    cfg = SearchConfig(
        embedding_provider="simple",
        vector_store_backend="in_memory",
        search_full_pipeline=False,
        cross_encoder_enabled=False,
    )
    return SearchEngine(config=cfg)


@pytest.fixture
def engine_full():
    cfg = SearchConfig(
        embedding_provider="simple",
        vector_store_backend="in_memory",
        search_full_pipeline=True,
        cross_encoder_enabled=False,
    )
    return SearchEngine(config=cfg)


def test_pipeline_flag_affects_explanation(engine_basic, engine_full):
    schema = IndexSchema(
        name="test",
        fields={"text": FieldSchema(type=FieldType.TEXT, searchable=True)},
    )

    # Setup for both engines
    for engine in [engine_basic, engine_full]:
        engine.create_index(schema)
        engine.index_documents(
            "test",
            [
                Document(id="d1", fields={"text": "hello world"}),
                Document(id="d2", fields={"text": "unrelated topic"}),
            ],
        )

    # 1. Basic search
    resp_basic = engine_basic.search("test", "world")
    assert resp_basic.hits[0].explanation["pipeline"] == "basic"
    assert resp_basic.hits[0].explanation["source"] == "keyword"

    # 2. Full search
    resp_full = engine_full.search("test", "world")
    assert resp_full.hits[0].explanation["pipeline"] == "full"
    # Source might be 'fusion' from HybridFusion
    assert resp_full.hits[0].explanation["source"] == "fusion"


def test_basic_pipeline_skips_facets(engine_basic):
    schema = IndexSchema(
        name="test",
        fields={
            "text": FieldSchema(type=FieldType.TEXT, searchable=True),
            "cat": FieldSchema(type=FieldType.KEYWORD, facetable=True),
        },
    )
    engine_basic.create_index(schema)
    engine_basic.index_documents(
        "test",
        [
            Document(id="d1", fields={"text": "a", "cat": "x"}),
            Document(id="d2", fields={"text": "b", "cat": "y"}),
        ],
    )

    # Search with facets requested
    resp = engine_basic.search("test", "a", facet_fields=["cat"])

    # Should be empty because facets are skipped in basic pipeline
    assert resp.facets == {}


def test_full_pipeline_builds_bm25_and_vector_score_maps(engine_full):
    schema = IndexSchema(
        name="test",
        fields={
            "text": FieldSchema(type=FieldType.TEXT, searchable=True),
        },
    )
    engine_full.create_index(schema)
    engine_full.index_documents(
        "test",
        [
            Document(id="d1", fields={"text": "hello world"}),
            Document(id="d2", fields={"text": "unrelated topic"}),
        ],
    )

    state = engine_full._indices["test"]
    captured: dict[str, dict[str, float]] = {}
    original_rank = state.ranking.rank

    def _capture_rank(query, candidates, documents, doc_texts, bm25_scores, vector_scores):
        captured["bm25"] = bm25_scores
        captured["vector"] = vector_scores
        return candidates

    state.ranking.rank = _capture_rank
    try:
        response = engine_full.search("test", "world")
    finally:
        state.ranking.rank = original_rank

    assert response.total > 0
    assert captured["bm25"]
    assert captured["vector"]
