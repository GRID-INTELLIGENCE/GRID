#!/usr/bin/env python3
"""
Test script to verify performance improvements in conversational RAG.
"""

import asyncio
import os
import sys
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from tools.rag.conversational_rag import create_conversational_rag_engine


async def test_fallback_mechanism():
    """Test the fallback mechanism."""
    print("Testing fallback mechanism...")

    engine = create_conversational_rag_engine()

    # Test query that should trigger fallback
    start_time = time.perf_counter()
    result = await engine.query("What is the meaning of life?")
    latency = (time.perf_counter() - start_time) * 1000

    print("Query: 'What is the meaning of life?'")
    print(f"Latency: {latency:.1f}ms")
    print(f"Answer: {result['answer'][:100]}...")
    print(f"Sources: {len(result['sources'])}")
    print(f"Fallback used: {result.get('fallback_used', False)}")
    print(f"Success: {'answer' in result}")

    return result


async def test_conversation_flow():
    """Test conversation flow with session."""
    print("\nTesting conversation flow...")

    engine = create_conversational_rag_engine()
    session_id = engine.create_session("test-conversation")

    queries = ["What is GRID?", "How does it work?", "What are the 9 cognition patterns?"]

    for i, query in enumerate(queries):
        start_time = time.perf_counter()
        result = await engine.query(query, session_id=session_id)
        latency = (time.perf_counter() - start_time) * 1000

        print(f"\nQuery {i+1}: '{query}'")
        print(f"Latency: {latency:.1f}ms")
        print(f"Answer: {result['answer'][:80]}...")
        print(f"Turn count: {result['conversation_metadata']['turn_count']}")
        print(f"Sources: {len(result['sources'])}")


async def test_auto_indexing():
    """Test auto-indexing functionality."""
    print("\nTesting auto-indexing...")

    engine = create_conversational_rag_engine()
    stats = engine.get_conversation_stats()

    print(f"Auto-indexing attempts: {stats.get('memory_stats', {}).get('auto_indexing_attempts', 0)}")
    print(f"Auto-indexing successes: {stats.get('memory_stats', {}).get('auto_indexing_successes', 0)}")

    # Test query that should now work with indexed content
    start_time = time.perf_counter()
    result = await engine.query("What is conversational RAG?")
    latency = (time.perf_counter() - start_time) * 1000

    print("\nQuery: 'What is conversational RAG?'")
    print(f"Latency: {latency:.1f}ms")
    print(f"Sources: {len(result['sources'])}")
    print(f"Fallback used: {result.get('fallback_used', False)}")


async def main():
    """Run performance improvement tests."""
    print("=" * 60)
    print("GRID Conversational RAG Performance Improvements Test")
    print("=" * 60)

    try:
        await test_fallback_mechanism()
        await test_conversation_flow()
        await test_auto_indexing()

        print("\n" + "=" * 60)
        print("Performance improvements test completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
