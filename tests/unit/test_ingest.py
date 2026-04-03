"""Unit tests for grid.knowledge.ingest."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

pytestmark = pytest.mark.unit

from grid.knowledge.ingest import IngestConfig, IngestResult, ingest, ingest_many
from grid.knowledge.persistent_store import PersistentJSONKnowledgeStore


SAMPLE_TEXT = """
# Knowledge Graphs

Knowledge Graphs are structured representations of information that use
entities and relationships to capture domain knowledge.

## Embedding Model

Embedding Model is a neural network that converts text into dense vector
representations for semantic similarity search.

Embedding Model uses Knowledge Graphs to enrich retrieval results.

## Vector Search

Vector Search is a technique for finding similar items using embedding
distance rather than keyword matching. Vector Search uses Embedding Model
to compute query embeddings.
"""


@pytest.fixture()
def tmp_store(tmp_path: Path) -> PersistentJSONKnowledgeStore:
    """Provide a temporary knowledge graph store."""
    store = PersistentJSONKnowledgeStore(storage_path=tmp_path / "kg.json")
    store.connect()
    return store


@pytest.fixture()
def heuristic_config() -> IngestConfig:
    """Config that forces heuristic extraction (no Ollama needed in CI)."""
    return IngestConfig(use_ollama=False, index_vectors=False)


class TestIngestText:
    def test_returns_ingest_result(self, tmp_store: PersistentJSONKnowledgeStore, heuristic_config: IngestConfig) -> None:
        result = ingest(SAMPLE_TEXT, config=heuristic_config, store=tmp_store)
        assert isinstance(result, IngestResult)

    def test_success_with_valid_text(self, tmp_store: PersistentJSONKnowledgeStore, heuristic_config: IngestConfig) -> None:
        result = ingest(SAMPLE_TEXT, config=heuristic_config, store=tmp_store)
        assert result.success
        assert result.errors == []

    def test_writes_entities(self, tmp_store: PersistentJSONKnowledgeStore, heuristic_config: IngestConfig) -> None:
        result = ingest(SAMPLE_TEXT, config=heuristic_config, store=tmp_store)
        assert result.entities_written > 0

    def test_writes_relations(self, tmp_store: PersistentJSONKnowledgeStore, heuristic_config: IngestConfig) -> None:
        result = ingest(SAMPLE_TEXT, config=heuristic_config, store=tmp_store)
        # Should have at least EXPLAINS relations (doc → concepts)
        assert result.relations_written > 0

    def test_document_entity_in_store(self, tmp_store: PersistentJSONKnowledgeStore, heuristic_config: IngestConfig) -> None:
        result = ingest(SAMPLE_TEXT, config=heuristic_config, store=tmp_store)
        assert result.document_id in tmp_store.entities

    def test_concept_entities_in_store(self, tmp_store: PersistentJSONKnowledgeStore, heuristic_config: IngestConfig) -> None:
        ingest(SAMPLE_TEXT, config=heuristic_config, store=tmp_store)
        entity_types = {e.entity_type.value for e in tmp_store.entities.values()}
        assert "Concept" in entity_types

    def test_document_entity_type(self, tmp_store: PersistentJSONKnowledgeStore, heuristic_config: IngestConfig) -> None:
        result = ingest(SAMPLE_TEXT, config=heuristic_config, store=tmp_store)
        doc_entity = tmp_store.entities[result.document_id]
        assert doc_entity.entity_type.value == "Document"

    def test_stable_document_id(self, tmp_store: PersistentJSONKnowledgeStore, heuristic_config: IngestConfig) -> None:
        r1 = ingest(SAMPLE_TEXT, config=heuristic_config, store=tmp_store)
        r2 = ingest(SAMPLE_TEXT, config=heuristic_config, store=tmp_store)
        assert r1.document_id == r2.document_id

    def test_extraction_method_heuristic(self, tmp_store: PersistentJSONKnowledgeStore, heuristic_config: IngestConfig) -> None:
        result = ingest(SAMPLE_TEXT, config=heuristic_config, store=tmp_store)
        assert result.extraction_method == "heuristic"

    def test_chunks_indexed_zero_without_vector_flag(
        self, tmp_store: PersistentJSONKnowledgeStore, heuristic_config: IngestConfig
    ) -> None:
        result = ingest(SAMPLE_TEXT, config=heuristic_config, store=tmp_store)
        assert result.chunks_indexed == 0


class TestIngestFile:
    def test_ingest_markdown_file(self, tmp_path: Path, heuristic_config: IngestConfig) -> None:
        md_file = tmp_path / "paper.md"
        md_file.write_text(SAMPLE_TEXT, encoding="utf-8")

        store = PersistentJSONKnowledgeStore(storage_path=tmp_path / "kg.json")
        store.connect()

        result = ingest(md_file, config=heuristic_config, store=store)

        assert result.success
        assert result.entities_written > 0
        store.disconnect()

    def test_ingest_persists_to_disk(self, tmp_path: Path, heuristic_config: IngestConfig) -> None:
        md_file = tmp_path / "paper.md"
        md_file.write_text(SAMPLE_TEXT, encoding="utf-8")
        store_path = tmp_path / "kg.json"

        store = PersistentJSONKnowledgeStore(storage_path=store_path)
        store.connect()
        ingest(md_file, config=heuristic_config, store=store)
        store.disconnect()

        assert store_path.exists()
        data = json.loads(store_path.read_text())
        assert len(data["entities"]) > 0


class TestIngestMany:
    def test_ingests_multiple_files(self, tmp_path: Path, heuristic_config: IngestConfig) -> None:
        texts = [
            "# RAG\nRAG is a retrieval-augmented generation technique.",
            "# Transformer\nTransformer is a deep learning architecture.",
        ]
        files = []
        for i, text in enumerate(texts):
            p = tmp_path / f"doc{i}.md"
            p.write_text(text, encoding="utf-8")
            files.append(p)

        heuristic_config.store_path = str(tmp_path / "kg.json")
        results = ingest_many(files, config=heuristic_config)

        assert len(results) == 2
        assert all(r.success for r in results)

    def test_different_document_ids(self, tmp_path: Path, heuristic_config: IngestConfig) -> None:
        files = []
        for i, text in enumerate(["# Doc A\nDoc A is first.", "# Doc B\nDoc B is second."]):
            p = tmp_path / f"doc{i}.md"
            p.write_text(text)
            files.append(p)

        heuristic_config.store_path = str(tmp_path / "kg.json")
        results = ingest_many(files, config=heuristic_config)

        ids = [r.document_id for r in results]
        assert ids[0] != ids[1]


class TestExportGraphVisualization:
    def test_empty_store(self, tmp_path: Path) -> None:
        store = PersistentJSONKnowledgeStore(storage_path=tmp_path / "kg.json")
        store.connect()
        out = store.export_graph_visualization()
        store.disconnect()
        assert out["nodes"] == []
        assert out["edges"] == []
        assert out["total_entities"] == 0
        assert out["truncated"] is False

    def test_after_ingest_has_nodes_and_edges(
        self, tmp_store: PersistentJSONKnowledgeStore, heuristic_config: IngestConfig
    ) -> None:
        ingest(SAMPLE_TEXT, config=heuristic_config, store=tmp_store)
        out = tmp_store.export_graph_visualization()
        assert len(out["nodes"]) >= 2
        assert len(out["edges"]) >= 1
        ids = {n["id"] for n in out["nodes"]}
        for e in out["edges"]:
            assert e["source"] in ids
            assert e["target"] in ids
            assert "type" in e
            assert "label" in e
        assert out["total_entities"] == len(out["nodes"])
        assert out["truncated"] is False

    def test_export_respects_max_nodes(
        self, tmp_store: PersistentJSONKnowledgeStore, heuristic_config: IngestConfig
    ) -> None:
        ingest(SAMPLE_TEXT, config=heuristic_config, store=tmp_store)
        full = tmp_store.export_graph_visualization()
        if full["total_entities"] <= 1:
            pytest.skip("fixture graph too small to test truncation")

        limited = tmp_store.export_graph_visualization(max_nodes=1)
        assert len(limited["nodes"]) == 1
        assert limited["total_entities"] == full["total_entities"]
        assert limited["truncated"] is True
        allowed = {limited["nodes"][0]["id"]}
        for e in limited["edges"]:
            assert e["source"] in allowed
            assert e["target"] in allowed
