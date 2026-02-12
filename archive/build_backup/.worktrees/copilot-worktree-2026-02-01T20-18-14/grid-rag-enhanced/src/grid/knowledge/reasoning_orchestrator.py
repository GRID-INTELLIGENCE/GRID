"""
GRID Reasoning Orchestrator - Kanye's Wild Experiments 🌊

Pairs web searches with knowledge graph queries and LLM inference.
Pattern: web search → KG query → LLM call (alternating)

Kanye says: "Why choose one when you can run them all in parallel?"
Jay says: "That's... actually brilliant."
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from grid.services.llm.llm_client import LLMClient, LLMConfig, OllamaNativeClient

logger = logging.getLogger(__name__)


class ReasoningMode(str, Enum):
    """Kanye's reasoning modes."""

    SEQUENTIAL = "sequential"  # Jay's preferred: one after another
    PARALLEL = "parallel"  # Kanye's wild idea: all at once
    ADAPTIVE = "adaptive"  # Dynamic: switch based on results


@dataclass
class ReasoningStep:
    """A step in the reasoning chain."""

    step_type: str  # web_search, kg_query, llm_call
    query: str
    result: Any = None
    duration_ms: int = 0
    timestamp: datetime | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}


class ReasoningOrchestrator:
    """
    Orchestrates multi-source reasoning:
    - Web searches (for external knowledge)
    - KG queries (for structural knowledge)
    - LLM calls (for dynamic reasoning)

    Kanye's contribution: Run them in parallel when possible!
    """

    def __init__(
        self,
        mode: ReasoningMode = ReasoningMode.ADAPTIVE,
        enable_web: bool = True,
        enable_kg: bool = True,
        enable_llm: bool = True,
        llm_model: str = "mistral-nemo:latest",
        llm_client: LLMClient | None = None,
    ):
        """Initialize reasoning orchestrator.

        Args:
            mode: Reasoning mode (sequential, parallel, adaptive)
            enable_web: Enable web searches
            enable_kg: Enable KG queries
            enable_llm: Enable LLM calls
            llm_model: Ollama model for LLM reasoning
            llm_client: Optional native LLM client
        """
        self.mode = mode
        self.enable_web = enable_web
        self.enable_kg = enable_kg
        self.enable_llm = enable_llm
        self.llm_model = llm_model
        self.llm_client = llm_client or OllamaNativeClient()
        self.reasoning_chain: list[ReasoningStep] = []

    async def reason(
        self,
        query: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute multi-source reasoning on a query.

        Args:
            query: Question or task to reason about
            context: Optional context for reasoning

        Returns:
            Reasoning results with steps and synthesis
        """
        logger.info(f"🧠 Reasoning: {query} (mode={self.mode.value})")

        # Kanye's parallel approach
        if self.mode == ReasoningMode.PARALLEL:
            results = await self._reason_parallel(query, context)
        # Jay's sequential approach
        else:
            results = await self._reason_sequential(query, context)

        # Synthesize results
        synthesis = self._synthesize_results(results)

        return {
            "query": query,
            "mode": self.mode.value,
            "steps": [self._step_to_dict(step) for step in results],
            "synthesis": synthesis,
            "total_steps": len(results),
        }

    async def _reason_sequential(
        self,
        query: str,
        context: dict[str, Any] | None,
    ) -> list[ReasoningStep]:
        """Jay's methodical sequential reasoning."""
        steps = []

        # Step 1: Web search (if enabled)
        if self.enable_web:
            web_result = await self._web_search(query)
            steps.append(web_result)

        # Step 2: KG query (if enabled)
        if self.enable_kg:
            kg_result = await self._kg_query(query, context)
            steps.append(kg_result)

        # Step 3: LLM inference (if enabled)
        if self.enable_llm:
            # Provide previous results as context
            llm_context = {
                "web_result": steps[0].result if steps else None,
                "kg_result": steps[1].result if len(steps) > 1 else None,
            }
            llm_result = await self._llm_call(query, llm_context)
            steps.append(llm_result)

        self.reasoning_chain.extend(steps)
        return steps

    async def _reason_parallel(
        self,
        query: str,
        context: dict[str, Any] | None,
    ) -> list[ReasoningStep]:
        """Kanye's wild parallel reasoning - run everything at once!"""
        tasks = []

        if self.enable_web:
            tasks.append(self._web_search(query))

        if self.enable_kg:
            tasks.append(self._kg_query(query, context))

        if self.enable_llm:
            tasks.append(self._llm_call(query, context))

        # Run all in parallel (Kanye: "MAXIMUM SPEED!")
        steps = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_steps = [s for s in steps if isinstance(s, ReasoningStep)]

        self.reasoning_chain.extend(valid_steps)
        return valid_steps

    async def _web_search(self, query: str) -> ReasoningStep:
        """Perform web search (placeholder - would use real search API)."""
        start = datetime.now()

        # Simulated web search (in real impl, use search_web tool)
        result = {
            "query": query,
            "snippets": ["Web search result placeholder"],
            "sources": [],
        }

        duration = int((datetime.now() - start).total_seconds() * 1000)

        return ReasoningStep(
            step_type="web_search",
            query=query,
            result=result,
            duration_ms=duration,
        )

    async def _kg_query(
        self,
        query: str,
        context: dict[str, Any] | None,
    ) -> ReasoningStep:
        """Query knowledge graph (placeholder - would use real KG)."""
        start = datetime.now()

        # Simulated KG query (in real impl, use graph database)
        # Example: Find related entities
        result = {
            "query": query,
            "entities": [],
            "relationships": [],
            "traversal_depth": 2,
        }

        duration = int((datetime.now() - start).total_seconds() * 1000)

        return ReasoningStep(
            step_type="kg_query",
            query=query,
            result=result,
            duration_ms=duration,
            metadata={"context": context},
        )

    async def _llm_call(
        self,
        query: str,
        context: dict[str, Any] | None,
    ) -> ReasoningStep:
        """Call local LLM via native client."""
        start = datetime.now()

        # Build context-aware prompt
        prompt = self._build_llm_prompt(query, context)

        try:
            # Call Ollama via native client
            response = await self.llm_client.generate(prompt=prompt, config=LLMConfig(model=self.llm_model))

            result = {
                "query": query,
                "response": response.content,
                "model": response.model,
                "tokens_used": response.tokens_used,
                "error": None,
            }

        except Exception as e:
            result = {
                "query": query,
                "response": None,
                "model": self.llm_model,
                "error": str(e),
            }

        duration = int((datetime.now() - start).total_seconds() * 1000)

        return ReasoningStep(
            step_type="llm_call",
            query=query,
            result=result,
            duration_ms=duration,
            metadata={"model": self.llm_model},
        )

    def _build_llm_prompt(self, query: str, context: dict[str, Any] | None) -> str:
        """Build context-aware LLM prompt."""
        prompt_parts = []

        if context:
            if "web_result" in context and context["web_result"]:
                prompt_parts.append("Web search results:")
                prompt_parts.append(json.dumps(context["web_result"], indent=2))

            if "kg_result" in context and context["kg_result"]:
                prompt_parts.append("Knowledge graph context:")
                prompt_parts.append(json.dumps(context["kg_result"], indent=2))

        prompt_parts.append(f"Query: {query}")
        prompt_parts.append("Provide a concise, insightful response in 100 words or less.")

        return "\n\n".join(prompt_parts)

    def _synthesize_results(self, steps: list[ReasoningStep]) -> str:
        """Synthesize results from all reasoning steps."""
        if not steps:
            return "No reasoning steps executed."

        synthesis_parts = []

        for step in steps:
            if step.step_type == "web_search":
                synthesis_parts.append("🌐 Web: External knowledge gathered")
            elif step.step_type == "kg_query":
                synthesis_parts.append("📊 KG: Structural relationships mapped")
            elif step.step_type == "llm_call":
                if step.result and step.result.get("response"):
                    synthesis_parts.append(f"🤖 LLM: {step.result['response'][:200]}")

        return " | ".join(synthesis_parts)

    def _step_to_dict(self, step: ReasoningStep) -> dict[str, Any]:
        """Convert step to dictionary."""
        return {
            "type": step.step_type,
            "query": step.query,
            "result": step.result,
            "duration_ms": step.duration_ms,
            "timestamp": step.timestamp.isoformat() if step.timestamp else None,
            "metadata": step.metadata,
        }

    def get_reasoning_chain(self) -> list[dict[str, Any]]:
        """Get the full reasoning chain."""
        return [self._step_to_dict(step) for step in self.reasoning_chain]


# Kanye's quick experiment function
async def quick_reason(
    query: str,
    use_parallel: bool = True,
    llm_model: str = "mistral-nemo:latest",
) -> dict[str, Any]:
    """Kanye's quick reasoning experiment.

    Args:
        query: Question to reason about
        use_parallel: Use parallel mode (Kanye's way)
        llm_model: LLM model to use

    Returns:
        Reasoning results
    """
    mode = ReasoningMode.PARALLEL if use_parallel else ReasoningMode.SEQUENTIAL
    orchestrator = ReasoningOrchestrator(mode=mode, llm_model=llm_model)
    return await orchestrator.reason(query)


__all__ = [
    "ReasoningMode",
    "ReasoningStep",
    "ReasoningOrchestrator",
    "quick_reason",
]
