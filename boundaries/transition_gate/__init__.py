"""Transition Gate - Secure envelope verification pipeline for GRID.

This module implements the 9-step verification pipeline for sealed envelopes:
1. envelope_exists - Parse envelope and verify required fields
2. payload_integrity - SHA-256 hash verification
3. fingerprint_match - HMAC-SHA256 timing-safe comparison
4. nonce_valid - Anti-replay nonce verification
5. timestamp_fresh - Staleness check
6. tests_verified - Quality gate check
7. scope_present - Scope validation
8. deploy_within_scope - Permission enforcement
9. audit_log - Record verdict and burn nonce
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

# Afterhours log display: store UTC; surface Asia/Dhaka (+06:00) for readability
_AUDIT_TZ = ZoneInfo("Asia/Dhaka")


def _audit_timestamps() -> tuple[str, str]:
    """Return (timestamp_utc, timestamp_local) for audit entries. Persist UTC; surface +06:00."""
    now = datetime.now(UTC)
    return now.isoformat(), now.astimezone(_AUDIT_TZ).isoformat()


class VerificationError(Exception):
    """Raised when envelope verification fails."""

    def __init__(self, step: str, reason: str):
        self.step = step
        self.reason = reason
        super().__init__(f"Verification failed at step '{step}': {reason}")


@dataclass
class VerificationStep:
    """Result of a single verification step."""

    step: str
    passed: bool
    details: str = ""


@dataclass
class VerificationResult:
    """Complete result of envelope verification."""

    envelope_id: str
    passed: bool
    steps: list[VerificationStep]
    reason: str = ""
    nonce_burned: bool = False
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "envelope_id": self.envelope_id,
            "passed": self.passed,
            "steps": [{"step": s.step, "passed": s.passed, "details": s.details} for s in self.steps],
            "reason": self.reason,
            "nonce_burned": self.nonce_burned,
            "duration_ms": self.duration_ms,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class NonceRegistry:
    """Manages nonce lifecycle - issue, verify, and burn."""

    def __init__(self, registry_path: str, max_age_seconds: float = 600.0):
        self.registry_path = Path(registry_path)
        self.max_age_seconds = max_age_seconds
        self._ensure_exists()

    def _ensure_exists(self) -> None:
        """Create registry file if it doesn't exist."""
        if not self.registry_path.exists():
            self.registry_path.write_text("{}")

    def _load(self) -> dict[str, Any]:
        """Load registry from disk."""
        try:
            content = self.registry_path.read_text()
            return json.loads(content) if content else {}
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save(self, registry: dict[str, Any]) -> None:
        """Save registry to disk."""
        self.registry_path.write_text(json.dumps(registry, indent=2))

    def issue(self) -> str:
        """Issue a new nonce and add it to the registry."""
        nonce = uuid.uuid4().hex
        registry = self._load()
        registry[nonce] = {
            "issued_at": datetime.now(UTC).timestamp(),
            "burned": False,
            "burned_at": None,
        }
        self._save(registry)
        return nonce

    def is_valid(self, nonce: str) -> tuple[bool, str]:
        """Check if nonce is valid (exists, not burned, not expired)."""
        registry = self._load()

        if nonce not in registry:
            return False, "nonce_not_found"

        entry = registry[nonce]

        if entry.get("burned", False):
            return False, "nonce_already_burned"

        issued_at = entry.get("issued_at", 0)
        age = datetime.now(UTC).timestamp() - issued_at
        if age > self.max_age_seconds:
            return False, "nonce_expired"

        return True, "valid"

    def burn(self, nonce: str) -> bool:
        """Burn a nonce (mark as used)."""
        registry = self._load()

        if nonce not in registry:
            return False

        registry[nonce]["burned"] = True
        registry[nonce]["burned_at"] = datetime.now(UTC).timestamp()
        self._save(registry)
        return True


