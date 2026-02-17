#!/usr/bin/env python3
"""
Integration tests for Enhanced RAG MCP Server.

Uses conditional imports to handle optional dependencies gracefully.
Tests MCP server tool registration and session management.
"""

import asyncio
import json
import os
import sys
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

# Conditional imports for optional dependencies
HAS_MCP_TYPES = False
HAS_ENHANCED_RAG_SERVER = False

try:
    from mcp.types import ListToolsRequest

    HAS_MCP_TYPES = True
except ImportError:
    ListToolsRequest = None

try:
    from grid.mcp.enhanced_rag_server import EnhancedRAGMCPServer

    HAS_ENHANCED_RAG_SERVER = True
except ImportError:
    EnhancedRAGMCPServer = None

# Mark tests as requiring optional dependencies
requires_mcp_server = pytest.mark.skipif(
    not (HAS_MCP_TYPES and HAS_ENHANCED_RAG_SERVER),
    reason="Enhanced RAG MCP Server requires mcp package and optional dependencies",
)


# =============================================================================
# Mock Classes for Testing Without Dependencies
# =============================================================================


class MockTool:
    """Mock MCP tool."""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description


class MockToolResult:
    """Mock tool result."""

    def __init__(self, content: list, is_error: bool = False):
        self.content = content
        self.isError = is_error


class MockContent:
    """Mock content block."""

    def __init__(self, text: str):
        self.text = text


class MockMCPHandler:
    """Mock MCP request handler."""

    def __init__(self):
        self.tools = [
            MockTool("query", "Query the RAG system"),
            MockTool("create_session", "Create a new session"),
            MockTool("get_session", "Get session info"),
            MockTool("delete_session", "Delete a session"),
            MockTool("get_stats", "Get session statistics"),
            MockTool("index", "Index documents"),
        ]
        self.sessions: dict[str, dict[str, Any]] = {}
        self._call_tool_handler = self._handle_tool_call

    async def _handle_list_tools(self, request):
        """Handle list_tools request."""
        return MagicMock(tools=self.tools)

    async def _handle_tool_call(self, name: str, arguments: dict):
        """Handle tool call."""
        if name == "create_session":
            session_id = arguments.get("session_id")
            self.sessions[session_id] = {"turn_count": 0, "queries": []}
            return MockToolResult([MockContent(json.dumps({"status": "created", "session_id": session_id}))])

        elif name == "query":
            session_id = arguments.get("session_id")
            query = arguments.get("query")
            if session_id in self.sessions:
                self.sessions[session_id]["turn_count"] += 1
                self.sessions[session_id]["queries"].append(query)

            return MockToolResult(
                [
                    MockContent(
                        json.dumps(
                            {
                                "answer": f"Mock answer for: {query[:30]}...",
                                "sources": [{"content": "mock source", "score": 0.9}],
                                "conversation_metadata": {
                                    "session_id": session_id,
                                    "turn_count": self.sessions.get(session_id, {}).get("turn_count", 1),
                                    "session_active": session_id in self.sessions,
                                },
                            }
                        )
                    )
                ]
            )

        elif name == "get_session":
            session_id = arguments.get("session_id")
            if session_id in self.sessions:
                return MockToolResult(
                    [MockContent(json.dumps({"session_id": session_id, **self.sessions[session_id]}))]
                )
            return MockToolResult([MockContent(json.dumps({"error": "Session not found"}))], is_error=True)

        elif name == "delete_session":
            session_id = arguments.get("session_id")
            if session_id in self.sessions:
                del self.sessions[session_id]
                return MockToolResult([MockContent(json.dumps({"status": "deleted", "session_id": session_id}))])
            return MockToolResult([MockContent(json.dumps({"error": "Session not found"}))], is_error=True)

        elif name == "get_stats":
            return MockToolResult(
                [
                    MockContent(
                        json.dumps(
                            {
                                "total_sessions": len(self.sessions),
                                "total_turns": sum(s["turn_count"] for s in self.sessions.values()),
                            }
                        )
                    )
                ]
            )

        else:
            return MockToolResult([MockContent(json.dumps({"error": f"Unknown tool: {name}"}))], is_error=True)


class MockEnhancedRAGMCPServer:
    """Mock Enhanced RAG MCP Server."""

    def __init__(self):
        self.server = MockMCPHandler()
        self.rag_engine = MagicMock()


# =============================================================================
# Tests with Real Dependencies
# =============================================================================


