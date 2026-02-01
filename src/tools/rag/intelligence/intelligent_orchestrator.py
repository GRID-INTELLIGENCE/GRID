"""
Intelligent RAG Orchestrator - Phase 3 Complete Integration.

This module orchestrates the complete intelligent RAG pipeline:
1. Query Understanding (Intent + Entities)
2. Multi-Stage Retrieval (Hybrid + Multi-Hop + Reranking)
3. Evidence Extraction (Structured facts with provenance)
4. Chain-of-Thought Reasoning (Transparent reasoning steps)
5. Response Synthesis (Polished answer with citations)

This is the top-level coordinator for the intelligent RAG system.
"""

import logging
import time
from dataclasses import dataclass
from typing import Any

from tools.rag.types import LLMProvider

from .evidence_extractor import create_evidence_extractor
from .query_understanding import QueryUnderstandingLayer, UnderstoodQuery
from .reasoning_engine import create_reasoning_engine
from .response_synthesizer import create_response_synthesizer
from .retrieval_orchestrator import RetrievalOrchestrator

logger = logging.getLogger(__name__)


@dataclass
class IntelligentRAGMetrics:
    """Metrics for the complete intelligent RAG pipeline."""

    # Timing metrics
    query_understanding_time: float = 0.0
    retrieval_time: float = 0.0
    evidence_extraction_time: float = 0.0
    reasoning_time: float = 0.0
    synthesis_time: float = 0.0
    total_time: float = 0.0

    # Component metrics
    intent: str = ""
    intent_confidence: float = 0.0
    entities_found: int = 0
    chunks_retrieved: int = 0
    evidence_extracted: int = 0
    strong_evidence_count: int = 0
    reasoning_steps: int = 0
    final_confidence: float = 0.0

    # Quality indicators
    has_contradictions: bool = False
    has_knowledge_gaps: bool = False
    evidence_coverage: float = 0.0  # % of evidence used in reasoning

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "timing": {
                "understanding": f"{self.query_understanding_time:.3f}s",
                "retrieval": f"{self.retrieval_time:.3f}s",
                "extraction": f"{self.evidence_extraction_time:.3f}s",
                "reasoning": f"{self.reasoning_time:.3f}s",
                "synthesis": f"{self.synthesis_time:.3f}s",
                "total": f"{self.total_time:.3f}s",
            },
            "pipeline": {
                "intent": self.intent,
                "intent_confidence": f"{self.intent_confidence:.0%}",
                "entities": self.entities_found,
                "chunks_retrieved": self.chunks_retrieved,
                "evidence_extracted": self.evidence_extracted,
                "strong_evidence": self.strong_evidence_count,
                "reasoning_steps": self.reasoning_steps,
                "final_confidence": f"{self.final_confidence:.0%}",
            },
            "quality": {
                "contradictions": self.has_contradictions,
                "knowledge_gaps": self.has_knowledge_gaps,
                "evidence_coverage": f"{self.evidence_coverage:.0%}",
            },
        }


