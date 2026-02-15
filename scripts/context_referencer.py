#!/usr/bin/env python3
"""
Context Referencer
Classifies context, generates lightweight embeddings, and sorts questions for EUFLE Studio.
No external backend required.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Iterable, Sequence

WORD_RE = re.compile(r"[A-Za-z0-9_]+")


@dataclass
class ContextItem:
    text: str
    source: str | None = None
    kind: str | None = None
    tags: list[str] = field(default_factory=list)
    embedding: list[float] = field(default_factory=list)


@dataclass
class QueryItem:
    question: str
    category: str
    embedding: list[float]
    top_context: list[tuple[str, float]]


@dataclass
class ContextReferencer:
    embedding_dim: int = 64
    context_items: list[ContextItem] = field(default_factory=list)

    category_rules: dict[str, Sequence[str]] = field(
        default_factory=lambda: {
            "setup": ["install", "setup", "configure", "requirements"],
            "ops": ["deploy", "run", "start", "service", "monitor"],
            "security": ["auth", "token", "secrets", "encryption", "rbac"],
            "data": ["schema", "database", "storage", "index", "etl"],
            "ai": ["model", "embedding", "rag", "llm", "prompt"],
            "dev": ["test", "lint", "format", "build", "ci"],
            "general": [],
        }
    )

    def classify_context(self, text: str) -> str:
        lowered = text.lower()
        for category, keywords in self.category_rules.items():
            if category == "general":
                continue
            if any(keyword in lowered for keyword in keywords):
                return category
        return "general"

    def _tokenize(self, text: str) -> list[str]:
        return [m.group(0).lower() for m in WORD_RE.finditer(text)]

    def embed_text(self, text: str) -> list[float]:
        """Lightweight hashing embedder (no backend)."""
        vector = [0.0] * self.embedding_dim
        tokens = self._tokenize(text)
        if not tokens:
            return vector

        for token in tokens:
            bucket = hash(token) % self.embedding_dim
            vector[bucket] += 1.0

        # L2 normalize
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]
        return vector

    def add_context(
        self, text: str, source: str | None = None, kind: str | None = None, tags: Iterable[str] | None = None
    ) -> ContextItem:
        category = kind or self.classify_context(text)
        item = ContextItem(
            text=text,
            source=source,
            kind=category,
            tags=list(tags) if tags else [],
        )
        item.embedding = self.embed_text(text)
        self.context_items.append(item)
        return item

    def _cosine(self, a: list[float], b: list[float]) -> float:
        if not a or not b:
            return 0.0
        return sum(x * y for x, y in zip(a, b, strict=False))

    def query(self, question: str, top_k: int = 5) -> QueryItem:
        q_embedding = self.embed_text(question)
        scored: list[tuple[str, float]] = []
        for item in self.context_items:
            score = self._cosine(q_embedding, item.embedding)
            if score > 0:
                scored.append((item.text, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        category = self.classify_context(question)
        return QueryItem(question=question, category=category, embedding=q_embedding, top_context=scored[:top_k])

    def sort_questions(self, questions: Iterable[str], top_k: int = 5) -> list[QueryItem]:
        results = [self.query(q, top_k=top_k) for q in questions]
        # Sort by category then by strongest context match
        results.sort(key=lambda r: (r.category, -(r.top_context[0][1] if r.top_context else 0.0)))
        return results


if __name__ == "__main__":
    referencer = ContextReferencer()
    referencer.add_context("Install dependencies and configure environment variables", source="setup")
    referencer.add_context("Use RAG embeddings to answer user queries", source="ai")
    referencer.add_context("Enable RBAC and token rotation", source="security")

    questions = [
        "How do I configure the environment?",
        "How can I help you?",
        "How do we handle token rotation?",
    ]

    queue = referencer.sort_questions(questions)
    for item in queue:
        print(f"[{item.category}] {item.question}")
