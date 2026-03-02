"""Tests for search.api.routes using FastAPI TestClient."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from search.api.routes import create_search_router
from search.engine import SearchEngine


@pytest.fixture
def client(test_config) -> TestClient:
    engine = SearchEngine(config=test_config)
    app = FastAPI()
    app.include_router(create_search_router(engine))
    return TestClient(app)


@pytest.fixture
def seeded_client(test_config, sample_documents) -> TestClient:
    engine = SearchEngine(config=test_config)
    app = FastAPI()
    app.include_router(create_search_router(engine))
    c = TestClient(app)

    c.put("/api/search/products/schema", json={
        "name": "products",
        "fields": {
            "title": {"type": "text", "searchable": True, "weight": 2.0},
            "description": {"type": "text", "searchable": True},
            "price": {"type": "float", "filterable": True, "facetable": True},
            "category": {"type": "keyword", "filterable": True, "facetable": True},
            "in_stock": {"type": "boolean", "filterable": True, "facetable": True},
        },
    })

    c.post("/api/search/products/index", json={
        "documents": [d.model_dump() for d in sample_documents],
    })

    return c


class TestSchemaEndpoint:
    def test_create_schema(self, client):
        resp = client.put("/api/search/myindex/schema", json={
            "name": "myindex",
            "fields": {"title": {"type": "text", "searchable": True}},
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "created"

    def test_duplicate_schema_409(self, client):
        payload = {"name": "x", "fields": {"t": {"type": "text", "searchable": True}}}
        client.put("/api/search/x/schema", json=payload)
        resp = client.put("/api/search/x/schema", json=payload)
        assert resp.status_code == 409


class TestIndexEndpoint:
    def test_index_documents(self, seeded_client):
        resp = seeded_client.get("/api/search/products/stats")
        assert resp.status_code == 200
        assert resp.json()["doc_count"] == 5

    def test_index_nonexistent_404(self, client):
        resp = client.post("/api/search/nope/index", json={"documents": []})
        assert resp.status_code == 404


class TestSearchEndpoint:
    def test_basic_search(self, seeded_client):
        resp = seeded_client.post("/api/search/products/query", json={"query": "headphones"})
        assert resp.status_code == 200
        data = resp.json()
        assert "hits" in data
        assert "total" in data

    def test_search_nonexistent_404(self, client):
        resp = client.post("/api/search/nope/query", json={"query": "x"})
        assert resp.status_code == 404


class TestDeleteEndpoint:
    def test_delete(self, seeded_client):
        resp = seeded_client.delete("/api/search/products")
        assert resp.status_code == 200
        assert resp.json()["status"] == "deleted"

    def test_delete_nonexistent_404(self, client):
        resp = client.delete("/api/search/nope")
        assert resp.status_code == 404


class TestHealthEndpoint:
    def test_health(self, client):
        resp = client.get("/api/search/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "latency_stats" in data
