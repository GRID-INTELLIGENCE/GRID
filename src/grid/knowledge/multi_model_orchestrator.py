"""
Multi-Model Reasoning Orchestrator - The Ensemble Workflow 🎭

Discusses with multiple Ollama models simultaneously, gathering insights from
codebase navigation and asking precise questions tailored to each model's
specific architecture and use-case profile.

Pattern:
1. Gather Navigation Insights (Zone, Standing, Hierarchy)
2. Inventory Available Models
3. Tailor Questions for each Model Type
4. Dispatch Parallel Inquiries
5. Synthesize Expert Consensus
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from grid.knowledge.reasoning_orchestrator import ReasoningMode, ReasoningOrchestrator, ReasoningStep

logger = logging.getLogger(__name__)


@dataclass
class ModelProfile:
    """Characterizes an Ollama model's 'standing' and expertise."""

    name: str
    architecture: str
    standings: str  # Reputation/Tier
    use_case: str
    specialty_prompt: str


class MultiModelOrchestrator(ReasoningOrchestrator):
    """
    Advanced orchestrator that leverages multiple local models as an
    expert panel.
    """

    DEFAULT_PROFILES = {
        "mistral-nemo": ModelProfile(
            name="mistral-nemo:latest",
            architecture="Mistral-7B Evolved",
            standings="Primary Generalist (Sovereign Tier)",
            use_case="Logic synthesis and conversational integration",
            specialty_prompt="Synthesize the following technical insights into a cohesive strategy.",
        ),
        "codestral": ModelProfile(
            name="codestral:latest",
            architecture="Mistral-Code-Large",
            standings="Expert Architect (Infrastructure Tier)",
            use_case="Refactoring, implementation details, and API design",
            specialty_prompt="Analyze the implementation risks and suggest optimal refactoring paths.",
        ),
        "llama3": ModelProfile(
            name="llama3.1:8b",
            architecture="Meta-Llama-3-Refined",
            standings="Reasoning Specialist (Cognitive Tier)",
            use_case="Task breakdown, instruction following, and constraints validation",
            specialty_prompt="Break down this requirement into atomic, verifiable implementation steps.",
        ),
        "qwen2.5-coder": ModelProfile(
            name="qwen2.5-coder:latest",
            architecture="Alibaba-Qwen-Coder",
            standings="Implementation Specialist (Tools Tier)",
            use_case="Code generation and precise syntactic analysis",
            specialty_prompt="Provide a direct code implementation or fix for the following scenario.",
        ),
        "deepseek-coder": ModelProfile(
            name="deepseek-coder:latest",
            architecture="DeepSeek-Coder",
            standings="Code Analysis Expert (Infrastructure Tier)",
            use_case="Complex code analysis and optimization",
            specialty_prompt="Analyze the code structure and identify optimization opportunities.",
        ),
        "qwen2.5": ModelProfile(
            name="qwen2.5:latest",
            architecture="Alibaba-Qwen-2.5",
            standings="General Reasoning (Sovereign Tier)",
            use_case="Broad reasoning and problem solving",
            specialty_prompt="Provide comprehensive analysis and logical reasoning for this scenario.",
        ),
        "mixtral": ModelProfile(
            name="mixtral:latest",
            architecture="Mistral-Mixture-of-Experts",
            standings="Expert Synthesizer (Cognitive Tier)",
            use_case="Complex synthesis and pattern recognition",
            specialty_prompt="Identify patterns and synthesize complex information into actionable insights.",
        ),
    }

    def __init__(
        self,
        workspace_root: str | None = None,
        mode: ReasoningMode = ReasoningMode.PARALLEL,
        grid_map_provider: Callable[[Path], Any] | None = None,
        model_lister: Callable[[], list[str]] | None = None,
    ) -> None:
        super().__init__(mode=mode)
        self.root = workspace_root or str(Path.cwd())
        self._grid_map_provider = grid_map_provider
        self._model_lister = model_lister
        self.grid_map = None
        if self._grid_map_provider is not None:
            try:
                self.grid_map = self._grid_map_provider(Path(self.root))
            except Exception:
                logger.warning("Failed to initialize territory map provider.")
        self.available_models = []
        try:
            if self._model_lister is not None:
                self.available_models = self._model_lister()
        except Exception:
            logger.warning("Could not list Ollama models. Defaulting to mistral-nemo.")

    async def reason_ensemble(self, query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Execute the ensemble workflow: Navigation → Multi-Model Inquiry → Synthesis.
        """
        start_time = datetime.now()

        # 1. Navigation Insight
        nav_insight = self._get_navigation_insight(query)
        logger.info(f"📍 Navigation Insight: Zone={nav_insight['zone']}")

        # 2. Select Experts from Inventory
        experts = self._select_experts()
        if not experts:
            # Fallback if no specific profiles match available models
            experts = [self.DEFAULT_PROFILES["mistral-nemo"]] if "mistral-nemo:latest" in self.available_models else []

        # 3. Parallel Inquiry
        tasks = []
        for expert in experts:
            # Tailor the prompt for this specific expert
            tailored_prompt = self._tailor_question(query, expert, nav_insight)
            tasks.append(self._llm_call_expert(tailored_prompt, expert))

        logger.info(f"📡 Dispatching to {len(tasks)} experts...")
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter valid steps
        llm_steps = [s for s in results if isinstance(s, ReasoningStep)]

        # 4. Final Synthesis
        synthesis = self._synthesize_ensemble(llm_steps, nav_insight)

        duration = int((datetime.now() - start_time).total_seconds() * 1000)

        return {
            "query": query,
            "navigation": nav_insight,
            "experts_consulted": [e.name for e in experts],
            "responses": [self._step_to_dict(s) for s in llm_steps],
            "final_response": synthesis,
            "duration_ms": duration,
        }

    def _get_navigation_insight(self, query: str) -> dict[str, Any]:
        """Gathers context from the Territory Map (The Harness)."""
        # Logic to guess which zone the query relates to
        q = query.lower()
        zone = "core"
        if any(x in q for x in ["app", "mothership", "api", "router"]):
            zone = "application"
        elif any(x in q for x in ["rag", "tool", "script"]):
            zone = "tools"
        elif any(x in q for x in ["cognitive", "reasoning", "mind"]):
            zone = "cognitive"

        zone_data: dict[str, Any] = {}
        if self.grid_map is not None and hasattr(self.grid_map, "get_zone_map"):
            zone_data = self.grid_map.get_zone_map().get(zone, {})
        node_count = zone_data.get("count", 0)

        # Enhanced metrics for deeper context
        complexity_score = min(100, node_count * 2)  # Simple complexity metric
        stability_indicator = "Stable" if node_count > 10 else "Experimental"

        # Extract additional context from query patterns
        has_architecture_terms = any(x in q for x in ["design", "pattern", "structure", "architecture"])
        has_implementation_terms = any(x in q for x in ["implement", "code", "function", "class"])
        has_debug_terms = any(x in q for x in ["error", "bug", "fix", "debug"])

        return {
            "zone": zone,
            "node_count": node_count,
            "standing": stability_indicator,
            "hierarchy": "L2_MODULES",
            "complexity_score": complexity_score,
            "query_indicators": {
                "architecture": has_architecture_terms,
                "implementation": has_implementation_terms,
                "debugging": has_debug_terms,
            },
        }

    def _select_experts(self) -> list[ModelProfile]:
        """Matches available Ollama models to their profiles."""
        selected = []
        for profile in self.DEFAULT_PROFILES.values():
            if profile.name in self.available_models:
                selected.append(profile)
        return selected

    def _tailor_question(self, query: str, expert: ModelProfile, nav: dict[str, Any]) -> str:
        """Formulates a precise question based on model architecture and standing."""
        return f"""### ROLE: {expert.standings} ({expert.architecture})
### CONTEXT: Zone={nav["zone"]}, Standing={nav["standing"]}

TASK: {expert.specialty_prompt}

USER QUERY: {query}

Please provide your insight tailored for the {nav["zone"]} zone of this architecture."""

    async def _llm_call_expert(self, prompt: str, expert: ModelProfile) -> ReasoningStep:
        """Individual LLM call to an expert model."""
        start = datetime.now()

        try:
            # We use subprocess for simplicity in this script, similar to path_navigator
            proc = await asyncio.create_subprocess_exec(
                "ollama",
                "run",
                expert.name,
                prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=45)
            response = stdout.decode().strip()

            result = {
                "response": response,
                "model": expert.name,
                "standing": expert.standings,
                "error": stderr.decode() if stderr else None,
            }
        except Exception as e:
            result = {"error": str(e), "model": expert.name}

        duration = int((datetime.now() - start).total_seconds() * 1000)

        return ReasoningStep(
            step_type="expert_inquiry",
            query=prompt,
            result=result,
            duration_ms=duration,
            metadata={"expert": expert.name, "tier": expert.standings},
        )

    def _synthesize_ensemble(self, steps: list[ReasoningStep], nav: dict[str, Any]) -> str:
        """Synthesizes perspectives into a final recommendation."""
        if not steps:
            return "No experts responded. Please check your Ollama installation."

        synthesis_parts = [
            f"### Stratagem Intelligence Recommendation (Zone: {nav['zone'].upper()})",
            f"Based on a collective reasoning session with {len(steps)} expert models.\n",
        ]

        for step in steps:
            res = step.result
            if res.get("response"):
                synthesis_parts.append(f"#### [{res['standing']}] View:")
                synthesis_parts.append(res["response"])
                synthesis_parts.append("")

        return "\n".join(synthesis_parts)


async def main() -> None:
    orchestrator = MultiModelOrchestrator()
    query = "How should we implement the new agentic memory system?"
    result = await orchestrator.reason_ensemble(query)
    print(result["final_response"])


if __name__ == "__main__":
    asyncio.run(main())
