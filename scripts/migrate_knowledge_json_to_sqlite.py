#!/usr/bin/env python3
"""
One-shot migration: PersistentJSONKnowledgeStore → PersistentSQLiteKnowledgeStore.

Usage:
    uv run python scripts/migrate_knowledge_json_to_sqlite.py
    uv run python scripts/migrate_knowledge_json_to_sqlite.py --json dev/knowledge_graph.json --db dev/knowledge_graph.db

Exits 0 on success, 1 on mismatch or error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure src/ is on the path when run from project root
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from grid.knowledge.graph_store import EntityId
from grid.knowledge.persistent_store import PersistentJSONKnowledgeStore
from grid.knowledge.sqlite_store import PersistentSQLiteKnowledgeStore


def migrate(json_path: Path, db_path: Path) -> int:
    """
    Copy all entities and relationships from the JSON store to the SQLite store.

    Returns exit code: 0 = success, 1 = failure.
    """
    if not json_path.exists():
        print(f"[ERROR] JSON source not found: {json_path}")
        return 1

    if db_path.exists():
        print(f"[WARN]  SQLite target already exists: {db_path}")
        print("        Delete it manually to start fresh, or the migration will merge.")

    print(f"[INFO]  Source : {json_path}")
    print(f"[INFO]  Target : {db_path}")

    json_store = PersistentJSONKnowledgeStore(storage_path=json_path)
    json_store.connect()
    src_stats = json_store.get_graph_statistics()
    print(
        f"[INFO]  Source has {src_stats['total_entities']} entities, {src_stats['total_relationships']} relationships"
    )

    db_store = PersistentSQLiteKnowledgeStore(storage_path=db_path)
    db_store.connect()

    entity_ok = 0
    entity_err = 0
    for entity in json_store.entities.values():
        try:
            db_store.store_entity(entity)
            entity_ok += 1
        except Exception as exc:
            print(f"[WARN]  Entity {entity.entity_id} skipped: {exc}")
            entity_err += 1

    rel_ok = 0
    rel_err = 0
    conn = db_store._ensure_connected()
    for rel in json_store.relationships.values():
        try:
            conn.execute(
                """
                INSERT OR IGNORE INTO relationships
                    (relationship_id, from_entity_id, to_entity_id,
                     relationship_type, properties, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rel.relationship_id,
                    rel.from_entity_id,
                    rel.to_entity_id,
                    rel.relationship_type.value,
                    json.dumps(rel.properties),
                    rel.created_at.isoformat(),
                    rel.updated_at.isoformat(),
                ),
            )
            conn.commit()
            rel_ok += 1
        except Exception as exc:
            print(f"[WARN]  Relationship {rel.relationship_id} skipped: {exc}")
            rel_err += 1

    dst_stats = db_store.get_graph_statistics()
    json_store.disconnect()
    db_store.disconnect()

    print()
    print("=== Migration Summary ===")
    print(f"  Entities  : {entity_ok} migrated, {entity_err} errors")
    print(f"  Relations : {rel_ok} migrated, {rel_err} errors")
    print(f"  DB totals : {dst_stats['total_entities']} entities, {dst_stats['total_relationships']} relationships")

    expected_entities = src_stats["total_entities"]
    expected_rels = src_stats["total_relationships"]

    if dst_stats["total_entities"] != expected_entities or dst_stats["total_relationships"] != expected_rels:
        print()
        print(
            f"[FAIL]  Count mismatch — expected {expected_entities} entities / "
            f"{expected_rels} relationships, got "
            f"{dst_stats['total_entities']} / {dst_stats['total_relationships']}"
        )
        return 1

    print()
    print("[OK]    Migration complete — counts match.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate knowledge graph JSON → SQLite")
    parser.add_argument(
        "--json",
        type=Path,
        default=Path("dev/knowledge_graph.json"),
        help="Path to source JSON file (default: dev/knowledge_graph.json)",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=Path("dev/knowledge_graph.db"),
        help="Path to target SQLite database (default: dev/knowledge_graph.db)",
    )
    args = parser.parse_args()
    sys.exit(migrate(args.json, args.db))


if __name__ == "__main__":
    main()
