"""Graph compiler for Echoes context to Glimpse Entity transformation.

Transforms Echoes audit/telemetry context into Glimpse Entity shapes for
visualization and cognitive analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class EntityType(Enum):
    """Glimpse entity types."""

    NODE = "node"
    EDGE = "edge"
    CLUSTER = "cluster"
    EVENT = "event"
    ARTIFACT = "artifact"


class RelationType(Enum):
    """Relationship types between entities."""

    CAUSED_BY = "caused_by"
    DEPENDS_ON = "depends_on"
    PART_OF = "part_of"
    REFERENCES = "references"
    FOLLOWED_BY = "followed_by"
    TRIGGERED = "triggered"


@dataclass(slots=True)
class GlimpseEntity:
    """A Glimpse-compatible entity for visualization.

    Represents a node in the cognitive graph with properties
    suitable for Glimpse engine rendering.
    """

    id: str
    entity_type: EntityType
    label: str
    properties: dict[str, Any] = field(default_factory=dict)
    position: tuple[float, float, float] | None = None
    weight: float = 1.0
    timestamp: datetime | None = None
    source_context: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "type": self.entity_type.value,
            "label": self.label,
            "properties": self.properties,
            "position": self.position,
            "weight": self.weight,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "source": self.source_context,
        }


@dataclass(slots=True)
class GlimpseEdge:
    """A relationship between two Glimpse entities."""

    id: str
    source_id: str
    target_id: str
    relation_type: RelationType
    weight: float = 1.0
    properties: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "source": self.source_id,
            "target": self.target_id,
            "relation": self.relation_type.value,
            "weight": self.weight,
            "properties": self.properties,
        }


@dataclass(slots=True)
class GlimpseGraph:
    """A complete Glimpse graph with entities and edges."""

    entities: list[GlimpseEntity] = field(default_factory=list)
    edges: list[GlimpseEdge] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "entities": [e.to_dict() for e in self.entities],
            "edges": [e.to_dict() for e in self.edges],
            "metadata": self.metadata,
        }

    def add_entity(self, entity: GlimpseEntity) -> None:
        """Add an entity to the graph."""
        self.entities.append(entity)

    def add_edge(self, edge: GlimpseEdge) -> None:
        """Add an edge to the graph."""
        self.edges.append(edge)


class GraphCompiler:
    """Compiles Echoes audit context into Glimpse graph structures.

    Transforms audit events, telemetry data, and context snapshots
    into a format suitable for Glimpse visualization engine.
    """

    def __init__(self, *, default_weight: float = 1.0) -> None:
        """Initialize the compiler.

        Args:
            default_weight: Default weight for entities without explicit weight.
        """
        self.default_weight = default_weight
        self._entity_cache: dict[str, GlimpseEntity] = {}

    def compile_echoes_context(self, context: dict[str, Any]) -> GlimpseGraph:
        """Compile an Echoes context snapshot into a Glimpse graph.

        Args:
            context: Echoes context dictionary containing audit events,
                    session data, and telemetry.

        Returns:
            GlimpseGraph ready for visualization.

        Example:
            >>> compiler = GraphCompiler()
            >>> ctx = {"events": [...], "session": {...}}
            >>> graph = compiler.compile_echoes_context(ctx)
        """
        graph = GlimpseGraph(
            metadata={
                "compiled_at": datetime.now().isoformat(),
                "source": "echoes",
                "version": "1.0",
            }
        )

        # Process events
        events = context.get("events", [])
        for event in events:
            entity = self._compile_event(event)
            graph.add_entity(entity)
            self._entity_cache[entity.id] = entity

        # Process session context
        if session := context.get("session"):
            session_entity = self._compile_session(session)
            graph.add_entity(session_entity)
            self._entity_cache[session_entity.id] = session_entity

        # Build relationships
        edges = self._build_relationships(context)
        for edge in edges:
            graph.add_edge(edge)

        return graph

    def compile_audit_event(self, event: dict[str, Any]) -> GlimpseEntity:
        """Compile a single audit event into a Glimpse entity.

        Args:
            event: Echoes audit event dictionary.

        Returns:
            GlimpseEntity representing the event.
        """
        return self._compile_event(event)

    def _compile_event(self, event: dict[str, Any]) -> GlimpseEntity:
        """Internal: compile an event to entity."""
        event_id = event.get("id", str(uuid4()))
        timestamp = None
        if ts := event.get("timestamp"):
            if isinstance(ts, str):
                timestamp = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            elif isinstance(ts, datetime):
                timestamp = ts

        return GlimpseEntity(
            id=f"event:{event_id}",
            entity_type=EntityType.EVENT,
            label=event.get("action", event.get("tool", "unknown")),
            properties={
                "source": event.get("source"),
                "status": event.get("status"),
                "duration_ms": event.get("durationMs"),
                "metadata": event.get("metadata", {}),
            },
            weight=self._calculate_weight(event),
            timestamp=timestamp,
            source_context="echoes_audit",
        )

    def _compile_session(self, session: dict[str, Any]) -> GlimpseEntity:
        """Internal: compile session context to entity."""
        session_id = session.get("id", str(uuid4()))
        return GlimpseEntity(
            id=f"session:{session_id}",
            entity_type=EntityType.CLUSTER,
            label=f"Session {session_id[:8]}",
            properties={
                "user": session.get("user"),
                "started_at": session.get("started_at"),
                "tool_count": session.get("tool_count", 0),
            },
            weight=2.0,  # Sessions have higher weight
            source_context="echoes_session",
        )

    def _calculate_weight(self, event: dict[str, Any]) -> float:
        """Calculate entity weight based on event properties."""
        weight = self.default_weight
        # Errors have higher weight
        if event.get("status") == "error":
            weight *= 1.5
        # Longer operations have higher weight
        if duration := event.get("durationMs"):
            if duration > 5000:
                weight *= 1.3
            elif duration > 1000:
                weight *= 1.1
        return weight

    def _build_relationships(self, context: dict[str, Any]) -> list[GlimpseEdge]:
        """Build edges from context relationships."""
        edges: list[GlimpseEdge] = []
        events = context.get("events", [])

        # Link sequential events
        for i, event in enumerate(events[:-1]):
            source_id = f"event:{event.get('id', i)}"
            target_id = f"event:{events[i + 1].get('id', i + 1)}"

            edges.append(
                GlimpseEdge(
                    id=f"edge:{uuid4()}",
                    source_id=source_id,
                    target_id=target_id,
                    relation_type=RelationType.FOLLOWED_BY,
                    weight=0.5,
                )
            )

        # Link events to session if present
        if session := context.get("session"):
            session_id = f"session:{session.get('id', 'default')}"
            for event in events:
                event_id = f"event:{event.get('id', str(uuid4()))}"
                edges.append(
                    GlimpseEdge(
                        id=f"edge:{uuid4()}",
                        source_id=event_id,
                        target_id=session_id,
                        relation_type=RelationType.PART_OF,
                        weight=0.3,
                    )
                )

        return edges

    def clear_cache(self) -> None:
        """Clear the entity cache."""
        self._entity_cache.clear()
