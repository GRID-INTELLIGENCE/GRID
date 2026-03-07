"""
Comprehensive tests for the transition gate module.

Tests cover:
- Fingerprint computation (user, machine, payload hash, timing-safe comparison)
- Nonce registry (generation, validation, burning, expiry, persistence)
- Envelope sealing (seal_envelope, serialization, deserialization)
- GateKeeper verification pipeline (all 9 steps, rejection cases, dry-run)
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from boundaries.transition_gate.envelope import (
    PERM_DEPLOY,
    PERM_READ_ONLY,
    PERM_RUN_TESTS,
    PERM_START_SERVER,
    ScopeDeclaration,
    TransitionEnvelope,
    seal_envelope,
)
from boundaries.transition_gate.fingerprint import (
    compute_machine_fingerprint,
    compute_payload_hash,
    compute_user_fingerprint,
    fingerprints_match,
)
from boundaries.transition_gate.gate_keeper import (
    GateKeeper,
    RejectionReason,
    VerificationStatus,
    verify_envelope,
)
from boundaries.transition_gate.nonce import NonceRegistry

# ── Shared test fixtures ──

MACHINE_FP_OVERRIDES = {
    "node_name": "TEST-NODE",
    "platform_system": "TestOS",
    "platform_machine": "x86_64",
    "username": "test_user",
}

TEST_SECRET = "test-shared-secret-do-not-use-in-production"
TEST_PAYLOAD = {"project": "GRID-main", "version": "2.6.1", "files": ["src/grid/__init__.py"]}


@pytest.fixture
def nonce_registry(tmp_path: Path) -> NonceRegistry:
    """Create a temporary nonce registry backed by a file."""
    registry_path = tmp_path / "nonce_registry.json"
    return NonceRegistry(registry_path, max_age_seconds=600.0)


@pytest.fixture
def memory_nonce_registry() -> NonceRegistry:
    """Create an in-memory nonce registry (no persistence)."""
    return NonceRegistry(None, max_age_seconds=600.0)


@pytest.fixture
def sealed_envelope(nonce_registry: NonceRegistry) -> TransitionEnvelope:
    """Create a sealed test envelope."""
    return seal_envelope(
        TEST_PAYLOAD,
        user_secret=TEST_SECRET,
        nonce_registry=nonce_registry,
        scope=ScopeDeclaration(
            permissions=(PERM_DEPLOY, PERM_RUN_TESTS, PERM_READ_ONLY),
            target_project="GRID-main",
        ),
        sealed_by="test_suite",
        tests_passed=True,
        lint_passed=True,
        machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
        metadata={"test": True},
    )


@pytest.fixture
def gate_keeper(nonce_registry: NonceRegistry, tmp_path: Path) -> GateKeeper:
    """Create a GateKeeper instance for testing."""
    audit_path = tmp_path / "audit.ndjson"
    return GateKeeper(
        user_secret=TEST_SECRET,
        nonce_registry=nonce_registry,
        audit_path=audit_path,
        max_age_seconds=600.0,
        require_tests=True,
        require_lint=False,
        machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
    )


# ═══════════════════════════════════════════════════════════════════════
# Fingerprint Tests
# ═══════════════════════════════════════════════════════════════════════


class TestComputeUserFingerprint:
    """Tests for HMAC-SHA256 user fingerprint computation."""

    def test_deterministic(self) -> None:
        """Same inputs produce the same fingerprint."""
        fp1 = compute_user_fingerprint(TEST_SECRET, machine_id="machine-abc")
        fp2 = compute_user_fingerprint(TEST_SECRET, machine_id="machine-abc")
        assert fp1 == fp2

    def test_different_secret_different_fingerprint(self) -> None:
        """Different secrets produce different fingerprints."""
        fp1 = compute_user_fingerprint("secret-A", machine_id="machine-abc")
        fp2 = compute_user_fingerprint("secret-B", machine_id="machine-abc")
        assert fp1 != fp2

    def test_different_machine_different_fingerprint(self) -> None:
        """Different machine IDs produce different fingerprints."""
        fp1 = compute_user_fingerprint(TEST_SECRET, machine_id="machine-A")
        fp2 = compute_user_fingerprint(TEST_SECRET, machine_id="machine-B")
        assert fp1 != fp2

    def test_extra_context_changes_fingerprint(self) -> None:
        """Adding extra context changes the fingerprint."""
        fp1 = compute_user_fingerprint(TEST_SECRET, machine_id="m1")
        fp2 = compute_user_fingerprint(TEST_SECRET, machine_id="m1", extra_context="session-123")
        assert fp1 != fp2

    def test_empty_secret_raises(self) -> None:
        """Empty secret raises ValueError."""
        with pytest.raises(ValueError, match="user_secret must not be empty"):
            compute_user_fingerprint("", machine_id="machine-abc")

    def test_hex_format(self) -> None:
        """Fingerprint is a valid hex string of correct length (SHA-256 = 64 hex chars)."""
        fp = compute_user_fingerprint(TEST_SECRET, machine_id="m1")
        assert len(fp) == 64
        int(fp, 16)  # Should not raise


class TestComputeMachineFingerprint:
    """Tests for SHA-256 machine fingerprint computation."""

    def test_deterministic_with_overrides(self) -> None:
        """Same overrides produce the same fingerprint."""
        fp1 = compute_machine_fingerprint(**MACHINE_FP_OVERRIDES)
        fp2 = compute_machine_fingerprint(**MACHINE_FP_OVERRIDES)
        assert fp1 == fp2

    def test_different_node_different_fingerprint(self) -> None:
        """Different node names produce different fingerprints."""
        fp1 = compute_machine_fingerprint(node_name="A", platform_system="X", platform_machine="Y", username="U")
        fp2 = compute_machine_fingerprint(node_name="B", platform_system="X", platform_machine="Y", username="U")
        assert fp1 != fp2

    def test_hex_format(self) -> None:
        """Machine fingerprint is a valid 64-char hex string."""
        fp = compute_machine_fingerprint(**MACHINE_FP_OVERRIDES)
        assert len(fp) == 64
        int(fp, 16)


class TestComputePayloadHash:
    """Tests for SHA-256 payload hashing."""

    def test_deterministic(self) -> None:
        """Same payload produces the same hash."""
        h1 = compute_payload_hash(TEST_PAYLOAD)
        h2 = compute_payload_hash(TEST_PAYLOAD)
        assert h1 == h2

    def test_dict_key_order_irrelevant(self) -> None:
        """Dict key order does not affect hash (canonical JSON with sorted keys)."""
        d1 = {"b": 2, "a": 1}
        d2 = {"a": 1, "b": 2}
        assert compute_payload_hash(d1) == compute_payload_hash(d2)

    def test_different_payload_different_hash(self) -> None:
        """Different payloads produce different hashes."""
        h1 = compute_payload_hash({"x": 1})
        h2 = compute_payload_hash({"x": 2})
        assert h1 != h2

    def test_string_payload(self) -> None:
        """String payloads are hashable."""
        h = compute_payload_hash("hello world")
        assert len(h) == 64

    def test_list_payload(self) -> None:
        """List payloads are hashable."""
        h = compute_payload_hash([1, 2, 3])
        assert len(h) == 64


class TestFingerprintsMatch:
    """Tests for timing-safe fingerprint comparison."""

    def test_match(self) -> None:
        """Identical fingerprints match."""
        fp = compute_payload_hash({"test": True})
        assert fingerprints_match(fp, fp) is True

    def test_no_match(self) -> None:
        """Different fingerprints do not match."""
        fp1 = compute_payload_hash({"a": 1})
        fp2 = compute_payload_hash({"b": 2})
        assert fingerprints_match(fp1, fp2) is False

    def test_timing_safe(self) -> None:
        """Comparison uses timing-safe function (via hmac.compare_digest)."""
        fp = "a" * 64
        # Contract test — verify the function produces correct results via compare_digest
        assert fingerprints_match(fp, fp) is True
        assert fingerprints_match(fp, "b" * 64) is False


# ═══════════════════════════════════════════════════════════════════════
# Nonce Registry Tests
# ═══════════════════════════════════════════════════════════════════════


class TestNonceRegistry:
    """Tests for the single-use nonce registry."""

    def test_generate_returns_hex(self, memory_nonce_registry: NonceRegistry) -> None:
        """Generated nonce is a valid hex string."""
        nonce = memory_nonce_registry.generate()
        assert len(nonce) == 32  # UUID4 hex = 32 chars
        int(nonce, 16)

    def test_generated_nonces_are_unique(self, memory_nonce_registry: NonceRegistry) -> None:
        """Each generated nonce is unique."""
        nonces = {memory_nonce_registry.generate() for _ in range(100)}
        assert len(nonces) == 100

    def test_validate_fresh_nonce(self, memory_nonce_registry: NonceRegistry) -> None:
        """A freshly generated nonce validates successfully."""
        nonce = memory_nonce_registry.generate()
        valid, reason = memory_nonce_registry.validate(nonce)
        assert valid is True
        assert reason == "valid"

    def test_validate_unknown_nonce(self, memory_nonce_registry: NonceRegistry) -> None:
        """An unknown nonce is rejected."""
        valid, reason = memory_nonce_registry.validate("nonexistent")
        assert valid is False
        assert reason == "nonce_unknown"

    def test_burn_nonce(self, memory_nonce_registry: NonceRegistry) -> None:
        """A nonce can be burned exactly once."""
        nonce = memory_nonce_registry.generate()
        ok, reason = memory_nonce_registry.burn(nonce)
        assert ok is True
        assert reason == "burned"
        assert memory_nonce_registry.is_burned(nonce) is True

    def test_burn_already_burned_nonce(self, memory_nonce_registry: NonceRegistry) -> None:
        """Burning an already-burned nonce fails (replay prevention)."""
        nonce = memory_nonce_registry.generate()
        memory_nonce_registry.burn(nonce)
        ok, reason = memory_nonce_registry.burn(nonce)
        assert ok is False
        assert reason == "nonce_already_burned"

    def test_burn_unknown_nonce(self, memory_nonce_registry: NonceRegistry) -> None:
        """Burning an unknown nonce fails."""
        ok, reason = memory_nonce_registry.burn("nonexistent")
        assert ok is False
        assert reason == "nonce_unknown"

    def test_expired_nonce_rejected(self) -> None:
        """An expired nonce is rejected on validation and burn."""
        registry = NonceRegistry(None, max_age_seconds=0.01, auto_prune=False)
        nonce = registry.generate()
        time.sleep(0.05)
        valid, reason = registry.validate(nonce)
        assert valid is False
        assert reason == "nonce_expired"

    def test_persistence(self, tmp_path: Path) -> None:
        """Nonce registry persists across instances."""
        path = tmp_path / "registry.json"
        reg1 = NonceRegistry(path, max_age_seconds=600.0)
        nonce = reg1.generate(envelope_id="env-1")

        # Create a second registry from the same file
        reg2 = NonceRegistry(path, max_age_seconds=600.0)
        assert reg2.contains(nonce) is True
        valid, reason = reg2.validate(nonce)
        assert valid is True

    def test_contains(self, memory_nonce_registry: NonceRegistry) -> None:
        """contains() returns True for registered nonces."""
        nonce = memory_nonce_registry.generate()
        assert memory_nonce_registry.contains(nonce) is True
        assert memory_nonce_registry.contains("nonexistent") is False

    def test_count_properties(self, memory_nonce_registry: NonceRegistry) -> None:
        """Count properties reflect registry state."""
        n1 = memory_nonce_registry.generate()
        _ = memory_nonce_registry.generate()
        assert memory_nonce_registry.count == 2
        assert memory_nonce_registry.active_count == 2
        assert memory_nonce_registry.burned_count == 0

        memory_nonce_registry.burn(n1)
        assert memory_nonce_registry.active_count == 1
        assert memory_nonce_registry.burned_count == 1

    def test_get_entry(self, memory_nonce_registry: NonceRegistry) -> None:
        """get_entry() returns a copy of the nonce entry."""
        nonce = memory_nonce_registry.generate(envelope_id="env-1", source="E:\\")
        entry = memory_nonce_registry.get_entry(nonce)
        assert entry is not None
        assert entry.nonce == nonce
        assert entry.envelope_id == "env-1"
        assert entry.source == "E:\\"
        assert entry.burned is False

    def test_get_entry_returns_none_for_unknown(self, memory_nonce_registry: NonceRegistry) -> None:
        """get_entry() returns None for unknown nonces."""
        assert memory_nonce_registry.get_entry("nonexistent") is None

    def test_clear(self, memory_nonce_registry: NonceRegistry) -> None:
        """clear() removes all nonces."""
        memory_nonce_registry.generate()
        memory_nonce_registry.generate()
        assert memory_nonce_registry.count == 2
        memory_nonce_registry.clear()
        assert memory_nonce_registry.count == 0

    def test_prune_expired(self) -> None:
        """prune_expired() removes expired nonces."""
        registry = NonceRegistry(None, max_age_seconds=0.01, auto_prune=False)
        registry.generate()
        registry.generate()
        time.sleep(0.05)
        pruned = registry.prune_expired()
        assert pruned == 2
        assert registry.count == 0

    def test_to_dict(self, memory_nonce_registry: NonceRegistry) -> None:
        """to_dict() returns a serializable dict."""
        memory_nonce_registry.generate()
        d = memory_nonce_registry.to_dict()
        assert "max_age_seconds" in d
        assert "nonces" in d
        assert len(d["nonces"]) == 1


# ═══════════════════════════════════════════════════════════════════════
# Envelope Tests
# ═══════════════════════════════════════════════════════════════════════


class TestScopeDeclaration:
    """Tests for ScopeDeclaration."""

    def test_default_is_read_only(self) -> None:
        """Default scope is read_only."""
        scope = ScopeDeclaration()
        assert scope.permissions == ("read_only",)
        assert scope.network_allowed is False

    def test_roundtrip(self) -> None:
        """ScopeDeclaration roundtrips through dict."""
        scope = ScopeDeclaration(
            permissions=(PERM_DEPLOY, PERM_RUN_TESTS),
            target_project="GRID-main",
            target_path="/deploy/grid",
            max_execution_time_seconds=120,
            network_allowed=True,
            notes="test scope",
        )
        d = scope.to_dict()
        restored = ScopeDeclaration.from_dict(d)
        assert restored.permissions == scope.permissions
        assert restored.target_project == scope.target_project
        assert restored.network_allowed is True
        assert restored.notes == "test scope"


class TestTransitionEnvelope:
    """Tests for TransitionEnvelope and seal_envelope."""

    def test_seal_creates_valid_envelope(self, sealed_envelope: TransitionEnvelope) -> None:
        """seal_envelope produces an envelope with all required fields."""
        assert sealed_envelope.envelope_id is not None
        assert sealed_envelope.payload == TEST_PAYLOAD
        assert len(sealed_envelope.payload_hash) == 64
        assert len(sealed_envelope.nonce) == 32
        assert sealed_envelope.timestamp > 0
        assert len(sealed_envelope.user_fingerprint) == 64
        assert len(sealed_envelope.machine_fingerprint) == 64
        assert sealed_envelope.scope is not None
        assert sealed_envelope.tests_passed is True
        assert sealed_envelope.lint_passed is True
        assert sealed_envelope.sealed_by == "test_suite"

    def test_payload_hash_matches(self, sealed_envelope: TransitionEnvelope) -> None:
        """Payload hash matches recomputed hash."""
        recomputed = compute_payload_hash(sealed_envelope.payload)
        assert fingerprints_match(recomputed, sealed_envelope.payload_hash)

    def test_is_quality_gated(self, sealed_envelope: TransitionEnvelope) -> None:
        """is_quality_gated returns True when both tests and lint passed."""
        assert sealed_envelope.is_quality_gated is True

    def test_age_seconds(self, sealed_envelope: TransitionEnvelope) -> None:
        """age_seconds is a positive float close to 0."""
        assert sealed_envelope.age_seconds >= 0
        assert sealed_envelope.age_seconds < 5  # Should be near-instant in tests

    def test_roundtrip_dict(self, sealed_envelope: TransitionEnvelope) -> None:
        """Envelope roundtrips through dict."""
        d = sealed_envelope.to_dict()
        restored = TransitionEnvelope.from_dict(d)
        assert restored.envelope_id == sealed_envelope.envelope_id
        assert restored.payload == sealed_envelope.payload
        assert restored.payload_hash == sealed_envelope.payload_hash
        assert restored.nonce == sealed_envelope.nonce
        assert restored.user_fingerprint == sealed_envelope.user_fingerprint
        assert restored.scope.permissions == sealed_envelope.scope.permissions

    def test_roundtrip_json(self, sealed_envelope: TransitionEnvelope) -> None:
        """Envelope roundtrips through JSON string."""
        json_str = sealed_envelope.to_json()
        restored = TransitionEnvelope.from_json(json_str)
        assert restored.envelope_id == sealed_envelope.envelope_id
        assert restored.payload_hash == sealed_envelope.payload_hash

    def test_roundtrip_file(self, sealed_envelope: TransitionEnvelope, tmp_path: Path) -> None:
        """Envelope roundtrips through file."""
        file_path = tmp_path / "envelope.json"
        sealed_envelope.write_to_file(file_path)
        assert file_path.exists()

        restored = TransitionEnvelope.from_file(file_path)
        assert restored.envelope_id == sealed_envelope.envelope_id
        assert restored.payload == sealed_envelope.payload
        assert restored.payload_hash == sealed_envelope.payload_hash

    def test_seal_empty_secret_raises(self, nonce_registry: NonceRegistry) -> None:
        """Sealing with empty secret raises ValueError."""
        with pytest.raises(ValueError, match="user_secret must not be empty"):
            seal_envelope(
                TEST_PAYLOAD,
                user_secret="",
                nonce_registry=nonce_registry,
            )

    def test_each_seal_gets_unique_nonce(self, nonce_registry: NonceRegistry) -> None:
        """Each seal_envelope call generates a different nonce."""
        e1 = seal_envelope(
            TEST_PAYLOAD,
            user_secret=TEST_SECRET,
            nonce_registry=nonce_registry,
            machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
        )
        e2 = seal_envelope(
            TEST_PAYLOAD,
            user_secret=TEST_SECRET,
            nonce_registry=nonce_registry,
            machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
        )
        assert e1.nonce != e2.nonce
        assert e1.envelope_id != e2.envelope_id

    def test_default_scope_is_read_only(self, nonce_registry: NonceRegistry) -> None:
        """Envelope sealed without explicit scope defaults to read_only."""
        envelope = seal_envelope(
            TEST_PAYLOAD,
            user_secret=TEST_SECRET,
            nonce_registry=nonce_registry,
            machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
        )
        assert envelope.scope.permissions == ("read_only",)


# ═══════════════════════════════════════════════════════════════════════
# GateKeeper Verification Tests
# ═══════════════════════════════════════════════════════════════════════


class TestGateKeeperFullPass:
    """Tests for the happy path: complete 9-step verification pass."""

    def test_full_pass(
        self,
        gate_keeper: GateKeeper,
        sealed_envelope: TransitionEnvelope,
    ) -> None:
        """A properly sealed envelope passes all 9 steps."""
        result = gate_keeper.verify(sealed_envelope, requested_action=PERM_READ_ONLY)
        assert result.passed is True
        assert result.status == VerificationStatus.PASSED
        assert result.reason is None
        assert len(result.steps) == 9
        assert all(s.status == VerificationStatus.PASSED for s in result.steps)
        assert result.nonce_burned is True

    def test_nonce_burned_after_pass(
        self,
        gate_keeper: GateKeeper,
        sealed_envelope: TransitionEnvelope,
        nonce_registry: NonceRegistry,
    ) -> None:
        """Nonce is burned after successful verification."""
        gate_keeper.verify(sealed_envelope, requested_action=PERM_READ_ONLY)
        assert nonce_registry.is_burned(sealed_envelope.nonce) is True

    def test_audit_log_written(
        self,
        gate_keeper: GateKeeper,
        sealed_envelope: TransitionEnvelope,
        tmp_path: Path,
    ) -> None:
        """Audit log is written after verification."""
        gate_keeper.verify(sealed_envelope, requested_action=PERM_READ_ONLY)
        audit_path = tmp_path / "audit.ndjson"
        assert audit_path.exists()
        lines = audit_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) >= 1
        entry = json.loads(lines[0])
        assert entry["event_type"] == "gate_verification"
        assert entry["status"] == "passed"

    def test_stats_updated_on_pass(
        self,
        gate_keeper: GateKeeper,
        sealed_envelope: TransitionEnvelope,
    ) -> None:
        """Stats are updated after verification."""
        gate_keeper.verify(sealed_envelope, requested_action=PERM_READ_ONLY)
        stats = gate_keeper.stats
        assert stats["total_verifications"] == 1
        assert stats["total_passed"] == 1
        assert stats["total_rejected"] == 0


class TestGateKeeperDryRun:
    """Tests for dry-run verification (no side effects)."""

    def test_dry_run_does_not_burn_nonce(
        self,
        gate_keeper: GateKeeper,
        sealed_envelope: TransitionEnvelope,
        nonce_registry: NonceRegistry,
    ) -> None:
        """Dry-run does not burn the nonce."""
        result = gate_keeper.verify(sealed_envelope, requested_action=PERM_READ_ONLY, dry_run=True)
        assert result.passed is True
        assert result.nonce_burned is False
        assert nonce_registry.is_burned(sealed_envelope.nonce) is False

    def test_dry_run_then_real_pass(
        self,
        gate_keeper: GateKeeper,
        sealed_envelope: TransitionEnvelope,
    ) -> None:
        """Dry-run followed by real verification both pass."""
        dry = gate_keeper.verify(sealed_envelope, requested_action=PERM_READ_ONLY, dry_run=True)
        assert dry.passed is True

        real = gate_keeper.verify(sealed_envelope, requested_action=PERM_READ_ONLY)
        assert real.passed is True
        assert real.nonce_burned is True


class TestGateKeeperRejections:
    """Tests for each rejection reason in the verification pipeline."""

    def test_reject_payload_integrity(
        self,
        gate_keeper: GateKeeper,
        sealed_envelope: TransitionEnvelope,
    ) -> None:
        """Tampering with payload after sealing causes integrity rejection."""
        # Mutate the payload (simulate tampering)
        sealed_envelope.payload["tampered"] = True
        result = gate_keeper.verify(sealed_envelope, requested_action=PERM_READ_ONLY)
        assert result.rejected is True
        assert result.reason == RejectionReason.PAYLOAD_INTEGRITY_FAILED

    def test_reject_fingerprint_mismatch(
        self,
        nonce_registry: NonceRegistry,
        tmp_path: Path,
    ) -> None:
        """Wrong user secret causes fingerprint mismatch rejection."""
        envelope = seal_envelope(
            TEST_PAYLOAD,
            user_secret=TEST_SECRET,
            nonce_registry=nonce_registry,
            tests_passed=True,
            scope=ScopeDeclaration(permissions=(PERM_READ_ONLY,)),
            machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
        )

        # Create gate keeper with WRONG secret
        keeper = GateKeeper(
            user_secret="wrong-secret",
            nonce_registry=nonce_registry,
            audit_path=tmp_path / "audit.ndjson",
            machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
        )
        result = keeper.verify(envelope, requested_action=PERM_READ_ONLY)
        assert result.rejected is True
        assert result.reason == RejectionReason.FINGERPRINT_MISMATCH

    def test_reject_nonce_replay(
        self,
        gate_keeper: GateKeeper,
        sealed_envelope: TransitionEnvelope,
    ) -> None:
        """Replaying a burned nonce is rejected."""
        # First verification passes and burns the nonce
        result1 = gate_keeper.verify(sealed_envelope, requested_action=PERM_READ_ONLY)
        assert result1.passed is True

        # Second verification with same nonce is rejected
        result2 = gate_keeper.verify(sealed_envelope, requested_action=PERM_READ_ONLY)
        assert result2.rejected is True
        assert result2.reason == RejectionReason.NONCE_REPLAY_OR_EXPIRED

    def test_reject_expired_envelope(
        self,
        nonce_registry: NonceRegistry,
        tmp_path: Path,
    ) -> None:
        """An expired envelope is rejected."""
        envelope = seal_envelope(
            TEST_PAYLOAD,
            user_secret=TEST_SECRET,
            nonce_registry=nonce_registry,
            tests_passed=True,
            scope=ScopeDeclaration(permissions=(PERM_READ_ONLY,)),
            machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
        )

        # Create keeper with very short max age
        keeper = GateKeeper(
            user_secret=TEST_SECRET,
            nonce_registry=nonce_registry,
            audit_path=tmp_path / "audit.ndjson",
            max_age_seconds=0.01,
            machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
        )
        time.sleep(0.05)
        result = keeper.verify(envelope, requested_action=PERM_READ_ONLY)
        assert result.rejected is True
        assert result.reason == RejectionReason.ENVELOPE_EXPIRED

    def test_reject_tests_not_passed(
        self,
        nonce_registry: NonceRegistry,
        tmp_path: Path,
    ) -> None:
        """Envelope with tests_passed=False is rejected when require_tests=True."""
        envelope = seal_envelope(
            TEST_PAYLOAD,
            user_secret=TEST_SECRET,
            nonce_registry=nonce_registry,
            tests_passed=False,  # Tests did not pass
            scope=ScopeDeclaration(permissions=(PERM_READ_ONLY,)),
            machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
        )

        keeper = GateKeeper(
            user_secret=TEST_SECRET,
            nonce_registry=nonce_registry,
            audit_path=tmp_path / "audit.ndjson",
            require_tests=True,
            machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
        )
        result = keeper.verify(envelope, requested_action=PERM_READ_ONLY)
        assert result.rejected is True
        assert result.reason == RejectionReason.TESTS_NOT_PASSED

    def test_reject_action_out_of_scope(
        self,
        gate_keeper: GateKeeper,
        nonce_registry: NonceRegistry,
    ) -> None:
        """Requesting an action not in scope permissions is rejected."""
        envelope = seal_envelope(
            TEST_PAYLOAD,
            user_secret=TEST_SECRET,
            nonce_registry=nonce_registry,
            tests_passed=True,
            scope=ScopeDeclaration(permissions=(PERM_READ_ONLY,)),  # Only read_only
            machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
        )

        result = gate_keeper.verify(envelope, requested_action=PERM_DEPLOY)
        assert result.rejected is True
        assert result.reason == RejectionReason.ACTION_OUT_OF_SCOPE

    def test_reject_empty_scope_permissions(
        self,
        gate_keeper: GateKeeper,
        nonce_registry: NonceRegistry,
    ) -> None:
        """Envelope with empty permissions list is rejected."""
        envelope = seal_envelope(
            TEST_PAYLOAD,
            user_secret=TEST_SECRET,
            nonce_registry=nonce_registry,
            tests_passed=True,
            scope=ScopeDeclaration(permissions=()),
            machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
        )

        result = gate_keeper.verify(envelope, requested_action=PERM_READ_ONLY)
        assert result.rejected is True
        assert result.reason == RejectionReason.SCOPE_MISSING

    def test_reject_missing_envelope_fields(
        self,
        gate_keeper: GateKeeper,
    ) -> None:
        """Envelope with missing required fields is rejected."""
        # Create an envelope with empty required fields
        broken = TransitionEnvelope(
            envelope_id="",
            payload=None,
            payload_hash="",
            nonce="",
            timestamp=0.0,
            user_fingerprint="",
            machine_fingerprint="",
            scope=ScopeDeclaration(),
        )
        result = gate_keeper.verify(broken, requested_action=PERM_READ_ONLY)
        assert result.rejected is True
        assert result.reason == RejectionReason.ENVELOPE_PARSE_ERROR


class TestGateKeeperStats:
    """Tests for GateKeeper statistics tracking."""

    def test_stats_track_rejections(
        self,
        nonce_registry: NonceRegistry,
        tmp_path: Path,
    ) -> None:
        """Stats track rejection counts per reason."""
        keeper = GateKeeper(
            user_secret=TEST_SECRET,
            nonce_registry=nonce_registry,
            audit_path=tmp_path / "audit.ndjson",
            machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
        )

        # Create an envelope that will fail tests_passed check
        envelope = seal_envelope(
            TEST_PAYLOAD,
            user_secret=TEST_SECRET,
            nonce_registry=nonce_registry,
            tests_passed=False,
            scope=ScopeDeclaration(permissions=(PERM_READ_ONLY,)),
            machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
        )

        keeper.verify(envelope, requested_action=PERM_READ_ONLY)
        stats = keeper.stats
        assert stats["total_rejected"] == 1
        assert RejectionReason.TESTS_NOT_PASSED in stats["rejection_counts"]


class TestVerifyFromFile:
    """Tests for file-based verification."""

    def test_verify_from_file_pass(
        self,
        gate_keeper: GateKeeper,
        sealed_envelope: TransitionEnvelope,
        tmp_path: Path,
    ) -> None:
        """verify_from_file loads and verifies a sealed envelope from disk."""
        file_path = tmp_path / "envelope.json"
        sealed_envelope.write_to_file(file_path)
        result = gate_keeper.verify_from_file(file_path, requested_action=PERM_READ_ONLY)
        assert result.passed is True

    def test_verify_from_file_missing(
        self,
        gate_keeper: GateKeeper,
        tmp_path: Path,
    ) -> None:
        """verify_from_file rejects a nonexistent file."""
        result = gate_keeper.verify_from_file(tmp_path / "nonexistent.json")
        assert result.rejected is True
        assert result.reason == RejectionReason.ENVELOPE_MISSING

    def test_verify_from_file_corrupt(
        self,
        gate_keeper: GateKeeper,
        tmp_path: Path,
    ) -> None:
        """verify_from_file rejects a corrupt file."""
        corrupt_file = tmp_path / "corrupt.json"
        corrupt_file.write_text("{invalid json", encoding="utf-8")
        result = gate_keeper.verify_from_file(corrupt_file)
        assert result.rejected is True
        assert result.reason == RejectionReason.ENVELOPE_PARSE_ERROR


class TestVerifyEnvelopeConvenience:
    """Tests for the verify_envelope() convenience function."""

    def test_convenience_pass(
        self,
        nonce_registry: NonceRegistry,
        tmp_path: Path,
    ) -> None:
        """verify_envelope() convenience function works end-to-end."""
        envelope = seal_envelope(
            TEST_PAYLOAD,
            user_secret=TEST_SECRET,
            nonce_registry=nonce_registry,
            tests_passed=True,
            scope=ScopeDeclaration(permissions=(PERM_READ_ONLY,)),
            machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
        )

        result = verify_envelope(
            envelope,
            user_secret=TEST_SECRET,
            nonce_registry=nonce_registry,
            audit_path=tmp_path / "audit.ndjson",
            requested_action=PERM_READ_ONLY,
            machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
        )
        assert result.passed is True

    def test_convenience_reject(
        self,
        nonce_registry: NonceRegistry,
        tmp_path: Path,
    ) -> None:
        """verify_envelope() rejects with wrong secret."""
        envelope = seal_envelope(
            TEST_PAYLOAD,
            user_secret=TEST_SECRET,
            nonce_registry=nonce_registry,
            tests_passed=True,
            scope=ScopeDeclaration(permissions=(PERM_READ_ONLY,)),
            machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
        )

        result = verify_envelope(
            envelope,
            user_secret="wrong-secret",
            nonce_registry=nonce_registry,
            audit_path=tmp_path / "audit.ndjson",
            requested_action=PERM_READ_ONLY,
            machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
        )
        assert result.rejected is True
        assert result.reason == RejectionReason.FINGERPRINT_MISMATCH


class TestVerificationResultSerialization:
    """Tests for VerificationResult serialization."""

    def test_to_dict(
        self,
        gate_keeper: GateKeeper,
        sealed_envelope: TransitionEnvelope,
    ) -> None:
        """VerificationResult serializes to a dict."""
        result = gate_keeper.verify(sealed_envelope, requested_action=PERM_READ_ONLY)
        d = result.to_dict()
        assert "envelope_id" in d
        assert "status" in d
        assert "steps" in d
        assert isinstance(d["steps"], list)
        assert "total_duration_ms" in d

    def test_to_json(
        self,
        gate_keeper: GateKeeper,
        sealed_envelope: TransitionEnvelope,
    ) -> None:
        """VerificationResult serializes to valid JSON."""
        result = gate_keeper.verify(sealed_envelope, requested_action=PERM_READ_ONLY)
        json_str = result.to_json()
        parsed = json.loads(json_str)
        assert parsed["status"] == "passed"
        assert len(parsed["steps"]) == 9


# ═══════════════════════════════════════════════════════════════════════
# Integration Tests
# ═══════════════════════════════════════════════════════════════════════


class TestEndToEndPipeline:
    """End-to-end integration tests for the full seal → verify pipeline."""

    def test_full_pipeline(self, tmp_path: Path) -> None:
        """Complete seal → write → read → verify pipeline."""
        registry_path = tmp_path / "registry.json"
        audit_path = tmp_path / "audit.ndjson"
        envelope_path = tmp_path / "envelope.json"

        nonce_registry = NonceRegistry(registry_path, max_age_seconds=600.0)

        # Seal
        envelope = seal_envelope(
            {"project": "echoes", "version": "1.0.0"},
            user_secret=TEST_SECRET,
            nonce_registry=nonce_registry,
            scope=ScopeDeclaration(
                permissions=(PERM_DEPLOY, PERM_RUN_TESTS, PERM_START_SERVER),
                target_project="echoes",
            ),
            tests_passed=True,
            lint_passed=True,
            sealed_by="integration_test",
            machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
        )

        # Write to disk
        envelope.write_to_file(envelope_path)

        # Create a NEW nonce registry from the same file (simulates process restart)
        verify_registry = NonceRegistry(registry_path, max_age_seconds=600.0)

        # Verify from file
        keeper = GateKeeper(
            user_secret=TEST_SECRET,
            nonce_registry=verify_registry,
            audit_path=audit_path,
            machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
        )
        result = keeper.verify_from_file(envelope_path, requested_action=PERM_DEPLOY)
        assert result.passed is True
        assert result.nonce_burned is True

        # Verify nonce is burned in the persistent registry
        final_registry = NonceRegistry(registry_path, max_age_seconds=600.0)
        assert final_registry.is_burned(envelope.nonce) is True

        # Replay attempt should fail
        replay_registry = NonceRegistry(registry_path, max_age_seconds=600.0)
        replay_keeper = GateKeeper(
            user_secret=TEST_SECRET,
            nonce_registry=replay_registry,
            audit_path=audit_path,
            machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
        )
        replay_result = replay_keeper.verify_from_file(envelope_path, requested_action=PERM_DEPLOY)
        assert replay_result.rejected is True
        assert replay_result.reason == RejectionReason.NONCE_REPLAY_OR_EXPIRED

    def test_tampered_payload_detected(self, tmp_path: Path) -> None:
        """Payload modification after sealing is detected."""
        nonce_registry = NonceRegistry(tmp_path / "registry.json", max_age_seconds=600.0)

        envelope = seal_envelope(
            {"clean": True},
            user_secret=TEST_SECRET,
            nonce_registry=nonce_registry,
            tests_passed=True,
            scope=ScopeDeclaration(permissions=(PERM_READ_ONLY,)),
            machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
        )

        # Write envelope, then tamper with the file
        file_path = tmp_path / "tampered.json"
        envelope.write_to_file(file_path)

        # Read the JSON, modify the payload, write back
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        data["payload"]["injected"] = "malicious"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        keeper = GateKeeper(
            user_secret=TEST_SECRET,
            nonce_registry=nonce_registry,
            audit_path=tmp_path / "audit.ndjson",
            machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
        )
        result = keeper.verify_from_file(file_path, requested_action=PERM_READ_ONLY)
        assert result.rejected is True
        assert result.reason == RejectionReason.PAYLOAD_INTEGRITY_FAILED

    def test_multiple_envelopes_independent(self, tmp_path: Path) -> None:
        """Multiple envelopes can be sealed and verified independently."""
        nonce_registry = NonceRegistry(tmp_path / "registry.json", max_age_seconds=600.0)
        audit_path = tmp_path / "audit.ndjson"

        envelopes = []
        for i in range(5):
            e = seal_envelope(
                {"batch": i},
                user_secret=TEST_SECRET,
                nonce_registry=nonce_registry,
                tests_passed=True,
                scope=ScopeDeclaration(permissions=(PERM_READ_ONLY,)),
                machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
            )
            envelopes.append(e)

        keeper = GateKeeper(
            user_secret=TEST_SECRET,
            nonce_registry=nonce_registry,
            audit_path=audit_path,
            machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
        )

        for e in envelopes:
            result = keeper.verify(e, requested_action=PERM_READ_ONLY)
            assert result.passed is True

        assert keeper.stats["total_passed"] == 5
        assert keeper.stats["total_rejected"] == 0
