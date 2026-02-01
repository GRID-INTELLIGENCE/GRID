from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .base import SimpleSkill


def _explain(args: Mapping[str, Any]) -> dict[str, Any]:
    concept = str(args.get("concept") or "").strip()
    source_domain = str(args.get("source_domain") or args.get("sourceDomain") or "").strip()
    target_domain = str(args.get("target_domain") or args.get("targetDomain") or "").strip()
    style = str(args.get("style") or "plain").strip()
    use_llm = bool(args.get("use_llm") or args.get("useLLM") or args.get("use_rag") or args.get("useRag"))

    if not concept:
        return {
            "skill": "cross_reference.explain",
            "status": "error",
            "error": "Missing required parameter: 'concept'",
        }

    if not source_domain:
        source_domain = "source domain"
    if not target_domain:
        target_domain = "target domain"

    if use_llm:
        try:
            import importlib

            rag_config_module = importlib.import_module("tools.rag.config")
            rag_llm_module = importlib.import_module("tools.rag.llm.factory")
            RAGConfig = rag_config_module.RAGConfig
            get_llm_provider = rag_llm_module.get_llm_provider

            config = RAGConfig.from_env()
            config.ensure_local_only()
            llm = get_llm_provider(config=config)

            prompt = (
                "Create a cross-domain explanation that maps concepts from one domain to another.\n"
                f"Source domain: {source_domain}\n"
                f"Target domain: {target_domain}\n"
                f"Concept to explain: {concept}\n\n"
                "Output format:\n"
                "1) A one-paragraph explanation in the target domain.\n"
                "2) A mapping table with 5-10 rows: source_term -> target_term -> why.\n"
                "3) A short 'compass' section: how to navigate decisions (3 rules).\n"
                "4) A short 'map' section: the big pieces and how they connect (5 bullets).\n\n"
                f"Style: {style}\n"
                "Avoid fluff. Prefer concrete nouns."
            )
            text = llm.generate(prompt=prompt, temperature=0.3)
            return {
                "skill": "cross_reference.explain",
                "status": "success",
                "concept": concept,
                "source_domain": source_domain,
                "target_domain": target_domain,
                "output": text,
            }
        except Exception as e:
            return {
                "skill": "cross_reference.explain",
                "status": "error",
                "error": str(e),
                "concept": concept,
                "source_domain": source_domain,
                "target_domain": target_domain,
            }

    # Heuristic fallback
    mapping = [
        {
            "source": "signal",
            "target": "input",
            "why": "Both represent incoming information to be interpreted.",
        },
        {
            "source": "noise",
            "target": "confounder",
            "why": "Both reduce clarity and must be filtered.",
        },
        {
            "source": "model",
            "target": "explanation frame",
            "why": "Both structure interpretation and prediction.",
        },
    ]

    output = (
        f"Explain '{concept}' by mapping from {source_domain} to {target_domain}. "
        "Use a mapping table and a navigation compass."
    )

    return {
        "skill": "cross_reference.explain",
        "status": "success",
        "concept": concept,
        "source_domain": source_domain,
        "target_domain": target_domain,
        "output": output,
        "mapping": mapping,
        "compass": [
            "Prefer stable invariants over surface details.",
            "Separate signal from noise before optimizing.",
            "Validate mapping with at least one counterexample.",
        ],
        "map": [
            "Inputs",
            "Constraints",
            "Transformations",
            "Outputs",
            "Feedback loop",
        ],
    }


cross_reference_explain = SimpleSkill(
    id="cross_reference.explain",
    name="Cross Reference Explain",
    description="Generate cross-domain explanations (maps + compass) to make complex concepts easy",
    handler=_explain,
)
