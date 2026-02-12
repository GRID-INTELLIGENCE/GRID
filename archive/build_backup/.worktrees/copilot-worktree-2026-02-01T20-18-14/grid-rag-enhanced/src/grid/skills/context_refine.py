from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from .base import SimpleSkill

_PRONOUNS = re.compile(
    r"\b(i|me|my|mine|we|us|our|ours|you|your|yours|he|him|his|she|her|hers|they|them|their|theirs|it|its|this|that|these|those)\b",
    re.IGNORECASE,
)


def _refine(args: Mapping[str, Any]) -> dict[str, Any]:
    text = args.get("text") or args.get("input")
    if text is None:
        return {
            "skill": "context.refine",
            "status": "error",
            "error": "Missing required parameter: 'text'",
        }

    text = str(text)
    use_llm = bool(args.get("use_llm") or args.get("useLLM"))

    if use_llm:
        try:
            from tools.rag.config import RAGConfig
            from tools.rag.llm.factory import get_llm_provider

            config = RAGConfig.from_env()
            config.ensure_local_only()
            llm = get_llm_provider(config=config)

            prompt = (
                "Rewrite the text into a refined structured form with minimal noise.\n"
                "Rules:\n"
                "- Avoid pronouns. Replace pronouns with explicit nouns where possible.\n"
                "- Prefer bullet points and short sentences.\n"
                "- Preserve technical meaning.\n"
                "- Output sections: Facts, Assumptions, Goals, Constraints, Next actions.\n\n"
                f"TEXT:\n{text}\n"
            )
            out = llm.generate(prompt=prompt, temperature=0.2)
            return {
                "skill": "context.refine",
                "status": "success",
                "output": out.strip(),
            }
        except Exception as e:
            return {
                "skill": "context.refine",
                "status": "error",
                "error": str(e),
            }

    # Heuristic fallback: remove pronouns + normalize whitespace
    cleaned = _PRONOUNS.sub("", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return {
        "skill": "context.refine",
        "status": "success",
        "output": cleaned,
        "note": "Heuristic mode used. Enable use_llm for higher-quality rewriting.",
    }


context_refine = SimpleSkill(
    id="context.refine",
    name="Context Refine",
    description="Refine context into structured, pronoun-minimized text for clarity",
    handler=_refine,
)
