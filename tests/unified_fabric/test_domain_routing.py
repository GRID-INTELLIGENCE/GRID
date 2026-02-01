"""
Tests for Unified Fabric - Domain Routing
"""

from unified_fabric.domain_routing import (
    ALL_DOMAIN,
    COINBASE_DOMAIN,
    GRID_DOMAIN,
    KNOWN_DOMAINS,
    SAFETY_DOMAIN,
    expand_domains,
    infer_domain,
    normalize_domains,
    resolve_target_domains,
)


def test_infer_domain():
    assert infer_domain("safety.test") == SAFETY_DOMAIN
    assert infer_domain("grid.action") == GRID_DOMAIN
    assert infer_domain("coinbase.trade") == COINBASE_DOMAIN
    assert infer_domain("unknown.type") == ALL_DOMAIN
    assert infer_domain("unknown.type", default=SAFETY_DOMAIN) == SAFETY_DOMAIN


def test_normalize_domains():
    assert normalize_domains(["Safety", "GRID", None, ""]) == ["safety", "grid"]
    assert normalize_domains(None) == []
    assert normalize_domains([]) == []


def test_resolve_target_domains():
    # Explicit targets
    assert resolve_target_domains(["safety"], "any.type") == ["safety"]
    # Inferred targets
    assert resolve_target_domains(None, "safety.check") == ["safety"]
    assert resolve_target_domains([], "grid.task") == ["grid"]
    # Fallback to ALL
    assert resolve_target_domains([], "random.event") == [ALL_DOMAIN]


def test_expand_domains():
    # Concrete domains
    assert expand_domains(["safety"]) == ["safety"]
    # Expansion of ALL
    expanded = expand_domains([ALL_DOMAIN])
    assert set(expanded) == KNOWN_DOMAINS
    assert "safety" in expanded
    assert "grid" in expanded
    assert "coinbase" in expanded
    # Empty
    assert expand_domains([]) == []
