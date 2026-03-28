"""
HMAC Integration Tests for GRID Admission Gate

End-to-end HMAC flow testing through actual middleware stack.
Tests entity signing, verification, and fallback scenarios.
"""

import json
import time
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from application.mothership.middleware.admission_gate import AdmissionGateMiddleware, EntityAttributionEngine
from application.mothership.middleware.entity_signing import sign_entity_id, verify_entity_signature, ENTITY_SIGNATURE_MAX_AGE


class TestHMACIntegration:
    """Test HMAC integration through actual middleware stack."""

    @pytest.fixture
    def app_with_secret(self):
        """Create FastAPI app with admission gate middleware and signing secret."""
        app = FastAPI()

        # Add admission gate middleware with entity signing secret
        secret = "test-integration-secret"
        attribution_engine = EntityAttributionEngine(entity_signing_secret=secret)

        @app.post("/api/v1/intelligence/process")
        async def test_endpoint(request: Request):
            # Simple endpoint that accepts valid structure
            return {"success": True, "processed": True}

        # Add middleware
        app.add_middleware(AdmissionGateMiddleware, attribution=attribution_engine)

        return TestClient(app), secret, attribution_engine

    @pytest.fixture
    def app_without_secret(self):
        """Create FastAPI app with admission gate middleware but no signing secret."""
        app = FastAPI()

        attribution_engine = EntityAttributionEngine(entity_signing_secret=None)

        @app.post("/api/v1/intelligence/process")
        async def test_endpoint(request: Request):
            return {"success": True, "processed": True}

        app.add_middleware(AdmissionGateMiddleware, attribution=attribution_engine)

        return TestClient(app), attribution_engine

    def test_valid_signature_admitted_with_claimed_entity(self, app_with_secret):
        """Test that valid signature is admitted and attributed to claimed entity."""
        client, secret, engine = app_with_secret

        entity_id = "test-entity-123"
        signature, timestamp = sign_entity_id(entity_id, secret)

        response = client.post("/api/v1/intelligence/process",
            json={"data": {"test": "valid"}},
            headers={
                "X-Entity-Id": entity_id,
                "X-Entity-Signature": signature,
                "X-Entity-Timestamp": str(timestamp),
            }
        )

        # Should be admitted
        assert response.status_code == 200
        assert response.json()["success"] is True

        # Check that the entity was tracked correctly
        assert engine.total_admitted == 1
        assert engine.total_rejected == 0
        assert len(engine.entities) == 1

    def test_missing_signature_falls_through_to_ip_and_admitted(self, app_with_secret):
        """Test that missing signature falls through to IP resolution but still admitted."""
        client, secret, engine = app_with_secret

        response = client.post("/api/v1/intelligence/process",
            json={"data": {"test": "valid"}},
            headers={
                "X-Entity-Id": "test-entity",
                # Missing signature and timestamp
            }
        )

        # Should be admitted (structure is valid)
        assert response.status_code == 200
        assert response.json()["success"] is True

        # Should be admitted with IP-based entity
        assert engine.total_admitted == 1
        assert engine.total_rejected == 0

    def test_invalid_signature_falls_through_to_ip_and_admitted(self, app_with_secret):
        """Test that invalid signature falls through to IP resolution but still admitted."""
        client, secret, engine = app_with_secret

        response = client.post("/api/v1/intelligence/process",
            json={"data": {"test": "valid"}},
            headers={
                "X-Entity-Id": "test-entity",
                "X-Entity-Signature": "invalid-signature",
                "X-Entity-Timestamp": str(int(time.time())),
            }
        )

        # Should be admitted (structure is valid)
        assert response.status_code == 200
        assert response.json()["success"] is True

        # Should be admitted with IP-based entity
        assert engine.total_admitted == 1
        assert engine.total_rejected == 0

    def test_expired_timestamp_falls_through_to_ip_and_admitted(self, app_with_secret):
        """Test that expired timestamp falls through to IP resolution but still admitted."""
        client, secret, engine = app_with_secret

        # Use timestamp older than 5 minutes
        old_timestamp = int(time.time()) - ENTITY_SIGNATURE_MAX_AGE - 60
        signature, _ = sign_entity_id("test-entity", secret, old_timestamp)

        response = client.post("/api/v1/intelligence/process",
            json={"data": {"test": "valid"}},
            headers={
                "X-Entity-Id": "test-entity",
                "X-Entity-Signature": signature,
                "X-Entity-Timestamp": str(old_timestamp),
            }
        )

        # Should be admitted (structure is valid)
        assert response.status_code == 200
        assert response.json()["success"] is True

        # Should be admitted with IP-based entity
        assert engine.total_admitted == 1
        assert engine.total_rejected == 0

    def test_wrong_secret_falls_through_to_ip_and_admitted(self, app_with_secret):
        """Test that signature with wrong secret falls through to IP resolution but still admitted."""
        client, secret, engine = app_with_secret

        # Sign with wrong secret
        wrong_secret = "wrong-secret"
        signature, timestamp = sign_entity_id("test-entity", wrong_secret)

        response = client.post("/api/v1/intelligence/process",
            json={"data": {"test": "valid"}},
            headers={
                "X-Entity-Id": "test-entity",
                "X-Entity-Signature": signature,
                "X-Entity-Timestamp": str(timestamp),
            }
        )

        # Should be admitted (structure is valid)
        assert response.status_code == 200
        assert response.json()["success"] is True

        # Should be admitted with IP-based entity
        assert engine.total_admitted == 1
        assert engine.total_rejected == 0

    def test_no_secret_configured_ignores_signature(self, app_without_secret):
        """Test that when no secret is configured, signature headers are ignored."""
        client, engine = app_without_secret

        response = client.post("/api/v1/intelligence/process",
            json={"data": {"test": "valid"}},
            headers={
                "X-Entity-Id": "test-entity",
                "X-Entity-Signature": "some-signature",
                "X-Entity-Timestamp": str(int(time.time())),
            }
        )

        # Should be admitted and attributed to claimed entity
        assert response.status_code == 200
        assert response.json()["success"] is True

        assert engine.total_admitted == 1
        assert engine.total_rejected == 0

    def test_api_key_fallback_with_invalid_signature(self, app_with_secret):
        """Test API key fallback when signature is invalid."""
        client, secret, engine = app_with_secret

        response = client.post("/api/v1/intelligence/process",
            json={"data": {"test": "valid"}},
            headers={
                "X-Entity-Id": "test-entity",
                "X-Entity-Signature": "invalid",
                "X-Entity-Timestamp": str(int(time.time())),
                "X-API-Key": "test-api-key-12345678",
            }
        )

        # Should be admitted
        assert response.status_code == 200
        assert response.json()["success"] is True

        assert engine.total_admitted == 1
        assert engine.total_rejected == 0

    def test_edge_case_empty_entity_id_admitted(self, app_with_secret):
        """Test edge case of empty entity ID header."""
        client, secret, engine = app_with_secret

        response = client.post("/api/v1/intelligence/process",
            json={"data": {"test": "valid"}},
            headers={
                "X-Entity-Id": "",
                "X-Entity-Signature": "signature",
                "X-Entity-Timestamp": str(int(time.time())),
            }
        )

        # Should be admitted with IP-based entity
        assert response.status_code == 200
        assert response.json()["success"] is True

        assert engine.total_admitted == 1
        assert engine.total_rejected == 0

    def test_edge_case_whitespace_only_entity_id_admitted(self, app_with_secret):
        """Test edge case of whitespace-only entity ID header."""
        client, secret, engine = app_with_secret

        response = client.post("/api/v1/intelligence/process",
            json={"data": {"test": "valid"}},
            headers={
                "X-Entity-Id": "   ",
                "X-Entity-Signature": "signature",
                "X-Entity-Timestamp": str(int(time.time())),
            }
        )

        # Should be admitted with IP-based entity
        assert response.status_code == 200
        assert response.json()["success"] is True

        assert engine.total_admitted == 1
        assert engine.total_rejected == 0
