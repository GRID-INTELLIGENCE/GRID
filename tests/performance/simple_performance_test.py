#!/usr/bin/env python3
"""
Simple performance test for conversational RAG improvements.
"""

import asyncio
import os
import sys
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from tools.rag.conversational_rag import create_conversational_rag_engine


async def test_fallback_performance():
    """Test fallback mechanism performance."""
    print("Testing fallback mechanism performance...")

    engine = create_conversational_rag_engine()

    # Test query that should trigger fallback
    queries = [
        "What is the meaning of life?",
        "Explain quantum computing",
        "Who won the world series in 2020?"
    ]

    for query in queries:
        start_time = time.perf_counter()
        result = await engine.query(query)
        latency = (time.perf_counter() - start_time) * 1000

        print(f"\nQuery: '{query}'")
        print(f"Latency: {latency:.1f}ms")
        print(f"Answer length: {len(result['answer'])} chars")
        print(f"Fallback used: {result.get('fallback_used', False)}")
        print(f"Sources: {len(result['sources'])}")

        if len(result['answer']) > 50:
            print(f"Answer preview: {result['answer'][:50]}...")


async def test_conversation_performance():
    """Test conversation performance."""
    print("\nTesting conversation performance...")

    engine = create_conversational_rag_engine()
    session_id = engine.create_session("test-performance")

    queries = [
        "What is GRID?",
        "How does it work?",
        "What are the main components?"
    ]

    for i, query in enumerate(queries):
        start_time = time.perf_counter()
        result = await engine.query(query, session_id=session_id)
        latency = (time.perf_counter() - start_time) * 1000

        print(f"\nQuery {i+1}: '{query}'")
        print(f"Latency: {latency:.1f}ms")
        print(f"Turn count: {result['conversation_metadata']['turn_count']}")
        print(f"Sources: {len(result['sources'])}")


async def test_metrics():
    """Test metrics collection."""
    print("\nTesting metrics collection...")

    engine = create_conversational_rag_engine()

    # Run a few queries
    await engine.query("Test query 1")
    await engine.query("Test query 2")

    session_id = engine.create_session("metrics-test")
    await engine.query("Test query 3", session_id=session_id)

    # Get metrics
    stats = engine.get_conversation_stats()

    print(f"Total sessions: {stats['total_sessions']}")
    print(f"Total turns: {stats['total_turns']}")
    print(f"Multi-hop queries: {stats['multi_hop_queries']}")
    print(f"Session avg turns: {stats['session_average_turns']:.1f}")


async def main():
    """Run simple performance tests."""
    print("=" * 60)
    print("GRID Conversational RAG Performance Test")
    print("=" * 60)

    try:
        await test_fallback_performance()
        await test_conversation_performance()
        await test_metrics()

        print("\n" + "=" * 60)
        print("Performance test completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