class IntelligentRAGOrchestrator:
    """
    Orchestrates the complete intelligent RAG pipeline.

    This replaces the simple "embed -> retrieve -> generate" pattern with
    a sophisticated multi-stage pipeline that produces transparent, reasoned,
    and well-cited responses.
    """

    def __init__(
        self,
        retrieval_orchestrator: RetrievalOrchestrator,
        llm_provider: LLMProvider | None = None,
        use_query_understanding: bool = True,
        use_evidence_extraction: bool = True,
        use_reasoning: bool = True,
        use_llm_synthesis: bool = True,
    ):
        """
        Initialize the intelligent RAG orchestrator.

        Args:
            retrieval_orchestrator: The multi-stage retrieval orchestrator
            llm_provider: Optional LLM for response synthesis
            use_query_understanding: Enable query understanding layer
            use_evidence_extraction: Enable evidence extraction
            use_reasoning: Enable chain-of-thought reasoning
            use_llm_synthesis: Enable LLM-based response synthesis
        """
        self.retrieval_orchestrator = retrieval_orchestrator
        self.llm_provider = llm_provider

        # Feature flags
        self.use_query_understanding = use_query_understanding
        self.use_evidence_extraction = use_evidence_extraction
        self.use_reasoning = use_reasoning
        self.use_llm_synthesis = use_llm_synthesis

        # Initialize components
        if self.use_query_understanding:
            self.query_understanding = QueryUnderstandingLayer(use_gpu=False)  # Local CPU models
        else:
            self.query_understanding = None

        if self.use_evidence_extraction:
            self.evidence_extractor = create_evidence_extractor()
        else:
            self.evidence_extractor = None

        if self.use_reasoning:
            self.reasoning_engine = create_reasoning_engine()
        else:
            self.reasoning_engine = None

        self.response_synthesizer = create_response_synthesizer(
            llm_provider=llm_provider if self.use_llm_synthesis else None,
            use_llm_polish=self.use_llm_synthesis,
        )

        logger.info(
            f"IntelligentRAGOrchestrator initialized with features: "
            f"understanding={use_query_understanding}, extraction={use_evidence_extraction}, "
            f"reasoning={use_reasoning}, llm_synthesis={use_llm_synthesis}"
        )

    async def query(
        self,
        query_text: str,
        top_k: int = 5,
        temperature: float = 0.3,
        include_reasoning: bool = False,
        include_metrics: bool = False,
    ) -> dict[str, Any]:
        """
        Execute the complete intelligent RAG pipeline.

        Args:
            query_text: The user's query
            top_k: Number of chunks to retrieve
            temperature: LLM temperature for synthesis
            include_reasoning: Whether to include reasoning chain in response
            include_metrics: Whether to include pipeline metrics

        Returns:
            Dictionary with answer, sources, citations, and optional reasoning/metrics
        """
        start_time = time.time()
        metrics = IntelligentRAGMetrics()

        logger.info(f"Starting intelligent RAG query: '{query_text[:60]}...'")

        # --- Stage 1: Query Understanding ---
        understood_query = None
        if self.use_query_understanding and self.query_understanding:
            stage_start = time.time()
            understood_query = self.query_understanding.understand(query_text)
            metrics.query_understanding_time = time.time() - stage_start
            metrics.intent = understood_query.intent.value
            metrics.intent_confidence = understood_query.intent_confidence
            metrics.entities_found = len(understood_query.entities)

            logger.info(
                f"Query understood: intent={understood_query.intent.value} "
                f"(confidence={understood_query.intent_confidence:.0%}), "
                f"entities={len(understood_query.entities)}"
            )
        else:
            # Fallback: create minimal understood query
            from .intent_classifier import Intent

            understood_query = UnderstoodQuery(
                original_query=query_text,
                intent=Intent.OTHER,
                intent_confidence=1.0,
                entities=[],
                search_terms=[],
                expanded_queries=[query_text],
            )

        # --- Stage 2: Multi-Stage Retrieval ---
        stage_start = time.time()
        retrieval_results = await self.retrieval_orchestrator.retrieve(understood_query, top_k=top_k)
        metrics.retrieval_time = time.time() - stage_start
        metrics.chunks_retrieved = len(retrieval_results.get("documents", []))

        if not retrieval_results.get("documents"):
            logger.warning("No documents retrieved. Returning empty result.")
            return {
                "query": query_text,
                "answer": "I couldn't find any relevant information in the knowledge base to answer this question.",
                "confidence": 0.0,
                "sources": [],
                "citations": [],
                "metrics": metrics.to_dict() if include_metrics else None,
            }

        logger.info(
            f"Retrieved {metrics.chunks_retrieved} chunks (reranked: {retrieval_results.get('reranked', False)})"
        )

        # --- Stage 3: Evidence Extraction ---
        evidence_set = None
        if self.use_evidence_extraction and self.evidence_extractor:
            stage_start = time.time()
            evidence_set = self.evidence_extractor.extract(
                query=query_text,
                documents=retrieval_results["documents"],
                metadatas=retrieval_results["metadatas"],
                ids=retrieval_results["ids"],
                distances=retrieval_results.get("distances"),
            )
            metrics.evidence_extraction_time = time.time() - stage_start
            metrics.evidence_extracted = len(evidence_set.evidence)
            metrics.strong_evidence_count = len(evidence_set.strong_evidence)
            metrics.has_contradictions = evidence_set.has_contradictions

            logger.info(
                f"Extracted {metrics.evidence_extracted} evidence pieces "
                f"({metrics.strong_evidence_count} strong, avg_conf={evidence_set.average_confidence:.0%})"
            )
        else:
            # Fallback: create minimal evidence set
            from .evidence_extractor import Evidence, EvidenceSet, EvidenceStrength, EvidenceType

            evidence_list = []
            for i, (doc, meta, chunk_id) in enumerate(
                zip(
                    retrieval_results["documents"],
                    retrieval_results["metadatas"],
                    retrieval_results["ids"],
                    strict=False,
                )
            ):
                evidence_list.append(
                    Evidence(
                        id=f"ev_{i}",
                        content=doc,
                        evidence_type=EvidenceType.ASSERTION,
                        strength=EvidenceStrength.MODERATE,
                        confidence=0.7,
                        source_chunk_id=chunk_id,
                        source_file=meta.get("source", "unknown"),
                    )
                )

            evidence_set = EvidenceSet(
                query=query_text,
                evidence=evidence_list,
                total_chunks_processed=len(evidence_list),
            )
            metrics.evidence_extracted = len(evidence_list)

        # --- Stage 4: Chain-of-Thought Reasoning ---
        reasoning_chain = None
        if self.use_reasoning and self.reasoning_engine:
            stage_start = time.time()
            reasoning_chain = self.reasoning_engine.reason(evidence_set)
            metrics.reasoning_time = time.time() - stage_start
            metrics.reasoning_steps = len(reasoning_chain.steps)
            metrics.has_knowledge_gaps = reasoning_chain.has_gaps
            metrics.final_confidence = reasoning_chain.overall_confidence

            if reasoning_chain.evidence_used:
                metrics.evidence_coverage = len(reasoning_chain.evidence_used) / len(evidence_set.evidence)

            logger.info(
                f"Reasoning complete: {metrics.reasoning_steps} steps, "
                f"confidence={reasoning_chain.overall_confidence:.0%}, "
                f"gaps={reasoning_chain.has_gaps}"
            )
        else:
            # Fallback: create minimal reasoning chain
            from .reasoning_engine import ReasoningChain, ReasoningStep, ReasoningStepType

            # Simple conclusion step
            conclusion_step = ReasoningStep(
                step_number=1,
                step_type=ReasoningStepType.CONCLUSION,
                content="Based on the retrieved evidence, here is the answer.",
                supporting_evidence=[e.id for e in evidence_set.evidence[:3]],
                confidence=evidence_set.average_confidence,
            )

            # Build simple answer from top evidence
            answer_parts = [e.content for e in evidence_set.evidence[:2]]
            simple_answer = "\n\n".join(answer_parts)

            reasoning_chain = ReasoningChain(
                query=query_text,
                steps=[conclusion_step],
                final_answer=simple_answer,
                overall_confidence=evidence_set.average_confidence,
                evidence_used=[e.id for e in evidence_set.evidence[:3]],
            )
            metrics.reasoning_steps = 1
            metrics.final_confidence = evidence_set.average_confidence

        # --- Stage 5: Response Synthesis ---
        stage_start = time.time()
        synthesized_response = await self.response_synthesizer.synthesize(
            reasoning_chain=reasoning_chain,
            evidence_set=evidence_set,
            temperature=temperature,
            show_reasoning=include_reasoning,
        )
        metrics.synthesis_time = time.time() - stage_start

        # --- Finalize ---
        metrics.total_time = time.time() - start_time

        logger.info(
            f"Intelligent RAG complete: {metrics.total_time:.2f}s total, confidence={metrics.final_confidence:.0%}"
        )

        # Build response
        response = synthesized_response.to_dict()

        if include_metrics:
            response["metrics"] = metrics.to_dict()

        return response

    def query_sync(
        self,
        query_text: str,
        top_k: int = 5,
        temperature: float = 0.3,
        include_reasoning: bool = False,
        include_metrics: bool = False,
    ) -> dict[str, Any]:
        """
        Synchronous wrapper for query method.

        Args:
            query_text: The user's query
            top_k: Number of chunks to retrieve
            temperature: LLM temperature for synthesis
            include_reasoning: Whether to include reasoning chain in response
            include_metrics: Whether to include pipeline metrics

        Returns:
            Dictionary with answer, sources, citations, and optional reasoning/metrics
        """
        import asyncio

        # Check if there's already a running event loop
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop is None:
            # No event loop running, create a new one
            return asyncio.run(
                self.query(
                    query_text=query_text,
                    top_k=top_k,
                    temperature=temperature,
                    include_reasoning=include_reasoning,
                    include_metrics=include_metrics,
                )
            )
        else:
            # Event loop already running, use it
            return loop.run_until_complete(
                self.query(
                    query_text=query_text,
                    top_k=top_k,
                    temperature=temperature,
                    include_reasoning=include_reasoning,
                    include_metrics=include_metrics,
                )
            )

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about the intelligent RAG system."""
        return {
            "features": {
                "query_understanding": self.use_query_understanding,
                "evidence_extraction": self.use_evidence_extraction,
                "reasoning": self.use_reasoning,
                "llm_synthesis": self.use_llm_synthesis,
            },
            "retrieval": {
                "hybrid_enabled": self.retrieval_orchestrator.config.use_hybrid,
                "multi_hop_enabled": self.retrieval_orchestrator.config.multi_hop_enabled,
                "reranking_enabled": self.retrieval_orchestrator.reranker is not None,
            },
        }


def create_intelligent_orchestrator(
    retrieval_orchestrator: RetrievalOrchestrator,
    llm_provider: LLMProvider | None = None,
    enable_all_features: bool = True,
) -> IntelligentRAGOrchestrator:
    """
    Factory function for intelligent RAG orchestrator.

    Args:
        retrieval_orchestrator: The retrieval orchestrator
        llm_provider: Optional LLM provider for synthesis
        enable_all_features: Whether to enable all intelligence features (default: True)

    Returns:
        IntelligentRAGOrchestrator instance
    """
    return IntelligentRAGOrchestrator(
        retrieval_orchestrator=retrieval_orchestrator,
        llm_provider=llm_provider,
        use_query_understanding=enable_all_features,
        use_evidence_extraction=enable_all_features,
        use_reasoning=enable_all_features,
        use_llm_synthesis=enable_all_features and llm_provider is not None,
    )


# --- Test harness ---
if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    print("\n" + "=" * 70)
    print("INTELLIGENT RAG ORCHESTRATOR - INTEGRATION TEST".center(70))
    print("=" * 70)
    print("\nThis test requires a running RAG engine with indexed data.")
    print("Use the RAG CLI to index a repository first:\n")
    print("  python -m tools.rag.cli index <repo_path>\n")
    print("Then modify this test to connect to your RAG engine.")
    print("\n" + "=" * 70)

    # To run a full integration test, you would:
    # 1. Initialize a RAGEngine
    # 2. Create RetrievalOrchestrator from the engine
    # 3. Create IntelligentRAGOrchestrator
    # 4. Execute queries

    # Example pseudo-code:
    """
    from tools.rag.rag_engine import RAGEngine
    from tools.rag.config import RAGConfig

    config = RAGConfig.from_env()
    engine = RAGEngine(config=config)

    # Create retrieval orchestrator
    retrieval_orch = RetrievalOrchestrator(engine=engine)

    # Create intelligent orchestrator
    intelligent_rag = create_intelligent_orchestrator(
        retrieval_orchestrator=retrieval_orch,
        llm_provider=engine.llm_provider,
        enable_all_features=True
    )

    # Query
    result = await intelligent_rag.query(
        query_text="What is the GRID architecture?",
        top_k=5,
        include_reasoning=True,
        include_metrics=True
    )

    print(result)
    """

    print("\nTest skeleton complete. Implement full test with your RAG engine instance.")
