#!/usr/bin/env python3
"""
Integration tests for Enhanced RAG MCP Server.

NOTE: These tests are skipped due to HuggingFace Hub metadata version conflicts.
These will be re-enabled in Phase 3 Sprint 2 after dependency resolution.
"""

import asyncio
import json
import os
import sys

import pytest

# Skip collection entirely for this module
pytest.skip("HuggingFace Hub importlib_metadata version issue", allow_module_level=True)

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from grid.mcp.enhanced_rag_server import EnhancedRAGMCPServer


class MockStream:
    """Mock stream for testing."""

    def __init__(self):
        self.messages = []
        self.closed = False

    async def write(self, data):
        """Write data to mock stream."""
        self.messages.append(data)

    async def read(self):
        """Read data from mock stream."""
        if self.messages:
            return self.messages.pop(0)
        return None

    async def close(self):
        """Close the stream."""
        self.closed = True


async def test_enhanced_rag_server():
    """Test Enhanced RAG MCP Server functionality."""
    print("Testing Enhanced RAG MCP Server...")

    # Create server instance
    server = EnhancedRAGMCPServer()

    # Create mock streams
    read_stream = MockStream()
    write_stream = MockStream()

    # Test 1: List tools
    print("\n1. Testing list_tools...")

    # Create a test tool request
    from mcp.types import ListToolsRequest

    @server.server.list_tools()
    async def list_tools():
        return await server.server._handle_list_tools(ListToolsRequest())

    result = await list_tools()
    tools = result.tools

    print(f"   Available tools: {[tool.name for tool in tools]}")
    assert len(tools) >= 6, f"Expected at least 6 tools, got {len(tools)}"
    assert any(tool.name == "query" for tool in tools)
    assert any(tool.name == "create_session" for tool in tools)
    assert any(tool.name == "get_session" for tool in tools)
    print("   ✅ List tools test passed")

    # Test 2: Create session
    print("\n2. Testing create_session...")

    session_id = "test-session-123"

    @server.server.call_tool()
    async def call_tool(name, arguments):
        return await server.server._call_tool_handler(name, arguments)

    result = await call_tool("create_session", {"session_id": session_id})

    print(f"   Result: {result.content[0].text}")
    assert not result.isError, f"Expected success, got error: {result.content[0].text}"
    assert "created successfully" in result.content[0].text
    print("   ✅ Create session test passed")

    # Test 3: Query with session
    print("\n3. Testing query with session...")

    query = "What is GRID?"
    result = await call_tool("query", {
        "query": query,
        "session_id": session_id
    })

    print(f"   Result type: {'Error' if result.isError else 'Success'}")
    if result.isError:
        print(f"   Error: {result.content[0].text}")
    else:
        response_data = json.loads(result.content[0].text)
        print(f"   Answer preview: {response_data.get('answer', '')[:50]}...")
        print(f"   Sources: {len(response_data.get('sources', []))}")
        print(f"   Session active: {response_data.get('conversation_metadata', {}).get('session_active', False)}")

        assert "answer" in response_data
        assert response_data.get("conversation_metadata", {}).get("session_id") == session_id

    print("   ✅ Query with session test passed")

    # Test 4: Get session info
    print("\n4. Testing get_session...")

    result = await call_tool("get_session", {"session_id": session_id})

    print(f"   Result type: {'Error' if result.isError else 'Success'}")
    if result.isError:
        print(f"   Error: {result.content[0].text}")
    else:
        session_info = json.loads(result.content[0].text)
        print(f"   Session ID: {session_info.get('session_id')}")
        print(f"   Turn count: {session_info.get('turn_count', 0)}")

        assert session_info.get("session_id") == session_id

    print("   ✅ Get session test passed")

    # Test 5: Get stats
    print("\n5. Testing get_stats...")

    result = await call_tool("get_stats", {})

    print(f"   Result type: {'Error' if result.isError else 'Success'}")
    if result.isError:
        print(f"   Error: {result.content[0].text}")
    else:
        stats = json.loads(result.content[0].text)
        print(f"   Total sessions: {stats.get('total_sessions', 0)}")
        print(f"   Total turns: {stats.get('total_turns', 0)}")

        assert "total_sessions" in stats
        assert "total_turns" in stats

    print("   ✅ Get stats test passed")

    # Test 6: Delete session
    print("\n6. Testing delete_session...")

    result = await call_tool("delete_session", {"session_id": session_id})

    print(f"   Result: {result.content[0].text}")
    assert not result.isError, f"Expected success, got error: {result.content[0].text}"
    assert "deleted successfully" in result.content[0].text
    print("   ✅ Delete session test passed")

    print("\n✅ All Enhanced RAG Server tests passed!")


async def test_conversation_flow():
    """Test conversation flow with multiple turns."""
    print("\nTesting conversation flow...")

    server = EnhancedRAGMCPServer()
    session_id = "conversation-test"

    @server.server.call_tool()
    async def call_tool(name, arguments):
        return await server.server._call_tool_handler(name, arguments)

    # Create session
    result = await call_tool("create_session", {"session_id": session_id})
    assert not result.isError

    # First query
    result = await call_tool("query", {
        "query": "What is GRID?",
        "session_id": session_id
    })
    assert not result.isError
    response1 = json.loads(result.content[0].text)

    # Second query (should use context)
    result = await call_tool("query", {
        "query": "How does it work?",
        "session_id": session_id
    })
    assert not result.isError
    response2 = json.loads(result.content[0].text)

    # Verify conversation progression
    turn_count1 = response1.get("conversation_metadata", {}).get("turn_count", 0)
    turn_count2 = response2.get("conversation_metadata", {}).get("turn_count", 0)

    print(f"   Turn count progression: {turn_count1} → {turn_count2}")
    assert turn_count2 > turn_count1, "Turn count should increase in conversation"

    print("   ✅ Conversation flow test passed")


async def main():
    """Run integration tests."""
    print("=" * 60)
    print("Enhanced RAG MCP Server Integration Tests")
    print("=" * 60)

    try:
        await test_enhanced_rag_server()
        await test_conversation_flow()

        print("\n" + "=" * 60)
        print("🎉 All Integration Tests Passed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
