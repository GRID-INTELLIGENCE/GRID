"""
Regression tests for PersistentJSONKnowledgeStore.

These tests capture the exact contract of the current JSON-backed store
and serve as the pass/fail gate for the SQLite migration in sqlite_store.py.
All tests must pass against both PersistentJSONKnowledgeStore and
PersistentSQLiteKnowledgeStore (parametrized below).
"""

from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from grid.knowledge.graph_schema import EntityType, RelationType
from grid.knowledge.graph_store import (
    Entity,
    EntityId,
    Relationship,
    RelationshipId,
    SearchContext,
)
from grid.knowledge.persistent_store import PersistentJSONKnowledgeStore
from grid.knowledge.sqlite_store import PersistentSQLiteKnowledgeStore

# Both stores must satisfy the same contract.
_STORE_CLASSES = [PersistentJSONKnowledgeStore, PersistentSQLiteKnowledgeStore]
_STORE_IDS = ["json", "sqlite"]


def _make_entity(
    entity_id: str = "test_entity_001",
    entity_type: EntityType = EntityType.CONCEPT,
    properties: dict | None = None,
    labels: set[str] | None = None,
) -> Entity:
    now = datetime.now()
    default_props = {
        "id": entity_id,
        "name": "Test Entity",
        "description": "A test concept",
        "created_at": now.isoformat(),
    }
    if properties is not None:
        merged = {**default_props, **properties}
        if "id" not in properties:
            merged["id"] = entity_id
        if "created_at" not in properties:
            merged["created_at"] = now.isoformat()
    else:
        merged = default_props
    return Entity(
        entity_id=entity_id,
        entity_type=entity_type,
        properties=merged,
        created_at=now,
        updated_at=now,
        labels=labels or {"concept"},
    )


def _make_relationship(
    from_id: str,
    to_id: str,
    rel_type: RelationType = RelationType.RELATED_TO,
    rel_id: str = "rel_001",
) -> Relationship:
    now = datetime.now()
    return Relationship(
        relationship_id=rel_id,
        from_entity_id=from_id,
        to_entity_id=to_id,
        relationship_type=rel_type,
        properties={"confidence": 0.9},
        created_at=now,
        updated_at=now,
    )


@pytest.fixture(params=_STORE_CLASSES, ids=_STORE_IDS)
def store(request: pytest.FixtureRequest, tmp_path: Path):
    cls = request.param
    ext = ".json" if cls is PersistentJSONKnowledgeStore else ".db"
    path = tmp_path / f"test_knowledge_graph{ext}"
    s = cls(storage_path=path)
    s.connect()
    return s


@pytest.fixture(params=_STORE_CLASSES, ids=_STORE_IDS)
def store_class_and_path(request: pytest.FixtureRequest, tmp_path: Path):
    """Returns (StoreClass, path) for roundtrip tests that create multiple instances."""
    cls = request.param
    ext = ".json" if cls is PersistentJSONKnowledgeStore else ".db"
    path = tmp_path / f"test_knowledge_graph{ext}"
    return cls, path


@pytest.fixture()
def tmp_json_path(tmp_path: Path) -> Path:
    return tmp_path / "test_knowledge_graph.json"


# ---------------------------------------------------------------------------
# store_entity
# ---------------------------------------------------------------------------


