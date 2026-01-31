"""
Persistent JSON Knowledge Store for GRID.
Lightweight graph storage using local JSON files for persistence.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .graph_schema import (
    EntityType,
    RelationType,
    get_kg_schema,
)
from .graph_store import Entity, EntityId, Relationship, RelationshipId, SearchContext

logger = logging.getLogger(__name__)

class PersistentJSONKnowledgeStore:
    """
    JSON-based knowledge graph storage.
    Follows the Neo4jKnowledgeStore interface for ease of transition.
    """

    def __init__(self, storage_path: str | Path | None = None):
        if storage_path is None:
            # Default to a location in the project
            storage_path = Path("dev/knowledge_graph.json")
        
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.entities: dict[str, Entity] = {}
        self.relationships: dict[str, Relationship] = {}
        self._schema = get_kg_schema()
        self._initialized = False
        
        logger.info(f"PersistentJSONKnowledgeStore initialized at {self.storage_path}")

    def connect(self) -> None:
        """Load data from disk if available."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                # Hydrate entities
                for eid, edata in data.get("entities", {}).items():
                    self.entities[eid] = Entity(
                        entity_id=edata["entity_id"],
                        entity_type=EntityType(edata["entity_type"]),
                        properties=edata["properties"],
                        created_at=datetime.fromisoformat(edata["created_at"]),
                        updated_at=datetime.fromisoformat(edata["updated_at"]),
                        labels=set(edata.get("labels", [])),
                    )
                
                # Hydrate relationships
                for rid, rdata in data.get("relationships", {}).items():
                    self.relationships[rid] = Relationship(
                        relationship_id=rdata["relationship_id"],
                        from_entity_id=rdata["from_entity_id"],
                        to_entity_id=rdata["to_entity_id"],
                        relationship_type=RelationType(rdata["relationship_type"]),
                        properties=rdata["properties"],
                        created_at=datetime.fromisoformat(rdata["created_at"]),
                        updated_at=datetime.fromisoformat(rdata["updated_at"]),
                    )
                logger.info(f"Loaded {len(self.entities)} entities and {len(self.relationships)} relationships from disk.")
            except Exception as e:
                logger.error(f"Failed to load knowledge graph from {self.storage_path}: {e}")
        
        self._initialized = True

    def disconnect(self) -> None:
        """Save data to disk."""
        self._save_to_disk()

    def _save_to_disk(self) -> None:
        """Write current state to JSON."""
        try:
            data = {
                "entities": {eid: e.to_dict() for eid, e in self.entities.items()},
                "relationships": {rid: r.to_dict() for rid, r in self.relationships.items()},
                "last_updated": datetime.now().isoformat()
            }
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved knowledge graph to {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to save knowledge graph to disk: {e}")

    def store_entity(self, entity: Entity) -> EntityId:
        if not self._initialized:
            self.connect()
        
        # Schema validation
        is_valid, errors = self._schema.validate_entity(entity.entity_type, entity.properties)
        if not is_valid:
            raise ValueError(f"Entity validation failed: {errors}")
            
        self.entities[entity.entity_id] = entity
        self._save_to_disk()
        return EntityId(entity.entity_id)

    def create_relationship(
        self,
        from_id: EntityId,
        to_id: EntityId,
        relationship_type: RelationType,
        properties: dict[str, Any] | None = None,
    ) -> RelationshipId:
        if not self._initialized:
            self.connect()
        
        rel_id = str(uuid4())
        now = datetime.now()
        relationship = Relationship(
            relationship_id=rel_id,
            from_entity_id=from_id.value,
            to_entity_id=to_id.value,
            relationship_type=relationship_type,
            properties=properties or {},
            created_at=now,
            updated_at=now
        )
        self.relationships[rel_id] = relationship
        self._save_to_disk()
        return RelationshipId(rel_id)

    def get_entity(self, entity_id: EntityId) -> Entity | None:
        if not self._initialized:
            self.connect()
        return self.entities.get(entity_id.value)

    def semantic_search(self, query: str, context: SearchContext) -> list[Entity]:
        if not self._initialized:
            self.connect()
        # Simple implementation for JSON store
        results = []
        for entity in self.entities.values():
            if context.entity_types and entity.entity_type not in context.entity_types:
                continue
            
            # Simple keyword match in properties
            found = False
            for val in entity.properties.values():
                if query.lower() in str(val).lower():
                    found = True
                    break
            
            if found or query.lower() in entity.entity_id.lower():
                results.append(entity)
        
        # Sort and limit
        # ... logic omitted for brevity, but follows core patterns ...
        return results[:context.limit]

    def get_graph_statistics(self) -> dict[str, Any]:
        if not self._initialized:
            self.connect()
        entity_counts = {}
        for entity in self.entities.values():
            etype = entity.entity_type.value
            entity_counts[etype] = entity_counts.get(etype, 0) + 1
            
        rel_counts = {}
        for rel in self.relationships.values():
            rtype = rel.relationship_type.value
            rel_counts[rtype] = rel_counts.get(rtype, 0) + 1
            
        return {
            "total_entities": len(self.entities),
            "total_relationships": len(self.relationships),
            "entity_counts": entity_counts,
            "relationship_counts": rel_counts,
            "storage_path": str(self.storage_path)
        }

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
