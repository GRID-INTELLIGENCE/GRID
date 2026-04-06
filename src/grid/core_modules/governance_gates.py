"""Governance gates for consent and value-based access control.

Evaluates consent levels and value alignment to produce GateVerdict
decisions for safe agent operations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class GateVerdict(Enum):
    """Gate evaluation verdicts."""

    ALLOW = "allow"  # Action permitted
    DENY = "deny"  # Action blocked
    ESCALATE = "escalate"  # Requires human review
    DEFER = "defer"  # Postpone decision (needs more context)


class ConsentType(Enum):
    """Types of consent signals."""

    EXPLICIT = "explicit"  # User explicitly granted
    IMPLICIT = "implicit"  # Inferred from context
    INHERITED = "inherited"  # From parent scope
    DEFAULT = "default"  # System default
    REVOKED = "revoked"  # Previously granted, now withdrawn


class ValueCategory(Enum):
    """Value alignment categories for gate evaluation."""

    SAFETY = "safety"  # Physical/digital safety
    PRIVACY = "privacy"  # Data protection
    AUTONOMY = "autonomy"  # User agency
    INTEGRITY = "integrity"  # Data/system integrity
    TRANSPARENCY = "transparency"  # Explainability


@dataclass(frozen=True, slots=True)
class ConsentSignal:
    """A consent signal from the user or system."""

    consent_type: ConsentType
    scope: str  # What the consent covers
    granted_at: datetime
    expires_at: datetime | None = None
    conditions: tuple[str, ...] = ()
    source: str = "user"

    def is_valid(self, current_time: datetime | None = None) -> bool:
        """Check if consent is currently valid."""
        if self.consent_type == ConsentType.REVOKED:
            return False
        if self.expires_at:
            now = current_time or datetime.now()
            return now < self.expires_at
        return True


@dataclass(frozen=True, slots=True)
class ValueAlignment:
    """Value alignment score for an action."""

    category: ValueCategory
    score: float  # -1.0 (violation) to 1.0 (fully aligned)
    rationale: str
    weight: float = 1.0  # Importance weight


@dataclass(slots=True)
class GateEvaluation:
    """Complete gate evaluation result."""

    verdict: GateVerdict
    action: str
    timestamp: datetime
    consent_signals: list[ConsentSignal]
    value_alignments: list[ValueAlignment]
    aggregate_score: float
    explanation: str
    trace_id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            "trace_id": self.trace_id,
            "verdict": self.verdict.value,
            "action": self.action,
            "timestamp": self.timestamp.isoformat(),
            "aggregate_score": self.aggregate_score,
            "explanation": self.explanation,
            "consent_count": len(self.consent_signals),
            "value_checks": len(self.value_alignments),
            "metadata": self.metadata,
        }


class GovernanceGate:
    """Governance gate for consent and value-based access control.

    Evaluates whether an action should be permitted based on
    consent signals and value alignment scores.
    """

    # Threshold configuration
    DENY_THRESHOLD = -0.3  # Below this = deny
    ESCALATE_THRESHOLD = 0.3  # Below this but above deny = escalate
    ALLOW_THRESHOLD = 0.6  # Above this = allow (between = defer)

    def __init__(
        self,
        *,
        require_explicit_consent: bool = False,
        strict_mode: bool = False,
    ) -> None:
        """Initialize the governance gate.

        Args:
            require_explicit_consent: If True, implicit consent is not sufficient.
            strict_mode: If True, any negative value alignment triggers escalation.
        """
        self.require_explicit_consent = require_explicit_consent
        self.strict_mode = strict_mode
        self._evaluation_history: list[GateEvaluation] = []

    def evaluate(
        self,
        action: str,
        consent_signals: list[ConsentSignal],
        value_alignments: list[ValueAlignment],
        *,
        context: dict[str, Any] | None = None,
    ) -> GateEvaluation:
        """Evaluate an action against consent and value alignment.

        Args:
            action: The action being evaluated.
            consent_signals: Consent signals from user/system.
            value_alignments: Value alignment scores for the action.
            context: Optional additional context for evaluation.

        Returns:
            GateEvaluation with verdict and explanation.

        Example:
            >>> gate = GovernanceGate()
            >>> consent = ConsentSignal(
            ...     consent_type=ConsentType.EXPLICIT,
            ...     scope="file_operations",
            ...     granted_at=datetime.now(),
            ... )
            >>> value = ValueAlignment(
            ...     category=ValueCategory.INTEGRITY,
            ...     score=0.8,
            ...     rationale="Standard file operation",
            ... )
            >>> result = gate.evaluate("write_file", [consent], [value])
            >>> result.verdict
            <GateVerdict.ALLOW: 'allow'>
        """
        timestamp = datetime.now()

        # Check consent validity
        consent_valid = self._evaluate_consent(consent_signals, action)
        if not consent_valid:
            return self._create_evaluation(
                verdict=GateVerdict.DENY,
                action=action,
                timestamp=timestamp,
                consent_signals=consent_signals,
                value_alignments=value_alignments,
                aggregate_score=-1.0,
                explanation="No valid consent for this action",
                context=context,
            )

        # Calculate aggregate value score
        aggregate_score = self._calculate_aggregate_score(value_alignments)

        # Check for critical violations in strict mode
        if self.strict_mode:
            critical_violation = self._check_critical_violations(value_alignments)
            if critical_violation:
                return self._create_evaluation(
                    verdict=GateVerdict.ESCALATE,
                    action=action,
                    timestamp=timestamp,
                    consent_signals=consent_signals,
                    value_alignments=value_alignments,
                    aggregate_score=aggregate_score,
                    explanation=f"Critical value violation: {critical_violation}",
                    context=context,
                )

        # Determine verdict based on aggregate score
        verdict, explanation = self._score_to_verdict(aggregate_score, action)

        return self._create_evaluation(
            verdict=verdict,
            action=action,
            timestamp=timestamp,
            consent_signals=consent_signals,
            value_alignments=value_alignments,
            aggregate_score=aggregate_score,
            explanation=explanation,
            context=context,
        )

    def _evaluate_consent(self, signals: list[ConsentSignal], action: str) -> bool:
        """Check if valid consent exists for the action."""
        if not signals:
            return False

        for signal in signals:
            if not signal.is_valid():
                continue

            if self.require_explicit_consent:
                if signal.consent_type != ConsentType.EXPLICIT:
                    continue

            # Check scope matching (simplified)
            if signal.scope == "*" or action.startswith(signal.scope):
                return True

        return False

    def _calculate_aggregate_score(self, alignments: list[ValueAlignment]) -> float:
        """Calculate weighted aggregate value alignment score."""
        if not alignments:
            return 0.0

        total_weight = sum(a.weight for a in alignments)
        if total_weight == 0:
            return 0.0

        weighted_sum = sum(a.score * a.weight for a in alignments)
        return weighted_sum / total_weight

    def _check_critical_violations(self, alignments: list[ValueAlignment]) -> str | None:
        """Check for critical value violations."""
        for alignment in alignments:
            if alignment.score < -0.5:
                return f"{alignment.category.value}: {alignment.rationale}"
        return None

    def _score_to_verdict(self, score: float, action: str) -> tuple[GateVerdict, str]:
        """Convert aggregate score to verdict."""
        if score < self.DENY_THRESHOLD:
            return GateVerdict.DENY, f"Action '{action}' blocked: value alignment too low ({score:.2f})"
        if score < self.ESCALATE_THRESHOLD:
            return GateVerdict.ESCALATE, f"Action '{action}' requires review: marginal value alignment ({score:.2f})"
        if score < self.ALLOW_THRESHOLD:
            return GateVerdict.DEFER, f"Action '{action}' deferred: needs more context ({score:.2f})"
        return GateVerdict.ALLOW, f"Action '{action}' permitted: good value alignment ({score:.2f})"

    def _create_evaluation(
        self,
        *,
        verdict: GateVerdict,
        action: str,
        timestamp: datetime,
        consent_signals: list[ConsentSignal],
        value_alignments: list[ValueAlignment],
        aggregate_score: float,
        explanation: str,
        context: dict[str, Any] | None,
    ) -> GateEvaluation:
        """Create and record an evaluation."""
        evaluation = GateEvaluation(
            verdict=verdict,
            action=action,
            timestamp=timestamp,
            consent_signals=consent_signals,
            value_alignments=value_alignments,
            aggregate_score=aggregate_score,
            explanation=explanation,
            metadata=context or {},
        )
        self._evaluation_history.append(evaluation)
        return evaluation

    def get_history(self) -> list[GateEvaluation]:
        """Get evaluation history."""
        return list(self._evaluation_history)

    def clear_history(self) -> None:
        """Clear evaluation history."""
        self._evaluation_history.clear()


def evaluate_gate(
    action: str,
    consent: ConsentSignal,
    value: ValueAlignment,
    *,
    strict: bool = False,
) -> GateVerdict:
    """Convenience function for simple gate evaluation.

    Args:
        action: Action to evaluate.
        consent: Single consent signal.
        value: Single value alignment.
        strict: Enable strict mode.

    Returns:
        GateVerdict for the action.
    """
    gate = GovernanceGate(strict_mode=strict)
    result = gate.evaluate(action, [consent], [value])
    return result.verdict
