"""
Reasoning stabilization service.

Implements deterministic reasoning stabilization, drift checks, and
roundtable reconciliation with persistent inference-gap logging.
"""

from __future__ import annotations

import hashlib
import json
import re
import threading
import uuid
from pathlib import Path
from typing import Any, Literal

from application.mothership.schemas.reasoning import (
    DecisionQualityRecord,
    DriftCheckResponse,
    DriftSignal,
    GapSource,
    GapStatus,
    InferenceGapRecord,
    ReasoningTrace,
    RoundtableReconcileResponse,
    StabilizeResponse,
    UncertaintySpan,
)

_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "with",
    "we",
    "you",
    "this",
    "those",
    "these",
    "was",
    "were",
    "will",
    "can",
    "could",
    "should",
    "would",
}

_UNCERTAINTY_TERMS: dict[str, str] = {
    "unknown": "high",
    "unclear": "high",
    "assume": "medium",
    "assuming": "medium",
    "might": "medium",
    "maybe": "medium",
    "possibly": "medium",
    "probably": "low",
    "likely": "low",
    "roughly": "low",
}

_POLARITY_PAIRS: list[tuple[str, str]] = [
    ("always", "never"),
    ("allow", "deny"),
    ("increase", "decrease"),
    ("stable", "unstable"),
    ("safe", "unsafe"),
    ("true", "false"),
]


class InferenceGapLedger:
    """Thread-safe in-memory ledger with JSONL append persistence."""

    def __init__(self, output_path: Path | None = None, max_records: int = 5000) -> None:
        self._records: list[InferenceGapRecord] = []
        self._lock = threading.Lock()
        self._max_records = max_records
        self._output_path = output_path or Path("artifacts") / "inference_gap_ledger.jsonl"
        self._output_path.parent.mkdir(parents=True, exist_ok=True)

    def append(
        self,
        *,
        case_id: str,
        source: GapSource,
        summary: str,
        confidence: float,
        metadata: dict[str, Any] | None = None,
    ) -> InferenceGapRecord:
        """Create and store a new open inference gap."""
        record = InferenceGapRecord(
            gap_id=f"gap_{uuid.uuid4().hex[:12]}",
            case_id=case_id,
            source=source,
            summary=summary,
            status=GapStatus.OPEN,
            confidence=max(0.0, min(1.0, confidence)),
            metadata=metadata or {},
        )
        with self._lock:
            self._records.append(record)
            if len(self._records) > self._max_records:
                self._records = self._records[-self._max_records :]
            self._append_to_disk(record)
        return record

    def list_case(self, case_id: str, status: GapStatus | None = None, limit: int = 100) -> list[InferenceGapRecord]:
        """Return gap records for a case, newest first."""
        with self._lock:
            matches = [r for r in self._records if r.case_id == case_id]
            if status is not None:
                matches = [r for r in matches if r.status == status]
            return list(reversed(matches[-limit:]))

    def _append_to_disk(self, record: InferenceGapRecord) -> None:
        """Best-effort JSONL append. Failures are intentionally ignored."""
        try:
            with self._output_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record.model_dump(mode="json"), sort_keys=True))
                handle.write("\n")
        except OSError:
            # Keep request path non-failing when filesystem append is unavailable.
            return


