#!/usr/bin/env python3
"""
Simple integration test for Enhanced RAG MCP Server structure.

This test verifies the server structure without requiring heavy ML dependencies.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))


def test_server_structure():
    """Test that the enhanced RAG server structure is correct."""
    print("Testing Enhanced RAG Server Structure...")

    # Test 1: Check server file exists
    server_path = Path(__file__).parent.parent.parent / 'src' / 'grid' / 'mcp' / 'enhanced_rag_server.py'
    assert server_path.exists(), f"Server file not found: {server_path}"
    print(f"   ✅ Server file exists: {server_path}")

    # Test 2: Check conversational RAG file exists
    conversational_rag_path = Path(__file__).parent.parent.parent / 'src' / 'tools' / 'rag' / 'conversational_rag.py'
    assert conversational_rag_path.exists(), f"Conversational RAG file not found: {conversational_rag_path}"
    print(f"   ✅ Conversational RAG file exists: {conversational_rag_path}")

    # Test 3: Check conversation.py exists
    conversation_path = Path(__file__).parent.parent.parent / 'src' / 'tools' / 'rag' / 'conversation.py'
    assert conversation_path.exists(), f"Conversation file not found: {conversation_path}"
    print(f"   ✅ Conversation file exists: {conversation_path}")

    # Test 4: Check RAG engine exists
    rag_engine_path = Path(__file__).parent.parent.parent / 'src' / 'tools' / 'rag' / 'rag_engine.py'
    assert rag_engine_path.exists(), f"RAG engine file not found: {rag_engine_path}"
    print(f"   ✅ RAG engine file exists: {rag_engine_path}")

    # Test 5: Check config file exists
    config_path = Path(__file__).parent.parent.parent / 'src' / 'tools' / 'rag' / 'config.py'
    assert config_path.exists(), f"Config file not found: {config_path}"
    print(f"   ✅ Config file exists: {config_path}")

    # Test 6: Verify server can be imported (structure only)
    try:
        # Just check if we can read the file
        with open(server_path) as f:
            content = f.read()

        # Check for key components
        assert 'class EnhancedRAGMCPServer' in content, "EnhancedRAGMCPServer class not found"
        assert 'query' in content, "query tool not found"
        assert 'create_session' in content, "create_session tool not found"
        assert 'get_session' in content, "get_session tool not found"
        assert 'delete_session' in content, "delete_session tool not found"
        assert 'get_stats' in content, "get_stats tool not found"
        assert 'index_documents' in content, "index_documents tool not found"

        print("   ✅ Server structure verified")
        print("      - EnhancedRAGMCPServer class found")
        print("      - 6 tools registered: query, create_session, get_session, delete_session, get_stats, index_documents")

    except Exception as e:
        print(f"   ❌ Server structure check failed: {e}")
        raise

    # Test 7: Check integration test file exists
    integration_test_path = Path(__file__).parent / 'test_enhanced_rag_integration.py'
    assert integration_test_path.exists(), f"Integration test file not found: {integration_test_path}"
    print(f"   ✅ Integration test file exists: {integration_test_path}")

    print("\n" + "=" * 70)
    print("✅ Enhanced RAG Server Structure Verification Complete!")
    print("=" * 70)
    print("\nVerified Components:")
    print("✅ Enhanced RAG MCP Server file")
    print("✅ Conversational RAG Engine")
    print("✅ Conversation Memory System")
    print("✅ RAG Engine Base")
    print("✅ Configuration Module")
    print("✅ Integration Test Suite")
    print("\nServer Tools:")
    print("  - query: Query the RAG knowledge base with conversation support")
    print("  - create_session: Create a new conversation session")
    print("  - get_session: Get information about a session")
    print("  - delete_session: Delete a conversation session")
    print("  - get_stats: Get RAG system statistics")
    print("  - index_documents: Index documents for RAG")


if __name__ == "__main__":
    try:
        test_server_structure()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
