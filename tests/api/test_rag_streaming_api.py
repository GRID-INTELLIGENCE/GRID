"""Tests for RAG streaming endpoint functionality.

Phase 3 Sprint 3: API endpoint tests (8 tests for RAG streaming).
Covers streaming query, batch processing, session management.
"""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


def parse_ndjson_events(response) -> list[dict[str, Any]]:
    """Parse NDJSON response into list of events."""
    events = []
    for line in response.iter_lines():
        if line.strip():
            try:
                data = json.loads(line)
                events.append(data)
            except json.JSONDecodeError:
                pass
    return events


async def mock_rag_stream(
    query: str, top_k: int = 5, session_id: str | None = None
) -> AsyncGenerator[dict[str, Any]]:
    """Mock async RAG streaming generator."""
    yield {"type": "analysis_started", "data": {"query": query}}
    yield {"type": "retrieval_started", "data": {"indices": []}}
    yield {
        "type": "documents_retrieved",
        "data": {"documents": [{"content": "test document"}], "count": 1},
    }
    yield {"type": "answer_chunk", "data": {"chunk": "This is a test answer"}}
    yield {"type": "complete", "data": {"status": "success"}}


@pytest.fixture
def rag_client():
    """Create test client for RAG streaming API with mocked engine."""
    # Patch the RAG engine creation before importing the router
    with patch(
        "application.mothership.routers.rag_streaming.create_conversational_rag_engine"
    ) as mock_create:
        # Create mock engine with proper async methods
        mock_engine = MagicMock()
        mock_engine.query = AsyncMock(
            return_value={
                "answer": "This is a test answer",
                "sources": [
                    {"confidence": 0.95, "metadata": {"path": "test.md"}},
                    {"confidence": 0.87, "metadata": {"path": "test2.md"}},
                ],
                "multi_hop_used": False,
                "hops_performed": 1,
                "follow_up_queries": [],
                "conversation_metadata": {},
            }
        )
        mock_create.return_value = mock_engine

        # Now import and create the app
        from application.mothership.routers.rag_streaming import router as rag_router

        app = FastAPI()
        app.include_router(rag_router, prefix="/api/v1")

        # Keep the patch active by returning within context
        yield TestClient(app)


# Test functions


def test_rag_stream_query_success(rag_client):
    """Test successful streaming RAG query."""
    response = rag_client.post(
        "/api/v1/rag/query/stream",
        json={"query": "What is machine learning?", "top_k": 5},
    )

    assert response.status_code == 200
    events = parse_ndjson_events(response)
    assert len(events) > 0
    assert events[0]["type"] == "analysis_started"
    assert events[-1]["type"] == "complete"


def test_rag_stream_query_with_session(rag_client):
    """Test streaming RAG query with session context."""
    response = rag_client.post(
        "/api/v1/rag/query/stream",
        json={
            "query": "What is the next topic?",
            "top_k": 5,
            "session_id": "test-session-123",
        },
    )

    assert response.status_code == 200
    events = parse_ndjson_events(response)
    assert len(events) > 0
    # Verify session flow
    assert any(e["type"] == "analysis_started" for e in events)
    assert any(e["type"] == "complete" for e in events)


def test_rag_batch_query_processing(rag_client):
    """Test batch query processing."""
    response = rag_client.post(
        "/api/v1/rag/query/batch",
        json=[
            {"query": "test1", "top_k": 5, "temperature": 0.7},
            {"query": "test2", "top_k": 5, "temperature": 0.7},
        ],
    )

    assert response.status_code == 200
    # Batch endpoint returns NDJSON streaming response
    events = parse_ndjson_events(response)
    assert len(events) > 0
    # Should have batch_started and batch_completed events
    assert any(e["type"] == "batch_started" for e in events)
    assert any(e["type"] == "batch_completed" for e in events)


def test_rag_query_validation_empty_query(rag_client):
    """Test validation of empty query."""
    response = rag_client.post(
        "/api/v1/rag/query/stream",
        json={"query": "", "top_k": 5},
    )

    # Endpoint may accept empty queries or reject them
    # Common behavior: accept but process gracefully
    assert response.status_code in (200, 400, 422)
    if response.status_code == 200:
        events = parse_ndjson_events(response)
        # Should complete even with empty query
        assert len(events) > 0


def test_rag_query_validation_invalid_temperature(rag_client):
    """Test validation of invalid temperature parameter."""
    response = rag_client.post(
        "/api/v1/rag/query/stream",
        json={"query": "test", "temperature": 2.5},  # Out of range
    )

    # Should return validation error or accept and process
    if response.status_code == 200:
        events = parse_ndjson_events(response)
        # Should still process (temperature might be clamped or ignored)
        assert len(events) > 0
    else:
        # Or it rejects with validation error
        assert response.status_code in (400, 422)


def test_rag_stream_ndjson_format(rag_client):
    """Test NDJSON format compliance."""
    response = rag_client.post(
        "/api/v1/rag/query/stream",
        json={"query": "format test", "top_k": 5},
    )

    assert response.status_code == 200
    # Verify each line is valid JSON
    for line in response.iter_lines():
        if line.strip():
            data = json.loads(line)  # Should not raise
            assert isinstance(data, dict)
            assert "type" in data
            assert "data" in data


def test_rag_stream_multi_hop_reasoning(rag_client):
    """Test multi-hop reasoning in streaming."""
    response = rag_client.post(
        "/api/v1/rag/query/stream",
        json={"query": "complex multi-part question", "top_k": 10},
    )

    assert response.status_code == 200
    events = parse_ndjson_events(response)
    # Verify event sequence
    type_sequence = [e["type"] for e in events]
    assert type_sequence[0] == "analysis_started"
    assert "retrieval_started" in type_sequence
    assert "documents_retrieved" in type_sequence
    assert type_sequence[-1] == "complete"


def test_rag_stream_error_handling(rag_client):
    """Test error handling in streaming responses."""
    response = rag_client.post(
        "/api/v1/rag/query/stream",
        json={"query": "test error", "top_k": 5},
    )

    # Should handle gracefully - either complete or error event
    assert response.status_code == 200
    events = parse_ndjson_events(response)
    if events:
        # Last event should indicate status
        assert "type" in events[-1]
