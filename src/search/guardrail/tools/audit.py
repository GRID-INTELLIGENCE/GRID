"""Audit guardrail tool: logs request/response for compliance."""

from __future__ import annotations

import hashlib
import logging

from .base import GuardrailContext, GuardrailToolResult, ToolResult

logger = logging.getLogger(__name__)


def audit_tool(ctx: GuardrailContext) -> GuardrailToolResult:
    """Log audit trail: identity, index, query hash, outcome."""
    config = ctx.config
    audit_enabled = getattr(config, "guardrail_audit_enabled", True) if config else True
    if not audit_enabled:
        return GuardrailToolResult(
            tool_name="audit",
            result=ToolResult.ALLOW,
        )
    req = ctx.request
    identity = req.identity if req else "anonymous"
    index_name = req.index_name if req else ""
    query_text = req.query_text if req else ""
    query_hash = hashlib.sha256(query_text.encode()).hexdigest()[:16]
    logger.info(
        "search_audit identity=%s index=%s query_hash=%s",
        identity,
        index_name,
        query_hash,
    )
    return GuardrailToolResult(
        tool_name="audit",
        result=ToolResult.ALLOW,
        context={"query_hash": query_hash},
    )
