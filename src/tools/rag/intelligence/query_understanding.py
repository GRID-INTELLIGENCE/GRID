"""
Query Understanding Orchestrator for Intelligent RAG.

This module coordinates intent classification, entity extraction, and query
expansion to provide a structured understanding of the user's request before
it reaches the retrieval layer.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from .entity_extractor import Entity, EntityExtractor
from .intent_classifier import Intent, IntentClassifier

# Set up logging
logger = logging.getLogger(__name__)


@dataclass
class UnderstoodQuery:
    """The structured result of the query understanding process."""

    original_query: str
    intent: Intent
    intent_confidence: float
    entities: list[Entity]
    search_terms: list[str]
    expanded_queries: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging or API responses."""
        return {
            "query": self.original_query,
            "intent": self.intent.value,
            "confidence": self.intent_confidence,
            "entities": [{"text": e.text, "label": e.label} for e in self.entities],
            "search_terms": self.search_terms,
            "expanded_queries": self.expanded_queries,
        }


class QueryUnderstandingLayer:
    """
    Orchestrates the understanding of user queries by combining intent
    classification and entity extraction.
    """

    def __init__(self, model_name: str = "cross-encoder/nli-deberta-v3-small", use_gpu: bool = True):
        """
        Initialize the query understanding components.
        """
        self.intent_classifier = IntentClassifier(model_name=model_name, use_gpu=use_gpu)
        self.entity_extractor = EntityExtractor()
        logger.info("QueryUnderstandingLayer initialized.")

    def understand(self, query: str) -> UnderstoodQuery:
        """
        Process a raw query into a structured UnderstoodQuery object.
        """
        if not query or not query.strip():
            return UnderstoodQuery(
                original_query=query,
                intent=Intent.OTHER,
                intent_confidence=0.0,
                entities=[],
                search_terms=[],
                expanded_queries=[],
            )

        # 1. Classify Intent
        intent_res = self.intent_classifier.classify(query)

        # 2. Extract Entities
        entities = self.entity_extractor.extract(query)

        # 3. Get optimized search terms
        search_terms = self.entity_extractor.get_search_terms(entities)

        # 4. Generate expansions (Phase 1 basic logic)
        expanded_queries = self._generate_expansions(query, intent_res.intent, entities)

        return UnderstoodQuery(
            original_query=query,
            intent=intent_res.intent,
            intent_confidence=intent_res.confidence,
            entities=entities,
            search_terms=search_terms,
            expanded_queries=expanded_queries,
            metadata={"all_intent_scores": intent_res.all_scores},
        )

    def _generate_expansions(self, query: str, intent: Intent, entities: list[Entity]) -> list[str]:
        """
        Generate variations of the query to improve retrieval recall.
        """
        expansions = [query]

        # Add entity-only search if entities exist
        entity_texts = [e.text for e in entities]
        if entity_texts:
            expansions.append(" ".join(entity_texts))

        # Intent-specific expansions
        if intent == Intent.IMPLEMENTATION:
            expansions.append(f"how is {query} implemented")
            expansions.append(f"source code for {query}")
        elif intent == Intent.DEFINITION:
            expansions.append(f"what is {query}")
            expansions.append(f"definition of {query}")
        elif intent == Intent.LOCATION:
            expansions.append(f"where is {query} defined")
            expansions.append(f"file path for {query}")
        elif intent == Intent.USAGE:
            expansions.append(f"example usage of {query}")
            expansions.append(f"how to use {query}")

        # Deduplicate while preserving order
        seen = set()
        unique_expansions = []
        for q in expansions:
            if q.lower() not in seen:
                unique_expansions.append(q)
                seen.add(q.lower())

        return unique_expansions


if __name__ == "__main__":
    # Test harness
    logging.basicConfig(level=logging.INFO)
    orchestrator = QueryUnderstandingLayer()

    test_queries = [
        "What is the GRID project?",
        "How does `RAGEngine` handle the search process in tools/rag/rag_engine.py?",
        "Where can I find the Mothership configuration?",
        "Fix the connection issue with Ollama",
    ]

    print("\n" + "=" * 50)
    print("QUERY UNDERSTANDING TEST".center(50))
    print("=" * 50)

    for q in test_queries:
        result = orchestrator.understand(q)
        print(f"\nOriginal: '{result.original_query}'")
        print(f"Intent:   {result.intent.value} ({result.intent_confidence:.2%})")
        print(f"Entities: {[f'[{e.label}] {e.text}' for e in result.entities]}")
        print(f"Search:   {result.search_terms}")
        print(f"Expands:  {result.expanded_queries[:3]}")
