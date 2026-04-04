#!/usr/bin/env python3
"""
Precedent Enforcement System — Knowledge Graph Ingestion & Query
================================================================

Stores the precedent enforcement system as knowledge graph entities:

  Entity   "precedent-system"    Artifact  { layer, servers, version }
  Entity   "recurrence-detector" Skill     { triggers, escalation }
  Entity   "echoes-server"       Agent     { role, runtime }

  Relationship  recurrence-detector  --DEPENDS_ON-->  precedent-system
  Relationship  echoes-server        --EXECUTED_BY-->  recurrence-detector

Then:
  1. query_knowledge("enforcement")
  2. get_entity_neighborhood("precedent-system", depth=2)
  3. Connectivity confirmation

Usage:
    cd CascadeProjects/GRID-main
    python dev/precedent_graph.py
"""

from __future__ import annotations

import json
import sys
from collections import deque
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Path bootstrap — make sure `grid` is importable from src/
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))

from grid.knowledge.graph_schema import EntityType, RelationType
from grid.knowledge.graph_store import Entity, EntityId, SearchContext
from grid.knowledge.persistent_store import PersistentJSONKnowledgeStore

# ---------------------------------------------------------------------------
# Storage location (mirrors what the MCP intelligence server uses)
# ---------------------------------------------------------------------------
_KG_PATH = Path.home() / ".grid" / "knowledge" / "knowledge_graph.json"

# Sentinel timestamp for reproducible entries
_NOW = datetime.now().isoformat()

# ANSI colours for terminal readability
_GREEN = "\033[92m"
_CYAN = "\033[96m"
_YELLOW = "\033[93m"
_BOLD = "\033[1m"
_RESET = "\033[0m"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _banner(title: str) -> None:
    bar = "─" * (len(title) + 4)
    print(f"\n{_BOLD}{_CYAN}┌{bar}┐")
    print(f"│  {title}  │")
    print(f"└{bar}┘{_RESET}")


def _ok(msg: str) -> None:
    print(f"  {_GREEN}✔{_RESET}  {msg}")


def _info(msg: str) -> None:
    print(f"  {_YELLOW}→{_RESET}  {msg}")


def _print_json(label: str, data: object) -> None:
    print(f"\n  {_BOLD}{label}{_RESET}")
    serialised = json.dumps(data, indent=4, default=str)
    for line in serialised.splitlines():
        print(f"    {line}")


# ---------------------------------------------------------------------------
# 1. Entity definitions
# ---------------------------------------------------------------------------


def _build_entities() -> list[Entity]:
    """Construct the three graph nodes for the precedent enforcement system."""

    artifact_precedent_system = Entity(
        entity_id="precedent-system",
        entity_type=EntityType.ARTIFACT,
        properties={
            # --- schema-required fields ---
            "id": "precedent-system",
            "name": "precedent-system",
            "created_at": _NOW,
            # --- domain properties ---
            "layer": "enforcement",
            "servers": ["echoes-server"],
            "version": "1.0.0",
            "type": "system",
        },
        created_at=datetime.now(),
        updated_at=datetime.now(),
        labels={"enforcement", "precedent"},
    )

    skill_recurrence_detector = Entity(
        entity_id="recurrence-detector",
        entity_type=EntityType.SKILL,
        properties={
            # --- schema-required fields ---
            "id": "recurrence-detector",
            "name": "recurrence-detector",
            "created_at": _NOW,
            # --- domain properties ---
            "description": "Detects recurring failure/error patterns and escalates enforcement level",
            "triggers": ["error", "blocked", "failed"],
            "escalation": "4-level",
            "version": "1.0.0",
        },
        created_at=datetime.now(),
        updated_at=datetime.now(),
        labels={"enforcement", "detector"},
    )

    agent_echoes_server = Entity(
        entity_id="echoes-server",
        entity_type=EntityType.AGENT,
        properties={
            # --- schema-required fields ---
            "id": "echoes-server",
            "name": "echoes-server",
            "created_at": _NOW,
            # --- domain properties ---
            "type": "server",
            "status": "active",
            "metadata": {
                "role": "precedent-runtime",
                "runtime": "node/typescript",
                "path": "CascadeProjects/echoes-server",
            },
        },
        created_at=datetime.now(),
        updated_at=datetime.now(),
        labels={"enforcement", "runtime"},
    )

    return [artifact_precedent_system, skill_recurrence_detector, agent_echoes_server]


# ---------------------------------------------------------------------------
# 2. Store entities
# ---------------------------------------------------------------------------


