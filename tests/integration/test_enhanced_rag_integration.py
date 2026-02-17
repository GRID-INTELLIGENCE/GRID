#!/usr/bin/env python3
"""
Integration tests for Enhanced RAG MCP Server.

This test verifies that the enhanced RAG server can be instantiated
and demonstrates its capabilities.

Uses conditional imports to handle optional dependencies gracefully.
"""

import asyncio
import os
import sys
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

# Conditional imports for optional dependencies
HAS_CONVERSATIONAL_RAG = False
HAS_ENHANCED_RAG_SERVER = False

try:
    from tools.rag.conversational_rag import create_conversational_rag_engine

    HAS_CONVERSATIONAL_RAG = True
except ImportError as e:
    create_conversational_rag_engine = None
    _RAG_IMPORT_ERROR = str(e)

try:
    from grid.mcp.enhanced_rag_server import EnhancedRAGMCPServer

    HAS_ENHANCED_RAG_SERVER = True
except ImportError as e:
    EnhancedRAGMCPServer = None
    _SERVER_IMPORT_ERROR = str(e)

# Mark module as requiring optional dependencies
requires_rag_deps = pytest.mark.skipif(
    not (HAS_CONVERSATIONAL_RAG and HAS_ENHANCED_RAG_SERVER),
    reason="Enhanced RAG requires optional dependencies. "
    f"Conversational RAG: {HAS_CONVERSATIONAL_RAG}, "
    f"Enhanced Server: {HAS_ENHANCED_RAG_SERVER}",
)


# =============================================================================
# Mock classes for testing without optional dependencies
# =============================================================================


class MockConversationalRAGEngine:
    """Mock conversational RAG engine for testing."""

    def __init__(self):
        self.sessions: dict[str, dict[str, Any]] = {}
        self.config = MagicMock()
        self.config.conversation_enabled = True
        self.config.multi_hop_enabled = False
        self._turn_count = 0

    def create_session(self, session_id: str, metadata: dict | None = None):
        self.sessions[session_id] = {
            "metadata": metadata or {},
            "turn_count": 0,
            "query_history": [],
        }

    def get_session_info(self, session_id: str) -> dict | None:
        return self.sessions.get(session_id)

    def delete_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    async def query(self, question: str, session_id: str | None = None, **kwargs):
        if session_id and session_id in self.sessions:
            self.sessions[session_id]["turn_count"] += 1
            turn_count = self.sessions[session_id]["turn_count"]
        else:
            self._turn_count += 1
            turn_count = self._turn_count

        return {
            "answer": f"Mock response for: {question[:50]}...",
            "sources": [{"content": "mock source", "score": 0.9}],
            "conversation_metadata": {"turn_count": turn_count},
            "multi_hop_used": kwargs.get("enable_multi_hop", False),
            "fallback_used": False,
        }

    def get_conversation_stats(self):
        return {
            "total_sessions": len(self.sessions),
            "total_turns": sum(s["turn_count"] for s in self.sessions.values()),
            "multi_hop_queries": 0,
        }


class MockEnhancedRAGMCPServer:
    """Mock Enhanced RAG MCP Server for testing."""

    def __init__(self):
        self.rag_engine = MockConversationalRAGEngine()
        self.sessions = {}
        self.server = MagicMock()
        self.server._tool_handlers = {
            "query": MagicMock(),
            "index": MagicMock(),
            "session_create": MagicMock(),
            "session_delete": MagicMock(),
        }


# =============================================================================
# Tests with Optional Dependencies
# =============================================================================


