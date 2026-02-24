from unittest.mock import MagicMock

import pytest

# Try to import legacy module, skip if not available
try:
    from grid.patterns.engine import PatternEngine

    HAS_LEGACY_SRC = True
except (ImportError, ModuleNotFoundError):
    HAS_LEGACY_SRC = False
    pytestmark = pytest.mark.skip(reason="legacy_src module not available")


class TestPatternEngineRAG:
    def test_pattern_engine_with_rag_context(self):
        mock_service = MagicMock()
        mock_service.retrieve_context.return_value = {"context": "data"}

        engine = PatternEngine(retrieval_service=mock_service)
        context = engine.retrieve_rag_context("query")

        assert context == {"context": "data"}
        mock_service.retrieve_context.assert_called_with("query")

    def test_pattern_engine_rag_failure_falls_back(self):
        mock_service = MagicMock()
        mock_service.retrieve_context.side_effect = Exception("RAG Error")

        engine = PatternEngine(retrieval_service=mock_service)
        context = engine.retrieve_rag_context("query")

        assert context == {}
