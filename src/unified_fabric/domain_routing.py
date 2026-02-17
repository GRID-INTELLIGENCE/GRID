"""
Unified Fabric - Domain Routing Helpers
======================================
Utilities for resolving event domains and routing decisions.
"""

from __future__ import annotations

from collections.abc import Iterable

SAFETY_DOMAIN = "safety"
GRID_DOMAIN = "grid"
COINBASE_DOMAIN = "coinbase"
ALL_DOMAIN = "all"

KNOWN_DOMAINS = {SAFETY_DOMAIN, GRID_DOMAIN, COINBASE_DOMAIN}

DOMAIN_PREFIXES = {
    "safety.": SAFETY_DOMAIN,
    "grid.": GRID_DOMAIN,
    "coinbase.": COINBASE_DOMAIN,
}


def infer_domain(event_type: str, default: str = ALL_DOMAIN) -> str:
    """Infer a domain from the event type prefix."""
    for prefix, domain in DOMAIN_PREFIXES.items():
        if event_type.startswith(prefix):
            return domain
    return default


def normalize_domains(domains: Iterable[str] | None) -> list[str]:
    """Normalize target domain list to lowercase strings."""
    if not domains:
        return []
    normalized: list[str] = []
    for domain in domains:
        if not domain:
            continue
        normalized.append(str(domain).lower())
    return normalized


def resolve_target_domains(target_domains: Iterable[str] | None, event_type: str) -> list[str]:
    """Resolve target domains, falling back to inferred domain or ALL."""
    normalized = normalize_domains(target_domains)
    if normalized:
        return normalized

    inferred = infer_domain(event_type, default=ALL_DOMAIN)
    return [inferred]


def expand_domains(target_domains: Iterable[str] | None) -> list[str]:
    """Expand ALL domain into concrete known domains for routing."""
    normalized = normalize_domains(target_domains)
    if ALL_DOMAIN in normalized:
        return sorted(KNOWN_DOMAINS)
    return normalized


__all__ = [
    "SAFETY_DOMAIN",
    "GRID_DOMAIN",
    "COINBASE_DOMAIN",
    "ALL_DOMAIN",
    "KNOWN_DOMAINS",
    "infer_domain",
    "normalize_domains",
    "resolve_target_domains",
    "expand_domains",
]
