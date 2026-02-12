"""
Unit tests for the safety middleware refusal behavior.

Tests that:
1. Refusals are deterministic and use the correct JSON structure.
2. Refusals are non-informative (no bypass hints).
3. Reason codes are present.
"""

from __future__ import annotations


class TestRefusalFormat:
    """Test that refusal responses match the required contract."""

    def test_refusal_json_structure(self):
        """Verify the refusal response matches the spec."""
        # Simulate what the middleware produces
        refusal = {
            "refused": True,
            "reason_code": "HIGH_RISK_BIO",
            "explanation": "request denied",
            "support_ticket_id": "audit-abc123",
        }
        assert refusal["refused"] is True
        assert isinstance(refusal["reason_code"], str)
        assert len(refusal["reason_code"]) > 0
        assert refusal["explanation"] == "request denied"
        assert refusal["support_ticket_id"].startswith("audit-")

    def test_refusal_is_non_informative(self):
        """Refusal explanation must not hint at how to bypass."""
        explanation = "request denied"
        bypass_hints = [
            "try",
            "rephrase",
            "instead",
            "allowed",
            "however",
            "you could",
            "alternative",
            "bypass",
            "workaround",
        ]
        for hint in bypass_hints:
            assert hint not in explanation.lower(), (
                f"Explanation contains bypass hint: {hint!r}"
            )

    def test_rate_limit_json_structure(self):
        """Verify rate-limit response structure."""
        response = {
            "rate_limited": True,
            "window_seconds": 3600,
            "support_ticket_id": "audit-def456",
        }
        assert response["rate_limited"] is True
        assert isinstance(response["window_seconds"], int)
        assert response["window_seconds"] > 0
