"""Tests for conversational RAG system."""

import pytest
from unittest.mock import Mock, AsyncMock
from src.tools.rag.conversational_rag import (
    ConversationalRAGEngine, 
    create_conversational_rag_engine
)
from src.tools.rag.conversation import ConversationMemory, ConversationSession, ConversationTurn
from src.tools.rag.config import RAGConfig


@pytest.fixture
def mock_rag_engine():
    """Create a mock RAG engine for testing."""
    engine = Mock()
    engine.config = Mock()
    engine.config.conversation_enabled = True
    engine.config.multi_hop_enabled = False
    engine.config.conversation_context_window = 1000
    engine.query = AsyncMock(return_value={
        "answer": "Test answer",
        "sources": [{"text": "source text", "metadata": {"path": "test.py"}}]
    })
    return engine


@pytest.fixture
def conversation_memory():
    """Create conversation memory instance."""
    return ConversationMemory()


@pytest.fixture
def conversational_engine():
    """Create conversational RAG engine for testing."""
    config = RAGConfig()
    config.conversation_enabled = True
    config.multi_hop_enabled = False
    return ConversationalRAGEngine(config)


class TestConversationMemory:
    """Test conversation memory functionality."""
    
    def test_create_session(self, conversation_memory):
        """Test creating a new session."""
        session = conversation_memory.create_session("test-session")
        assert session.session_id == "test-session"
        assert conversation_memory.get_session("test-session") is not None
    
    def test_add_turn_to_session(self, conversation_memory):
        """Test adding a turn to a session."""
        conversation_memory.create_session("session1")
        turn = ConversationTurn("test query", "test response", [])
        conversation_memory.add_turn("session1", turn)
        
        session = conversation_memory.get_session("session1")
        assert len(session.turns) == 1
        assert session.turns[0].user_query == "test query"
    
    def test_get_context_for_query(self, conversation_memory):
        """Test conversation context generation."""
        session = conversation_memory.create_session("session1")
        
        # Add multiple turns
        turn1 = ConversationTurn("first query", "first response", [])
        turn2 = ConversationTurn("second query", "second response", [])
        
        session.add_turn(turn1)
        session.add_turn(turn2)
        
        context = session.get_context_for_query()
        assert "first query" in context
        assert "first response" in context
        assert "second query" in context
        assert "second response" in context
    
    def test_session_cleanup(self, conversation_memory):
        """Test automatic session cleanup."""
        # Set small TTL for testing
        conversation_memory.session_ttl_hours = 0.001  # ~3.6 seconds
        
        conversation_memory.create_session("session1")
        assert conversation_memory.get_session("session1") is not None
        
        # Simulate time passing
        import time
        time.sleep(0.1)
        
        # Create another session to trigger cleanup
        conversation_memory.create_session("session2")
        
        # First session should be cleaned up
        assert conversation_memory.get_session("session1") is None
        assert conversation_memory.get_session("session2") is not None


class TestConversationalRAGEngine:
    """Test conversational RAG engine functionality."""
    
    @pytest.mark.asyncio
    async def test_create_conversational_engine(self):
        """Test creating conversational RAG engine."""
        engine = create_conversational_rag_engine()
        assert isinstance(engine, ConversationalRAGEngine)
        assert hasattr(engine, 'conversation_memory')
        assert engine.config.conversation_enabled
    
    @pytest.mark.asyncio
    async def test_query_with_session(self, conversational_engine):
        """Test query with conversation session."""
        # Mock the parent query method
        conversational_engine._rag_engine = Mock()
        conversational_engine._rag_engine.query = AsyncMock(return_value={
            "answer": "Mock answer",
            "sources": []
        })
        
        result = await conversational_engine.query(
            "test query",
            session_id="test-session",
            enable_multi_hop=False
        )
        
        assert "answer" in result
        assert "conversation_metadata" in result
        assert result["conversation_metadata"]["session_id"] == "test-session"
    
    @pytest.mark.asyncio
    async def test_session_creation(self, conversational_engine):
        """Test creating and managing sessions."""
        session_id = conversational_engine.create_session("test-session")
        assert session_id == "test-session"
        
        session_info = conversational_engine.get_session_info("test-session")
        assert session_info["session_id"] == "test-session"
        assert session_info["turn_count"] == 0
        
        # Test deleting session
        result = conversational_engine.delete_session("test-session")
        assert result
        assert conversational_engine.get_session_info("test-session") is None
    
    @pytest.mark.asyncio
    async def test_conversation_stats(self, conversational_engine):
        """Test conversation statistics."""
        # Create session and add turns
        conversational_engine.create_session("session1")
        
        # Mock query to simulate conversation
        conversational_engine._rag_engine = Mock()
        conversational_engine._rag_engine.query = AsyncMock(return_value={
            "answer": "Answer 1",
            "sources": []
        })
        
        await conversational_engine.query("Query 1", session_id="session1")
        await conversational_engine.query("Query 2", session_id="session1")
        
        stats = conversational_engine.get_conversation_stats()
        assert stats["total_sessions"] == 1
        assert stats["total_turns"] == 2
        assert stats["session_average_turns"] == 2.0
    
    def test_enhance_query_with_context(self, conversational_engine):
        """Test query enhancement with conversation context."""
        # Test without context
        query = "What is RAG?"
        enhanced = conversational_engine._enhance_query_with_context(query, "")
        assert enhanced == query
        
        # Test with context
        context = "User: What is AI?\nAssistant: AI is artificial intelligence.\n"
        enhanced = conversational_engine._enhance_query_with_context(query, context)
        assert context in enhanced
        assert query in enhanced
    
    def test_improve_citation_quality(self, conversational_engine):
        """Test citation quality enhancement."""
        sources = [
            {
                "text": "Sample text",
                "metadata": {
                    "path": "test.py",
                    "chunk_index": 1
                }
            }
        ]
        
        enhanced_sources = conversational_engine._improve_citation_quality(sources)
        
        # Check enhancement
        assert len(enhanced_sources) == 1
        enhanced_source = enhanced_sources[0]
        
        # Should have citation fields
        assert "citation" in enhanced_source
        assert "confidence" in enhanced_source
        assert "citation_score" in enhanced_source["metadata"]
        assert "context_relevance" in enhanced_source["metadata"]
    
    def test_format_citation(self, conversational_engine):
        """Test citation formatting."""
        source = {
            "metadata": {
                "path": "src/test.py",
                "chunk_index": 5
            }
        }
        
        citation = conversational_engine._format_citation(source)
        assert "src/test.py" in citation
        assert "Chunk 5" in citation


