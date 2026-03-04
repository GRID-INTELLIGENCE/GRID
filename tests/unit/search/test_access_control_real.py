import pytest

from search.guardrail.models import GuardrailProfile
from search.guardrail.tools.access_control import access_control_tool
from search.guardrail.tools.base import GuardrailContext, ToolResult
from search.models import FilterClause, RequestContext


def test_access_control_allowed_indices():
    # Profile with allowed indices
    profile = GuardrailProfile(name="test_profile", allowed_indices=["public"])

    # 1. Allowed index
    ctx = GuardrailContext(request=RequestContext(index_name="public"), profile=profile)
    result = access_control_tool(ctx)
    assert result.result == ToolResult.ALLOW

    # 2. Denied index
    ctx = GuardrailContext(request=RequestContext(index_name="private"), profile=profile)
    result = access_control_tool(ctx)
    assert result.result == ToolResult.BLOCK
    assert "denied" in result.message


def test_access_control_allowed_fields():
    # Profile with allowed fields
    profile = GuardrailProfile(name="test_profile", allowed_fields={"products": ["title", "price"]})

    # 1. Allowed fields
    ctx = GuardrailContext(
        request=RequestContext(
            index_name="products", filters=[FilterClause(field="title", value="test")], facet_fields=["price"]
        ),
        profile=profile,
    )
    result = access_control_tool(ctx)
    assert result.result == ToolResult.ALLOW

    # 2. Denied filter field
    ctx = GuardrailContext(
        request=RequestContext(index_name="products", filters=[FilterClause(field="secret_field", value="test")]),
        profile=profile,
    )
    result = access_control_tool(ctx)
    assert result.result == ToolResult.BLOCK
    assert "Filter field 'secret_field' not allowed" in result.message

    # 3. Denied facet field
    ctx = GuardrailContext(request=RequestContext(index_name="products", facet_fields=["margin"]), profile=profile)
    result = access_control_tool(ctx)
    assert result.result == ToolResult.BLOCK
    assert "Facet field 'margin' not allowed" in result.message


def test_access_control_no_restrictions():
    # Profile with no restrictions
    profile = GuardrailProfile(name="basic")

    ctx = GuardrailContext(request=RequestContext(index_name="anything"), profile=profile)
    result = access_control_tool(ctx)
    assert result.result == ToolResult.ALLOW