class TestStoreEntity:
    def test_returns_entity_id(self, store: PersistentJSONKnowledgeStore) -> None:
        entity = _make_entity()
        result = store.store_entity(entity)
        assert isinstance(result, EntityId)
        assert result.value == entity.entity_id

    def test_entity_retrievable_after_store(self, store: PersistentJSONKnowledgeStore) -> None:
        entity = _make_entity(entity_id="e_retrieve")
        store.store_entity(entity)
        fetched = store.get_entity(EntityId("e_retrieve"))
        assert fetched is not None
        assert fetched.entity_id == "e_retrieve"
        assert fetched.entity_type == EntityType.CONCEPT

    def test_properties_preserved(self, store: PersistentJSONKnowledgeStore) -> None:
        props = {"name": "Transformer", "description": "Attention model", "confidence": 0.95}
        entity = _make_entity(entity_id="e_props", properties=props)
        store.store_entity(entity)
        fetched = store.get_entity(EntityId("e_props"))
        assert fetched is not None
        assert fetched.properties["name"] == "Transformer"
        assert fetched.properties["confidence"] == 0.95

    def test_labels_preserved(self, store: PersistentJSONKnowledgeStore) -> None:
        entity = _make_entity(entity_id="e_labels", labels={"concept", "important"})
        store.store_entity(entity)
        fetched = store.get_entity(EntityId("e_labels"))
        assert fetched is not None
        assert "concept" in fetched.labels
        assert "important" in fetched.labels

    def test_overwrite_existing_entity(self, store: PersistentJSONKnowledgeStore) -> None:
        entity = _make_entity(entity_id="e_overwrite", properties={"name": "Original"})
        store.store_entity(entity)
        updated = _make_entity(entity_id="e_overwrite", properties={"name": "Updated"})
        store.store_entity(updated)
        fetched = store.get_entity(EntityId("e_overwrite"))
        assert fetched is not None
        assert fetched.properties["name"] == "Updated"

    def test_multiple_entity_types(self, store: PersistentJSONKnowledgeStore) -> None:
        for etype in [EntityType.AGENT, EntityType.SKILL, EntityType.DOCUMENT]:
            entity = _make_entity(entity_id=f"e_{etype.value}", entity_type=etype)
            result = store.store_entity(entity)
            assert result.value == f"e_{etype.value}"

    def test_different_entities_stored_independently(self, store: PersistentJSONKnowledgeStore) -> None:
        e1 = _make_entity(entity_id="e_alpha", properties={"name": "Alpha"})
        e2 = _make_entity(entity_id="e_beta", properties={"name": "Beta"})
        store.store_entity(e1)
        store.store_entity(e2)
        assert store.get_entity(EntityId("e_alpha")).properties["name"] == "Alpha"
        assert store.get_entity(EntityId("e_beta")).properties["name"] == "Beta"


# ---------------------------------------------------------------------------
# get_entity
# ---------------------------------------------------------------------------


class TestGetEntity:
    def test_returns_none_for_missing_entity(self, store: PersistentJSONKnowledgeStore) -> None:
        result = store.get_entity(EntityId("nonexistent"))
        assert result is None

    def test_entity_id_value_matches(self, store: PersistentJSONKnowledgeStore) -> None:
        entity = _make_entity(entity_id="e_check_id")
        store.store_entity(entity)
        fetched = store.get_entity(EntityId("e_check_id"))
        assert fetched.entity_id == "e_check_id"


# ---------------------------------------------------------------------------
# create_relationship
# ---------------------------------------------------------------------------


class TestCreateRelationship:
    def test_returns_relationship_id(self, store: PersistentJSONKnowledgeStore) -> None:
        e1 = _make_entity(entity_id="e_from")
        e2 = _make_entity(entity_id="e_to")
        store.store_entity(e1)
        store.store_entity(e2)
        result = store.create_relationship(
            from_id=EntityId("e_from"),
            to_id=EntityId("e_to"),
            relationship_type=RelationType.RELATED_TO,
            properties={"confidence": 0.9},
        )
        assert isinstance(result, RelationshipId)
        assert result.value  # non-empty

    def test_relationship_properties_stored(self, store: PersistentJSONKnowledgeStore) -> None:
        store.store_entity(_make_entity(entity_id="r_from"))
        store.store_entity(_make_entity(entity_id="r_to"))
        store.create_relationship(
            from_id=EntityId("r_from"),
            to_id=EntityId("r_to"),
            relationship_type=RelationType.EXPLAINS,
            properties={"excerpt": "test", "confidence": 0.75},
        )
        stats = store.get_graph_statistics()
        assert stats["total_relationships"] == 1

    def test_multiple_relationships(self, store: PersistentJSONKnowledgeStore) -> None:
        store.store_entity(_make_entity(entity_id="m_a"))
        store.store_entity(_make_entity(entity_id="m_b"))
        store.store_entity(_make_entity(entity_id="m_c"))
        store.create_relationship(EntityId("m_a"), EntityId("m_b"), RelationType.DEPENDS_ON)
        store.create_relationship(EntityId("m_b"), EntityId("m_c"), RelationType.GENERATED)
        assert store.get_graph_statistics()["total_relationships"] == 2

    def test_relationship_without_properties(self, store: PersistentJSONKnowledgeStore) -> None:
        store.store_entity(_make_entity(entity_id="np_from"))
        store.store_entity(_make_entity(entity_id="np_to"))
        result = store.create_relationship(
            from_id=EntityId("np_from"),
            to_id=EntityId("np_to"),
            relationship_type=RelationType.REFERENCES,
        )
        assert isinstance(result, RelationshipId)


