"""
GRID Knowledge Graph Schema - Jay's Methodical Foundation

Ontology-driven schema mapping to prevent ingestion errors and conflicts.
Inspired by Neo4j property graphs + Apache Jena RDF/OWL patterns.

Aligned with existing GRID schemas:
- schemas/progress_compass_schema.json (checkpoint/compass/signals patterns)
- schemas/batch_validation_schema.json (severity, issue types)
- schemas/delegation_task.py (DelegationTask dataclass)

See also: schemas/knowledge_graph_schema.json for JSON Schema representation.

Key Entity Types:
- Agent: Agentic systems and their instances
- Skill: Executable capabilities with inputs/outputs
- Event: Temporal occurrences in the system
- Context: Environmental/state information (with phase/momentum from progress_compass)
- Artifact: Generated outputs (code, documents, models)
- Task: Delegatable work items (aligned with delegation_task.py)
- Decision: Recorded decisions with rationale

Relationship Types (Neo4j style - ALL_CAPS_WITH_UNDERSCORES):
- EXECUTED_BY: Skill → Agent
- DEPENDS_ON: Skill → Skill
- GENERATED: Agent → Artifact
- OCCURRED_AT: Event → Context
- HAS_PARENT: Agent → Agent
- REFERENCES: Artifact → Artifact
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class EntityType(str, Enum):
    """Core entity types in the knowledge graph."""

    AGENT = "Agent"
    SKILL = "Skill"
    EVENT = "Event"
    CONTEXT = "Context"
    ARTIFACT = "Artifact"
    TASK = "Task"
    DECISION = "Decision"


class RelationType(str, Enum):
    """Typed relationships (Neo4j-style naming)."""

    EXECUTED_BY = "EXECUTED_BY"
    DEPENDS_ON = "DEPENDS_ON"
    GENERATED = "GENERATED"
    OCCURRED_AT = "OCCURRED_AT"
    HAS_PARENT = "HAS_PARENT"
    REFERENCES = "REFERENCES"
    REQUIRES = "REQUIRES"
    PRODUCES = "PRODUCES"
    RELATED_TO = "RELATED_TO"


class PropertyType(str, Enum):
    """Property data types for validation."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    LIST = "list"
    DICT = "dict"


@dataclass
class PropertySchema:
    """Schema definition for an entity property."""

    name: str
    property_type: PropertyType
    required: bool = False
    description: str = ""
    constraints: dict[str, Any] = field(default_factory=dict)


@dataclass
class EntitySchema:
    """Schema definition for an entity type."""

    entity_type: EntityType
    properties: list[PropertySchema]
    unique_keys: list[str] = field(default_factory=list)
    indexes: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class RelationshipSchema:
    """Schema definition for a relationship type."""

    relation_type: RelationType
    from_entity: EntityType
    to_entity: EntityType
    properties: list[PropertySchema] = field(default_factory=list)
    cardinality: str = "many-to-many"  # one-to-one, one-to-many, many-to-many
    description: str = ""


