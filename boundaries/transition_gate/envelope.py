"""
Transition Envelope: sealed artifact container for cross-partition transfers.

The envelope is the sole trusted artifact crossing the E:\\ → C:\\ boundary.
It contains the payload, cryptographic integrity proofs, a single-use nonce,
timestamp, scope declaration, and fingerprints.

Security invariants:
- Payload hash is computed at seal time and immutable
- User fingerprint binds the envelope to the sealing identity
- Machine fingerprint binds the envelope to the sealing host
- Nonce ensures single-use (burn-after-verify)
- Timestamp enables freshness checks (max_age enforcement)
- Scope declaration limits what the receiving side may do with the payload
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from boundaries.transition_gate.fingerprint import (  # type: ignore[import-untyped]
    compute_machine_fingerprint,
    compute_payload_hash,
    compute_user_fingerprint,
)
from boundaries.transition_gate.nonce import NonceRegistry  # type: ignore[import-untyped]


@dataclass(frozen=True)
class ScopeDeclaration:
    """
    Declares what the receiving side is permitted to do with this envelope.

    Permissions follow least-privilege: only the listed actions are allowed.
    """

    permissions: tuple[str, ...] = ("read_only",)
    target_project: str | None = None
    target_path: str | None = None
    max_execution_time_seconds: int = 300
    network_allowed: bool = False
    notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "permissions": list(self.permissions),
            "target_project": self.target_project,
            "target_path": self.target_path,
            "max_execution_time_seconds": self.max_execution_time_seconds,
            "network_allowed": self.network_allowed,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ScopeDeclaration:
        return cls(
            permissions=tuple(d.get("permissions", ("read_only",))),
            target_project=d.get("target_project"),
            target_path=d.get("target_path"),
            max_execution_time_seconds=int(d.get("max_execution_time_seconds", 300)),
            network_allowed=d.get("network_allowed", False),
            notes=d.get("notes"),
        )


# Well-known permission constants for scope declarations
PERM_DEPLOY = "deploy"
PERM_RUN_TESTS = "run_tests"
PERM_START_SERVER = "start_server"
PERM_READ_ONLY = "read_only"
PERM_WRITE_RESULTS = "write_results"
PERM_NETWORK = "network"

ALL_KNOWN_PERMISSIONS = frozenset(
    {
        PERM_DEPLOY,
        PERM_RUN_TESTS,
        PERM_START_SERVER,
        PERM_READ_ONLY,
        PERM_WRITE_RESULTS,
        PERM_NETWORK,
    }
)


@dataclass
class TransitionEnvelope:
    """
    Sealed envelope for cross-partition artifact transfer.

    This is the ONLY trusted object that crosses the E:\\ → C:\\ boundary.
    It is created by seal_envelope() and verified by GateKeeper.verify().

    Fields:
        envelope_id: Unique identifier for this envelope (UUID4).
        payload: The artifact data being transferred (JSON-serializable).
        payload_hash: SHA-256 of the canonical JSON serialization of payload.
        nonce: Single-use nonce from the NonceRegistry.
        timestamp: Unix timestamp of seal time.
        user_fingerprint: HMAC-SHA256 binding identity to machine.
        machine_fingerprint: SHA-256 of stable machine attributes.
        scope: Scope declaration limiting receiver actions.
        source_partition: Label of the source partition (e.g. ``E:\\``).
        target_partition: Label of the target partition (e.g. ``C:\\``).
        sealed_by: Optional human-readable identifier of the sealer.
        tests_passed: Whether the source project's tests passed before sealing.
        lint_passed: Whether the source project's linting passed before sealing.
        metadata: Optional additional metadata.
    """

    envelope_id: str
    payload: Any
    payload_hash: str
    nonce: str
    timestamp: float
    user_fingerprint: str
    machine_fingerprint: str
    scope: ScopeDeclaration
    source_partition: str = "E:\\"
    target_partition: str = "C:\\Users\\USER\\cascadeprojects"
    sealed_by: str | None = None
    tests_passed: bool = False
    lint_passed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the envelope to a dictionary."""
        d = asdict(self)
        d["scope"] = self.scope.to_dict()
        return d

    def to_json(self, indent: int = 2) -> str:
        """Serialize the envelope to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> TransitionEnvelope:
        """Deserialize an envelope from a dictionary."""
        scope_data = d.get("scope", {})
        scope = ScopeDeclaration.from_dict(scope_data) if isinstance(scope_data, dict) else ScopeDeclaration()

        return cls(
            envelope_id=d["envelope_id"],
            payload=d["payload"],
            payload_hash=d["payload_hash"],
            nonce=d["nonce"],
            timestamp=float(d["timestamp"]),
            user_fingerprint=d["user_fingerprint"],
            machine_fingerprint=d["machine_fingerprint"],
            scope=scope,
            source_partition=d.get("source_partition", "E:\\"),
            target_partition=d.get("target_partition", "C:\\Users\\USER\\cascadeprojects"),
            sealed_by=d.get("sealed_by"),
            tests_passed=d.get("tests_passed", False),
            lint_passed=d.get("lint_passed", False),
            metadata=d.get("metadata", {}),
        )

    @classmethod
    def from_json(cls, json_str: str) -> TransitionEnvelope:
        """Deserialize an envelope from a JSON string."""
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def from_file(cls, path: Path | str) -> TransitionEnvelope:
        """Load an envelope from a JSON file."""
        with open(path, encoding="utf-8") as f:
            return cls.from_dict(json.load(f))

    def write_to_file(self, path: Path | str) -> Path:
        """
        Write the sealed envelope to a JSON file.

        Uses atomic write (temp + rename) to prevent partial writes.

        Args:
            path: Destination file path.

        Returns:
            The resolved Path where the envelope was written.
        """
        dest = Path(path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        tmp_path = dest.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
        tmp_path.replace(dest)
        return dest.resolve()

    @property
    def age_seconds(self) -> float:
        """How many seconds ago this envelope was sealed."""
        return time.time() - self.timestamp

    @property
    def is_quality_gated(self) -> bool:
        """Whether this envelope passed both test and lint gates."""
        return self.tests_passed and self.lint_passed


def seal_envelope(
    payload: Any,
    *,
    user_secret: str,
    nonce_registry: NonceRegistry,
    scope: ScopeDeclaration | None = None,
    source_partition: str = "E:\\",
    target_partition: str = "C:\\Users\\USER\\cascadeprojects",
    sealed_by: str | None = None,
    tests_passed: bool = False,
    lint_passed: bool = False,
    metadata: dict[str, Any] | None = None,
    machine_fingerprint_overrides: dict[str, str] | None = None,
    extra_fingerprint_context: str | None = None,
) -> TransitionEnvelope:
    """
    Seal a payload into a TransitionEnvelope with full cryptographic binding.

    This is the primary entry point for the seal side of the pipeline.
    It computes all hashes, generates a nonce, and returns a sealed envelope
    ready for transfer.

    Pipeline steps performed:
    1. Generate envelope ID (UUID4)
    2. Compute payload hash (SHA-256 of canonical JSON)
    3. Compute machine fingerprint (SHA-256 of OS attributes)
    4. Compute user fingerprint (HMAC-SHA256 of secret + machine identity)
    5. Generate and register a single-use nonce
    6. Capture current timestamp
    7. Assemble the sealed envelope

    Args:
        payload: JSON-serializable artifact data to transfer.
        user_secret: Shared secret for HMAC fingerprint.
        nonce_registry: NonceRegistry instance for nonce generation.
        scope: Scope declaration for the receiver. Defaults to read_only.
        source_partition: Source partition label.
        target_partition: Target partition label.
        sealed_by: Human-readable sealer identifier.
        tests_passed: Whether source project tests passed before sealing.
        lint_passed: Whether source project linting passed before sealing.
        metadata: Additional metadata to include.
        machine_fingerprint_overrides: Optional overrides for machine
            fingerprint computation (for testing).
        extra_fingerprint_context: Optional extra context for user fingerprint.

    Returns:
        A sealed TransitionEnvelope ready for writing to disk and transfer.

    Raises:
        ValueError: If user_secret is empty.
        TypeError: If payload is not JSON-serializable.
    """
    if not user_secret:
        raise ValueError("user_secret must not be empty for sealing")

    envelope_id = str(uuid.uuid4())

    # Step 1: Payload integrity
    payload_hash = compute_payload_hash(payload)

    # Step 2: Machine fingerprint
    fp_kwargs = machine_fingerprint_overrides or {}
    machine_fp = compute_machine_fingerprint(**fp_kwargs)

    # Step 3: User fingerprint (binds secret to machine)
    user_fp = compute_user_fingerprint(
        user_secret,
        machine_id=machine_fp,
        extra_context=extra_fingerprint_context,
    )

    # Step 4: Nonce (single-use, registered)
    nonce = nonce_registry.generate(
        envelope_id=envelope_id,
        source=source_partition,
    )

    # Step 5: Timestamp
    timestamp = time.time()

    # Step 6: Scope
    if scope is None:
        scope = ScopeDeclaration()

    # Step 7: Assemble
    return TransitionEnvelope(
        envelope_id=envelope_id,
        payload=payload,
        payload_hash=payload_hash,
        nonce=nonce,
        timestamp=timestamp,
        user_fingerprint=user_fp,
        machine_fingerprint=machine_fp,
        scope=scope,
        source_partition=source_partition,
        target_partition=target_partition,
        sealed_by=sealed_by,
        tests_passed=tests_passed,
        lint_passed=lint_passed,
        metadata=metadata or {},
    )
