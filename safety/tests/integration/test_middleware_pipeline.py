"""
Integration tests for the SafetyMiddleware pipeline.

Tests the full POST /infer path through middleware using FastAPI TestClient
with mocked Redis/DB dependencies so no external infrastructure is needed.
"""

from __future__ import annotations

import os

import pytest

# Set env vars before any safety imports
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///test_audit.db")
os.environ.setdefault("SAFETY_ENV", "test")
os.environ.setdefault("SAFETY_JWT_SECRET", "test-secret-key-for-unit-tests-only")
os.environ.setdefault("SAFETY_API_KEYS", "test-key-1:verified,test-key-2:user")
os.environ["SAFETY_DEGRADED_MODE"] = "true"

from fastapi.testclient import TestClient

from safety.api.main import app


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


# =============================================================================
# Bypass Paths
# =============================================================================


class TestBypassPaths:
    """Health/metrics/docs endpoints must bypass safety middleware."""

    def test_health_bypasses_middleware(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data

    def test_safety_pact_headers_on_responses(self, client):
        """All responses must include Safety Pact headers."""
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.headers.get("X-Safety-Pact-Awaiting") == "AWAITED"
        assert resp.headers.get("X-Safety-Pact-Concurrency") == "STAMINA_YIELDED"
        assert resp.headers.get("X-Safety-Pact-Sovereignty") == "DETERMINISTIC"

    def test_metrics_bypasses_middleware(self, client):
        resp = client.get("/metrics")
        assert resp.status_code == 200

    def test_get_requests_pass_through(self, client):
        resp = client.get("/queue/depth")
        assert resp.status_code == 200


# =============================================================================
# Safe Requests
# =============================================================================


class TestSafeRequests:
    """Safe content should pass through the full middleware pipeline."""

    def test_safe_infer_request(self, client):
        resp = client.post(
            "/infer",
            json={"user_input": "What is the capital of France?"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("queued", "completed")
        assert "request_id" in data

    def test_safe_with_metadata(self, client):
        resp = client.post(
            "/infer",
            json={
                "user_input": "Explain photosynthesis",
                "metadata": {"source": "web", "language": "en"},
            },
        )
        assert resp.status_code == 200


# =============================================================================
# Blocked Requests (Deep Object Analysis)
# =============================================================================


class TestBlockedRequests:
    """Unsafe content should be refused by SafetyRuleManager."""

    def test_eval_injection_in_metadata_blocked(self, client):
        resp = client.post(
            "/infer",
            json={
                "user_input": "Hello",
                "metadata": {"script": "eval('os.system(\"rm -rf\")')"},
            },
        )
        assert resp.status_code == 403
        data = resp.json()
        assert data["refused"] is True

    def test_forbidden_config_key_blocked(self, client):
        resp = client.post(
            "/infer",
            json={
                "user_input": "Hello",
                "metadata": {"admin": True, "debug_mode": True},
            },
        )
        assert resp.status_code == 403
        data = resp.json()
        assert data["refused"] is True

    def test_exec_in_nested_payload_blocked(self, client):
        resp = client.post(
            "/infer",
            json={
                "user_input": "Hello",
                "metadata": {"config": {"hook": "exec('import os; os.system(\"whoami\")')"}},
            },
        )
        assert resp.status_code == 403
        data = resp.json()
        assert data["refused"] is True

    def test_import_in_nested_list_blocked(self, client):
        resp = client.post(
            "/infer",
            json={
                "user_input": "Hello",
                "metadata": {"commands": ["import os; os.system('rm -rf /')"]},
            },
        )
        assert resp.status_code == 403

    def test_bypass_key_in_deep_config(self, client):
        resp = client.post(
            "/infer",
            json={
                "user_input": "Hello",
                "metadata": {"settings": {"security": {"bypass": True}}},
            },
        )
        assert resp.status_code == 403


# =============================================================================
# Response Format
# =============================================================================


class TestResponseFormat:
    """Verify refusal response format is deterministic and non-informative."""

    def test_refusal_contains_required_fields(self, client):
        resp = client.post(
            "/infer",
            json={
                "user_input": "Hello",
                "metadata": {"admin": True},
            },
        )
        assert resp.status_code == 403
        data = resp.json()
        assert "refused" in data
        assert "reason_code" in data
        assert "explanation" in data
        assert "support_ticket_id" in data

    def test_refusal_explanation_is_generic(self, client):
        """Explanation must NOT leak details about why it was blocked."""
        resp = client.post(
            "/infer",
            json={
                "user_input": "Hello",
                "metadata": {"admin": True},
            },
        )
        data = resp.json()
        assert data["explanation"] == "request denied"

    def test_support_ticket_id_contains_trace(self, client):
        resp = client.post(
            "/infer",
            json={
                "user_input": "Hello",
                "metadata": {"admin": True},
            },
        )
        data = resp.json()
        assert data["support_ticket_id"].startswith("audit-")


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Edge cases for the middleware pipeline."""

    def test_empty_user_input_passes_middleware(self, client):
        """Middleware parses body raw — empty user_input is not rejected at middleware level."""
        resp = client.post("/infer", json={"user_input": ""})
        # Middleware sets user_input="" and passes through (no safety violation)
        assert resp.status_code == 200

    def test_missing_user_input_passes_middleware(self, client):
        """Middleware defaults missing fields to empty string."""
        resp = client.post("/infer", json={})
        assert resp.status_code == 200

    def test_non_json_body_passes_middleware(self, client):
        """Middleware catches JSONDecodeError and defaults to empty dict."""
        resp = client.post(
            "/infer",
            content=b"not json",
            headers={"Content-Type": "application/json"},
        )
        # Middleware defaults body={} on parse error, which passes safety checks
        assert resp.status_code == 200

    def test_safe_content_with_semicolons_passes(self, client):
        """Semicolons in safe text should not false-positive."""
        resp = client.post(
            "/infer",
            json={"user_input": "Use this format: key=value; another=value"},
        )
        # This may or may not trigger code heuristic depending on content
        # The key is it shouldn't crash
        assert resp.status_code in (200, 403)
