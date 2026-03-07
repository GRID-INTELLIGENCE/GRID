"""Tests for BoundaryEngine fail-closed enforcement, consent lifecycle, and guardrail logic.

These tests cover the operational enforcement engine in boundaries/boundary.py,
complementing test_overwatch.py (overwatch alerts) and test_preparedness.py (gate checks).
The key property under test is **fail-closed**: unknown boundary/guardrail IDs are denied,
never silently allowed.
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from boundaries.boundary import BoundaryEngine


def _engine_config(
    boundaries: list[dict] | None = None,
    consents: list[dict] | None = None,
    guardrails: list[dict] | None = None,
) -> dict:
    """Build a minimal BoundaryEngine config dict."""
    return {
        "boundaries": boundaries or [],
        "consents": consents or [],
        "guardrails": guardrails or [],
        "rightToRefuse": {"enabled": False, "triggers": []},
    }


class TestBoundaryEngineFailClosed(unittest.TestCase):
    """Verify that unknown IDs are denied (fail-closed), not silently allowed."""

    @patch("boundaries.boundary.get_logger")
    @patch("boundaries.boundary.check_refusal", return_value=None)
    def test_unknown_boundary_id_returns_false(
        self, mock_refusal: MagicMock, mock_get_logger: MagicMock
    ) -> None:
        mock_get_logger.return_value = MagicMock()
        engine = BoundaryEngine(_engine_config())
        result = engine.check_boundary("nonexistent_boundary", "any_subject")
        self.assertFalse(result)

    @patch("boundaries.boundary.get_logger")
    @patch("boundaries.boundary.check_refusal", return_value=None)
    def test_unknown_guardrail_id_returns_block(
        self, mock_refusal: MagicMock, mock_get_logger: MagicMock
    ) -> None:
        mock_get_logger.return_value = MagicMock()
        engine = BoundaryEngine(_engine_config())
        action, overridden = engine.check_guardrail("nonexistent_guardrail")
        self.assertEqual(action, "block")
        self.assertFalse(overridden)


class TestBoundaryEngineRuleEvaluation(unittest.TestCase):
    """Verify boundary rule evaluation: allow lists, deny lists, no-rule pass."""

    @patch("boundaries.boundary.get_logger")
    @patch("boundaries.boundary.check_refusal", return_value=None)
    def test_boundary_with_deny_rule_blocks_subject(
        self, mock_refusal: MagicMock, mock_get_logger: MagicMock
    ) -> None:
        mock_get_logger.return_value = MagicMock()
        config = _engine_config(boundaries=[{
            "id": "b1", "name": "Test Boundary", "type": "access",
            "enforcement": "hard", "rule": {"deny": ["blocked_user"]},
        }])
        engine = BoundaryEngine(config)
        self.assertFalse(engine.check_boundary("b1", "blocked_user"))
        self.assertTrue(engine.check_boundary("b1", "allowed_user"))

    @patch("boundaries.boundary.get_logger")
    @patch("boundaries.boundary.check_refusal", return_value=None)
    def test_boundary_with_allow_rule_only_permits_listed(
        self, mock_refusal: MagicMock, mock_get_logger: MagicMock
    ) -> None:
        mock_get_logger.return_value = MagicMock()
        config = _engine_config(boundaries=[{
            "id": "b2", "name": "Allow-List Boundary", "type": "access",
            "enforcement": "hard", "rule": {"allow": ["admin", "operator"]},
        }])
        engine = BoundaryEngine(config)
        self.assertTrue(engine.check_boundary("b2", "admin"))
        self.assertTrue(engine.check_boundary("b2", "operator"))
        self.assertFalse(engine.check_boundary("b2", "random_user"))

    @patch("boundaries.boundary.get_logger")
    @patch("boundaries.boundary.check_refusal", return_value=None)
    def test_boundary_with_no_rule_allows_all(
        self, mock_refusal: MagicMock, mock_get_logger: MagicMock
    ) -> None:
        mock_get_logger.return_value = MagicMock()
        config = _engine_config(boundaries=[{
            "id": "b3", "name": "Open Boundary", "type": "access",
            "enforcement": "soft",
        }])
        engine = BoundaryEngine(config)
        self.assertTrue(engine.check_boundary("b3", "anyone"))


class TestConsentLifecycle(unittest.TestCase):
    """Verify consent state transitions: pending → granted → revoked → denied."""

    @patch("boundaries.boundary.get_logger")
    def test_consent_default_state_is_pending(self, mock_get_logger: MagicMock) -> None:
        mock_get_logger.return_value = MagicMock()
        config = _engine_config(consents=[{
            "id": "c1", "name": "Data Collection", "scope": "user_data",
        }])
        engine = BoundaryEngine(config)
        self.assertEqual(engine.get_consent_state("c1"), "pending")
        self.assertFalse(engine.require_consent("c1"))

    @patch("boundaries.boundary.get_logger")
    def test_grant_then_require_returns_true(self, mock_get_logger: MagicMock) -> None:
        mock_get_logger.return_value = MagicMock()
        config = _engine_config(consents=[{
            "id": "c1", "name": "Data Collection", "scope": "user_data",
        }])
        engine = BoundaryEngine(config)
        engine.grant_consent("c1", actor_id="user_1")
        self.assertTrue(engine.require_consent("c1"))
        self.assertEqual(engine.get_consent_state("c1"), "granted")

    @patch("boundaries.boundary.get_logger")
    def test_revoke_after_grant_blocks_access(self, mock_get_logger: MagicMock) -> None:
        mock_get_logger.return_value = MagicMock()
        config = _engine_config(consents=[{
            "id": "c1", "name": "Data Collection", "scope": "user_data",
        }])
        engine = BoundaryEngine(config)
        engine.grant_consent("c1")
        self.assertTrue(engine.require_consent("c1"))
        engine.revoke_consent("c1")
        self.assertFalse(engine.require_consent("c1"))
        self.assertEqual(engine.get_consent_state("c1"), "revoked")

    @patch("boundaries.boundary.get_logger")
    def test_deny_consent_blocks_access(self, mock_get_logger: MagicMock) -> None:
        mock_get_logger.return_value = MagicMock()
        config = _engine_config(consents=[{
            "id": "c1", "name": "Data Collection", "scope": "user_data",
        }])
        engine = BoundaryEngine(config)
        engine.deny_consent("c1")
        self.assertFalse(engine.require_consent("c1"))
        self.assertEqual(engine.get_consent_state("c1"), "denied")

    @patch("boundaries.boundary.get_logger")
    def test_unknown_consent_id_returns_pending(self, mock_get_logger: MagicMock) -> None:
        mock_get_logger.return_value = MagicMock()
        engine = BoundaryEngine(_engine_config())
        self.assertEqual(engine.get_consent_state("nonexistent"), "pending")
        self.assertFalse(engine.require_consent("nonexistent"))


class TestGuardrailActions(unittest.TestCase):
    """Verify guardrail action dispatch and refusal override."""

    @patch("boundaries.boundary.get_logger")
    @patch("boundaries.boundary.check_refusal", return_value=None)
    def test_known_guardrail_returns_configured_action(
        self, mock_refusal: MagicMock, mock_get_logger: MagicMock
    ) -> None:
        mock_get_logger.return_value = MagicMock()
        config = _engine_config(guardrails=[{
            "id": "g1", "name": "Content Filter", "kind": "content",
            "action": "warn",
        }])
        engine = BoundaryEngine(config)
        action, overridden = engine.check_guardrail("g1")
        self.assertEqual(action, "warn")
        self.assertFalse(overridden)

    @patch("boundaries.boundary.get_logger")
    @patch("boundaries.boundary.check_refusal", return_value={"trigger": "g2"})
    def test_refusal_overrides_when_allowed(
        self, mock_refusal: MagicMock, mock_get_logger: MagicMock
    ) -> None:
        mock_get_logger.return_value = MagicMock()
        config = _engine_config(guardrails=[{
            "id": "g2", "name": "Optional Guard", "kind": "optional",
            "action": "block", "overridableByRefusal": True,
        }])
        engine = BoundaryEngine(config)
        action, overridden = engine.check_guardrail("g2")
        self.assertEqual(action, "block")
        self.assertTrue(overridden)

    @patch("boundaries.boundary.get_logger")
    @patch("boundaries.boundary.check_refusal", return_value={"trigger": "g3"})
    def test_refusal_does_not_override_when_not_allowed(
        self, mock_refusal: MagicMock, mock_get_logger: MagicMock
    ) -> None:
        mock_get_logger.return_value = MagicMock()
        config = _engine_config(guardrails=[{
            "id": "g3", "name": "Hard Guard", "kind": "security",
            "action": "block", "overridableByRefusal": False,
        }])
        engine = BoundaryEngine(config)
        action, overridden = engine.check_guardrail("g3")
        self.assertEqual(action, "block")
        self.assertFalse(overridden)


if __name__ == "__main__":
    unittest.main()
