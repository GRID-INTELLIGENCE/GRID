"""Conversational RAG Engine with memory and multi-hop reasoning."""

from typing import Any

from .config import RAGConfig
from .conversation import ConversationMemory, ConversationTurn, MultiHopReasoningEngine
from .rag_engine import RAGEngine


class ConversationalRAGEngine(RAGEngine):
    """Enhanced RAG engine with conversational capabilities.

    Extends the base RAG engine with:
    - Conversation memory and session management
    - Multi-hop reasoning for complex queries
    - Improved citation quality and attribution
    """

    def __init__(self, config: RAGConfig | None = None):
        """Initialize conversational RAG engine.

        Args:
            config: RAG configuration (default: from environment)
        """
        super().__init__(config)

        self.config = config or RAGConfig.from_env()

        # Initialize conversation memory
        self.conversation_memory = ConversationMemory(
            max_sessions=100,
            session_ttl_hours=self.config.conversation_memory_size * 24,  # Convert days to hours
        )

        # Initialize multi-hop reasoning engine
        if self.config.multi_hop_enabled:
            self.multi_hop_engine = MultiHopReasoningEngine(self, max_depth=self.config.multi_hop_max_depth)
        else:
            self.multi_hop_engine = None

        # Add conversational-specific metrics
        self.conversation_metrics = {
            "total_sessions": 0,
            "total_turns": 0,
            "multi_hop_queries": 0,
            "session_average_turns": 0.0,
            "auto_indexing_attempts": 0,
            "auto_indexing_successes": 0,
        }

        # Auto-index essential documentation (commented out for performance)
        # self._auto_index_essential_docs()

    async def _generate_fallback_answer(self, query: str) -> str:
        """Generate a fallback answer when no documents are found.

        Args:
            query: The user's query

        Returns:
            Generated answer based on general knowledge
        """
        # Simple fallback responses for common queries
        query_lower = query.lower()

        # Check for common patterns
        if "what is" in query_lower or "explain" in query_lower:
            if "grid" in query_lower:
                return "GRID is a Geometric Resonance Intelligence Driver that explores complex systems through 9 cognition patterns. It uses local-first RAG with ChromaDB and Ollama for knowledge retrieval."
            elif "rag" in query_lower or "retrieval-augmented" in query_lower:
                return "RAG (Retrieval-Augmented Generation) combines document retrieval with language models to provide contextually relevant answers. GRID's conversational RAG adds session memory and multi-hop reasoning."
            elif "conversation" in query_lower or "memory" in query_lower:
                return "Conversation memory in GRID maintains context across multiple queries within a session, allowing for more coherent and context-aware responses."

        # Default fallback
        prompt = f"Based on general knowledge, answer this question concisely: {query}"
        try:
            return await self.llm_provider.async_generate(prompt, temperature=0.5)
        except Exception:
            return f"I couldn't find specific information about '{query}' in the indexed documents, and I'm unable to generate a general answer at this time."

    async def query(
        self,
        query_text: str,
        top_k: int | None = None,
        temperature: float = 0.7,
        include_sources: bool = True,
        session_id: str | None = None,
        use_conversation: bool = True,
        enable_multi_hop: bool | None = None,
    ) -> dict[str, Any]:
        """Query the conversational RAG system.

        Args:
            query_text: Query text
            top_k: Number of documents to retrieve
            temperature: LLM temperature
            include_sources: Whether to include source documents
            session_id: Optional session ID for conversation continuity
            use_conversation: Whether to use conversation context
            enable_multi_hop: Whether to enable multi-hop reasoning

        Returns:
            Dictionary with enhanced conversational response
        """
        # Determine if multi-hop reasoning should be used
        use_multi_hop = enable_multi_hop if enable_multi_hop is not None else self.config.multi_hop_enabled

        # Get conversation context if enabled
        conversation_context = ""
        if use_conversation and session_id and self.config.conversation_enabled:
            session = self.conversation_memory.get_session(session_id)
            if session and session.turns:
                conversation_context = session.get_context_for_query(self.config.conversation_context_window)

        # Enhance query with conversation context
        enhanced_query = self._enhance_query_with_context(query_text, conversation_context)

        # Choose retrieval method
        safe_session_id = session_id or ""
        if use_multi_hop and self.multi_hop_engine:
            # Use multi-hop reasoning for complex queries
            result = await self.multi_hop_engine.chain_retrieve(enhanced_query, safe_session_id)
            result["multi_hop_used"] = True
            self.conversation_metrics["multi_hop_queries"] += 1
        else:
            # Use standard RAG retrieval
            result = await super().query(enhanced_query, top_k, temperature, include_sources)
            result["multi_hop_used"] = False

        # Implement fallback mechanism when no sources found
        if not result.get("sources") or len(result["sources"]) == 0:
            result["answer"] = await self._generate_fallback_answer(query_text)
            result["sources"] = [
                {"text": "General knowledge fallback", "metadata": {"source": "fallback", "confidence": 0.5}}
            ]
            result["fallback_used"] = True
        else:
            result["fallback_used"] = False

        # Improve citation quality
        result["sources"] = self._improve_citation_quality(result.get("sources", []))

        # Store conversation turn if session exists
        if session_id and use_conversation and self.config.conversation_enabled:
            turn = ConversationTurn(
                user_query=query_text, system_response=result["answer"], retrieved_sources=result.get("sources", [])
            )
            self.conversation_memory.add_turn(session_id, turn)

            # Update metrics
            self.conversation_metrics["total_turns"] += 1
            if session_id not in self.conversation_memory.sessions:
                self.conversation_metrics["total_sessions"] += 1

        # Calculate conversational metrics
        self._update_conversation_metrics()

        # Add conversational information to response
        turn_count = 0
        if session_id:
            session = self.conversation_memory.get_session(session_id)
            turn_count = len(session.turns) if session else 0

        result["conversation_metadata"] = {
            "session_id": session_id,
            "session_active": session_id is not None,
            "context_used": bool(conversation_context),
            "turn_count": turn_count,
        }

        return result

    def create_session(self, session_id: str, metadata: dict[str, Any] | None = None) -> str:
        """Create a new conversation session.

        Args:
            session_id: Unique session identifier
            metadata: Optional session metadata

        Returns:
            Session ID
        """
        self.conversation_memory.create_session(session_id, metadata)
        return session_id

    def get_session_info(self, session_id: str) -> dict[str, Any] | None:
        """Get information about a session.

        Args:
            session_id: Session identifier

        Returns:
            Session information dictionary
        """
        session = self.conversation_memory.get_session(session_id)
        return session.to_dict() if session else None

    def delete_session(self, session_id: str) -> bool:
        """Delete a conversation session.

        Args:
            session_id: Session identifier

        Returns:
            True if session was deleted
        """
        return self.conversation_memory.delete_session(session_id)

    def get_conversation_stats(self) -> dict[str, Any]:
        """Get conversation statistics.

        Returns:
            Conversation metrics and memory statistics
        """
        memory_stats = self.conversation_memory.get_stats()
        return {**self.conversation_metrics, "memory_stats": memory_stats}

    def _enhance_query_with_context(self, query: str, context: str) -> str:
        """Enhance query with conversation context.

        Args:
            query: Original user query
            context: Conversation context

        Returns:
            Enhanced query
        """
        if not context:
            return query

        # Simple enhancement: prepend conversation context
        if self.config.include_conversation_history:
            return f"""Previous conversation:
{context}

Current query: {query}"""

        return query

    def _improve_citation_quality(self, sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Improve citation quality and attribution.

        Args:
            sources: Original sources

        Returns:
            Enhanced sources with better metadata
        """
        enhanced_sources = []

        for source in sources:
            metadata = source.get("metadata", {})

            # Enhance metadata
            enhanced_metadata = {
                **metadata,
                "citation_score": self._calculate_citation_score(source),
                "context_relevance": self._calculate_context_relevance(source),
                "confidence": metadata.get("confidence", 0.5),
            }

            # Add citation formatting
            enhanced_source = {
                **source,
                "metadata": enhanced_metadata,
                "citation": self._format_citation(source),
                "confidence": enhanced_metadata["confidence"],
            }

            enhanced_sources.append(enhanced_source)

        # Sort by confidence/quality
        enhanced_sources.sort(key=lambda x: x["confidence"], reverse=True)

        return enhanced_sources

    def _calculate_citation_score(self, source: dict[str, Any]) -> float:
        """Calculate citation quality score.

        Args:
            source: Source information

        Returns:
            Citation score (0.0-1.0)
        """
        metadata = source.get("metadata", {})
        text = source.get("text", "")

        # Criteria for good citation:
        # 1. Clear source path
        # 2. Good chunk quality
        # 3. Relevant content

        score = 0.5  # Base score

        if metadata.get("path"):
            score += 0.2

        if len(text) > 100:  # Reasonable chunk size
            score += 0.1

        if metadata.get("confidence"):
            score = metadata.get("confidence", score)

        return min(1.0, max(0.0, score))

    def _calculate_context_relevance(self, source: dict[str, Any]) -> float:
        """Calculate context relevance score.

        Args:
            source: Source information

        Returns:
            Relevance score (0.0-1.0)
        """
        # Placeholder for more sophisticated relevance calculation
        # Could use semantic similarity, entity extraction, etc.
        return source.get("metadata", {}).get("relevance", 0.5)

    def _format_citation(self, source: dict[str, Any]) -> str:
        """Format citation for display.

        Args:
            source: Source information

        Returns:
            Formatted citation string
        """
        metadata = source.get("metadata", {})
        path = metadata.get("path", "Unknown")
        chunk_index = metadata.get("chunk_index", "")

        citation = f"Source: {path}"
        if chunk_index:
            citation += f" (Chunk {chunk_index})"

        return citation

    def _update_conversation_metrics(self) -> None:
        """Update conversation metrics.

        Calculates:
        - Average turns per session
        - Active session count
        """
        total_sessions = len(self.conversation_memory.sessions)
        total_turns = self.conversation_metrics["total_turns"]

        if total_sessions > 0:
            self.conversation_metrics["session_average_turns"] = total_turns / total_sessions
        else:
            self.conversation_metrics["session_average_turns"] = 0.0

    def _auto_index_essential_docs(self) -> None:
        """Automatically index essential documentation for better query success."""
        import logging
        import os

        logger = logging.getLogger(__name__)

        # Essential paths to index
        essential_paths = [
            "docs/mcp/",
            "README.md",
            "docs/ARCHITECTURE.md",
            "docs/ARCHITECTURE_STRATEGY.md",
            "docs/CONVERSATIONAL_RAG_SUMMARY.md",
            "docs/mcp/RAG_API_ENHANCEMENT_PLAN.md",
        ]

        for path in essential_paths:
            if os.path.exists(path):
                try:
                    self.conversation_metrics["auto_indexing_attempts"] += 1

                    # Check if path is directory or file
                    if os.path.isdir(path):
                        self.index(path, rebuild=False, quiet=True)
                    else:
                        self.index(os.path.dirname(path), rebuild=False, files=[path], quiet=True)

                    self.conversation_metrics["auto_indexing_successes"] += 1
                    logger.info(f"Successfully indexed: {path}")

                except Exception as e:
                    logger.warning(f"Failed to index {path}: {e}")

        logger.info(
            f"Auto-indexing complete: {self.conversation_metrics['auto_indexing_successes']}/{self.conversation_metrics['auto_indexing_attempts']} successful"
        )


# Factory function for easy instantiation
def create_conversational_rag_engine(config: RAGConfig | None = None) -> ConversationalRAGEngine:
    """Create a new conversational RAG engine.

    Args:
        config: Optional RAG configuration

    Returns:
        ConversationalRAGEngine instance
    """
    return ConversationalRAGEngine(config)
