from __future__ import annotations

import asyncio

import pytest
from fastapi import HTTPException

import application.mothership.routers.knowledge as knowledge_router


def _run_graph(**kwargs):
    return asyncio.run(knowledge_router.knowledge_graph(**kwargs))


def test_graph_success_response_includes_hash_and_limits(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "nodes": [
            {"id": "a", "label": "A", "entity_type": "Concept", "subtitle": ""},
            {"id": "b", "label": "B", "entity_type": "Concept", "subtitle": ""},
        ],
        "edges": [{"id": "e1", "source": "a", "target": "b", "type": "RELATED_TO", "label": "RELATED_TO"}],
        "storage_path": "dev/knowledge_graph.json",
        "total_entities": 2,
        "truncated": False,
    }
    monkeypatch.setattr(knowledge_router, "_export_graph_payload", lambda max_nodes: payload)

    response = _run_graph(max_nodes=200)
    assert response.graph_hash
    assert response.limits.applied_max_nodes == 200
    assert response.limits.max_edges == knowledge_router.GRAPH_DEFAULT_MAX_EDGES
    assert response.nodes[0].id == "a"


def test_graph_rejects_hard_node_limit() -> None:
    with pytest.raises(HTTPException) as exc:
        _run_graph(max_nodes=5_000)
    assert exc.value.status_code == 409
    assert exc.value.detail["code"] == "GRAPH_TOO_LARGE"


def test_graph_rejects_invalid_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(knowledge_router, "_export_graph_payload", lambda max_nodes: {"nodes": "bad", "edges": []})
    with pytest.raises(HTTPException) as exc:
        _run_graph(max_nodes=10)
    assert exc.value.status_code == 422
    assert exc.value.detail["code"] == "SCHEMA_INVALID"


def test_graph_rejects_inconsistent_edges(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "nodes": [{"id": "a", "label": "A", "entity_type": "Concept", "subtitle": ""}],
        "edges": [{"id": "e1", "source": "a", "target": "missing", "type": "RELATED_TO", "label": "RELATED_TO"}],
        "storage_path": "dev/knowledge_graph.json",
        "total_entities": 1,
        "truncated": False,
    }
    monkeypatch.setattr(knowledge_router, "_export_graph_payload", lambda max_nodes: payload)
    with pytest.raises(HTTPException) as exc:
        _run_graph(max_nodes=10)
    assert exc.value.status_code == 409
    assert exc.value.detail["code"] == "INCONSISTENT_GRAPH"


def test_graph_rejects_overdense_edges(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "nodes": [
            {"id": "a", "label": "A", "entity_type": "Concept", "subtitle": ""},
            {"id": "b", "label": "B", "entity_type": "Concept", "subtitle": ""},
        ],
        "edges": [
            {"id": "e1", "source": "a", "target": "b", "type": "RELATED_TO", "label": "RELATED_TO"},
            {"id": "e2", "source": "a", "target": "b", "type": "RELATED_TO", "label": "RELATED_TO"},
        ],
        "storage_path": "dev/knowledge_graph.json",
        "total_entities": 2,
        "truncated": False,
    }
    monkeypatch.setattr(knowledge_router, "_export_graph_payload", lambda max_nodes: payload)
    with pytest.raises(HTTPException) as exc:
        _run_graph(max_nodes=10, max_edges=1)
    assert exc.value.status_code == 409
    assert exc.value.detail["code"] == "GRAPH_TOO_LARGE"