# ---------------------------------------------------------------------------
# semantic_search
# ---------------------------------------------------------------------------


class TestSemanticSearch:
    def test_finds_entity_by_name_keyword(self, store: PersistentJSONKnowledgeStore) -> None:
        store.store_entity(
            _make_entity(
                entity_id="s_transformer", properties={"name": "Transformer", "description": "Attention model"}
            )
        )
        store.store_entity(
            _make_entity(entity_id="s_other", properties={"name": "Unrelated", "description": "Something else"})
        )
        ctx = SearchContext(query="Transformer")
        results = store.semantic_search("Transformer", ctx)
        ids = [e.entity_id for e in results]
        assert "s_transformer" in ids

    def test_case_insensitive_match(self, store: PersistentJSONKnowledgeStore) -> None:
        store.store_entity(_make_entity(entity_id="s_case", properties={"name": "ATTENTION", "description": ""}))
        ctx = SearchContext(query="attention")
        results = store.semantic_search("attention", ctx)
        assert any(e.entity_id == "s_case" for e in results)

    def test_filters_by_entity_type(self, store: PersistentJSONKnowledgeStore) -> None:
        store.store_entity(
            _make_entity(entity_id="s_concept", entity_type=EntityType.CONCEPT, properties={"name": "shared"})
        )
        store.store_entity(
            _make_entity(entity_id="s_agent", entity_type=EntityType.AGENT, properties={"name": "shared"})
        )
        ctx = SearchContext(query="shared", entity_types=[EntityType.CONCEPT])
        results = store.semantic_search("shared", ctx)
        assert all(e.entity_type == EntityType.CONCEPT for e in results)
        assert any(e.entity_id == "s_concept" for e in results)

    def test_respects_limit(self, store: PersistentJSONKnowledgeStore) -> None:
        for i in range(10):
            store.store_entity(
                _make_entity(
                    entity_id=f"s_limit_{i}", properties={"name": f"entity {i}", "description": "common keyword"}
                )
            )
        ctx = SearchContext(query="common", limit=3)
        results = store.semantic_search("common", ctx)
        assert len(results) <= 3

    def test_no_match_returns_empty(self, store: PersistentJSONKnowledgeStore) -> None:
        store.store_entity(_make_entity(entity_id="s_nomatch", properties={"name": "Banana", "description": "fruit"}))
        ctx = SearchContext(query="zzznomatch999")
        results = store.semantic_search("zzznomatch999", ctx)
        assert results == []

    def test_matches_entity_id_directly(self, store: PersistentJSONKnowledgeStore) -> None:
        store.store_entity(_make_entity(entity_id="unique_entity_xyz"))
        ctx = SearchContext(query="unique_entity_xyz")
        results = store.semantic_search("unique_entity_xyz", ctx)
        assert any(e.entity_id == "unique_entity_xyz" for e in results)


# ---------------------------------------------------------------------------
# get_graph_statistics
# ---------------------------------------------------------------------------


class TestGetGraphStatistics:
    def test_empty_store(self, store: PersistentJSONKnowledgeStore) -> None:
        stats = store.get_graph_statistics()
        assert stats["total_entities"] == 0
        assert stats["total_relationships"] == 0

    def test_counts_entities_correctly(self, store: PersistentJSONKnowledgeStore) -> None:
        store.store_entity(_make_entity(entity_id="stat_a"))
        store.store_entity(_make_entity(entity_id="stat_b"))
        stats = store.get_graph_statistics()
        assert stats["total_entities"] == 2

    def test_entity_counts_by_type(self, store: PersistentJSONKnowledgeStore) -> None:
        store.store_entity(_make_entity(entity_id="sc_concept", entity_type=EntityType.CONCEPT))
        store.store_entity(_make_entity(entity_id="sc_agent", entity_type=EntityType.AGENT))
        stats = store.get_graph_statistics()
        assert stats["entity_counts"].get("Concept") == 1
        assert stats["entity_counts"].get("Agent") == 1

    def test_storage_path_in_stats(self, store: PersistentJSONKnowledgeStore) -> None:
        stats = store.get_graph_statistics()
        assert "storage_path" in stats
        assert stats["storage_path"]  # non-empty


