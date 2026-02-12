"""
Neo4j Knowledge Graph implementation for GRID.

Provides enterprise-grade graph database integration with Neo4j for storing
and querying complex relationships between entities. Implements high-performance
graph traversal, semantic search, and relationship analytics.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)

Driver = Session = Record = Any
Neo4jGraphDatabase = Any

try:
    from neo4j import GraphDatabase as _GraphDatabase  # type: ignore[import-not-found]
    NEO4J_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    _GraphDatabase = None  # type: ignore[assignment]
    NEO4J_AVAILABLE = False

from ..knowledge.graph_schema import (
    EntityType,
    RelationType,
    get_kg_schema,
)


@dataclass
class Entity:
    """Knowledge graph entity."""

    entity_id: str
    entity_type: EntityType
    properties: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    labels: set[str] | None = None

    def __post_init__(self):
        if self.labels is None:
            self.labels = set()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type.value,
            "properties": self.properties,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "labels": list(self.labels) if self.labels else [],
        }


@dataclass
class Relationship:
    """Knowledge graph relationship."""

    relationship_id: str
    from_entity_id: str
    to_entity_id: str
    relationship_type: RelationType
    properties: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "relationship_id": self.relationship_id,
            "from_entity_id": self.from_entity_id,
            "to_entity_id": self.to_entity_id,
            "relationship_type": self.relationship_type.value,
            "properties": self.properties,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class EntityId:
    """Entity identifier wrapper."""

    value: str

    def __str__(self) -> str:
        return self.value


@dataclass
class RelationshipId:
    """Relationship identifier wrapper."""

    value: str

    def __str__(self) -> str:
        return self.value


@dataclass
class SearchContext:
    """Context for semantic search operations."""

    query: str
    entity_types: list[EntityType] | None = None
    relationship_types: list[RelationType] | None = None
    limit: int = 100
    offset: int = 0
    filters: dict[str, Any] | None = None
    sort_by: str | None = None
    sort_order: str = "ASC"

    def __post_init__(self):
        if self.filters is None:
            self.filters = {}


class Neo4jKnowledgeStore:
    """
    Neo4j-based knowledge graph storage and query engine.

    Features:
    - High-performance graph operations with Neo4j
    - Automatic schema validation and constraint management
    - Advanced graph traversal and pattern matching
    - Semantic search with full-text indexing
    - Relationship analytics and path finding
    - Transactional guarantees and rollback support
    """

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        username: str = "neo4j",
        password: str = "password",
        database: str = "neo4j",
        max_connection_lifetime: int = 3600,
        max_connection_pool_size: int = 100,
        connection_acquisition_timeout: int = 60,
    ):
        """
        Initialize Neo4j knowledge store.

        Args:
            uri: Neo4j connection URI
            username: Database username
            password: Database password
            database: Database name
            max_connection_lifetime: Max connection lifetime in seconds
            max_connection_pool_size: Max connection pool size
            connection_acquisition_timeout: Connection acquisition timeout
        """
        if not NEO4J_AVAILABLE:
            raise ImportError("neo4j package is required. Install with: pip install neo4j")

        self.uri = uri
        self.username = username
        self.password = password
        self.database = database

        self.driver: Driver | None = None
        self._schema = get_kg_schema()
        self._initialized = False

        # Connection configuration
        self.max_connection_lifetime = max_connection_lifetime
        self.max_connection_pool_size = max_connection_pool_size
        self.connection_acquisition_timeout = connection_acquisition_timeout

        logger.info(f"Neo4jKnowledgeStore initialized for {database}")

    def connect(self) -> None:
        """Establish connection to Neo4j database."""
        try:
            if _GraphDatabase is None:
                raise ImportError("neo4j package is required. Install with: pip install neo4j")

            self.driver = _GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
                max_connection_lifetime=self.max_connection_lifetime,
                max_connection_pool_size=self.max_connection_pool_size,
                connection_acquisition_timeout=self.connection_acquisition_timeout,
            )

            if self.driver is None:
                raise RuntimeError("Failed to initialize Neo4j driver")

            driver = self._ensure_driver()

            with driver.session(database=self.database) as session:
                result = session.run("RETURN 1 as test")
                test_value = result.single()["test"]
                if test_value != 1:
                    raise Exception("Connection test failed")

            # Initialize database schema
            self._initialize_schema()
            self._initialized = True

            logger.info(f"Connected to Neo4j database: {self.database}")

        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    def disconnect(self) -> None:
        """Close Neo4j database connection."""
        if self.driver:
            self.driver.close()
            self.driver = None
            self._initialized = False
            logger.info("Disconnected from Neo4j database")

    def store_entity(self, entity: Entity) -> EntityId:
        """
        Store an entity in the knowledge graph.

        Args:
            entity: Entity to store

        Returns:
            Entity ID
        """
        driver = self._ensure_driver()

        # Validate entity against schema
        is_valid, errors = self._schema.validate_entity(entity.entity_type, entity.properties)
        if not is_valid:
            raise ValueError(f"Entity validation failed: {errors}")

        with driver.session(database=self.database) as session:
            # Create entity with labels
            labels = [entity.entity_type.value] + list(entity.labels or [])
            label_str = ":".join(labels)

            query = f"""
            MERGE (e:{label_str} {{entity_id: $entity_id}})
            SET e += $properties,
                e.created_at = $created_at,
                e.updated_at = $updated_at
            RETURN e.entity_id as entity_id
            """

            result = session.run(query, {
                "entity_id": entity.entity_id,
                "properties": entity.properties,
                "created_at": entity.created_at.isoformat(),
                "updated_at": entity.updated_at.isoformat(),
            })

            entity_id = result.single()["entity_id"]
            logger.debug(f"Stored entity {entity_id} of type {entity.entity_type.value}")

            return EntityId(entity_id)

    def create_relationship(
        self,
        from_id: EntityId,
        to_id: EntityId,
        relationship_type: RelationType,
        properties: dict[str, Any] | None = None,
    ) -> RelationshipId:
        """
        Create a relationship between entities.

        Args:
            from_id: Source entity ID
            to_id: Target entity ID
            relationship_type: Type of relationship
            properties: Relationship properties

        Returns:
            Relationship ID
        """
        driver = self._ensure_driver()

        relationship_id = str(uuid4())
        now = datetime.now()
        with driver.session(database=self.database) as session:
            query = f"""
            MATCH (a {{entity_id: $from_id}}), (b {{entity_id: $to_id}})
            MERGE (a)-[r:{relationship_type.value} {{relationship_id: $relationship_id}}]->(b)
            SET r += $properties,
                r.created_at = $created_at,
                r.updated_at = $updated_at
            RETURN r.relationship_id as relationship_id
            """

            result = session.run(query, {
                "from_id": from_id.value,
                "to_id": to_id.value,
                "relationship_id": relationship_id,
                "properties": properties or {},
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
            })

            rel_id = result.single()["relationship_id"]
            logger.debug(f"Created relationship {rel_id} from {from_id.value} to {to_id.value}")

            return RelationshipId(rel_id)

    def get_entity(self, entity_id: EntityId) -> Entity | None:
        """
        Retrieve an entity by ID.

        Args:
            entity_id: Entity ID

        Returns:
            Entity or None if not found
        """
        driver = self._ensure_driver()

        with driver.session(database=self.database) as session:
            query = """
            MATCH (e {entity_id: $entity_id})
            RETURN e, labels(e) as labels
            """

            result = session.run(query, {"entity_id": entity_id.value})
            record = result.single()

            if not record:
                return None

            node = record["e"]
            labels = record["labels"]

            # Determine entity type from labels
            entity_type = None
            for label in labels:
                try:
                    entity_type = EntityType(label)
                    break
                except ValueError:
                    continue

            if not entity_type:
                raise ValueError(f"Unknown entity type for entity {entity_id.value}")

            # Extract properties (excluding system properties)
            properties = dict(node)
            properties.pop("entity_id", None)
            properties.pop("created_at", None)
            properties.pop("updated_at", None)

            return Entity(
                entity_id=node["entity_id"],
                entity_type=entity_type,
                properties=properties,
                created_at=datetime.fromisoformat(node["created_at"]),
                updated_at=datetime.fromisoformat(node["updated_at"]),
                labels=set(labels) - {entity_type.value},
            )

    def semantic_search(self, query: str, context: SearchContext) -> list[Entity]:
        """
        Perform semantic search across the knowledge graph.

        Args:
            query: Search query
            context: Search context parameters

        Returns:
            List of matching entities
        """
        driver = self._ensure_driver()

        with driver.session(database=self.database) as session:
            # Build base query
            query_parts: list[str] = []
            params: dict[str, Any] = {"search_term": query}

            # Entity type filtering
            if context.entity_types:
                type_filter = " OR ".join([f"e:{etype.value}" for etype in context.entity_types])
                query_parts.append(f"({type_filter})")

            # Property search
            query_parts.append("(toLower(e.name) CONTAINS toLower($search_term) OR " +
                              "toLower(e.description) CONTAINS toLower($search_term))")

            # Build full query
            where_clause = " AND ".join(query_parts)

            base_query = f"""
            MATCH (e)
            WHERE {where_clause}
            RETURN e, labels(e) as labels
            ORDER BY e.{context.sort_by or 'created_at'} {context.sort_order}
            SKIP $offset LIMIT $limit
            """

            params["offset"] = context.offset
            params["limit"] = context.limit

            result = session.run(base_query, params)
            entities = []

            for record in result:
                node = record["e"]
                labels = record["labels"]

                # Determine entity type
                entity_type = None
                for label in labels:
                    try:
                        entity_type = EntityType(label)
                        break
                    except ValueError:
                        continue

                if not entity_type:
                    continue

                # Extract properties
                properties = dict(node)
                properties.pop("entity_id", None)
                properties.pop("created_at", None)
                properties.pop("updated_at", None)

                entity = Entity(
                    entity_id=node["entity_id"],
                    entity_type=entity_type,
                    properties=properties,
                    created_at=datetime.fromisoformat(node["created_at"]),
                    updated_at=datetime.fromisoformat(node["updated_at"]),
                    labels=set(labels) - {entity_type.value},
                )

                entities.append(entity)

            logger.debug(f"Semantic search returned {len(entities)} entities")
            return entities

    def find_relationships(
        self,
        entity_id: EntityId,
        relationship_type: RelationType | None = None,
        direction: str = "both",  # "outgoing", "incoming", "both"
        limit: int = 100,
    ) -> list[tuple[Relationship, Entity]]:
        """
        Find relationships for an entity.

        Args:
            entity_id: Entity ID
            relationship_type: Filter by relationship type
            direction: Direction of relationships
            limit: Maximum number of results

        Returns:
            List of (relationship, related_entity) tuples
        """
        driver = self._ensure_driver()

        with driver.session(database=self.database) as session:
            # Build query based on direction
            if direction == "outgoing":
                match_clause = "MATCH (e {entity_id: $entity_id})-[r]->(related)"
            elif direction == "incoming":
                match_clause = "MATCH (e {entity_id: $entity_id})<-[r]-(related)"
            else:  # both
                match_clause = "MATCH (e {entity_id: $entity_id})-[r]-(related)"

            # Add relationship type filter if specified
            where_clause = ""
            if relationship_type:
                where_clause = f"WHERE type(r) = '{relationship_type.value}'"

            query = f"""
            {match_clause}
            {where_clause}
            RETURN r, related, labels(related) as labels
            LIMIT $limit
            """

            result = session.run(query, {
                "entity_id": entity_id.value,
                "limit": limit,
            })

            relationships = []

            for record in result:
                rel = record["r"]
                related_node = record["related"]
                labels = record["labels"]

                # Determine related entity type
                entity_type = None
                for label in labels:
                    try:
                        entity_type = EntityType(label)
                        break
                    except ValueError:
                        continue

                if not entity_type:
                    continue

                # Create relationship object
                relationship = Relationship(
                    relationship_id=rel["relationship_id"],
                    from_entity_id=rel.start_node["entity_id"],
                    to_entity_id=rel.end_node["entity_id"],
                    relationship_type=RelationType(type(rel)),
                    properties=dict(rel),
                    created_at=datetime.fromisoformat(rel["created_at"]),
                    updated_at=datetime.fromisoformat(rel["updated_at"]),
                )

                # Create related entity
                properties = dict(related_node)
                properties.pop("entity_id", None)
                properties.pop("created_at", None)
                properties.pop("updated_at", None)

                related_entity = Entity(
                    entity_id=related_node["entity_id"],
                    entity_type=entity_type,
                    properties=properties,
                    created_at=datetime.fromisoformat(related_node["created_at"]),
                    updated_at=datetime.fromisoformat(related_node["updated_at"]),
                    labels=set(labels) - {entity_type.value},
                )

                relationships.append((relationship, related_entity))

            return relationships

    def find_path(
        self,
        from_id: EntityId,
        to_id: EntityId,
        max_depth: int = 5,
        relationship_types: list[RelationType] | None = None,
    ) -> list[Entity]:
        """
        Find shortest path between two entities.

        Args:
            from_id: Source entity ID
            to_id: Target entity ID
            max_depth: Maximum path depth
            relationship_types: Allowed relationship types

        Returns:
            List of entities in the path
        """
        driver = self._ensure_driver()

        with driver.session(database=self.database) as session:
            # Build relationship filter
            rel_filter = ""
            if relationship_types:
                rel_types = "|".join([rt.value for rt in relationship_types])
                rel_filter = f":{rel_types}"

            query = f"""
            MATCH path = shortestPath(
                (start {{entity_id: $from_id}})-[{rel_filter}*1..{max_depth}]-(end {{entity_id: $to_id}})
            )
            RETURN [node in nodes(path) | node] as path_nodes
            """

            result = session.run(query, {
                "from_id": from_id.value,
                "to_id": to_id.value,
            })

            record = result.single()
            if not record:
                return []

            path_nodes = record["path_nodes"]
            entities = []

            for node in path_nodes:
                # Get entity labels
                labels_query = """
                MATCH (e {entity_id: $entity_id})
                RETURN labels(e) as labels
                """
                labels_result = session.run(labels_query, {"entity_id": node["entity_id"]})
                labels = labels_result.single()["labels"]

                # Determine entity type
                entity_type = None
                for label in labels:
                    try:
                        entity_type = EntityType(label)
                        break
                    except ValueError:
                        continue

                if not entity_type:
                    continue

                # Extract properties
                properties = dict(node)
                properties.pop("entity_id", None)
                properties.pop("created_at", None)
                properties.pop("updated_at", None)

                entity = Entity(
                    entity_id=node["entity_id"],
                    entity_type=entity_type,
                    properties=properties,
                    created_at=datetime.fromisoformat(node["created_at"]),
                    updated_at=datetime.fromisoformat(node["updated_at"]),
                    labels=set(labels) - {entity_type.value},
                )

                entities.append(entity)

            return entities

    def get_graph_statistics(self) -> dict[str, Any]:
        """
        Get knowledge graph statistics.

        Returns:
            Dictionary with graph statistics
        """
        driver = self._ensure_driver()

        with driver.session(database=self.database) as session:
            # Count entities by type
            entity_counts_query = """
            MATCH (e)
            RETURN labels(e) as labels, count(e) as count
            """
            entity_result = session.run(entity_counts_query)
            entity_counts = {}
            for record in entity_result:
                labels = record["labels"]
                if labels:
                    primary_label = labels[0]  # Assume first label is the entity type
                    entity_counts[primary_label] = record["count"]

            # Count relationships by type
            rel_counts_query = """
            MATCH ()-[r]->()
            RETURN type(r) as type, count(r) as count
            """
            rel_result = session.run(rel_counts_query)
            relationship_counts = {}
            for record in rel_result:
                relationship_counts[record["type"]] = record["count"]

            # Get overall statistics
            stats_query = """
            MATCH (n) RETURN count(n) as total_nodes
            MATCH ()-[r]->() RETURN count(r) as total_relationships
            """
            stats_result = session.run(stats_query)
            stats_records = list(stats_result)

            total_nodes = stats_records[0]["total_nodes"] if len(stats_records) > 0 else 0
            total_relationships = stats_records[1]["total_relationships"] if len(stats_records) > 1 else 0

            return {
                "total_entities": total_nodes,
                "total_relationships": total_relationships,
                "entity_counts": entity_counts,
                "relationship_counts": relationship_counts,
                "database": self.database,
            }

    def _initialize_schema(self) -> None:
        """Initialize database schema with constraints and indexes."""
        driver = self._ensure_driver()
        with driver.session(database=self.database) as session:
            # Create uniqueness constraints for entity IDs
            for entity_type in EntityType:
                constraint_query = f"""
                CREATE CONSTRAINT IF NOT EXISTS FOR (e:{entity_type.value})
                REQUIRE e.entity_id IS UNIQUE
                """
                session.run(constraint_query)

            # Create indexes for common properties
            indexes = [
                ("Entity", "name"),
                ("Entity", "created_at"),
                ("Skill", "version"),
                ("Event", "event_type"),
                ("Event", "timestamp"),
            ]

            for label, property in indexes:
                index_query = f"""
                CREATE INDEX IF NOT EXISTS FOR (e:{label}) ON (e.{property})
                """
                session.run(index_query)

            # Create full-text search indexes
            search_indexes = [
                ("Entity", ["name", "description"]),
                ("Skill", ["name", "description"]),
                ("Artifact", ["name", "type"]),
            ]

            for label, properties in search_indexes:
                search_query = f"""
                CREATE FULLTEXT INDEX IF NOT EXISTS FOR (e:{label})
                ON EACH [{', '.join([f'e.{prop}' for prop in properties])}]
                """
                session.run(search_query)

            logger.info("Database schema initialized")

    def _validate_entity(self, entity: Entity) -> tuple[bool, list[str]]:
        """Validate entity against schema."""
        return self._schema.validate_entity(entity.entity_type, entity.properties)

    def _ensure_driver(self) -> Driver:
        """Ensure driver is initialized and connected."""
        if not self._initialized:
            self.connect()
        if self.driver is None:
            raise RuntimeError("Neo4j driver is not initialized")
        return self.driver

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


# Global knowledge store instance
_global_knowledge_store: Neo4jKnowledgeStore | None = None


def get_knowledge_store() -> Neo4jKnowledgeStore:
    """Get or create global knowledge store instance."""
    global _global_knowledge_store
    if _global_knowledge_store is None:
        _global_knowledge_store = Neo4jKnowledgeStore()
    return _global_knowledge_store


def set_knowledge_store(store: Neo4jKnowledgeStore) -> None:
    """Set global knowledge store instance."""
    global _global_knowledge_store
    _global_knowledge_store = store