def store_entities(store: PersistentJSONKnowledgeStore) -> None:
    _banner("PHASE 1 — Storing Entities")

    entities = _build_entities()
    for entity in entities:
        eid = store.store_entity(entity)
        _ok(f"Stored [{entity.entity_type.value}] '{eid}' labels={sorted(entity.labels or [])}")

    # Verify all three landed
    assert "precedent-system" in store.entities, "precedent-system missing"
    assert "recurrence-detector" in store.entities, "recurrence-detector missing"
    assert "echoes-server" in store.entities, "echoes-server missing"
    _ok("All 3 entities verified in store ✓")


# ---------------------------------------------------------------------------
# 3. Store relationships
# ---------------------------------------------------------------------------


def store_relationships(store: PersistentJSONKnowledgeStore) -> None:
    _banner("PHASE 2 — Storing Relationships")

    # recurrence-detector ──DEPENDS_ON──▶ precedent-system
    r1 = store.create_relationship(
        from_id=EntityId("recurrence-detector"),
        to_id=EntityId("precedent-system"),
        relationship_type=RelationType.DEPENDS_ON,
        properties={
            "dependency_type": "hard",
            "reason": "Recurrence detector reads and writes precedent store records",
        },
    )
    _ok(f"Relationship created: recurrence-detector ─DEPENDS_ON─▶ precedent-system  [{r1}]")

    # echoes-server ──EXECUTED_BY──▶ recurrence-detector
    r2 = store.create_relationship(
        from_id=EntityId("echoes-server"),
        to_id=EntityId("recurrence-detector"),
        relationship_type=RelationType.EXECUTED_BY,
        properties={
            "execution_context": "request-handler",
            "reason": "echoes-server hosts and executes the recurrence-detector skill on every audit event",
        },
    )
    _ok(f"Relationship created: echoes-server ─EXECUTED_BY─▶ recurrence-detector  [{r2}]")

    assert len(store.relationships) >= 2, "Expected at least 2 relationships"
    _ok(f"Relationship count confirmed: {len(store.relationships)} total in store ✓")


# ---------------------------------------------------------------------------
# 4. query_knowledge("enforcement")
# ---------------------------------------------------------------------------


def query_enforcement(store: PersistentJSONKnowledgeStore) -> list[Entity]:
    _banner('PHASE 3 — query_knowledge("enforcement")')

    ctx = SearchContext(query="enforcement", limit=50)
    results = store.semantic_search("enforcement", ctx)

    _info(f"Query 'enforcement' returned {len(results)} entity/entities:")
    for e in results:
        _print_json(
            f"[{e.entity_type.value}] {e.entity_id}",
            {
                "entity_id": e.entity_id,
                "entity_type": e.entity_type.value,
                "labels": sorted(e.labels or []),
                "properties": e.properties,
            },
        )

    return results


# ---------------------------------------------------------------------------
# 5. get_entity_neighborhood("precedent-system", depth=2)
# ---------------------------------------------------------------------------


def get_neighborhood(
    store: PersistentJSONKnowledgeStore,
    center_id: str = "precedent-system",
    depth: int = 2,
) -> dict:
    _banner(f'PHASE 4 — get_entity_neighborhood("{center_id}", depth={depth})')

    # BFS traversal (mirrors _get_subgraph_from_store in intelligence_server.py)
    visited_entities: set[str] = set()
    visited_rels: set[str] = set()
    queue: deque[tuple[str, int]] = deque([(center_id, 0)])
    entities_out: list[dict] = []
    rels_out: list[dict] = []

    while queue:
        current_id, current_depth = queue.popleft()
        if current_id in visited_entities:
            continue
        visited_entities.add(current_id)

        entity = store.entities.get(current_id)
        if entity:
            entities_out.append(entity.to_dict())

        if current_depth >= depth:
            continue

        for rid, rel in store.relationships.items():
            if rid in visited_rels:
                continue
            neighbor_id: str | None = None
            if rel.from_entity_id == current_id:
                neighbor_id = rel.to_entity_id
            elif rel.to_entity_id == current_id:
                neighbor_id = rel.from_entity_id

            if neighbor_id is not None:
                visited_rels.add(rid)
                rels_out.append(rel.to_dict())
                if neighbor_id not in visited_entities:
                    queue.append((neighbor_id, current_depth + 1))

    subgraph = {
        "center_entity_id": center_id,
        "depth": depth,
        "entity_count": len(entities_out),
        "relationship_count": len(rels_out),
        "entities": entities_out,
        "relationships": rels_out,
    }

    _info(f"Subgraph centred on '{center_id}' at depth {depth}:")
    _info(f"  Entities reached    : {subgraph['entity_count']}")
    _info(f"  Relationships found : {subgraph['relationship_count']}")

    for e in entities_out:
        _print_json(f"[{e['entity_type']}] {e['entity_id']}", e)

    print(f"\n  {_BOLD}Edges:{_RESET}")
    for r in rels_out:
        print(f"    {r['from_entity_id']}  ─{r['relationship_type']}─▶  {r['to_entity_id']}")

    return subgraph


