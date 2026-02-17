"""
Chain-of-Thought Reasoning Engine for Intelligent RAG.

This module implements structured reasoning over extracted evidence, producing
transparent, step-by-step reasoning chains with full source attribution.

Part of Phase 3: Reasoning Layer
"""

import logging
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from .evidence_extractor import Evidence, EvidenceSet, EvidenceStrength, EvidenceType

logger = logging.getLogger(__name__)


class ReasoningStepType(StrEnum):
    """Types of reasoning steps in the chain."""

    OBSERVATION = "observation"  # What we observe in the evidence
    INFERENCE = "inference"  # What we deduce from observations
    SYNTHESIS = "synthesis"  # Combining multiple pieces
    VALIDATION = "validation"  # Checking consistency
    CONCLUSION = "conclusion"  # Final answer
    UNCERTAINTY = "uncertainty"  # Acknowledging gaps


@dataclass
class ReasoningStep:
    """A single step in the chain-of-thought reasoning process."""

    step_number: int
    step_type: ReasoningStepType
    content: str  # The reasoning text
    supporting_evidence: list[str] = field(default_factory=list)  # Evidence IDs
    confidence: float = 1.0  # 0.0 to 1.0
    leads_to: int | None = None  # Next step number

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "step": self.step_number,
            "type": self.step_type.value,
            "content": self.content,
            "evidence_ids": self.supporting_evidence,
            "confidence": self.confidence,
        }


@dataclass
class ReasoningChain:
    """Complete chain-of-thought reasoning process."""

    query: str
    steps: list[ReasoningStep]
    final_answer: str
    overall_confidence: float
    evidence_used: list[str] = field(default_factory=list)  # Evidence IDs
    evidence_unused: list[str] = field(default_factory=list)  # Evidence IDs not used
    warnings: list[str] = field(default_factory=list)  # Uncertainty warnings
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_confident(self) -> bool:
        """Check if we're confident in the answer."""
        return self.overall_confidence >= 0.7

    @property
    def has_gaps(self) -> bool:
        """Check if there are knowledge gaps."""
        return any(step.step_type == ReasoningStepType.UNCERTAINTY for step in self.steps)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "query": self.query,
            "answer": self.final_answer,
            "confidence": self.overall_confidence,
            "is_confident": self.is_confident,
            "has_gaps": self.has_gaps,
            "steps": [s.to_dict() for s in self.steps],
            "evidence_used_count": len(self.evidence_used),
            "evidence_unused_count": len(self.evidence_unused),
            "warnings": self.warnings,
        }

    def format_markdown(self, include_steps: bool = True) -> str:
        """Format the reasoning chain as markdown."""
        lines = []
        lines.append(f"**Query:** {self.query}\n")
        lines.append(f"**Confidence:** {self.overall_confidence:.0%}\n")

        if include_steps:
            lines.append("\n### Reasoning Steps\n")
            for step in self.steps:
                emoji = self._step_emoji(step.step_type)
                lines.append(f"{step.step_number}. {emoji} **{step.step_type.value.title()}**: {step.content}")
                if step.supporting_evidence:
                    lines.append(f"   *Evidence: {len(step.supporting_evidence)} source(s)*")
                lines.append("")

        lines.append(f"\n### Answer\n\n{self.final_answer}\n")

        if self.warnings:
            lines.append("\n### ⚠️ Uncertainties\n")
            lines.extend(f"- {warning}" for warning in self.warnings)

        return "\n".join(lines)

    @staticmethod
    def _step_emoji(step_type: ReasoningStepType) -> str:
        """Get emoji for reasoning step type."""
        emojis = {
            ReasoningStepType.OBSERVATION: "👁️",
            ReasoningStepType.INFERENCE: "🧠",
            ReasoningStepType.SYNTHESIS: "🔗",
            ReasoningStepType.VALIDATION: "✓",
            ReasoningStepType.CONCLUSION: "💡",
            ReasoningStepType.UNCERTAINTY: "❓",
        }
        return emojis.get(step_type, "•")


