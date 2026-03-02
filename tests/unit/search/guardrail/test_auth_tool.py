"""Tests for auth guardrail tool."""

import pytest

from search.guardrail.tools.auth import auth_tool
from search.guardrail.tools.base import GuardrailContext, ToolResult


class TestAuthTool:
    def test_allow_when_identity_present(self, guardrail_context):
        result = auth_tool(guardrail_context)
        assert result.tool_name == "auth"
        assert result.result == ToolResult.ALLOW
        assert result.context.get("identity") == "user-123"

    def test_block_when_identity_missing_and_required(self, guardrail_context_no_identity):
        result = auth_tool(guardrail_context_no_identity)
        assert result.result == ToolResult.BLOCK
        assert "Authentication" in (result.message or "")

    def test_allow_when_auth_not_required(self, guardrail_context_no_identity, guardrail_config_auth_optional):
        ctx = GuardrailContext(
            request=guardrail_context_no_identity.request,
            config=guardrail_config_auth_optional,
        )
        result = auth_tool(ctx)
        assert result.result == ToolResult.ALLOW
