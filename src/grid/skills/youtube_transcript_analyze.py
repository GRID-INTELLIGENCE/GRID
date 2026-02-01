from __future__ import annotations

import asyncio
import re
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .base import SimpleSkill

_STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "to",
    "of",
    "in",
    "on",
    "for",
    "with",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "it",
    "that",
    "this",
    "as",
    "at",
    "by",
    "from",
    "but",
    "not",
    "we",
    "you",
    "i",
    "they",
    "he",
    "she",
    "them",
    "his",
    "her",
    "our",
    "your",
}


def _read_transcript(args: Mapping[str, Any]) -> str:
    transcript_file = args.get("transcript_file") or args.get("transcriptFile")
    transcript_text = args.get("transcript") or args.get("text")

    if transcript_file:
        return Path(str(transcript_file)).read_text(encoding="utf-8")
    if transcript_text is None:
        raise ValueError("Provide 'transcript' (text) or 'transcript_file' (path)")
    return str(transcript_text)


def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z0-9_']+", text.lower())
    return [t for t in tokens if len(t) >= 3 and t not in _STOPWORDS]


def _analyze(args: Mapping[str, Any]) -> dict[str, Any]:
    transcript = _read_transcript(args)
    tokens = _tokenize(transcript)

    counter = Counter(tokens)
    top_n = int(args.get("top_n", 15) or 15)

    result: dict[str, Any] = {
        "skill": "youtube.transcript_analyze",
        "chars": len(transcript),
        "words": len(transcript.split()),
        "tokens": len(tokens),
        "top_keywords": [{"token": t, "count": c} for t, c in counter.most_common(top_n)],
    }

    use_rag = bool(args.get("use_rag") or args.get("useRag"))
    if use_rag:
        try:
            import importlib

            rag_config_module = importlib.import_module("tools.rag.config")
            rag_engine_module = importlib.import_module("tools.rag.rag_engine")
            RAGConfig = rag_config_module.RAGConfig
            RAGEngine = rag_engine_module.RAGEngine

            config = RAGConfig.from_env()
            config.ensure_local_only()
            engine = RAGEngine(config=config)

            focus = ", ".join([t for t, _ in counter.most_common(8)])
            q = (
                "Given this transcript keyword focus: "
                f"{focus}\n\n"
                "What existing GRID modules/features should be used next, and which exact file paths are relevant?"
            )
            rag = asyncio.run(engine.query(query_text=q, top_k=8, temperature=0.2))
            result["rag"] = {
                "answer": rag.get("answer"),
                "sources": rag.get("sources", []),
            }
        except Exception as e:
            result["rag_error"] = str(e)

    return result


youtube_transcript_analyze = SimpleSkill(
    id="youtube.transcript_analyze",
    name="YouTube Transcript Analyze",
    description="Analyze a transcript (local-first) and optionally enrich with RAG",
    handler=_analyze,
)