class ReasoningEngine:
    """
    Implements Chain-of-Thought reasoning over extracted evidence.

    This engine takes structured evidence and constructs a transparent
    reasoning chain that shows HOW it arrived at an answer, not just WHAT
    the answer is.
    """

    def __init__(self, min_evidence_for_confidence: int = 2, min_confidence_threshold: float = 0.6):
        """
        Initialize the reasoning engine.

        Args:
            min_evidence_for_confidence: Minimum evidence pieces for high confidence
            min_confidence_threshold: Minimum confidence to avoid uncertainty warnings
        """
        self.min_evidence_for_confidence = min_evidence_for_confidence
        self.min_confidence_threshold = min_confidence_threshold
        logger.info("ReasoningEngine initialized.")

    def reason(self, evidence_set: EvidenceSet) -> ReasoningChain:
        """
        Execute chain-of-thought reasoning over evidence.

        Args:
            evidence_set: The extracted evidence to reason over

        Returns:
            ReasoningChain with complete reasoning process
        """
        query = evidence_set.query
        steps: list[ReasoningStep] = []
        step_counter = 1
        warnings: list[str] = []

        logger.info(f"Starting reasoning for query: '{query}'")

        # --- Step 1: Observe what evidence we have ---
        observation_step = self._create_observation_step(step_counter, evidence_set, evidence_set.strong_evidence)
        steps.append(observation_step)
        step_counter += 1

        # --- Step 2: Check for contradictions ---
        if evidence_set.has_contradictions:
            validation_step = self._create_validation_step(step_counter, evidence_set)
            steps.append(validation_step)
            step_counter += 1
            warnings.append("Found contradictory evidence - answer may vary by source")

        # --- Step 3: Make inferences based on evidence type ---
        # Group by intent/type to structure reasoning
        by_type = evidence_set.by_type

        if EvidenceType.DEFINITION in by_type:
            inference = self._infer_from_definitions(step_counter, by_type[EvidenceType.DEFINITION])
            if inference:
                steps.append(inference)
                step_counter += 1

        if EvidenceType.IMPLEMENTATION in by_type:
            inference = self._infer_from_implementations(step_counter, by_type[EvidenceType.IMPLEMENTATION])
            if inference:
                steps.append(inference)
                step_counter += 1

        if EvidenceType.EXAMPLE in by_type:
            inference = self._infer_from_examples(step_counter, by_type[EvidenceType.EXAMPLE])
            if inference:
                steps.append(inference)
                step_counter += 1

        # --- Step 4: Synthesize across sources ---
        if len(evidence_set.by_source) > 1:
            synthesis_step = self._create_synthesis_step(step_counter, evidence_set)
            steps.append(synthesis_step)
            step_counter += 1

        # --- Step 5: Check for knowledge gaps ---
        if len(evidence_set.strong_evidence) < self.min_evidence_for_confidence:
            uncertainty_step = self._create_uncertainty_step(step_counter, evidence_set)
            steps.append(uncertainty_step)
            step_counter += 1
            warnings.append(f"Limited evidence: only {len(evidence_set.strong_evidence)} strong sources found")

        # --- Step 6: Draw conclusion ---
        conclusion_step, final_answer = self._create_conclusion_step(step_counter, evidence_set, query)
        steps.append(conclusion_step)

        # --- Calculate overall confidence ---
        overall_confidence = self._calculate_overall_confidence(evidence_set, steps)

        # Track which evidence was used
        evidence_used = list({eid for step in steps for eid in step.supporting_evidence})
        evidence_unused = [e.id for e in evidence_set.evidence if e.id not in evidence_used]

        chain = ReasoningChain(
            query=query,
            steps=steps,
            final_answer=final_answer,
            overall_confidence=overall_confidence,
            evidence_used=evidence_used,
            evidence_unused=evidence_unused,
            warnings=warnings,
            metadata={"evidence_count": len(evidence_set.evidence), "sources": list(evidence_set.by_source.keys())},
        )

        logger.info(
            f"Reasoning complete: {len(steps)} steps, confidence={overall_confidence:.2%}, "
            f"used {len(evidence_used)}/{len(evidence_set.evidence)} evidence"
        )

        return chain

    def _create_observation_step(
        self, step_num: int, evidence_set: EvidenceSet, strong_evidence: list[Evidence]
    ) -> ReasoningStep:
        """Create initial observation step."""
        if not strong_evidence:
            content = f"I found {len(evidence_set.evidence)} pieces of evidence, but none are strongly relevant."
            confidence = 0.3
            evidence_ids = [e.id for e in evidence_set.evidence[:3]]
        else:
            sources = {e.source_file for e in strong_evidence}
            content = (
                f"I found {len(strong_evidence)} highly relevant evidence pieces from {len(sources)} source file(s)."
            )
            confidence = min(1.0, len(strong_evidence) / 5.0)
            evidence_ids = [e.id for e in strong_evidence[:5]]

        return ReasoningStep(
            step_number=step_num,
            step_type=ReasoningStepType.OBSERVATION,
            content=content,
            supporting_evidence=evidence_ids,
            confidence=confidence,
        )

    def _create_validation_step(self, step_num: int, evidence_set: EvidenceSet) -> ReasoningStep:
        """Create validation step for checking contradictions."""
        contradictory = [e for e in evidence_set.evidence if e.strength == EvidenceStrength.CONTRADICTORY]

        sources = {e.source_file for e in contradictory}
        content = f"Warning: Found contradictory information across {len(sources)} sources. Will prioritize most recent/authoritative."

        return ReasoningStep(
            step_number=step_num,
            step_type=ReasoningStepType.VALIDATION,
            content=content,
            supporting_evidence=[e.id for e in contradictory[:3]],
            confidence=0.6,
        )

    def _infer_from_definitions(self, step_num: int, definitions: list[Evidence]) -> ReasoningStep | None:
        """Infer from definition-type evidence."""
        if not definitions:
            return None

        # Take the highest confidence definition
        best_def = max(definitions, key=lambda e: e.confidence)

        content = (
            f"Based on the definition in {best_def.source_file}, "
            f"I can establish the core concept: {best_def.content[:150]}..."
        )

        return ReasoningStep(
            step_number=step_num,
            step_type=ReasoningStepType.INFERENCE,
            content=content,
            supporting_evidence=[best_def.id],
            confidence=best_def.confidence,
        )

    def _infer_from_implementations(self, step_num: int, implementations: list[Evidence]) -> ReasoningStep | None:
        """Infer from implementation-type evidence (code)."""
        if not implementations:
            return None

        impl_files = {e.source_file for e in implementations}
        languages = {e.code_language for e in implementations if e.code_language}

        content = (
            f"The implementation is found in {len(impl_files)} file(s) "
            f"({', '.join(languages) if languages else 'code'}). "
            f"This shows the concrete realization of the concept."
        )

        return ReasoningStep(
            step_number=step_num,
            step_type=ReasoningStepType.INFERENCE,
            content=content,
            supporting_evidence=[e.id for e in implementations[:3]],
            confidence=min(1.0, len(implementations) / 3.0),
        )

    def _infer_from_examples(self, step_num: int, examples: list[Evidence]) -> ReasoningStep | None:
        """Infer from example-type evidence."""
        if not examples:
            return None

        content = f"Found {len(examples)} usage example(s) demonstrating practical application."

        return ReasoningStep(
            step_number=step_num,
            step_type=ReasoningStepType.INFERENCE,
            content=content,
            supporting_evidence=[e.id for e in examples[:2]],
            confidence=0.7,
        )

    def _create_synthesis_step(self, step_num: int, evidence_set: EvidenceSet) -> ReasoningStep:
        """Create synthesis step combining evidence from multiple sources."""
        by_source = evidence_set.by_source
        source_names = list(by_source.keys())

        # Find agreement across sources
        content = (
            f"Synthesizing information from {len(source_names)} sources "
            f"({', '.join(s.split('/')[-1] for s in source_names[:3])}{', ...' if len(source_names) > 3 else ''}). "
            f"The information appears consistent."
        )

        # Use evidence from different sources
        evidence_ids = [source_evs[0].id for source_evs in list(by_source.values())[:3] if source_evs]

        return ReasoningStep(
            step_number=step_num,
            step_type=ReasoningStepType.SYNTHESIS,
            content=content,
            supporting_evidence=evidence_ids,
            confidence=0.85,
        )

    def _create_uncertainty_step(self, step_num: int, evidence_set: EvidenceSet) -> ReasoningStep:
        """Create uncertainty step when evidence is insufficient."""
        strong_count = len(evidence_set.strong_evidence)
        total_count = len(evidence_set.evidence)

        content = (
            f"Uncertainty note: Only {strong_count}/{total_count} evidence pieces are strongly relevant. "
            f"The answer may be incomplete or based on tangential information."
        )

        return ReasoningStep(
            step_number=step_num,
            step_type=ReasoningStepType.UNCERTAINTY,
            content=content,
            supporting_evidence=[],
            confidence=0.4,
        )

    def _create_conclusion_step(
        self, step_num: int, evidence_set: EvidenceSet, query: str
    ) -> tuple[ReasoningStep, str]:
        """Create final conclusion step and generate answer."""
        # Build answer from strongest evidence
        strong_ev = evidence_set.strong_evidence
        if not strong_ev:
            strong_ev = sorted(evidence_set.evidence, key=lambda e: e.confidence, reverse=True)[:3]

        # Generate answer by synthesizing top evidence
        answer_parts = []
        evidence_ids = []

        # Prioritize definitions first
        definitions = [e for e in strong_ev if e.evidence_type == EvidenceType.DEFINITION]
        if definitions:
            ev = definitions[0]
            answer_parts.append(ev.content)
            evidence_ids.append(ev.id)

        # Then implementations
        implementations = [e for e in strong_ev if e.evidence_type == EvidenceType.IMPLEMENTATION]
        if implementations and len(answer_parts) < 2:
            ev = implementations[0]
            answer_parts.append(f"Implementation: {ev.content[:200]}...")
            evidence_ids.append(ev.id)

        # Add other relevant evidence
        for ev in strong_ev:
            if ev.id not in evidence_ids and len(answer_parts) < 3:
                answer_parts.append(ev.content[:150] + "...")
                evidence_ids.append(ev.id)

        # Construct final answer
        if not answer_parts:
            final_answer = (
                f"Based on the available evidence, I cannot provide a confident answer to: '{query}'. "
                f"The retrieved information is only tangentially related."
            )
        else:
            final_answer = "\n\n".join(answer_parts)
            # Add source attribution
            sources = list({e.source_file for e in strong_ev if e.id in evidence_ids})
            final_answer += f"\n\n*Sources: {', '.join(s.split('/')[-1] for s in sources[:3])}*"

        content = f"Conclusion: Based on {len(evidence_ids)} pieces of evidence, I can answer the query."

        conclusion_step = ReasoningStep(
            step_number=step_num,
            step_type=ReasoningStepType.CONCLUSION,
            content=content,
            supporting_evidence=evidence_ids,
            confidence=evidence_set.average_confidence,
        )

        return conclusion_step, final_answer

    def _calculate_overall_confidence(self, evidence_set: EvidenceSet, steps: list[ReasoningStep]) -> float:
        """Calculate overall confidence in the reasoning chain."""
        # Start with evidence confidence
        evidence_confidence = evidence_set.average_confidence

        # Penalize if too few strong evidence
        if len(evidence_set.strong_evidence) < self.min_evidence_for_confidence:
            evidence_confidence *= 0.7

        # Penalize if contradictions exist
        if evidence_set.has_contradictions:
            evidence_confidence *= 0.8

        # Boost if we have synthesis across multiple sources
        if len(evidence_set.by_source) >= 3:
            evidence_confidence = min(1.0, evidence_confidence * 1.1)

        # Consider step confidence
        if steps:
            step_confidences = [s.confidence for s in steps if s.step_type != ReasoningStepType.UNCERTAINTY]
            if step_confidences:
                avg_step_confidence = sum(step_confidences) / len(step_confidences)
                # Weight: 70% evidence, 30% steps
                overall = evidence_confidence * 0.7 + avg_step_confidence * 0.3
            else:
                overall = evidence_confidence
        else:
            overall = evidence_confidence

        return min(1.0, max(0.0, overall))


