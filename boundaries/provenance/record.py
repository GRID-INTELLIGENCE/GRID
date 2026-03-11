"""
LIMITATIONS
This file implements safety patterns using keyword matching and rule-based checks.
These are insufficient for production safety without integration with a trained classifier or ML model.
All verdicts must be reviewed by human operators for high-risk scenarios.

DPR creation and serialization for DCoC.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

from boundaries.provenance.chain import compute_chain_hash, compute_hash
from boundaries.provenance.signer import sign_record
from boundaries.provenance.types import (
    ChainRef,
    DecisionProvenanceRecord,
    DPRCreateInput,
)

PROVENANCE_VERSION = "1.0.0"


def serialize_dpr_for_hashing(dpr_dict: dict) -> str:
    return json.dumps(dpr_dict, sort_keys=True, default=str)


def create_dpr(
    inp: DPRCreateInput,
    parent: ChainRef | None = None,
) -> DecisionProvenanceRecord:
    dpr_id = str(uuid.uuid4())
    timestamp = datetime.now(UTC).isoformat()
    sequence_number = parent.sequence_number + 1 if parent else 0

    output_hash = compute_hash(inp.output_content) if inp.output_content else compute_hash("")
    input_context_hash = compute_hash(inp.input_context) if inp.input_context else compute_hash("")

    partial = {
        "dpr_id": dpr_id,
        "parent_dpr_id": parent.dpr_id if parent else None,
        "timestamp": timestamp,
        "sequence_number": sequence_number,
        "decision_type": inp.decision_type.value,
        "action_taken": inp.action_taken,
        "output_hash": output_hash,
        "input_context_hash": input_context_hash,
        "model_id": inp.model_id,
        "model_parameters": inp.model_parameters,
        "confidence": inp.confidence,
        "reasoning_summary": inp.reasoning_summary,
        "authority_type": inp.authority_type.value,
        "actor_id": inp.actor_id,
        "consent_reference": inp.consent_reference,
        "safety_verdicts": [v.to_dict() for v in inp.safety_verdicts],
        "risk_tier": inp.risk_tier,
        "jurisdiction": inp.jurisdiction,
        "provenance_version": PROVENANCE_VERSION,
    }

    serialized = serialize_dpr_for_hashing(partial)
    chain_hash = compute_chain_hash(
        parent.chain_hash if parent else None,
        serialized,
    )

    with_chain = {**partial, "chain_hash": chain_hash}
    full_serialized = json.dumps(with_chain, sort_keys=True, default=str)
    signature = sign_record(full_serialized)

    return DecisionProvenanceRecord(
        dpr_id=dpr_id,
        parent_dpr_id=parent.dpr_id if parent else None,
        chain_hash=chain_hash,
        timestamp=timestamp,
        sequence_number=sequence_number,
        decision_type=inp.decision_type,
        action_taken=inp.action_taken,
        output_hash=output_hash,
        input_context_hash=input_context_hash,
        model_id=inp.model_id,
        model_parameters=inp.model_parameters,
        confidence=inp.confidence,
        reasoning_summary=inp.reasoning_summary,
        authority_type=inp.authority_type,
        actor_id=inp.actor_id,
        consent_reference=inp.consent_reference,
        safety_verdicts=inp.safety_verdicts,
        risk_tier=inp.risk_tier,
        jurisdiction=inp.jurisdiction,
        signature=signature,
        provenance_version=PROVENANCE_VERSION,
    )


def get_chain_ref(dpr: DecisionProvenanceRecord) -> ChainRef:
    return ChainRef(
        dpr_id=dpr.dpr_id,
        chain_hash=dpr.chain_hash,
        sequence_number=dpr.sequence_number,
    )
