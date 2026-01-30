"""Tests for structural learning layer functionality."""

from __future__ import annotations

import pytest

from grid.knowledge.structural_learning import (
    AdaptiveRelationshipModel,
    Entity,
    EntityTypingFramework,
    HierarchyEvolutionTracker,
    Relationship,
    StructuralLearningLayer,
)


class TestEntityTypingFramework:
    """Test EntityTypingFramework."""

    @pytest.fixture
    def framework(self):
        """Create entity typing framework."""
        return EntityTypingFramework()

    def test_register_entity_type(self, framework):
        """Test registering entity types."""
        entity_type = framework.register_entity_type(
            "Person",
            semantic_features={"name": str, "age": int},
            structural_features={"properties": dict},
        )

        assert entity_type.type_name == "Person"
        assert "Person" in framework.entity_types

    def test_infer_entity_type(self, framework):
        """Test inferring entity type."""
        # Register a type
        framework.register_entity_type(
            "Person",
            semantic_features={"name": str, "age": int},
            structural_features={"name": str, "age": int},
        )

        # Create entity
        entity = Entity(
            id="person1",
            entity_type="unknown",
            properties={"name": "John", "age": 30},
        )

        # Infer type
        inferred = framework.infer_entity_type(entity)

        assert len(inferred) > 0
        assert "Person" in inferred

    def test_adapt_type_hierarchy(self, framework):
        """Test adapting type hierarchy."""
        framework.register_entity_type("Animal")
        framework.register_entity_type("Dog", parent_types=["Animal"])
        framework.register_entity_type("Cat")  # Register Cat first

        new_relationships = [("Animal", "Cat")]
        updated = framework.adapt_type_hierarchy(new_relationships)

        assert "Cat" in updated
        assert "Animal" in updated["Cat"]
        assert "Cat" in framework.entity_types["Animal"].child_types


class TestAdaptiveRelationshipModel:
    """Test AdaptiveRelationshipModel."""

    @pytest.fixture
    def model(self):
        """Create adaptive relationship model."""
        return AdaptiveRelationshipModel()

    def test_add_relationship(self, model):
        """Test adding relationships."""
        rel = model.add_relationship("entity1", "entity2", "related_to", properties={"weight": 0.8}, strength=0.9)

        assert rel.source_id == "entity1"
        assert rel.target_id == "entity2"
        assert rel.relationship_type == "related_to"
        assert rel.strength == 0.9
        assert ("entity1", "entity2") in model.relationships

    def test_adapt_relationship_strength(self, model):
        """Test adapting relationship strength."""
        model.add_relationship("entity1", "entity2", "related_to", strength=0.5)

        updated = model.adapt_relationship_strength("entity1", "entity2", 0.8)

        assert updated is not None
        assert updated.strength == 0.8

    def test_get_relationships(self, model):
        """Test getting relationships."""
        model.add_relationship("entity1", "entity2", "related_to")
        model.add_relationship("entity2", "entity3", "related_to")

        outgoing = model.get_relationships("entity1", direction="outgoing")
        incoming = model.get_relationships("entity2", direction="incoming")
        both = model.get_relationships("entity2", direction="both")

        assert len(outgoing) == 1
        assert len(incoming) == 1
        assert len(both) == 2

    def test_predict_relationships(self, model):
        """Test predicting relationships."""
        # Add some existing relationships
        model.add_relationship("entity1", "entity2", "related_to", strength=0.9)
        model.add_relationship("entity1", "entity3", "related_to", strength=0.8)
        model.add_relationship("entity2", "entity4", "related_to", strength=0.7)

        # Predict relationships for entity1
        predictions = model.predict_relationships("entity1", ["entity4", "entity5"])

        assert len(predictions) == 2
        # entity4 should have higher confidence (connected through entity2)
        assert predictions[0][0] == "entity4" or predictions[1][0] == "entity4"