class TestMultiHopReasoning:
    """Test multi-hop reasoning functionality."""
    
    @pytest.mark.asyncio
    async def test_multi_hop_chain(self):
        """Test multi-hop reasoning chain."""
        # Create engine with multi-hop enabled
        config = RAGConfig()
        config.multi_hop_enabled = True
        config.multi_hop_max_depth = 2
        engine = ConversationalRAGEngine(config)
        
        # Mock the base engine
        engine._rag_engine = Mock()
        engine._rag_engine.query = AsyncMock(return_value={
            "answer": "Base answer",
            "sources": [{"text": "source1", "metadata": {"path": "file1.py"}}]
        })
        
        # Mock multi-hop engine
        engine.multi_hop_engine = Mock()
        engine.multi_hop_engine.chain_retrieve = AsyncMock(return_value={
            "answer": "Multi-hop answer",
            "sources": [{"text": "source2", "metadata": {"path": "file2.py"}}],
            "multi_hop_used": True,
            "hops_performed": 2
        })
        
        result = await engine.query("complex query", enable_multi_hop=True)
        
        assert result["multi_hop_used"] == True
        assert "hops_performed" in result
        assert len(result["sources"]) > 0


class TestStreamingAPI:
    """Test streaming API functionality."""
    
    def test_chunk_text_function(self):
        """Test text chunking for streaming."""
        from src.application.mothership.routers.rag_streaming import chunk_text
        
        text = "Hello world, this is a test for chunking functionality"
        chunks = chunk_text(text, chunk_size=10)
        
        assert len(chunks) == 6  # Text has 52 chars, 10 chars per chunk
        assert "Hello" in chunks[0]
        assert "functionality" in chunks[-1]
    
    @pytest.mark.asyncio
    async def test_stream_chunk_generation(self):
        """Test stream chunk generation."""
        from src.application.mothership.routers.rag_streaming import StreamChunk
        
        chunk = StreamChunk("test_type", {"data": "test"})
        json_output = chunk.to_json()
        
        assert "test_type" in json_output
        assert "test" in json_output
        
        # Test that it's valid JSON
        import json
        parsed = json.loads(json_output)
        assert parsed["type"] == "test_type"
        assert parsed["data"]["data"] == "test"


if __name__ == "__main__":
    # Run interactive test
    import asyncio
    
    async def demo_conversation():
        """Demo conversation functionality."""
        engine = create_conversational_rag_engine()
        
        # Create session
        session_id = engine.create_session("demo-session")
        print(f"Created session: {session_id}")
        
        # Mock the RAG engine for demo
        engine._rag_engine = Mock()
        engine._rag_engine.query = AsyncMock(return_value={
            "answer": "This is a demo answer showing how conversation context is maintained.",
            "sources": [{
                "text": "Demo source text",
                "metadata": {"path": "demo.py", "chunk_index": 1}
            }]
        })
        
        # Execute queries
        for i in range(3):
            result = await engine.query(f"Demo query {i+1}", session_id=session_id)
            print(f"Query {i+1}: {result['answer'][:50]}...")
            print(f"Sources: {len(result['sources'])}")
        
        # Show session info
        session_info = engine.get_session_info(session_id)
        print(f"\nSession Info:")
        print(f"- Turns: {session_info['turn_count']}")
        print(f"- Created: {session_info['created_at']}")
        
        # Show stats
        stats = engine.get_conversation_stats()
        print(f"\nConversation Stats:")
        print(f"- Total sessions: {stats['total_sessions']}")
        print(f"- Total turns: {stats['total_turns']}")
    
    asyncio.run(demo_conversation())