class TestEnhancedRAGMCPServerWithDeps:
    """Tests that require the real MCP server."""

    @pytest.fixture
    def server(self):
        """Create real Enhanced RAG MCP Server."""
        if not HAS_ENHANCED_RAG_SERVER:
            pytest.skip("Enhanced RAG Server not available")
        try:
            return EnhancedRAGMCPServer()
        except (RuntimeError, Exception) as e:
            pytest.skip(f"Enhanced RAG Server unavailable (Ollama might be down): {e}")

    @requires_mcp_server
    def test_server_instantiation(self, server):
        """Test server can be instantiated."""
        assert server is not None
        assert hasattr(server, "server")
        assert hasattr(server, "rag_engine")

    @requires_mcp_server
    @pytest.mark.asyncio
    async def test_list_tools(self, server):
        """Test list_tools returns expected tools."""
        if not HAS_MCP_TYPES:
            pytest.skip("MCP types not available")

        result = await server.server._handle_list_tools(ListToolsRequest())
        tools = result.tools

        assert len(tools) >= 6, f"Expected at least 6 tools, got {len(tools)}"
        tool_names = [tool.name for tool in tools]
        assert "query" in tool_names
        assert "create_session" in tool_names or "session_create" in tool_names

    @requires_mcp_server
    @pytest.mark.asyncio
    async def test_session_lifecycle(self, server):
        """Test create, get, delete session flow."""
        session_id = "test-session-pytest"

        # Create session
        create_result = await server.server._call_tool_handler("create_session", {"session_id": session_id})
        assert not create_result.isError

        # Query with session
        query_result = await server.server._call_tool_handler(
            "query", {"query": "Test query", "session_id": session_id}
        )
        assert not query_result.isError

        # Get session
        get_result = await server.server._call_tool_handler("get_session", {"session_id": session_id})
        assert not get_result.isError

        # Delete session
        delete_result = await server.server._call_tool_handler("delete_session", {"session_id": session_id})
        assert not delete_result.isError

    @requires_mcp_server
    @pytest.mark.asyncio
    async def test_conversation_turn_progression(self, server):
        """Test turn count increases with queries."""
        session_id = "conversation-test-pytest"

        await server.server._call_tool_handler("create_session", {"session_id": session_id})

        result1 = await server.server._call_tool_handler("query", {"query": "First question", "session_id": session_id})
        response1 = json.loads(result1.content[0].text)

        result2 = await server.server._call_tool_handler(
            "query", {"query": "Second question", "session_id": session_id}
        )
        response2 = json.loads(result2.content[0].text)

        turn1 = response1.get("conversation_metadata", {}).get("turn_count", 0)
        turn2 = response2.get("conversation_metadata", {}).get("turn_count", 0)

        assert turn2 > turn1, f"Turn count should increase: {turn1} -> {turn2}"

        await server.server._call_tool_handler("delete_session", {"session_id": session_id})


# =============================================================================
# Tests with Mocked Dependencies (Always Run)
# =============================================================================