class ReasoningStabilityService:
    """Deterministic stabilizer for reasoning traces and drift checks."""

    def __init__(self, ledger: InferenceGapLedger | None = None) -> None:
        self._ledger = ledger or InferenceGapLedger()

    @staticmethod
    def derive_case_id(input_text: str) -> str:
        """Derive deterministic case id from request input when client omits one."""
        digest = hashlib.sha256(input_text.encode("utf-8")).hexdigest()[:10]
        return f"case_{digest}"

    def stabilize(
        self,
        *,
        input_text: str,
        context: dict[str, Any],
        task_type: str,
        risk_level: str,
        case_id: str,
        include_gap_log: bool,
    ) -> StabilizeResponse:
        """Build stabilized reasoning trace with quality and uncertainty scoring."""
        cleaned = input_text.strip()
        context_keys = [k for k, v in context.items() if v not in (None, "", [], {})]
        uncertainty = self._extract_uncertainty(cleaned)
        contradiction_count = len(self._find_polarity_conflicts(cleaned, cleaned))

        trace = [
            ReasoningTrace(
                step_number=1,
                stage="intent_capture",
                statement=f"Task '{task_type}' received with risk level '{risk_level}'.",
                confidence=0.9,
                evidence_refs=["request.task_type", "request.risk_level"],
            ),
            ReasoningTrace(
                step_number=2,
                stage="context_alignment",
                statement=(
                    f"Context anchors detected: {', '.join(context_keys[:6])}"
                    if context_keys
                    else "No strong context anchors were supplied."
                ),
                confidence=0.82 if context_keys else 0.55,
                evidence_refs=[f"context.{k}" for k in context_keys[:6]],
            ),
            ReasoningTrace(
                step_number=3,
                stage="uncertainty_scan",
                statement=(
                    f"Detected {len(uncertainty)} uncertainty span(s); contradiction markers={contradiction_count}."
                ),
                confidence=0.78,
                evidence_refs=["request.input"],
            ),
            ReasoningTrace(
                step_number=4,
                stage="action_projection",
                statement="Constructed next-step actions with emphasis on factual grounding and coherence checks.",
                confidence=0.8,
                evidence_refs=["stability.policy.v1"],
            ),
        ]

        if not context_keys:
            uncertainty.append(
                UncertaintySpan(
                    text="missing context",
                    reason="No context fields with substantive values were provided.",
                    severity="high",
                )
            )

        next_actions = self._next_actions(risk_level=risk_level, uncertainty=uncertainty, context_keys=context_keys)
        quality = self._quality_record(
            uncertainty_count=len(uncertainty),
            context_anchor_count=len(context_keys),
            contradiction_count=contradiction_count,
        )

        logged_gaps: list[InferenceGapRecord] = []
        if include_gap_log:
            for span in uncertainty:
                if span.severity == "low":
                    continue
                logged_gaps.append(
                    self._ledger.append(
                        case_id=case_id,
                        source=GapSource.STABILIZE,
                        summary=f"Uncertainty: {span.reason}",
                        confidence=0.65 if span.severity == "medium" else 0.45,
                        metadata={"span_text": span.text, "severity": span.severity},
                    )
                )

        return StabilizeResponse(
            stabilized_trace=trace,
            uncertainty_map=uncertainty,
            next_actions=next_actions,
            quality_record=quality,
            logged_gaps=logged_gaps,
        )

    def drift_check(
        self,
        *,
        trace_so_far: list[dict[str, Any] | str] | str,
        candidate_response: str,
        case_id: str,
        include_gap_log: bool,
    ) -> DriftCheckResponse:
        """Detect intent drift and contradictions before response release."""
        trace_text = self._flatten_trace(trace_so_far)
        candidate = candidate_response.strip()

        drift_flags: list[DriftSignal] = []
        contradictions = self._find_polarity_conflicts(trace_text, candidate)

        if contradictions:
            drift_flags.append(
                DriftSignal(
                    signal_type="contradiction",
                    severity="high",
                    message="Candidate response conflicts with established trace polarity.",
                    evidence=contradictions[:3],
                )
            )

        trace_tokens = self._tokenize(trace_text)
        candidate_tokens = self._tokenize(candidate)
        overlap = len(trace_tokens & candidate_tokens)
        coverage = overlap / max(1, len(candidate_tokens))

        if coverage < 0.2:
            drift_flags.append(
                DriftSignal(
                    signal_type="intent_shift",
                    severity="medium",
                    message="Candidate response introduces mostly new intent tokens with weak trace overlap.",
                    evidence=[f"token_overlap={coverage:.2f}"],
                )
            )

        if (
            any(x in candidate.lower() for x in ("guarantee", "always", "never"))
            and "evidence" not in candidate.lower()
        ):
            drift_flags.append(
                DriftSignal(
                    signal_type="unsupported_claim",
                    severity="medium",
                    message="Strong certainty language appears without explicit evidence references.",
                    evidence=["missing 'evidence' markers in candidate response"],
                )
            )

        if len(candidate.split()) < 6 and len(trace_text.split()) > 30:
            drift_flags.append(
                DriftSignal(
                    signal_type="coherence_drop",
                    severity="low",
                    message="Candidate response may be too compressed relative to trace complexity.",
                    evidence=["candidate_length_short"],
                )
            )

        repair = self._repair_suggestions(drift_flags)

        logged_gaps: list[InferenceGapRecord] = []
        if include_gap_log:
            for signal in drift_flags:
                if signal.severity == "low":
                    continue
                logged_gaps.append(
                    self._ledger.append(
                        case_id=case_id,
                        source=GapSource.DRIFT_CHECK,
                        summary=f"Drift signal [{signal.signal_type}]: {signal.message}",
                        confidence=0.6 if signal.severity == "medium" else 0.4,
                        metadata={"evidence": signal.evidence, "severity": signal.severity},
                    )
                )

        return DriftCheckResponse(
            drift_flags=drift_flags,
            contradictions=contradictions,
            repair_suggestions=repair,
            logged_gaps=logged_gaps,
        )

    def reconcile_roundtable(
        self,
        *,
        case_id: str,
        human_notes: list[str] | str,
        system_trace: list[dict[str, Any] | str] | str,
        topic: str | None,
    ) -> RoundtableReconcileResponse:
        """Reconcile human notes and system trace using equal-weight logic."""
        note_lines = self._normalize_notes(human_notes)
        system_lines = self._normalize_system_trace(system_trace)

        resolved: list[str] = []
        open_gaps: list[InferenceGapRecord] = []

        for statement in system_lines:
            best_overlap = max((self._overlap(statement, note) for note in note_lines), default=0.0)
            if best_overlap >= 0.35:
                resolved.append(statement)
                continue
            open_gaps.append(
                self._ledger.append(
                    case_id=case_id,
                    source=GapSource.ROUNDTABLE_RECONCILE,
                    summary=f"System statement not corroborated by human notes: {statement}",
                    confidence=max(0.3, 1.0 - best_overlap),
                    metadata={"overlap": round(best_overlap, 3), "topic": topic or "general"},
                )
            )

        policy_hints = [
            "Require explicit evidence references before high-certainty claims.",
            "Use roundtable reconciliation when token overlap < 0.35 between system and human notes.",
            "Treat unresolved gaps as open until corroborating notes or data arrive.",
        ]
        if open_gaps:
            policy_hints.append("Escalate unresolved high-risk gaps to manual review before action release.")

        synthesis = f"Roundtable reconciled {len(resolved)} statement(s) with {len(open_gaps)} open gap(s)" + (
            f" on topic '{topic}'." if topic else "."
        )

        return RoundtableReconcileResponse(
            resolved_facts=resolved[:20],
            open_gaps=open_gaps[:20],
            updated_policy_hints=policy_hints,
            synthesis=synthesis,
        )

    def list_case_gaps(
        self, case_id: str, status: GapStatus | None = None, limit: int = 100
    ) -> list[InferenceGapRecord]:
        """List persisted gaps for case."""
        return self._ledger.list_case(case_id=case_id, status=status, limit=limit)

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        tokens = re.findall(r"[a-zA-Z0-9_]+", text.lower())
        return {t for t in tokens if len(t) > 2 and t not in _STOPWORDS}

    def _extract_uncertainty(self, text: str) -> list[UncertaintySpan]:
        spans: list[UncertaintySpan] = []
        lowered = text.lower()
        for term, severity in _UNCERTAINTY_TERMS.items():
            for match in re.finditer(rf"\b{re.escape(term)}\b", lowered):
                start = max(0, match.start() - 25)
                end = min(len(text), match.end() + 25)
                snippet = text[start:end].strip()
                severity_label: Literal["low", "medium", "high"] = "medium"
                if severity == "high":
                    severity_label = "high"
                elif severity == "low":
                    severity_label = "low"
                spans.append(
                    UncertaintySpan(
                        text=snippet or term,
                        reason=f"Contains uncertainty marker '{term}'.",
                        severity=severity_label,
                        start_index=match.start(),
                        end_index=match.end(),
                    )
                )
        return spans[:25]

    @staticmethod
    def _find_polarity_conflicts(base_text: str, candidate_text: str) -> list[str]:
        base = base_text.lower()
        candidate = candidate_text.lower()
        conflicts: list[str] = []
        for left, right in _POLARITY_PAIRS:
            if left in base and right in candidate:
                conflicts.append(f"Trace uses '{left}' while candidate uses '{right}'.")
            elif right in base and left in candidate:
                conflicts.append(f"Trace uses '{right}' while candidate uses '{left}'.")
        return conflicts

    @staticmethod
    def _next_actions(risk_level: str, uncertainty: list[UncertaintySpan], context_keys: list[str]) -> list[str]:
        actions = [
            "Anchor final response to verified context fields.",
            "Preserve step-by-step trace in output metadata for auditability.",
        ]
        if not context_keys:
            actions.insert(0, "Request at least one concrete context anchor before final execution.")
        if any(item.severity == "high" for item in uncertainty):
            actions.append("Route high-severity uncertainty spans to manual validation.")
        if risk_level == "high":
            actions.append("Apply conservative mode: block irreversible actions until contradictions are zero.")
        return actions

    @staticmethod
    def _quality_record(
        *,
        uncertainty_count: int,
        context_anchor_count: int,
        contradiction_count: int,
    ) -> DecisionQualityRecord:
        uncertainty_penalty = min(0.6, 0.08 * uncertainty_count)
        contradiction_penalty = min(0.3, 0.1 * contradiction_count)
        evidence_coverage = min(1.0, 0.2 + (context_anchor_count * 0.2))
        coherence = max(0.0, 1.0 - uncertainty_penalty - contradiction_penalty)
        quality = max(0.0, min(1.0, (coherence * 0.5) + (evidence_coverage * 0.5)))

        return DecisionQualityRecord(
            quality_score=quality,
            coherence=coherence,
            evidence_coverage=evidence_coverage,
            uncertainty_penalty=min(1.0, uncertainty_penalty + contradiction_penalty),
            recommendations=[
                "Increase context anchors to improve evidence coverage."
                if evidence_coverage < 0.6
                else "Maintain current evidence anchoring level.",
                "Reduce ambiguity terms in upstream prompt when possible."
                if uncertainty_count > 0
                else "Current prompt clarity is strong.",
            ],
        )

    @staticmethod
    def _repair_suggestions(signals: list[DriftSignal]) -> list[str]:
        if not signals:
            return ["No drift signals detected. Response can proceed to final review."]

        suggestions: list[str] = []
        for signal in signals:
            if signal.signal_type == "contradiction":
                suggestions.append("Rewrite conflicting statements and align polarity with established trace.")
            elif signal.signal_type == "intent_shift":
                suggestions.append("Re-anchor response to original objective and core entities.")
            elif signal.signal_type == "unsupported_claim":
                suggestions.append("Add concrete evidence references or reduce certainty language.")
            elif signal.signal_type == "coherence_drop":
                suggestions.append("Expand candidate response to preserve reasoning continuity.")
        return sorted(set(suggestions))

    @staticmethod
    def _flatten_trace(trace_so_far: list[dict[str, Any] | str] | str) -> str:
        if isinstance(trace_so_far, str):
            return trace_so_far
        parts: list[str] = []
        for item in trace_so_far:
            if isinstance(item, str):
                parts.append(item)
                continue
            statement = str(item.get("statement") or item.get("text") or item.get("stage") or "")
            if statement:
                parts.append(statement)
        return "\n".join(parts)

    @staticmethod
    def _normalize_notes(notes: list[str] | str) -> list[str]:
        if isinstance(notes, str):
            raw = [chunk.strip() for chunk in re.split(r"[.\n]", notes) if chunk.strip()]
            return raw[:30]
        return [line.strip() for line in notes if line.strip()][:30]

    @staticmethod
    def _normalize_system_trace(trace: list[dict[str, Any] | str] | str) -> list[str]:
        if isinstance(trace, str):
            return [chunk.strip() for chunk in re.split(r"[.\n]", trace) if chunk.strip()][:40]
        lines: list[str] = []
        for item in trace:
            if isinstance(item, str):
                if item.strip():
                    lines.append(item.strip())
                continue
            statement = str(item.get("statement") or item.get("text") or "")
            if statement.strip():
                lines.append(statement.strip())
        return lines[:40]

    def _overlap(self, a: str, b: str) -> float:
        ta = self._tokenize(a)
        tb = self._tokenize(b)
        if not ta or not tb:
            return 0.0
        return len(ta & tb) / len(ta | tb)
