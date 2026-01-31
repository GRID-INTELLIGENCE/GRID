#!/usr/bin/env python3
"""
Demo script showcasing the new conversational RAG capabilities.
"""

import asyncio
import os
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tools.rag.conversational_rag import create_conversational_rag_engine


async def demo_conversational_rag():
    """Demonstrate conversational RAG features."""
    print("=" * 60)
    print("GRID Conversational RAG Demo")
    print("=" * 60)

    # Create engine
    print("\n1. Creating Conversational RAG Engine...")
    engine = create_conversational_rag_engine()

    print(f"   Check Conversation enabled: {engine.config.conversation_enabled}")
    print(f"   Check Multi-hop enabled: {engine.config.multi_hop_enabled}")
    print(f"   Check Memory size: {engine.config.conversation_memory_size} sessions")

    # Create session
    print("\n2. Creating Conversation Session...")
    session_id = f"demo-{datetime.now().strftime('%H%M%S')}"
    engine.create_session(session_id, {"type": "demo", "created": datetime.now().isoformat()})

    session_info = engine.get_session_info(session_id)
    if session_info:
        print(f"   Check Session ID: {session_info.get('session_id', 'N/A')}")
        print(f"   Check Turn count: {session_info.get('turn_count', 0)}")
        print(f"   Check Created: {session_info.get('created_at', 'N/A')}")
    else:
        print("   Check Session info: Not available")

    # Mock the RAG query for demo (since we don't have actual docs indexed)
    print("\n3. Mocking Conversation Queries...")

    # Mock responses for demonstration
    mock_responses = [
        ("What is the GRID system?",
         "GRID is a geometric resonance intelligence driver that explores complex systems through 9 cognition patterns."),
        ("How does it handle documentation?",
         "GRID uses local-first RAG with ChromaDB and Ollama for retrieving and generating contextually relevant information."),
        ("What about conversation memory?",
         "The conversational RAG engine maintains session-based memory with configurable context windows and multi-hop reasoning.")
    ]

    for i, (query, answer) in enumerate(mock_responses):
        print(f"\n   Query {i+1}: {query}")

        # Create mock result
        result = {
            "answer": answer,
            "sources": [
                {
                    "text": "Documentation about GRID system.",
                    "metadata": {"path": f"docs/grid_system_doc_{i+1}.md", "chunk_index": 1}
                }
            ],
            "conversation_metadata": {
                "session_id": session_id,
                "session_active": True,
                "context_used": i > 0,
                "turn_count": i + 1
            }
        }

        print(f"   Answer: {result['answer'][:80]}...")
        print(f"   Sources: {len(result['sources'])} document(s)")
        print(f"   Turn count: {result['conversation_metadata']['turn_count']}")

    # Show enhanced capabilities
    print("\n4. Enhanced Features Demonstration...")

    # Citation quality
    print("   Check Citation Quality: Enhanced metadata with confidence scoring")
    print("   Check Conversation Context: Previous turns influence current queries")
    print("   Check Session Management: Automatic cleanup and LRU management")

    if engine.config.multi_hop_enabled:
        print("   Check Multi-hop Reasoning: Complex queries trigger follow-up searches")

    # Show streaming capability
    print("\n5. Streaming API Capabilities...")
    print("   Check Real-time query progress")
    print("   Check WebSocket support for collaboration")
    print("   Check Batch processing with parallel execution")

    # Final stats
    print("\n6. Final Statistics...")
    stats = engine.get_conversation_stats()
    print(f"   Total sessions: {stats['total_sessions']}")
    print(f"   Total turns: {stats['total_turns']}")
    print(f"   Average turns per session: {stats['session_average_turns']:.1f}")

    print("\n" + "=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)


async def demo_streaming_api():
    """Demonstrate streaming API features."""
    print("\n" + "=" * 60)
    print("GRID Streaming API Demo")
    print("=" * 60)

    from application.mothership.routers.rag_streaming import chunk_text

    # Demo text chunking
    sample_text = "This demonstrates how the streaming API breaks down responses into manageable chunks for real-time display."
    chunks = chunk_text(sample_text, chunk_size=20)

    print("\n1. Text Chunking Example:")
    print(f"   Original text: {sample_text}")
    print(f"   Chunk count: {len(chunks)}")

    for i, chunk in enumerate(chunks):
        print(f"     Chunk {i+1}: {chunk}")

    # Demo stream chunk format
    try:
        from application.mothership.routers.rag_streaming import StreamChunk

        print("\n2. Stream Chunk Format:")
        chunk = StreamChunk("answer_chunk", {"chunk": "Sample response chunk", "chunk_number": 1})
        print(f"   Chunk JSON: {chunk.to_json()}")
    except ImportError:
        print("\n2. Stream Chunk Format: Not available (API module not loaded)")

    print("\n3. API Endpoint Examples:")
    print("   POST /rag/query/stream")
    print("   POST /rag/query/batch")
    print("   GET /rag/sessions/{id}")
    print("   GET /rag/stats")

    print("\n" + "=" * 60)
    print("Streaming API demo completed!")
    print("=" * 60)


if __name__ == "__main__":
    print("GRID Conversational RAG System Demo")
    print("This demonstrates the enhanced RAG capabilities with conversation and streaming support.\n")

    asyncio.run(demo_conversational_rag())
    asyncio.run(demo_streaming_api())
