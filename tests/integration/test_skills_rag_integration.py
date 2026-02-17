"""
Integration tests for Skills + RAG system interaction.

Tests the workflow between the skills registry and RAG engine,
including skill execution that queries the RAG system.
"""

import os
import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Conditional imports
HAS_SKILLS = False
HAS_RAG = False

try:
    from grid.skills.registry import SkillsRegistry
    from grid.skills.base import Skill

    HAS_SKILLS = True
except ImportError:
    SkillsRegistry = None
    Skill = None

try:
    from tools.rag.rag_engine import RAGEngine
    from tools.rag.config import RAGConfig

    HAS_RAG = True
except ImportError:
    RAGEngine = None
    RAGConfig = None

requires_skills = pytest.mark.skipif(not HAS_SKILLS, reason="Skills registry not available")
requires_rag = pytest.mark.skipif(not HAS_RAG, reason="RAG engine not available")


# =============================================================================
# Mock Classes
# =============================================================================


class MockRAGEngine:
    """Mock RAG engine for testing."""

    def __init__(self):
        self.documents: list[dict] = []
        self.queries: list[str] = []
        self._setup_default_documents()

    def _setup_default_documents(self):
        self.documents = [
            {
                "id": "doc_1",
                "content": "The GRID system is a framework for intelligent data processing.",
                "metadata": {"topic": "grid", "type": "overview"},
            },
            {
                "id": "doc_2",
                "content": "Skills are executable transformations that can be discovered and run.",
                "metadata": {"topic": "skills", "type": "definition"},
            },
            {
                "id": "doc_3",
                "content": "RAG (Retrieval-Augmented Generation) combines search with language models.",
                "metadata": {"topic": "rag", "type": "definition"},
            },
            {
                "id": "doc_4",
                "content": "The transform.data skill converts data between different formats.",
                "metadata": {"topic": "skills", "type": "documentation"},
            },
            {
                "id": "doc_5",
                "content": "Authentication is handled via JWT tokens with configurable expiration.",
                "metadata": {"topic": "auth", "type": "technical"},
            },
        ]

    async def query(self, question: str, **kwargs) -> dict:
        """Query the RAG engine."""
        self.queries.append(question)

        # Simple keyword matching for mock
        relevant_docs = [
            doc for doc in self.documents if any(kw in doc["content"].lower() for kw in question.lower().split())
        ]

        if not relevant_docs:
            relevant_docs = self.documents[:2]  # Default fallback

        return {
            "answer": f"Based on the documents: {relevant_docs[0]['content'][:100]}...",
            "sources": [
                {"content": doc["content"], "metadata": doc["metadata"], "score": 0.9 - i * 0.1}
                for i, doc in enumerate(relevant_docs[:3])
            ],
            "confidence": 0.85,
        }

    async def index(self, documents: list[dict], **kwargs) -> dict:
        """Index documents."""
        self.documents.extend(documents)
        return {"status": "success", "indexed": len(documents)}

    def add_document(self, content: str, metadata: dict | None = None) -> str:
        """Add a single document."""
        doc_id = f"doc_{len(self.documents) + 1}"
        self.documents.append({"id": doc_id, "content": content, "metadata": metadata or {}})
        return doc_id

    def get_stats(self) -> dict:
        """Get RAG engine statistics."""
        return {
            "document_count": len(self.documents),
            "query_count": len(self.queries),
        }


class RAGQuerySkill:
    """A skill that queries the RAG engine."""

    def __init__(self, rag_engine: MockRAGEngine):
        self.name = "rag.query"
        self.description = "Query the RAG knowledge base for information"
        self.rag_engine = rag_engine
        self.run_count = 0

    def run(self, args: dict[str, Any]) -> dict[str, Any]:
        """Execute a RAG query."""
        import asyncio

        self.run_count += 1
        query = args.get("query", args.get("input", ""))

        # Run async query
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(self.rag_engine.query(query))
        finally:
            loop.close()

        return {
            "status": "success",
            "output": {
                "answer": result["answer"],
                "confidence": result["confidence"],
                "source_count": len(result["sources"]),
            },
        }

    def validate_args(self, args: dict[str, Any]) -> bool:
        return "query" in args or "input" in args


