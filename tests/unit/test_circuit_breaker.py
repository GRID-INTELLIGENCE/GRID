"""Tests for circuit_breaker.py — Circuit state machine, manager, and middleware."""

from __future__ import annotations

import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from application.mothership.middleware.circuit_breaker import (
    Circuit,
    CircuitBreakerManager,
    CircuitBreakerMiddleware,
    CircuitConfig,
    CircuitState,
    FailureType,
    reset_circuit_manager,
)


@pytest.fixture(autouse=True)
def reset_cb():
    reset_circuit_manager()
    yield
    reset_circuit_manager()


# ---------------------------------------------------------------------------
# Circuit state machine unit tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCircuitStateMachine:
    def _circuit(self, **kwargs: object) -> Circuit:
        config = CircuitConfig(failure_threshold=3, recovery_timeout_seconds=30.0, **kwargs)
        return Circuit(key="test", config=config)

    def test_starts_closed(self) -> None:
        c = self._circuit()
        assert c.state == CircuitState.CLOSED

    def test_closed_allows_all_requests(self) -> None:
        c = self._circuit()
        assert c.should_allow_request() is True

    def test_failures_below_threshold_keep_circuit_closed(self) -> None:
        c = self._circuit()
        c.record_failure(FailureType.SERVER_ERROR, status_code=500)
        c.record_failure(FailureType.SERVER_ERROR, status_code=500)
        assert c.state == CircuitState.CLOSED

    def test_failures_at_threshold_open_circuit(self) -> None:
        c = self._circuit()
        for _ in range(3):
            c.record_failure(FailureType.SERVER_ERROR, status_code=500)
        assert c.state == CircuitState.OPEN

    def test_open_circuit_rejects_requests(self) -> None:
        c = self._circuit()
        for _ in range(3):
            c.record_failure(FailureType.SERVER_ERROR, status_code=500)
        assert c.should_allow_request() is False

    def test_open_circuit_transitions_to_half_open_after_timeout(self) -> None:
        c = self._circuit(recovery_timeout_seconds=0.01)
        for _ in range(3):
            c.record_failure(FailureType.SERVER_ERROR, status_code=500)
        assert c.state == CircuitState.OPEN
        time.sleep(0.02)
        result = c.should_allow_request()
        assert result is True
        assert c.state == CircuitState.HALF_OPEN

    def test_half_open_limits_concurrent_requests(self) -> None:
        c = self._circuit(recovery_timeout_seconds=0.01, half_open_max_requests=2)
        for _ in range(3):
            c.record_failure(FailureType.SERVER_ERROR, status_code=500)
        time.sleep(0.02)
        c.should_allow_request()  # triggers transition to HALF_OPEN
        c.half_open_requests = 2  # simulate two in-flight
        assert c.should_allow_request() is False

    def test_successes_in_half_open_close_circuit(self) -> None:
        c = self._circuit(recovery_timeout_seconds=0.01, success_threshold=2)
        for _ in range(3):
            c.record_failure(FailureType.SERVER_ERROR, status_code=500)
        time.sleep(0.02)
        c.should_allow_request()  # OPEN → HALF_OPEN
        c.record_success()
        assert c.state == CircuitState.HALF_OPEN
        c.record_success()
        assert c.state == CircuitState.CLOSED

    def test_failure_in_half_open_reopens_circuit(self) -> None:
        c = self._circuit(recovery_timeout_seconds=0.01)
        for _ in range(3):
            c.record_failure(FailureType.SERVER_ERROR, status_code=500)
        time.sleep(0.02)
        c.should_allow_request()  # OPEN → HALF_OPEN
        c.record_failure(FailureType.SERVER_ERROR, status_code=500)
        assert c.state == CircuitState.OPEN

    def test_force_open_and_close(self) -> None:
        c = self._circuit()
        c.force_open()
        assert c.state == CircuitState.OPEN
        c.force_close()
        assert c.state == CircuitState.CLOSED

    def test_reset_clears_state(self) -> None:
        c = self._circuit()
        for _ in range(3):
            c.record_failure(FailureType.SERVER_ERROR, status_code=500)
        c.reset()
        assert c.state == CircuitState.CLOSED
        assert c.failures == []

    def test_success_metrics_tracked(self) -> None:
        c = self._circuit()
        c.record_success()
        assert c.metrics.total_requests == 1
        assert c.metrics.successful_requests == 1

    def test_failure_metrics_tracked(self) -> None:
        c = self._circuit()
        c.record_failure(FailureType.TIMEOUT, error_message="timed out")
        assert c.metrics.failed_requests == 1
        assert c.metrics.last_failure_time is not None

    def test_rejection_metrics_tracked(self) -> None:
        c = self._circuit()
        c.record_rejection()
        assert c.metrics.rejected_requests == 1

    def test_old_failures_pruned_outside_window(self) -> None:
        c = self._circuit(failure_window_seconds=0.01)
        c.record_failure(FailureType.SERVER_ERROR, status_code=500)
        c.record_failure(FailureType.SERVER_ERROR, status_code=500)
        time.sleep(0.02)
        # Third failure — window pruning should clear the old two
        c.record_failure(FailureType.SERVER_ERROR, status_code=500)
        # Should still be closed because effective window-count is 1
        assert c.state == CircuitState.CLOSED

    def test_to_dict_contains_expected_keys(self) -> None:
        c = self._circuit()
        d = c.to_dict()
        assert "state" in d
        assert "failure_count" in d
        assert "metrics" in d