# ---------------------------------------------------------------------------
# 6. Connectivity confirmation
# ---------------------------------------------------------------------------


def confirm_connectivity(
    store: PersistentJSONKnowledgeStore,
    subgraph: dict,
) -> bool:
    _banner("PHASE 5 — Connectivity Confirmation")

    expected_nodes = {"precedent-system", "recurrence-detector", "echoes-server"}
    reached_nodes = {e["entity_id"] for e in subgraph["entities"]}

    expected_edge_types = {RelationType.DEPENDS_ON.value, RelationType.EXECUTED_BY.value}
    reached_edge_types = {r["relationship_type"] for r in subgraph["relationships"]}

    # Check all nodes are reachable from precedent-system at depth 2
    missing_nodes = expected_nodes - reached_nodes
    missing_edges = expected_edge_types - reached_edge_types

    node_connected = len(missing_nodes) == 0
    edge_connected = len(missing_edges) == 0

    _info(f"Expected nodes : {sorted(expected_nodes)}")
    _info(f"Reached  nodes : {sorted(reached_nodes)}")
    _info(f"Missing  nodes : {sorted(missing_nodes) or 'none'}")
    print()
    _info(f"Expected edge types : {sorted(expected_edge_types)}")
    _info(f"Reached  edge types : {sorted(reached_edge_types)}")
    _info(f"Missing  edge types : {sorted(missing_edges) or 'none'}")

    # Validate store statistics
    stats = store.get_graph_statistics()
    _print_json("Graph Statistics", stats)

    # Final verdict
    is_connected = node_connected and edge_connected
    print()
    if is_connected:
        print(
            f"  {_GREEN}{_BOLD}✔  GRAPH IS CONNECTED{_RESET}  — "
            f"all {stats['total_entities']} nodes reachable from 'precedent-system' "
            f"within depth 2 via {stats['total_relationships']} edge(s)."
        )
    else:
        print(f"  ✘  CONNECTIVITY GAP detected — missing nodes: {missing_nodes}, missing edges: {missing_edges}")

    # Adjacency summary for human review
    print(f"\n  {_BOLD}Adjacency list:{_RESET}")
    adj: dict[str, list[str]] = {}
    for rel in store.relationships.values():
        adj.setdefault(rel.from_entity_id, []).append(f"─{rel.relationship_type.value}─▶ {rel.to_entity_id}")
        adj.setdefault(rel.to_entity_id, []).append(f"◀─{rel.relationship_type.value}─ {rel.from_entity_id}")
    for node in sorted(adj):
        for edge in sorted(adj[node]):
            print(f"    {node}  {edge}")

    return is_connected


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print(f"\n{_BOLD}{'=' * 70}")
    print("  PRECEDENT ENFORCEMENT SYSTEM — Knowledge Graph Ingestion & Query")
    print(f"{'=' * 70}{_RESET}")
    print(f"  Storage : {_KG_PATH}")
    print(f"  Time    : {_NOW}")

    with PersistentJSONKnowledgeStore(storage_path=_KG_PATH) as store:
        # Phase 1 — ingest
        store_entities(store)

        # Phase 2 — wire
        store_relationships(store)

        # Phase 3 — search
        enforcement_hits = query_enforcement(store)

        # Phase 4 — neighbourhood traversal
        subgraph = get_neighborhood(store, center_id="precedent-system", depth=2)

        # Phase 5 — confirm connectivity
        connected = confirm_connectivity(store, subgraph)

    # Exit code reflects connectivity check
    _banner("DONE")
    _ok(f"enforcement query hits : {len(enforcement_hits)}")
    _ok(f"neighbourhood nodes    : {subgraph['entity_count']}")
    _ok(f"neighbourhood edges    : {subgraph['relationship_count']}")
    status = f"{_GREEN}CONNECTED{_RESET}" if connected else "DISCONNECTED"
    _ok(f"graph status           : {status}")

    sys.exit(0 if connected else 1)


if __name__ == "__main__":
    main()
