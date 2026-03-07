"""
GateKeeper: 9-step verification pipeline for sealed transition envelopes.

The GateKeeper is the receiving side's enforcement point. It validates every
aspect of a sealed envelope before allowing any actions on the payload.

Verification pipeline (9 steps):
1. envelope_exists    — Envelope is present and parseable
2. payload_integrity  — SHA-256 of payload matches envelope's payload_hash
3. fingerprint_match  — User fingerprint matches recomputed HMAC-SHA256
4. nonce_valid        — Nonce exists in registry, not burned, not expired
5. timestamp_fresh    — Envelope age < max_age_seconds
6. tests_verified     — Source reports tests_passed == True
7. scope_present      — Scope declaration is non-empty and well-formed
8. deploy_within_scope — Requested action is within declared permissions
9. audit_log          — All results appended to audit trail

Security posture:
- Fail-closed: any step failure rejects the entire envelope
- Timing-safe HMAC comparison (via hmac.compare_digest)
- Nonce burned on successful verification (replay prevention)
- Append-only NDJSON audit trail for forensic review
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from boundaries.transition_gate.envelope import (  # type: ignore[import-untyped]
    TransitionEnvelope,
)
from boundaries.transition_gate.fingerprint import (  # type: ignore[import-untyped]
    compute_payload_hash,
    compute_user_fingerprint,
    fingerprints_match,
)
from boundaries.transition_gate.nonce import NonceRegistry  # type: ignore[import-untyped]


class VerificationStatus(StrEnum):
    """Outcome of a verification step or overall result."""

    PASSED = "passed"
    REJECTED = "rejected"
    ERROR = "error"


class RejectionReason(StrEnum):
    """Machine-readable rejection reasons."""

    ENVELOPE_MISSING = "rejected:envelope_missing"
    ENVELOPE_PARSE_ERROR = "rejected:envelope_parse_error"
    PAYLOAD_INTEGRITY_FAILED = "rejected:payload_integrity_failed"
    FINGERPRINT_MISMATCH = "rejected:fingerprint_mismatch"
    NONCE_REPLAY_OR_EXPIRED = "rejected:nonce_replay_or_expired"
    ENVELOPE_EXPIRED = "rejected:envelope_expired"
    TESTS_NOT_PASSED = "rejected:tests_not_passed"
    SCOPE_MISSING = "rejected:scope_missing"
    ACTION_OUT_OF_SCOPE = "rejected:action_out_of_scope"
    INTERNAL_ERROR = "rejected:internal_error"


@dataclass
class StepResult:
    """Result of a single verification pipeline step."""

    step: int
    name: str
    status: str
    detail: str | None = None
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VerificationResult:
    """
    Complete result of the 9-step verification pipeline.

    Contains per-step results and the overall verdict.
    """

    envelope_id: str | None
    status: str
    reason: str | None = None
    steps: list[StepResult] = field(default_factory=list)
    timestamp: str = ""
    total_duration_ms: float = 0.0
    nonce_burned: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(UTC).isoformat()

    @property
    def passed(self) -> bool:
        return self.status == VerificationStatus.PASSED

    @property
    def rejected(self) -> bool:
        return self.status == VerificationStatus.REJECTED

    def to_dict(self) -> dict[str, Any]:
        return {
            "envelope_id": self.envelope_id,
            "status": self.status,
            "reason": self.reason,
            "steps": [s.to_dict() for s in self.steps],
            "timestamp": self.timestamp,
            "total_duration_ms": self.total_duration_ms,
            "nonce_burned": self.nonce_burned,
            "metadata": self.metadata,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)


class GateKeeper:
    """
    Verification engine for sealed transition envelopes.

    Implements the full 9-step verification pipeline with fail-closed
    semantics, nonce burning, and append-only audit logging.

    Args:
        user_secret: The shared secret for recomputing user fingerprints.
        nonce_registry: NonceRegistry instance for nonce validation/burning.
        audit_path: Path to the NDJSON audit log file. If None, audit
                    logging is disabled.
        max_age_seconds: Maximum envelope age before rejection. Defaults
                         to 600 (10 minutes).
        require_tests: Whether to require tests_passed == True. Default True.
        require_lint: Whether to require lint_passed == True. Default False.
        machine_fingerprint_overrides: Optional overrides for recomputing
            machine fingerprint (for cross-machine verification).
        extra_fingerprint_context: Optional extra context for user fingerprint
            recomputation.
    """

    def __init__(
        self,
        *,
        user_secret: str,
        nonce_registry: NonceRegistry,
        audit_path: Path | str | None = None,
        max_age_seconds: float = 600.0,
        require_tests: bool = True,
        require_lint: bool = False,
        machine_fingerprint_overrides: dict[str, str] | None = None,
        extra_fingerprint_context: str | None = None,
    ):
        if not user_secret:
            raise ValueError("user_secret must not be empty")

        self._user_secret = user_secret
        self._nonce_registry = nonce_registry
        self._audit_path = Path(audit_path) if audit_path else None
        self._max_age_seconds = max_age_seconds
        self._require_tests = require_tests
        self._require_lint = require_lint
        self._machine_fp_overrides = machine_fingerprint_overrides or {}
        self._extra_fp_context = extra_fingerprint_context

        if self._audit_path:
            self._audit_path.parent.mkdir(parents=True, exist_ok=True)

        # Counters for monitoring / KPIs
        self._total_verifications: int = 0
        self._total_passed: int = 0
        self._total_rejected: int = 0
        self._rejection_counts: dict[str, int] = {}

    @property
    def stats(self) -> dict[str, Any]:
        """Return current verification statistics."""
        return {
            "total_verifications": self._total_verifications,
            "total_passed": self._total_passed,
            "total_rejected": self._total_rejected,
            "pass_rate": (self._total_passed / self._total_verifications if self._total_verifications > 0 else 0.0),
            "rejection_counts": dict(self._rejection_counts),
        }

    def verify(
        self,
        envelope: TransitionEnvelope,
        *,
        requested_action: str | None = None,
        dry_run: bool = False,
    ) -> VerificationResult:
        """
        Run the full 9-step verification pipeline on a sealed envelope.

        If dry_run is True, the nonce is validated but not burned, and no
        audit entry is written. Use dry_run for pre-flight checks.

        Args:
            envelope: The sealed TransitionEnvelope to verify.
            requested_action: The action the receiver wants to perform.
                              Must be within the envelope's scope permissions.
                              If None, defaults to "read_only".
            dry_run: If True, don't burn nonce or write audit log.

        Returns:
            VerificationResult with per-step details and overall verdict.
        """
        pipeline_start = time.monotonic()
        steps: list[StepResult] = []
        action = requested_action or "read_only"

        result = VerificationResult(
            envelope_id=envelope.envelope_id,
            status=VerificationStatus.PASSED,
        )

        # ── Step 1: envelope_exists ──
        step_result = self._step_envelope_exists(envelope)
        steps.append(step_result)
        if step_result.status != VerificationStatus.PASSED:
            return self._finalize(
                result,
                steps,
                pipeline_start,
                status=VerificationStatus.REJECTED,
                reason=RejectionReason.ENVELOPE_PARSE_ERROR,
                dry_run=dry_run,
            )

        # ── Step 2: payload_integrity ──
        step_result = self._step_payload_integrity(envelope)
        steps.append(step_result)
        if step_result.status != VerificationStatus.PASSED:
            return self._finalize(
                result,
                steps,
                pipeline_start,
                status=VerificationStatus.REJECTED,
                reason=RejectionReason.PAYLOAD_INTEGRITY_FAILED,
                dry_run=dry_run,
            )

        # ── Step 3: fingerprint_match ──
        step_result = self._step_fingerprint_match(envelope)
        steps.append(step_result)
        if step_result.status != VerificationStatus.PASSED:
            return self._finalize(
                result,
                steps,
                pipeline_start,
                status=VerificationStatus.REJECTED,
                reason=RejectionReason.FINGERPRINT_MISMATCH,
                dry_run=dry_run,
            )

        # ── Step 4: nonce_valid ──
        step_result = self._step_nonce_valid(envelope, dry_run=dry_run)
        steps.append(step_result)
        if step_result.status != VerificationStatus.PASSED:
            return self._finalize(
                result,
                steps,
                pipeline_start,
                status=VerificationStatus.REJECTED,
                reason=RejectionReason.NONCE_REPLAY_OR_EXPIRED,
                dry_run=dry_run,
            )

        # ── Step 5: timestamp_fresh ──
        step_result = self._step_timestamp_fresh(envelope)
        steps.append(step_result)
        if step_result.status != VerificationStatus.PASSED:
            return self._finalize(
                result,
                steps,
                pipeline_start,
                status=VerificationStatus.REJECTED,
                reason=RejectionReason.ENVELOPE_EXPIRED,
                dry_run=dry_run,
            )

        # ── Step 6: tests_verified ──
        step_result = self._step_tests_verified(envelope)
        steps.append(step_result)
        if step_result.status != VerificationStatus.PASSED:
            return self._finalize(
                result,
                steps,
                pipeline_start,
                status=VerificationStatus.REJECTED,
                reason=RejectionReason.TESTS_NOT_PASSED,
                dry_run=dry_run,
            )

        # ── Step 7: scope_present ──
        step_result = self._step_scope_present(envelope)
        steps.append(step_result)
        if step_result.status != VerificationStatus.PASSED:
            return self._finalize(
                result,
                steps,
                pipeline_start,
                status=VerificationStatus.REJECTED,
                reason=RejectionReason.SCOPE_MISSING,
                dry_run=dry_run,
            )

        # ── Step 8: deploy_within_scope ──
        step_result = self._step_deploy_within_scope(envelope, action)
        steps.append(step_result)
        if step_result.status != VerificationStatus.PASSED:
            return self._finalize(
                result,
                steps,
                pipeline_start,
                status=VerificationStatus.REJECTED,
                reason=RejectionReason.ACTION_OUT_OF_SCOPE,
                dry_run=dry_run,
            )

        # ── Step 9: audit_log ──
        # On full pass, burn the nonce (unless dry_run)
        nonce_burned = False
        if not dry_run:
            burn_ok, burn_reason = self._nonce_registry.burn(envelope.nonce)
            nonce_burned = burn_ok

        step_result = self._step_audit_log(envelope, passed=True, dry_run=dry_run)
        steps.append(step_result)

        result.nonce_burned = nonce_burned
        return self._finalize(
            result,
            steps,
            pipeline_start,
            status=VerificationStatus.PASSED,
            reason=None,
            dry_run=dry_run,
        )

    def verify_from_file(
        self,
        path: Path | str,
        *,
        requested_action: str | None = None,
        dry_run: bool = False,
    ) -> VerificationResult:
        """
        Load an envelope from a JSON file and run verification.

        Args:
            path: Path to the sealed envelope JSON file.
            requested_action: The action the receiver wants to perform.
            dry_run: If True, don't burn nonce or write audit log.

        Returns:
            VerificationResult.
        """
        file_path = Path(path)
        if not file_path.exists():
            result = VerificationResult(
                envelope_id=None,
                status=VerificationStatus.REJECTED,
                reason=RejectionReason.ENVELOPE_MISSING,
                steps=[
                    StepResult(
                        step=1,
                        name="envelope_exists",
                        status=VerificationStatus.REJECTED,
                        detail=f"File not found: {file_path}",
                    )
                ],
            )
            self._update_stats(result)
            self._audit_log_entry(result)
            return result

        try:
            envelope = TransitionEnvelope.from_file(file_path)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            result = VerificationResult(
                envelope_id=None,
                status=VerificationStatus.REJECTED,
                reason=RejectionReason.ENVELOPE_PARSE_ERROR,
                steps=[
                    StepResult(
                        step=1,
                        name="envelope_exists",
                        status=VerificationStatus.REJECTED,
                        detail=f"Parse error: {exc}",
                    )
                ],
            )
            self._update_stats(result)
            self._audit_log_entry(result)
            return result

        return self.verify(
            envelope,
            requested_action=requested_action,
            dry_run=dry_run,
        )

    # ── Pipeline step implementations ──

    def _step_envelope_exists(self, envelope: TransitionEnvelope) -> StepResult:
        """Step 1: Verify envelope is present and has required fields."""
        start = time.monotonic()
        required_fields = [
            "envelope_id",
            "payload",
            "payload_hash",
            "nonce",
            "timestamp",
            "user_fingerprint",
            "machine_fingerprint",
        ]
        missing = [f for f in required_fields if not getattr(envelope, f, None)]
        duration = (time.monotonic() - start) * 1000

        if missing:
            return StepResult(
                step=1,
                name="envelope_exists",
                status=VerificationStatus.REJECTED,
                detail=f"Missing required fields: {missing}",
                duration_ms=duration,
            )
        return StepResult(
            step=1,
            name="envelope_exists",
            status=VerificationStatus.PASSED,
            detail="All required fields present",
            duration_ms=duration,
        )

    def _step_payload_integrity(self, envelope: TransitionEnvelope) -> StepResult:
        """Step 2: Verify payload hash matches recomputed SHA-256."""
        start = time.monotonic()
        try:
            recomputed = compute_payload_hash(envelope.payload)
        except (TypeError, ValueError) as exc:
            duration = (time.monotonic() - start) * 1000
            return StepResult(
                step=2,
                name="payload_integrity",
                status=VerificationStatus.REJECTED,
                detail=f"Cannot hash payload: {exc}",
                duration_ms=duration,
            )

        duration = (time.monotonic() - start) * 1000
        if not fingerprints_match(recomputed, envelope.payload_hash):
            return StepResult(
                step=2,
                name="payload_integrity",
                status=VerificationStatus.REJECTED,
                detail="Payload hash mismatch (data may have been tampered with)",
                duration_ms=duration,
            )
        return StepResult(
            step=2,
            name="payload_integrity",
            status=VerificationStatus.PASSED,
            detail="Payload hash verified",
            duration_ms=duration,
        )

    def _step_fingerprint_match(self, envelope: TransitionEnvelope) -> StepResult:
        """Step 3: Verify user fingerprint matches recomputed HMAC-SHA256."""
        start = time.monotonic()

        # Recompute user fingerprint using the shared secret and the
        # machine fingerprint FROM THE ENVELOPE (since we're verifying
        # that the sealer's identity matches, not our own machine).
        recomputed = compute_user_fingerprint(
            self._user_secret,
            machine_id=envelope.machine_fingerprint,
            extra_context=self._extra_fp_context,
        )

        duration = (time.monotonic() - start) * 1000
        if not fingerprints_match(recomputed, envelope.user_fingerprint):
            return StepResult(
                step=3,
                name="fingerprint_match",
                status=VerificationStatus.REJECTED,
                detail="User fingerprint mismatch (secret or machine identity differs)",
                duration_ms=duration,
            )
        return StepResult(
            step=3,
            name="fingerprint_match",
            status=VerificationStatus.PASSED,
            detail="User fingerprint verified (timing-safe)",
            duration_ms=duration,
        )

    def _step_nonce_valid(self, envelope: TransitionEnvelope, *, dry_run: bool = False) -> StepResult:
        """Step 4: Verify nonce is valid (exists, not burned, not expired)."""
        start = time.monotonic()

        valid, reason = self._nonce_registry.validate(envelope.nonce)
        duration = (time.monotonic() - start) * 1000

        if not valid:
            return StepResult(
                step=4,
                name="nonce_valid",
                status=VerificationStatus.REJECTED,
                detail=f"Nonce rejected: {reason}",
                duration_ms=duration,
            )
        return StepResult(
            step=4,
            name="nonce_valid",
            status=VerificationStatus.PASSED,
            detail="Nonce valid and unburned" + (" (dry-run, not burning)" if dry_run else ""),
            duration_ms=duration,
        )

    def _step_timestamp_fresh(self, envelope: TransitionEnvelope) -> StepResult:
        """Step 5: Verify envelope timestamp is within max_age_seconds."""
        start = time.monotonic()
        age = envelope.age_seconds
        duration = (time.monotonic() - start) * 1000

        if age > self._max_age_seconds:
            return StepResult(
                step=5,
                name="timestamp_fresh",
                status=VerificationStatus.REJECTED,
                detail=f"Envelope age {age:.1f}s exceeds max {self._max_age_seconds:.1f}s",
                duration_ms=duration,
            )
        return StepResult(
            step=5,
            name="timestamp_fresh",
            status=VerificationStatus.PASSED,
            detail=f"Envelope age {age:.1f}s within limit {self._max_age_seconds:.1f}s",
            duration_ms=duration,
        )

    def _step_tests_verified(self, envelope: TransitionEnvelope) -> StepResult:
        """Step 6: Verify that source reports tests (and optionally lint) passed."""
        start = time.monotonic()
        issues: list[str] = []

        if self._require_tests and not envelope.tests_passed:
            issues.append("tests_passed=False")
        if self._require_lint and not envelope.lint_passed:
            issues.append("lint_passed=False")

        duration = (time.monotonic() - start) * 1000
        if issues:
            return StepResult(
                step=6,
                name="tests_verified",
                status=VerificationStatus.REJECTED,
                detail=f"Quality gate failed: {', '.join(issues)}",
                duration_ms=duration,
            )
        return StepResult(
            step=6,
            name="tests_verified",
            status=VerificationStatus.PASSED,
            detail="Quality gates satisfied",
            duration_ms=duration,
        )

    def _step_scope_present(self, envelope: TransitionEnvelope) -> StepResult:
        """Step 7: Verify scope declaration exists and has permissions."""
        start = time.monotonic()
        duration_fn = lambda: (time.monotonic() - start) * 1000  # noqa: E731

        if envelope.scope is None:
            return StepResult(
                step=7,
                name="scope_present",
                status=VerificationStatus.REJECTED,
                detail="No scope declaration in envelope",
                duration_ms=duration_fn(),
            )

        if not envelope.scope.permissions:
            return StepResult(
                step=7,
                name="scope_present",
                status=VerificationStatus.REJECTED,
                detail="Scope has empty permissions list",
                duration_ms=duration_fn(),
            )

        return StepResult(
            step=7,
            name="scope_present",
            status=VerificationStatus.PASSED,
            detail=f"Scope present with permissions: {list(envelope.scope.permissions)}",
            duration_ms=duration_fn(),
        )

    def _step_deploy_within_scope(self, envelope: TransitionEnvelope, action: str) -> StepResult:
        """Step 8: Verify the requested action is within the envelope's scope."""
        start = time.monotonic()

        allowed_permissions = set(envelope.scope.permissions)
        duration = (time.monotonic() - start) * 1000

        if action not in allowed_permissions:
            return StepResult(
                step=8,
                name="deploy_within_scope",
                status=VerificationStatus.REJECTED,
                detail=f"Action '{action}' not in permitted scope {sorted(allowed_permissions)}",
                duration_ms=duration,
            )
        return StepResult(
            step=8,
            name="deploy_within_scope",
            status=VerificationStatus.PASSED,
            detail=f"Action '{action}' is within scope",
            duration_ms=duration,
        )

    def _step_audit_log(
        self,
        envelope: TransitionEnvelope,
        *,
        passed: bool,
        dry_run: bool = False,
    ) -> StepResult:
        """Step 9: Write audit log entry (unless dry_run)."""
        start = time.monotonic()

        if dry_run:
            duration = (time.monotonic() - start) * 1000
            return StepResult(
                step=9,
                name="audit_log",
                status=VerificationStatus.PASSED,
                detail="Dry-run: audit log skipped",
                duration_ms=duration,
            )

        # Audit entry is written in _finalize via _audit_log_entry
        duration = (time.monotonic() - start) * 1000
        return StepResult(
            step=9,
            name="audit_log",
            status=VerificationStatus.PASSED,
            detail="Audit log entry queued",
            duration_ms=duration,
        )

    # ── Internal helpers ──

    def _finalize(
        self,
        result: VerificationResult,
        steps: list[StepResult],
        pipeline_start: float,
        *,
        status: str,
        reason: str | None,
        dry_run: bool,
    ) -> VerificationResult:
        """Finalize the verification result with timing and audit."""
        result.steps = steps
        result.status = status
        result.reason = reason
        result.total_duration_ms = (time.monotonic() - pipeline_start) * 1000

        self._update_stats(result)

        if not dry_run:
            self._audit_log_entry(result)

        return result

    def _update_stats(self, result: VerificationResult) -> None:
        """Update internal counters."""
        self._total_verifications += 1
        if result.passed:
            self._total_passed += 1
        else:
            self._total_rejected += 1
            if result.reason:
                self._rejection_counts[result.reason] = self._rejection_counts.get(result.reason, 0) + 1

    def _audit_log_entry(self, result: VerificationResult) -> None:
        """Append a verification result to the NDJSON audit trail."""
        if self._audit_path is None:
            return

        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event_type": "gate_verification",
            "envelope_id": result.envelope_id,
            "status": result.status,
            "reason": result.reason,
            "nonce_burned": result.nonce_burned,
            "total_duration_ms": result.total_duration_ms,
            "step_count": len(result.steps),
            "failed_step": next(
                (s.name for s in result.steps if s.status != VerificationStatus.PASSED),
                None,
            ),
        }

        try:
            with open(self._audit_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, default=str) + "\n")
        except OSError:
            # Audit write is best-effort; don't crash verification
            pass


