"""
Runtime policy: config/policy.yaml drives network and external API reach.

Policy and principles are loaded as code context; these tests assert runtime
behavior (network allowed, external API allowed, protected tools not blocked).
"""

# Import after potential path setup; policy loader finds repo root via __file__
from tools.runtime_policy import (
    clear_cache,
    get_blocked_tools,
    get_policy,
    get_principles,
    get_protected_tools,
    is_external_api_allowed,
    is_network_allowed,
    is_tool_allowed,
    load_policy,
)


def test_policy_loads():
    """config/policy.yaml loads and exposes principles and tool policy."""
    clear_cache()
    p = load_policy(reload=True)
    assert "principles" in p
    assert "network" in p
    assert "external_api" in p
    assert "blocked_tools" in p
    assert "protected_tools" in p


def test_network_allowed_by_policy():
    """Runtime may perform outbound network calls (policy-driven)."""
    clear_cache()
    assert is_network_allowed(reload=True) is True


def test_external_api_allowed_by_policy():
    """Runtime may call external AI providers (policy-driven)."""
    clear_cache()
    assert is_external_api_allowed(reload=True) is True


def test_protected_tools_not_blocked():
    """Protected tools (freedom to think) must not be in blocked_tools."""
    clear_cache()
    blocked = set(get_blocked_tools(reload=True))
    protected = set(get_protected_tools(reload=True))
    overlap = blocked & protected
    assert not overlap, (
        f"Protected tools {overlap} must not be blocked; open-source principles and freedom to think require access."
    )


def test_external_api_and_network_tools_allowed():
    """external_api and network tools are allowed (is_tool_allowed)."""
    clear_cache()
    assert is_tool_allowed("external_api", reload=True) is True
    assert is_tool_allowed("network", reload=True) is True


def test_principles_flags_reflect_access_default():
    """Principle flags expose access_default and freedom_to_think."""
    clear_cache()
    principles = get_principles(reload=True)
    assert principles.get("access_default") is True
    assert principles.get("freedom_to_think") is True
    assert principles.get("network_and_external_api_allowed_by_default") is True


def test_get_policy_returns_code_context():
    """get_policy() returns full dict for use as code context."""
    clear_cache()
    ctx = get_policy(reload=True)
    assert ctx.get("network", {}).get("allowed") is True
    assert ctx.get("external_api", {}).get("allowed") is True
    assert "external_api" not in ctx.get("blocked_tools", [])
    assert "network" not in ctx.get("blocked_tools", [])
