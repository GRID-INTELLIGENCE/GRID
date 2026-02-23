"""
Response Synthesizer for Intelligent RAG.

This module integrates the reasoning chain with LLM generation to produce
final, polished responses that maintain transparency and source attribution.

Part of Phase 3: Reasoning Layer
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from tools.rag.types import LLMProvider

from .evidence_extractor import Evidence, EvidenceSet
from .reasoning_engine import ReasoningChain, ReasoningStepType

logger = logging.getLogger(__name__)


@dataclass
class SynthesizedResponse:
    """Complete response with reasoning transparency."""

    query: str
    answer: str  # Final polished answer
    reasoning_chain: ReasoningChain
    evidence_set: EvidenceSet
    confidence: float

    # Source attribution
    sources: list[dict[str, Any]] = field(default_factory=list)
    citations: list[str] = field(default_factory=list)

    # Metadata
    show_reasoning: bool = False
    generation_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        result = {
            "query": self.query,
            "answer": self.answer,
            "confidence": self.confidence,
            "sources": self.sources,
            "citations": self.citations,
        }

        if self.show_reasoning:
            result["reasoning"] = self.reasoning_chain.to_dict()
            result["evidence"] = {
                "total": len(self.evidence_set.evidence),
                "strong": len(self.evidence_set.strong_evidence),
                "by_type": {k.value: len(v) for k, v in self.evidence_set.by_type.items()},
            }

        return result

    def format_markdown(self, include_reasoning: bool = False, include_citations: bool = True) -> str:
        """Format response as markdown."""
        lines = []

        # Main answer
        lines.append(f"**Query:** {self.query}\n")
        lines.append(f"{self.answer}\n")

        # Confidence indicator
        confidence_emoji = "🟢" if self.confidence >= 0.7 else "🟡" if self.confidence >= 0.5 else "🔴"
        lines.append(f"\n{confidence_emoji} **Confidence:** {self.confidence:.0%}")

        # Citations
        if include_citations and self.citations:
            lines.append("\n### 📚 Sources")
            lines.extend(f"- {citation}" for citation in self.citations)

        # Reasoning transparency
        if include_reasoning:
            lines.append("\n---\n")
            lines.append(self.reasoning_chain.format_markdown(include_steps=True))

        return "\n".join(lines)


class ResponseSynthesizer:
    """
    Synthesizes final responses by combining evidence, reasoning, and LLM generation.

    This is the final stage of Phase 3 - it takes the structured reasoning chain
    and produces a user-friendly response while maintaining full transparency.
    """

    def __init__(
        self,
        llm_provider: LLMProvider | None = None,
        use_llm_polish: bool = True,
        max_prompt_tokens: int = 4000,
    ):
        """
        Initialize the response synthesizer.

        Args:
            llm_provider: Optional LLM for polishing responses
            use_llm_polish: Whether to use LLM for final polish (vs template-based)
            max_prompt_tokens: Maximum prompt size for LLM (rough estimate)
        """
        self.llm_provider = llm_provider
        self.use_llm_polish = use_llm_polish
        self.max_prompt_tokens = max_prompt_tokens
        logger.info(f"ResponseSynthesizer initialized (LLM polish: {use_llm_polish})")

    async def synthesize(
        self,
        reasoning_chain: ReasoningChain,
        evidence_set: EvidenceSet,
        temperature: float = 0.3,
        show_reasoning: bool = False,
    ) -> SynthesizedResponse:
        """
        Synthesize final response from reasoning chain and evidence.

        Args:
            reasoning_chain: The completed reasoning chain
            evidence_set: The evidence used in reasoning
            temperature: LLM temperature for generation
            show_reasoning: Whether to include reasoning in response

        Returns:
            SynthesizedResponse with polished answer
        """
        query = reasoning_chain.query

        logger.info(f"Synthesizing response for: '{query[:50]}...'")

        # Collect evidence citations
        evidence_map = {e.id: e for e in evidence_set.evidence}
        used_evidence = [evidence_map[eid] for eid in reasoning_chain.evidence_used if eid in evidence_map]

        # Generate citations and sources
        citations, sources = self._generate_citations(used_evidence)

        # Decide whether to use LLM polish or template-based
        if self.use_llm_polish and self.llm_provider:
            answer = await self._llm_synthesize(
                reasoning_chain=reasoning_chain,
                evidence=used_evidence,
                temperature=temperature,
            )
        else:
            answer = self._template_synthesize(reasoning_chain=reasoning_chain, evidence=used_evidence)

        # Add confidence caveat if needed
        if reasoning_chain.warnings:
            answer += "\n\n**Note:** " + reasoning_chain.warnings[0]

        response = SynthesizedResponse(
            query=query,
            answer=answer,
            reasoning_chain=reasoning_chain,
            evidence_set=evidence_set,
            confidence=reasoning_chain.overall_confidence,
            sources=sources,
            citations=citations,
            show_reasoning=show_reasoning,
            generation_metadata={
                "method": "llm" if (self.use_llm_polish and self.llm_provider) else "template",
                "evidence_count": len(used_evidence),
                "temperature": temperature,
            },
        )

        logger.info(
            f"Response synthesized: {len(answer)} chars, "
            f"{len(citations)} citations, confidence={response.confidence:.2%}"
        )

        return response

    def _generate_citations(self, evidence: list[Evidence]) -> tuple[list[str], list[dict[str, Any]]]:
        """Generate citation strings and source metadata."""
        citations = []
        sources = []
        seen_files = set()

        for ev in evidence:
            # Generate citation
            citation = ev.citation()
            if citation not in citations:
                citations.append(citation)

            # Generate source metadata (deduplicate by file)
            if ev.source_file not in seen_files:
                seen_files.add(ev.source_file)
                source_info = {
                    "file": ev.source_file,
                    "type": ev.evidence_type.value,
                    "confidence": ev.confidence,
                }
                if ev.source_line_start:
                    source_info["lines"] = f"{ev.source_line_start}-{ev.source_line_end or ev.source_line_start}"
                sources.append(source_info)

        return citations, sources

    async def _llm_synthesize(
        self,
        reasoning_chain: ReasoningChain,
        evidence: list[Evidence],
        temperature: float,
    ) -> str:
        """Use LLM to synthesize a polished response."""
        # Build prompt with reasoning context
        prompt = self._build_synthesis_prompt(reasoning_chain, evidence)

        # Generate response
        try:
            if hasattr(self.llm_provider, "async_generate"):
                response = await self.llm_provider.async_generate(prompt, temperature=temperature)
            else:
                response = self.llm_provider.generate(prompt)

            # Clean up response
            response = response.strip()

            # Remove common LLM artifacts
            if response.startswith("Answer:"):
                response = response[7:].strip()

            return response

        except Exception as e:
            logger.error(f"LLM synthesis failed: {e}. Falling back to template.")
            return self._template_synthesize(reasoning_chain, evidence)

    def _template_synthesize(self, reasoning_chain: ReasoningChain, evidence: list[Evidence]) -> str:
        """Template-based synthesis (no LLM required)."""
        # Use the conclusion from reasoning chain as base
        answer_parts = []

        # Add main conclusion
        conclusion_steps = [s for s in reasoning_chain.steps if s.step_type == ReasoningStepType.CONCLUSION]
        if conclusion_steps:
            # Extract evidence content for conclusion
            conclusion_evidence_ids = conclusion_steps[0].supporting_evidence
            evidence_map = {e.id: e for e in evidence}

            for eid in conclusion_evidence_ids:
                if eid in evidence_map:
                    ev = evidence_map[eid]
                    answer_parts.append(ev.content)

        if not answer_parts:
            # Fallback: use strongest evidence
            strong = sorted(evidence, key=lambda e: e.confidence, reverse=True)[:2]
            answer_parts = [e.content for e in strong]

        # Combine with proper formatting
        answer = "\n\n".join(answer_parts)

        # Add synthesis note
        if len(evidence) > 1:
            sources_list = list({e.source_file.split("/")[-1] for e in evidence})
            answer += f"\n\n*Synthesized from {len(sources_list)} source(s): {', '.join(sources_list[:3])}*"

        return answer

    def _build_synthesis_prompt(self, reasoning_chain: ReasoningChain, evidence: list[Evidence]) -> str:
        """Build prompt for LLM synthesis."""
        # Estimate token budget (rough: 4 chars = 1 token)
        max_chars = self.max_prompt_tokens * 4

        prompt_parts = []

        # System instruction
        prompt_parts.append(
            "You are a precise assistant that answers questions based on provided evidence. "
            "Your answer must be grounded in the evidence below. Do not speculate or add information "
            "not present in the evidence. Be clear, concise, and accurate.\n"
        )

        # Add query
        prompt_parts.append(f"**Question:** {reasoning_chain.query}\n")

        # Add reasoning steps (compressed)
        prompt_parts.append("**Reasoning Process:**")
        prompt_parts.extend(
            f"{step.step_number}. {step.content}"
            for step in reasoning_chain.steps
            if step.step_type != ReasoningStepType.UNCERTAINTY
        )
        prompt_parts.append("")

        # Add evidence
        prompt_parts.append("**Evidence:**")
        current_length = sum(len(p) for p in prompt_parts)

        # Add evidence until we hit budget
        for i, ev in enumerate(evidence, 1):
            ev_text = f"\n[{i}] Source: {ev.source_file}\n{ev.content}\n"

            if current_length + len(ev_text) > max_chars:
                prompt_parts.append(f"\n... ({len(evidence) - i + 1} more sources omitted)")
                break

            prompt_parts.append(ev_text)
            current_length += len(ev_text)

        # Final instruction
        prompt_parts.append(
            "\n**Instructions:**\n"
            "Based on the reasoning and evidence above, provide a clear, accurate answer. "
            "Cite sources using [Source: filename] notation. "
            "If the evidence is incomplete, acknowledge this.\n"
            "\n**Answer:**"
        )

        return "\n".join(prompt_parts)


def create_response_synthesizer(
    llm_provider: LLMProvider | None = None,
    use_llm_polish: bool = True,
    max_prompt_tokens: int = 4000,
) -> ResponseSynthesizer:
    """Factory function for response synthesizer."""
    return ResponseSynthesizer(
        llm_provider=llm_provider,
        use_llm_polish=use_llm_polish,
        max_prompt_tokens=max_prompt_tokens,
    )


# --- Test harness ---
if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # Import dependencies for testing
    from .evidence_extractor import Evidence, EvidenceSet, EvidenceStrength, EvidenceType
    from .reasoning_engine import ReasoningChain, ReasoningStep, ReasoningStepType

    # Create test data
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
            content="The architecture follows a layered approach: core, API, database, CLI, and services.",
            evidence_type=EvidenceType.ASSERTION,
            strength=EvidenceStrength.STRONG,
            confidence=0.85,
            source_chunk_id="chunk_001",
            source_file="docs/ARCHITECTURE.md",
            source_line_start=10,
        ),
    ]

    evidence_set = EvidenceSet(
        query="What is the GRID architecture?",
        evidence=test_evidence,
        total_chunks_processed=2,
    )

    reasoning_chain = ReasoningChain(
        query="What is the GRID architecture?",
        steps=[
            ReasoningStep(
                step_number=1,
                step_type=ReasoningStepType.OBSERVATION,
                content="I found 2 highly relevant evidence pieces from 2 source files.",
                supporting_evidence=["ev_001", "ev_002"],
                confidence=0.9,
            ),
            ReasoningStep(
                step_number=2,
                step_type=ReasoningStepType.INFERENCE,
                content="Based on the definition in docs/README.md, I can establish the core concept.",
                supporting_evidence=["ev_001"],
                confidence=0.9,
            ),
            ReasoningStep(
                step_number=3,
                step_type=ReasoningStepType.CONCLUSION,
                content="Conclusion: Based on 2 pieces of evidence, I can answer the query.",
                supporting_evidence=["ev_001", "ev_002"],
                confidence=0.875,
            ),
        ],
        final_answer="GRID is a Python-based framework for exploring complex systems. Architecture follows a layered approach.",
        overall_confidence=0.875,
        evidence_used=["ev_001", "ev_002"],
        evidence_unused=[],
    )

    async def test():
        # Test without LLM (template-based)
        synthesizer = ResponseSynthesizer(llm_provider=None, use_llm_polish=False)

        response = await synthesizer.synthesize(
            reasoning_chain=reasoning_chain,
            evidence_set=evidence_set,
            show_reasoning=True,
        )

        print("\n" + "=" * 70)
        print("RESPONSE SYNTHESIZER TEST".center(70))
        print("=" * 70)

        print(response.format_markdown(include_reasoning=True, include_citations=True))

        print("\n" + "=" * 70)
        print("RESPONSE METADATA".center(70))
        print("=" * 70)
        print(f"Answer Length: {len(response.answer)} chars")
        print(f"Citations: {len(response.citations)}")
        print(f"Sources: {len(response.sources)}")
        print(f"Confidence: {response.confidence:.0%}")
        print(f"Method: {response.generation_metadata['method']}")

    asyncio.run(test())