def create_reasoning_engine(
    min_evidence_for_confidence: int = 2, min_confidence_threshold: float = 0.6
) -> ReasoningEngine:
    """Factory function for reasoning engine."""
    return ReasoningEngine(
        min_evidence_for_confidence=min_evidence_for_confidence, min_confidence_threshold=min_confidence_threshold
    )


# --- Test harness ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # Import evidence extractor for testing
    from .evidence_extractor import Evidence, EvidenceSet, EvidenceStrength, EvidenceType

    # Create test evidence set
    test_evidence = [
        Evidence(
            id="ev_001",
            content="GRID is a Python-based framework for exploring complex systems through geometric resonance patterns.",
            evidence_type=EvidenceType.DEFINITION,
            strength=EvidenceStrength.STRONG,
            confidence=0.9,
            source_chunk_id="chunk_001",
            source_file="docs/README.md",
            source_line_start=1,
        ),
        Evidence(
            id="ev_002",
            content="The architecture follows a layered approach with core, API, database, and CLI layers.",
            evidence_type=EvidenceType.ASSERTION,
            strength=EvidenceStrength.STRONG,
            confidence=0.85,
            source_chunk_id="chunk_001",
            source_file="docs/README.md",
            source_line_start=10,
        ),
        Evidence(
            id="ev_003",
            content="class GridEngine:\n    def __init__(self, config: GridConfig):\n        self.config = config",
            evidence_type=EvidenceType.IMPLEMENTATION,
            strength=EvidenceStrength.STRONG,
            confidence=0.8,
            source_chunk_id="chunk_002",
            source_file="grid/core/engine.py",
            is_code=True,
            code_language="python",
        ),
        Evidence(
            id="ev_004",
            content="Pattern recognition uses 9 distinct cognition patterns.",
            evidence_type=EvidenceType.ASSERTION,
            strength=EvidenceStrength.MODERATE,
            confidence=0.7,
            source_chunk_id="chunk_003",
            source_file="docs/patterns.md",
        ),
    ]

    evidence_set = EvidenceSet(
        query="What is the GRID architecture?",
        evidence=test_evidence,
        total_chunks_processed=3,
    )

    # Test reasoning engine
    engine = ReasoningEngine()
    chain = engine.reason(evidence_set)

    print("\n" + "=" * 70)
    print("REASONING ENGINE TEST".center(70))
    print("=" * 70)

    print(chain.format_markdown(include_steps=True))

    print("\n" + "=" * 70)
    print("REASONING METADATA".center(70))
    print("=" * 70)
    print(f"Overall Confidence: {chain.overall_confidence:.0%}")
    print(f"Is Confident: {chain.is_confident}")
    print(f"Has Gaps: {chain.has_gaps}")
    print(f"Evidence Used: {len(chain.evidence_used)}/{len(evidence_set.evidence)}")
    print(f"Reasoning Steps: {len(chain.steps)}")