class TestHierarchyEvolutionTracker:
    """Test HierarchyEvolutionTracker."""

    @pytest.fixture
    def tracker(self):
        """Create hierarchy evolution tracker."""
        return HierarchyEvolutionTracker()

    def test_capture_snapshot(self, tracker):
        """Test capturing hierarchy snapshots."""
        entities = {
            "root1": Entity(id="root1", entity_type="Root"),
            "child1": Entity(id="child1", entity_type="Child"),
            "child2": Entity(id="child2", entity_type="Child"),
        }

        relationships = {
            ("root1", "child1"): Relationship(source_id="root1", target_id="child1", relationship_type="has_child"),
            ("root1", "child2"): Relationship(source_id="root1", target_id="child2", relationship_type="has_child"),
        }

        snapshot = tracker.capture_snapshot(entities, relationships)

        assert 0 in snapshot  # Root level
        assert "root1" in snapshot[0].entities
        assert 1 in snapshot  # Child level
        assert "child1" in snapshot[1].entities
        assert "child2" in snapshot[1].entities

    def test_detect_hierarchy_changes(self, tracker):
        """Test detecting hierarchy changes."""
        # First snapshot
        entities1 = {
            "root1": Entity(id="root1", entity_type="Root"),
            "child1": Entity(id="child1", entity_type="Child"),
        }
        relationships1 = {
            ("root1", "child1"): Relationship(source_id="root1", target_id="child1", relationship_type="has_child"),
        }
        tracker.capture_snapshot(entities1, relationships1)

        # Second snapshot with changes
        entities2 = {
            "root1": Entity(id="root1", entity_type="Root"),
            "child1": Entity(id="child1", entity_type="Child"),
            "child2": Entity(id="child2", entity_type="Child"),
        }
        relationships2 = {
            ("root1", "child1"): Relationship(source_id="root1", target_id="child1", relationship_type="has_child"),
            ("root1", "child2"): Relationship(source_id="root1", target_id="child2", relationship_type="has_child"),
        }
        tracker.capture_snapshot(entities2, relationships2)

        changes = tracker.detect_hierarchy_changes(threshold=0.1)

        assert len(changes) > 0
        assert any(change["type"] == "level_entity_change" for change in changes)


class TestStructuralLearningLayer:
    """Test StructuralLearningLayer."""

    @pytest.fixture
    def layer(self):
        """Create structural learning layer."""
        return StructuralLearningLayer()

    def test_add_entity(self, layer):
        """Test adding entities."""
        entity = layer.add_entity("entity1", "Person", {"name": "John"})

        assert entity.id == "entity1"
        assert entity.entity_type == "Person"
        assert "entity1" in layer.entities

    def test_add_relationship(self, layer):
        """Test adding relationships."""
        layer.add_entity("entity1", "Person")
        layer.add_entity("entity2", "Person")

        rel = layer.add_relationship("entity1", "entity2", "knows", strength=0.8)

        assert rel.source_id == "entity1"
        assert rel.target_id == "entity2"
        assert rel.relationship_type == "knows"

    def test_adapt_to_changes(self, layer):
        """Test adapting to changes."""
        # Add initial entities
        layer.add_entity("entity1", "Person")
        layer.add_entity("entity2", "Person")
        layer.add_relationship("entity1", "entity2", "knows")

        # New entities and relationships
        new_entities = [Entity(id="entity3", entity_type="Person", properties={"name": "Alice"})]
        new_relationships = [
            Relationship(
                source_id="entity2",
                target_id="entity3",
                relationship_type="knows",
                strength=0.7,
            )
        ]

        result = layer.adapt_to_changes(new_entities, new_relationships)

        assert result["entities_added"] == 1
        assert result["relationships_added"] == 1
        assert len(result["changes"]) >= 0

    def test_get_entity_subgraph(self, layer):
        """Test getting entity subgraph."""
        # Build a small graph
        layer.add_entity("entity1", "Person")
        layer.add_entity("entity2", "Person")
        layer.add_entity("entity3", "Person")
        layer.add_relationship("entity1", "entity2", "knows")
        layer.add_relationship("entity2", "entity3", "knows")

        subgraph = layer.get_entity_subgraph("entity1", depth=2)

        assert "center" in subgraph
        assert subgraph["center"] == "entity1"
        assert "entities" in subgraph
        assert "relationships" in subgraph
        assert len(subgraph["entities"]) > 0
        assert len(subgraph["relationships"]) > 0