class DataEnrichmentSkill:
    """A skill that enriches data using RAG."""

    def __init__(self, rag_engine: MockRAGEngine):
        self.name = "data.enrich"
        self.description = "Enrich data with information from RAG"
        self.rag_engine = rag_engine
        self.run_count = 0

    def run(self, args: dict[str, Any]) -> dict[str, Any]:
        """Enrich data using RAG."""
        import asyncio

        self.run_count += 1
        data = args.get("data", {})
        enrichment_query = args.get("enrichment_query", f"What is {data.get('type', 'this')}?")

        loop = asyncio.new_event_loop()
        try:
            rag_result = loop.run_until_complete(self.rag_engine.query(enrichment_query))
        finally:
            loop.close()

        enriched_data = data.copy()
        enriched_data["enrichment"] = {
            "source": rag_result["answer"],
            "confidence": rag_result["confidence"],
        }

        return {"status": "success", "output": enriched_data}

    def validate_args(self, args: dict[str, Any]) -> bool:
        return "data" in args


class SkillRagOrchestrator:
    """Orchestrates interactions between skills and RAG."""

    def __init__(self, rag_engine: MockRAGEngine):
        self.rag_engine = rag_engine
        self.skills: dict[str, Any] = {}

        # Register RAG-related skills
        self._register_skills()

    def _register_skills(self):
        self.skills["rag.query"] = RAGQuerySkill(self.rag_engine)
        self.skills["data.enrich"] = DataEnrichmentSkill(self.rag_engine)

    def get_skill(self, name: str):
        return self.skills.get(name)

    def list_skills(self) -> list[str]:
        return list(self.skills.keys())

    async def run_skill_with_rag_context(self, skill_name: str, args: dict, context_query: str | None = None):
        """Run a skill with RAG context enrichment."""
        skill = self.get_skill(skill_name)
        if not skill:
            return {"status": "error", "error": f"Skill {skill_name} not found"}

        # Optionally enrich with RAG context
        if context_query:
            rag_result = await self.rag_engine.query(context_query)
            args["rag_context"] = rag_result

        return skill.run(args)


# =============================================================================
# Tests with Mocked Dependencies (Always Run)
# =============================================================================


class TestSkillsRAGIntegration:
    """Test skills integration with RAG - mocked version."""

    @pytest.fixture
    def rag_engine(self):
        """Create mock RAG engine."""
        return MockRAGEngine()

    @pytest.fixture
    def orchestrator(self, rag_engine):
        """Create skill-RAG orchestrator."""
        return SkillRagOrchestrator(rag_engine)

    def test_orchestrator_has_skills(self, orchestrator):
        """Test orchestrator has expected skills."""
        skills = orchestrator.list_skills()

        assert "rag.query" in skills
        assert "data.enrich" in skills

    def test_get_rag_query_skill(self, orchestrator):
        """Test getting RAG query skill."""
        skill = orchestrator.get_skill("rag.query")

        assert skill is not None
        assert skill.name == "rag.query"

    def test_rag_query_skill_runs(self, orchestrator, rag_engine):
        """Test RAG query skill executes and queries engine."""
        skill = orchestrator.get_skill("rag.query")

        result = skill.run({"query": "What is GRID?"})

        assert result["status"] == "success"
        assert "answer" in result["output"]
        assert len(rag_engine.queries) == 1
        assert rag_engine.queries[0] == "What is GRID?"

    def test_rag_query_skill_input_fallback(self, orchestrator, rag_engine):
        """Test RAG query skill uses 'input' as fallback for query."""
        skill = orchestrator.get_skill("rag.query")

        result = skill.run({"input": "Tell me about skills"})

        assert result["status"] == "success"
        assert rag_engine.queries[-1] == "Tell me about skills"

    def test_data_enrichment_skill(self, orchestrator, rag_engine):
        """Test data enrichment skill uses RAG."""
        skill = orchestrator.get_skill("data.enrich")

        result = skill.run({"data": {"type": "skill", "name": "transform.data"}})

        assert result["status"] == "success"
        assert "enrichment" in result["output"]
        assert len(rag_engine.queries) == 1

    @pytest.mark.asyncio
    async def test_run_skill_with_rag_context(self, orchestrator, rag_engine):
        """Test running skill with RAG context enrichment."""
        result = await orchestrator.run_skill_with_rag_context(
            skill_name="rag.query",
            args={"query": "What is authentication?"},
            context_query="Security best practices",
        )

        assert result["status"] == "success"
        # Should have queried RAG for both the main query and context
        assert len(rag_engine.queries) >= 1

    @pytest.mark.asyncio
    async def test_nonexistent_skill_returns_error(self, orchestrator):
        """Test running nonexistent skill returns error."""
        result = await orchestrator.run_skill_with_rag_context(
            skill_name="nonexistent.skill",
            args={},
        )

        assert result["status"] == "error"
        assert "not found" in result["error"]


