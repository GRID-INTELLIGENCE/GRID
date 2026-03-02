"""Integration tests for guardrail-wrapped search API."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from search.api.routes import create_search_router
from search.config import SearchConfig
from search.engine import SearchEngine
from search.models import Document


@pytest.fixture
def guardrail_config():
    return SearchConfig(
        embedding_provider="simple",
        vector_store_backend="in_memory",
        cross_encoder_enabled=False,
        guardrail_enabled=True,
        guardrail_auth_required=True,
    )


@pytest.fixture
def guardrail_config_no_auth():
    return SearchConfig(
        embedding_provider="simple",
        vector_store_backend="in_memory",
        cross_encoder_enabled=False,
        guardrail_enabled=True,
        guardrail_auth_required=False,
    )


@pytest.fixture
def client_with_guardrail(guardrail_config):
    engine = SearchEngine(config=guardrail_config)
    app = FastAPI()
    app.include_router(create_search_router(engine, config=guardrail_config))
    return TestClient(app)


@pytest.fixture
def client_guardrail_no_auth(guardrail_config_no_auth, sample_documents):
    engine = SearchEngine(config=guardrail_config_no_auth)
    app = FastAPI()
    app.include_router(create_search_router(engine, config=guardrail_config_no_auth))
    c = TestClient(app)
    c.put("/api/search/products/schema", json={
        "name": "products",
        "fields": {
            "title": {"type": "text", "searchable": True},
            "description": {"type": "text", "searchable": True},
            "price": {"type": "float", "filterable": True},
        },
    })
    c.post("/api/search/products/index", json={
        "documents": [d.model_dump() for d in sample_documents],
    })
    return c


@pytest.mark.integration
class TestGuardrailApiIntegration:
    def test_search_without_auth_blocked_when_required(self, client_with_guardrail):
        client_with_guardrail.put("/api/search/products/schema", json={
            "name": "products",
            "fields": {
                "title": {"type": "text", "searchable": True},
                "price": {"type": "float", "filterable": True},
            },
        })
        client_with_guardrail.post("/api/search/products/index", json={
            "documents": [{"id": "p1", "fields": {"title": "Headphones", "price": 79.99}}],
        })
        resp = client_with_guardrail.post("/api/search/products/query", json={"query": "headphones"})
        assert resp.status_code in (401, 403)

    def test_search_with_auth_succeeds_when_required(self, client_with_guardrail):
        client_with_guardrail.put("/api/search/products/schema", json={
            "name": "products",
            "fields": {
                "title": {"type": "text", "searchable": True},
                "price": {"type": "float", "filterable": True},
            },
        })
        client_with_guardrail.post("/api/search/products/index", json={
            "documents": [{"id": "p1", "fields": {"title": "Headphones", "price": 79.99}}],
        })
        resp = client_with_guardrail.post(
            "/api/search/products/query",
            json={"query": "headphones"},
            headers={"Authorization": "Bearer test-token-123"},
        )
        assert resp.status_code == 200

    def test_search_without_auth_succeeds_when_not_required(self, client_guardrail_no_auth):
        resp = client_guardrail_no_auth.post("/api/search/products/query", json={"query": "headphones"})
        assert resp.status_code == 200
        data = resp.json()
        assert "hits" in data
        assert "total" in data