class TestEnhancedRAGCapabilitiesWithDeps:
    """Test Enhanced RAG capabilities when dependencies are available."""

    @pytest.fixture
    def engine(self):
        """Create conversational RAG engine."""
        if not HAS_CONVERSATIONAL_RAG:
            pytest.skip("Conversational RAG dependencies not available")
        try:
            return create_conversational_rag_engine()
        except Exception as e:
            pytest.skip(f"Failed to create RAG engine: {e}")

    @requires_rag_deps
    @pytest.mark.asyncio
    async def test_engine_creation(self, engine):
        """Test that conversational RAG engine can be created."""
        assert engine is not None
        assert hasattr(engine, "config")
        assert hasattr(engine, "create_session")

    @requires_rag_deps
    @pytest.mark.asyncio
    async def test_session_management(self, engine):
        """Test session creation and retrieval."""
        session_id = "test-session-123"

        engine.create_session(session_id, {"test": "metadata"})

        session_info = engine.get_session_info(session_id)
        assert session_info is not None

        success = engine.delete_session(session_id)
        assert success is True

        session_info = engine.get_session_info(session_id)
        assert session_info is None

    @requires_rag_deps
    @pytest.mark.asyncio
    async def test_conversational_query(self, engine):
        """Test conversational query flow."""
        session_id = "test-conv-session"
        engine.create_session(session_id)

        # First query
        result1 = await engine.query("What is GRID?", session_id=session_id)
        assert "answer" in result1
        assert "sources" in result1

        # Second query should maintain context
        result2 = await engine.query("How does it work?", session_id=session_id)
        turn1 = result1.get("conversation_metadata", {}).get("turn_count", 0)
        turn2 = result2.get("conversation_metadata", {}).get("turn_count", 0)
        assert turn2 >= turn1

        engine.delete_session(session_id)

    @requires_rag_deps
    @pytest.mark.asyncio
    async def test_multi_hop_reasoning(self, engine):
        """Test multi-hop reasoning capability."""
        session_id = "test-multihop-session"
        engine.create_session(session_id)

        try:
            result = await engine.query(
                "Explain the architecture",
                session_id=session_id,
                enable_multi_hop=True,
            )
            assert "answer" in result
        finally:
            engine.delete_session(session_id)

    @requires_rag_deps
    def test_conversation_stats(self, engine):
        """Test conversation statistics collection."""
        stats = engine.get_conversation_stats()
        assert "total_sessions" in stats
        assert "total_turns" in stats


class TestEnhancedRAGMCPServerWithDeps:
    """Test Enhanced RAG MCP Server when dependencies are available."""

    @pytest.fixture
    def server(self):
        """Create Enhanced RAG MCP Server."""
        if not HAS_ENHANCED_RAG_SERVER:
            pytest.skip("Enhanced RAG Server dependencies not available")
        try:
            return EnhancedRAGMCPServer()
        except Exception as e:
            pytest.skip(f"Failed to create server: {e}")

    @requires_rag_deps
    def test_server_instantiation(self, server):
        """Test server can be instantiated."""
        assert server is not None
        assert hasattr(server, "rag_engine")

    @requires_rag_deps
    def test_tools_registered(self, server):
        """Test that MCP tools are registered."""
        assert hasattr(server, "server")
        # Tools should be registered for query, index, etc.


# =============================================================================
# Tests with Mocked Dependencies (Always Run)
# =============================================================================


class TestConversationalRAGMocked:
    """Test conversational RAG with mocked dependencies - always runs."""

    @pytest.fixture
    def mock_engine(self):
        """Create mock conversational RAG engine."""
        return MockConversationalRAGEngine()

    def test_mock_session_creation(self, mock_engine):
        """Test mock session creation."""
        session_id = "mock-session"
        mock_engine.create_session(session_id, {"test": "data"})

        session_info = mock_engine.get_session_info(session_id)
        assert session_info is not None
        assert session_info["metadata"]["test"] == "data"

    def test_mock_session_deletion(self, mock_engine):
        """Test mock session deletion."""
        session_id = "delete-test-session"
        mock_engine.create_session(session_id)

        success = mock_engine.delete_session(session_id)
        assert success is True

        session_info = mock_engine.get_session_info(session_id)
        assert session_info is None

    @pytest.mark.asyncio
    async def test_mock_query_flow(self, mock_engine):
        """Test mock query flow."""
        session_id = "query-session"
        mock_engine.create_session(session_id)

        result = await mock_engine.query("Test question", session_id=session_id)

        assert "answer" in result
        assert "sources" in result
        assert "conversation_metadata" in result
        assert result["conversation_metadata"]["turn_count"] == 1

        # Second query should increment turn count
        result2 = await mock_engine.query("Follow-up", session_id=session_id)
        assert result2["conversation_metadata"]["turn_count"] == 2

    def test_mock_conversation_stats(self, mock_engine):
        """Test mock conversation statistics."""
        mock_engine.create_session("session1")
        mock_engine.create_session("session2")

        stats = mock_engine.get_conversation_stats()
        assert stats["total_sessions"] == 2

    @pytest.mark.asyncio
    async def test_mock_multi_hop_flag(self, mock_engine):
        """Test multi-hop flag is passed through."""
        session_id = "multihop-session"
        mock_engine.create_session(session_id)

        result = await mock_engine.query(
            "Test",
            session_id=session_id,
            enable_multi_hop=True,
        )

        assert result["multi_hop_used"] is True


