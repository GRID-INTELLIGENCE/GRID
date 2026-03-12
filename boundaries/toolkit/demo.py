Seeds\GRID-main\boundaries\toolkit\demo.py
```

```python
"""
Interactive demonstrations for the Transition Gate Toolkit.

Provides hands-on walkthroughs showing:
- How sealing creates cryptographic bindings
- How each verification step works
- Security measures in action
- Real-time demonstrations with visual feedback
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

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
    VerificationResult,
    VerificationStatus,
)
from boundaries.transition_gate.nonce import NonceRegistry


# ═══════════════════════════════════════════════════════════════════════════
# Demo Configuration
# ═══════════════════════════════════════════════════════════════════════════

DEMO_SECRET = "demo-secret-do-not-use-in-production"
DEMO_PAYLOAD = {
    "project": "GRID-demo",
    "version": "1.0.0",
    "files": ["src/demo.py", "src/utils.py"],
    "metadata": {"demo": True, "timestamp": time.time()},
}

DEMO_MACHINE_OVERRIDES = {
    "node_name": "DEMO-NODE",
    "platform_system": "DemoOS",
    "platform_machine": "x86_64",
    "username": "demo_user",
}


# ═══════════════════════════════════════════════════════════════════════════
# Visual Formatting Helpers
# ═══════════════════════════════════════════════════════════════════════════

def print_header(text: str) -> None:
    """Print a styled header."""
    print(f"\n{'=' * 70}")
    print(f"  {text}")
    print(f"{'=' * 70}\n")


def print_section(title: str) -> None:
    """Print a section divider."""
    print(f"\n{'─' * 70}")
    print(f"  {title}")
    print(f"{'─' * 70}")


def print_step(step_num: int, title: str) -> None:
    """Print a step indicator."""
    print(f"\n  Step {step_num}: {title}")


def print_success(message: str) -> None:
    """Print a success message."""
    print(f"    ✅ {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    print(f"    ⚠️  {message}")


def print_error(message: str) -> None:
    """Print an error message."""
    print(f"    ❌ {message}")


def print_info(label: str, value: Any) -> None:
    """Print labeled information."""
    if isinstance(value, str) and len(value) > 50:
        print(f"    {label:20}: {value[:47]}...")
    else:
        print(f"    {label:20}: {value}")


def print_json(data: dict[str, Any], indent: int = 4) -> None:
    """Print formatted JSON."""
    print(json.dumps(data, indent=indent, default=str))


def pause(message: str = "Press Enter to continue...") -> None:
    """Pause for user input."""
    input(f"\n    {message}")


# ═══════════════════════════════════════════════════════════════════════════
# Core Demonstrations
# ═══════════════════════════════════════════════════════════════════════════


def demo_fingerprints() -> None:
    """
    Demonstrate cryptographic fingerprinting.

    Shows how user, machine, and payload fingerprints are computed
    and why they provide cryptographic binding.
    """
    print_header("DEMO: Cryptographic Fingerprinting")

    print("This demo shows how three types of fingerprints create")
    print("cryptographic bindings that secure the transition gate.\n")

    # 1. Payload Hash
    print_step(1, "Payload Hash (SHA-256)")
    print("  The payload hash ensures data integrity.")
    print()

    payload = DEMO_PAYLOAD
    print("  Original payload:")
    print_json(payload, indent=6)

    hash1 = compute_payload_hash(payload)
    print_info("SHA-256 Hash", hash1)
    print_success("Hash computed - any change to payload changes hash")

    # Modify payload slightly
    modified_payload = payload.copy()
    modified_payload["version"] = "1.0.1"
    hash2 = compute_payload_hash(modified_payload)
    print_info("Modified hash", hash2)

    if hash1 != hash2:
        print_success("Even tiny changes produce completely different hashes!")
    pause()

    # 2. Machine Fingerprint
    print_step(2, "Machine Fingerprint (SHA-256)")
    print("  The machine fingerprint binds operations to specific hardware.")
    print()

    machine_fp = compute_machine_fingerprint(**DEMO_MACHINE_OVERRIDES)
    print_info("Machine Fingerprint", machine_fp)
    print_info("Node", DEMO_MACHINE_OVERRIDES["node_name"])
    print_info("Platform", DEMO_MACHINE_OVERRIDES["platform_system"])
    print_info("Architecture", DEMO_MACHINE_OVERRIDES["platform_machine"])
    print_info("User", DEMO_MACHINE_OVERRIDES["username"])
    print_success("Fingerprint uniquely identifies this machine configuration")
    pause()

    # 3. User Fingerprint
    print_step(3, "User Fingerprint (HMAC-SHA256)")
    print("  The user fingerprint binds the shared secret to machine identity.")
    print()

    user_fp = compute_user_fingerprint(
        DEMO_SECRET,
        machine_id=machine_fp,
    )
    print_info("User Fingerprint", user_fp)
    print_info("Secret (first 10 chars)", DEMO_SECRET[:10] + "...")
    print_info("Machine ID (first 10 chars)", machine_fp[:10] + "...")
    print_success("HMAC combines secret with machine identity")
    pause()

    # Show binding
    print_step(4, "Binding Demonstration")
    print("  The same secret on different machines produces different fingerprints.")
    print()

    different_machine = DEMO_MACHINE_OVERRIDES.copy()
    different_machine["node_name"] = "OTHER-NODE"
    different_machine_fp = compute_machine_fingerprint(**different_machine)

    user_fp_same_machine = compute_user_fingerprint(DEMO_SECRET, machine_id=machine_fp)
    user_fp_diff_machine = compute_user_fingerprint(DEMO_SECRET, machine_id=different_machine_fp)

    print_info("Same secret, original machine", user_fp_same_machine[:20] + "...")
    print_info("Same secret, different machine", user_fp_diff_machine[:20] + "...")

    if user_fp_same_machine != user_fp_diff_machine:
        print_success("Fingerprints differ - credential theft to different machine fails!")
    pause()


def demo_sealing() -> None:
    """
    Demonstrate the envelope sealing process.

    Shows how a payload is transformed into a sealed envelope
    with cryptographic proofs.
    """
    print_header("DEMO: Envelope Sealing")

    print("This demo shows how artifacts are sealed for secure transfer.")
    print("Each envelope contains cryptographic proofs that enable verification.\n")

    # Setup
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tmp_path = Path(td)
        nonce_registry = NonceRegistry(tmp_path / "nonces.json", max_age_seconds=600.0)

        print_step(1, "Create Scope Declaration")
        scope = ScopeDeclaration(
            permissions=(PERM_READ_ONLY, PERM_RUN_TESTS),
            target_project="DEMO-PROJECT",
            max_execution_time_seconds=300,
            network_allowed=False,
        )
        print("  Scope defines what the receiver may do:")
        print_json(scope.to_dict(), indent=4)
        pause()

        print_step(2, "Seal the Payload")
        print("  Calling seal_envelope() with:")
        print_info("Payload size", f"{len(json.dumps(DEMO_PAYLOAD))} bytes")
        print_info("Permissions", ", ".join(scope.permissions))
        print()

        envelope = seal_envelope(
            DEMO_PAYLOAD,
            user_secret=DEMO_SECRET,
            nonce_registry=nonce_registry,
            scope=scope,
            source_partition="E:\\",
            target_partition="C:\\Users\\USER\\cascadeprojects",
            sealed_by="demo_user",
            tests_passed=True,
            lint_passed=True,
            machine_fingerprint_overrides=DEMO_MACHINE_OVERRIDES,
            metadata={"demo_run": True},
        )

        print_success("Envelope sealed successfully!")
        print()
        print_info("Envelope ID", envelope.envelope_id)
        print_info("Timestamp", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(envelope.timestamp)))
        print_info("Nonce", envelope.nonce[:16] + "...")
        print_info("Payload Hash", envelope.payload_hash[:20] + "...")
        print_info("User Fingerprint", envelope.user_fingerprint[:20] + "...")
        print_info("Machine Fingerprint", envelope.machine_fingerprint[:20] + "...")
        pause()

        print_step(3, "Envelope Structure")
        print("  Full envelope contents:")
        print()
        envelope_dict = envelope.to_dict()
        print_json({k: v for k, v in envelope_dict.items() if k != "payload"}, indent=4)
        pause()

        print_step(4, "Serialize to JSON")
        json_file = tmp_path / "sealed_envelope.json"
        envelope.write_to_file(json_file)
        print_info("File saved", json_file)
        print_info("File size", f"{json_file.stat().st_size} bytes")
        print_success("Envelope ready for secure transfer!")
        pause()


def demo_verification_pipeline() -> None:
    """
    Demonstrate the 9-step verification pipeline.

    Shows each step of verification with pass/fail indicators.
    """
    print_header("DEMO: 9-Step Verification Pipeline")

    print("This demo walks through each verification step.")
    print("Each step has a specific security purpose.\n")

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tmp_path = Path(td)
        nonce_registry = NonceRegistry(tmp_path / "nonces.json", max_age_seconds=600.0)

        # Create a valid envelope
        envelope = seal_envelope(
            DEMO_PAYLOAD,
            user_secret=DEMO_SECRET,
            nonce_registry=nonce_registry,
            scope=ScopeDeclaration(
                permissions=(PERM_DEPLOY, PERM_READ_ONLY),
                target_project="DEMO-PROJECT",
            ),
            sealed_by="demo_user",
            tests_passed=True,
            lint_passed=True,
            machine_fingerprint_overrides=DEMO_MACHINE_OVERRIDES,
        )

        # Create GateKeeper
        audit_path = tmp_path / "audit.ndjson"
        gate_keeper = GateKeeper(
            user_secret=DEMO_SECRET,
            nonce_registry=nonce_registry,
            audit_path=audit_path,
            machine_fingerprint_overrides=DEMO_MACHINE_OVERRIDES,
        )

        print("Starting verification pipeline...\n")

        # Step descriptions
        steps = [
            ("envelope_exists", "Verify envelope exists and is parseable"),
            ("payload_integrity", "Verify SHA-256 hash matches payload"),
            ("fingerprint_match", "Verify HMAC-SHA256 signature"),
            ("nonce_valid", "Verify nonce exists and not burned"),
            ("timestamp_fresh", "Verify envelope not expired"),
            ("tests_verified", "Verify tests passed before sealing"),
            ("scope_present", "Verify scope declaration present"),
            ("deploy_within_scope", "Verify action within permissions"),
            ("audit_log", "Write result to audit trail"),
        ]

        for i, (step_name, description) in enumerate(steps, 1):
            print(f"  Step {i}: {step_name}")
            print(f"           {description}")

            if i < 9:
                print(f"           Status: {'✅ PASS (simulated)' if i <= 8 else '⏳ PENDING'}")
            print()

        print("\nRunning actual verification...")
        pause()

        result = gate_keeper.verify(envelope, requested_action="deploy")

        print("\nResults:")
        for step in result.steps:
            icon = "✅" if step.status == "passed" else "❌" if step.status == "rejected" else "⚠️"
            print(f"  {icon} Step {step.step}: {step.name} - {step.status}")
            if step.detail:
                print(f"           {step.detail}")

        print()
        if result.passed:
            print_success(f"VERIFICATION PASSED in {result.total_duration_ms:.2f}ms")
            print_info("Nonce burned", "Yes" if result.nonce_burned else "No")
        else:
            print_error(f"VERIFICATION REJECTED: {result.reason}")

        pause()


def demo_replay_attack() -> None:
    """
    Demonstrate replay attack prevention.

    Shows how nonce burning prevents reuse of intercepted envelopes.
    """
    print_header("DEMO: Replay Attack Prevention")

    print("This demo shows how the transition gate prevents replay attacks.")
    print("A replay attacker intercepts a valid envelope and tries to reuse it.\n")

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tmp_path = Path(td)
        nonce_registry = NonceRegistry(tmp_path / "nonces.json", max_age_seconds=600.0)

        print("SETUP: Alice wants to deploy code to production.")
        print("       She seals an envelope with her credentials.\n")

        # Alice seals an envelope
        envelope = seal_envelope(
            DEMO_PAYLOAD,
            user_secret=DEMO_SECRET,
            nonce_registry=nonce_registry,
            scope=ScopeDeclaration(permissions=(PERM_DEPLOY,)),
            sealed_by="alice",
            tests_passed=True,
            lint_passed=True,
            machine_fingerprint_overrides=DEMO_MACHINE_OVERRIDES,
        )

        print_info("Envelope ID", envelope.envelope_id)
        print_info("Nonce", envelope.nonce[:20] + "...")
        print_success("Envelope sealed by Alice")
        pause()

        # First verification (legitimate)
        print_section("SCENARIO 1: Legitimate First Use")
        print("Alice sends the envelope to the production server...")

        gate_keeper = GateKeeper(
            user_secret=DEMO_SECRET,
            nonce_registry=nonce_registry,
            audit_path=tmp_path / "audit.ndjson",
            machine_fingerprint_overrides=DEMO_MACHINE_OVERRIDES,
        )

        result1 = gate_keeper.verify(envelope)

        if result1.passed:
            print_success("First verification: PASSED")
            print_info("Nonce burned", "Yes" if result1.nonce_burned else "No")
        pause()

        # Second verification (replay attack)
        print_section("SCENARIO 2: Replay Attack Attempt")
        print("Eve intercepts the envelope and tries to replay it...")
        print("She doesn't know the nonce has already been burned.\n")

        result2 = gate_keeper.verify(envelope)

        print_info("Second verification status", result2.status)
        print_info("Rejection reason", result2.reason)

        if result2.rejected and result2.reason == RejectionReason.NONCE_REPLAY_OR_EXPIRED:
            print_success("Replay attack BLOCKED! Nonce already burned.")
            print("    This prevents Eve from reusing intercepted envelopes.")
        pause()

        print_section("Security Analysis")
        print("Key protections:")
        print("  1. Single-use nonces: Each envelope gets a unique nonce")
        print("  2. Burn-after-verify: Nonce marked as used after first verification")
        print("  3. Replay detection: Reused nonces are immediately rejected")
        print("  4. No window: Attacker has zero time to replay")
        pause()


def demo_privilege_escalation() -> None:
    """
    Demonstrate privilege escalation prevention.

    Shows how scope declarations prevent unauthorized actions.
    """
    print_header("DEMO: Privilege Escalation Prevention")

    print("This demo shows how scope declarations enforce least privilege.")
    print("Users can only perform actions explicitly permitted in the envelope.\n")

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tmp_path = Path(td)
        nonce_registry = NonceRegistry(tmp_path / "nonces.json", max_age_seconds=600.0)

        print("SETUP: Developer has read-only access to production.")
        print("       They try to escalate to deploy privileges.\n")

        # Create read-only envelope
        envelope = seal_envelope(
            DEMO_PAYLOAD,
            user_secret=DEMO_SECRET,
            nonce_registry=nonce_registry,
            scope=ScopeDeclaration(
                permissions=(PERM_READ_ONLY,),  # Only read!
                target_project="PROD-API",
            ),
            sealed_by="developer",
            tests_passed=True,
            lint_passed=True,
            machine_fingerprint_overrides=DEMO_MACHINE_OVERRIDES,
        )

        print_info("Scope permissions", ", ".join(envelope.scope.permissions))
        print_info("Target project", envelope.scope.target_project)
        print_warning("Developer does NOT have deploy permission")
        pause()

        # Attempt 1: Read (should succeed)
        print_section("ATTEMPT 1: Read Operation")
        print("Requesting: read_only")

        gate_keeper = GateKeeper(
            user_secret=DEMO_SECRET,
            nonce_registry=nonce_registry,
            audit_path=tmp_path / "audit.ndjson",
            machine_fingerprint_overrides=DEMO_MACHINE_OVERRIDES,
        )

        result1 = gate_keeper.verify(envelope, requested_action="read_only")

        if result1.passed:
            print_success("Read operation ALLOWED (within scope)")
        pause()

        # Attempt 2: Deploy (should fail)
        print_section("ATTEMPT 2: Privilege Escalation")
        print("Requesting: deploy")
        print("Developer tries to deploy without permission...")

        # Need fresh nonce for second verification
        envelope2 = seal_envelope(
            DEMO_PAYLOAD,
            user_secret=DEMO_SECRET,
            nonce_registry=nonce_registry,
            scope=ScopeDeclaration(
                permissions=(PERM_READ_ONLY,),
                target_project="PROD-API",
            ),
            sealed_by="developer",
            tests_passed=True,
            lint_passed=True,
            machine_fingerprint_overrides=DEMO_MACHINE_OVERRIDES,
        )

        result2 = gate_keeper.verify(envelope2, requested_action="deploy")

        print_info("Result", result2.status)
        print_info("Rejection reason", result2.reason)

        if result2.rejected:
            print_success("Privilege escalation BLOCKED!")
            print("    Scope enforcement prevented unauthorized deployment")
        pause()

        # Attempt 3: Proper admin deploy
        print_section("ATTEMPT 3: Proper Admin Deploy")
        print("Admin creates envelope with proper permissions...")

        admin_envelope = seal_envelope(
            DEMO_PAYLOAD,
            user_secret=DEMO_SECRET,
            nonce_registry=nonce_registry,
            scope=ScopeDeclaration(
                permissions=(PERM_DEPLOY, PERM_READ_ONLY),  # Has deploy!
                target_project="PROD-API",
            ),
            sealed_by="admin",
            tests_passed=True,
            lint_passed=True,
            machine_fingerprint_overrides=DEMO_MACHINE_OVERRIDES,
        )

        result3 = gate_keeper.verify(admin_envelope, requested_action="deploy")

        if result3.passed:
            print_success("Admin deploy ALLOWED (proper scope)")

        pause()


def demo_timing_attack_prevention() -> None:
    """
    Demonstrate timing-safe comparison.

    Shows how hmac.compare_digest prevents timing side-channels.
    """
    print_header("DEMO: Timing Attack Prevention")

    print("This demo explains timing-safe fingerprint comparison.")
    print("Standard string comparison leaks information via timing side-channels.\n")

    print("VULNERABLE COMPARISON:")
    print("  def bad_compare(a, b):")
    print("      if len(a) != len(b): return False  # <-- Leaks length!")
    print("      for i in range(len(a)):")
    print("          if a[i] != b[i]: return False  # <-- Leaks position!")
    print("      return True")
    print()

    print("TIMING-SAFE COMPARISON (used in Transition Gate):")
    print("  import hmac")
    print("  def safe_compare(a, b):")
    print("      return hmac.compare_digest(a, b)  # <-- Constant time!")
    print()

    print("DEMONSTRATION:")

    import time

    secret_fp = compute_user_fingerprint(
        DEMO_SECRET,
        machine_id=compute_machine_fingerprint(**DEMO_MACHINE_OVERRIDES),
    )

    # Wrong fingerprint
    wrong_secret = DEMO_SECRET + "_wrong"
    wrong_fp = compute_user_fingerprint(
        wrong_secret,
        machine_id=compute_machine_fingerprint(**DEMO_MACHINE_OVERRIDES),
    )

    # Timing test
    iterations = 1000

    # Vulnerable comparison
    start = time.perf_counter()
    for _ in range(iterations):
        _ = (secret_fp == wrong_fp)  # Standard comparison
    vuln_time = (time.perf_counter() - start) * 1000

    # Safe comparison
    start = time.perf_counter()
    for _ in range(iterations):
        _ = fingerprints_match(secret_fp, wrong_fp)  # Constant time
    safe_time = (time.perf_counter() - start) * 1000

    print_info(f"Vulnerable comparison ({iterations}x)", f"{vuln_time:.3f}ms")
    print_info(f"Timing-safe comparison ({iterations}x)", f"{safe_time:.3f}ms")
    print()
    print("Both take similar time regardless of where mismatch occurs.")
    print("This prevents attackers from learning partial fingerprint matches.")
    pause()


def run_all_demos() -> None:
    """Run all interactive demonstrations."""
    demos = [
        ("Cryptographic Fingerprinting", demo_fingerprints),
        ("Envelope Sealing", demo_sealing),
        ("Verification Pipeline", demo_verification_pipeline),
        ("Replay Attack Prevention", demo_replay_attack),
        ("Privilege Escalation Prevention", demo_privilege_escalation),
        ("Timing Attack Prevention", demo_timing_attack_prevention),
    ]

    print_header("TRANSITION GATE TOOLKIT - INTERACTIVE DEMONSTRATIONS")
    print(f"Total demonstrations: {len(demos)}")
    print()

    for i, (name, func) in enumerate(demos, 1):
        print(f"{i}. {name}")

    print("\n" + "=" * 70)

    for name, func in demos:
        try:
            func()
        except KeyboardInterrupt:
            print("\n\nDemo interrupted by user.")
            break
        except Exception as e:
            print(f"\nError in demo: {e}")

    print_header("DEMONSTRATIONS COMPLETE")
    print("Thank you for exploring the Transition Gate security features!")
    print("Run individual demos or test scenarios for more exploration.")
    print("=" * 70)


def run_demo_by_name(name: str) -> None:
    """
    Run a specific demo by name.

    Args:
        name: Name of the demo to run (e.g., "fingerprints", "sealing")

    Raises:
        ValueError: If demo name is not recognized
    """
    demos = {
        "fingerprints": demo_fingerprints,
        "sealing": demo_sealing,
        "verification": demo_verification_pipeline,
        "pipeline": demo_verification_pipeline,
        "replay": demo_replay_attack,
        "privilege": demo_privilege_escalation,
        "timing": demo_timing_attack_prevention,
    }

    if name not in demos:
        available = ", ".join(demos.keys())
        raise ValueError(f"Unknown demo: {name}. Available: {available}")

    demos[name]()


def list_demos() -> list[dict[str, str]]:
    """
    List all available demonstrations.

    Returns:
        List of demo metadata dictionaries
    """
    return [
        {"name": "fingerprints", "title": "Cryptographic Fingerprinting", "description": "How SHA-256 and HMAC-SHA256 create cryptographic bindings"},
        {"name": "sealing", "title": "Envelope Sealing", "description": "How payloads are transformed into sealed envelopes"},
        {"name": "verification", "title": "Verification Pipeline", "description": "Walk through all 9 verification steps"},
        {"name": "replay", "title": "Replay Attack Prevention", "description": "How nonce burning prevents replay attacks"},
        {"name": "privilege", "title": "Privilege Escalation Prevention", "description": "How scope declarations enforce least privilege"},
        {"name": "timing", "title": "Timing Attack Prevention", "description": "How constant-time comparison prevents side-channels"},
    ]


if __name__ == "__main__":
    run_all_demos()
