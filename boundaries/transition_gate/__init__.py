"""
Transition Gate: sealed-envelope handshake for cross-partition artifact transfers.

Provides cryptographic sealing, fingerprinting, nonce management, and verification
for transferring build artifacts from E:\\ (source) to C:\\ (deployment target).

Security model:
- Zero-trust at transfer boundary
- HMAC-SHA256 user fingerprints
- SHA-256 payload integrity
- Single-use nonces (burn after verify)
- Timestamp freshness enforcement
- Append-only audit trail

Usage:
    from boundaries.transition_gate import (
        seal_envelope,
        verify_envelope,
        TransitionEnvelope,
        NonceRegistry,
        GateKeeper,
    )
"""

from boundaries.transition_gate.envelope import (  # type: ignore
    TransitionEnvelope,
    seal_envelope,
)
from boundaries.transition_gate.fingerprint import (  # type: ignore
    compute_machine_fingerprint,
    compute_payload_hash,
    compute_user_fingerprint,
)
from boundaries.transition_gate.gate_keeper import (  # type: ignore
    GateKeeper,
    VerificationResult,
    verify_envelope,
)
from boundaries.transition_gate.nonce import NonceRegistry  # type: ignore

__all__ = [
    "TransitionEnvelope",
    "seal_envelope",
    "verify_envelope",
    "compute_machine_fingerprint",
    "compute_payload_hash",
    "compute_user_fingerprint",
    "GateKeeper",
    "VerificationResult",
    "NonceRegistry",
]
