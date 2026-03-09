"""
Phase 4 — Security-focused tests for attack surface guardrails.

Covers: agentic auth required, dev token rejected when env disabled,
sandbox suspicious-pattern detection, webhook signature rejection,
validate_url_allowlist for outbound HTTP (SSRF mitigation).
"""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from application.mothership.main import create_app
from application.mothership.utils import validate_url_allowlist
from grid.skills.sandbox import SandboxConfig, SkillsSandbox


class TestAgenticRoutesRequireAuth:
    """Agentic routes must return 401 when no valid auth is provided."""

    def test_agentic_cases_post_requires_auth(self):
        """POST /api/v1/agentic/cases without auth returns 401."""
        app = create_app()
        client = TestClient(app)
        response = client.post(
            "/api/v1/agentic/cases",
            json={"raw_input": "test case", "examples": [], "scenarios": []},
        )
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"

    def test_agentic_get_case_requires_auth(self):
        """GET /api/v1/agentic/cases/{id} without auth returns 401."""
        app = create_app()
        client = TestClient(app)
        response = client.get("/api/v1/agentic/cases/some-case-id")
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"


class TestDevTokenRejectedWhenEnvDisabled:
    """dev-test-token must be rejected when ENABLE_DEV_TOKEN is not set (or in production)."""

    def test_dev_token_rejected_when_enable_dev_token_unset(self, monkeypatch):
        """With ENABLE_DEV_TOKEN unset, Bearer dev-test-token returns 401."""
        monkeypatch.setenv("ENABLE_DEV_TOKEN", "")
        app = create_app()
        client = TestClient(app)
        response = client.get(
            "/api/v1/agentic/cases/some-id",
            headers={"Authorization": "Bearer dev-test-token"},
        )
        assert response.status_code == 401, f"Expected 401 when ENABLE_DEV_TOKEN not set, got {response.status_code}"


class TestSandboxDetectsSuspiciousPattern:
    """SkillsSandbox _check_security_violations must flag suspicious patterns in skill_code."""

    def test_sandbox_flags_import_os_in_skill_code(self):
        """Skill code containing 'import os' is reported as suspicious pattern."""
        sandbox = SkillsSandbox(config=SandboxConfig(allow_filesystem=False, timeout=5.0))
        work_dir = Path.cwd()
        execution_id = "test-exec-1"
        skill_code_with_os = "import os\ndef main(args):\n    return os.getcwd()"
        violations = sandbox._check_security_violations(execution_id, work_dir, skill_code=skill_code_with_os)
        assert any("Suspicious pattern" in v and "import os" in v for v in violations), (
            f"Expected suspicious pattern for 'import os', got: {violations}"
        )

    def test_sandbox_flags_import_subprocess_in_skill_code(self):
        """Skill code containing 'import subprocess' is reported as suspicious pattern."""
        sandbox = SkillsSandbox(config=SandboxConfig(allow_filesystem=False, timeout=5.0))
        work_dir = Path.cwd()
        execution_id = "test-exec-2"
        skill_code = "import subprocess\ndef main(args):\n    return {}"
        violations = sandbox._check_security_violations(execution_id, work_dir, skill_code=skill_code)
        assert any("Suspicious pattern" in v and "subprocess" in v for v in violations), (
            f"Expected suspicious pattern for subprocess, got: {violations}"
        )


class TestWebhookSignatureRejected:
    """Payment webhook must reject missing or invalid signature."""

    def test_webhook_missing_signature_returns_400(self):
        """POST /api/v1/payment/webhook without stripe-signature returns 400."""
        app = create_app()
        client = TestClient(app)
        response = client.post(
            "/api/v1/payment/webhook",
            content=b'{"id":"evt_123"}',
            headers={"Content-Type": "application/json"},
        )
        # 400 = missing signature rejected; 503 = payment gateway unavailable in test env
        assert response.status_code in (400, 503), (
            f"Expected 400 or 503 for webhook without valid setup, got {response.status_code}"
        )
        if response.status_code == 400:
            detail = response.json().get("detail", "")
            assert "signature" in detail.lower() or "Missing" in detail


class TestValidateUrlAllowlist:
    """validate_url_allowlist must be used for outbound HTTP (webhooks/callbacks). SSRF mitigation."""

    def test_rejects_disallowed_host(self) -> None:
        """URL with host not in allowed_hosts returns False."""
        assert validate_url_allowlist("https://evil.com/cb", ["api.stripe.com"], True) is False

    def test_accepts_allowed_host(self) -> None:
        """URL with host in allowed_hosts returns True."""
        assert validate_url_allowlist("https://api.stripe.com/v1/events", ["api.stripe.com"], True) is True

    def test_rejects_http_when_require_https(self) -> None:
        """HTTP URL when require_https=True returns False."""
        assert validate_url_allowlist("http://hooks.example.com/cb", ["hooks.example.com"], True) is False

    def test_accepts_http_when_require_https_false(self) -> None:
        """HTTP URL when require_https=False can be allowed."""
        assert validate_url_allowlist("http://hooks.example.com/cb", ["hooks.example.com"], False) is True

    def test_rejects_empty_url_or_hosts(self) -> None:
        """Empty url or allowed_hosts returns False."""
        assert validate_url_allowlist("", ["api.stripe.com"], True) is False
        assert validate_url_allowlist("https://api.stripe.com/", [], True) is False