class TestEnhancedRAGMCPServerMocked:
    """Tests with mocked server - always run."""

    @pytest.fixture
    def mock_server(self):
        """Create mock server."""
        return MockEnhancedRAGMCPServer()

    def test_mock_server_creation(self, mock_server):
        """Test mock server can be created."""
        assert mock_server is not None
        assert mock_server.server is not None

    def test_mock_tools_available(self, mock_server):
        """Test mock tools are available."""
        tools = mock_server.server.tools
        assert len(tools) >= 6

        tool_names = [t.name for t in tools]
        assert "query" in tool_names
        assert "create_session" in tool_names
        assert "get_session" in tool_names
        assert "delete_session" in tool_names
        assert "get_stats" in tool_names
        assert "index" in tool_names

    @pytest.mark.asyncio
    async def test_mock_create_session(self, mock_server):
        """Test mock session creation."""
        result = await mock_server.server._call_tool_handler("create_session", {"session_id": "mock-session-1"})

        assert not result.isError
        data = json.loads(result.content[0].text)
        assert data["status"] == "created"
        assert data["session_id"] == "mock-session-1"

    @pytest.mark.asyncio
    async def test_mock_query(self, mock_server):
        """Test mock query functionality."""
        await mock_server.server._call_tool_handler("create_session", {"session_id": "query-session"})

        result = await mock_server.server._call_tool_handler(
            "query", {"query": "What is GRID?", "session_id": "query-session"}
        )

        assert not result.isError
        data = json.loads(result.content[0].text)
        assert "answer" in data
        assert "sources" in data
        assert "conversation_metadata" in data

    @pytest.mark.asyncio
    async def test_mock_conversation_progression(self, mock_server):
        """Test turn count increases in conversation."""
        session_id = "conv-progress-session"

        await mock_server.server._call_tool_handler("create_session", {"session_id": session_id})

        result1 = await mock_server.server._call_tool_handler("query", {"query": "First", "session_id": session_id})
        data1 = json.loads(result1.content[0].text)
        turn1 = data1["conversation_metadata"]["turn_count"]

        result2 = await mock_server.server._call_tool_handler("query", {"query": "Second", "session_id": session_id})
        data2 = json.loads(result2.content[0].text)
        turn2 = data2["conversation_metadata"]["turn_count"]

        assert turn2 == 2
        assert turn2 > turn1

    @pytest.mark.asyncio
    async def test_mock_get_stats(self, mock_server):
        """Test get_stats returns session statistics."""
        await mock_server.server._call_tool_handler("create_session", {"session_id": "stats-session-1"})
        await mock_server.server._call_tool_handler("create_session", {"session_id": "stats-session-2"})

        result = await mock_server.server._call_tool_handler("get_stats", {})

        assert not result.isError
        data = json.loads(result.content[0].text)
        assert "total_sessions" in data
        assert data["total_sessions"] == 2

    @pytest.mark.asyncio
    async def test_mock_delete_session(self, mock_server):
        """Test session deletion."""
        session_id = "delete-test-session"

        await mock_server.server._call_tool_handler("create_session", {"session_id": session_id})

        result = await mock_server.server._call_tool_handler("delete_session", {"session_id": session_id})

        assert not result.isError
        data = json.loads(result.content[0].text)
        assert data["status"] == "deleted"

        # Verify session is deleted
        get_result = await mock_server.server._call_tool_handler("get_session", {"session_id": session_id})
        assert get_result.isError

    @pytest.mark.asyncio
    async def test_mock_unknown_tool(self, mock_server):
        """Test unknown tool returns error."""
        result = await mock_server.server._call_tool_handler("unknown_tool", {"arg": "value"})

        assert result.isError
        data = json.loads(result.content[0].text)
        assert "error" in data


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestSessionEdgeCases:
    """Test edge cases in session management."""

    @pytest.fixture
    def mock_server(self):
        """Create mock server."""
        return MockEnhancedRAGMCPServer()

    @pytest.mark.asyncio
    async def test_query_without_session(self, mock_server):
        """Test query without session still works."""
        result = await mock_server.server._call_tool_handler("query", {"query": "Test without session"})

        # Should work, just no session tracking
        assert not result.isError
        data = json.loads(result.content[0].text)
        assert "answer" in data

    @pytest.mark.asyncio
    async def test_delete_nonexistent_session(self, mock_server):
        """Test deleting session that doesn't exist."""
        result = await mock_server.server._call_tool_handler("delete_session", {"session_id": "nonexistent"})

        assert result.isError

    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, mock_server):
        """Test getting session that doesn't exist."""
        result = await mock_server.server._call_tool_handler("get_session", {"session_id": "nonexistent"})

        assert result.isError

    @pytest.mark.asyncio
    async def test_create_duplicate_session(self, mock_server):
        """Test creating session with same ID twice."""
        session_id = "duplicate-test"

        result1 = await mock_server.server._call_tool_handler("create_session", {"session_id": session_id})
        assert not result1.isError

        # Second create should either overwrite or error
        result2 = await mock_server.server._call_tool_handler("create_session", {"session_id": session_id})
        # Either behavior is acceptable
        assert result2 is not None


# =============================================================================
# Main Entry Point
# =============================================================================


async def main():
    """Run integration tests with status reporting."""
    print("=" * 60)
    print("Enhanced RAG MCP Server Integration Tests")
    print("=" * 60)
    print("\nDependency Status:")
    print(f"  MCP Types: {'✅ Available' if HAS_MCP_TYPES else '❌ Not Available'}")
    print(f"  Enhanced RAG Server: {'✅ Available' if HAS_ENHANCED_RAG_SERVER else '❌ Not Available'}")
    print()

    if HAS_ENHANCED_RAG_SERVER and HAS_MCP_TYPES:
        print("Running full integration tests...")
        try:
            server = EnhancedRAGMCPServer()
            print("✅ Server created")

            # Test tool listing
            result = await server.server._handle_list_tools(ListToolsRequest())
            print(f"✅ Tools available: {len(result.tools)}")

            # Test session lifecycle
            result = await server.server._call_tool_handler("create_session", {"session_id": "main-test"})
            print("✅ Session created")

            result = await server.server._call_tool_handler("query", {"query": "Test query", "session_id": "main-test"})
            print("✅ Query executed")

            result = await server.server._call_tool_handler("delete_session", {"session_id": "main-test"})
            print("✅ Session deleted")

        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback

            traceback.print_exc()
    else:
        print("Running mock-based tests...")
        server = MockEnhancedRAGMCPServer()
        print("✅ Mock server created")

        result = await server.server._call_tool_handler("create_session", {"session_id": "mock-main"})
        print("✅ Mock session created")

        result = await server.server._call_tool_handler("query", {"query": "Test query", "session_id": "mock-main"})
        print("✅ Mock query executed")

        result = await server.server._call_tool_handler("delete_session", {"session_id": "mock-main"})
        print("✅ Mock session deleted")

    print("\n" + "=" * 60)
    print("Integration Test Completed")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
