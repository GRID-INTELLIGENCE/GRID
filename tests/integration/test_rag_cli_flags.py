"""Integration tests for RAG CLI flags."""

from unittest.mock import MagicMock, patch

import pytest

from tools.rag.cli import index_command, query_command


@pytest.mark.asyncio
async def test_rag_flags_hybrid_rerank():
    """Test that hybrid and rerank flags update the configuration."""
    args = MagicMock()
    args.query = "test query"
    args.top_k = 5
    args.temperature = 0.1
    args.hybrid = True
    args.rerank = True

    with patch("tools.rag.cli.RAGEngine") as MockEngine:
        with patch("tools.rag.cli.RAGConfig.from_env") as MockConfig:
            config_instance = MockConfig.return_value
            # Defaults
            config_instance.use_hybrid = False
            config_instance.use_reranker = False

            # Run command
            await query_command(args)

            # Verify config updates
            assert config_instance.use_hybrid is True
            assert config_instance.use_reranker is True

            # Verify engine init with updated config
            MockEngine.assert_called_with(config=config_instance)

            # Verify query call
            MockEngine.return_value.query.assert_called_with(query_text="test query", top_k=5, temperature=0.1)


@pytest.mark.asyncio
async def test_rag_index_quality_threshold():
    """Test that quality threshold is passed to indexer."""
    args = MagicMock()
    args.path = "."
    args.rebuild = True
    args.update = False
    args.curate = False
    args.manifest = None
    args.quality_threshold = 0.8
    args.skip_preflight = True

    with patch("tools.rag.cli.RAGEngine") as MockEngine:
        with patch("tools.rag.cli.RAGConfig.from_env"):
            # Run command
            await index_command(args)

            # Verify engine.index called with quality_threshold
            MockEngine.return_value.index.assert_called()
            call_kwargs = MockEngine.return_value.index.call_args.kwargs
            assert call_kwargs["quality_threshold"] == 0.8
