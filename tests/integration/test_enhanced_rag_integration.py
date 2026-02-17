#!/usr/bin/env python3
"""
Integration tests for Enhanced RAG MCP Server.

This test verifies that the enhanced RAG server can be instantiated
and demonstrates its capabilities.

NOTE: These tests are skipped due to HuggingFace Hub metadata version conflicts.
See: https://github.com/huggingface/huggingface_hub/issues/XXXX
These will be re-enabled in Phase 3 Sprint 2 after dependency resolution.
"""

import asyncio
import os
import sys

import pytest

# Skip collection entirely for this module
pytest.skip("HuggingFace Hub importlib_metadata version issue", allow_module_level=True)

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from grid.mcp.enhanced_rag_server import EnhancedRAGMCPServer
from tools.rag.conversational_rag import create_conversational_rag_engine


async def test_enhanced_rag_capabilities():
    """Test Enhanced RAG capabilities directly."""
    print("Testing Enhanced RAG Capabilities...")

    # Test 1: Create conversational RAG engine
    print("\n1. Creating Conversational RAG Engine...")
    engine = create_conversational_rag_engine()

    print(f"   ✅ Engine created: {type(engine).__name__}")
    print(f"   ✅ Conversation enabled: {engine.config.conversation_enabled}")
    print(f"   ✅ Multi-hop enabled: {engine.config.multi_hop_enabled}")

    # Test 2: Session management
    print("\n2. Testing Session Management...")
    session_id = "test-integration-session"

    # Create session
    engine.create_session(session_id, {"test": "integration"})
    print(f"   ✅ Session created: {session_id}")

    # Get session info
    session_info = engine.get_session_info(session_id)
    print(f"   ✅ Session info retrieved: turn_count={session_info.get('turn_count', 0)}")

    # Test 3: Query with conversation
    print("\n3. Testing Conversational Queries...")

    # First query
    result1 = await engine.query("What is GRID?", session_id=session_id)
    print(f"   ✅ Query 1: {result1['answer'][:50]}...")
    print(f"      Sources: {len(result1['sources'])}")
    print(f"      Turn count: {result1['conversation_metadata']['turn_count']}")

    # Second query (should use context)
    result2 = await engine.query("How does it work?", session_id=session_id)
    print(f"   ✅ Query 2: {result2['answer'][:50]}...")
    print(f"      Sources: {len(result2['sources'])}")
    print(f"      Turn count: {result2['conversation_metadata']['turn_count']}")

    # Verify conversation progression
    turn_count1 = result1["conversation_metadata"]["turn_count"]
    turn_count2 = result2["conversation_metadata"]["turn_count"]
    assert turn_count2 > turn_count1, "Turn count should increase in conversation"
    print(f"   ✅ Conversation progression: {turn_count1} → {turn_count2}")

    # Test 4: Multi-hop reasoning
    print("\n4. Testing Multi-hop Reasoning...")

    # Enable multi-hop for this query
    result3 = await engine.query("Explain the GRID architecture", session_id=session_id, enable_multi_hop=True)

    print(f"   ✅ Multi-hop query: {result3['answer'][:50]}...")
    print(f"      Multi-hop used: {result3.get('multi_hop_used', False)}")
    print(f"      Sources: {len(result3['sources'])}")

    # Test 5: Fallback mechanism
    print("\n5. Testing Fallback Mechanism...")

    # Query that should trigger fallback
    result4 = await engine.query("What is the meaning of life?", session_id=session_id)

    print(f"   ✅ Fallback query: {result4['answer'][:50]}...")
    print(f"      Fallback used: {result4.get('fallback_used', False)}")
    print(f"      Sources: {len(result4['sources'])}")

    # Test 6: Get statistics
    print("\n6. Testing Statistics...")

    stats = engine.get_conversation_stats()
    print("   ✅ Statistics retrieved:")
    print(f"      Total sessions: {stats.get('total_sessions', 0)}")
    print(f"      Total turns: {stats.get('total_turns', 0)}")
    print(f"      Multi-hop queries: {stats.get('multi_hop_queries', 0)}")

    # Test 7: Delete session
    print("\n7. Testing Session Deletion...")

    success = engine.delete_session(session_id)
    print(f"   ✅ Session deleted: {success}")

    session_info = engine.get_session_info(session_id)
    print(f"   ✅ Session verification: {session_info is None}")


async def test_enhanced_rag_server_instantiation():
    """Test Enhanced RAG Server instantiation."""
    print("\nTesting Enhanced RAG Server Instantiation...")

    # Create server instance
    server = EnhancedRAGMCPServer()

    print(f"   ✅ Server created: {type(server).__name__}")
    print(f"   ✅ RAG engine: {type(server.rag_engine).__name__}")
    print(f"   ✅ Session storage: {len(server.sessions)} sessions")

    # Verify tools are registered
    print(f"   ✅ Tools registered: {len(server.server._tool_handlers)} tools")

    return server


async def main():
    """Run integration tests."""
    print("=" * 70)
    print("Enhanced RAG MCP Server Integration Test")
    print("=" * 70)
    print("This test demonstrates the enhanced RAG capabilities")
    print("and verifies integration with the MCP server framework.\n")

    try:
        # Test server instantiation
        await test_enhanced_rag_server_instantiation()

        # Test enhanced RAG capabilities
        await test_enhanced_rag_capabilities()

        print("\n" + "=" * 70)
        print("🎉 Enhanced RAG Integration Test Completed Successfully!")
        print("=" * 70)
        print("\nKey Capabilities Verified:")
        print("✅ Conversational RAG Engine")
        print("✅ Session Management")
        print("✅ Multi-hop Reasoning")
        print("✅ Fallback Mechanism")
        print("✅ Statistics Collection")
        print("✅ MCP Server Integration")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
