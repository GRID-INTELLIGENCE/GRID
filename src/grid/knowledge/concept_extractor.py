"""
Concept Extractor for GRID Knowledge Ingestion.

Extracts named concepts and semantic relationships from documents
to populate the knowledge graph. Supports two modes:

- LLM-assisted: Uses Ollama with a structured prompt to extract
  concepts and connections with high accuracy.
- Heuristic fallback: Regex + heading/definition pattern matching
  for offline or fast extraction.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import structlog

from .graph_schema import EntityType, RelationType
from .graph_store import Entity, Relationship

logger = structlog.get_logger(__name__)


@dataclass
class ExtractedConcept:
    """A concept extracted from a document."""

    name: str
    description: str
    confidence: float = 1.0
    excerpt: str = ""


@dataclass
class ExtractedRelation:
    """A relationship between two concepts."""

    from_concept: str
    to_concept: str
    relation_label: str  # e.g. "extends", "contrasts with", "is part of"
    confidence: float = 1.0


@dataclass
class ExtractionResult:
    """Output of concept extraction from a document."""

    concepts: list[ExtractedConcept] = field(default_factory=list)
    relations: list[ExtractedRelation] = field(default_factory=list)
    method: str = "heuristic"  # "ollama" | "heuristic"


# ---------------------------------------------------------------------------
# Heuristic extraction (offline, no LLM)
# ---------------------------------------------------------------------------

_DEFINITION_PATTERNS = [
    # "X is a/an ..."
    re.compile(r"^([A-Z][^.]{2,60}?) is (?:a|an) ([^.]{10,200})\.", re.MULTILINE),
    # "X refers to ..."
    re.compile(r"^([A-Z][^.]{2,60}?) refers to ([^.]{10,200})\.", re.MULTILINE),
    # "X: description" (glossary style)
    re.compile(r"^([A-Z][A-Za-z\s\-]{2,50}):\s+([^.\n]{20,200})", re.MULTILINE),
]

# Concept names in sample docs use hyphens (Multi-Head, Self-Attention); include them in captures.
_REL_NAME = r"[A-Z][A-Za-z0-9\s\-]+"

_RELATION_PATTERNS = [
    (re.compile(rf"({_REL_NAME}) extends ({_REL_NAME})", re.MULTILINE), "extends"),
    (re.compile(rf"({_REL_NAME}) is based on ({_REL_NAME})", re.MULTILINE), "is based on"),
    (re.compile(rf"({_REL_NAME}) uses ({_REL_NAME})", re.MULTILINE), "uses"),
    (re.compile(rf"({_REL_NAME}) contrasts with ({_REL_NAME})", re.MULTILINE), "contrasts with"),
    (re.compile(rf"({_REL_NAME}) builds on ({_REL_NAME})", re.MULTILINE), "builds on"),
    (re.compile(rf"({_REL_NAME}) differs from ({_REL_NAME})", re.MULTILINE), "differs from"),
]


def _extract_headings(text: str) -> list[ExtractedConcept]:
    """Extract concepts from markdown headings."""
    concepts = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        match = re.match(r"^#{1,3}\s+(.+)$", line)
        if not match:
            continue
        name = match.group(1).strip()
        if len(name) < 3 or len(name) > 80:
            continue
        # Get the first non-empty line after the heading as description
        description = ""
        for j in range(i + 1, min(i + 5, len(lines))):
            candidate = lines[j].strip()
            if candidate and not candidate.startswith("#"):
                description = candidate[:200]
                break
        concepts.append(ExtractedConcept(name=name, description=description, confidence=0.7))
    return concepts


def _extract_definitions(text: str) -> list[ExtractedConcept]:
    """Extract concepts from definition patterns."""
    concepts = []
    seen: set[str] = set()
    for pattern in _DEFINITION_PATTERNS:
        for match in pattern.finditer(text):
            name = match.group(1).strip()
            desc = match.group(2).strip()
            if name in seen or len(name) < 3:
                continue
            seen.add(name)
            concepts.append(
                ExtractedConcept(
                    name=name,
                    description=desc,
                    confidence=0.8,
                    excerpt=match.group(0)[:200],
                )
            )
    return concepts


def _norm_concept_key(name: str) -> str:
    """Lowercase, hyphen/space-insensitive key for matching regex fragments to heading names."""
    return " ".join(name.lower().replace("-", " ").split())


def _resolve_raw_to_known(raw: str, known_concepts: set[str]) -> str | None:
    """Map a regex capture to the canonical concept name from the known set."""
    r = raw.strip()
    if len(r) < 2:
        return None
    if r in known_concepts:
        return r
    r_key = _norm_concept_key(r)
    for k in known_concepts:
        if _norm_concept_key(k) == r_key:
            return k

    def boundary_ok(prefix: str, full: str) -> bool:
        if not full.startswith(prefix):
            return False
        if len(full) == len(prefix):
            return True
        return full[len(prefix)] in " \t\n-,.;:)"

    # Regex stopped early (e.g. before a hyphen): raw is a prefix of a known heading name.
    prefix_hits = [k for k in known_concepts if boundary_ok(r, k)]
    if prefix_hits:
        return max(prefix_hits, key=len)

    # Greedy capture ran past the name: known heading is a prefix of raw.
    suffix_hits = [k for k in known_concepts if boundary_ok(k, r)]
    if suffix_hits:
        return max(suffix_hits, key=len)

    return None


def _extract_relations_heuristic(text: str, known_concepts: set[str]) -> list[ExtractedRelation]:
    """Extract relationships using pattern matching."""
    relations = []
    for pattern, label in _RELATION_PATTERNS:
        for match in pattern.finditer(text):
            from_c = match.group(1).strip()
            to_c = match.group(2).strip()
            canon_from = _resolve_raw_to_known(from_c, known_concepts)
            canon_to = _resolve_raw_to_known(to_c, known_concepts)
            if canon_from is None or canon_to is None:
                continue
            relations.append(
                ExtractedRelation(
                    from_concept=canon_from,
                    to_concept=canon_to,
                    relation_label=label,
                    confidence=0.6,
                )
            )
    return relations


def extract_heuristic(text: str) -> ExtractionResult:
    """Fast offline extraction using regex and heading patterns."""
    concepts: list[ExtractedConcept] = []

    # Heading-based concepts
    concepts.extend(_extract_headings(text))

    # Definition-based concepts
    for c in _extract_definitions(text):
        if not any(existing.name == c.name for existing in concepts):
            concepts.append(c)

    known = {c.name for c in concepts}
    relations = _extract_relations_heuristic(text, known)

    return ExtractionResult(concepts=concepts, relations=relations, method="heuristic")


# ---------------------------------------------------------------------------
# LLM-assisted extraction (Ollama)
# ---------------------------------------------------------------------------

_EXTRACTION_PROMPT = """\
You are a knowledge graph extraction engine. Given the document text below, extract:

1. KEY CONCEPTS: Named ideas, terms, methods, or frameworks the document introduces or discusses.
2. RELATIONSHIPS: Connections between those concepts.

Return ONLY valid JSON in this exact structure:
{{
  "concepts": [
    {{"name": "Concept Name", "description": "One sentence definition", "excerpt": "quote from text"}}
  ],
  "relations": [
    {{"from": "Concept A", "to": "Concept B", "label": "extends|uses|contrasts with|builds on|is part of|requires"}}
  ]
}}

Rules:
- Concepts must be proper noun phrases (2-6 words), not generic terms like "system" or "method"
- Limit to 15 concepts and 20 relations maximum
- Only extract relations between concepts you listed
- excerpt must be a short verbatim quote (max 100 chars)

DOCUMENT:
{text}
"""


def _call_ollama(text: str, model: str, base_url: str, timeout: float) -> dict[str, Any] | None:
    """Call Ollama synchronously and return parsed JSON response."""
    try:
        import httpx
    except ImportError:
        logger.warning("httpx not available, falling back to heuristic extraction")
        return None

    prompt = _EXTRACTION_PROMPT.format(text=text[:6000])

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(
                f"{base_url}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
            )
            response.raise_for_status()
            raw = response.json().get("response", "")
            # Extract JSON block (LLM may wrap in markdown code fences)
            json_match = re.search(r"\{.*\}", raw, re.DOTALL)
            if not json_match:
                return None
            return json.loads(json_match.group(0))  # type: ignore[no-any-return]
    except Exception as exc:
        logger.warning("Ollama extraction failed, falling back to heuristic", error=str(exc))
        return None


def extract_with_ollama(
    text: str,
    model: str = "ministral:latest",
    base_url: str = "http://localhost:11434",
    timeout: float = 60.0,
) -> ExtractionResult:
    """LLM-assisted extraction via Ollama with heuristic fallback."""
    data = _call_ollama(text, model, base_url, timeout)

    if not data:
        return extract_heuristic(text)

    concepts: list[ExtractedConcept] = []
    for item in data.get("concepts", []):
        name = str(item.get("name", "")).strip()
        if not name:
            continue
        concepts.append(
            ExtractedConcept(
                name=name,
                description=str(item.get("description", "")),
                confidence=0.9,
                excerpt=str(item.get("excerpt", ""))[:200],
            )
        )

    known = {c.name for c in concepts}
    relations: list[ExtractedRelation] = []
    for item in data.get("relations", []):
        from_c = str(item.get("from", "")).strip()
        to_c = str(item.get("to", "")).strip()
        label = str(item.get("label", "related to")).strip()
        if from_c in known and to_c in known and from_c != to_c:
            relations.append(
                ExtractedRelation(
                    from_concept=from_c,
                    to_concept=to_c,
                    relation_label=label,
                    confidence=0.85,
                )
            )

    return ExtractionResult(concepts=concepts, relations=relations, method="ollama")


# ---------------------------------------------------------------------------
# Graph entity builders
# ---------------------------------------------------------------------------


def build_concept_entities(
    concepts: list[ExtractedConcept],
    document_id: str,
) -> list[Entity]:
    """Convert extracted concepts into Entity objects for the knowledge graph."""
    now = datetime.now(UTC)
    entities = []
    for concept in concepts:
        entity_id = f"concept_{concept.name.lower().replace(' ', '_')}_{document_id[:8]}"
        entities.append(
            Entity(
                entity_id=entity_id,
                entity_type=EntityType.CONCEPT,
                properties={
                    "id": entity_id,
                    "name": concept.name,
                    "description": concept.description,
                    "source_document": document_id,
                    "created_at": now.isoformat(),
                    "metadata": {"excerpt": concept.excerpt, "confidence": concept.confidence},
                },
                created_at=now,
                updated_at=now,
                labels={"concept"},
            )
        )
    return entities


def build_relationship_entities(
    relations: list[ExtractedRelation],
    concept_entities: list[Entity],
) -> list[Relationship]:
    """Convert extracted relations into Relationship objects."""
    now = datetime.now(UTC)
    name_to_id = {e.properties["name"]: e.entity_id for e in concept_entities}
    relationships = []
    for rel in relations:
        from_id = name_to_id.get(rel.from_concept)
        to_id = name_to_id.get(rel.to_concept)
        if not from_id or not to_id:
            continue
        relationships.append(
            Relationship(
                relationship_id=str(uuid4()),
                from_entity_id=from_id,
                to_entity_id=to_id,
                relationship_type=RelationType.CONNECTS_TO,
                properties={
                    "relation_label": rel.relation_label,
                    "confidence": rel.confidence,
                },
                created_at=now,
                updated_at=now,
            )
        )
    return relationships


__all__ = [
    "ExtractedConcept",
    "ExtractedRelation",
    "ExtractionResult",
    "extract_heuristic",
    "extract_with_ollama",
    "build_concept_entities",
    "build_relationship_entities",
]