@dataclass
class TransitionEnvelope:
    """A sealed envelope for secure cross-boundary transfers."""

    envelope_id: str
    payload: dict[str, Any]
    payload_hash: str
    nonce: str
    timestamp: float
    user_fingerprint: str
    machine_fingerprint: str
    scope: dict[str, Any]
    source_partition: str
    target_partition: str
    tests_passed: bool
    lint_passed: bool

    @classmethod
    def from_file(cls, path: str) -> TransitionEnvelope:
        """Load envelope from JSON file."""
        data = json.loads(Path(path).read_text())
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TransitionEnvelope:
        """Create envelope from dictionary."""
        required = [
            "envelope_id", "payload", "payload_hash", "nonce", "timestamp",
            "user_fingerprint", "machine_fingerprint", "scope",
            "source_partition", "target_partition", "tests_passed", "lint_passed"
        ]

        for field_name in required:
            if field_name not in data:
                raise VerificationError("envelope_exists", f"Missing required field: {field_name}")

        return cls(
            envelope_id=data["envelope_id"],
            payload=data["payload"],
            payload_hash=data["payload_hash"],
            nonce=data["nonce"],
            timestamp=data["timestamp"],
            user_fingerprint=data["user_fingerprint"],
            machine_fingerprint=data["machine_fingerprint"],
            scope=data["scope"],
            source_partition=data["source_partition"],
            target_partition=data["target_partition"],
            tests_passed=data["tests_passed"],
            lint_passed=data["lint_passed"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "envelope_id": self.envelope_id,
            "payload": self.payload,
            "payload_hash": self.payload_hash,
            "nonce": self.nonce,
            "timestamp": self.timestamp,
            "user_fingerprint": self.user_fingerprint,
            "machine_fingerprint": self.machine_fingerprint,
            "scope": self.scope,
            "source_partition": self.source_partition,
            "target_partition": self.target_partition,
            "tests_passed": self.tests_passed,
            "lint_passed": self.lint_passed,
        }


class GateKeeper:
    """Verifies sealed envelopes through the 9-step pipeline."""

    def __init__(
        self,
        user_secret: str,
        nonce_registry: NonceRegistry,
        audit_path: str,
        max_age_seconds: float = 600.0,
        require_tests: bool = True,
        require_lint: bool = False,
        trusted_sources: list[str] | None = None,
        dry_run: bool = False,
    ):
        self.user_secret = user_secret
        self.nonce_registry = nonce_registry
        self.audit_path = Path(audit_path)
        self.max_age_seconds = max_age_seconds
        self.require_tests = require_tests
        self.require_lint = require_lint
        self.trusted_sources = trusted_sources or ["E:\\"]
        self.dry_run = dry_run

    def _compute_payload_hash(self, payload: dict[str, Any]) -> str:
        """Compute SHA-256 of canonical JSON payload."""
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()

    def _compute_user_fingerprint(
        self, payload_hash: str, machine_fingerprint: str, nonce: str
    ) -> str:
        """Compute HMAC-SHA256 fingerprint."""
        message = f"{payload_hash}:{machine_fingerprint}:{nonce}"
        return hmac.new(
            self.user_secret.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()

    def _compute_machine_fingerprint(self) -> str:
        """Compute machine fingerprint from system attributes."""
        attributes = [
            os.environ.get("COMPUTERNAME", "unknown"),
            os.name,
            os.environ.get("PROCESSOR_ARCHITECTURE", "unknown"),
            os.environ.get("USERNAME", "unknown"),
        ]
        machine_str = ":".join(attributes)
        return hashlib.sha256(machine_str.encode()).hexdigest()

    def _audit(self, entry: dict[str, Any]) -> None:
        """Append entry to audit log. Timestamps stored UTC; local (+06:00) for log display."""
        if self.dry_run:
            return
        ts_utc, ts_local = _audit_timestamps()
        record = {"timestamp": ts_utc, "timestamp_local_+06": ts_local, **entry}
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.audit_path, "a") as f:
            f.write(json.dumps(record) + "\n")

    def verify(self, envelope: TransitionEnvelope, requested_action: str | None = None) -> VerificationResult:
        """Run full verification pipeline on an envelope."""
        steps: list[VerificationStep] = []
        start_time = time.time()

        def add_step(name: str, passed: bool, details: str = "") -> bool:
            steps.append(VerificationStep(name, passed, details))
            return passed

        # Step 1: envelope_exists (already validated by from_dict)
        if not add_step("envelope_exists", True, f"Envelope {envelope.envelope_id} loaded"):
            pass  # Always passes if we have an envelope object

        # Verify source partition is trusted
        if envelope.source_partition not in self.trusted_sources:
            result = VerificationResult(
                envelope_id=envelope.envelope_id,
                passed=False,
                steps=steps,
                reason=f"source_partition {envelope.source_partition} not in trusted sources",
                duration_ms=(time.time() - start_time) * 1000,
            )
            self._audit({
                "timestamp": datetime.now(UTC).isoformat(),
                "envelope_id": envelope.envelope_id,
                "status": "rejected",
                "step": "envelope_exists",
                "reason": result.reason,
            })
            return result

        # Step 2: payload_integrity
        computed_hash = self._compute_payload_hash(envelope.payload)
        if not hmac.compare_digest(computed_hash.encode(), envelope.payload_hash.encode()):
            result = VerificationResult(
                envelope_id=envelope.envelope_id,
                passed=False,
                steps=steps,
                reason="payload_integrity_failed",
                duration_ms=(time.time() - start_time) * 1000,
            )
            self._audit({
                "timestamp": datetime.now(UTC).isoformat(),
                "envelope_id": envelope.envelope_id,
                "status": "rejected",
                "step": "payload_integrity",
                "reason": result.reason,
            })
            return result
        add_step("payload_integrity", True, "Hash matches")

        # Step 3: fingerprint_match
        computed_fingerprint = self._compute_user_fingerprint(
            envelope.payload_hash,
            envelope.machine_fingerprint,
            envelope.nonce,
        )
        if not hmac.compare_digest(computed_fingerprint.encode(), envelope.user_fingerprint.encode()):
            result = VerificationResult(
                envelope_id=envelope.envelope_id,
                passed=False,
                steps=steps,
                reason="fingerprint_mismatch",
                duration_ms=(time.time() - start_time) * 1000,
            )
            self._audit({
                "timestamp": datetime.now(UTC).isoformat(),
                "envelope_id": envelope.envelope_id,
                "status": "rejected",
                "step": "fingerprint_match",
                "reason": result.reason,
            })
            return result
        add_step("fingerprint_match", True, "Fingerprint valid")

        # Step 4: nonce_valid
        is_valid, nonce_reason = self.nonce_registry.is_valid(envelope.nonce)
        if not is_valid:
            result = VerificationResult(
                envelope_id=envelope.envelope_id,
                passed=False,
                steps=steps,
                reason=f"nonce_invalid: {nonce_reason}",
                duration_ms=(time.time() - start_time) * 1000,
            )
            self._audit({
                "timestamp": datetime.now(UTC).isoformat(),
                "envelope_id": envelope.envelope_id,
                "status": "rejected",
                "step": "nonce_valid",
                "reason": result.reason,
            })
            return result
        add_step("nonce_valid", True, "Nonce is valid and unburned")

        # Step 5: timestamp_fresh
        age = datetime.now(UTC).timestamp() - envelope.timestamp
        if age > self.max_age_seconds:
            result = VerificationResult(
                envelope_id=envelope.envelope_id,
                passed=False,
                steps=steps,
                reason="envelope_expired",
                duration_ms=(time.time() - start_time) * 1000,
            )
            self._audit({
                "timestamp": datetime.now(UTC).isoformat(),
                "envelope_id": envelope.envelope_id,
                "status": "rejected",
                "step": "timestamp_fresh",
                "reason": result.reason,
            })
            return result
        add_step("timestamp_fresh", True, f"Envelope age {age:.1f}s < {self.max_age_seconds}s")

        # Step 6: tests_verified
        if self.require_tests and not envelope.tests_passed:
            result = VerificationResult(
                envelope_id=envelope.envelope_id,
                passed=False,
                steps=steps,
                reason="tests_not_passed",
                duration_ms=(time.time() - start_time) * 1000,
            )
            self._audit({
                "timestamp": datetime.now(UTC).isoformat(),
                "envelope_id": envelope.envelope_id,
                "status": "rejected",
                "step": "tests_verified",
                "reason": result.reason,
            })
            return result
        add_step("tests_verified", True, f"tests_passed={envelope.tests_passed}")

        # Step 7: scope_present
        permissions = envelope.scope.get("permissions", [])
        if not permissions:
            result = VerificationResult(
                envelope_id=envelope.envelope_id,
                passed=False,
                steps=steps,
                reason="invalid_scope: no permissions declared",
                duration_ms=(time.time() - start_time) * 1000,
            )
            self._audit({
                "timestamp": datetime.now(UTC).isoformat(),
                "envelope_id": envelope.envelope_id,
                "status": "rejected",
                "step": "scope_present",
                "reason": result.reason,
            })
            return result
        add_step("scope_present", True, f"Scope has {len(permissions)} permissions")

        # Step 8: deploy_within_scope
        if requested_action:
            if requested_action not in permissions:
                result = VerificationResult(
                    envelope_id=envelope.envelope_id,
                    passed=False,
                    steps=steps,
                    reason=f"action_out_of_scope: {requested_action} not in {permissions}",
                    duration_ms=(time.time() - start_time) * 1000,
                )
                self._audit({
                    "timestamp": datetime.now(UTC).isoformat(),
                    "envelope_id": envelope.envelope_id,
                    "status": "rejected",
                    "step": "deploy_within_scope",
                    "reason": result.reason,
                })
                return result
            add_step("deploy_within_scope", True, f"Action {requested_action} permitted")
        else:
            add_step("deploy_within_scope", True, "No action requested, scope only validated")

        # All checks passed - burn nonce and audit
        nonce_burned = False
        if not self.dry_run:
            nonce_burned = self.nonce_registry.burn(envelope.nonce)

        duration_ms = (time.time() - start_time) * 1000
        add_step("audit_log", True, f"Nonce burned={nonce_burned}")

        result = VerificationResult(
            envelope_id=envelope.envelope_id,
            passed=True,
            steps=steps,
            reason="all_checks_passed",
            nonce_burned=nonce_burned,
            duration_ms=duration_ms,
        )

        self._audit({
            "timestamp": datetime.now(UTC).isoformat(),
            "envelope_id": envelope.envelope_id,
            "status": "passed",
            "step": "audit_log",
            "reason": result.reason,
            "nonce_burned": nonce_burned,
            "duration_ms": duration_ms,
        })

        return result

    def verify_from_file(self, path: str, requested_action: str | None = None) -> VerificationResult:
        """Load envelope from file and verify."""
        envelope = TransitionEnvelope.from_file(path)
        return self.verify(envelope, requested_action)
