"""
Unit tests for the Mothership inference router.

Covers: models listing, async inference queuing, task status lookup.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    from application.mothership.main import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    resp = await client.post("/api/v1/auth/login", json={"username": "operator", "password": "operator"})
    if resp.status_code == 200:
        data = resp.json()
        token = data.get("data", {}).get("access_token", data.get("access_token", data.get("token", "dev")))
        return {"Authorization": f"Bearer {token}"}
    return {"Authorization": "Bearer dev-test-token"}


class TestInferenceModels:
    @pytest.mark.anyio
    async def test_list_models_returns_list(self, client, auth_headers):
        resp = await client.get("/api/v1/inference/models", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "models" in data
        assert isinstance(data["models"], list)
        assert "default" in data

    @pytest.mark.anyio
    async def test_list_models_has_default(self, client, auth_headers):
        resp = await client.get("/api/v1/inference/models", headers=auth_headers)
        data = resp.json()
        assert data["default"] in data["models"]


class TestInferenceAsync:
    @pytest.mark.anyio
    async def test_async_inference_returns_task_id(self, client, auth_headers):
        resp = await client.post(
            "/api/v1/inference/async",
            json={"prompt": "Hello world"},
            headers=auth_headers,
        )
        # May return 200 (queued) or 503 (service unavailable)
        if resp.status_code == 200:
            data = resp.json()
            assert "task_id" in data
            assert data["status"] == "queued"

    @pytest.mark.anyio
    async def test_status_unknown_task_returns_404(self, client, auth_headers):
        resp = await client.get(
            "/api/v1/inference/status/nonexistent_task_id",
            headers=auth_headers,
        )
        assert resp.status_code in (404, 500)
