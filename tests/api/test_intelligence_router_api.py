from __future__ import annotations

from typing import Any
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from application.mothership import dependencies
from application.mothership.routers.intelligence import router as intelligence_router


class _FakeIntelligenceApplication:
    instances: list[_FakeIntelligenceApplication] = []

    def __init__(self) -> None:
        self.interaction_log: list[dict[str, Any]] = []
        self.reset_called = False
        self.instance_number = len(self.instances) + 1
        self.instances.append(self)

    async def process_input(
        self,
        data: dict[str, Any],
        context_params: dict[str, Any],
        include_evidence: bool = False,
    ) -> dict[str, Any]:
        entry = {
            "instance_number": self.instance_number,
            "echo_data": data,
            "seen_user_id": context_params.get("user_id"),
        }
        if include_evidence:
            entry["timings_ms"] = {}
        self.interaction_log.append(entry)
        return entry

    def reset(self) -> None:
        self.reset_called = True
        self.interaction_log.clear()


def _build_test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(intelligence_router, prefix="/api/v1/intelligence")
    app.dependency_overrides[dependencies.verify_authentication] = lambda: {
        "authenticated": True,
        "method": "api_key",
        "permissions": {"read", "write"},
        "token_payload": {},
        "user_id": "user-123",
        "email": "user@example.com",
    }
    app.dependency_overrides[dependencies.check_rate_limit] = lambda: True
    app.dependency_overrides[dependencies.get_request_context] = lambda: {"request_id": "req-123"}
    return app


def test_process_intelligence_uses_fresh_application_per_request() -> None:
    _FakeIntelligenceApplication.instances.clear()

    with patch("application.mothership.routers.intelligence.IntelligenceApplication", _FakeIntelligenceApplication):
        app = _build_test_app()
        with TestClient(app) as client:
            first = client.post(
                "/api/v1/intelligence/process",
                json={"data": {"value": 1}, "context": {}, "include_evidence": True},
            )
            second = client.post(
                "/api/v1/intelligence/process",
                json={"data": {"value": 2}, "context": {}, "include_evidence": True},
            )

    assert first.status_code == 200
    assert second.status_code == 200
    assert len(_FakeIntelligenceApplication.instances) == 2
    assert first.json()["data"]["instance_number"] == 1
    assert second.json()["data"]["instance_number"] == 2
    assert first.json()["data"]["interaction_count"] == 1
    assert second.json()["data"]["interaction_count"] == 1
    assert first.json()["data"]["seen_user_id"] == "user-123"
    assert second.json()["data"]["seen_user_id"] == "user-123"


def test_process_intelligence_reset_session_is_request_local() -> None:
    _FakeIntelligenceApplication.instances.clear()

    with patch("application.mothership.routers.intelligence.IntelligenceApplication", _FakeIntelligenceApplication):
        app = _build_test_app()
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/intelligence/process",
                json={"data": {"value": 3}, "context": {}, "include_evidence": True, "reset_session": True},
            )

    assert response.status_code == 200
    assert len(_FakeIntelligenceApplication.instances) == 1
    assert _FakeIntelligenceApplication.instances[0].reset_called is True
    assert response.json()["meta"]["request_id"] == "req-123"
