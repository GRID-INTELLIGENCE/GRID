"""Model routing utilities for RAG."""

from __future__ import annotations

from dataclasses import dataclass

# Optional import - will fail gracefully if module not available
try:
    from grid.knowledge.multi_model_orchestrator import MultiModelOrchestrator
except ImportError:
    MultiModelOrchestrator = None

from .config import RAGConfig
from .utils import find_embedding_model, find_llm_model, list_ollama_models


@dataclass
class ModelRoutingDecision:
    embedding_provider: str
    embedding_model: str
    llm_provider: str
    llm_model: str
    reason: str


def _classify_query(query: str) -> str:
    q = query.lower()
    if any(x in q for x in ["stack trace", "traceback", "exception", "error:", "segfault"]):
        return "debug"
    if any(
        x in q for x in ["implement", "refactor", "function", "class ", "python", "typescript", "javascript", "sql"]
    ):
        return "code"
    if any(x in q for x in ["summarize", "tl;dr", "overview"]):
        return "summarize"
    if any(x in q for x in ["architecture", "design", "strategy", "roadmap"]):
        return "architecture"
    return "general"


def route_models(
    query: str,
    base_config: RAGConfig | None = None,
    prefer_ollama: bool = True,
) -> ModelRoutingDecision:
    config = base_config or RAGConfig.from_env()

    query_kind = _classify_query(query)

    llm_model = config.llm_model_local
    embedding_provider = config.embedding_provider
    embedding_model = config.embedding_model

    reason_parts: list[str] = [f"query_kind={query_kind}"]

    if prefer_ollama:
        try:
            models = list_ollama_models(config.ollama_base_url)
            if models:
                reason_parts.append("ollama_available=true")
                # Embeddings: prefer nomic embed if available
                found_emb = find_embedding_model(preferred=config.embedding_model, base_url=config.ollama_base_url)
                if found_emb is not None:
                    embedding_provider = "ollama"
                    embedding_model = found_emb
                    reason_parts.append(f"embedding=ollama:{found_emb}")

                # LLM: try preferred, else pick a reasonable fallback
                found_llm = find_llm_model(preferred=config.llm_model_local, base_url=config.ollama_base_url)
                if found_llm is not None:
                    llm_model = found_llm
                    reason_parts.append(f"llm=ollama:{found_llm}")
                else:
                    reason_parts.append("llm=ollama:unavailable")
        except Exception:
            reason_parts.append("ollama_available=false")

    # If query looks code-heavy, slightly bias to a larger/coding-ish model if present.
    if prefer_ollama:
        try:
            models = list_ollama_models(config.ollama_base_url)
            if query_kind in {"code", "debug"}:
                for cand in ["qwen2.5-coder", "deepseek-coder", "codestral", "codellama", "llama3.1", "llama3"]:
                    hit = next((m for m in models if cand in m.lower()), None)
                    if hit:
                        llm_model = hit
                        reason_parts.append(f"llm_bias={hit}")
                        break
        except Exception:
            pass

    return ModelRoutingDecision(
        embedding_provider=embedding_provider,
        embedding_model=embedding_model,
        llm_provider="ollama-local",
        llm_model=llm_model,
        reason="; ".join(reason_parts),
    )


async def route_ensemble_models(
    query: str,
    workspace_root: str | None = None,
    base_config: RAGConfig | None = None,
) -> dict:
    """
    Route to multi-model ensemble for complex queries requiring diverse perspectives.
    """
    base_config or RAGConfig.from_env()
    query_kind = _classify_query(query)

    # Use ensemble for architecture, complex code, or strategic queries
    if query_kind in {"architecture", "code"}:
        try:
            import grid.knowledge.multi_model_orchestrator
            from application.canvas.territory_map import get_grid_map

            config = base_config or RAGConfig.from_env()
            orchestrator = grid.knowledge.multi_model_orchestrator.MultiModelOrchestrator(
                workspace_root=workspace_root,
                grid_map_provider=get_grid_map,
                model_lister=lambda: list_ollama_models(config.ollama_base_url),
            )
            return await orchestrator.reason_ensemble(query)
        except ImportError:
            # Fallback to single model if ensemble not available
            pass

    # Fallback to single model for simpler queries
    decision = route_models(query, base_config, prefer_ollama=True)
    return {
        "query": query,
        "navigation": {"zone": "general", "standing": "stable"},
        "experts_consulted": [decision.llm_model],
        "final_response": f"Single model routing selected: {decision.llm_model}",
        "reason": decision.reason,
    }
