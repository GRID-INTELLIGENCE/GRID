"""Tests for GuardrailOrchestrator."""

import pytest

from search.guardrail import GuardrailOrchestrator, GuardrailPolicy, create_default_registry
from search.guardrail.tools.base import GuardrailContext
from search.models import RequestContext


@pytest.fixture
def policy_minimal():
    """Policy with only auth (for focused tests)."""
    return GuardrailPolicy(
        phases={
            "pre_query": ["auth"],
            "post_query": ["audit"],
        }
    )


@pytest.fixture
def policy_no_pre():
    """Policy with no pre_query tools (allows all)."""
    return GuardrailPolicy(phases={"pre_query": [], "post_query": ["audit"]})


class TestGuardrailOrchestrator:
    @pytest.mark.asyncio
    async def test_run_pre_query_allows_when_identity_present(
        self,
        guardrail_context,
        test_config,
    ):
        test_config.guardrail_auth_required = False
        orch = GuardrailOrchestrator(config=test_config, policy=GuardrailPolicy(phases={"pre_query": ["auth"]}))
        result = await orch.run_pre_query(guardrail_context)
        assert not result.blocked

    @pytest.mark.asyncio
    async def test_run_pre_query_blocks_when_auth_fails(
        self,
        guardrail_context_no_identity,
        test_config,
    ):
        test_config.guardrail_auth_required = True
        orch = GuardrailOrchestrator(config=test_config, policy=GuardrailPolicy(phases={"pre_query": ["auth"]}))
        result = await orch.run_pre_query(GuardrailContext(request=guardrail_context_no_identity.request, config=test_config))
        assert result.blocked
        assert "Authentication" in (result.block_reason or "")

    @pytest.mark.asyncio
    async def test_run_pre_query_empty_phase_allows(self, guardrail_context, test_config):
        orch = GuardrailOrchestrator(config=test_config, policy=GuardrailPolicy(phases={"pre_query": []}))
        result = await orch.run_pre_query(guardrail_context)
        assert not result.blocked

    @pytest.mark.asyncio
    async def test_run_post_query_runs_tools(self, guardrail_context, test_config):
        from search.models import Document, SearchHit, SearchResponse

        response = SearchResponse(
            hits=[
                SearchHit(document=Document(id="1", fields={"title": "test"}), score=1.0),
            ],
            total=1,
            page=1,
            size=10,
        )
        orch = GuardrailOrchestrator(config=test_config, policy=GuardrailPolicy(phases={"post_query": ["audit"]}))
        ctx = GuardrailContext(
            request=guardrail_context.request,
            response=response,
            config=test_config,
        )
        result = await orch.run_post_query(ctx, response)
        assert not result.blocked
        assert len(result.tool_results) == 1
