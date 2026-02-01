from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .base import SimpleSkill


def _compress(args: Mapping[str, Any]) -> dict[str, Any]:
    text = args.get("text") or args.get("concept") or args.get("input")
    if text is None:
        return {
            "skill": "compress.articulate",
            "status": "error",
            "error": "Missing required parameter: 'text' (or 'concept')",
        }

    text = str(text)
    max_chars = int(args.get("max_chars", 280) or 280)
    use_llm = bool(args.get("use_llm") or args.get("useLLM"))

    if max_chars < 50:
        max_chars = 50

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
                "Rewrite the following content to be maximally clear while using as few characters as possible.\n"
                f"Hard limit: {max_chars} characters.\n"
                "Avoid pronouns if possible. Prefer concrete nouns.\n\n"
                f"CONTENT:\n{text}\n\n"
                "OUTPUT (must be <= limit):"
            )
            out = llm.generate(prompt=prompt, temperature=0.2)
            out = out.strip()
            if len(out) > max_chars:
                out = out[: max_chars - 1].rstrip() + "…"
            return {
                "skill": "compress.articulate",
                "status": "success",
                "max_chars": max_chars,
                "chars": len(out),
                "output": out,
            }
        except Exception as e:
            return {
                "skill": "compress.articulate",
                "status": "error",
                "error": str(e),
            }

    # Heuristic fallback: first sentence + trimming
    trimmed = " ".join(text.split())
    if len(trimmed) > max_chars:
        trimmed = trimmed[: max_chars - 1].rstrip() + "…"

    return {
        "skill": "compress.articulate",
        "status": "success",
        "max_chars": max_chars,
        "chars": len(trimmed),
        "output": trimmed,
    }


compress_articulate = SimpleSkill(
    id="compress.articulate",
    name="Compress Articulate",
    description="Compress and articulate complex text using minimal characters",
    handler=_compress,
)
