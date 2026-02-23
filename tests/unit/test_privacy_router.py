"""
Unit tests for the Mothership privacy router.

Covers: privacy levels, stats, and endpoint availability.
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


class TestPrivacyLevels:
    @pytest.mark.anyio
    async def test_levels_returns_all_three(self, client, auth_headers):
        resp = await client.get("/api/v1/privacy/levels", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "strict" in data["levels"]
        assert "balanced" in data["levels"]
        assert "minimal" in data["levels"]

    @pytest.mark.anyio
    async def test_default_level_is_balanced(self, client, auth_headers):
        resp = await client.get("/api/v1/privacy/levels", headers=auth_headers)
        assert resp.json()["default"] == "balanced"


class TestPrivacyStats:
    @pytest.mark.anyio
    async def test_stats_returns_counters(self, client, auth_headers):
        resp = await client.get("/api/v1/privacy/stats", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_requests" in data
        assert "entities_detected" in data
        assert "texts_processed" in data
        assert "uptime" in data
