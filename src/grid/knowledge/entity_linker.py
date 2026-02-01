"""
Cross-Project Entity Linking - Normalizing and linking entities across namespaces.
"""

import logging
import re

from unified_fabric.cross_project_validator import get_policy_validator

from .graph_schema import RelationType
from .graph_store import Entity, EntityId
from .persistent_store import PersistentJSONKnowledgeStore

logger = logging.getLogger(__name__)


class EntityLinker:
    """
    Handles linking of entities across different project namespaces.
    Ensures that 'StrategicReasoningLibrary' in one project is recognized
    as the 'SAME_AS' 'StrategicReasoningLibrary' in another.
    """

    def __init__(self, store: PersistentJSONKnowledgeStore):
        self.store = store
        self.validator = get_policy_validator()

    def normalize_name(self, name: str) -> str:
        """Normalize entity name for comparison."""
        # Remove special chars and lowercase
        return re.sub(r"[^a-zA-Z0-9]", "", name).lower()

    def find_potential_matches(self, entity: Entity) -> list[Entity]:
        """Find potential duplicate entities in the store."""
        matches = []
        target_name = self.normalize_name(entity.properties.get("name", ""))

        if not target_name:
            return []

        for other_id, other_entity in self.store.entities.items():
            if other_id == entity.entity_id:
                continue

            # 1. Name Match
            other_name = self.normalize_name(other_entity.properties.get("name", ""))
            if target_name == other_name and entity.entity_type == other_entity.entity_type:
                matches.append(other_entity)
                continue

            # 2. Property Overlap (e.g., same external ID or slug)
            for prop in ["id", "slug", "external_id"]:
                if prop in entity.properties and prop in other_entity.properties:
                    if entity.properties[prop] == other_entity.properties[prop]:
                        matches.append(other_entity)
                        break

        return matches

    def link_entities(self, entity_a: Entity, entity_b: Entity, confidence: float = 1.0) -> bool:
        """Create a SAME_AS relationship between two entities if permitted."""
        # Validate cross-project policy
        project_a = entity_a.properties.get("project", "unknown")
        project_b = entity_b.properties.get("project", "unknown")

        # Basic check: are these allowed to talk?
        if project_a != project_b:
            validation = self.validator.validate_context({"project": project_a, "target_project": project_b})
            if not validation.allowed:
                logger.warning(f"Policy blocked linking: {project_a} -> {project_b} ({validation.reason})")
                return False

        # Create relationships in both directions
        self.store.create_relationship(
            EntityId(entity_a.entity_id),
            EntityId(entity_b.entity_id),
            RelationType.RELATED_TO,
            properties={
                "link_type": "SAME_AS",
                "confidence": confidence,
                "reason": "Automatic name normalization match",
            },
        )

        logger.info(f"Linked entities: {entity_a.entity_id} <-> {entity_b.entity_id} ({confidence})")
        return True

    def process_new_entity(self, entity: Entity):
        """Scan for matches and link automatically for a new entity."""
        matches = self.find_potential_matches(entity)
        for match in matches:
            self.link_entities(entity, match)
