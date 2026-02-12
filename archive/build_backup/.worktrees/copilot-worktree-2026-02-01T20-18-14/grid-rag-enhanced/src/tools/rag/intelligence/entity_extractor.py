"""
Entity Extractor for Intelligent RAG.

This module extracts code-specific entities (classes, functions, files, variables)
from user queries to help ground the RAG search in specific parts of the codebase.
"""

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

# Set up logging
logger = logging.getLogger(__name__)


@dataclass
class Entity:
    """Represents a code entity found in a query."""

    text: str
    label: str  # CLASS, FUNCTION, FILE, MODULE, VARIABLE, etc.
    start: int
    end: int
    confidence: float = 1.0


class EntityExtractor:
    """
    Extracts code entities from natural language queries.
    Uses a hybrid approach of regex patterns and keyword matching to identify
    code-specific references that should be prioritized during retrieval.
    """

    def __init__(self):
        # Regex patterns for common code identifiers
        self.patterns = {
            # File paths: src/tools/rag/chat.py or chat.py
            "FILE": r"\b(?:[\w\-\.]+/)*[\w\-\.]+\.(?:py|md|toml|yaml|json|sh|js|ts|sql)\b",
            # Explicit code references in backticks: `RAGEngine`
            "CODE_REF": r"`([^`]+)`",
            # Function calls: RAGEngine.query() or initialize()
            "FUNCTION": r"\b(?:[A-Za-z_]\w*\.)*[A-Za-z_]\w*(?=\s*\()",
            # Decorators: @router.get
            "DECORATOR": r"@[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*",
            # Classes (CamelCase convention check)
            "CLASS_CANDIDATE": r"\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b",
            # Environment variables / Constants: GRID_QUIET
            "CONSTANT": r"\b[A-Z_][A-Z0-9_]{2,}\b",
        }

        # Known project-specific terms to always flag if found
        self.known_entities = {
            "GRID": "PROJECT",
            "Mothership": "COMPONENT",
            "RAG": "SYSTEM",
            "Ollama": "DEPENDENCY",
            "ChromaDB": "DEPENDENCY",
            "Databricks": "DEPENDENCY",
        }

    def extract(self, query: str) -> List[Entity]:
        """
        Extract all identifiable code entities from a query string.

        Args:
            query: The user's input string.

        Returns:
            List of Entity objects found in the query.
        """
        if not query:
            return []

        entities: List[Entity] = []
        seen_spans: Set[tuple] = set()

        # 1. Check for backtick references first (highest confidence)
        for match in re.finditer(self.patterns["CODE_REF"], query):
            entity_text = match.group(1)
            e = Entity(text=entity_text, label="CODE_BLOCK", start=match.start(), end=match.end(), confidence=1.0)
            entities.append(e)
            seen_spans.add((match.start(), match.end()))

        # 2. Run regex patterns
        for label, pattern in self.patterns.items():
            if label == "CODE_REF":
                continue  # Already handled

            for match in re.finditer(pattern, query):
                # Skip if this span is already covered by a backtick reference
                if any(match.start() >= s and match.end() <= e for s, e in seen_spans):
                    continue

                entities.append(
                    Entity(text=match.group(0), label=label, start=match.start(), end=match.end(), confidence=0.8)
                )
                seen_spans.add((match.start(), match.end()))

        # 3. Check for known project terms
        for term, label in self.known_entities.items():
            # Case-insensitive search for known terms
            for match in re.finditer(rf"\b{re.escape(term)}\b", query, re.IGNORECASE):
                if any(match.start() >= s and match.end() <= e for s, e in seen_spans):
                    continue

                entities.append(
                    Entity(text=match.group(0), label=label, start=match.start(), end=match.end(), confidence=0.9)
                )

        # Sort by start position
        return sorted(entities, key=lambda x: x.start)

    def get_search_terms(self, entities: List[Entity]) -> List[str]:
        """
        Convert extracted entities into optimized search keywords for the vector store.
        """
        terms = []
        for e in entities:
            if e.label == "FILE":
                # Add the filename and the full path
                terms.append(e.text)
                if "/" in e.text:
                    terms.append(e.text.split("/")[-1])
            else:
                terms.append(e.text)
        return list(set(terms))


if __name__ == "__main__":
    # Test cases
    extractor = EntityExtractor()
    test_queries = [
        "How does `RAGEngine.query` work in tools/rag/rag_engine.py?",
        "Show me the logic for the @router.get decorator",
        "Explain GRID_QUIET and USE_DATABRICKS environment variables",
        "Where is the ClassNamedSomething defined?",
        "Tell me about the Mothership component using Ollama",
    ]

    print("\n--- Entity Extraction Test ---")
    for q in test_queries:
        found = extractor.extract(q)
        print(f"Query: '{q}'")
        for ent in found:
            print(f"  - [{ent.label}] {ent.text} ({ent.start}:{ent.end})")
        print("-" * 30)
