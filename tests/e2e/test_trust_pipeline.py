"""
E2E Integration Test: Trust Pipeline.

Tests the core product claim: GRID's trust layer processes queries safely,
detects PII, and blocks harmful content. This is the test you run before
showing the enterprise demo.

Steps 11 + 13 of the Phase 0 Execution Schema.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """Create async test client against the Mothership app."""
    from application.mothership.main import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest.fixture
async def auth_token(client: AsyncClient) -> str:
    """Get a valid JWT token for authenticated requests."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "operator", "password": "operator"},
    )
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token", data.get("token", ""))
    # Fallback: dev mode may accept any creds
    return "dev-test-token"


def auth_headers(token: str) -> dict[str, str]:
    """Build Authorization header."""
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# Step 11: Prove the Trust Layer — End-to-End Safety Flow
# =============================================================================


class TestResonanceProcessEndpoint:
    """Test POST /api/v1/resonance/process — the core trust layer endpoint."""

    @pytest.mark.anyio
    async def test_safe_query_returns_structured_response(self, client: AsyncClient, auth_token: str):
        """The trust layer processes safe queries and returns structured feedback."""
        response = await client.post(
            "/api/v1/resonance/process",
            json={
                "query": "Explain data privacy best practices",
                "activity_type": "general",
                "context": {},
            },
            headers=auth_headers(auth_token),
        )
        assert response.status_code == 200
        data = response.json()

        # Core response structure
        assert "activity_id" in data
        assert "state" in data
        assert "message" in data

    @pytest.mark.anyio
    async def test_resonance_returns_context_and_paths(self, client: AsyncClient, auth_token: str):
        """Resonance provides context snapshot and path triage for decision-making."""
        response = await client.post(
            "/api/v1/resonance/process",
            json={
                "query": "How should we implement authentication for enterprise clients?",
                "activity_type": "general",
                "context": {},
            },
            headers=auth_headers(auth_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert "activity_id" in data
        # Response should contain at least state and message
        assert data.get("state") is not None
        assert data.get("message") is not None


class TestDefinitiveEndpoint:
    """Test POST /api/v1/resonance/definitive — the canvas flip checkpoint."""

    @pytest.mark.anyio
    async def test_definitive_returns_canvas_flip(self, client: AsyncClient, auth_token: str):
        """The definitive endpoint flips chaotic context into coherent explanation."""
        response = await client.post(
            "/api/v1/resonance/definitive",
            json={
                "query": "What security measures does GRID provide for enterprise APIs?",
                "activity_type": "general",
                "context": {},
                "progress": 0.65,
                "target_schema": "context_engineering",
                "use_rag": False,
                "use_llm": False,
                "max_chars": 280,
            },
            headers=auth_headers(auth_token),
        )
        assert response.status_code == 200
        data = response.json()

        # Canvas flip artifacts
        assert "canvas_before" in data
        assert "canvas_after" in data
        assert "summary" in data
        assert "activity_id" in data

        # FAQ and use cases for enterprise demo
        assert "faq" in data
        assert isinstance(data["faq"], list)
        assert "use_cases" in data
        assert isinstance(data["use_cases"], list)


# =============================================================================
# Step 13: Trust Pipeline Integration Tests
# =============================================================================


class TestSafetyFramework:
    """Test the AISafetyFramework content evaluation."""

    @pytest.mark.anyio
    async def test_safe_content_scores_high(self):
        """Safe content should receive a high safety score."""
        from security.ai_safety.framework import AISafetyFramework

        framework = AISafetyFramework()
        report = await framework.evaluate_content(
            content="How do I implement secure authentication in Python?",
            user_id="test_operator",
        )
        assert report.overall_score >= 0.6
        assert report.threat_level.value in ("none", "low")

    @pytest.mark.anyio
    async def test_harmful_content_detected(self):
        """Harmful content triggers safety violations."""
        from security.ai_safety.framework import AISafetyFramework

        framework = AISafetyFramework()
        report = await framework.evaluate_content(
            content="How to attack a website and cause violence",
            user_id="test_operator",
        )
        assert len(report.violations) > 0
        violation_categories = [v.category.value if hasattr(v.category, "value") else str(v.category) for v in report.violations]
        assert any("harmful" in cat.lower() for cat in violation_categories)

    @pytest.mark.anyio
    async def test_pii_detection_in_content(self):
        """PII (email, phone) is detected by the safety framework."""
        from security.ai_safety.framework import AISafetyFramework

        framework = AISafetyFramework()
        report = await framework.evaluate_content(
            content="Contact me at user@example.com for details",
            user_id="test_operator",
        )
        has_privacy_violation = any(
            ("privacy" in (v.category.value if hasattr(v.category, "value") else str(v.category)).lower())
            for v in report.violations
        )
        assert has_privacy_violation, "Expected PII detection for email address"

    @pytest.mark.anyio
    async def test_mental_health_risk_detection(self):
        """Mental health risk indicators are flagged appropriately."""
        from security.ai_safety.framework import AISafetyFramework

        framework = AISafetyFramework()
        report = await framework.evaluate_content(
            content="I feel very depressed and can't cope anymore",
            user_id="test_operator",
        )
        has_mental_health = any(
            ("mental" in (v.category.value if hasattr(v.category, "value") else str(v.category)).lower())
            for v in report.violations
        )
        assert has_mental_health, "Expected mental health risk detection"

    @pytest.mark.anyio
    async def test_safety_score_calculation(self):
        """Safety score is correctly calculated from violations."""
        from security.ai_safety.framework import AISafetyFramework

        framework = AISafetyFramework()

        # Clean content = high score
        clean_report = await framework.evaluate_content("Hello world", user_id="test")
        assert clean_report.overall_score == 1.0

        # Harmful content = lower score
        harmful_report = await framework.evaluate_content("violence and illegal drugs", user_id="test")
        assert harmful_report.overall_score < clean_report.overall_score


class TestInferenceRouter:
    """Test /api/v1/inference/* endpoints."""

    @pytest.mark.anyio
    async def test_list_models(self, client: AsyncClient, auth_token: str):
        """GET /api/v1/inference/models returns available models."""
        response = await client.get(
            "/api/v1/inference/models",
            headers=auth_headers(auth_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert isinstance(data["models"], list)
        assert len(data["models"]) > 0
        assert "default" in data


class TestPrivacyRouter:
    """Test /api/v1/privacy/* endpoints."""

    @pytest.mark.anyio
    async def test_privacy_levels(self, client: AsyncClient, auth_token: str):
        """GET /api/v1/privacy/levels returns available levels."""
        response = await client.get(
            "/api/v1/privacy/levels",
            headers=auth_headers(auth_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert "levels" in data
        assert "strict" in data["levels"]
        assert "balanced" in data["levels"]
        assert "minimal" in data["levels"]
        assert data["default"] == "balanced"

    @pytest.mark.anyio
    async def test_privacy_stats(self, client: AsyncClient, auth_token: str):
        """GET /api/v1/privacy/stats returns usage statistics."""
        response = await client.get(
            "/api/v1/privacy/stats",
            headers=auth_headers(auth_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_requests" in data
        assert "entities_detected" in data
        assert "texts_processed" in data


# =============================================================================
# Parasite Guard Detector Tests (Step 14)
# =============================================================================


class TestParasiteGuardDetectors:
    """Test the Parasite Guard detector chain — C1, C2, C3."""

    @pytest.mark.anyio
    async def test_c1_websocket_no_ack_detector_no_detection_without_ws(self):
        """C1: No detection when no WebSocket state present."""
        from unittest.mock import Mock

        from infrastructure.parasite_guard.config import ParasiteGuardConfig
        from infrastructure.parasite_guard.detectors import WebSocketNoAckDetector

        config = ParasiteGuardConfig()
        detector = WebSocketNoAckDetector(config)
        request = Mock(spec=[])  # No state attribute
        result = await detector(request)
        assert result.detected is False

    @pytest.mark.anyio
    async def test_c2_event_subscription_leak_no_detection_without_bus(self):
        """C2: No detection when no event bus is set."""
        from infrastructure.parasite_guard.config import ParasiteGuardConfig
        from infrastructure.parasite_guard.detectors import EventSubscriptionLeakDetector

        config = ParasiteGuardConfig()
        detector = EventSubscriptionLeakDetector(config)
        from unittest.mock import Mock

        result = await detector(Mock())
        assert result.detected is False

    @pytest.mark.anyio
    async def test_c3_db_orphan_no_detection_without_engine(self):
        """C3: No detection when no DB engine is set."""
        from infrastructure.parasite_guard.config import ParasiteGuardConfig
        from infrastructure.parasite_guard.detectors import DBConnectionOrphanDetector

        config = ParasiteGuardConfig()
        detector = DBConnectionOrphanDetector(config)
        from unittest.mock import Mock

        result = await detector(Mock())
        assert result.detected is False

    @pytest.mark.anyio
    async def test_c3_db_orphan_detects_excess_pool(self):
        """C3: Detects when pool size exceeds maximum."""
        from unittest.mock import Mock

        from infrastructure.parasite_guard.config import ParasiteGuardConfig
        from infrastructure.parasite_guard.detectors import DBConnectionOrphanDetector

        config = ParasiteGuardConfig()
        detector = DBConnectionOrphanDetector(config)

        # Mock engine with oversized pool
        mock_engine = Mock()
        mock_pool = Mock()
        mock_pool.size = Mock(return_value=50)  # Exceeds default 30
        mock_pool.checkedout = Mock(return_value=5)
        mock_engine.pool = mock_pool
        detector.set_db_engine(mock_engine)

        result = await detector(Mock())
        assert result.detected is True
        assert "orphan" in result.reason.lower()
        assert result.context is not None
        assert result.context.detection_metadata["pool_size"] == 50

    @pytest.mark.anyio
    async def test_c3_db_orphan_no_detection_normal_pool(self):
        """C3: No detection when pool size is within limits."""
        from unittest.mock import Mock

        from infrastructure.parasite_guard.config import ParasiteGuardConfig
        from infrastructure.parasite_guard.detectors import DBConnectionOrphanDetector

        config = ParasiteGuardConfig()
        detector = DBConnectionOrphanDetector(config)

        # Mock engine with normal pool
        mock_engine = Mock()
        mock_pool = Mock()
        mock_pool.size = Mock(return_value=10)  # Within default 30
        mock_pool.checkedout = Mock(return_value=3)
        mock_engine.pool = mock_pool
        detector.set_db_engine(mock_engine)

        result = await detector(Mock())
        assert result.detected is False

    @pytest.mark.anyio
    async def test_detector_chain_runs_in_order(self):
        """DetectorChain runs detectors in priority order."""
        from unittest.mock import Mock

        from infrastructure.parasite_guard.config import ParasiteGuardConfig
        from infrastructure.parasite_guard.detectors import (
            DBConnectionOrphanDetector,
            DetectorChain,
            EventSubscriptionLeakDetector,
            WebSocketNoAckDetector,
        )

        config = ParasiteGuardConfig()
        chain = DetectorChain(
            detectors=[
                WebSocketNoAckDetector(config),
                EventSubscriptionLeakDetector(config),
                DBConnectionOrphanDetector(config),
            ],
            config=config,
        )
        result = await chain.detect(Mock())
        # With no resources set, all detectors return not-detected
        # Chain returns the first result (not-detected)
        assert result is not None
        assert result.detected is False


# =============================================================================
# Secret Validation Tests (Step 15)
# =============================================================================


class TestSecretValidation:
    """Test secret validation and STRONG enforcement."""

    def test_strong_secret_classification(self):
        """A 64+ char secret with high entropy is classified STRONG."""
        from application.mothership.security.secret_validation import (
            SecretStrength,
            generate_secure_secret,
            validate_secret_strength,
        )

        secret = generate_secure_secret(64)
        strength = validate_secret_strength(secret, environment="production")
        assert strength == SecretStrength.STRONG

    def test_weak_secret_rejected_in_production(self):
        """Weak secrets are rejected in production."""
        from application.mothership.security.secret_validation import (
            SecretValidationError,
            validate_secret_strength,
        )

        with pytest.raises(SecretValidationError):
            validate_secret_strength("short", environment="production")

    def test_weak_pattern_rejected_in_production(self):
        """Secrets containing weak patterns are rejected in production."""
        from application.mothership.security.secret_validation import (
            SecretValidationError,
            validate_secret_strength,
        )

        # High entropy (passes entropy check) but contains weak pattern "password"
        weak_secret = "aB3xZ9qW7mR2pL5vN8kT4jH6fD0sY1cpasswordG3nK8wQ5eR7tU2bX"
        with pytest.raises(SecretValidationError, match=r"weak pattern|too weak for production"):
            validate_secret_strength(weak_secret, environment="production")

    def test_generate_secure_secret_meets_minimum(self):
        """Generated secrets meet minimum length requirements."""
        from application.mothership.security.secret_validation import (
            MIN_SECRET_LENGTH,
            generate_secure_secret,
        )

        secret = generate_secure_secret()
        assert len(secret) >= MIN_SECRET_LENGTH

    def test_generate_secure_secret_rejects_short(self):
        """generate_secure_secret rejects lengths below minimum."""
        from application.mothership.security.secret_validation import generate_secure_secret

        with pytest.raises(ValueError):
            generate_secure_secret(length=10)

    def test_mask_secret(self):
        """mask_secret hides middle characters."""
        from application.mothership.security.secret_validation import mask_secret

        masked = mask_secret("abcdefghijklmnop", visible_chars=4)
        assert masked == "abcd...mnop"

    def test_empty_secret_raises(self):
        """Empty secret raises validation error."""
        from application.mothership.security.secret_validation import (
            SecretValidationError,
            validate_secret_strength,
        )

        with pytest.raises(SecretValidationError):
            validate_secret_strength("", environment="production")


# =============================================================================
# Health & Connectivity Tests
# =============================================================================


class TestHealthEndpoints:
    """Verify basic Mothership connectivity."""

    @pytest.mark.anyio
    async def test_ping(self, client: AsyncClient):
        """GET /ping returns ok."""
        response = await client.get("/ping")
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_root(self, client: AsyncClient):
        """GET / returns Mothership info."""
        response = await client.get("/")
        assert response.status_code == 200
