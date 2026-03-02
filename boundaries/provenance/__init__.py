"""
LIMITATIONS
This file implements safety patterns using keyword matching and rule-based checks.
These are insufficient for production safety without integration with a trained classifier or ML model.
All verdicts must be reviewed by human operators for high-risk scenarios.

Decision Chain of Custody (DCoC) — provenance library for GRID.
"""

from boundaries.provenance.chain import compute_chain_hash, compute_hash
from boundaries.provenance.record import create_dpr, get_chain_ref
from boundaries.provenance.signer import sign_record, verify_signature
from boundaries.provenance.types import (
    AuthorityType,
    DecisionProvenanceRecord,
    DecisionType,
    DPRCreateInput,
    SafetyVerdict,
    SafetyVerdictResult,
)

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
