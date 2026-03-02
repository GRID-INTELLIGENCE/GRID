"""Security tests for search guardrail."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from search.api.routes import create_search_router
from search.config import SearchConfig
from search.engine import SearchEngine


@pytest.fixture
def guardrail_config_strict():
    return SearchConfig(
        embedding_provider="simple",
        vector_store_backend="in_memory",
        cross_encoder_enabled=False,
        guardrail_enabled=True,
        guardrail_auth_required=False,
        guardrail_rate_limit_per_minute=2,
    )


@pytest.fixture
def security_client(guardrail_config_strict):
    engine = SearchEngine(config=guardrail_config_strict)
    app = FastAPI()
    app.include_router(create_search_router(engine, config=guardrail_config_strict))
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
    )
    c.post(
        "/api/search/products/index",
        json={
            "documents": [{"id": "p1", "fields": {"title": "Test", "price": 10}}],
        },
    )
    return c


@pytest.mark.security
class TestSearchGuardrailSecurity:
    def test_sanitize_blocks_injection_patterns(self, security_client):
        resp = security_client.post(
            "/api/search/products/query",
            json={"query": "test; DROP TABLE users"},
        )
        assert resp.status_code == 403

    def test_sanitize_blocks_script_injection(self, security_client):
        resp = security_client.post(
            "/api/search/products/query",
            json={"query": "hello <script>alert(1)</script>"},
        )
        assert resp.status_code == 403

    def test_rate_limit_enforced(self, security_client):
        for _ in range(3):
            resp = security_client.post(
                "/api/search/products/query",
                json={"query": "test"},
            )
        assert resp.status_code == 429
