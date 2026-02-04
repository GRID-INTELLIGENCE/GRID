"""Structural learning layer for knowledge graph adaptation.

This module implements knowledge graph entity typing, adaptive relationship
modeling, and hierarchy evolution tracking for the Embedded Agentic Knowledge System.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Entity:
    """Represents a knowledge graph entity."""

    id: str
    entity_type: str
    properties: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def update_properties(self, new_properties: dict[str, Any]) -> None:
        """Update entity properties."""
        self.properties.update(new_properties)
        self.updated_at = datetime.now()


@dataclass
class Relationship:
    """Represents a relationship between entities."""

    source_id: str
    target_id: str
    relationship_type: str
    properties: dict[str, Any] = field(default_factory=dict)
    strength: float = 1.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def update_strength(self, new_strength: float) -> None:
        """Update relationship strength."""
        self.strength = max(0.0, min(1.0, new_strength))
        self.updated_at = datetime.now()


@dataclass
class HierarchyLevel:
    """Represents a level in a hierarchy."""

    level: int
    entities: set[str] = field(default_factory=set)
    relationships: set[tuple[str, str]] = field(default_factory=set)


@dataclass
class EntityType:
    """Represents an entity type with semantic and structural knowledge."""

    type_name: str
    semantic_features: dict[str, Any] = field(default_factory=dict)
    structural_features: dict[str, Any] = field(default_factory=dict)
    parent_types: list[str] = field(default_factory=list)
    child_types: list[str] = field(default_factory=list)


class EntityTypingFramework:
    """Framework for entity typing with semantic and structural knowledge."""

    def __init__(self) -> None:
        self.entity_types: dict[str, EntityType] = {}
        self.type_hierarchy: dict[str, list[str]] = {}  # type -> [parent_types]

    def register_entity_type(
        self,
        type_name: str,
        semantic_features: dict[str, Any] | None = None,
        structural_features: dict[str, Any] | None = None,
        parent_types: list[str] | None = None,
    ) -> EntityType:
        """Register a new entity type.

        Args:
            type_name: Name of the entity type
            semantic_features: Semantic characteristics
            structural_features: Structural characteristics
            parent_types: Parent types in hierarchy

        Returns:
            Created EntityType
        """
        entity_type = EntityType(
            type_name=type_name,
            semantic_features=semantic_features or {},
            structural_features=structural_features or {},
            parent_types=parent_types or [],
        )

        self.entity_types[type_name] = entity_type
        self.type_hierarchy[type_name] = parent_types or []

        # Update parent-child relationships
        for parent in parent_types or []:
            if parent in self.entity_types:
                if type_name not in self.entity_types[parent].child_types:
                    self.entity_types[parent].child_types.append(type_name)

        logger.info(f"Registered entity type: {type_name}")

        return entity_type

    def infer_entity_type(self, entity: Entity, context: dict[str, Any] | None = None) -> list[str]:
        """Infer entity type from properties and context.

        Args:
            entity: Entity to type
            context: Optional context for typing

        Returns:
            List of inferred type names (ordered by confidence)
        """
        scores: dict[str, float] = {}

        for type_name, entity_type in self.entity_types.items():
            score = 0.0

            # Semantic matching
            semantic_match = self._match_semantic_features(entity.properties, entity_type.semantic_features)
            score += semantic_match * 0.5

            # Structural matching
            structural_match = self._match_structural_features(entity.properties, entity_type.structural_features)
            score += structural_match * 0.5

            scores[type_name] = score

        # Sort by score and return top types
        sorted_types = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [type_name for type_name, score in sorted_types if score > 0.3]

    def _match_semantic_features(self, properties: dict[str, Any], semantic_features: dict[str, Any]) -> float:
        """Match semantic features."""
        if not semantic_features:
            return 0.0

        matches = 0
        total = len(semantic_features)

        for key, value in semantic_features.items():
            if key in properties:
                if isinstance(value, (int, float)):
                    # Numeric comparison
                    prop_val = properties[key]
                    if isinstance(prop_val, (int, float)):
                        if abs(prop_val - value) < 0.1:
                            matches += 1
                else:
                    # String/other comparison
                    if properties[key] == value:
                        matches += 1

        return matches / total if total > 0 else 0.0

    def _match_structural_features(self, properties: dict[str, Any], structural_features: dict[str, Any]) -> float:
        """Match structural features."""
        if not structural_features:
            return 0.0

        matches = 0
        total = len(structural_features)

        for key, expected_type in structural_features.items():
            if key in properties:
                prop_value = properties[key]
                if isinstance(expected_type, type):
                    if isinstance(prop_value, expected_type):
                        matches += 1
                elif isinstance(expected_type, str):
                    # Type name matching
                    if expected_type.lower() in str(type(prop_value)).lower():
                        matches += 1

        return matches / total if total > 0 else 0.0

    def adapt_type_hierarchy(self, new_relationships: list[tuple[str, str]]) -> dict[str, list[str]]:
        """Adapt type hierarchy based on new relationships.

        Args:
            new_relationships: List of (parent_type, child_type) relationships

        Returns:
            Updated type hierarchy
        """
        for parent, child in new_relationships:
            if parent in self.entity_types and child in self.entity_types:
                # Add parent-child relationship
                if child not in self.entity_types[parent].child_types:
                    self.entity_types[parent].child_types.append(child)
                if parent not in self.entity_types[child].parent_types:
                    self.entity_types[child].parent_types.append(parent)

                # Update hierarchy
                if child not in self.type_hierarchy:
                    self.type_hierarchy[child] = []
                if parent not in self.type_hierarchy[child]:
                    self.type_hierarchy[child].append(parent)

        return self.type_hierarchy


class AdaptiveRelationshipModel:
    """Model for adaptive relationship modeling."""

    def __init__(self) -> None:
        self.relationships: dict[tuple[str, str], Relationship] = {}
        self.relationship_history: list[Relationship] = []

    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        properties: dict[str, Any] | None = None,
        strength: float = 1.0,
    ) -> Relationship:
        """Add or update a relationship.

        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            relationship_type: Type of relationship
            properties: Optional relationship properties
            strength: Relationship strength (0.0-1.0)

        Returns:
            Created or updated Relationship
        """
        key = (source_id, target_id)

        if key in self.relationships:
            # Update existing relationship
            rel = self.relationships[key]
            rel.relationship_type = relationship_type
            rel.update_strength(strength)
            if properties:
                rel.properties.update(properties)
        else:
            # Create new relationship
            rel = Relationship(
                source_id=source_id,
                target_id=target_id,
                relationship_type=relationship_type,
                properties=properties or {},
                strength=strength,
            )
            self.relationships[key] = rel
            self.relationship_history.append(rel)

        logger.info(f"Relationship {relationship_type} ({source_id} -> {target_id}): strength={strength:.2f}")

        return rel

    def adapt_relationship_strength(self, source_id: str, target_id: str, new_strength: float) -> Relationship | None:
        """Adapt relationship strength based on interactions.

        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            new_strength: New strength value

        Returns:
            Updated Relationship or None if not found
        """
        key = (source_id, target_id)
        if key in self.relationships:
            rel = self.relationships[key]
            old_strength = rel.strength
            rel.update_strength(new_strength)

            logger.info(f"Adapted relationship ({source_id} -> {target_id}): {old_strength:.2f} -> {new_strength:.2f}")

            return rel

        return None

    def get_relationships(self, entity_id: str, direction: str = "both") -> list[Relationship]:
        """Get relationships for an entity.

        Args:
            entity_id: Entity ID
            direction: "outgoing", "incoming", or "both"

        Returns:
            List of relationships
        """
        relationships = []

        for (source_id, target_id), rel in self.relationships.items():
            if direction == "outgoing" and source_id == entity_id:
                relationships.append(rel)
            elif direction == "incoming" and target_id == entity_id:
                relationships.append(rel)
            elif direction == "both" and (source_id == entity_id or target_id == entity_id):
                relationships.append(rel)

        return relationships

    def predict_relationships(self, entity_id: str, candidate_ids: list[str]) -> list[tuple[str, float]]:
        """Predict potential relationships using unsupervised methods.

        Args:
            entity_id: Entity ID
            candidate_ids: Candidate entity IDs

        Returns:
            List of (candidate_id, confidence_score) tuples
        """
        predictions: list[tuple[str, float]] = []

        # Get existing relationships
        existing_rels = self.get_relationships(entity_id, direction="both")
        existing_ids = {rel.target_id if rel.source_id == entity_id else rel.source_id for rel in existing_rels}

        for candidate_id in candidate_ids:
            if candidate_id == entity_id:
                continue

            # Calculate confidence based on:
            # 1. Similarity to existing relationships
            # 2. Structural patterns
            confidence = 0.0

            # Check if similar entities have relationships
            candidate_rels = self.get_relationships(candidate_id, direction="both")
            common_entities = existing_ids & {
                rel.target_id if rel.source_id == candidate_id else rel.source_id for rel in candidate_rels
            }

            if common_entities:
                confidence = min(len(common_entities) / 5.0, 1.0)

            predictions.append((candidate_id, confidence))

        # Sort by confidence
        predictions.sort(key=lambda x: x[1], reverse=True)

        return predictions


class HierarchyEvolutionTracker:
    """Tracks hierarchy evolution over time."""

    def __init__(self) -> None:
        self.hierarchy_snapshots: list[dict[int, HierarchyLevel]] = []
        self.evolution_history: list[dict[str, Any]] = []

    def capture_snapshot(
        self, entities: dict[str, Entity], relationships: dict[tuple[str, str], Relationship]
    ) -> dict[int, HierarchyLevel]:
        """Capture a snapshot of the current hierarchy.

        Args:
            entities: Dictionary of entities
            relationships: Dictionary of relationships

        Returns:
            Hierarchy snapshot by level
        """
        # Build hierarchy levels
        levels: dict[int, HierarchyLevel] = {}

        # Find root entities (entities with no incoming relationships)
        root_entities = set(entities.keys())
        for (source_id, target_id), _rel in relationships.items():
            if target_id in root_entities:
                root_entities.remove(target_id)

        # Level 0: root entities
        levels[0] = HierarchyLevel(level=0, entities=root_entities)

        # Build subsequent levels
        current_level = 0
        processed = root_entities.copy()

        while True:
            next_level_entities: set[str] = set()
            next_level_relationships: set[tuple[str, str]] = set()

            for entity_id in levels[current_level].entities:
                # Find children
                for (source_id, target_id), _rel in relationships.items():
                    if source_id == entity_id and target_id not in processed:
                        next_level_entities.add(target_id)
                        next_level_relationships.add((source_id, target_id))
                        processed.add(target_id)

            if not next_level_entities:
                break

            current_level += 1
            levels[current_level] = HierarchyLevel(
                level=current_level,
                entities=next_level_entities,
                relationships=next_level_relationships,
            )

        self.hierarchy_snapshots.append(levels)

        logger.info(f"Captured hierarchy snapshot: {len(levels)} levels, {len(processed)} entities")

        return levels

    def detect_hierarchy_changes(self, threshold: float = 0.2) -> list[dict[str, Any]]:
        """Detect significant hierarchy changes.

        Args:
            threshold: Change threshold (0.0-1.0)

        Returns:
            List of detected changes
        """
        if len(self.hierarchy_snapshots) < 2:
            return []

        changes = []
        previous = self.hierarchy_snapshots[-2]
        current = self.hierarchy_snapshots[-1]

        # Compare levels
        previous_levels = set(previous.keys())
        current_levels = set(current.keys())

        # New or removed levels
        new_levels = current_levels - previous_levels
        removed_levels = previous_levels - current_levels

        if new_levels:
            changes.append(
                {
                    "type": "new_levels",
                    "levels": list(new_levels),
                    "timestamp": datetime.now().isoformat(),
                }
            )

        if removed_levels:
            changes.append(
                {
                    "type": "removed_levels",
                    "levels": list(removed_levels),
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # Compare entities at each level
        for level in previous_levels & current_levels:
            prev_entities = previous[level].entities
            curr_entities = current[level].entities

            entity_change = len(curr_entities ^ prev_entities) / max(len(prev_entities | curr_entities), 1)

            if entity_change > threshold:
                changes.append(
                    {
                        "type": "level_entity_change",
                        "level": level,
                        "change_ratio": entity_change,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        if changes:
            self.evolution_history.extend(changes)

        return changes


class StructuralLearningLayer:
    """Main structural learning layer combining all components."""

    def __init__(self) -> None:
        self.entity_typing = EntityTypingFramework()
        self.relationship_model = AdaptiveRelationshipModel()
        self.hierarchy_tracker = HierarchyEvolutionTracker()
        self.entities: dict[str, Entity] = {}

    def add_entity(
        self,
        entity_id: str,
        entity_type: str | None = None,
        properties: dict[str, Any] | None = None,
    ) -> Entity:
        """Add an entity to the knowledge graph.

        Args:
            entity_id: Entity ID
            entity_type: Optional entity type
            properties: Optional entity properties

        Returns:
            Created Entity
        """
        entity = Entity(
            id=entity_id,
            entity_type=entity_type or "unknown",
            properties=properties or {},
        )

        # Infer type if not provided
        if entity_type is None:
            inferred_types = self.entity_typing.infer_entity_type(entity)
            if inferred_types:
                entity.entity_type = inferred_types[0]

        self.entities[entity_id] = entity

        logger.info(f"Added entity: {entity_id} (type: {entity.entity_type})")

        return entity

    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        properties: dict[str, Any] | None = None,
        strength: float = 1.0,
    ) -> Relationship:
        """Add a relationship between entities.

        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            relationship_type: Relationship type
            properties: Optional relationship properties
            strength: Relationship strength

        Returns:
            Created Relationship
        """
        # Ensure entities exist
        if source_id not in self.entities:
            self.add_entity(source_id)
        if target_id not in self.entities:
            self.add_entity(target_id)

        return self.relationship_model.add_relationship(source_id, target_id, relationship_type, properties, strength)

    def adapt_to_changes(self, new_entities: list[Entity], new_relationships: list[Relationship]) -> dict[str, Any]:
        """Adapt knowledge graph to new entities and relationships.

        Args:
            new_entities: List of new entities
            new_relationships: List of new relationships

        Returns:
            Adaptation summary
        """
        # Add new entities
        for entity in new_entities:
            self.entities[entity.id] = entity

        # Add new relationships
        for rel in new_relationships:
            self.relationship_model.relationships[(rel.source_id, rel.target_id)] = rel

        # Capture hierarchy snapshot
        snapshot = self.hierarchy_tracker.capture_snapshot(self.entities, self.relationship_model.relationships)

        # Detect changes
        changes = self.hierarchy_tracker.detect_hierarchy_changes()

        # Adapt type hierarchy
        type_relationships = [
            (self.entities[rel.source_id].entity_type, self.entities[rel.target_id].entity_type)
            for rel in new_relationships
            if rel.source_id in self.entities and rel.target_id in self.entities
        ]
        updated_hierarchy = self.entity_typing.adapt_type_hierarchy(type_relationships)

        logger.info(
            f"Adapted to changes: {len(new_entities)} entities, "
            f"{len(new_relationships)} relationships, {len(changes)} changes detected"
        )

        return {
            "entities_added": len(new_entities),
            "relationships_added": len(new_relationships),
            "hierarchy_levels": len(snapshot),
            "changes_detected": len(changes),
            "changes": changes,
            "updated_hierarchy": updated_hierarchy,
        }

    def get_entity_subgraph(self, entity_id: str, depth: int = 2) -> dict[str, Any]:
        """Get subgraph around an entity.

        Args:
            entity_id: Entity ID
            depth: Depth of subgraph

        Returns:
            Subgraph representation
        """
        if entity_id not in self.entities:
            return {}

        subgraph = {
            "center": entity_id,
            "entities": {},
            "relationships": [],
        }

        visited: set[str] = {entity_id}
        current_level: set[str] = {entity_id}

        for _level in range(depth):
            next_level: set[str] = set()

            for entity_id in current_level:
                if entity_id in self.entities:
                    subgraph["entities"][entity_id] = {
                        "type": self.entities[entity_id].entity_type,
                        "properties": self.entities[entity_id].properties,
                    }

                # Get relationships
                rels = self.relationship_model.get_relationships(entity_id, direction="both")
                for rel in rels:
                    other_id = rel.target_id if rel.source_id == entity_id else rel.source_id
                    if other_id not in visited:
                        next_level.add(other_id)
                        visited.add(other_id)

                    subgraph["relationships"].append(
                        {
                            "source": rel.source_id,
                            "target": rel.target_id,
                            "type": rel.relationship_type,
                            "strength": rel.strength,
                        }
                    )

            current_level = next_level
            if not current_level:
                break

        return subgraph
