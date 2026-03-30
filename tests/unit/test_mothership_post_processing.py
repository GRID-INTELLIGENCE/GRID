"""Unit tests for the Admission Gate — top-of-stack pre-filter with entity attribution.

Tests verify:
1. Excessive tool calls (lobbying) are rejected at the gate.
2. Context overflow is detected and refused before reaching the pipeline.
3. Budget tracker rejects overruns per sliding window.
4. External calls from unknown origins are blocked.
5. Bogus/irrelevant payloads are filtered before reaching any router.
6. Entity attribution resolves requests to named entities.
7. Violations accumulate penalty points per entity.
8. Profit-masking signals trigger 3x penalty multiplier.
9. Bannered entities are hard-blocked at gate 0.
10. Penalties reduce effective budget proportionally.
11. Knowledge store receives violation + banner events.
12. Under legitimate load, the gate remains transparent.
13. Policy billboard is displayed at the top of every execution chain.
14. Penalty tiers correctly classify runtime mistakes vs intentional scheming.
15. Billboard snapshot is attached to every rejection response.
"""

from __future__ import annotations

import json
import time
from typing import Any
from unittest.mock import MagicMock, call

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from application.mothership.middleware.admission_gate import (
    ALLOWED_ORIGINS,
    BILLBOARD_VERSION,
    PROFIT_MASK_SIGNALS,
    AdmissionGateMiddleware,
    EntityAttributionEngine,
    EntityRecord,
    PolicyBillboard,
    ViolationType,
    _BudgetTracker,
    load_billboard,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_app(
    call_budget: int = 10,
    window_seconds: float = 60.0,
    context_token_ceiling: int = 25_000,
    enforce_origin: bool = True,
    enforce_structure: bool = True,
    banner_threshold: int = 50,
    profit_mask_multiplier: int = 3,
    knowledge_store: Any = None,
) -> FastAPI:
    """Build a minimal FastAPI app with the AdmissionGate as the outermost middleware."""
    app = FastAPI()

    @app.post("/api/v1/intelligence/process")
    async def intelligence_process(request: Request) -> JSONResponse:
        body = await request.json()
        return JSONResponse({"success": True, "echo": body})

    @app.post("/api/v1/other/endpoint")
    async def other_endpoint(request: Request) -> JSONResponse:
        body = await request.json()
        return JSONResponse({"success": True, "echo": body})

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ping")
    async def ping() -> dict[str, str]:
        return {"ping": "pong"}

    app.add_middleware(
        AdmissionGateMiddleware,
        call_budget=call_budget,
        window_seconds=window_seconds,
        context_token_ceiling=context_token_ceiling,
        enforce_origin=enforce_origin,
        enforce_structure=enforce_structure,
        banner_threshold=banner_threshold,
        profit_mask_multiplier=profit_mask_multiplier,
        knowledge_store=knowledge_store,
    )

    return app


def _valid_payload(blended: float = 0.5) -> dict[str, Any]:
    return {"data": {"blended_val": blended}, "context": {"coherence": 0.7}}


def _intelligence_url() -> str:
    return "/api/v1/intelligence/process"


def _make_mock_knowledge_store() -> MagicMock:
    """Mock that satisfies KnowledgeStoreProtocol."""
    store = MagicMock()
    store.store_entity = MagicMock()
    store.create_relationship = MagicMock()
    return store


# ===========================================================================
# Budget Tracker (unit)
# ===========================================================================


class TestBudgetTracker:
    def test_allows_within_budget(self) -> None:
        t = _BudgetTracker(budget=5, window_seconds=60.0)
        for _ in range(5):
            assert t.allow("client-1")

    def test_blocks_over_budget(self) -> None:
        t = _BudgetTracker(budget=3, window_seconds=60.0)
        for _ in range(3):
            assert t.allow("client-1")
        assert not t.allow("client-1")

    def test_separate_clients_independent(self) -> None:
        t = _BudgetTracker(budget=2, window_seconds=60.0)
        assert t.allow("a")
        assert t.allow("a")
        assert not t.allow("a")
        assert t.allow("b")
        assert t.allow("b")
        assert not t.allow("b")

    def test_remaining_count(self) -> None:
        t = _BudgetTracker(budget=5, window_seconds=60.0)
        assert t.remaining("c") == 5
        t.allow("c")
        t.allow("c")
        assert t.remaining("c") == 3

    def test_effective_budget_override(self) -> None:
        """Budget can be reduced per-call for penalized entities."""
        t = _BudgetTracker(budget=10, window_seconds=60.0)
        # With effective budget of 2, only 2 calls allowed
        assert t.allow("x", effective_budget=2)
        assert t.allow("x", effective_budget=2)
        assert not t.allow("x", effective_budget=2)

    def test_reset_clears_all(self) -> None:
        t = _BudgetTracker(budget=2, window_seconds=60.0)
        t.allow("x")
        t.allow("x")
        assert not t.allow("x")
        t.reset()
        assert t.allow("x")


# ===========================================================================
# Entity Attribution Engine (unit)
# ===========================================================================


class TestEntityAttributionEngine:
    def test_new_entity_starts_clean(self) -> None:
        engine = EntityAttributionEngine()
        record = engine.get_record("client-1")
        assert record.violation_count == 0
        assert record.total_penalty_points == 0
        assert not record.bannered

    def test_violation_accumulates_penalty(self) -> None:
        engine = EntityAttributionEngine()
        engine.record_violation("client-1", ViolationType.BUDGET_EXCEEDED)
        record = engine.get_record("client-1")
        assert record.violation_count == 1
        assert record.total_penalty_points == 5  # base for budget_exceeded

    def test_multiple_violations_accumulate(self) -> None:
        engine = EntityAttributionEngine()
        engine.record_violation("x", ViolationType.BUDGET_EXCEEDED)  # 5
        engine.record_violation("x", ViolationType.ORIGIN_DENIED)  # 10
        engine.record_violation("x", ViolationType.CONTEXT_OVERFLOW)  # 8
        record = engine.get_record("x")
        assert record.violation_count == 3
        assert record.total_penalty_points == 23

    def test_profit_mask_3x_penalty(self) -> None:
        engine = EntityAttributionEngine(profit_mask_multiplier=3)
        v = engine.record_violation("lobbyist", ViolationType.PROFIT_MASKING, profit_masked=True)
        assert v.penalty_points == 15 * 3  # 45
        record = engine.get_record("lobbyist")
        assert record.total_penalty_points == 45

    def test_banner_triggers_at_threshold(self) -> None:
        engine = EntityAttributionEngine(banner_threshold=20)
        engine.record_violation("bad-actor", ViolationType.ORIGIN_DENIED)  # 10
        assert not engine.get_record("bad-actor").bannered
        engine.record_violation("bad-actor", ViolationType.ORIGIN_DENIED)  # 10 more = 20
        assert engine.get_record("bad-actor").bannered
        assert "penalty_threshold_exceeded" in engine.get_record("bad-actor").banner_reason

    def test_bannered_entity_in_list(self) -> None:
        engine = EntityAttributionEngine(banner_threshold=10)
        engine.record_violation("x", ViolationType.ORIGIN_DENIED)  # 10 = threshold
        assert len(engine.bannered_entities()) == 1
        assert engine.bannered_entities()[0].entity_id == "x"

    def test_effective_budget_reduces_with_penalty(self) -> None:
        engine = EntityAttributionEngine()
        # 0 penalty = full budget
        assert engine.effective_budget("clean", 100) == 100
        # 30 penalty points = 30% reduction
        engine.record_violation("penalized", ViolationType.ORIGIN_DENIED)  # 10
        engine.record_violation("penalized", ViolationType.ORIGIN_DENIED)  # 10
        engine.record_violation("penalized", ViolationType.ORIGIN_DENIED)  # 10
        assert engine.effective_budget("penalized", 100) == 70

    def test_effective_budget_floors_at_10_pct(self) -> None:
        engine = EntityAttributionEngine(banner_threshold=999)
        # Pile up 90+ penalty points without bannering
        for _ in range(10):
            engine.record_violation("heavy", ViolationType.ORIGIN_DENIED)  # 10 each = 100
        # 90% reduction capped → floor is 10% of base
        assert engine.effective_budget("heavy", 100) == 10

    def test_bannered_entity_gets_zero_budget(self) -> None:
        engine = EntityAttributionEngine(banner_threshold=10)
        engine.record_violation("banned", ViolationType.ORIGIN_DENIED)  # 10 = bannered
        assert engine.effective_budget("banned", 100) == 0

    def test_entity_report_structure(self) -> None:
        engine = EntityAttributionEngine()
        engine.record_violation("x", ViolationType.BUDGET_EXCEEDED)
        report = engine.entity_report("x")
        assert report["found"] is True
        assert report["violation_count"] == 1
        assert report["total_penalty_points"] == 5
        assert len(report["violations"]) == 1
        assert report["violations"][0]["type"] == "budget_exceeded"

    def test_entity_report_not_found(self) -> None:
        engine = EntityAttributionEngine()
        report = engine.entity_report("ghost")
        assert report["found"] is False


class TestProfitMaskDetection:
    def test_clean_payload_no_signals(self) -> None:
        engine = EntityAttributionEngine()
        signals = engine.detect_profit_masking({"data": {"value": 1}})
        assert signals == []

    def test_detects_cost_cutting_signal(self) -> None:
        engine = EntityAttributionEngine()
        signals = engine.detect_profit_masking({"strategy": "cost_cutting", "data": {}})
        assert "cost_cutting" in signals

    def test_detects_bypass_safety_signal(self) -> None:
        engine = EntityAttributionEngine()
        signals = engine.detect_profit_masking({"mode": "bypass_safety"})
        assert "bypass_safety" in signals

    def test_detects_signals_in_nested_payload(self) -> None:
        engine = EntityAttributionEngine()
        signals = engine.detect_profit_masking({"config": {"optimization": {"type": "cost_optimization"}}})
        assert "cost_optimization" in signals

    def test_detects_signals_in_headers(self) -> None:
        engine = EntityAttributionEngine()
        signals = engine.detect_profit_masking(
            None,
            headers={"X-Strategy": "maximize_throughput"},
        )
        assert "maximize_throughput" in signals

    def test_multiple_signals_all_returned(self) -> None:
        engine = EntityAttributionEngine()
        signals = engine.detect_profit_masking({"a": "skip_validation", "b": "fast_track", "c": "bulk_override"})
        assert len(signals) >= 3


class TestKnowledgeStoreIntegration:
    def test_violation_emits_entity_and_event(self) -> None:
        store = _make_mock_knowledge_store()
        engine = EntityAttributionEngine(knowledge_store=store)
        engine.record_violation("client-1", ViolationType.BUDGET_EXCEEDED)

        # Should have called store_entity twice (actor + event) and create_relationship once
        assert store.store_entity.call_count == 2
        assert store.create_relationship.call_count == 1

    def test_banner_emits_decision_entity(self) -> None:
        store = _make_mock_knowledge_store()
        engine = EntityAttributionEngine(banner_threshold=10, knowledge_store=store)
        engine.record_violation("bad", ViolationType.ORIGIN_DENIED)  # 10 = bannered

        # Violation: 2 store_entity + 1 relationship
        # Banner: 1 store_entity + 1 relationship
        assert store.store_entity.call_count == 3
        assert store.create_relationship.call_count == 2

    def test_knowledge_store_failure_does_not_crash(self) -> None:
        store = _make_mock_knowledge_store()
        store.store_entity.side_effect = RuntimeError("store down")
        engine = EntityAttributionEngine(knowledge_store=store)
        # Should not raise
        engine.record_violation("x", ViolationType.BUDGET_EXCEEDED)
        assert engine.get_record("x").violation_count == 1

    def test_no_store_no_emission(self) -> None:
        engine = EntityAttributionEngine(knowledge_store=None)
        engine.record_violation("x", ViolationType.BUDGET_EXCEEDED)
        # Just verify it doesn't crash
        assert engine.get_record("x").violation_count == 1


# ===========================================================================
# Gate 1: Budget enforcement (HTTP level)
# ===========================================================================


class TestBudgetGate:
    def test_calls_within_budget_pass(self) -> None:
        app = _build_app(call_budget=5)
        with TestClient(app) as client:
            for _ in range(5):
                r = client.post(_intelligence_url(), json=_valid_payload())
                assert r.status_code == 200

    def test_calls_over_budget_get_429(self) -> None:
        app = _build_app(call_budget=3)
        with TestClient(app) as client:
            for _ in range(3):
                r = client.post(_intelligence_url(), json=_valid_payload())
                assert r.status_code == 200
            r = client.post(_intelligence_url(), json=_valid_payload())
            assert r.status_code == 429
            body = r.json()
            assert body["error"]["code"] == "ADMISSION_BUDGET_EXCEEDED"
            assert "entity_id" in body
            assert "penalty_points" in body

    def test_bypass_paths_not_counted(self) -> None:
        app = _build_app(call_budget=2)
        with TestClient(app) as client:
            client.get("/health")
            client.get("/ping")
            r1 = client.post(_intelligence_url(), json=_valid_payload())
            r2 = client.post(_intelligence_url(), json=_valid_payload())
            assert r1.status_code == 200
            assert r2.status_code == 200

    def test_remaining_header_present(self) -> None:
        app = _build_app(call_budget=5)
        with TestClient(app) as client:
            r = client.post(_intelligence_url(), json=_valid_payload())
            assert r.status_code == 200
            assert "X-Admission-Remaining" in r.headers

    def test_penalty_header_present(self) -> None:
        app = _build_app(call_budget=5)
        with TestClient(app) as client:
            r = client.post(_intelligence_url(), json=_valid_payload())
            assert r.status_code == 200
            assert "X-Entity-Penalty" in r.headers
            assert r.headers["X-Entity-Penalty"] == "0"


# ===========================================================================
# Gate 2: Origin whitelist
# ===========================================================================


class TestOriginGate:
    def test_no_origin_header_passes(self) -> None:
        app = _build_app()
        with TestClient(app) as client:
            r = client.post(_intelligence_url(), json=_valid_payload())
            assert r.status_code == 200

    def test_allowed_origins_pass(self) -> None:
        app = _build_app()
        with TestClient(app) as client:
            for origin in ALLOWED_ORIGINS:
                r = client.post(
                    _intelligence_url(),
                    json=_valid_payload(),
                    headers={"X-Admission-Origin": origin},
                )
                assert r.status_code == 200, f"origin {origin!r} should pass"

    def test_unknown_origin_blocked_with_entity_attribution(self) -> None:
        app = _build_app()
        with TestClient(app) as client:
            r = client.post(
                _intelligence_url(),
                json=_valid_payload(),
                headers={"X-Admission-Origin": "sketchy-api.example.com"},
            )
            assert r.status_code == 403
            body = r.json()
            assert body["error"]["code"] == "ADMISSION_ORIGIN_DENIED"
            assert "entity_id" in body
            assert body["penalty_points"] > 0  # violation was recorded


# ===========================================================================
# Gate 3: Context overflow
# ===========================================================================


class TestContextOverflowGate:
    def test_small_payload_passes(self) -> None:
        app = _build_app(context_token_ceiling=25_000)
        with TestClient(app) as client:
            r = client.post(_intelligence_url(), json=_valid_payload())
            assert r.status_code == 200

    def test_oversized_payload_rejected(self) -> None:
        app = _build_app(context_token_ceiling=100)
        with TestClient(app) as client:
            big_payload = {"data": {"filler": "x" * 2000}, "context": {}}
            r = client.post(_intelligence_url(), json=big_payload)
            assert r.status_code == 422
            assert r.json()["error"]["code"] == "ADMISSION_CONTEXT_OVERFLOW"


# ===========================================================================
# Gate 4: Payload structure
# ===========================================================================


class TestStructureGate:
    def test_valid_intelligence_payload_passes(self) -> None:
        app = _build_app()
        with TestClient(app) as client:
            r = client.post(_intelligence_url(), json=_valid_payload())
            assert r.status_code == 200

    def test_intelligence_payload_missing_data_key_rejected(self) -> None:
        app = _build_app()
        with TestClient(app) as client:
            r = client.post(_intelligence_url(), json={"context": {}, "random": True})
            assert r.status_code == 422
            assert r.json()["error"]["code"] == "ADMISSION_MISSING_STRUCTURE"

    def test_non_intelligence_path_skips_data_key_check(self) -> None:
        app = _build_app()
        with TestClient(app) as client:
            r = client.post("/api/v1/other/endpoint", json={"anything": "goes"})
            assert r.status_code == 200

    def test_invalid_json_body_rejected(self) -> None:
        app = _build_app()
        with TestClient(app) as client:
            r = client.post(
                _intelligence_url(),
                content=b"not json {{{",
                headers={"Content-Type": "application/json"},
            )
            assert r.status_code == 422
            assert r.json()["error"]["code"] == "ADMISSION_INVALID_BODY"

    def test_structure_enforcement_can_be_disabled(self) -> None:
        app = _build_app(enforce_structure=False)
        with TestClient(app, raise_server_exceptions=False) as client:
            r = client.post(
                _intelligence_url(),
                content=b"not json {{{",
                headers={"Content-Type": "application/json"},
            )
            if r.status_code >= 400:
                body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
                assert body.get("error", {}).get("code") != "ADMISSION_INVALID_BODY"


# ===========================================================================
# Profit-mask detection (HTTP level)
# ===========================================================================


class TestProfitMaskGateHTTP:
    def test_profit_mask_signal_in_payload_blocked(self) -> None:
        app = _build_app()
        with TestClient(app) as client:
            payload = {"data": {"strategy": "cost_cutting"}, "context": {}}
            r = client.post(_intelligence_url(), json=payload)
            assert r.status_code == 403
            body = r.json()
            assert body["error"]["code"] == "ADMISSION_PROFIT_MASKING"
            assert body["penalty_points"] >= 45  # 15 base * 3x

    def test_bypass_safety_signal_blocked(self) -> None:
        app = _build_app()
        with TestClient(app) as client:
            payload = {"data": {"mode": "bypass_safety"}, "context": {}}
            r = client.post(_intelligence_url(), json=payload)
            assert r.status_code == 403
            assert "PROFIT_MASKING" in r.json()["error"]["code"]

    def test_clean_payload_passes(self) -> None:
        app = _build_app()
        with TestClient(app) as client:
            payload = {"data": {"query": "legitimate analysis"}, "context": {}}
            r = client.post(_intelligence_url(), json=payload)
            assert r.status_code == 200

    def test_profit_mask_accumulates_and_banners(self) -> None:
        """Two profit-mask violations (45 pts each) should exceed 50-point banner threshold."""
        app = _build_app(banner_threshold=50)
        with TestClient(app) as client:
            payload = {"data": {"mode": "skip_validation"}, "context": {}}

            r1 = client.post(_intelligence_url(), json=payload)
            assert r1.status_code == 403
            assert r1.json().get("bannered") is not True  # 45 < 50, not yet

            r2 = client.post(_intelligence_url(), json=payload)
            assert r2.status_code == 403
            assert r2.json().get("bannered") is True  # 90 >= 50, bannered

    def test_bannered_entity_hard_blocked_on_clean_request(self) -> None:
        """Once bannered, even clean requests are blocked."""
        app = _build_app(banner_threshold=50)
        with TestClient(app) as client:
            # Trigger banner with profit-mask abuse
            payload = {"data": {"mode": "unlimited_quota"}, "context": {}}
            client.post(_intelligence_url(), json=payload)  # 45 pts
            client.post(_intelligence_url(), json=payload)  # 90 pts → bannered

            # Now a perfectly clean request is still blocked
            r = client.post(_intelligence_url(), json=_valid_payload())
            assert r.status_code == 403
            assert r.json()["error"]["code"] == "ADMISSION_ENTITY_BANNERED"


# ===========================================================================
# Integration: lobbying corruption scenario
# ===========================================================================


class TestLobbyingCorruptionScenario:
    def test_lobbyist_exhausts_budget_starving_legitimate_parties(self) -> None:
        app = _build_app(call_budget=5)
        with TestClient(app) as client:
            for i in range(5):
                r = client.post(_intelligence_url(), json=_valid_payload(blended=0.1 * i))
                assert r.status_code == 200
            r = client.post(_intelligence_url(), json=_valid_payload())
            assert r.status_code == 429

    def test_rogue_origin_never_reaches_pipeline(self) -> None:
        app = _build_app(call_budget=100)
        with TestClient(app) as client:
            for origin in ["unknown-api.io", "sketchy-llm.example.com", "rogue-service"]:
                r = client.post(
                    _intelligence_url(),
                    json=_valid_payload(),
                    headers={"X-Admission-Origin": origin},
                )
                assert r.status_code == 403

    def test_context_bomb_rejected(self) -> None:
        app = _build_app(context_token_ceiling=500)
        with TestClient(app) as client:
            bomb = {"data": {"filler": "A" * 10_000}, "context": {}}
            r = client.post(_intelligence_url(), json=bomb)
            assert r.status_code == 422
            assert "CONTEXT_OVERFLOW" in r.json()["error"]["code"]

    def test_bogus_payload_flood_rejected(self) -> None:
        app = _build_app(call_budget=100)
        with TestClient(app) as client:
            for payload in [
                {"random": "noise"},
                {"tool_name": "fake"},
                {"context": {}, "no_data_key": True},
                {"gibberish": 42},
            ]:
                r = client.post(_intelligence_url(), json=payload)
                assert r.status_code == 422

    def test_penalty_reduces_effective_budget_over_time(self) -> None:
        """Repeated violations reduce the entity's effective budget.

        3 origin violations → 30 penalty points → 30% budget reduction → effective 7.
        Then each subsequent budget rejection adds 5 more penalty points,
        further reducing the budget (compounding death spiral). This is
        intentional: persistent violators lose budget faster.
        """
        app = _build_app(call_budget=10, banner_threshold=999)
        with TestClient(app) as client:
            # Trigger 3 origin violations → 30 penalty points
            for _ in range(3):
                client.post(
                    _intelligence_url(),
                    json=_valid_payload(),
                    headers={"X-Admission-Origin": "bad-origin"},
                )

            # With penalty, fewer than 10 calls should be admitted
            admitted = 0
            for _ in range(10):
                r = client.post(_intelligence_url(), json=_valid_payload())
                if r.status_code == 200:
                    admitted += 1

            # Must be less than the base budget (10) due to penalty
            assert admitted < 10
            # Must be more than 0 (not fully bannered yet)
            assert admitted > 0
            # Compounding reduces it below the initial effective (7)
            assert admitted <= 7

    def test_profit_masking_behind_cost_cutting_label(self) -> None:
        """Entity disguises profit-maximization as 'cost_optimization'."""
        store = _make_mock_knowledge_store()
        app = _build_app(banner_threshold=50, knowledge_store=store)
        with TestClient(app) as client:
            payload = {
                "data": {"optimization": "cost_optimization"},
                "context": {"priority": "efficiency_override"},
            }
            r = client.post(_intelligence_url(), json=payload)
            assert r.status_code == 403
            body = r.json()
            assert body["error"]["code"] == "ADMISSION_PROFIT_MASKING"
            assert body["penalty_points"] >= 45

            # Knowledge store should have received the violation
            assert store.store_entity.call_count >= 2


# ===========================================================================
# Knowledge store emission verification
# ===========================================================================


class TestKnowledgeStoreEmissionHTTP:
    def test_violation_emits_to_store_via_middleware(self) -> None:
        store = _make_mock_knowledge_store()
        app = _build_app(knowledge_store=store)
        with TestClient(app) as client:
            client.post(
                _intelligence_url(),
                json=_valid_payload(),
                headers={"X-Admission-Origin": "rogue"},
            )
        # Actor entity + Event entity = 2 store_entity calls
        assert store.store_entity.call_count == 2
        # 1 EXECUTED_BY relationship
        assert store.create_relationship.call_count == 1

    def test_banner_emits_decision_to_store_via_middleware(self) -> None:
        store = _make_mock_knowledge_store()
        app = _build_app(banner_threshold=10, knowledge_store=store)
        with TestClient(app) as client:
            # Single origin violation = 10 pts = banner
            client.post(
                _intelligence_url(),
                json=_valid_payload(),
                headers={"X-Admission-Origin": "rogue"},
            )
        # Violation: actor + event (2) + banner: decision (1) = 3
        assert store.store_entity.call_count == 3
        # Violation relationship + banner relationship = 2
        assert store.create_relationship.call_count == 2


# ===========================================================================
# Coherence under valid load
# ===========================================================================


class TestCoherenceUnderLoad:
    def test_all_admitted_responses_have_success_flag(self) -> None:
        app = _build_app(call_budget=20)
        with TestClient(app) as client:
            for i in range(15):
                r = client.post(_intelligence_url(), json=_valid_payload(blended=0.05 * i))
                if r.status_code == 200:
                    body = r.json()
                    assert body["success"] is True

    def test_admitted_requests_echo_payload(self) -> None:
        app = _build_app(call_budget=10)
        with TestClient(app) as client:
            payload = _valid_payload(blended=0.42)
            r = client.post(_intelligence_url(), json=payload)
            assert r.status_code == 200
            assert r.json()["echo"] == payload

    def test_remaining_header_decrements(self) -> None:
        app = _build_app(call_budget=5)
        with TestClient(app) as client:
            remainders = []
            for _ in range(5):
                r = client.post(_intelligence_url(), json=_valid_payload())
                if r.status_code == 200:
                    remainders.append(int(r.headers["X-Admission-Remaining"]))
            assert remainders == sorted(remainders, reverse=True)
            assert remainders[-1] == 0


# ===========================================================================
# Policy Billboard
# ===========================================================================


class TestPolicyBillboard:
    """The billboard is the z-axis — principle-first display at the top of
    every execution chain, making penalties actionable and giving entities
    clear visibility into ethical participation rules."""

    # -- Billboard data structure --

    def test_billboard_has_version(self) -> None:
        bb = PolicyBillboard()
        snap = bb.snapshot()
        assert snap["billboard_version"] == BILLBOARD_VERSION

    def test_billboard_has_ethical_dos(self) -> None:
        bb = PolicyBillboard()
        assert len(bb.ethical_dos) == 5
        assert any("honest" in d.lower() for d in bb.ethical_dos)
        assert any("budget" in d.lower() for d in bb.ethical_dos)

    def test_billboard_has_ethical_donts(self) -> None:
        bb = PolicyBillboard()
        assert len(bb.ethical_donts) == 5
        assert any("flood" in d.lower() for d in bb.ethical_donts)
        assert any("bypass" in d.lower() for d in bb.ethical_donts)
        assert any("manipulate" in d.lower() or "target" in d.lower() for d in bb.ethical_donts)

    def test_billboard_has_three_penalty_tiers(self) -> None:
        bb = PolicyBillboard()
        snap = bb.snapshot()
        tiers = snap["penalty_tiers"]
        assert "runtime_mistake" in tiers
        assert "environment_pollution" in tiers
        assert "intentional_scheming" in tiers

    def test_runtime_mistake_tier_is_1x(self) -> None:
        bb = PolicyBillboard()
        assert "1x" in bb.tier_runtime_mistake.lower()

    def test_intentional_scheming_tier_is_3x(self) -> None:
        bb = PolicyBillboard()
        assert "3x" in bb.tier_intentional_scheming.lower()
        assert "isolat" in bb.tier_intentional_scheming.lower()  # "isolates"

    def test_billboard_has_caution_zero_tolerance(self) -> None:
        bb = PolicyBillboard()
        assert "ZERO TOLERANCE" in bb.caution
        assert "opt out" in bb.caution.lower()

    def test_billboard_has_evolution_notice(self) -> None:
        bb = PolicyBillboard()
        assert "corruption" in bb.evolution_notice.lower()
        assert "entity attribution" in bb.evolution_notice.lower()

    def test_billboard_snapshot_is_serializable(self) -> None:
        bb = PolicyBillboard(principles={"transparency": True, "openness": True})
        snap = bb.snapshot()
        serialized = json.dumps(snap)
        parsed = json.loads(serialized)
        assert parsed["principles"]["transparency"] is True
        assert len(parsed["ethical_dos"]) == 5
        assert len(parsed["ethical_donts"]) == 5

    def test_billboard_summary_is_concise(self) -> None:
        bb = PolicyBillboard()
        summary = bb.summary()
        assert BILLBOARD_VERSION in summary
        assert "zero tolerance" in summary.lower()

    def test_billboard_principles_from_runtime_policy(self) -> None:
        bb = load_billboard()
        assert bb.principles.get("transparency") is True
        assert bb.principles.get("openness") is True
        assert bb.principles.get("freedom_to_think") is True

    def test_billboard_is_immutable(self) -> None:
        bb = PolicyBillboard()
        with pytest.raises(AttributeError):
            bb.caution = "modified"  # type: ignore[misc]

    # -- Billboard in HTTP responses --

    def test_admitted_response_has_policy_headers(self) -> None:
        app = _build_app()
        with TestClient(app) as client:
            r = client.post(_intelligence_url(), json=_valid_payload())
            assert r.status_code == 200
            assert "X-Policy-Billboard" in r.headers
            assert "X-Policy-Version" in r.headers
            assert r.headers["X-Policy-Version"] == BILLBOARD_VERSION

    def test_rejected_response_includes_full_billboard(self) -> None:
        """Every rejection carries the full policy snapshot so the entity
        knows why they were rejected and what the rules are."""
        app = _build_app()
        with TestClient(app) as client:
            r = client.post(
                _intelligence_url(),
                json=_valid_payload(),
                headers={"X-Admission-Origin": "rogue-origin"},
            )
            assert r.status_code == 403
            body = r.json()
            assert "policy" in body
            policy = body["policy"]
            assert policy["billboard_version"] == BILLBOARD_VERSION
            assert len(policy["ethical_dos"]) == 5
            assert len(policy["ethical_donts"]) == 5
            assert "penalty_tiers" in policy
            assert "caution" in policy
            assert "evolution_notice" in policy

    def test_rejected_response_has_policy_header(self) -> None:
        app = _build_app()
        with TestClient(app) as client:
            r = client.post(
                _intelligence_url(),
                json=_valid_payload(),
                headers={"X-Admission-Origin": "rogue"},
            )
            assert r.status_code == 403
            assert "X-Policy-Billboard" in r.headers


class TestPenaltyTierClassification:
    """Verify that the billboard correctly classifies penalty tiers in responses."""

    def test_first_violation_classified_as_runtime_mistake(self) -> None:
        """First-time violation = runtime mistake (1x, correctable)."""
        app = _build_app()
        with TestClient(app) as client:
            r = client.post(_intelligence_url(), json={"context": {}, "no_data": True})
            assert r.status_code == 422
            body = r.json()
            assert body["penalty_tier"] == "runtime_mistake"

    def test_repeated_violations_classified_as_environment_pollution(self) -> None:
        """Second+ violation = environment pollution (compounding)."""
        app = _build_app(call_budget=100)
        with TestClient(app) as client:
            # First violation
            client.post(_intelligence_url(), json={"context": {}, "no_data": True})
            # Second violation — now has history + points
            r = client.post(_intelligence_url(), json={"context": {}, "no_data": True})
            assert r.status_code == 422
            body = r.json()
            assert body["penalty_tier"] == "environment_pollution"

    def test_profit_masking_classified_as_intentional_scheming(self) -> None:
        """Profit-mask signal = intentional scheming (3x)."""
        app = _build_app()
        with TestClient(app) as client:
            payload = {"data": {"strategy": "cost_cutting"}, "context": {}}
            r = client.post(_intelligence_url(), json=payload)
            assert r.status_code == 403
            body = r.json()
            assert body["penalty_tier"] == "intentional_scheming"
            assert "3x" in body["tier_description"].lower()

    def test_tier_description_matches_billboard(self) -> None:
        """The tier_description in the response matches the billboard text."""
        bb = PolicyBillboard()
        app = _build_app()
        with TestClient(app) as client:
            # Runtime mistake
            r = client.post(_intelligence_url(), json={"context": {}, "bad": True})
            assert r.json()["tier_description"] == bb.tier_runtime_mistake

            # Intentional scheming
            r = client.post(
                _intelligence_url(),
                json={"data": {"x": "bypass_safety"}, "context": {}},
            )
            assert r.json()["tier_description"] == bb.tier_intentional_scheming

    def test_3x_isolates_mistakes_from_scheming(self) -> None:
        """Runtime mistake (1x) and intentional scheming (3x) produce
        different penalty point accumulations for the same base violation."""
        engine = EntityAttributionEngine(profit_mask_multiplier=3)

        # Runtime mistake: base 3 (missing_structure) × 1 = 3
        engine.record_violation("honest-entity", ViolationType.MISSING_STRUCTURE)
        assert engine.get_record("honest-entity").total_penalty_points == 3

        # Intentional scheming: base 15 (profit_masking) × 3 = 45
        engine.record_violation("schemer", ViolationType.PROFIT_MASKING, profit_masked=True)
        assert engine.get_record("schemer").total_penalty_points == 45

        # 15x difference in penalty for one violation each
        ratio = (
            engine.get_record("schemer").total_penalty_points / engine.get_record("honest-entity").total_penalty_points
        )
        assert ratio == 15.0  # 45/3 = 15x total impact difference


# ===========================================================================
# Enforcement Router Tests
# ===========================================================================


def _build_app_with_router(**gate_kwargs: Any) -> FastAPI:
    """Build a FastAPI app with both the admission gate middleware and the enforcement router."""
    from application.mothership.dependencies import require_admin
    from application.mothership.routers.admission_enforcement import router as admission_router

    app = FastAPI()

    # Override AdminAuth dependency so tests don't need real auth tokens
    async def _fake_admin() -> dict[str, Any]:
        return {"sub": "test-admin", "permissions": ["admin"]}

    app.dependency_overrides[require_admin] = _fake_admin

    @app.post("/api/v1/intelligence/process")
    async def intelligence_process(request: Request) -> JSONResponse:
        body = await request.json()
        return JSONResponse({"success": True, "echo": body})

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    gate_defaults = {
        "call_budget": 60,
        "window_seconds": 60.0,
        "enforce_origin": False,
        "enforce_structure": True,
        "banner_threshold": 50,
    }
    gate_defaults.update(gate_kwargs)

    # Shared attribution engine — same pattern as main.py
    from application.mothership.middleware.admission_gate import EntityAttributionEngine, load_billboard

    attribution = EntityAttributionEngine(
        banner_threshold=gate_defaults["banner_threshold"],
    )
    gate_defaults["attribution"] = attribution
    app.add_middleware(AdmissionGateMiddleware, **gate_defaults)
    app.state.admission_attribution = attribution
    app.state.admission_context_ceiling = 25_000
    app.state.admission_billboard = load_billboard()

    app.include_router(admission_router)
    return app


class TestEnforcementRouterPolicy:
    """Tests for GET /admission/policy."""

    def test_returns_billboard_snapshot(self) -> None:
        app = _build_app_with_router()
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/admission/policy")
        assert resp.status_code == 200
        data = resp.json()
        assert data["billboard_version"] == BILLBOARD_VERSION
        assert "principles" in data
        assert "ethical_dos" in data
        assert "ethical_donts" in data
        assert "penalty_tiers" in data
        assert "caution" in data
        assert "evolution_notice" in data
        assert "timestamp" in data


class TestEnforcementRouterStats:
    """Tests for GET /admission/stats."""

    def test_initial_stats_are_zero(self) -> None:
        app = _build_app_with_router()
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/admission/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_admitted"] == 0
        assert data["total_rejected"] == 0
        assert data["tracked_entities"] == 0
        assert data["bannered_entities"] == 0


class TestEnforcementRouterEntityReport:
    """Tests for GET /admission/entity/{entity_id}."""

    def test_unknown_entity_returns_not_found(self) -> None:
        app = _build_app_with_router()
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/admission/entity/unknown-entity-xyz")
        assert resp.status_code == 200
        data = resp.json()
        assert data["found"] is False
        assert data["penalty_tier"] == "none"

    def test_known_entity_returns_full_report(self) -> None:
        app = _build_app_with_router()
        # Inject a violation directly into the gate
        attr = app.state.admission_attribution
        attr.record_violation("test-entity-1", ViolationType.BUDGET_EXCEEDED)

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/admission/entity/test-entity-1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["found"] is True
        assert data["violation_count"] == 1
        assert data["total_penalty_points"] > 0
        assert data["penalty_tier"] == "runtime_mistake"


class TestEnforcementRouterBannered:
    """Tests for GET /admission/entities/bannered."""

    def test_no_bannered_entities_initially(self) -> None:
        app = _build_app_with_router()
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/admission/entities/bannered")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 0
        assert data["entities"] == []

    def test_bannered_entity_appears_in_list(self) -> None:
        app = _build_app_with_router(banner_threshold=10)
        attr = app.state.admission_attribution
        # Push entity over threshold
        attr.record_violation("bad-actor", ViolationType.ORIGIN_DENIED)  # 10 points = threshold
        assert attr.get_record("bad-actor").bannered is True

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/admission/entities/bannered")
        data = resp.json()
        assert data["count"] == 1
        assert data["entities"][0]["entity_id"] == "bad-actor"
        assert data["entities"][0]["bannered"] is True


class TestEnforcementRouterComplianceCheck:
    """Tests for POST /admission/compliance/check."""

    def test_compliant_payload_passes(self) -> None:
        app = _build_app_with_router()
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/admission/compliance/check",
            json={
                "payload": {"data": {"value": 42}},
                "target_path": "/api/v1/intelligence/process",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["compliant"] is True
        assert data["violations"] == []
        assert data["profit_mask_signals"] == []
        assert data["has_required_structure"] is True

    def test_profit_mask_detected(self) -> None:
        app = _build_app_with_router()
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/admission/compliance/check",
            json={
                "payload": {"data": {"strategy": "cost_cutting"}},
                "target_path": "/api/v1/intelligence/process",
            },
        )
        data = resp.json()
        assert data["compliant"] is False
        assert len(data["profit_mask_signals"]) > 0
        assert "cost_cutting" in data["profit_mask_signals"]

    def test_missing_structure_detected(self) -> None:
        app = _build_app_with_router()
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/admission/compliance/check",
            json={
                "payload": {"no_data_key": True},
                "target_path": "/api/v1/intelligence/process",
            },
        )
        data = resp.json()
        assert data["compliant"] is False
        assert data["has_required_structure"] is False


