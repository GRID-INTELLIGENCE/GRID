"""
Unit tests for reasoning stabilization API router.

Covers stabilize, drift-check, roundtable reconciliation, and inference-gap
query flows.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def reset_reasoning_singleton():
    from application.mothership.routers.reasoning import reset_reasoning_service

    reset_reasoning_service()
    yield
    reset_reasoning_service()


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


@pytest.mark.anyio
async def test_stabilize_returns_trace_and_quality(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    response = await client.post(
        "/api/v1/stabilize",
        json={
            "input": "We might increase throughput, but some behavior is unclear in this path.",
            "context": {"domain": "infra", "objective": "reduce latency"},
            "task_type": "reasoning_stabilizer",
            "risk_level": "high",
            "case_id": "case_reasoning_001",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["stabilized_trace"]
    assert payload["data"]["quality_record"]["quality_score"] >= 0.0
    assert "next_actions" in payload["data"]


@pytest.mark.anyio
async def test_drift_check_detects_contradiction(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    response = await client.post(
        "/api/v1/drift-check",
        json={
            "trace_so_far": [
                {"statement": "The policy should always allow requests with verified evidence."},
                {"statement": "Maintain stable, safe operation under load."},
            ],
            "candidate_response": "The system should never allow evidence verification in this flow.",
            "case_id": "case_reasoning_002",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    flags = payload["data"]["drift_flags"]
    assert any(flag["signal_type"] == "contradiction" for flag in flags)


@pytest.mark.anyio
async def test_roundtable_reconcile_logs_open_gaps_and_query(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    case_id = "case_reasoning_003"
    reconcile = await client.post(
        "/api/v1/roundtable/reconcile",
        json={
            "case_id": case_id,
            "topic": "decision quality",
            "human_notes": [
                "Use conservative rollout and verify assumptions.",
                "Require confidence calibration before release.",
            ],
            "system_trace": [
                {"statement": "Enable immediate global rollout without validation."},
                {"statement": "Require confidence calibration before release."},
            ],
        },
        headers=auth_headers,
    )

    assert reconcile.status_code == 200
    reconcile_payload = reconcile.json()
    assert reconcile_payload["success"] is True
    assert "open_gaps" in reconcile_payload["data"]
    assert len(reconcile_payload["data"]["open_gaps"]) >= 1

    gaps = await client.get(f"/api/v1/inference-gaps/{case_id}", headers=auth_headers)
    assert gaps.status_code == 200
    gaps_payload = gaps.json()
    assert gaps_payload["success"] is True
    assert gaps_payload["data"]["case_id"] == case_id
    assert gaps_payload["data"]["total"] >= 1