# ---------------------------------------------------------------------------
# export_graph_visualization
# ---------------------------------------------------------------------------


class TestExportGraphVisualization:
    def test_returns_nodes_and_edges_keys(self, store: PersistentJSONKnowledgeStore) -> None:
        result = store.export_graph_visualization()
        assert "nodes" in result
        assert "edges" in result

    def test_nodes_contain_expected_fields(self, store: PersistentJSONKnowledgeStore) -> None:
        store.store_entity(_make_entity(entity_id="vis_a", properties={"name": "Vis Entity", "description": "Desc"}))
        result = store.export_graph_visualization()
        assert len(result["nodes"]) == 1
        node = result["nodes"][0]
        assert node["id"] == "vis_a"
        assert node["label"] == "Vis Entity"
        assert "entity_type" in node

    def test_max_nodes_truncation(self, store: PersistentJSONKnowledgeStore) -> None:
        for i in range(5):
            store.store_entity(_make_entity(entity_id=f"vis_{i}", properties={"name": f"E{i}"}))
        result = store.export_graph_visualization(max_nodes=3)
        assert len(result["nodes"]) == 3
        assert result["truncated"] is True

    def test_no_truncation_when_under_limit(self, store: PersistentJSONKnowledgeStore) -> None:
        store.store_entity(_make_entity(entity_id="vis_only"))
        result = store.export_graph_visualization(max_nodes=10)
        assert result["truncated"] is False

    def test_edges_excluded_when_endpoints_truncated(self, store: PersistentJSONKnowledgeStore) -> None:
        for i in range(4):
            store.store_entity(_make_entity(entity_id=f"trunc_{i}"))
        store.create_relationship(EntityId("trunc_0"), EntityId("trunc_3"), RelationType.RELATED_TO)
        result = store.export_graph_visualization(max_nodes=2)
        assert result["edges"] == []


# ---------------------------------------------------------------------------
# connect / disconnect roundtrip
# ---------------------------------------------------------------------------


class TestConnectDisconnectRoundtrip:
    def test_data_persists_across_reconnect(self, store_class_and_path) -> None:
        cls, path = store_class_and_path
        s1 = cls(storage_path=path)
        s1.connect()
        s1.store_entity(_make_entity(entity_id="persist_me", properties={"name": "Persist"}))
        s1.disconnect()

        s2 = cls(storage_path=path)
        s2.connect()
        fetched = s2.get_entity(EntityId("persist_me"))
        assert fetched is not None
        assert fetched.properties["name"] == "Persist"
        s2.disconnect()

    def test_relationships_persist_across_reconnect(self, store_class_and_path) -> None:
        cls, path = store_class_and_path
        s1 = cls(storage_path=path)
        s1.connect()
        s1.store_entity(_make_entity(entity_id="rp_a"))
        s1.store_entity(_make_entity(entity_id="rp_b"))
        s1.create_relationship(EntityId("rp_a"), EntityId("rp_b"), RelationType.DEPENDS_ON)
        s1.disconnect()

        s2 = cls(storage_path=path)
        s2.connect()
        stats = s2.get_graph_statistics()
        assert stats["total_relationships"] == 1
        s2.disconnect()

    def test_connect_on_missing_file_starts_empty(self, store_class_and_path) -> None:
        cls, path = store_class_and_path
        s = cls(storage_path=path)
        s.connect()
        stats = s.get_graph_statistics()
        assert stats["total_entities"] == 0

    def test_context_manager(self, store_class_and_path) -> None:
        cls, path = store_class_and_path
        with cls(storage_path=path) as s:
            s.store_entity(_make_entity(entity_id="ctx_e"))
        with cls(storage_path=path) as s:
            assert s.get_entity(EntityId("ctx_e")) is not None