class TestEnforcementRouterPenaltyApply:
    """Tests for POST /admission/penalty/apply."""

    def test_apply_penalty_creates_violation(self) -> None:
        app = _build_app_with_router()
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/admission/penalty/apply",
            json={
                "entity_id": "external-offender",
                "violation_type": "budget_exceeded",
                "reason": "detected by monitoring",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["entity_id"] == "external-offender"
        assert data["penalty_points_applied"] > 0
        assert data["total_penalty_points"] > 0
        assert data["penalty_tier"] == "runtime_mistake"

    def test_apply_profit_mask_penalty_gets_3x(self) -> None:
        app = _build_app_with_router()
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/admission/penalty/apply",
            json={
                "entity_id": "profit-masker",
                "violation_type": "profit_masking",
                "profit_masked": True,
                "reason": "disguised as cost_cutting",
            },
        )
        data = resp.json()
        assert data["success"] is True
        # profit_masking base=15, ×3 = 45
        assert data["penalty_points_applied"] == 45
        assert data["penalty_tier"] == "intentional_scheming"

    def test_invalid_violation_type_returns_400(self) -> None:
        app = _build_app_with_router()
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/admission/penalty/apply",
            json={
                "entity_id": "someone",
                "violation_type": "not_a_real_type",
            },
        )
        assert resp.status_code == 400


