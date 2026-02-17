"""Conversational RAG components for maintaining conversation context."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class ConversationTurn:
    """A single turn in a conversation."""

    user_query: str
    system_response: str
    retrieved_sources: list[dict[str, Any]]
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    query_embedding: list[float] | None = None
    response_embedding: list[float] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert turn to dictionary."""
        return {
            "user_query": self.user_query,
            "system_response": self.system_response,
            "retrieved_sources": self.retrieved_sources,
            "timestamp": self.timestamp.isoformat(),
            "has_query_embedding": self.query_embedding is not None,
            "has_response_embedding": self.response_embedding is not None,
        }


@dataclass
class ConversationSession:
    """A conversation session with multiple turns."""

    session_id: str
    turns: list[ConversationTurn] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_accessed: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_turn(self, turn: ConversationTurn) -> None:
        """Add a new turn to the conversation."""
        self.turns.append(turn)
        self.last_accessed = datetime.now(UTC)

    def get_recent_context(self, window_size: int = 5) -> str:
        """Get recent conversation context as text."""
        recent_turns = self.turns[-window_size:] if self.turns else []
        context_parts = []

        for turn in recent_turns:
            context_parts.append(f"User: {turn.user_query}")
            context_parts.append(f"Assistant: {turn.system_response}")

        return "\n".join(context_parts)

    def get_context_for_query(self, max_length: int = 1000) -> str:
        """Get conversation context formatted for LLM query."""
        context = self.get_recent_context()
        if len(context) > max_length:
            # Truncate from the beginning to keep recent context
            context = context[-max_length:]
        return context

    def to_dict(self) -> dict[str, Any]:
        """Convert session to dictionary."""
        return {
            "session_id": self.session_id,
            "turn_count": len(self.turns),
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "metadata": self.metadata,
            "turns": [turn.to_dict() for turn in self.turns],
        }


class ConversationMemory:
    """Manages multiple conversation sessions with persistence."""

    def __init__(self, max_sessions: int = 100, session_ttl_hours: int = 24):
        """Initialize conversation memory.

        Args:
            max_sessions: Maximum number of sessions to keep in memory
            session_ttl_hours: Time-to-live for sessions in hours
        """
        self.max_sessions = max_sessions
        self.session_ttl_hours = session_ttl_hours
        self.sessions: dict[str, ConversationSession] = {}
        self.access_order: list[str] = []  # LRU tracking

    def create_session(self, session_id: str, metadata: dict[str, Any] | None = None) -> ConversationSession:
        """Create a new conversation session."""
        if session_id in self.sessions:
            raise ValueError(f"Session {session_id} already exists")

        # Clean up old sessions if we're at capacity
        self._cleanup()

        session = ConversationSession(session_id=session_id, metadata=metadata or {})
        self.sessions[session_id] = session
        self.access_order.append(session_id)

        return session

    def get_session(self, session_id: str) -> ConversationSession | None:
        """Get a session by ID, updating access time."""
        session = self.sessions.get(session_id)
        if session:
            # Update LRU order
            if session_id in self.access_order:
                self.access_order.remove(session_id)
            self.access_order.append(session_id)
            session.last_accessed = datetime.now()

        return session

    def add_turn(self, session_id: str, turn: ConversationTurn) -> None:
        """Add a turn to a session."""
        session = self.get_session(session_id)
        if not session:
            session = self.create_session(session_id)

        session.add_turn(turn)

    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            if session_id in self.access_order:
                self.access_order.remove(session_id)
            return True
        return False

    def get_stats(self) -> dict[str, Any]:
        """Get memory statistics."""
        return {
            "total_sessions": len(self.sessions),
            "max_sessions": self.max_sessions,
            "session_ttl_hours": self.session_ttl_hours,
            "access_order_count": len(self.access_order),
            "oldest_session": min(s.created_at for s in self.sessions.values()).isoformat() if self.sessions else None,
            "newest_session": (
                max(s.last_accessed for s in self.sessions.values()).isoformat() if self.sessions else None
            ),
        }

    def _cleanup(self) -> None:
        """Clean up old sessions based on LRU and TTL."""
        now = datetime.now()

        # Remove expired sessions
        expired_sessions = []
        for session_id, session in self.sessions.items():
            age_hours = (now - session.last_accessed).total_seconds() / 3600
            if age_hours > self.session_ttl_hours:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            self.delete_session(session_id)

        # Remove oldest sessions if still over capacity
        while len(self.sessions) > self.max_sessions and self.access_order:
            oldest_id = self.access_order.pop(0)
            if oldest_id in self.sessions:
                del self.sessions[oldest_id]


