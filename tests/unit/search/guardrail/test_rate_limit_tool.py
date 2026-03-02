"""Tests for rate limit guardrail tool."""

import pytest

from search.config import SearchConfig
from search.guardrail.tools.base import GuardrailContext, ToolResult
from search.guardrail.tools.rate_limit import InMemoryRateLimiter, rate_limit_tool


class TestInMemoryRateLimiter:
    def test_allow_under_limit(self):
        limiter = InMemoryRateLimiter(requests_per_minute=10)
        assert limiter.check("user1") is True
        assert limiter.check("user1") is True

    def test_block_over_limit(self):
        limiter = InMemoryRateLimiter(requests_per_minute=1)
        assert limiter.check("user1") is True
        assert limiter.check("user1") is False


class TestRateLimitTool:
    def test_allow_under_limit(self, guardrail_context):
        result = rate_limit_tool(guardrail_context)
        assert result.result == ToolResult.ALLOW

    def test_block_over_limit(self, guardrail_context):
        cfg = SearchConfig(
            embedding_provider="simple",
            vector_store_backend="in_memory",
            cross_encoder_enabled=False,
            guardrail_rate_limit_per_minute=1,
        )
        ctx = GuardrailContext(request=guardrail_context.request, config=cfg)
        r1 = rate_limit_tool(ctx)
        assert r1.result == ToolResult.ALLOW
        r2 = rate_limit_tool(ctx)
        assert r2.result == ToolResult.BLOCK
