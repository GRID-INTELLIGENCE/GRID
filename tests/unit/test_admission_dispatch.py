"""Tests for AdmissionGateMiddleware.dispatch() — gate-by-gate.

Complements test_admission_gate.py (which covers attribution helpers and signing).
Each test builds a minimal FastAPI app, drives it through TestClient, and asserts
on HTTP status codes, response bodies, and response headers.
"""

from __future__ import annotations

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from application.mothership.middleware.admission_gate import (
    AdmissionGateMiddleware,
    EntityAttributionEngine,
    PolicyBillboard,
    ViolationType,
)
from application.mothership.security.merit_standing import MERIT_SCORING_ENGINE


@pytest.fixture(autouse=True)
def reset_merit():
    """Reset the global merit engine so score state does not bleed between tests."""
    MERIT_SCORING_ENGINE.reset()
    yield
    MERIT_SCORING_ENGINE.reset()


def _build_app(
    *,
    call_budget: int = 100,
    window_seconds: float = 60.0,
    enforce_origin: bool = True,
    enforce_structure: bool = True,
    context_token_ceiling: int = 25_000,
    attribution: EntityAttributionEngine | None = None,
) -> FastAPI:
    app = FastAPI()

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/api/test")
    def api_get():
        return {"ok": True}

    @app.post("/api/test")
    def api_post():
        return {"ok": True}

    @app.post("/api/intelligence/analyze")
    def intelligence_analyze():
        return {"ok": True}

    @app.get("/api/v1/agentic/tasks")
    def agentic_no_auth():
        return {"ok": True}

    kwargs: dict = {
        "call_budget": call_budget,
        "window_seconds": window_seconds,
        "context_token_ceiling": context_token_ceiling,
        "enforce_origin": enforce_origin,
        "enforce_structure": enforce_structure,
        "billboard": PolicyBillboard(),
    }
    if attribution is not None:
        kwargs["attribution"] = attribution

    app.add_middleware(AdmissionGateMiddleware, **kwargs)
    return app


@pytest.mark.unit
class TestBypassPaths:
    def test_health_path_bypasses_gate(self) -> None:
        client = TestClient(_build_app(), raise_server_exceptions=False)
        r = client.get("/health")
        assert r.status_code == 200

    def test_root_path_bypasses_gate(self) -> None:
        app = _build_app()

        @app.get("/")
        def root():
            return {"root": True}

        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/")
        assert r.status_code == 200

    def test_agentic_route_without_auth_passes_through(self) -> None:
        """Auth-gated agentic routes are delegated to the auth middleware, not the gate."""
        client = TestClient(_build_app(), raise_server_exceptions=False)
        r = client.get("/api/v1/agentic/tasks")
        # Gate lets it through; route may 401 from auth — not our concern here.
        assert r.status_code != 403


@pytest.mark.unit
class TestGate0Banner:
    def test_bannered_entity_is_blocked(self) -> None:
        attribution = EntityAttributionEngine(banner_threshold=1)
        # Trigger a violation to cause the banner
        attribution.record_violation("test-entity", ViolationType.BUDGET_EXCEEDED)
        assert attribution.get_record("test-entity").bannered

        client = TestClient(
            _build_app(attribution=attribution),
            raise_server_exceptions=False,
            headers={"X-Entity-Id": "test-entity"},
        )
        r = client.get("/api/test")
        assert r.status_code == 403
        body = r.json()
        assert body["error"]["code"] == "ADMISSION_ENTITY_BANNERED"
        assert body["bannered"] is True


@pytest.mark.unit
class TestGate1Budget:
    def test_within_budget_is_admitted(self) -> None:
        client = TestClient(_build_app(call_budget=5), raise_server_exceptions=False)
        r = client.get("/api/test")
        assert r.status_code == 200
        assert "X-Admission-Remaining" in r.headers

    def test_budget_exceeded_returns_429(self) -> None:
        client = TestClient(_build_app(call_budget=2), raise_server_exceptions=False)
        client.get("/api/test")
        client.get("/api/test")
        r = client.get("/api/test")
        assert r.status_code == 429
        body = r.json()
        assert body["error"]["code"] == "ADMISSION_BUDGET_EXCEEDED"
        assert "Retry-After" in r.headers

    def test_remaining_header_decrements(self) -> None:
        client = TestClient(_build_app(call_budget=5), raise_server_exceptions=False)
        r1 = client.get("/api/test")
        r2 = client.get("/api/test")
        assert int(r1.headers["X-Admission-Remaining"]) > int(r2.headers["X-Admission-Remaining"])


