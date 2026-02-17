"""GRID Entity Influence Analysis.

Provides mechanisms to calculate entity influence on skills and enhance
RAG queries with entity-driven context.
"""

from __future__ import annotations

from typing import Any


class EntityInfluenceCalculator:
    """Calculates entity influence score for skill selection."""

    def __init__(self) -> None:
        self.entity_weights = {
            "COMPONENT": 0.9,
            "RAILWAY_TERM": 0.8,
            "AUDIO_CONCEPT": 0.7,
            "WATCH_MODULE": 0.6,
            "SCOPE_KEYWORD": 0.8,
            "PHASE": 0.5,
        }

    def calculate_influence_score(self, entities: list[Any], skill_config: dict[str, Any]) -> float:
        """Calculate entity influence score for skill selection.

        Args:
            entities: List of detected entities (objects with entity_type and confidence)
            skill_config: Configuration for the skill including weights and requirements

        Returns:
            Influence score from 0.0 to 1.0
        """
        score = 0.0

        # Influence configuration from skill
        influence_cfg = skill_config.get("entity_influence", {})
        required = influence_cfg.get("required_entities", [])
        optional = influence_cfg.get("optional_entities", [])
        context_weight = influence_cfg.get("context_weight", 0.8)

        # Required entities (must be present)
        for req_type in required:
            if not any(getattr(e, "entity_type", None) == req_type for e in entities):
                return 0.0  # Required entity missing
            score += self.entity_weights.get(req_type, 0.5) * 1.0

        # Optional entities (bonus points)
        for opt_type in optional:
            matching = [e for e in entities if getattr(e, "entity_type", None) == opt_type]
            if matching:
                avg_confidence = sum(getattr(e, "confidence", 0.0) for e in matching) / len(matching)
                score += self.entity_weights.get(opt_type, 0.5) * avg_confidence

        return min(float(score * context_weight), 1.0)


class RAGEntityContextManager:
    """Manages entity-driven context for RAG operations."""

    def __init__(self) -> None:
        self.entity_cache: dict[str, Any] = {}
        self.context_history: list[dict[str, Any]] = []

    def enhance_query_with_entities(self, query: str, entities: list[Any]) -> dict[str, Any]:
        """Enhance RAG query with entity context.

        Args:
            query: The original text query
            entities: Detected entities in the query or context

        Returns:
            Enhanced query dictionary
        """
        # Build entity context
        entity_context = self._build_entity_context(entities)

        # Create enhanced query
        enhanced_query = {
            "original": query,
            "entity_context": entity_context,
            "combined": f"{query} {entity_context}".strip(),
            "entity_weights": self._calculate_entity_weights(entities),
        }

        return enhanced_query

    def _build_entity_context(self, entities: list[Any]) -> str:
        """Build contextual string from entities."""
        context_parts = []
        for entity in entities:
            # Only include high-confidence entities as per influence filtering rules
            if getattr(entity, "confidence", 0.0) > 0.6:
                text = getattr(entity, "text", "")
                if text and text not in context_parts:
                    context_parts.append(text)
        return " ".join(context_parts)

    def _calculate_entity_weights(self, entities: list[Any]) -> dict[str, float]:
        """Calculate weights for entity terms in query."""
        weights: dict[str, float] = {}
        for entity in entities:
            text = getattr(entity, "text", "").lower()
            if text:
                # Weight by confidence and importance (default importance 1.0)
                importance = getattr(entity, "importance", 1.0)
                weight = getattr(entity, "confidence", 0.0) * importance
                weights[text] = max(weights.get(text, 0.0), weight)
        return weights


def detect_entities_filtered(entities: list[Any]) -> list[Any]:
    """Filter entities by confidence and context relevance.

    Rule: confidence > 0.7 and context_relevance > 0.6
    """
    return [e for e in entities if getattr(e, "confidence", 0.0) > 0.7 and getattr(e, "context_relevance", 1.0) > 0.6]


def adjust_context_window_by_entities(entities: list[Any], base_window: int = 1000) -> int:
    """Adjust RAG context window based on entity complexity."""
    if not entities:
        return base_window

    entity_complexity = sum(getattr(e, "confidence", 0.0) * getattr(e, "importance", 1.0) for e in entities) / len(
        entities
    )

    # Dynamic window sizing
    if entity_complexity > 0.8:
        return int(base_window * 1.5)  # Expand for complex entities
    elif entity_complexity < 0.3:
        return int(base_window * 0.7)  # Compact for simple entities
    else:
        return base_window