# ---------------------------------------------------------------------------
# CircuitBreakerManager
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCircuitBreakerManager:
    def test_get_circuit_creates_new(self) -> None:
        manager = CircuitBreakerManager()
        c = manager.get_circuit("my-service")
        assert c.key == "my-service"
        assert c.state == CircuitState.CLOSED

    def test_get_circuit_returns_same_instance(self) -> None:
        manager = CircuitBreakerManager()
        c1 = manager.get_circuit("svc")
        c2 = manager.get_circuit("svc")
        assert c1 is c2

    def test_reset_circuit(self) -> None:
        manager = CircuitBreakerManager()
        c = manager.get_circuit("svc")
        c.force_open()
        assert manager.reset_circuit("svc") is True
        assert manager.get_circuit("svc").state == CircuitState.CLOSED

    def test_reset_circuit_missing_key(self) -> None:
        manager = CircuitBreakerManager()
        assert manager.reset_circuit("nonexistent") is False

    def test_reset_all_circuits(self) -> None:
        manager = CircuitBreakerManager()
        manager.get_circuit("a").force_open()
        manager.get_circuit("b").force_open()
        count = manager.reset_all_circuits()
        assert count == 2
        assert manager.get_circuit("a").state == CircuitState.CLOSED

    def test_force_open_circuit(self) -> None:
        manager = CircuitBreakerManager()
        manager.get_circuit("svc")
        assert manager.force_open_circuit("svc") is True
        assert manager.get_circuit("svc").state == CircuitState.OPEN

    def test_force_close_circuit(self) -> None:
        manager = CircuitBreakerManager()
        manager.get_circuit("svc").force_open()
        assert manager.force_close_circuit("svc") is True
        assert manager.get_circuit("svc").state == CircuitState.CLOSED

    def test_get_metrics_aggregates(self) -> None:
        manager = CircuitBreakerManager()
        manager.get_circuit("a").force_open()
        metrics = manager.get_metrics()
        assert metrics["total_circuits"] == 1
        assert metrics["open_circuits"] == 1

    def test_get_all_circuits(self) -> None:
        manager = CircuitBreakerManager()
        manager.get_circuit("x")
        manager.get_circuit("y")
        circuits = manager.get_all_circuits()
        assert set(circuits.keys()) == {"x", "y"}


# ---------------------------------------------------------------------------
# CircuitBreakerMiddleware
# ---------------------------------------------------------------------------


def _make_app(
    *,
    failure_threshold: int = 3,
    recovery_timeout: float = 30.0,
    excluded_paths: list[str] | None = None,
    fail_route: bool = False,
) -> FastAPI:
    app = FastAPI()

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/api/success")
    def success():
        return {"ok": True}

    @app.get("/api/fail")
    def fail_endpoint():
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=500, content={"error": "server error"})

    app.add_middleware(
        CircuitBreakerMiddleware,
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        excluded_paths=excluded_paths or ["/health", "/ping", "/metrics"],
    )
    return app


@pytest.mark.unit
class TestCircuitBreakerMiddleware:
    def test_excluded_path_bypasses_circuit_breaker(self) -> None:
        client = TestClient(_make_app(), raise_server_exceptions=False)
        r = client.get("/health")
        assert r.status_code == 200
        # No X-Circuit-State header for excluded paths
        assert "X-Circuit-State" not in r.headers

    def test_successful_request_adds_circuit_state_header(self) -> None:
        client = TestClient(_make_app(), raise_server_exceptions=False)
        r = client.get("/api/success")
        assert r.status_code == 200
        assert r.headers.get("X-Circuit-State") == "closed"

    def test_5xx_responses_count_as_failures(self) -> None:
        app = _make_app(failure_threshold=2)
        client = TestClient(app, raise_server_exceptions=False)
        client.get("/api/fail")
        client.get("/api/fail")
        # Third request should find circuit OPEN
        r = client.get("/api/fail")
        assert r.status_code == 503
        body = r.json()
        assert body["error"]["code"] == "CIRCUIT_OPEN"

    def test_open_circuit_returns_503(self) -> None:
        app = _make_app(failure_threshold=2)
        client = TestClient(app, raise_server_exceptions=False)
        for _ in range(2):
            client.get("/api/fail")
        r = client.get("/api/success")
        assert r.status_code == 503
        assert "Retry-After" in r.headers
        assert r.headers["X-Circuit-State"] == "open"

    def test_successful_requests_keep_circuit_closed(self) -> None:
        client = TestClient(_make_app(), raise_server_exceptions=False)
        for _ in range(5):
            r = client.get("/api/success")
            assert r.status_code == 200
            assert r.headers.get("X-Circuit-State") == "closed"

    def test_circuit_key_granularity_path(self) -> None:
        """Different paths have independent circuits."""
        app = _make_app(failure_threshold=2)

        @app.get("/api/other")
        def other():
            return {"ok": True}

        client = TestClient(app, raise_server_exceptions=False)
        # Exhaust /api/fail circuit
        client.get("/api/fail")
        client.get("/api/fail")
        # /api/other should still be healthy
        r = client.get("/api/other")
        assert r.status_code == 200
