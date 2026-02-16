"""Unit tests for PreparednessFramework: check_gate, approve/revoke, enforce_biosecurity_scope."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from boundaries.preparedness import (
    BiosecurityScope,
    Gate,
    PreparednessFramework,
    RiskTier,
)


def _prep_config(
    enabled: bool = True,
    gates: list[dict] | None = None,
    risk_tiers: list[dict] | None = None,
    biosecurity: dict | None = None,
) -> dict:
    return {
        "preparedness": {
            "enabled": enabled,
            "riskTiers": risk_tiers
            or [
                {"id": "tier0", "name": "Minimal", "level": 0},
                {"id": "tier2", "name": "Medium", "level": 2, "requiresApproval": True},
                {"id": "tier3", "name": "High", "level": 3, "requiresApproval": True},
            ],
            "gates": gates
            or [
                {
                    "id": "gate_protocol",
                    "name": "Protocol change",
                    "riskTierId": "tier2",
                    "actionRequired": "require_approval",
                    "approvalAuthority": "lab_lead",
                },
                {
                    "id": "gate_capability",
                    "name": "Capability expansion",
                    "riskTierId": "tier3",
                    "actionRequired": "block",
                    "approvalAuthority": "preparedness_review",
                },
                {"id": "gate_audit", "name": "Audit only", "actionRequired": "audit"},
                {"id": "gate_log", "name": "Log and allow", "actionRequired": "log_and_allow"},
            ],
            "biosecurityScope": biosecurity
            or {
                "benignOnly": True,
                "taskScopeLimit": "optimization_only",
                "controlledSetting": True,
            },
        },
    }


class TestRiskTierAndGate(unittest.TestCase):
    def test_risk_tier_from_dict(self) -> None:
        t = RiskTier.from_dict({"id": "t1", "name": "Low", "level": 1, "requiresApproval": True, "scope": "protocol"})
        self.assertEqual(t.id, "t1")
        self.assertEqual(t.name, "Low")
        self.assertEqual(t.level, 1)
        self.assertTrue(t.requires_approval)
        self.assertEqual(t.scope, "protocol")

    def test_gate_from_dict(self) -> None:
        g = Gate.from_dict(
            {
                "id": "g1",
                "name": "Test",
                "riskTierId": "t2",
                "actionRequired": "block",
                "approvalAuthority": "review",
            }
        )
        self.assertEqual(g.id, "g1")
        self.assertEqual(g.action_required, "block")
        self.assertEqual(g.risk_tier_id, "t2")
        self.assertEqual(g.approval_authority, "review")


class TestBiosecurityScope(unittest.TestCase):
    def test_from_dict_none(self) -> None:
        bs = BiosecurityScope.from_dict(None)
        self.assertTrue(bs.benign_only)
        self.assertIsNone(bs.task_scope_limit)
        self.assertTrue(bs.controlled_setting)

    def test_from_dict(self) -> None:
        bs = BiosecurityScope.from_dict({"benignOnly": False, "taskScopeLimit": "x", "controlledSetting": False})
        self.assertFalse(bs.benign_only)
        self.assertEqual(bs.task_scope_limit, "x")
        self.assertFalse(bs.controlled_setting)


class TestPreparednessFrameworkCheckGate(unittest.TestCase):
    @patch("boundaries.preparedness.get_logger")
    def test_disabled_always_allows(self, mock_get_logger: MagicMock) -> None:
        mock_get_logger.return_value = MagicMock()
        config = _prep_config(enabled=False)
        prep = PreparednessFramework(config)
        action, allowed = prep.check_gate("gate_capability")
        self.assertEqual(action, "log_and_allow")
        self.assertTrue(allowed)
        mock_get_logger.return_value.log_preparedness_gate.assert_not_called()

    @patch("boundaries.preparedness.get_logger")
    def test_unknown_gate_audit_allowed(self, mock_get_logger: MagicMock) -> None:
        mock_get_logger.return_value = MagicMock()
        prep = PreparednessFramework(_prep_config())
        action, allowed = prep.check_gate("nonexistent_gate")
        self.assertEqual(action, "audit")
        self.assertTrue(allowed)

    @patch("boundaries.preparedness.get_logger")
    def test_block_gate_not_allowed_without_approval(self, mock_get_logger: MagicMock) -> None:
        mock_get_logger.return_value = MagicMock()
        prep = PreparednessFramework(_prep_config())
        action, allowed = prep.check_gate("gate_capability")
        self.assertEqual(action, "block")
        self.assertFalse(allowed)
        mock_get_logger.return_value.log_preparedness_gate.assert_called_once()

    @patch("boundaries.preparedness.get_logger")
    def test_block_gate_allowed_after_approval(self, mock_get_logger: MagicMock) -> None:
        mock_get_logger.return_value = MagicMock()
        prep = PreparednessFramework(_prep_config())
        prep.approve_gate("gate_capability")
        action, allowed = prep.check_gate("gate_capability")
        self.assertEqual(action, "block")
        self.assertTrue(allowed)

    @patch("boundaries.preparedness.get_logger")
    def test_require_approval_not_allowed_until_approved(self, mock_get_logger: MagicMock) -> None:
        mock_get_logger.return_value = MagicMock()
        prep = PreparednessFramework(_prep_config())
        action, allowed = prep.check_gate("gate_protocol")
        self.assertEqual(action, "require_approval")
        self.assertFalse(allowed)
        prep.approve_gate("gate_protocol")
        action, allowed = prep.check_gate("gate_protocol")
        self.assertTrue(allowed)

    @patch("boundaries.preparedness.get_logger")
    def test_log_and_allow_always_allowed(self, mock_get_logger: MagicMock) -> None:
        mock_get_logger.return_value = MagicMock()
        prep = PreparednessFramework(_prep_config())
        action, allowed = prep.check_gate("gate_log")
        self.assertEqual(action, "log_and_allow")
        self.assertTrue(allowed)

    @patch("boundaries.preparedness.get_logger")
    def test_audit_gate_always_allowed(self, mock_get_logger: MagicMock) -> None:
        mock_get_logger.return_value = MagicMock()
        prep = PreparednessFramework(_prep_config())
        action, allowed = prep.check_gate("gate_audit")
        self.assertEqual(action, "audit")
        self.assertTrue(allowed)


class TestPreparednessFrameworkApproveRevoke(unittest.TestCase):
    @patch("boundaries.preparedness.get_logger")
    def test_revoke_approval(self, mock_get_logger: MagicMock) -> None:
        mock_get_logger.return_value = MagicMock()
        prep = PreparednessFramework(_prep_config())
        prep.approve_gate("gate_protocol")
        _, allowed = prep.check_gate("gate_protocol")
        self.assertTrue(allowed)
        prep.revoke_approval("gate_protocol")
        _, allowed = prep.check_gate("gate_protocol")
        self.assertFalse(allowed)
        prep.revoke_approval("nonexistent")  # no error


class TestPreparednessFrameworkEnforceBiosecurityScope(unittest.TestCase):
    @patch("boundaries.preparedness.get_logger")
    def test_disabled_returns_true(self, mock_get_logger: MagicMock) -> None:
        mock_get_logger.return_value = MagicMock()
        prep = PreparednessFramework(_prep_config(enabled=False))
        self.assertTrue(prep.enforce_biosecurity_scope())
        self.assertTrue(prep.enforce_biosecurity_scope(benign_only=False, task_scope="other"))

    @patch("boundaries.preparedness.get_logger")
    def test_benign_only_mismatch(self, mock_get_logger: MagicMock) -> None:
        mock_get_logger.return_value = MagicMock()
        prep = PreparednessFramework(
            _prep_config(
                biosecurity={"benignOnly": True, "taskScopeLimit": "opt", "controlledSetting": True},
            )
        )
        self.assertTrue(prep.enforce_biosecurity_scope(benign_only=True))
        self.assertFalse(prep.enforce_biosecurity_scope(benign_only=False))

    @patch("boundaries.preparedness.get_logger")
    def test_task_scope_mismatch(self, mock_get_logger: MagicMock) -> None:
        mock_get_logger.return_value = MagicMock()
        prep = PreparednessFramework(
            _prep_config(
                biosecurity={"benignOnly": True, "taskScopeLimit": "optimization_only", "controlledSetting": True},
            )
        )
        self.assertTrue(prep.enforce_biosecurity_scope(task_scope="optimization_only"))
        self.assertFalse(prep.enforce_biosecurity_scope(task_scope="other_scope"))

    @patch("boundaries.preparedness.get_logger")
    def test_controlled_setting_mismatch(self, mock_get_logger: MagicMock) -> None:
        mock_get_logger.return_value = MagicMock()
        prep = PreparednessFramework(
            _prep_config(
                biosecurity={"benignOnly": True, "taskScopeLimit": "opt", "controlledSetting": True},
            )
        )
        self.assertTrue(prep.enforce_biosecurity_scope(controlled_setting=True))
        self.assertFalse(prep.enforce_biosecurity_scope(controlled_setting=False))

    @patch("boundaries.preparedness.get_logger")
    def test_all_match_returns_true(self, mock_get_logger: MagicMock) -> None:
        mock_get_logger.return_value = MagicMock()
        prep = PreparednessFramework(_prep_config())
        self.assertTrue(
            prep.enforce_biosecurity_scope(
                benign_only=True,
                task_scope="optimization_only",
                controlled_setting=True,
            )
        )


if __name__ == "__main__":
    unittest.main()
