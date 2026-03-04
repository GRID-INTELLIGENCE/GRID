"""
Tests for Mycelium - Knowledge Federation
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mycelium.knowledge_federation import (
    FederatedResult,
    GridRAGAdapter,
    KnowledgeFederator,
    PathwaysRAGAdapter,
    RAGBackend,
)


class MockRAGBackend:
    """Simple in-memory RAG backend for testing."""

    def __init__(self, results: list[str] | None = None):
        self._results = results or []

    async def query(self, question: str, top_k: int = 5) -> list[str]:
        return self._results[:top_k]


class SlowRAGBackend:
    """Backend that times out."""

    async def query(self, question: str, top_k: int = 5) -> list[str]:
        import asyncio

        await asyncio.sleep(10)
        return ["should not reach"]


class FailingRAGBackend:
    """Backend that raises errors."""

    async def query(self, question: str, top_k: int = 5) -> list[str]:
        raise ConnectionError("Backend unavailable")


def test_rag_backend_protocol():
    """MockRAGBackend satisfies the RAGBackend protocol."""
    backend = MockRAGBackend()
    assert isinstance(backend, RAGBackend)


def test_federated_result_defaults():
    result = FederatedResult(question="test")
    assert result.grid_results == []
    assert result.pathways_results == []
    assert result.sources == []
    assert result.synthesis is None


@pytest.mark.asyncio
async def test_grid_rag_adapter_no_engine():
    adapter = GridRAGAdapter(rag_engine=None)
    results = await adapter.query("test question")
    assert results == []


@pytest.mark.asyncio
async def test_grid_rag_adapter_with_engine():
    engine = MagicMock()
    engine.query = AsyncMock(return_value=["result1", "result2"])
    adapter = GridRAGAdapter(rag_engine=engine)
    results = await adapter.query("test question", top_k=2)
    assert results == ["result1", "result2"]


@pytest.mark.asyncio
async def test_grid_rag_adapter_error_handling():
    engine = MagicMock()
    engine.query = AsyncMock(side_effect=RuntimeError("boom"))
    adapter = GridRAGAdapter(rag_engine=engine)
    results = await adapter.query("test")
    assert results == []


@pytest.mark.asyncio
async def test_federator_both_backends():
    grid = MockRAGBackend(["grid chunk 1", "grid chunk 2"])
    pathways = MockRAGBackend(["pathways chunk 1"])

    with patch("mycelium.knowledge_federation.get_event_bus") as mock_bus:
        mock_bus.return_value.publish = AsyncMock()
        federator = KnowledgeFederator(
            grid_backend=grid,
            pathways_backend=pathways,
        )
        result = await federator.query("What is recursion?")

    assert result.question == "What is recursion?"
    assert len(result.grid_results) == 2
    assert len(result.pathways_results) == 1
    assert "grid" in result.sources
    assert "pathways" in result.sources
    assert result.synthesis is not None


@pytest.mark.asyncio
async def test_federator_grid_only():
    grid = MockRAGBackend(["grid data"])
    pathways = MockRAGBackend([])  # empty

    with patch("mycelium.knowledge_federation.get_event_bus") as mock_bus:
        mock_bus.return_value.publish = AsyncMock()
        federator = KnowledgeFederator(grid_backend=grid, pathways_backend=pathways)
        result = await federator.query("test")

    assert "grid" in result.sources
    assert "pathways" not in result.sources


@pytest.mark.asyncio
async def test_federator_empty_results():
    grid = MockRAGBackend([])
    pathways = MockRAGBackend([])

    with patch("mycelium.knowledge_federation.get_event_bus") as mock_bus:
        mock_bus.return_value.publish = AsyncMock()
        federator = KnowledgeFederator(grid_backend=grid, pathways_backend=pathways)
        result = await federator.query("test")

    assert result.sources == []
    assert result.synthesis is None


@pytest.mark.asyncio
async def test_federator_timeout_graceful_degradation():
    """When one backend times out, the other's results still come through."""
    grid = MockRAGBackend(["grid works"])
    pathways = SlowRAGBackend()

    with patch("mycelium.knowledge_federation.get_event_bus") as mock_bus:
        mock_bus.return_value.publish = AsyncMock()
        federator = KnowledgeFederator(grid_backend=grid, pathways_backend=pathways)
        result = await federator.query("test", timeout=0.1)

    assert len(result.grid_results) == 1
    assert len(result.pathways_results) == 0
    assert "grid" in result.sources


@pytest.mark.asyncio
async def test_federator_error_graceful_degradation():
    grid = FailingRAGBackend()
    pathways = MockRAGBackend(["pathways works"])

    with patch("mycelium.knowledge_federation.get_event_bus") as mock_bus:
        mock_bus.return_value.publish = AsyncMock()
        federator = KnowledgeFederator(grid_backend=grid, pathways_backend=pathways)
        result = await federator.query("test")

    assert len(result.pathways_results) == 1
    assert "pathways" in result.sources


@pytest.mark.asyncio
async def test_federator_broadcasts_result_event():
    grid = MockRAGBackend(["data"])
    pathways = MockRAGBackend([])

    with patch("mycelium.knowledge_federation.get_event_bus") as mock_bus:
        mock_bus.return_value.publish = AsyncMock()
        federator = KnowledgeFederator(grid_backend=grid, pathways_backend=pathways)
        await federator.query("test")

    mock_bus.return_value.publish.assert_called_once()
    event = mock_bus.return_value.publish.call_args[0][0]
    assert event.event_type == "grid.knowledge.federated"
    assert event.payload["question"] == "test"
