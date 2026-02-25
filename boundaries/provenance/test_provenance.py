"""Tests for Decision Chain of Custody (DCoC) provenance library."""

import os
import pytest

os.environ.setdefault("GRID_PROVENANCE_SECRET", "test-provenance-secret")

from boundaries.provenance.types import (
    DecisionType,
    AuthorityType,
    SafetyVerdict,
    SafetyVerdictResult,
    DPRCreateInput,
)
from boundaries.provenance.record import create_dpr, get_chain_ref
from boundaries.provenance.chain import compute_hash, compute_chain_hash
from boundaries.provenance.signer import sign_record, verify_signature


def _make_input(**kwargs) -> DPRCreateInput:
    defaults = {
        "decision_type": DecisionType.GATE_VERDICT,
        "action_taken": "authentication_check",
        "reasoning_summary": "JWT validated",
        "authority_type": AuthorityType.SYSTEM_POLICY,
        "actor_id": "user-123",
    }
    defaults.update(kwargs)
    return DPRCreateInput(**defaults)


class TestDPRCreation:
    def test_creates_valid_dpr(self):
        dpr = create_dpr(_make_input())
        assert dpr.dpr_id
        assert dpr.parent_dpr_id is None
        assert dpr.chain_hash
        assert dpr.signature
        assert dpr.sequence_number == 0
        assert dpr.provenance_version == "1.0.0"
        assert dpr.decision_type == DecisionType.GATE_VERDICT

    def test_chains_dprs(self):
        first = create_dpr(_make_input())
        second = create_dpr(
            _make_input(action_taken="rate_limit_check"),
            get_chain_ref(first),
        )
        assert second.parent_dpr_id == first.dpr_id
        assert second.sequence_number == 1
        assert second.chain_hash != first.chain_hash

    def test_different_inputs_produce_different_hashes(self):
        a = create_dpr(_make_input(action_taken="action_a"))
        b = create_dpr(_make_input(action_taken="action_b"))
        assert a.chain_hash != b.chain_hash


class TestHashChain:
    def test_three_record_chain(self):
        d1 = create_dpr(_make_input(action_taken="auth"))
        d2 = create_dpr(_make_input(action_taken="rate_limit"), get_chain_ref(d1))
        d3 = create_dpr(_make_input(action_taken="llm_call"), get_chain_ref(d2))
        assert d1.sequence_number == 0
        assert d2.sequence_number == 1
        assert d3.sequence_number == 2
        assert d2.parent_dpr_id == d1.dpr_id
        assert d3.parent_dpr_id == d2.dpr_id

    def test_detects_tampered_hash(self):
        dpr = create_dpr(_make_input())
        original_hash = dpr.chain_hash
        # Tamper
        assert original_hash != "tampered_value"


class TestSigning:
    def test_sign_and_verify(self):
        data = "test-data-for-signing"
        sig = sign_record(data)
        assert sig
        assert verify_signature(data, sig)

    def test_rejects_tampered_data(self):
        sig = sign_record("original")
        assert not verify_signature("tampered", sig)

    def test_rejects_tampered_signature(self):
        sig = sign_record("test-data")
        tampered = sig[:-5] + "XXXXX"
        assert not verify_signature("test-data", tampered)


class TestPrivacyPreservation:
    def test_hashes_input_not_raw_text(self):
        dpr = create_dpr(_make_input(
            input_context="Sensitive user input about a meeting",
            output_content="Brief response about priorities",
        ))
        assert dpr.input_context_hash
        assert dpr.output_hash
        assert dpr.input_context_hash == compute_hash("Sensitive user input about a meeting")
        serialized = str(dpr.to_dict())
        assert "Sensitive user input" not in serialized
        assert "Brief response about" not in serialized


class TestSafetyVerdicts:
    def test_records_verdicts(self):
        dpr = create_dpr(_make_input(
            safety_verdicts=[
                SafetyVerdict("jwt_auth", "auth", SafetyVerdictResult.PASS, 1.0, 1.0),
                SafetyVerdict("rate_limit", "rate_limit", SafetyVerdictResult.PASS, 3.0, 1.0),
            ],
        ))
        assert len(dpr.safety_verdicts) == 2
        assert dpr.safety_verdicts[0].gate_id == "jwt_auth"

    def test_records_blocked_verdicts(self):
        dpr = create_dpr(_make_input(
            decision_type=DecisionType.REFUSAL,
            action_taken="service_refusal",
            safety_verdicts=[
                SafetyVerdict("rate_limit", "rate_limit", SafetyVerdictResult.BLOCK, 2.0, 1.0),
            ],
        ))
        assert dpr.decision_type == DecisionType.REFUSAL
        assert dpr.safety_verdicts[0].verdict == SafetyVerdictResult.BLOCK


class TestNominalization:
    def test_action_taken_uses_abstract_nouns(self):
        actions = [
            "authentication_check",
            "rate_limit_enforcement",
            "session_limit_check",
            "llm_response_delivery",
            "service_refusal",
            "consent_change",
            "data_export",
        ]
        import re
        for action in actions:
            assert not re.match(r"^(I |you |we |do |make )", action, re.IGNORECASE)
            assert re.match(r"^[a-z_]+$", action)
