"""Unit tests for grid.knowledge.concept_extractor."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

pytestmark = pytest.mark.unit

from grid.knowledge.concept_extractor import (
    ExtractedConcept,
    ExtractedRelation,
    ExtractionResult,
    build_concept_entities,
    build_relationship_entities,
    extract_heuristic,
)
from grid.knowledge.graph_schema import EntityType, RelationType

SAMPLE_MARKDOWN = """
# Attention Mechanism

Attention Mechanism is a neural network component that allows models to focus
on relevant parts of the input when producing output.

## Transformer Architecture

Transformer Architecture is a model design that relies entirely on attention
mechanisms, dispensing with recurrence and convolutions entirely.

Transformer Architecture extends Attention Mechanism to enable parallelization.

## Self-Attention

Self-Attention is a variant of attention that relates different positions of a
single sequence. Self-Attention uses Attention Mechanism internally.

## Feed-Forward Network

Feed-Forward Network is a sub-layer in each Transformer block that applies
two linear transformations with a ReLU activation in between.
"""


class TestHeuristicExtraction:
    def test_extracts_headings_as_concepts(self) -> None:
        result = extract_heuristic(SAMPLE_MARKDOWN)
        names = [c.name for c in result.concepts]
        assert "Attention Mechanism" in names
        assert "Transformer Architecture" in names
        assert "Self-Attention" in names

    def test_method_is_heuristic(self) -> None:
        result = extract_heuristic(SAMPLE_MARKDOWN)
        assert result.method == "heuristic"

    def test_extracts_relations(self) -> None:
        result = extract_heuristic(SAMPLE_MARKDOWN)
        # "extends" and "uses" patterns should fire
        assert len(result.relations) > 0

    def test_empty_text(self) -> None:
        result = extract_heuristic("")
        assert result.concepts == []
        assert result.relations == []

    def test_no_duplicate_concepts(self) -> None:
        result = extract_heuristic(SAMPLE_MARKDOWN)
        names = [c.name for c in result.concepts]
        assert len(names) == len(set(names))

    def test_concept_has_description(self) -> None:
        result = extract_heuristic(SAMPLE_MARKDOWN)
        attention = next(c for c in result.concepts if c.name == "Attention Mechanism")
        assert len(attention.description) > 0

    def test_confidence_range(self) -> None:
        result = extract_heuristic(SAMPLE_MARKDOWN)
        for concept in result.concepts:
            assert 0.0 <= concept.confidence <= 1.0

    def test_hyphenated_concepts_connect_in_relation_sentences(self) -> None:
        """Headings with hyphens must match relation patterns and resolve to canonical names."""
        md = """# Paper

## Multi-Head Attention

Multi-Head Attention extends Attention Mechanism by running attention in parallel.

## Attention Mechanism

Attention Mechanism is the core idea.
"""
        result = extract_heuristic(md)
        pairs = {(r.from_concept, r.to_concept, r.relation_label) for r in result.relations}
        assert ("Multi-Head Attention", "Attention Mechanism", "extends") in pairs


class TestBuildConceptEntities:
    def test_produces_entity_per_concept(self) -> None:
        concepts = [
            ExtractedConcept(name="RAG", description="Retrieval Augmented Generation", confidence=0.9),
            ExtractedConcept(name="ChromaDB", description="A vector database", confidence=0.8),
        ]
        entities = build_concept_entities(concepts, "doc_abc123")
        assert len(entities) == 2

    def test_entity_type_is_concept(self) -> None:
        concepts = [ExtractedConcept(name="Test Concept", description="A concept", confidence=1.0)]
        entities = build_concept_entities(concepts, "doc_xyz")
        assert entities[0].entity_type == EntityType.CONCEPT

    def test_entity_has_required_properties(self) -> None:
        concepts = [ExtractedConcept(name="Embedding", description="A vector representation", confidence=0.9)]
        entities = build_concept_entities(concepts, "doc_test")
        props = entities[0].properties
        assert "id" in props
        assert "name" in props
        assert props["name"] == "Embedding"
        assert props["source_document"] == "doc_test"

    def test_entity_id_is_stable(self) -> None:
        concepts = [ExtractedConcept(name="My Concept", description="", confidence=1.0)]
        e1 = build_concept_entities(concepts, "doc_aaa")
        e2 = build_concept_entities(concepts, "doc_aaa")
        assert e1[0].entity_id == e2[0].entity_id

    def test_empty_concepts(self) -> None:
        entities = build_concept_entities([], "doc_empty")
        assert entities == []


class TestBuildRelationshipEntities:
    def test_produces_relationship_per_known_pair(self) -> None:
        concepts = [
            ExtractedConcept(name="A", description="First", confidence=1.0),
            ExtractedConcept(name="B", description="Second", confidence=1.0),
        ]
        entities = build_concept_entities(concepts, "doc_rel")
        relations = [ExtractedRelation(from_concept="A", to_concept="B", relation_label="extends", confidence=0.8)]
        rels = build_relationship_entities(relations, entities)
        assert len(rels) == 1
        assert rels[0].relationship_type == RelationType.CONNECTS_TO

    def test_skips_unknown_concepts(self) -> None:
        entities = build_concept_entities([ExtractedConcept(name="Known", description="", confidence=1.0)], "doc_x")
        relations = [
            ExtractedRelation(from_concept="Known", to_concept="Unknown", relation_label="uses", confidence=0.7)
        ]
        rels = build_relationship_entities(relations, entities)
        assert rels == []

    def test_relationship_has_label_property(self) -> None:
        concepts = [
            ExtractedConcept(name="X", description="", confidence=1.0),
            ExtractedConcept(name="Y", description="", confidence=1.0),
        ]
        entities = build_concept_entities(concepts, "doc_lbl")
        relations = [
            ExtractedRelation(from_concept="X", to_concept="Y", relation_label="contrasts with", confidence=0.75)
        ]
        rels = build_relationship_entities(relations, entities)
        assert rels[0].properties["relation_label"] == "contrasts with"
        assert rels[0].properties["confidence"] == 0.75