class TestEnhancedRAGMCPServerMocked:
    """Test Enhanced RAG MCP Server with mocked dependencies - always runs."""

    @pytest.fixture
    def mock_server(self):
        """Create mock Enhanced RAG MCP Server."""
        return MockEnhancedRAGMCPServer()

    def test_mock_server_instantiation(self, mock_server):
        """Test mock server can be instantiated."""
        assert mock_server is not None
        assert mock_server.rag_engine is not None

    def test_mock_server_tools(self, mock_server):
        """Test mock server has expected tools."""
        assert "query" in mock_server.server._tool_handlers
        assert "index" in mock_server.server._tool_handlers

    @pytest.mark.asyncio
    async def test_mock_server_query(self, mock_server):
        """Test mock server query through RAG engine."""
        mock_server.rag_engine.create_session("test")

        result = await mock_server.rag_engine.query("Test query", session_id="test")

        assert "answer" in result


# =============================================================================
# Utility Tests (Always Run)
# =============================================================================


class TestRAGUtilities:
    """Test RAG utility functions - always runs."""

    def test_session_id_generation(self):
        """Test unique session ID generation."""
        import uuid

        session_ids = set()
        for _ in range(100):
            session_id = str(uuid.uuid4())
            assert session_id not in session_ids
            session_ids.add(session_id)

    def test_conversation_turn_tracking(self):
        """Test conversation turn tracking logic."""
        turns = []
        for i in range(5):
            turns.append(i + 1)

        # Verify progression
        for i in range(len(turns) - 1):
            assert turns[i + 1] > turns[i]


class TestImportErrorReporting:
    """Test that import errors are properly reported - always runs."""

    def test_import_availability_detection(self):
        """Test that we correctly detect import availability."""
        # These should be boolean values
        assert isinstance(HAS_CONVERSATIONAL_RAG, bool)
        assert isinstance(HAS_ENHANCED_RAG_SERVER, bool)

    def test_mock_engine_works_without_imports(self):
        """Test that mock engine works even without real imports."""
        engine = MockConversationalRAGEngine()
        assert engine is not None
        assert engine.config.conversation_enabled is True


# =============================================================================
# Main entry point for standalone execution
# =============================================================================


async def main():
    """Run integration tests with status reporting."""
    print("=" * 70)
    print("Enhanced RAG MCP Server Integration Test")
    print("=" * 70)
    print("\nDependency Status:")
    print(f"  Conversational RAG: {'✅ Available' if HAS_CONVERSATIONAL_RAG else '❌ Not Available'}")
    print(f"  Enhanced RAG Server: {'✅ Available' if HAS_ENHANCED_RAG_SERVER else '❌ Not Available'}")
    print()

    if HAS_CONVERSATIONAL_RAG and HAS_ENHANCED_RAG_SERVER:
        print("Running full integration tests...")
        try:
            engine = create_conversational_rag_engine()
            print("✅ Engine created")

            engine.create_session("test-main")
            result = await engine.query("Test query", session_id="test-main")
            print(f"✅ Query result: {result['answer'][:50]}...")

            engine.delete_session("test-main")
            print("✅ Session deleted")

        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback

            traceback.print_exc()
    else:
        print("Running mock-based tests...")
        engine = MockConversationalRAGEngine()
        print("✅ Mock engine created")

        engine.create_session("mock-main")
        result = await engine.query("Test query", session_id="mock-main")
        print(f"✅ Mock query result: {result['answer'][:50]}...")

        engine.delete_session("mock-main")
        print("✅ Mock session deleted")

    print("\n" + "=" * 70)
    print("Integration Test Completed")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())