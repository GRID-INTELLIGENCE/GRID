"""Unit tests for GridIntelligenceMCPServer."""

import asyncio
import json
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from grid.mcp.intelligence_server import (
    TOOLS,
    GridIntelligenceMCPServer,
    _get_subgraph_from_store,
    _SlidingWindowRateLimiter,
    _validate_essential_state,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@dataclass
class _FakeHybridResult:
    statistical_patterns: list[str]
    syntactic_patterns: list[str]
    neural_patterns: list[str]
    combined_patterns: list[str]
    confidence_scores: dict[str, float]
    metadata: dict[str, Any]


def _make_mock_pattern_detector() -> AsyncMock:
    detector = AsyncMock()
    detector.detect = AsyncMock(
        return_value=_FakeHybridResult(
            statistical_patterns=["trend_up"],
            syntactic_patterns=["sequence"],
            neural_patterns=["cluster_a"],
            combined_patterns=["trend_up", "sequence", "cluster_a"],
            confidence_scores={"statistical": 0.8, "syntactic": 0.7, "neural": 0.9},
            metadata={"method": "hybrid"},
        )
    )
    return detector


def _make_mock_agentic_detector() -> AsyncMock:
    detector = AsyncMock()
    detector.detect_embedded_agentic = AsyncMock(
        return_value={
            "embedded_agentic_species": ["neural_network"],
            "base_patterns": ["FLOW_MOTION"],
            "all_patterns": ["FLOW_MOTION", "neural_network"],
            "confidence_scores": {"neural_network": 0.85},
            "pattern_matches": {"neural_network": ["FLOW_MOTION"]},
            "structure_analysis": {"has_structure": True},
            "agentic_indicators": {"has_structure": True, "has_flow": False, "has_connections": True},
        }
    )
    return detector


def _make_mock_extended_recognition() -> AsyncMock:
    recognizer = AsyncMock()
    recognizer.get_embedded_analysis = AsyncMock(
        return_value={
            "embedded_agentic_species": ["information_flow"],
            "base_patterns": ["TEMPORAL_PATTERNS"],
            "all_patterns": ["TEMPORAL_PATTERNS", "information_flow"],
            "confidence_scores": {"information_flow": 0.72},
            "pattern_matches": {},
            "structure_analysis": {"has_flow": True},
            "agentic_indicators": {"has_structure": False, "has_flow": True, "has_connections": False},
        }
    )
    return recognizer


def _make_mock_knowledge_store() -> MagicMock:
    """Build a mock PersistentJSONKnowledgeStore with in-memory data."""
    store = MagicMock()
    store._initialized = True

    # Fake entity data
    entity_a = MagicMock()
    entity_a.entity_id = "a1"
    entity_a.entity_type = MagicMock(value="Agent")
    entity_a.to_dict.return_value = {
        "entity_id": "a1",
        "entity_type": "Agent",
        "properties": {"name": "alpha"},
        "created_at": "2026-01-01T00:00:00",
        "updated_at": "2026-01-01T00:00:00",
        "labels": [],
    }

    entity_b = MagicMock()
    entity_b.entity_id = "b1"
    entity_b.entity_type = MagicMock(value="Skill")
    entity_b.to_dict.return_value = {
        "entity_id": "b1",
        "entity_type": "Skill",
        "properties": {"name": "beta"},
        "created_at": "2026-01-01T00:00:00",
        "updated_at": "2026-01-01T00:00:00",
        "labels": [],
    }

    rel = MagicMock()
    rel.from_entity_id = "a1"
    rel.to_entity_id = "b1"
    rel.to_dict.return_value = {
        "relationship_id": "r1",
        "from_entity_id": "a1",
        "to_entity_id": "b1",
        "relationship_type": "EXECUTED_BY",
        "properties": {},
        "created_at": "2026-01-01T00:00:00",
        "updated_at": "2026-01-01T00:00:00",
    }

    store.entities = {"a1": entity_a, "b1": entity_b}
    store.relationships = {"r1": rel}
    store.semantic_search = MagicMock(return_value=[entity_a])
    store.store_entity = MagicMock(return_value=MagicMock(value="a1", __str__=lambda s: "a1"))
    store.create_relationship = MagicMock(return_value=MagicMock(value="r1", __str__=lambda s: "r1"))
    store.connect = MagicMock()

    return store


def _make_mock_trace_manager() -> MagicMock:
    """Build a mock TraceManager with a mock store."""
    trace = MagicMock()
    trace.trace_id = "t-001"
    trace.action_type = "test_action"
    trace.action_name = "Test Action"
    trace.input_data = {}
    trace.model_used = None
    trace.safety_score = None
    trace.risk_level = None
    trace.model_dump.return_value = {
        "trace_id": "t-001",
        "action_type": "test_action",
        "action_name": "Test Action",
        "context": {"trace_id": "t-001", "origin": "api_request"},
        "success": True,
    }
    trace.complete = MagicMock()

    manager = MagicMock()
    manager.store = MagicMock()
    manager.store.query_traces = MagicMock(return_value=[trace])
    manager.store.save_trace = MagicMock()
    manager.get_trace_chain = MagicMock(return_value=[trace])
    manager.create_trace = MagicMock(return_value=trace)

    return manager


@pytest.fixture()
def server() -> GridIntelligenceMCPServer:
    return GridIntelligenceMCPServer(
        pattern_detector_factory=_make_mock_pattern_detector,
        agentic_detector_factory=_make_mock_agentic_detector,
        extended_recognition_factory=_make_mock_extended_recognition,
        knowledge_store_factory=_make_mock_knowledge_store,
        trace_manager_factory=_make_mock_trace_manager,
    )


def _run(coro):
    """Helper to run async in sync tests."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Tool listing
# ---------------------------------------------------------------------------


class TestToolListing:
    def test_tools_count(self):
        assert len(TOOLS) == 11

    def test_tool_names(self):
        names = {t.name for t in TOOLS}
        expected = {
            "detect_patterns",
            "detect_agentic_species",
            "list_pattern_detectors",
            "query_knowledge",
            "get_entity_neighborhood",
            "store_entity",
            "store_relationship",
            "query_traces",
            "get_trace_lineage",
            "record_trace",
            "analyze_coherence",
        }
        assert names == expected

    def test_all_tools_have_input_schema(self):
        for tool in TOOLS:
            assert "type" in tool.inputSchema

    @pytest.mark.asyncio()
    async def test_list_tools_handler(self, server: GridIntelligenceMCPServer):
        result = await server.server._handle_list_tools()
        assert len(result.tools) == 11


# ---------------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------------


class TestRateLimiter:
    def test_allows_within_limit(self):
        limiter = _SlidingWindowRateLimiter(max_calls=5, window_seconds=60.0)
        for _ in range(5):
            assert limiter.allow()

    def test_blocks_over_limit(self):
        limiter = _SlidingWindowRateLimiter(max_calls=3, window_seconds=60.0)
        for _ in range(3):
            assert limiter.allow()
        assert not limiter.allow()

    def test_window_expiry(self):
        limiter = _SlidingWindowRateLimiter(max_calls=2, window_seconds=0.1)
        assert limiter.allow()
        assert limiter.allow()
        assert not limiter.allow()
        time.sleep(0.15)
        assert limiter.allow()

    @pytest.mark.asyncio()
    async def test_rate_limit_error_response(self, server: GridIntelligenceMCPServer):
        server._rate_limiter = _SlidingWindowRateLimiter(max_calls=1, window_seconds=60.0)
        # First call succeeds
        r1 = await server._dispatch_tool("list_pattern_detectors", {})
        assert not r1.isError
        # Second call rate-limited
        r2 = await server._dispatch_tool("list_pattern_detectors", {})
        assert r2.isError
        assert "Rate limit" in r2.content[0].text


# ---------------------------------------------------------------------------
# EssentialState validation
# ---------------------------------------------------------------------------


class TestValidateEssentialState:
    def test_valid_input(self):
        state = _validate_essential_state(
            {"pattern_signature": "test", "quantum_state": {"a": 1}, "context_depth": 2.0, "coherence_factor": 0.8}
        )
        assert state.pattern_signature == "test"
        assert state.quantum_state == {"a": 1}
        assert state.context_depth == 2.0
        assert state.coherence_factor == 0.8

    def test_defaults(self):
        state = _validate_essential_state({"pattern_signature": "sig", "quantum_state": {"x": 1}})
        assert state.context_depth == 1.0
        assert state.coherence_factor == 0.5

    def test_missing_pattern_signature(self):
        with pytest.raises(ValueError, match="pattern_signature"):
            _validate_essential_state({"quantum_state": {"a": 1}})

    def test_empty_pattern_signature(self):
        with pytest.raises(ValueError, match="pattern_signature"):
            _validate_essential_state({"pattern_signature": "", "quantum_state": {}})

    def test_missing_quantum_state(self):
        with pytest.raises(ValueError, match="quantum_state"):
            _validate_essential_state({"pattern_signature": "sig"})

    def test_invalid_quantum_state_type(self):
        with pytest.raises(ValueError, match="quantum_state"):
            _validate_essential_state({"pattern_signature": "sig", "quantum_state": "not_a_dict"})

    def test_invalid_context_depth_type(self):
        with pytest.raises(ValueError, match="context_depth"):
            _validate_essential_state(
                {"pattern_signature": "sig", "quantum_state": {"a": 1}, "context_depth": "bad"}
            )


# ---------------------------------------------------------------------------
# BFS subgraph helper
# ---------------------------------------------------------------------------


class TestGetSubgraph:
    def test_single_entity(self):
        store = _make_mock_knowledge_store()
        result = _get_subgraph_from_store(store, "a1", depth=0)
        assert result["entity_count"] == 1
        assert result["relationship_count"] == 0
        assert result["center_entity_id"] == "a1"

    def test_depth_1_traversal(self):
        store = _make_mock_knowledge_store()
        result = _get_subgraph_from_store(store, "a1", depth=1)
        assert result["entity_count"] == 2
        assert result["relationship_count"] == 1

    def test_nonexistent_entity(self):
        store = _make_mock_knowledge_store()
        result = _get_subgraph_from_store(store, "nonexistent", depth=2)
        assert result["entity_count"] == 0
        assert result["relationship_count"] == 0

    def test_calls_connect_if_not_initialized(self):
        store = _make_mock_knowledge_store()
        store._initialized = False
        _get_subgraph_from_store(store, "a1", depth=0)
        store.connect.assert_called_once()


# ---------------------------------------------------------------------------
# Pattern Detection tools
# ---------------------------------------------------------------------------


class TestPatternDetection:
    @pytest.mark.asyncio()
    async def test_detect_patterns_success(self, server: GridIntelligenceMCPServer):
        result = await server._dispatch_tool(
            "detect_patterns",
            {"pattern_signature": "test_sig", "quantum_state": {"data": 1}},
        )
        assert not result.isError
        data = json.loads(result.content[0].text)
        assert "combined_patterns" in data
        assert "trend_up" in data["combined_patterns"]

    @pytest.mark.asyncio()
    async def test_detect_patterns_validation_error(self, server: GridIntelligenceMCPServer):
        result = await server._dispatch_tool("detect_patterns", {"quantum_state": {"data": 1}})
        assert result.isError
        assert "pattern_signature" in result.content[0].text

    @pytest.mark.asyncio()
    async def test_detect_agentic_species_success(self, server: GridIntelligenceMCPServer):
        result = await server._dispatch_tool(
            "detect_agentic_species",
            {"pattern_signature": "agentic_sig", "quantum_state": {"nodes": [1, 2]}},
        )
        assert not result.isError
        data = json.loads(result.content[0].text)
        assert "neural_network" in data["embedded_agentic_species"]

    @pytest.mark.asyncio()
    async def test_list_pattern_detectors(self, server: GridIntelligenceMCPServer):
        result = await server._dispatch_tool("list_pattern_detectors", {})
        assert not result.isError
        data = json.loads(result.content[0].text)
        assert len(data["detectors"]) == 6
        names = {d["name"] for d in data["detectors"]}
        assert "HybridPatternDetector" in names
        assert "EmbeddedAgenticDetector" in names


# ---------------------------------------------------------------------------
# Knowledge Graph tools
# ---------------------------------------------------------------------------


class TestKnowledgeGraph:
    @pytest.mark.asyncio()
    async def test_query_knowledge_success(self, server: GridIntelligenceMCPServer):
        result = await server._dispatch_tool("query_knowledge", {"query": "alpha"})
        assert not result.isError
        data = json.loads(result.content[0].text)
        assert data["count"] == 1
        assert data["entities"][0]["entity_id"] == "a1"

    @pytest.mark.asyncio()
    async def test_query_knowledge_empty_query(self, server: GridIntelligenceMCPServer):
        result = await server._dispatch_tool("query_knowledge", {"query": ""})
        assert result.isError
        assert "query" in result.content[0].text.lower()

    @pytest.mark.asyncio()
    async def test_get_entity_neighborhood(self, server: GridIntelligenceMCPServer):
        result = await server._dispatch_tool("get_entity_neighborhood", {"entity_id": "a1", "depth": 1})
        assert not result.isError
        data = json.loads(result.content[0].text)
        assert data["center_entity_id"] == "a1"
        assert data["entity_count"] == 2

    @pytest.mark.asyncio()
    async def test_get_entity_neighborhood_missing_id(self, server: GridIntelligenceMCPServer):
        result = await server._dispatch_tool("get_entity_neighborhood", {"entity_id": ""})
        assert result.isError

    @pytest.mark.asyncio()
    async def test_store_entity(self, server: GridIntelligenceMCPServer):
        result = await server._dispatch_tool(
            "store_entity",
            {"entity_id": "new1", "entity_type": "Agent", "properties": {"name": "new_agent"}},
        )
        assert not result.isError
        data = json.loads(result.content[0].text)
        assert data["stored"] is True

    @pytest.mark.asyncio()
    async def test_store_entity_missing_type(self, server: GridIntelligenceMCPServer):
        result = await server._dispatch_tool(
            "store_entity",
            {"entity_id": "new1", "entity_type": "", "properties": {}},
        )
        assert result.isError

    @pytest.mark.asyncio()
    async def test_store_relationship(self, server: GridIntelligenceMCPServer):
        result = await server._dispatch_tool(
            "store_relationship",
            {
                "from_entity_id": "a1",
                "to_entity_id": "b1",
                "relationship_type": "EXECUTED_BY",
            },
        )
        assert not result.isError
        data = json.loads(result.content[0].text)
        assert data["stored"] is True

    @pytest.mark.asyncio()
    async def test_store_relationship_missing_ids(self, server: GridIntelligenceMCPServer):
        result = await server._dispatch_tool(
            "store_relationship",
            {"from_entity_id": "", "to_entity_id": "b1", "relationship_type": "DEPENDS_ON"},
        )
        assert result.isError


# ---------------------------------------------------------------------------
# Tracing tools
# ---------------------------------------------------------------------------


class TestTracing:
    @pytest.mark.asyncio()
    async def test_query_traces(self, server: GridIntelligenceMCPServer):
        result = await server._dispatch_tool("query_traces", {"action_type": "test_action"})
        assert not result.isError
        data = json.loads(result.content[0].text)
        assert data["count"] == 1

    @pytest.mark.asyncio()
    async def test_query_traces_no_store(self, server: GridIntelligenceMCPServer):
        # Force trace manager with no store
        server._trace_manager = MagicMock()
        server._trace_manager.store = None
        result = await server._dispatch_tool("query_traces", {})
        assert result.isError
        assert "No trace store" in result.content[0].text

    @pytest.mark.asyncio()
    async def test_get_trace_lineage(self, server: GridIntelligenceMCPServer):
        result = await server._dispatch_tool("get_trace_lineage", {"trace_id": "t-001"})
        assert not result.isError
        data = json.loads(result.content[0].text)
        assert data["trace_id"] == "t-001"
        assert data["lineage_depth"] == 1

    @pytest.mark.asyncio()
    async def test_get_trace_lineage_missing_id(self, server: GridIntelligenceMCPServer):
        result = await server._dispatch_tool("get_trace_lineage", {"trace_id": ""})
        assert result.isError

    @pytest.mark.asyncio()
    async def test_record_trace(self, server: GridIntelligenceMCPServer):
        result = await server._dispatch_tool(
            "record_trace",
            {
                "action_type": "mcp_call",
                "action_name": "Test Record",
                "origin": "api_request",
                "tags": ["test"],
                "model_used": "claude-opus-4-6",
                "safety_score": 0.95,
                "risk_level": "low",
            },
        )
        assert not result.isError
        data = json.loads(result.content[0].text)
        assert data["recorded"] is True
        assert data["trace_id"] == "t-001"

    @pytest.mark.asyncio()
    async def test_record_trace_missing_fields(self, server: GridIntelligenceMCPServer):
        result = await server._dispatch_tool("record_trace", {"action_type": "x"})
        assert result.isError


# ---------------------------------------------------------------------------
# Analysis tools
# ---------------------------------------------------------------------------


class TestAnalysis:
    @pytest.mark.asyncio()
    async def test_analyze_coherence(self, server: GridIntelligenceMCPServer):
        result = await server._dispatch_tool(
            "analyze_coherence",
            {"pattern_signature": "coherence_test", "quantum_state": {"flow": True}, "coherence_factor": 0.9},
        )
        assert not result.isError
        data = json.loads(result.content[0].text)
        assert data["coherence_factor"] == 0.9
        assert data["pattern_signature"] == "coherence_test"
        assert "embedded_agentic_species" in data


# ---------------------------------------------------------------------------
# Unknown tool
# ---------------------------------------------------------------------------


class TestUnknownTool:
    @pytest.mark.asyncio()
    async def test_unknown_tool(self, server: GridIntelligenceMCPServer):
        result = await server._dispatch_tool("nonexistent_tool", {})
        assert result.isError
        assert "Unknown tool" in result.content[0].text


# ---------------------------------------------------------------------------
# Lazy init
# ---------------------------------------------------------------------------


class TestLazyInit:
    def test_subsystems_not_initialized_on_create(self, server: GridIntelligenceMCPServer):
        assert server._pattern_detector is None
        assert server._agentic_detector is None
        assert server._extended_recognition is None
        assert server._knowledge_store is None
        assert server._trace_manager is None

    @pytest.mark.asyncio()
    async def test_pattern_detector_initialized_on_first_call(self, server: GridIntelligenceMCPServer):
        await server._dispatch_tool(
            "detect_patterns", {"pattern_signature": "init_test", "quantum_state": {"x": 1}}
        )
        assert server._pattern_detector is not None

    @pytest.mark.asyncio()
    async def test_knowledge_store_initialized_on_first_call(self, server: GridIntelligenceMCPServer):
        await server._dispatch_tool("query_knowledge", {"query": "test"})
        assert server._knowledge_store is not None
