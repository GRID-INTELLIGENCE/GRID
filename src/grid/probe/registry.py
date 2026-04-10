"""Entity registry — central store for discovered governance entities.

The registry holds all entities (both seed and discovered), provides
lookup by ID, domain, and type, and tracks the entity map used for
probe reports and dependency graphs.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime
from typing import Any

from grid.probe.models import (
    Domain,
    Entity,
    EntityType,
)

logger = logging.getLogger(__name__)


class EntityRegistry:
    """Central registry for governance entities.

    Supports:
    - Registration of entities (seed or discovered)
    - Lookup by ID, domain, or type
    - Entity map export (matching probe-entity-map.schema.json)
    - Deduplication by entity ID
    """

    def __init__(self) -> None:
        self._entities: dict[str, Entity] = {}
        self._by_domain: dict[Domain, list[str]] = defaultdict(list)
        self._by_type: dict[EntityType, list[str]] = defaultdict(list)

    def register(self, entity: Entity) -> bool:
        """Register an entity. Returns True if new, False if duplicate.

        Args:
            entity: The entity to register.

        Returns:
            True if the entity was newly registered, False if already existed.
        """
        if entity.id in self._entities:
            logger.debug("Entity %s already registered, skipping", entity.id)
            return False

        self._entities[entity.id] = entity
        self._by_domain[entity.domain].append(entity.id)
        self._by_type[entity.type].append(entity.id)
        return True

    def register_many(self, entities: list[Entity]) -> int:
        """Register multiple entities. Returns count of newly registered."""
        return sum(1 for e in entities if self.register(e))

    def get(self, entity_id: str) -> Entity | None:
        """Look up an entity by ID."""
        return self._entities.get(entity_id)

    def get_by_domain(self, domain: Domain) -> list[Entity]:
        """Get all entities in a domain."""
        return [self._entities[eid] for eid in self._by_domain.get(domain, [])]

    def get_by_type(self, entity_type: EntityType) -> list[Entity]:
        """Get all entities of a given type."""
        return [self._entities[eid] for eid in self._by_type.get(entity_type, [])]

    def all_entities(self) -> list[Entity]:
        """Get all registered entities."""
        return list(self._entities.values())

    @property
    def count(self) -> int:
        """Total entity count."""
        return len(self._entities)

    @property
    def domains(self) -> list[Domain]:
        """Domains with registered entities."""
        return list(self._by_domain.keys())

    def to_entity_map(self) -> dict[str, Any]:
        """Export as entity map matching probe-entity-map.schema.json.

        Returns:
            Dictionary conforming to the probe-entity-map schema.
        """
        entities_dict: dict[str, Any] = {}
        for eid, entity in self._entities.items():
            entry: dict[str, Any] = {
                "label": entity.label,
                "type": entity.type.value,
                "domain": entity.domain.value,
                "source": entity.source,
                "discovered_by": entity.discovered_by.value,
            }
            if entity.class_name:
                entry["class_name"] = entity.class_name
            if entity.line_number:
                entry["line_number"] = entity.line_number
            if entity.description:
                entry["description"] = entity.description
            if entity.execution_order:
                entry["execution_order"] = entity.execution_order
            if entity.conditional:
                entry["conditional"] = True
                if entity.condition_flag:
                    entry["condition_flag"] = entity.condition_flag
            if entity.critical:
                entry["critical"] = True
            if entity.dependencies:
                entry["dependencies"] = list(entity.dependencies)
            entities_dict[eid] = entry

        # Build domain summary
        domains_dict: dict[str, Any] = {}
        for domain, eids in self._by_domain.items():
            domains_dict[domain.value] = {
                "entity_count": len(eids),
                "entity_ids": list(eids),
            }

        return {
            "schema_version": "probe-entities/1.0",
            "generated_at": datetime.now().isoformat(),
            "entity_count": self.count,
            "entities": entities_dict,
            "domains": domains_dict,
        }
