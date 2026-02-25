"""DCoC type definitions — Decision Provenance Record schema."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class DecisionType(StrEnum):
    CLASSIFICATION = "classification"
    GENERATION = "generation"
    REFUSAL = "refusal"
    GATE_VERDICT = "gate_verdict"
    CONSENT_CHANGE = "consent_change"
    DATA_OPERATION = "data_operation"
    ESCALATION = "escalation"
    CIRCUIT_BREAKER = "circuit_breaker"


class AuthorityType(StrEnum):
    HUMAN_CONSENT = "human_consent"
    SYSTEM_POLICY = "system_policy"
    AUTONOMOUS_THRESHOLD = "autonomous_threshold"
    EMERGENCY_OVERRIDE = "emergency_override"


class SafetyVerdictResult(StrEnum):
    PASS = "pass"
    BLOCK = "block"
    ESCALATE = "escalate"
    WARN = "warn"


@dataclass
class SafetyVerdict:
    gate_id: str
    gate_type: str  # boundary | guardrail | refusal | preparedness | rate_limit | auth
    verdict: SafetyVerdictResult
    latency_ms: float
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "gate_type": self.gate_type,
            "verdict": self.verdict.value,
            "latency_ms": self.latency_ms,
            "confidence": self.confidence,
        }


@dataclass
class DecisionProvenanceRecord:
    dpr_id: str
    parent_dpr_id: str | None
    chain_hash: str

    timestamp: str
    sequence_number: int

    decision_type: DecisionType
    action_taken: str
    output_hash: str

    input_context_hash: str
    model_id: str | None
    model_parameters: dict[str, Any] | None
    confidence: float | None
    reasoning_summary: str

    authority_type: AuthorityType
    actor_id: str
    consent_reference: str | None

    safety_verdicts: list[SafetyVerdict]
    risk_tier: str | None
    jurisdiction: str | None

    signature: str
    provenance_version: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "dpr_id": self.dpr_id,
            "parent_dpr_id": self.parent_dpr_id,
            "chain_hash": self.chain_hash,
            "timestamp": self.timestamp,
            "sequence_number": self.sequence_number,
            "decision_type": self.decision_type.value,
            "action_taken": self.action_taken,
            "output_hash": self.output_hash,
            "input_context_hash": self.input_context_hash,
            "model_id": self.model_id,
            "model_parameters": self.model_parameters,
            "confidence": self.confidence,
            "reasoning_summary": self.reasoning_summary,
            "authority_type": self.authority_type.value,
            "actor_id": self.actor_id,
            "consent_reference": self.consent_reference,
            "safety_verdicts": [v.to_dict() for v in self.safety_verdicts],
            "risk_tier": self.risk_tier,
            "jurisdiction": self.jurisdiction,
            "signature": self.signature,
            "provenance_version": self.provenance_version,
        }


@dataclass
class DPRCreateInput:
    decision_type: DecisionType
    action_taken: str
    reasoning_summary: str
    authority_type: AuthorityType
    actor_id: str
    output_content: str | None = None
    input_context: str | None = None
    model_id: str | None = None
    model_parameters: dict[str, Any] | None = None
    confidence: float | None = None
    consent_reference: str | None = None
    safety_verdicts: list[SafetyVerdict] = field(default_factory=list)
    risk_tier: str | None = None
    jurisdiction: str | None = None


@dataclass
class ChainRef:
    dpr_id: str
    chain_hash: str
    sequence_number: int