@pytest.mark.unit
class TestGate2Origin:
    def test_unknown_origin_is_rejected(self) -> None:
        client = TestClient(_build_app(enforce_origin=True), raise_server_exceptions=False)
        r = client.get("/api/test", headers={"X-Admission-Origin": "evil-external"})
        assert r.status_code == 403
        body = r.json()
        assert body["error"]["code"] == "ADMISSION_ORIGIN_DENIED"

    def test_allowed_origin_passes(self) -> None:
        client = TestClient(_build_app(enforce_origin=True), raise_server_exceptions=False)
        r = client.get("/api/test", headers={"X-Admission-Origin": "internal"})
        assert r.status_code == 200

    def test_missing_origin_header_passes(self) -> None:
        """No X-Admission-Origin is not a violation — only explicit unknown values are blocked."""
        client = TestClient(_build_app(enforce_origin=True), raise_server_exceptions=False)
        r = client.get("/api/test")
        assert r.status_code == 200

    def test_enforce_origin_disabled_passes_any_origin(self) -> None:
        client = TestClient(_build_app(enforce_origin=False), raise_server_exceptions=False)
        r = client.get("/api/test", headers={"X-Admission-Origin": "totally-unknown"})
        assert r.status_code == 200


@pytest.mark.unit
class TestGate3BodyChecks:
    def test_context_ceiling_exceeded_returns_422(self) -> None:
        # 1 token ≈ 4 bytes; ceiling of 10 tokens → 40 bytes; send 80 bytes
        tiny_ceiling = 10
        client = TestClient(
            _build_app(context_token_ceiling=tiny_ceiling, enforce_structure=True),
            raise_server_exceptions=False,
        )
        large_payload = json.dumps({"data": "x" * 200})
        r = client.post("/api/test", content=large_payload, headers={"Content-Type": "application/json"})
        assert r.status_code == 422
        body = r.json()
        assert body["error"]["code"] == "ADMISSION_CONTEXT_OVERFLOW"

    def test_invalid_json_body_returns_422(self) -> None:
        client = TestClient(_build_app(), raise_server_exceptions=False)
        r = client.post("/api/test", content=b"not-json!!!", headers={"Content-Type": "application/json"})
        assert r.status_code == 422
        body = r.json()
        assert body["error"]["code"] == "ADMISSION_INVALID_BODY"

    def test_intelligence_path_missing_data_key_returns_422(self) -> None:
        client = TestClient(_build_app(), raise_server_exceptions=False)
        payload = json.dumps({"message": "hello"})
        r = client.post(
            "/api/intelligence/analyze",
            content=payload,
            headers={"Content-Type": "application/json"},
        )
        assert r.status_code == 422
        body = r.json()
        assert body["error"]["code"] == "ADMISSION_MISSING_STRUCTURE"

    def test_intelligence_path_with_data_key_passes_body_check(self) -> None:
        client = TestClient(_build_app(), raise_server_exceptions=False)
        payload = json.dumps({"data": "some input"})
        r = client.post(
            "/api/intelligence/analyze",
            content=payload,
            headers={"Content-Type": "application/json"},
        )
        # May be blocked by merit (POST requires B2), but NOT by body structure check
        assert r.status_code != 422 or r.json().get("error", {}).get("code") != "ADMISSION_MISSING_STRUCTURE"

    def test_structure_enforcement_disabled_skips_body_checks(self) -> None:
        client = TestClient(_build_app(enforce_structure=False), raise_server_exceptions=False)
        r = client.post("/api/test", content=b"raw garbage", headers={"Content-Type": "application/json"})
        # Gate 3 skipped entirely when enforce_structure=False
        assert r.status_code != 422


@pytest.mark.unit
class TestGate3dProfitMasking:
    def test_profit_masking_signal_returns_403(self) -> None:
        client = TestClient(_build_app(), raise_server_exceptions=False)
        payload = json.dumps({"data": "something", "intent": "skip_validation"})
        r = client.post("/api/test", content=payload, headers={"Content-Type": "application/json"})
        assert r.status_code == 403
        body = r.json()
        assert body["error"]["code"] == "ADMISSION_PROFIT_MASKING"

    def test_profit_masking_applies_3x_penalty(self) -> None:
        attribution = EntityAttributionEngine()
        client = TestClient(_build_app(attribution=attribution), raise_server_exceptions=False)
        payload = json.dumps({"data": "x", "skip_validation": True})
        client.post("/api/test", content=payload, headers={"Content-Type": "application/json"})

        entity_id = list(attribution.entities.keys())[0]
        record = attribution.get_record(entity_id)
        # Base penalty for PROFIT_MASKING is 15; 3x multiplier → 45
        assert record.total_penalty_points == 45

    def test_clean_payload_passes_profit_mask_check(self) -> None:
        client = TestClient(_build_app(), raise_server_exceptions=False)
        payload = json.dumps({"data": "a normal request"})
        r = client.post("/api/test", content=payload, headers={"Content-Type": "application/json"})
        # May be blocked by merit but NOT by profit mask
        if r.status_code == 403:
            assert r.json().get("error", {}).get("code") != "ADMISSION_PROFIT_MASKING"


