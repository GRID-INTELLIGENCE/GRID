"""
Skill: patterns.detect_entities

Extract and analyze named entities using GRID's NER pipeline.
Detects persons, organizations, domains, and other entity types.
"""

from __future__ import annotations

import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

# Add grid root to path
grid_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(grid_root))

from .base import SimpleSkill


# Fallback entity detection if NER service is not available
def _simple_entity_detection(text: str, entity_types: list[str]) -> list[dict[str, Any]]:
    """Simple heuristic entity detection as fallback."""
    import re

    entities = []

    # PERSON patterns
    if "PERSON" in entity_types:
        person_pattern = r"\b[A-Z][a-z]+ [A-Z][a-z]+\b"
        for match in re.finditer(person_pattern, text):
            entities.append(
                {
                    "text": match.group(),
                    "type": "PERSON",
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": 0.75,  # Lower confidence for heuristic
                }
            )

    # ORG patterns (ALL CAPS or Title Case with Corp/Inc/LLC)
    if "ORG" in entity_types:
        org_pattern = r"\b[A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)*\s+(?:Corp|Inc|LLC|Ltd|Co|Company|Organization)\b"
        for match in re.finditer(org_pattern, text):
            entities.append(
                {
                    "text": match.group(),
                    "type": "ORG",
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": 0.80,
                }
            )

    # DOMAIN patterns
    if "DOMAIN" in entity_types:
        domain_pattern = r"\b(?:machine learning|artificial intelligence|data science|software engineering|web development|cloud computing|devops|cybersecurity)\b"
        for match in re.finditer(domain_pattern, text, re.IGNORECASE):
            entities.append(
                {
                    "text": match.group(),
                    "type": "DOMAIN",
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": 0.85,
                }
            )

    return entities


def _detect_entities(args: Mapping[str, Any]) -> dict[str, Any]:
    """Detect entities in text."""
    text = args.get("text")
    if not text:
        return {
            "skill": "patterns.detect_entities",
            "status": "error",
            "error": "Missing required parameter: 'text'",
        }

    entity_types = args.get("entity_types")
    if isinstance(entity_types, str):
        entity_types = [t.strip() for t in entity_types.split(",")]
    elif not entity_types:
        entity_types = ["PERSON", "ORG", "DOMAIN"]

    try:
        # Try to use GRID's NER service
        try:
            from application.mothership.ner_service import NERService  # type: ignore[import-not-found]

            ner = NERService()
            entities = ner.extract(text, entity_types=entity_types)
        except ImportError:
            # Fallback to simple detection
            entities = _simple_entity_detection(text, entity_types)

        return {
            "skill": "patterns.detect_entities",
            "status": "success",
            "entities": entities,
            "entity_count": len(entities),
            "extracted_from_chars": len(text),
            "entity_types_requested": entity_types,
        }

    except Exception as e:
        return {
            "skill": "patterns.detect_entities",
            "status": "error",
            "error": str(e),
        }


# Register skill
patterns_detect_entities = SimpleSkill(
    id="patterns.detect_entities",
    name="Entity Detection",
    description="Extract named entities (persons, organizations, domains) from text",
    handler=_detect_entities,
)
