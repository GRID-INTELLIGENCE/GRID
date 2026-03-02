"""Tests for search.api.routes using FastAPI TestClient."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from search.api.routes import create_search_router
from search.config import SearchConfig
from search.engine import SearchEngine


@pytest.fixture
def client(test_config) -> TestClient:
    engine = SearchEngine(config=test_config)
    app = FastAPI()
    app.include_router(create_search_router(engine, config=test_config))
    return TestClient(app)


@pytest.fixture
def admin_gating_config():
    return SearchConfig(
        embedding_provider="simple",
        vector_store_backend="in_memory",
        cross_encoder_enabled=False,
        guardrail_admin_gating=True,
    )


@pytest.fixture
def client_with_admin_gating(admin_gating_config, sample_documents) -> TestClient:
    engine = SearchEngine(config=admin_gating_config)
    app = FastAPI()
    app.include_router(create_search_router(engine, config=admin_gating_config))
    c = TestClient(app)
    c.put(
        "/api/search/products/schema",
        json={
            "name": "products",
            "fields": {
                "title": {"type": "text", "searchable": True},
                "price": {"type": "float", "filterable": True},
            },
        },
        headers={"X-Admin-Role": "admin"},
    )
    c.post(
        "/api/search/products/index",
        json={"documents": [d.model_dump() for d in sample_documents]},
        headers={"X-Admin-Role": "admin"},
    )
    return c


@pytest.fixture
def seeded_client(test_config, sample_documents) -> TestClient:
    engine = SearchEngine(config=test_config)
    app = FastAPI()
    app.include_router(create_search_router(engine, config=test_config))
    c = TestClient(app)

    c.put(
        "/api/search/products/schema",
        json={
            "name": "products",
            "fields": {
                "title": {"type": "text", "searchable": True, "weight": 2.0},
                "description": {"type": "text", "searchable": True},
                "price": {"type": "float", "filterable": True, "facetable": True},
                "category": {"type": "keyword", "filterable": True, "facetable": True},
                "in_stock": {"type": "boolean", "filterable": True, "facetable": True},
            },
        },
    )

    c.post(
        "/api/search/products/index",
        json={
            "documents": [d.model_dump() for d in sample_documents],
        },
    )

    return c


class TestSchemaEndpoint:
    def test_create_schema(self, client):
        resp = client.put(
            "/api/search/myindex/schema",
            json={
                "name": "myindex",
                "fields": {"title": {"type": "text", "searchable": True}},
            },
        )
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


class TestAdminGating:
    def test_schema_403_without_admin_when_gating_enabled(self, admin_gating_config):
        engine = SearchEngine(config=admin_gating_config)
        app = FastAPI()
        app.include_router(create_search_router(engine, config=admin_gating_config))
        c = TestClient(app)
        resp = c.put(
            "/api/search/myindex/schema",
            json={"name": "myindex", "fields": {"title": {"type": "text", "searchable": True}}},
        )
        assert resp.status_code == 403
        assert "Admin" in resp.json().get("detail", "")

    def test_schema_200_with_admin_header(self, admin_gating_config):
        engine = SearchEngine(config=admin_gating_config)
        app = FastAPI()
        app.include_router(create_search_router(engine, config=admin_gating_config))
        c = TestClient(app)
        resp = c.put(
            "/api/search/myindex/schema",
            json={"name": "myindex", "fields": {"title": {"type": "text", "searchable": True}}},
            headers={"X-Admin-Role": "admin"},
        )
        assert resp.status_code == 200

    def test_index_403_without_admin_when_gating_enabled(self, admin_gating_config, sample_documents):
        engine = SearchEngine(config=admin_gating_config)
        app = FastAPI()
        app.include_router(create_search_router(engine, config=admin_gating_config))
        c = TestClient(app)
        c.put(
            "/api/search/products/schema",
            json={
                "name": "products",
                "fields": {
                    "title": {"type": "text", "searchable": True},
                    "price": {"type": "float", "filterable": True},
                },
            },
            headers={"X-Admin-Role": "admin"},
        )
        resp = c.post(
            "/api/search/products/index",
            json={"documents": [d.model_dump() for d in sample_documents]},
        )
        assert resp.status_code == 403

    def test_delete_403_without_admin_when_gating_enabled(self, client_with_admin_gating):
        resp = client_with_admin_gating.delete("/api/search/products")
        assert resp.status_code == 403

    def test_delete_200_with_admin_header(self, client_with_admin_gating):
        resp = client_with_admin_gating.delete("/api/search/products", headers={"X-Admin-Role": "admin"})
        assert resp.status_code == 200

    def test_search_and_stats_not_gated(self, client_with_admin_gating):
        resp = client_with_admin_gating.post("/api/search/products/query", json={"query": "headphones"})
        assert resp.status_code == 200
        resp = client_with_admin_gating.get("/api/search/products/stats")
        assert resp.status_code == 200