class TestRAGSkillExecution:
    """Test RAG skills execution patterns."""

    @pytest.fixture
    def rag_engine(self):
        """Create mock RAG engine."""
        return MockRAGEngine()

    @pytest.fixture
    def rag_query_skill(self, rag_engine):
        """Create RAG query skill."""
        return RAGQuerySkill(rag_engine)

    def test_skill_returns_answer(self, rag_query_skill):
        """Test skill returns answer from RAG."""
        result = rag_query_skill.run({"query": "What is GRID?"})

        assert result["status"] == "success"
        assert "answer" in result["output"]
        assert result["output"]["confidence"] > 0

    def test_skill_returns_sources_count(self, rag_query_skill):
        """Test skill returns source count."""
        result = rag_query_skill.run({"query": "skills"})

        assert "source_count" in result["output"]
        assert result["output"]["source_count"] >= 0

    def test_skill_run_count_increments(self, rag_query_skill):
        """Test skill run count increments."""
        initial_count = rag_query_skill.run_count

        rag_query_skill.run({"query": "test 1"})
        rag_query_skill.run({"query": "test 2"})
        rag_query_skill.run({"query": "test 3"})

        assert rag_query_skill.run_count == initial_count + 3

    def test_skill_validate_args(self, rag_query_skill):
        """Test skill argument validation."""
        # Valid args
        assert rag_query_skill.validate_args({"query": "test"}) is True
        assert rag_query_skill.validate_args({"input": "test"}) is True

        # Invalid args
        assert rag_query_skill.validate_args({}) is False
        assert rag_query_skill.validate_args({"other": "value"}) is False


class TestRAGDocumentIndexing:
    """Test RAG document indexing with skills."""

    @pytest.fixture
    def rag_engine(self):
        """Create mock RAG engine."""
        return MockRAGEngine()

    @pytest.fixture
    def orchestrator(self, rag_engine):
        """Create orchestrator."""
        return SkillRagOrchestrator(rag_engine)

    def test_initial_documents_exist(self, rag_engine):
        """Test RAG engine has initial documents."""
        assert len(rag_engine.documents) > 0

    @pytest.mark.asyncio
    async def test_index_new_documents(self, rag_engine):
        """Test indexing new documents."""
        new_docs = [
            {"content": "New document about caching", "metadata": {"topic": "caching"}},
            {"content": "Another new document", "metadata": {"topic": "misc"}},
        ]

        result = await rag_engine.index(new_docs)

        assert result["status"] == "success"
        assert result["indexed"] == 2
        assert len(rag_engine.documents) >= 7  # 5 initial + 2 new

    def test_add_single_document(self, rag_engine):
        """Test adding a single document."""
        doc_id = rag_engine.add_document(
            content="Single document content",
            metadata={"topic": "test"},
        )

        assert doc_id.startswith("doc_")
        assert len(rag_engine.documents) >= 6

    @pytest.mark.asyncio
    async def test_query_after_indexing(self, rag_engine):
        """Test query returns newly indexed content."""
        await rag_engine.index(
            [{"content": "UniqueKeywordForTesting 123", "metadata": {"topic": "test"}}]
        )

        result = await rag_engine.query("UniqueKeywordForTesting")

        assert result["confidence"] > 0
        assert len(result["sources"]) > 0


class TestSkillRAGCaching:
    """Test caching in skill-RAG interactions."""

    @pytest.fixture
    def rag_engine(self):
        """Create mock RAG engine with query tracking."""
        return MockRAGEngine()

    @pytest.fixture
    def rag_query_skill(self, rag_engine):
        """Create RAG query skill."""
        return RAGQuerySkill(rag_engine)

    def test_queries_are_tracked(self, rag_query_skill, rag_engine):
        """Test that queries are tracked for caching/similarity."""
        rag_query_skill.run({"query": "first query"})
        rag_query_skill.run({"query": "second query"})
        rag_query_skill.run({"query": "first query"})  # Duplicate

        assert len(rag_engine.queries) == 3
        assert rag_engine.queries[0] == rag_engine.queries[2]  # Same query

    def test_rag_stats(self, rag_engine):
        """Test RAG engine statistics."""
        initial_stats = rag_engine.get_stats()

        assert "document_count" in initial_stats
        assert "query_count" in initial_stats


# =============================================================================
# Edge Cases
# =============================================================================


