"""Tests for sanitize guardrail tool."""

import pytest

from search.guardrail.tools.base import GuardrailContext, ToolResult
from search.guardrail.tools.sanitize import sanitize_tool


class TestSanitizeTool:
    def test_allow_normal_query(self, guardrail_context):
        result = sanitize_tool(guardrail_context)
        assert result.result == ToolResult.ALLOW

    def test_block_oversized_query(self, guardrail_context):
        guardrail_context.request.query_text = "x" * 15_000
        result = sanitize_tool(guardrail_context)
        assert result.result == ToolResult.BLOCK
        assert "max length" in (result.message or "")

    def test_block_dangerous_pattern_semicolon(self, guardrail_context):
        guardrail_context.request.query_text = "test; drop table"
        result = sanitize_tool(guardrail_context)
        assert result.result == ToolResult.BLOCK

    def test_block_script_tag(self, guardrail_context):
        guardrail_context.request.query_text = "hello <script>alert(1)</script>"
        result = sanitize_tool(guardrail_context)
        assert result.result == ToolResult.BLOCK