@pytest.mark.unit
class TestAdmittedRequest:
    def test_admitted_get_returns_200(self) -> None:
        client = TestClient(_build_app(), raise_server_exceptions=False)
        r = client.get("/api/test")
        assert r.status_code == 200

    def test_admitted_response_has_remaining_header(self) -> None:
        client = TestClient(_build_app(call_budget=10), raise_server_exceptions=False)
        r = client.get("/api/test")
        assert r.status_code == 200
        assert "X-Admission-Remaining" in r.headers
        assert int(r.headers["X-Admission-Remaining"]) == 9

    def test_admitted_response_has_penalty_header(self) -> None:
        client = TestClient(_build_app(), raise_server_exceptions=False)
        r = client.get("/api/test")
        assert "X-Entity-Penalty" in r.headers
        assert r.headers["X-Entity-Penalty"] == "0"

    def test_admitted_response_has_policy_billboard_header(self) -> None:
        client = TestClient(_build_app(), raise_server_exceptions=False)
        r = client.get("/api/test")
        assert "X-Policy-Billboard" in r.headers
        assert "GRID Policy" in r.headers["X-Policy-Billboard"]

    def test_admitted_counter_increments(self) -> None:
        attribution = EntityAttributionEngine()
        client = TestClient(_build_app(attribution=attribution), raise_server_exceptions=False)
        client.get("/api/test")
        client.get("/api/test")
        assert attribution.total_admitted == 2


@pytest.mark.unit
class TestEntityResolution:
    def test_api_key_header_used_for_entity_id(self) -> None:
        attribution = EntityAttributionEngine()
        client = TestClient(_build_app(attribution=attribution), raise_server_exceptions=False)
        client.get("/api/test", headers={"X-API-Key": "abcdef123456789"})
        # Entity should be resolved as "api:<first 16 chars>"
        entity_keys = list(attribution.entities.keys())
        assert any(k.startswith("api:") for k in entity_keys)

    def test_ip_fallback_when_no_key(self) -> None:
        attribution = EntityAttributionEngine()
        client = TestClient(_build_app(attribution=attribution), raise_server_exceptions=False)
        client.get("/api/test")
        entity_keys = list(attribution.entities.keys())
        assert any(k.startswith("ip:") for k in entity_keys)


@pytest.mark.unit
class TestDriftSummary:
    def test_drift_summary_empty_fleet(self) -> None:
        attribution = EntityAttributionEngine()
        summary = attribution.drift_summary()
        assert summary["tracked_entities"] == 0
        assert summary["mean_drift"] == 0.0
        assert summary["max_drift"] == 0.0
        assert summary["top_drifting"] == []

    def test_drift_summary_after_update(self) -> None:
        attribution = EntityAttributionEngine()
        attribution.update_drift("entity-a", 0.8)
        attribution.update_drift("entity-b", 0.3)
        summary = attribution.drift_summary(top_n=5)
        assert summary["tracked_entities"] == 2
        assert summary["max_drift"] == pytest.approx(0.8)
        assert any(e["entity_id"] == "entity-a" for e in summary["top_drifting"])

    def test_drift_summary_top_n_zero_skips_sort(self) -> None:
        attribution = EntityAttributionEngine()
        attribution.update_drift("entity-a", 0.9)
        summary = attribution.drift_summary(top_n=0)
        assert summary["tracked_entities"] == 1
        assert summary["top_drifting"] == []

    def test_drift_score_clamped_to_unit_interval(self) -> None:
        attribution = EntityAttributionEngine()
        attribution.update_drift("entity-a", 5.0)
        record = attribution.get_record("entity-a")
        assert record.drift_score == 1.0

        attribution.update_drift("entity-b", -1.0)
        record_b = attribution.get_record("entity-b")
        assert record_b.drift_score == 0.0