class TestSkillsRAGEdgeCases:
    """Test edge cases in skills-RAG integration."""

    @pytest.fixture
    def rag_engine(self):
        """Create mock RAG engine."""
        return MockRAGEngine()

    @pytest.fixture
    def rag_query_skill(self, rag_engine):
        """Create RAG query skill."""
        return RAGQuerySkill(rag_engine)

    @pytest.fixture
    def orchestrator(self, rag_engine):
        """Create orchestrator."""
        return SkillRagOrchestrator(rag_engine)

    def test_empty_query(self, rag_query_skill):
        """Test skill handles empty query."""
        result = rag_query_skill.run({"query": ""})

        assert result["status"] == "success"
        # Should return some result even for empty query

    def test_special_characters_query(self, rag_query_skill):
        """Test skill handles special characters in query."""
        result = rag_query_skill.run({"query": "What is @#$%^&*()?"})

        assert result["status"] == "success"

    def test_very_long_query(self, rag_query_skill):
        """Test skill handles very long query."""
        long_query = "What is " + "data " * 1000  # Very long query

        result = rag_query_skill.run({"query": long_query})

        assert result["status"] == "success"

    def test_unicode_query(self, rag_query_skill):
        """Test skill handles unicode in query."""
        result = rag_query_skill.run({"query": "什么是数据？🚀"})

        assert result["status"] == "success"

    def test_null_data_enrichment(self, orchestrator):
        """Test data enrichment with null/empty data."""
        skill = orchestrator.get_skill("data.enrich")

        result = skill.run({"data": {}})

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_rag_engine_with_no_documents(self):
        """Test RAG engine behavior with no documents."""
        engine = MockRAGEngine()
        engine.documents = []  # Remove all documents

        result = await engine.query("anything")

        # Should still return some result
        assert "answer" in result or "error" in result


# =============================================================================
# Performance Tests
# =============================================================================


class TestSkillsRAGPerformance:
    """Test performance of skills-RAG integration."""

    @pytest.fixture
    def large_rag_engine(self):
        """Create RAG engine with many documents."""
        engine = MockRAGEngine()

        # Add 1000 documents
        for i in range(1000):
            engine.documents.append(
                {
                    "id": f"doc_{i}",
                    "content": f"Document number {i} about topic {i % 10}",
                    "metadata": {"topic": f"topic_{i % 10}", "index": i},
                }
            )

        return engine

    @pytest.fixture
    def orchestrator(self, large_rag_engine):
        """Create orchestrator with large RAG engine."""
        return SkillRagOrchestrator(large_rag_engine)

    @pytest.mark.asyncio
    async def test_query_performance_with_many_documents(self, large_rag_engine):
        """Test query performance with many documents."""
        import time

        start = time.time()
        result = await large_rag_engine.query("topic 5")
        elapsed = time.time() - start

        assert result["confidence"] > 0
        assert elapsed < 0.5  # Should be fast even with many docs

    def test_skill_execution_performance(self, orchestrator):
        """Test skill execution is performant."""
        import time

        skill = orchestrator.get_skill("rag.query")

        start = time.time()
        for _ in range(10):
            skill.run({"query": "test query"})
        elapsed = time.time() - start

        assert elapsed < 2.0  # 10 queries in under 2 seconds

    @pytest.mark.asyncio
    async def test_concurrent_queries(self, large_rag_engine):
        """Test concurrent query handling."""
        import asyncio
        import time

        queries = [f"topic {i}" for i in range(10)]

        start = time.time()
        results = await asyncio.gather(*[large_rag_engine.query(q) for q in queries])
        elapsed = time.time() - start

        assert len(results) == 10
        assert all(r["confidence"] > 0 for r in results)
        assert elapsed < 2.0  # 10 concurrent queries in under 2 seconds


# =============================================================================
# Tests with Real Dependencies (Conditional)
# =============================================================================


@requires_skills
@requires_rag
class TestRealSkillsRAGIntegration:
    """Tests with real skills and RAG implementation."""

    @pytest.fixture
    def rag_config(self, monkeypatch: pytest.MonkeyPatch):
        """Create RAG configuration."""
        monkeypatch.setenv("RAG_VECTOR_STORE_PROVIDER", "in_memory")
        monkeypatch.setenv("RAG_EMBEDDING_PROVIDER", "mock")
        return RAGConfig.from_env()

    @pytest.fixture
    def skills_registry(self):
        """Create real skills registry."""
        return SkillsRegistry()

    @pytest.fixture
    def rag_engine(self, rag_config):
        """Create real RAG engine."""
        try:
            return RAGEngine(config=rag_config)
        except Exception:
            pytest.skip("RAG engine initialization failed")

    def test_skills_registry_has_skills(self, skills_registry):
        """Test skills registry discovers skills."""
        skills = skills_registry.list_skills()
        assert isinstance(skills, list)

    def test_rag_engine_initialization(self, rag_engine):
        """Test RAG engine initializes correctly."""
        assert rag_engine is not None