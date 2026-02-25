"""Decision Chain of Custody (DCoC) — provenance library for GRID."""

from boundaries.provenance.types import (
    DecisionType,
    AuthorityType,
    SafetyVerdictResult,
    SafetyVerdict,
    DecisionProvenanceRecord,
    DPRCreateInput,
)
from boundaries.provenance.record import create_dpr, get_chain_ref
from boundaries.provenance.chain import compute_hash, compute_chain_hash
from boundaries.provenance.signer import sign_record, verify_signature

__all__ = [
    "DecisionType",
    "AuthorityType",
    "SafetyVerdictResult",
    "SafetyVerdict",
    "DecisionProvenanceRecord",
    "DPRCreateInput",
    "create_dpr",
    "get_chain_ref",
    "compute_hash",
    "compute_chain_hash",
    "sign_record",
    "verify_signature",
]