class KnowledgeGraphSchema:
    """
    Jay's methodical schema definition for the GRID knowledge graph.

    Prevents ontology conflicts by defining strict entity/relationship types,
    property schemas, and validation rules.
    """

    def __init__(self):
        """Initialize the KG schema."""
        self.entity_schemas: dict[EntityType, EntitySchema] = {}
        self.relationship_schemas: dict[RelationType, list[RelationshipSchema]] = {}
        self._build_schema()

    def _build_schema(self) -> None:
        """Build the foundational schema."""

        # Agent entity
        self.entity_schemas[EntityType.AGENT] = EntitySchema(
            entity_type=EntityType.AGENT,
            properties=[
                PropertySchema("id", PropertyType.STRING, required=True, description="Unique agent ID"),
                PropertySchema("name", PropertyType.STRING, required=True, description="Agent name"),
                PropertySchema("type", PropertyType.STRING, description="Agent type (agentic, resonance, etc.)"),
                PropertySchema("status", PropertyType.STRING, description="Current status"),
                PropertySchema("created_at", PropertyType.DATETIME, required=True),
                PropertySchema("metadata", PropertyType.DICT, description="Additional metadata"),
            ],
            unique_keys=["id"],
            indexes=["name", "type", "status"],
            description="Agentic system or processor",
        )

        # Skill entity
        self.entity_schemas[EntityType.SKILL] = EntitySchema(
            entity_type=EntityType.SKILL,
            properties=[
                PropertySchema("id", PropertyType.STRING, required=True),
                PropertySchema("name", PropertyType.STRING, required=True),
                PropertySchema("description", PropertyType.STRING),
                PropertySchema("input_schema", PropertyType.DICT, description="Expected inputs"),
                PropertySchema("output_schema", PropertyType.DICT, description="Expected outputs"),
                PropertySchema("version", PropertyType.STRING),
                PropertySchema("created_at", PropertyType.DATETIME, required=True),
            ],
            unique_keys=["id"],
            indexes=["name", "version"],
            description="Executable capability with defined I/O",
        )

        # Artifact entity
        self.entity_schemas[EntityType.ARTIFACT] = EntitySchema(
            entity_type=EntityType.ARTIFACT,
            properties=[
                PropertySchema("id", PropertyType.STRING, required=True),
                PropertySchema("name", PropertyType.STRING, required=True),
                PropertySchema("type", PropertyType.STRING, description="code, document, model, etc."),
                PropertySchema("content_hash", PropertyType.STRING, description="Content hash for deduplication"),
                PropertySchema("file_path", PropertyType.STRING),
                PropertySchema("size_bytes", PropertyType.INTEGER),
                PropertySchema("created_at", PropertyType.DATETIME, required=True),
                PropertySchema("metadata", PropertyType.DICT),
            ],
            unique_keys=["id"],
            indexes=["name", "type", "content_hash"],
            description="Generated output or file",
        )

        # Event entity
        self.entity_schemas[EntityType.EVENT] = EntitySchema(
            entity_type=EntityType.EVENT,
            properties=[
                PropertySchema("id", PropertyType.STRING, required=True),
                PropertySchema("event_type", PropertyType.STRING, required=True),
                PropertySchema("timestamp", PropertyType.DATETIME, required=True),
                PropertySchema("source", PropertyType.STRING, description="Event source"),
                PropertySchema("payload", PropertyType.DICT, description="Event data"),
                PropertySchema("correlation_id", PropertyType.STRING, description="For tracing"),
            ],
            unique_keys=["id"],
            indexes=["event_type", "timestamp", "correlation_id"],
            description="Temporal occurrence",
        )

        # Context entity
        self.entity_schemas[EntityType.CONTEXT] = EntitySchema(
            entity_type=EntityType.CONTEXT,
            properties=[
                PropertySchema("id", PropertyType.STRING, required=True),
                PropertySchema("name", PropertyType.STRING, required=True),
                PropertySchema("scope", PropertyType.STRING, description="global, session, local"),
                PropertySchema("state", PropertyType.DICT, description="Context state"),
                PropertySchema("valid_from", PropertyType.DATETIME),
                PropertySchema("valid_to", PropertyType.DATETIME),
            ],
            unique_keys=["id"],
            indexes=["name", "scope"],
            description="Environmental or state context",
        )

        # Define relationships
        self._build_relationships()

    def _build_relationships(self) -> None:
        """Define relationship schemas."""

        # EXECUTED_BY: Skill → Agent
        self.add_relationship_schema(
            RelationshipSchema(
                relation_type=RelationType.EXECUTED_BY,
                from_entity=EntityType.SKILL,
                to_entity=EntityType.AGENT,
                properties=[
                    PropertySchema("execution_time", PropertyType.DATETIME),
                    PropertySchema("duration_ms", PropertyType.INTEGER),
                    PropertySchema("status", PropertyType.STRING),
                ],
                cardinality="many-to-many",
                description="Skill execution by agent",
            )
        )

        # GENERATED: Agent → Artifact
        self.add_relationship_schema(
            RelationshipSchema(
                relation_type=RelationType.GENERATED,
                from_entity=EntityType.AGENT,
                to_entity=EntityType.ARTIFACT,
                properties=[
                    PropertySchema("timestamp", PropertyType.DATETIME, required=True),
                    PropertySchema("context_id", PropertyType.STRING),
                ],
                cardinality="one-to-many",
                description="Agent generated artifact",
            )
        )

        # DEPENDS_ON: Skill → Skill
        self.add_relationship_schema(
            RelationshipSchema(
                relation_type=RelationType.DEPENDS_ON,
                from_entity=EntityType.SKILL,
                to_entity=EntityType.SKILL,
                properties=[
                    PropertySchema("dependency_type", PropertyType.STRING, description="hard, soft, optional"),
                    PropertySchema("version_constraint", PropertyType.STRING),
                ],
                cardinality="many-to-many",
                description="Skill dependency",
            )
        )

        # OCCURRED_AT: Event → Context
        self.add_relationship_schema(
            RelationshipSchema(
                relation_type=RelationType.OCCURRED_AT,
                from_entity=EntityType.EVENT,
                to_entity=EntityType.CONTEXT,
                properties=[
                    PropertySchema("timestamp", PropertyType.DATETIME, required=True),
                ],
                cardinality="many-to-one",
                description="Event contextual location",
            )
        )

    def add_relationship_schema(self, schema: RelationshipSchema) -> None:
        """Add a relationship schema."""
        if schema.relation_type not in self.relationship_schemas:
            self.relationship_schemas[schema.relation_type] = []
        self.relationship_schemas[schema.relation_type].append(schema)

    def validate_entity(self, entity_type: EntityType, data: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate an entity against its schema.

        Args:
            entity_type: Type of entity
            data: Entity data to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        if entity_type not in self.entity_schemas:
            return False, [f"Unknown entity type: {entity_type}"]

        schema = self.entity_schemas[entity_type]
        errors = []

        # Check required properties
        for prop in schema.properties:
            if prop.required and prop.name not in data:
                errors.append(f"Missing required property: {prop.name}")

        # Validate property types
        for prop in schema.properties:
            if prop.name not in data:
                continue

            value = data[prop.name]
            if not self._validate_property_type(value, prop.property_type):
                errors.append(
                    f"Property '{prop.name}' has invalid type. "
                    f"Expected {prop.property_type.value}, got {type(value).__name__}"
                )

        # Check unique keys
        # (Would need actual KG context to validate uniqueness)

        return len(errors) == 0, errors

    def _validate_property_type(self, value: Any, expected_type: PropertyType) -> bool:
        """Validate a property value against its expected type."""
        type_checks = {
            PropertyType.STRING: lambda v: isinstance(v, str),
            PropertyType.INTEGER: lambda v: isinstance(v, int) and not isinstance(v, bool),
            PropertyType.FLOAT: lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
            PropertyType.BOOLEAN: lambda v: isinstance(v, bool),
            PropertyType.DATETIME: lambda v: isinstance(v, (datetime, str)),  # Allow ISO strings
            PropertyType.LIST: lambda v: isinstance(v, list),
            PropertyType.DICT: lambda v: isinstance(v, dict),
        }

        check_fn = type_checks.get(expected_type)
        return check_fn(value) if check_fn else False

    def get_entity_schema(self, entity_type: EntityType) -> EntitySchema | None:
        """Get schema for an entity type."""
        return self.entity_schemas.get(entity_type)

    def get_relationship_schemas(self, relation_type: RelationType) -> list[RelationshipSchema]:
        """Get all schemas for a relationship type."""
        return self.relationship_schemas.get(relation_type, [])

    def get_schema_map(self) -> dict[str, Any]:
        """Get visual representation of the schema.

        Returns:
            Dictionary with schema hierarchy
        """
        return {
            "entities": {
                entity_type.value: {
                    "properties": [
                        {
                            "name": prop.name,
                            "type": prop.property_type.value,
                            "required": prop.required,
                            "description": prop.description,
                        }
                        for prop in schema.properties
                    ],
                    "unique_keys": schema.unique_keys,
                    "indexes": schema.indexes,
                    "description": schema.description,
                }
                for entity_type, schema in self.entity_schemas.items()
            },
            "relationships": {
                relation_type.value: [
                    {
                        "from": rel.from_entity.value,
                        "to": rel.to_entity.value,
                        "cardinality": rel.cardinality,
                        "description": rel.description,
                        "properties": [prop.name for prop in rel.properties],
                    }
                    for rel in rels
                ]
                for relation_type, rels in self.relationship_schemas.items()
            },
        }


# Global schema instance
_kg_schema: KnowledgeGraphSchema | None = None


def get_kg_schema() -> KnowledgeGraphSchema:
    """Get the global KG schema instance."""
    global _kg_schema
    if _kg_schema is None:
        _kg_schema = KnowledgeGraphSchema()
    return _kg_schema


__all__ = [
    "EntityType",
    "RelationType",
    "PropertyType",
    "PropertySchema",
    "EntitySchema",
    "RelationshipSchema",
    "KnowledgeGraphSchema",
    "get_kg_schema",
]
