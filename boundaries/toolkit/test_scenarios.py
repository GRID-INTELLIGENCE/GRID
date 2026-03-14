"""
Test Scenarios for the Transition Gate Toolkit.

Provides 9 structured test hooks, one for each verification step,
demonstrating specific attack vectors, edge cases, and security measures.

Each scenario can be run independently to test a specific aspect of the
transition gate security model.

Usage:
    from boundaries.toolkit.test_scenarios import run_scenario, SCENARIOS

    # Run a specific scenario
    result = run_scenario("replay_attack")

    # Run all scenarios
    results = run_all_scenarios()
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from boundaries.transition_gate.envelope import (
    PERM_DEPLOY,
    PERM_READ_ONLY,
    PERM_RUN_TESTS,
    ScopeDeclaration,
    TransitionEnvelope,
    seal_envelope,
)
from boundaries.transition_gate.gate_keeper import (
    GateKeeper,
    RejectionReason,
    VerificationResult,
)
from boundaries.transition_gate.nonce import NonceRegistry

# ═══════════════════════════════════════════════════════════════════════════
# Test Data and Constants
# ═══════════════════════════════════════════════════════════════════════════

TEST_SECRET = "test-secret-for-toolkit-scenarios"
TEST_SECRET_ALT = "different-secret-for-attack-scenarios"

MACHINE_FP_OVERRIDES = {
    "node_name": "TEST-NODE-TOOLKIT",
    "platform_system": "TestOS",
    "platform_machine": "x86_64",
    "username": "test_user",
}

SAMPLE_PAYLOAD = {
    "project": "GRID-main",
    "version": "2.7.0",
    "files": ["src/grid/core.py", "src/grid/api.py"],
    "checksums": {"src/grid/core.py": "abc123"},
}


# ═══════════════════════════════════════════════════════════════════════════
# Scenario Result Types
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class ScenarioResult:
    """
    Result of running a test scenario.

    Contains the verification result plus scenario-specific metadata
    explaining what was tested and why.
    """

    name: str
    description: str
    step_tested: str
    attack_vector: str | None
    verification_result: VerificationResult | None
    passed: bool  # Did the scenario complete as expected?
    expected_rejection: bool  # Was rejection the expected outcome?
    notes: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "step_tested": self.step_tested,
            "attack_vector": self.attack_vector,
            "verification_passed": self.verification_result.passed if self.verification_result else None,
            "scenario_passed": self.passed,
            "expected_rejection": self.expected_rejection,
            "notes": self.notes,
            "metadata": self.metadata,
        }


# ═══════════════════════════════════════════════════════════════════════════
# Scenario Registry
# ═══════════════════════════════════════════════════════════════════════════

SCENARIOS: dict[str, Callable[[Path], ScenarioResult]] = {}


def register_scenario(name: str, description: str, step: str, attack: str | None = None):
    """
    Decorator to register a test scenario.

    Args:
        name: Short identifier for the scenario
        description: Human-readable description
        step: Which verification step this tests
        attack: What attack vector this simulates (if any)
    """

    def decorator(func: Callable[[Path], ScenarioResult]) -> Callable[[Path], ScenarioResult]:
        SCENARIOS[name] = func
        func._scenario_meta = {
            "name": name,
            "description": description,
            "step": step,
            "attack": attack,
        }
        return func

    return decorator


# ═══════════════════════════════════════════════════════════════════════════
# STEP 1: envelope_exists - Envelope presence and parseability
# ═══════════════════════════════════════════════════════════════════════════


@register_scenario(
    "envelope_missing", "Test rejection when envelope file doesn't exist", "envelope_exists", "missing_file"
)
def scenario_envelope_missing(tmp_path: Path) -> ScenarioResult:
    """Test that missing envelope files are properly rejected."""
    nonce_registry = NonceRegistry(tmp_path / "nonce.json", max_age_seconds=600.0)
    audit_path = tmp_path / "audit.ndjson"

    gate_keeper = GateKeeper(
        user_secret=TEST_SECRET,
        nonce_registry=nonce_registry,
        audit_path=audit_path,
        machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
    )

    # Try to verify a non-existent file
    result = gate_keeper.verify_from_file(tmp_path / "nonexistent.json")

    notes = [
        "Attempted to verify a file that doesn't exist",
        f"Got rejection reason: {result.reason}",
    ]

    return ScenarioResult(
        name="envelope_missing",
        description="Missing envelope file rejection",
        step_tested="envelope_exists",
        attack_vector="missing_file",
        verification_result=result,
        passed=result.rejected and result.reason == RejectionReason.ENVELOPE_MISSING,
        expected_rejection=True,
        notes=notes,
    )


@register_scenario(
    "envelope_corrupted", "Test rejection when envelope JSON is corrupted", "envelope_exists", "data_corruption"
)
def scenario_envelope_corrupted(tmp_path: Path) -> ScenarioResult:
    """Test that corrupted envelope JSON is properly rejected."""
    # Create a corrupted JSON file
    corrupted_file = tmp_path / "corrupted.json"
    corrupted_file.write_text('{"invalid json: missing closing brace', encoding="utf-8")

    nonce_registry = NonceRegistry(tmp_path / "nonce.json", max_age_seconds=600.0)
    audit_path = tmp_path / "audit.ndjson"

    gate_keeper = GateKeeper(
        user_secret=TEST_SECRET,
        nonce_registry=nonce_registry,
        audit_path=audit_path,
        machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
    )

    result = gate_keeper.verify_from_file(corrupted_file)

    notes = [
        "Created file with malformed JSON",
        f"Got rejection reason: {result.reason}",
    ]

    return ScenarioResult(
        name="envelope_corrupted",
        description="Corrupted envelope JSON rejection",
        step_tested="envelope_exists",
        attack_vector="data_corruption",
        verification_result=result,
        passed=result.rejected and result.reason == RejectionReason.ENVELOPE_PARSE_ERROR,
        expected_rejection=True,
        notes=notes,
    )


# ═══════════════════════════════════════════════════════════════════════════
# STEP 2: payload_integrity - SHA-256 payload hash verification
# ═══════════════════════════════════════════════════════════════════════════


@register_scenario("payload_tampering", "Test detection of payload tampering", "payload_integrity", "man-in-the-middle")
def scenario_payload_tampering(tmp_path: Path) -> ScenarioResult:
    """Test that modified payloads are detected via hash mismatch."""
    nonce_registry = NonceRegistry(tmp_path / "nonce.json", max_age_seconds=600.0)

    # Create legitimate envelope
    envelope = seal_envelope(
        SAMPLE_PAYLOAD,
        user_secret=TEST_SECRET,
        nonce_registry=nonce_registry,
        scope=ScopeDeclaration(permissions=(PERM_DEPLOY,)),
        tests_passed=True,
        lint_passed=True,
        machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
    )

    # Tamper with the payload after sealing
    envelope_dict = envelope.to_dict()
    envelope_dict["payload"]["malicious"] = "injected_data"

    # Save tampered envelope
    tampered_file = tmp_path / "tampered.json"
    with open(tampered_file, "w", encoding="utf-8") as f:
        json.dump(envelope_dict, f)

    # Try to verify tampered envelope
    audit_path = tmp_path / "audit.ndjson"
    gate_keeper = GateKeeper(
        user_secret=TEST_SECRET,
        nonce_registry=nonce_registry,
        audit_path=audit_path,
        machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
    )

    tampered_envelope = TransitionEnvelope.from_file(tampered_file)
    result = gate_keeper.verify(tampered_envelope)

    notes = [
        "Original payload hash computed at seal time",
        "Payload was modified after sealing (injection attack simulation)",
        "Hash verification should detect the tampering",
        f"Got rejection reason: {result.reason}",
    ]

    return ScenarioResult(
        name="payload_tampering",
        description="Payload tampering detection",
        step_tested="payload_integrity",
        attack_vector="man-in-the-middle",
        verification_result=result,
        passed=result.rejected and result.reason == RejectionReason.PAYLOAD_INTEGRITY_FAILED,
        expected_rejection=True,
        notes=notes,
    )


# ═══════════════════════════════════════════════════════════════════════════
# STEP 3: fingerprint_match - HMAC-SHA256 user fingerprint verification
# ═══════════════════════════════════════════════════════════════════════════


@register_scenario(
    "wrong_secret", "Test rejection with incorrect shared secret", "fingerprint_match", "credential_compromise"
)
def scenario_wrong_secret(tmp_path: Path) -> ScenarioResult:
    """Test that wrong shared secret causes fingerprint mismatch."""
    nonce_registry = NonceRegistry(tmp_path / "nonce.json", max_age_seconds=600.0)

    # Seal with correct secret
    envelope = seal_envelope(
        SAMPLE_PAYLOAD,
        user_secret=TEST_SECRET,
        nonce_registry=nonce_registry,
        scope=ScopeDeclaration(permissions=(PERM_DEPLOY,)),
        tests_passed=True,
        lint_passed=True,
        machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
    )

    # Verify with wrong secret
    audit_path = tmp_path / "audit.ndjson"
    gate_keeper = GateKeeper(
        user_secret=TEST_SECRET_ALT,  # Different secret!
        nonce_registry=nonce_registry,
        audit_path=audit_path,
        machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
    )

    result = gate_keeper.verify(envelope)

    notes = [
        f"Sealed with secret: {TEST_SECRET[:10]}...",
        f"Verified with secret: {TEST_SECRET_ALT[:10]}...",
        "HMAC-SHA256 fingerprint should not match",
        f"Got rejection reason: {result.reason}",
    ]

    return ScenarioResult(
        name="wrong_secret",
        description="Wrong shared secret rejection",
        step_tested="fingerprint_match",
        attack_vector="credential_compromise",
        verification_result=result,
        passed=result.rejected and result.reason == RejectionReason.FINGERPRINT_MISMATCH,
        expected_rejection=True,
        notes=notes,
    )


@register_scenario("machine_binding", "Test machine fingerprint binding", "fingerprint_match", "machine_mismatch")
def scenario_machine_binding(tmp_path: Path) -> ScenarioResult:
    """Test that fingerprints are bound to specific machines."""
    nonce_registry = NonceRegistry(tmp_path / "nonce.json", max_age_seconds=600.0)

    # Seal with specific machine fingerprint
    envelope = seal_envelope(
        SAMPLE_PAYLOAD,
        user_secret=TEST_SECRET,
        nonce_registry=nonce_registry,
        scope=ScopeDeclaration(permissions=(PERM_DEPLOY,)),
        tests_passed=True,
        lint_passed=True,
        machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
    )

    # Try to verify with different machine attributes
    different_overrides = {
        "node_name": "DIFFERENT-NODE",
        "platform_system": "DifferentOS",
        "platform_machine": "arm64",
        "username": "different_user",
    }

    audit_path = tmp_path / "audit.ndjson"
    gate_keeper = GateKeeper(
        user_secret=TEST_SECRET,
        nonce_registry=nonce_registry,
        audit_path=audit_path,
        machine_fingerprint_overrides=different_overrides,  # Different machine!
    )

    result = gate_keeper.verify(envelope)

    notes = [
        f"Sealed with machine: {MACHINE_FP_OVERRIDES['node_name']}",
        f"Verified with machine: {different_overrides['node_name']}",
        "User fingerprint includes machine binding",
        f"Got rejection reason: {result.reason}",
    ]

    return ScenarioResult(
        name="machine_binding",
        description="Machine fingerprint binding test",
        step_tested="fingerprint_match",
        attack_vector="machine_mismatch",
        verification_result=result,
        passed=result.rejected and result.reason == RejectionReason.FINGERPRINT_MISMATCH,
        expected_rejection=True,
        notes=notes,
    )


# ═══════════════════════════════════════════════════════════════════════════
# STEP 4: nonce_valid - Single-use nonce validation
# ═══════════════════════════════════════════════════════════════════════════


@register_scenario("replay_attack", "Test replay attack prevention via nonce burning", "nonce_valid", "replay_attack")
def scenario_replay_attack(tmp_path: Path) -> ScenarioResult:
    """Test that replay attacks are prevented via nonce burning."""
    nonce_registry = NonceRegistry(tmp_path / "nonce.json", max_age_seconds=600.0)

    # Create envelope
    envelope = seal_envelope(
        SAMPLE_PAYLOAD,
        user_secret=TEST_SECRET,
        nonce_registry=nonce_registry,
        scope=ScopeDeclaration(permissions=(PERM_DEPLOY,)),
        tests_passed=True,
        lint_passed=True,
        machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
    )

    audit_path = tmp_path / "audit.ndjson"
    gate_keeper = GateKeeper(
        user_secret=TEST_SECRET,
        nonce_registry=nonce_registry,
        audit_path=audit_path,
        machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
    )

    # First verification should succeed
    result1 = gate_keeper.verify(envelope)

    # Second verification should fail (replay)
    result2 = gate_keeper.verify(envelope)

    notes = [
        "First verification should PASS (nonce valid and not burned)",
        f"First result: {result1.status} (nonce_burned={result1.nonce_burned})",
        "Second verification should REJECT (replay attack detected)",
        f"Second result: {result2.status} (reason={result2.reason})",
    ]

    return ScenarioResult(
        name="replay_attack",
        description="Replay attack prevention test",
        step_tested="nonce_valid",
        attack_vector="replay_attack",
        verification_result=result2,
        passed=result1.passed and result2.rejected and result2.reason == RejectionReason.NONCE_REPLAY_OR_EXPIRED,
        expected_rejection=True,
        notes=notes,
        metadata={
            "first_verification_passed": result1.passed,
            "first_nonce_burned": result1.nonce_burned,
            "second_verification_rejected": result2.rejected,
        },
    )


@register_scenario("unknown_nonce", "Test rejection of unknown/forged nonce", "nonce_valid", "nonce_forgery")
def scenario_unknown_nonce(tmp_path: Path) -> ScenarioResult:
    """Test that unknown nonces are rejected."""
    nonce_registry = NonceRegistry(tmp_path / "nonce.json", max_age_seconds=600.0)

    # Create envelope with legitimate nonce
    envelope = seal_envelope(
        SAMPLE_PAYLOAD,
        user_secret=TEST_SECRET,
        nonce_registry=nonce_registry,
        scope=ScopeDeclaration(permissions=(PERM_DEPLOY,)),
        tests_passed=True,
        lint_passed=True,
        machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
    )

    # Create fresh registry (loses all known nonces)
    fresh_registry = NonceRegistry(tmp_path / "fresh_nonce.json", max_age_seconds=600.0)

    audit_path = tmp_path / "audit.ndjson"
    gate_keeper = GateKeeper(
        user_secret=TEST_SECRET,
        nonce_registry=fresh_registry,  # Fresh registry doesn't know the nonce
        audit_path=audit_path,
        machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
    )

    result = gate_keeper.verify(envelope)

    notes = [
        "Envelope sealed with nonce from original registry",
        "Verifying with fresh registry (nonce unknown)",
        "Should reject as unknown/forged nonce",
        f"Got rejection reason: {result.reason}",
    ]

    return ScenarioResult(
        name="unknown_nonce",
        description="Unknown nonce rejection test",
        step_tested="nonce_valid",
        attack_vector="nonce_forgery",
        verification_result=result,
        passed=result.rejected and result.reason == RejectionReason.NONCE_REPLAY_OR_EXPIRED,
        expected_rejection=True,
        notes=notes,
    )


# ═══════════════════════════════════════════════════════════════════════════
# STEP 5: timestamp_fresh - Envelope age verification
# ═══════════════════════════════════════════════════════════════════════════


@register_scenario("expired_envelope", "Test rejection of expired/stale envelopes", "timestamp_fresh", "stale_data")
def scenario_expired_envelope(tmp_path: Path) -> ScenarioResult:
    """Test that old envelopes are rejected as expired."""
    # Use short expiry for testing
    nonce_registry = NonceRegistry(tmp_path / "nonce.json", max_age_seconds=600.0)

    # Create envelope
    envelope = seal_envelope(
        SAMPLE_PAYLOAD,
        user_secret=TEST_SECRET,
        nonce_registry=nonce_registry,
        scope=ScopeDeclaration(permissions=(PERM_DEPLOY,)),
        tests_passed=True,
        lint_passed=True,
        machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
    )

    # Manually set timestamp to be very old
    old_timestamp = time.time() - 7200  # 2 hours ago
    envelope_dict = envelope.to_dict()
    envelope_dict["timestamp"] = old_timestamp

    audit_path = tmp_path / "audit.ndjson"
    gate_keeper = GateKeeper(
        user_secret=TEST_SECRET,
        nonce_registry=nonce_registry,
        audit_path=audit_path,
        max_age_seconds=600.0,  # 10 minutes max age
        machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
    )

    # Load envelope with old timestamp
    old_envelope = TransitionEnvelope.from_dict(envelope_dict)
    result = gate_keeper.verify(old_envelope)

    notes = [
        f"Envelope timestamp set to {old_timestamp} (2 hours ago)",
        "Max age threshold: 600 seconds (10 minutes)",
        f"Envelope age: {time.time() - old_timestamp:.0f} seconds",
        "Should reject as expired",
        f"Got rejection reason: {result.reason}",
    ]

    return ScenarioResult(
        name="expired_envelope",
        description="Expired envelope rejection test",
        step_tested="timestamp_fresh",
        attack_vector="stale_data",
        verification_result=result,
        passed=result.rejected and result.reason == RejectionReason.ENVELOPE_EXPIRED,
        expected_rejection=True,
        notes=notes,
        metadata={
            "envelope_age_seconds": time.time() - old_timestamp,
            "max_age_seconds": 600.0,
        },
    )


# ═══════════════════════════════════════════════════════════════════════════
# STEP 6: tests_verified - Test status verification
# ═══════════════════════════════════════════════════════════════════════════


@register_scenario("failed_tests", "Test rejection when source tests failed", "tests_verified", "untested_code")
def scenario_failed_tests(tmp_path: Path) -> ScenarioResult:
    """Test that envelopes with failed tests are rejected."""
    nonce_registry = NonceRegistry(tmp_path / "nonce.json", max_age_seconds=600.0)

    # Create envelope with tests_passed=False
    envelope = seal_envelope(
        SAMPLE_PAYLOAD,
        user_secret=TEST_SECRET,
        nonce_registry=nonce_registry,
        scope=ScopeDeclaration(permissions=(PERM_DEPLOY,)),
        tests_passed=False,  # Tests failed!
        lint_passed=True,
        machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
    )

    audit_path = tmp_path / "audit.ndjson"
    gate_keeper = GateKeeper(
        user_secret=TEST_SECRET,
        nonce_registry=nonce_registry,
        audit_path=audit_path,
        require_tests=True,  # Require tests to pass
        machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
    )

    result = gate_keeper.verify(envelope)

    notes = [
        "Envelope created with tests_passed=False",
        "GateKeeper configured with require_tests=True",
        "Should reject due to test failure",
        f"Got rejection reason: {result.reason}",
    ]

    return ScenarioResult(
        name="failed_tests",
        description="Failed tests rejection",
        step_tested="tests_verified",
        attack_vector="untested_code",
        verification_result=result,
        passed=result.rejected and result.reason == RejectionReason.TESTS_NOT_PASSED,
        expected_rejection=True,
        notes=notes,
    )


@register_scenario("optional_tests", "Test that tests can be optional if configured", "tests_verified", None)
def scenario_optional_tests(tmp_path: Path) -> ScenarioResult:
    """Test that test requirement can be disabled."""
    nonce_registry = NonceRegistry(tmp_path / "nonce.json", max_age_seconds=600.0)

    # Create envelope with tests_passed=False
    envelope = seal_envelope(
        SAMPLE_PAYLOAD,
        user_secret=TEST_SECRET,
        nonce_registry=nonce_registry,
        scope=ScopeDeclaration(permissions=(PERM_DEPLOY,)),
        tests_passed=False,
        lint_passed=True,
        machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
    )

    audit_path = tmp_path / "audit.ndjson"
    gate_keeper = GateKeeper(
        user_secret=TEST_SECRET,
        nonce_registry=nonce_registry,
        audit_path=audit_path,
        require_tests=False,  # Tests not required
        machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
    )

    result = gate_keeper.verify(envelope)

    notes = [
        "Envelope created with tests_passed=False",
        "GateKeeper configured with require_tests=False",
        "Should PASS (test requirement disabled)",
    ]

    return ScenarioResult(
        name="optional_tests",
        description="Optional tests configuration test",
        step_tested="tests_verified",
        attack_vector=None,
        verification_result=result,
        passed=result.passed,
        expected_rejection=False,
        notes=notes,
    )


# ═══════════════════════════════════════════════════════════════════════════
# STEP 7: scope_present - Scope declaration validation
# ═══════════════════════════════════════════════════════════════════════════


@register_scenario(
    "missing_scope", "Test rejection when scope is missing/empty", "scope_present", "privilege_escalation"
)
def scenario_missing_scope(tmp_path: Path) -> ScenarioResult:
    """Test that missing scope declarations are rejected."""
    nonce_registry = NonceRegistry(tmp_path / "nonce.json", max_age_seconds=600.0)

    # Create envelope with empty scope
    envelope = seal_envelope(
        SAMPLE_PAYLOAD,
        user_secret=TEST_SECRET,
        nonce_registry=nonce_registry,
        scope=ScopeDeclaration(permissions=()),  # Empty permissions!
        tests_passed=True,
        lint_passed=True,
        machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
    )

    audit_path = tmp_path / "audit.ndjson"
    gate_keeper = GateKeeper(
        user_secret=TEST_SECRET,
        nonce_registry=nonce_registry,
        audit_path=audit_path,
        machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
    )

    # Try to request an action (will fail scope check)
    result = gate_keeper.verify(envelope, requested_action="deploy")

    notes = [
        "Envelope created with empty scope (no permissions)",
        "Requested action: deploy",
        "Should fail scope check",
    ]

    return ScenarioResult(
        name="missing_scope",
        description="Missing scope declaration test",
        step_tested="scope_present",
        attack_vector="privilege_escalation",
        verification_result=result,
        passed=result.rejected and result.reason == RejectionReason.ACTION_OUT_OF_SCOPE,
        expected_rejection=True,
        notes=notes,
    )


# ═══════════════════════════════════════════════════════════════════════════
# STEP 8: deploy_within_scope - Permission enforcement
# ═══════════════════════════════════════════════════════════════════════════


@register_scenario(
    "out_of_scope", "Test rejection when action exceeds permissions", "deploy_within_scope", "privilege_escalation"
)
def scenario_out_of_scope(tmp_path: Path) -> ScenarioResult:
    """Test that out-of-scope actions are rejected."""
    nonce_registry = NonceRegistry(tmp_path / "nonce.json", max_age_seconds=600.0)

    # Create envelope with limited scope
    envelope = seal_envelope(
        SAMPLE_PAYLOAD,
        user_secret=TEST_SECRET,
        nonce_registry=nonce_registry,
        scope=ScopeDeclaration(
            permissions=(PERM_READ_ONLY,),  # Only read-only!
            target_project="GRID-main",
        ),
        tests_passed=True,
        lint_passed=True,
        machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
    )

    audit_path = tmp_path / "audit.ndjson"
    gate_keeper = GateKeeper(
        user_secret=TEST_SECRET,
        nonce_registry=nonce_registry,
        audit_path=audit_path,
        machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
    )

    # Try to perform unauthorized action
    result = gate_keeper.verify(envelope, requested_action="deploy")

    notes = [
        "Envelope scope: read_only only",
        "Requested action: deploy",
        "Should reject as out of scope",
        f"Got rejection reason: {result.reason}",
    ]

    return ScenarioResult(
        name="out_of_scope",
        description="Out-of-scope action rejection",
        step_tested="deploy_within_scope",
        attack_vector="privilege_escalation",
        verification_result=result,
        passed=result.rejected and result.reason == RejectionReason.ACTION_OUT_OF_SCOPE,
        expected_rejection=True,
        notes=notes,
    )


@register_scenario("scope_enforcement", "Test that permissions are strictly enforced", "deploy_within_scope", None)
def scenario_scope_enforcement(tmp_path: Path) -> ScenarioResult:
    """Test that each permission is correctly enforced."""
    nonce_registry = NonceRegistry(tmp_path / "nonce.json", max_age_seconds=600.0)

    # Create envelope with specific permissions
    envelope = seal_envelope(
        SAMPLE_PAYLOAD,
        user_secret=TEST_SECRET,
        nonce_registry=nonce_registry,
        scope=ScopeDeclaration(
            permissions=(PERM_READ_ONLY, PERM_RUN_TESTS),  # No deploy!
            target_project="GRID-main",
        ),
        tests_passed=True,
        lint_passed=True,
        machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
    )

    audit_path = tmp_path / "audit.ndjson"
    gate_keeper = GateKeeper(
        user_secret=TEST_SECRET,
        nonce_registry=nonce_registry,
        audit_path=audit_path,
        machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
    )

    # Test read_only (should pass)
    result_read = gate_keeper.verify(envelope, requested_action="read_only")

    # Test run_tests (should pass)
    result_tests = gate_keeper.verify(
        TransitionEnvelope.from_dict(envelope.to_dict()),  # Fresh copy
        requested_action="run_tests",
    )

    notes = [
        "Scope: read_only, run_tests (no deploy)",
        f"Action 'read_only': {result_read.status}",
        f"Action 'run_tests': {result_tests.status}",
    ]

    return ScenarioResult(
        name="scope_enforcement",
        description="Permission enforcement test",
        step_tested="deploy_within_scope",
        attack_vector=None,
        verification_result=result_read,
        passed=result_read.passed and result_tests.passed,
        expected_rejection=False,
        notes=notes,
    )


# ═══════════════════════════════════════════════════════════════════════════
# STEP 9: audit_log - Audit trail verification
# ═══════════════════════════════════════════════════════════════════════════


@register_scenario("audit_trail", "Test that audit entries are written", "audit_log", None)
def scenario_audit_trail(tmp_path: Path) -> ScenarioResult:
    """Test that audit entries are properly written."""
    nonce_registry = NonceRegistry(tmp_path / "nonce.json", max_age_seconds=600.0)

    # Create envelope
    envelope = seal_envelope(
        SAMPLE_PAYLOAD,
        user_secret=TEST_SECRET,
        nonce_registry=nonce_registry,
        scope=ScopeDeclaration(permissions=(PERM_DEPLOY,)),
        tests_passed=True,
        lint_passed=True,
        machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
    )

    audit_path = tmp_path / "audit.ndjson"
    gate_keeper = GateKeeper(
        user_secret=TEST_SECRET,
        nonce_registry=nonce_registry,
        audit_path=audit_path,
        machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
    )

    # Verify (should write audit entry)
    result = gate_keeper.verify(envelope)

    # Check audit file
    audit_entries = []
    if audit_path.exists():
        with open(audit_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    audit_entries.append(json.loads(line))

    notes = [
        f"Verification result: {result.status}",
        f"Audit file exists: {audit_path.exists()}",
        f"Number of audit entries: {len(audit_entries)}",
    ]

    if audit_entries:
        last_entry = audit_entries[-1]
        notes.append(f"Last entry envelope_id: {last_entry.get('envelope_id')}")
        notes.append(f"Last entry status: {last_entry.get('status')}")

    return ScenarioResult(
        name="audit_trail",
        description="Audit trail verification",
        step_tested="audit_log",
        attack_vector=None,
        verification_result=result,
        passed=result.passed and len(audit_entries) > 0,
        expected_rejection=False,
        notes=notes,
        metadata={
            "audit_entries_count": len(audit_entries),
            "audit_file_exists": audit_path.exists(),
        },
    )


# ═══════════════════════════════════════════════════════════════════════════
# BONUS: Positive test scenarios (should all pass)
# ═══════════════════════════════════════════════════════════════════════════


@register_scenario("happy_path", "Test successful end-to-end verification", "all_steps", None)
def scenario_happy_path(tmp_path: Path) -> ScenarioResult:
    """Test that valid envelopes pass all 9 steps."""
    nonce_registry = NonceRegistry(tmp_path / "nonce.json", max_age_seconds=600.0)

    # Create valid envelope
    envelope = seal_envelope(
        SAMPLE_PAYLOAD,
        user_secret=TEST_SECRET,
        nonce_registry=nonce_registry,
        scope=ScopeDeclaration(
            permissions=(PERM_DEPLOY, PERM_READ_ONLY),
            target_project="GRID-main",
        ),
        tests_passed=True,
        lint_passed=True,
        machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
    )

    audit_path = tmp_path / "audit.ndjson"
    gate_keeper = GateKeeper(
        user_secret=TEST_SECRET,
        nonce_registry=nonce_registry,
        audit_path=audit_path,
        machine_fingerprint_overrides=MACHINE_FP_OVERRIDES,
    )

    # Verify
    result = gate_keeper.verify(envelope, requested_action="deploy")

    # Check all 9 steps passed
    step_names = [s.name for s in result.steps]

    notes = [
        f"Overall result: {result.status}",
        f"Steps completed: {len(result.steps)}",
        f"Steps: {', '.join(step_names)}",
        f"Nonce burned: {result.nonce_burned}",
    ]

    expected_steps = [
        "envelope_exists",
        "payload_integrity",
        "fingerprint_match",
        "nonce_valid",
        "timestamp_fresh",
        "tests_verified",
        "scope_present",
        "deploy_within_scope",
        "audit_log",
    ]

    all_steps_present = all(s in step_names for s in expected_steps)

    return ScenarioResult(
        name="happy_path",
        description="Successful end-to-end verification",
        step_tested="all_steps",
        attack_vector=None,
        verification_result=result,
        passed=result.passed and all_steps_present and result.nonce_burned,
        expected_rejection=False,
        notes=notes,
        metadata={
            "steps_executed": step_names,
            "expected_steps": expected_steps,
            "all_steps_present": all_steps_present,
        },
    )


# ═══════════════════════════════════════════════════════════════════════════
# Runner Functions
# ═══════════════════════════════════════════════════════════════════════════


def run_scenario(scenario_name: str, tmp_path: Path | None = None) -> ScenarioResult:
    """
    Run a specific test scenario by name.

    Args:
        scenario_name: Name of the scenario to run
        tmp_path: Optional path for temporary files (creates temp dir if None)

    Returns:
        ScenarioResult with full test details

    Raises:
        KeyError: If scenario_name is not registered
    """
    if scenario_name not in SCENARIOS:
        raise KeyError(f"Unknown scenario: {scenario_name}. Available: {list(SCENARIOS.keys())}")

    import tempfile

    if tmp_path is None:
        with tempfile.TemporaryDirectory() as td:
            return SCENARIOS[scenario_name](Path(td))

    return SCENARIOS[scenario_name](Path(tmp_path))


def run_all_scenarios(tmp_path: Path | None = None) -> dict[str, ScenarioResult]:
    """
    Run all registered test scenarios.

    Args:
        tmp_path: Optional path for temporary files

    Returns:
        Dict mapping scenario name to ScenarioResult
    """
    import tempfile

    results = {}

    if tmp_path is None:
        with tempfile.TemporaryDirectory() as td:
            for name in SCENARIOS:
                results[name] = SCENARIOS[name](Path(td))
    else:
        for name in SCENARIOS:
            results[name] = SCENARIOS[name](Path(tmp_path))

    return results


def get_scenario_info() -> list[dict[str, Any]]:
    """
    Get metadata about all registered scenarios.

    Returns:
        List of scenario metadata dictionaries
    """
    info = []
    for name, func in SCENARIOS.items():
        meta = getattr(func, "_scenario_meta", {})
        info.append(
            {
                "name": name,
                "description": meta.get("description", "No description"),
                "step": meta.get("step", "unknown"),
                "attack_vector": meta.get("attack", None),
            }
        )
    return info


def get_scenarios_by_step(step_name: str) -> list[str]:
    """
    Get all scenarios that test a specific verification step.

    Args:
        step_name: Name of the verification step

    Returns:
        List of scenario names
    """
    return [name for name, func in SCENARIOS.items() if getattr(func, "_scenario_meta", {}).get("step") == step_name]


def format_scenario_result(result: ScenarioResult, verbose: bool = True) -> str:
    """
    Format a scenario result for display.

    Args:
        result: The scenario result to format
        verbose: Include detailed notes

    Returns:
        Formatted string
    """
    lines = [
        f"{'=' * 70}",
        f"Scenario: {result.name}",
        f"Description: {result.description}",
        f"Step Tested: {result.step_tested}",
        f"Attack Vector: {result.attack_vector or 'N/A'}",
        f"Expected Rejection: {'Yes' if result.expected_rejection else 'No'}",
        f"Verification Result: {result.verification_result.status if result.verification_result else 'N/A'}",
        f"Scenario Passed: {'✅ YES' if result.passed else '❌ NO'}",
    ]

    if verbose and result.notes:
        lines.extend(["", "Notes:"])
        for note in result.notes:
            lines.append(f"  • {note}")

    if verbose and result.metadata:
        lines.extend(["", "Metadata:"])
        for key, value in result.metadata.items():
            lines.append(f"  {key}: {value}")

    lines.append(f"{'=' * 70}")

    return "\n".join(lines)


def run_comprehensive_test_suite() -> dict[str, Any]:
    """
    Run all scenarios and compile comprehensive results.

    Returns:
        Dict with summary statistics and all results
    """
    results = run_all_scenarios()

    total = len(results)
    passed = sum(1 for r in results.values() if r.passed)
    failed = total - passed

    security_tests = sum(1 for r in results.values() if r.attack_vector is not None)
    security_passed = sum(1 for r in results.values() if r.attack_vector is not None and r.passed)

    return {
        "summary": {
            "total_scenarios": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": (passed / total * 100) if total > 0 else 0,
            "security_tests": security_tests,
            "security_passed": security_passed,
        },
        "by_step": _group_by_step(results),
        "by_attack_vector": _group_by_attack_vector(results),
        "results": {name: r.to_dict() for name, r in results.items()},
    }


def _group_by_step(results: dict[str, ScenarioResult]) -> dict[str, list[str]]:
    """Group scenario results by verification step."""
    grouped = {}
    for name, result in results.items():
        step = result.step_tested
        if step not in grouped:
            grouped[step] = []
        grouped[step].append(
            {
                "name": name,
                "passed": result.passed,
                "attack_vector": result.attack_vector,
            }
        )
    return grouped


def _group_by_attack_vector(results: dict[str, ScenarioResult]) -> dict[str, list[str]]:
    """Group scenario results by attack vector."""
    grouped = {}
    for name, result in results.items():
        attack = result.attack_vector or "none"
        if attack not in grouped:
            grouped[attack] = []
        grouped[attack].append(
            {
                "name": name,
                "passed": result.passed,
                "step": result.step_tested,
            }
        )
    return grouped
