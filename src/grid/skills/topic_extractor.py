from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from .base import SimpleSkill


def _extract_topics(args: Mapping[str, Any]) -> dict[str, Any]:
    """Extract discussion topics using wall-board metaphor with pins/stitching imagery."""
    text = args.get("text") or args.get("input")
    if text is None:
        return {
            "skill": "topic_extractor",
            "status": "error",
            "error": "Missing required parameter: 'text'",
        }

    text = str(text)
    use_llm = bool(args.get("use_llm") or args.get("useLLM"))
    max_topics = int(args.get("max_topics", 8))

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
                "Extract the main discussion topics from this text using a wall-board metaphor. "
                "Imagine each topic as a note pinned to a wall with colorful pins, connected by "
                "thread like stitches creating a visual map of the conversation flow.\n\n"
                "For each topic, provide:\n"
                "- topic: The main theme/subject\n"
                "- pins: Key points or sub-topics (bullet points)\n"
                "- connections: How this topic links to other topics\n"
                "- weight: Relative importance (1-10)\n\n"
                f"TEXT:\n{text}\n\n"
                "Format as JSON array of topic objects."
            )
            out = llm.generate(prompt=prompt, temperature=0.3)

            return {
                "skill": "topic_extractor",
                "status": "success",
                "output": out.strip(),
                "metaphor": "wall_board",
            }
        except Exception as e:
            return {
                "skill": "topic_extractor",
                "status": "error",
                "error": str(e),
            }

    # Heuristic fallback: extract key phrases and create topic clusters
    # Split text into sentences and also comma-separated chunks
    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]

    # Stop words to filter out
    stop_words = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "must",
        "shall",
        "can",
        "need",
        "dare",
        "this",
        "that",
        "these",
        "those",
        "i",
        "you",
        "he",
        "she",
        "it",
        "we",
        "they",
        "what",
        "which",
        "who",
        "whom",
        "whose",
        "where",
        "when",
        "why",
        "how",
        "all",
        "each",
        "every",
        "both",
        "few",
        "more",
        "most",
        "other",
        "some",
        "such",
        "no",
        "nor",
        "not",
        "only",
        "own",
        "same",
        "so",
        "than",
        "too",
        "very",
        "just",
        "also",
        "now",
        "here",
        "there",
        "then",
        "once",
        "let",
        "lets",
        "about",
        "use",
        "using",
        "important",
        "new",
    }

    # Extract compound noun phrases (e.g., "API design", "rate limiting")

    # Technical term patterns
    tech_patterns = [
        r"\b([A-Z]{2,}(?:\s+\w+)?)\b",  # Acronyms like JWT, API
        r"\b(\w+(?:ing|tion|ment|ity|ness)\s+\w+|\w+\s+(?:layer|schema|framework|design|system|strategy|choice|permissions?))\b",
        r"\b((?:rate|user|database|frontend|backend|auth\w*|cache|data)\s*\w*)\b",
    ]

    topics: list[dict[str, Any]] = []
    seen_topics = set()

    def add_topic(topic_name: str, context: str, weight: int = 1) -> None:
        """Add a topic if it's valid and not already seen."""
        topic_name = topic_name.strip().lower()
        # Clean up and validate
        words = topic_name.split()
        words = [w for w in words if w not in stop_words and len(w) > 2]
        if not words:
            return
        topic_name = " ".join(words)
        if len(topic_name) < 3 or topic_name in seen_topics:
            return
        seen_topics.add(topic_name)
        topics.append({"topic": topic_name, "context": context, "pins": [], "connections": [], "weight": weight})

    # Extract from comma/semicolon separated lists
    for sentence in sentences:
        chunks = re.split(r"[,;]", sentence)
        for chunk in chunks:
            chunk = chunk.strip()
            if len(chunk) > 3:
                # Look for key phrases in chunk
                for pattern in tech_patterns:
                    matches = re.findall(pattern, chunk, re.IGNORECASE)
                    for match in matches:
                        if isinstance(match, tuple):
                            match = match[0]
                        add_topic(match, sentence, weight=2)

    # Extract capitalized phrases (often topics)
    cap_phrases = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z]?[a-z]+)*)\b", text)
    for phrase in cap_phrases:
        if len(phrase) > 3:
            add_topic(phrase, text[:100], weight=1)

    # Extract action-based topics (what we're discussing/considering)
    action_patterns = [
        r"\b(?:discuss|talk\s+about|explore|examine|consider|need|handle|choose|design)\s+(?:the\s+)?(\w+(?:\s+\w+)?)",
        r"\b(\w+\s+(?:design|layer|schema|framework|strategy|choice|permissions?|limiting|caching))\b",
    ]
    for sentence in sentences:
        for pattern in action_patterns:
            matches = re.findall(pattern, sentence, re.IGNORECASE)
            for match in matches:
                add_topic(match, sentence, weight=3)

    # Fallback: extract significant words if no topics found
    if not topics:
        words = re.findall(r"\b[a-zA-Z]{4,}\b", text)
        word_freq: dict[str, int] = {}
        for word in words:
            w = word.lower()
            if w not in stop_words:
                word_freq[w] = word_freq.get(w, 0) + 1
        # Take top words by frequency
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        for word, freq in sorted_words[:5]:
            add_topic(word, text[:100], weight=freq)

    # Topics already deduplicated via seen_topics set
    # Sort by weight
    topic_list = sorted(topics, key=lambda x: x["weight"], reverse=True)
    topic_list.sort(key=lambda x: x["weight"], reverse=True)

    # Limit to max_topics
    topic_list = topic_list[:max_topics]

    # Add pins (key phrases) for each topic
    for topic in topic_list:
        words = re.findall(r"\b\w+\b", str(topic["context"]))
        key_words = [w for w in words if w.lower() not in stop_words and len(w) > 3]
        topic["pins"] = list(dict.fromkeys(key_words))[:5]  # Top 5 unique key words as pins

    # Create connections between topics based on shared words
    for i, topic1 in enumerate(topic_list):
        for _j, topic2 in enumerate(topic_list[i + 1 :], i + 1):
            words1 = set(topic1["pins"])
            words2 = set(topic2["pins"])
            shared = words1.intersection(words2)
            if shared:
                topic1["connections"].append(
                    {"to": topic2["topic"], "shared_words": list(shared), "strength": len(shared)}
                )
                topic2["connections"].append(
                    {"to": topic1["topic"], "shared_words": list(shared), "strength": len(shared)}
                )

    # Normalize weights to 1-10 scale
    if topic_list:
        max_weight = max(t["weight"] for t in topic_list)
        for topic in topic_list:
            topic["weight"] = max(1, min(10, int((topic["weight"] / max_weight) * 10)))

    return {
        "skill": "topic_extractor",
        "status": "success",
        "output": {
            "wall_board": {
                "topics": topic_list,
                "total_topics": len(topic_list),
                "connections": sum(len(t["connections"]) for t in topic_list)
                // 2,  # Divide by 2 since connections are bidirectional
                "metaphor": "Each topic is a note pinned to the wall, connected by threads showing conversation flow",
            }
        },
        "note": "Heuristic mode used. Enable use_llm for higher-quality topic extraction.",
    }


topic_extractor = SimpleSkill(
    id="topic_extractor",
    name="Topic Extractor",
    description="Extract discussion topics using wall-board metaphor with pins and stitching imagery",
    handler=_extract_topics,
)
