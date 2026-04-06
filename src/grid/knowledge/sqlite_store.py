"""
SQLite-backed Knowledge Store for GRID.

Drop-in replacement for PersistentJSONKnowledgeStore with:
- SQLite + WAL mode for concurrent reads without blocking
- FTS5 full-text index for O(log n) semantic_search (replaces O(n) linear scan)
- Per-operation writes (no full-file rewrite on every mutation)
- No full-file load on connect (lazy open, not bulk hydration)

Public interface is identical to PersistentJSONKnowledgeStore.
"""

from __future__ import annotations

import json
import logging
import sqlite3
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

_DDL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS entities (
    entity_id   TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    properties  TEXT NOT NULL,
    labels      TEXT NOT NULL DEFAULT '[]',
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS relationships (
    relationship_id   TEXT PRIMARY KEY,
    from_entity_id    TEXT NOT NULL,
    to_entity_id      TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    properties        TEXT NOT NULL DEFAULT '{}',
    created_at        TEXT NOT NULL,
    updated_at        TEXT NOT NULL,
    FOREIGN KEY (from_entity_id) REFERENCES entities(entity_id),
    FOREIGN KEY (to_entity_id)   REFERENCES entities(entity_id)
);

CREATE VIRTUAL TABLE IF NOT EXISTS entities_fts USING fts5(
    entity_id UNINDEXED,
    searchable_text,
    content=entities,
    content_rowid=rowid
);

CREATE TRIGGER IF NOT EXISTS entities_fts_insert
AFTER INSERT ON entities BEGIN
    INSERT INTO entities_fts(rowid, entity_id, searchable_text)
    VALUES (NEW.rowid, NEW.entity_id, NEW.entity_id || ' ' || NEW.entity_type || ' ' || NEW.properties);
END;

CREATE TRIGGER IF NOT EXISTS entities_fts_update
AFTER UPDATE ON entities BEGIN
    INSERT INTO entities_fts(entities_fts, rowid, entity_id, searchable_text)
    VALUES ('delete', OLD.rowid, OLD.entity_id, OLD.entity_id || ' ' || OLD.entity_type || ' ' || OLD.properties);
    INSERT INTO entities_fts(rowid, entity_id, searchable_text)
    VALUES (NEW.rowid, NEW.entity_id, NEW.entity_id || ' ' || NEW.entity_type || ' ' || NEW.properties);
END;

CREATE TRIGGER IF NOT EXISTS entities_fts_delete
AFTER DELETE ON entities BEGIN
    INSERT INTO entities_fts(entities_fts, rowid, entity_id, searchable_text)
    VALUES ('delete', OLD.rowid, OLD.entity_id, OLD.entity_id || ' ' || OLD.entity_type || ' ' || OLD.properties);
END;
"""


def _row_to_entity(row: sqlite3.Row) -> Entity:
    return Entity(
        entity_id=row["entity_id"],
        entity_type=EntityType(row["entity_type"]),
        properties=json.loads(row["properties"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
        labels=set(json.loads(row["labels"])),
    )


def _row_to_relationship(row: sqlite3.Row) -> Relationship:
    return Relationship(
        relationship_id=row["relationship_id"],
        from_entity_id=row["from_entity_id"],
        to_entity_id=row["to_entity_id"],
        relationship_type=RelationType(row["relationship_type"]),
        properties=json.loads(row["properties"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


class PersistentSQLiteKnowledgeStore:
    """
    SQLite-backed knowledge graph storage.

    Implements the same public interface as PersistentJSONKnowledgeStore
    for transparent drop-in replacement. Uses WAL mode and FTS5 for
    concurrent read safety and indexed full-text search.
    """

    def __init__(self, storage_path: str | Path | None = None) -> None:
        if storage_path is None:
            storage_path = Path("dev/knowledge_graph.db")

        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        self._schema = get_kg_schema()
        self._conn: sqlite3.Connection | None = None
        self._initialized = False

        logger.info("PersistentSQLiteKnowledgeStore initialized at %s", self.storage_path)

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    def connect(self) -> None:
        """Open the SQLite database and apply DDL if needed."""
        if self._conn is not None:
            return
        self._conn = sqlite3.connect(str(self.storage_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_DDL)
        self._conn.commit()
        self._initialized = True
        stats = self.get_graph_statistics()
        logger.info(
            "Connected to SQLite store — %d entities, %d relationships",
            stats["total_entities"],
            stats["total_relationships"],
        )

    def disconnect(self) -> None:
        """Close the database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None
            self._initialized = False

    def _ensure_connected(self) -> sqlite3.Connection:
        if self._conn is None:
            self.connect()
        return self._conn  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Entity operations
    # ------------------------------------------------------------------

    def store_entity(self, entity: Entity) -> EntityId:
        """
        Insert or replace an entity in the store.

        Validates against the graph schema before writing.
        """
        is_valid, errors = self._schema.validate_entity(entity.entity_type, entity.properties)
        if not is_valid:
            raise ValueError(f"Entity validation failed: {errors}")

        conn = self._ensure_connected()
        conn.execute(
            """
            INSERT INTO entities (entity_id, entity_type, properties, labels, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(entity_id) DO UPDATE SET
                entity_type = excluded.entity_type,
                properties  = excluded.properties,
                labels      = excluded.labels,
                updated_at  = excluded.updated_at
            """,
            (
                entity.entity_id,
                entity.entity_type.value,
                json.dumps(entity.properties),
                json.dumps(list(entity.labels) if entity.labels else []),
                entity.created_at.isoformat(),
                entity.updated_at.isoformat(),
            ),
        )
        conn.commit()
        logger.debug("Stored entity %s of type %s", entity.entity_id, entity.entity_type.value)
        return EntityId(entity.entity_id)

    def get_entity(self, entity_id: EntityId) -> Entity | None:
        """Retrieve a single entity by ID. Returns None if not found."""
        conn = self._ensure_connected()
        row = conn.execute(
            "SELECT * FROM entities WHERE entity_id = ?",
            (entity_id.value,),
        ).fetchone()
        return _row_to_entity(row) if row else None

    # ------------------------------------------------------------------
    # Relationship operations
    # ------------------------------------------------------------------

    def create_relationship(
        self,
        from_id: EntityId,
        to_id: EntityId,
        relationship_type: RelationType,
        properties: dict[str, Any] | None = None,
    ) -> RelationshipId:
        """Insert a typed relationship between two entities."""
        rel_id = str(uuid4())
        now = datetime.now()
        conn = self._ensure_connected()
        conn.execute(
            """
            INSERT INTO relationships
                (relationship_id, from_entity_id, to_entity_id, relationship_type, properties, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                rel_id,
                from_id.value,
                to_id.value,
                relationship_type.value,
                json.dumps(properties or {}),
                now.isoformat(),
                now.isoformat(),
            ),
        )
        conn.commit()
        logger.debug("Created relationship %s: %s → %s", rel_id, from_id.value, to_id.value)
        return RelationshipId(rel_id)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def semantic_search(self, query: str, context: SearchContext) -> list[Entity]:
        """
        FTS5-backed full-text search over entity properties and IDs.

        Falls back to a LIKE scan when the FTS5 query would be empty
        or contain only stop words, preserving the contract of the
        original linear-scan implementation.
        """
        conn = self._ensure_connected()
        limit = context.limit if context.limit else 100

        type_filter_sql = ""
        type_params: list[str] = []
        if context.entity_types:
            placeholders = ",".join("?" * len(context.entity_types))
            type_filter_sql = f"AND e.entity_type IN ({placeholders})"
            type_params = [et.value for et in context.entity_types]

        try:
            fts_query = query.replace('"', '""')
            # type_filter_sql is safe: built from EntityType enum values, not user input
            rows = conn.execute(
                f"""
                SELECT e.*
                FROM entities e
                JOIN entities_fts fts ON fts.entity_id = e.entity_id
                WHERE entities_fts MATCH ?
                {type_filter_sql}
                LIMIT ?
                """,  # noqa: S608
                [fts_query, *type_params, limit],
            ).fetchall()
        except sqlite3.OperationalError:
            # type_filter_sql is safe: built from EntityType enum values, not user input
            rows = conn.execute(
                f"""
                SELECT e.*
                FROM entities e
                WHERE (
                    LOWER(e.properties) LIKE ?
                    OR LOWER(e.entity_id) LIKE ?
                )
                {type_filter_sql}
                LIMIT ?
                """,  # noqa: S608
                [f"%{query.lower()}%", f"%{query.lower()}%", *type_params, limit],
            ).fetchall()

        return [_row_to_entity(r) for r in rows]

    # ------------------------------------------------------------------
    # Statistics & visualization
    # ------------------------------------------------------------------

    def get_graph_statistics(self) -> dict[str, Any]:
        """Return counts and breakdown by entity/relationship type."""
        conn = self._ensure_connected()

        total_entities = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
        total_relationships = conn.execute("SELECT COUNT(*) FROM relationships").fetchone()[0]

        entity_counts: dict[str, int] = {}
        for row in conn.execute("SELECT entity_type, COUNT(*) AS cnt FROM entities GROUP BY entity_type"):
            entity_counts[row["entity_type"]] = row["cnt"]

        rel_counts: dict[str, int] = {}
        for row in conn.execute(
            "SELECT relationship_type, COUNT(*) AS cnt FROM relationships GROUP BY relationship_type"
        ):
            rel_counts[row["relationship_type"]] = row["cnt"]

        return {
            "total_entities": total_entities,
            "total_relationships": total_relationships,
            "entity_counts": entity_counts,
            "relationship_counts": rel_counts,
            "storage_path": str(self.storage_path),
        }

    def export_graph_visualization(self, *, max_nodes: int | None = None) -> dict[str, Any]:
        """
        Serialize entities and relationships for graph UIs (nodes + edges).

        Args:
            max_nodes: When set, return at most this many entities (stable order
                by entity_id) and only edges whose endpoints are both included.

        Returns:
            Dict with ``nodes``, ``edges``, ``storage_path``, ``total_entities``,
            and ``truncated``.
        """
        conn = self._ensure_connected()
        total_entities = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]

        if max_nodes is not None:
            entity_rows = conn.execute("SELECT * FROM entities ORDER BY entity_id LIMIT ?", (max_nodes,)).fetchall()
            truncated = total_entities > max_nodes
        else:
            entity_rows = conn.execute("SELECT * FROM entities ORDER BY entity_id").fetchall()
            truncated = False

        allowed_ids: set[str] = set()
        nodes: list[dict[str, Any]] = []
        for row in entity_rows:
            allowed_ids.add(row["entity_id"])
            props = json.loads(row["properties"])
            name = props.get("name", row["entity_id"])
            desc = props.get("description", "")
            subtitle = desc[:160] if isinstance(desc, str) else ""
            nodes.append(
                {
                    "id": row["entity_id"],
                    "label": str(name),
                    "entity_type": row["entity_type"],
                    "subtitle": subtitle,
                }
            )

        rel_rows = conn.execute("SELECT * FROM relationships").fetchall()
        edges: list[dict[str, Any]] = []
        for row in rel_rows:
            if row["from_entity_id"] not in allowed_ids or row["to_entity_id"] not in allowed_ids:
                continue
            rprops = json.loads(row["properties"]) if row["properties"] else {}
            label = rprops.get("relation_label") or row["relationship_type"]
            edges.append(
                {
                    "id": row["relationship_id"],
                    "source": row["from_entity_id"],
                    "target": row["to_entity_id"],
                    "type": row["relationship_type"],
                    "label": str(label),
                }
            )

        return {
            "nodes": nodes,
            "edges": edges,
            "storage_path": str(self.storage_path),
            "total_entities": total_entities,
            "truncated": truncated,
        }

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def __enter__(self) -> PersistentSQLiteKnowledgeStore:
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.disconnect()