def verify_envelope(
    envelope: TransitionEnvelope,
    *,
    user_secret: str,
    nonce_registry: NonceRegistry,
    audit_path: Path | str | None = None,
    max_age_seconds: float = 600.0,
    requested_action: str | None = None,
    require_tests: bool = True,
    require_lint: bool = False,
    dry_run: bool = False,
    machine_fingerprint_overrides: dict[str, str] | None = None,
    extra_fingerprint_context: str | None = None,
) -> VerificationResult:
    """
    Convenience function: create a GateKeeper and verify an envelope in one call.

    This is the primary entry point for the verify side of the pipeline.

    Args:
        envelope: The sealed TransitionEnvelope to verify.
        user_secret: Shared secret for fingerprint recomputation.
        nonce_registry: NonceRegistry for nonce validation/burning.
        audit_path: Path to the NDJSON audit log file.
        max_age_seconds: Maximum envelope age before rejection.
        requested_action: The action the receiver wants to perform.
        require_tests: Whether to require tests_passed == True.
        require_lint: Whether to require lint_passed == True.
        dry_run: If True, don't burn nonce or write audit log.
        machine_fingerprint_overrides: Optional overrides for machine
            fingerprint computation.
        extra_fingerprint_context: Optional extra context for user fingerprint.

    Returns:
        VerificationResult with per-step details and overall verdict.
    """
    keeper = GateKeeper(
        user_secret=user_secret,
        nonce_registry=nonce_registry,
        audit_path=audit_path,
        max_age_seconds=max_age_seconds,
        require_tests=require_tests,
        require_lint=require_lint,
        machine_fingerprint_overrides=machine_fingerprint_overrides,
        extra_fingerprint_context=extra_fingerprint_context,
    )
    return keeper.verify(
        envelope,
        requested_action=requested_action,
        dry_run=dry_run,
    )