class MultiHopReasoningEngine:
    """Implements multi-hop reasoning for complex queries."""

    def __init__(self, base_rag_engine, max_depth: int = 2):
        """Initialize multi-hop reasoning engine.

        Args:
            base_rag_engine: The base RAG engine to use for retrieval
            max_depth: Maximum depth for hop traversal
        """
        self.base_rag_engine = base_rag_engine
        self.max_depth = max_depth

    async def chain_retrieve(self, query: str, session_id: str | None = None) -> dict[str, Any]:
        """Perform multi-hop retrieval for complex queries.

        Args:
            query: The user's query
            session_id: Optional session ID for conversation context

        Returns:
            Enhanced query result with multi-hop reasoning
        """
        # Use conversation context if available
        conversation_context = ""
        if session_id and hasattr(self.base_rag_engine, "conversation_memory"):
            session = self.base_rag_engine.conversation_memory.get_session(session_id)
            if session:
                conversation_context = session.get_context_for_query()

        # Step 1: Initial retrieval
        initial_result = await self.base_rag_engine.query(query, conversation_context=conversation_context)

        # Step 2: Analyze retrieved content for follow-up questions
        follow_up_queries = self._generate_follow_up_queries(query, initial_result)

        # Step 3: Execute follow-up queries
        additional_context = []
        for follow_up_query in follow_up_queries[: self.max_depth - 1]:
            follow_up_result = await self.base_rag_engine.query(follow_up_query)
            if follow_up_result["sources"]:
                additional_context.extend(follow_up_result["sources"])

        # Step 4: Synthesize final answer
        if additional_context:
            enhanced_context = self._combine_contexts(initial_result["sources"], additional_context)

            # Re-generate answer with enhanced context
            final_answer = await self._generate_final_answer(query, enhanced_context, conversation_context)

            return {
                "answer": final_answer,
                "sources": enhanced_context,
                "multi_hop": True,
                "hops_performed": len(follow_up_queries[: self.max_depth - 1]) + 1,
                "follow_up_queries": follow_up_queries[: self.max_depth - 1],
            }

        return initial_result

    def _generate_follow_up_queries(self, query: str, result: dict[str, Any]) -> list[str]:
        """Generate follow-up queries based on initial retrieval."""
        # Simple heuristic: extract entities and concepts from retrieved content
        # In production, this could use an LLM to generate sophisticated follow-ups

        " ".join(
            [doc.get("metadata", {}).get("path", "") + ": " + doc.get("text", "") for doc in result.get("sources", [])]
        )

        # Extract potential follow-up topics
        follow_ups = []

        # Example: if query mentions "security", ask about specific security measures
        if "security" in query.lower():
            follow_ups.append("What specific security measures are implemented?")
            follow_ups.append("How are API endpoints secured?")

        # Example: if query mentions "performance", ask about optimization
        if "performance" in query.lower():
            follow_ups.append("What performance optimizations are used?")
            follow_ups.append("How is caching implemented for RAG?")

        return follow_ups

    def _combine_contexts(self, initial_context: list[dict], additional_context: list[dict]) -> list[dict]:
        """Combine contexts from multiple hops."""
        combined = list(initial_context)

        # Add unique additional contexts
        added_paths = {ctx.get("metadata", {}).get("path") for ctx in combined}

        for ctx in additional_context:
            path = ctx.get("metadata", {}).get("path")
            if path not in added_paths:
                combined.append(ctx)
                added_paths.add(path)

        return combined

    async def _generate_final_answer(self, query: str, contexts: list[dict], conversation_context: str) -> str:
        """Generate final answer with enhanced context."""
        # Combine all context sources
        combined_context = "\n".join(
            [f"Source: {ctx.get('metadata', {}).get('path', 'Unknown')}\n{ctx.get('text', '')}" for ctx in contexts]
        )

        prompt = f"""Based on the following comprehensive context, please answer the query.

Conversation History (if any):
{conversation_context}

Retrieved Context:
{combined_context}

Query: {query}

Answer:"""

        # Use the LLM provider to generate answer
        if hasattr(self.base_rag_engine, "llm_provider"):
            answer = await self.base_rag_engine.llm_provider.async_generate(prompt)
            return answer

        return "I've gathered additional information from multiple sources but could not generate a final answer."