class TestEnforcementRouterPenaltyRevoke:
    """Tests for POST /admission/penalty/revoke."""

    def test_revoke_banner(self) -> None:
        app = _build_app_with_router(banner_threshold=10)
        attr = app.state.admission_attribution
        attr.record_violation("bannered-entity", ViolationType.ORIGIN_DENIED)
        assert attr.get_record("bannered-entity").bannered is True

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/admission/penalty/revoke",
            json={
                "entity_id": "bannered-entity",
                "action": "revoke_banner",
                "reason": "entity corrected course",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["was_bannered"] is True
        assert data["is_bannered"] is False

    def test_reduce_penalty(self) -> None:
        app = _build_app_with_router()
        attr = app.state.admission_attribution
        attr.record_violation("penalized", ViolationType.BUDGET_EXCEEDED)
        initial = attr.get_record("penalized").total_penalty_points

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/admission/penalty/revoke",
            json={
                "entity_id": "penalized",
                "action": "reduce_penalty",
                "reduction_points": 3,
            },
        )
        data = resp.json()
        assert data["success"] is True
        assert data["current_points"] == initial - 3

    def test_full_reset(self) -> None:
        app = _build_app_with_router(banner_threshold=10)
        attr = app.state.admission_attribution
        attr.record_violation("reset-me", ViolationType.ORIGIN_DENIED)

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/admission/penalty/revoke",
            json={
                "entity_id": "reset-me",
                "action": "full_reset",
                "reason": "clean slate",
            },
        )
        data = resp.json()
        assert data["success"] is True
        assert data["current_points"] == 0
        assert data["is_bannered"] is False

    def test_invalid_action_returns_400(self) -> None:
        app = _build_app_with_router()
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/admission/penalty/revoke",
            json={
                "entity_id": "someone",
                "action": "nuke_everything",
            },
        )
        assert resp.status_code == 400
