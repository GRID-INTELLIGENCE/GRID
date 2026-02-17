"""
Runtime policy loader: principles and tool/network reach as code context.

Loads config/policy.yaml (derived from docs/PRINCIPLES.md and GLOBAL_CONFIG.md)
and exposes it so runtime behavior—network and external API access, tool allow/block—
is driven by policy, not hardcoded.

Usage:
    from tools.runtime_policy import get_policy, is_tool_allowed, is_network_allowed

    if is_network_allowed():
        ...  # allow outbound calls
    if is_tool_allowed("external_api"):
        ...  # allow external AI provider calls
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

# Cached loaded policy; cleared when reload is needed
_policy_cache: dict[str, Any] | None = None


def _find_repo_root() -> Path:
    """Find repo root by looking for config/policy.yaml or .cursor/devprograms."""
    start = Path(__file__).resolve().parent
    for parent in [start, *start.parents]:
        if (parent / "config" / "policy.yaml").exists():
            return parent
        if (parent / ".cursor" / "devprograms" / "GLOBAL_CONFIG.md").exists():
            return parent
    return start.parent.parent  # fallback: src/tools -> repo root


def _policy_path() -> Path:
    env_path = os.environ.get("GRID_POLICY_PATH", "").strip()
    if env_path:
        p = Path(env_path).resolve()
        if p.is_file():
            return p
        if p.is_dir():
            return p / "config" / "policy.yaml"
    return _find_repo_root() / "config" / "policy.yaml"


def load_policy(reload: bool = False) -> dict[str, Any]:
    """Load policy YAML and return as dict. Cached unless reload=True."""
    global _policy_cache
    if _policy_cache is not None and not reload:
        return _policy_cache
    path = _policy_path()
    if not path.exists():
        _policy_cache = _default_policy()
        return _policy_cache
    if yaml is None:
        _policy_cache = _default_policy()
        return _policy_cache
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    _policy_cache = {**_default_policy(), **data}
    return _policy_cache


def _default_policy() -> dict[str, Any]:
    """Default policy when file missing: access allowed (principles)."""
    return {
        "principles": {
            "transparency": True,
            "openness": True,
            "freedom_to_think": True,
            "access_default": True,
            "network_and_external_api_allowed_by_default": True,
        },
        "network": {"allowed": True},
        "external_api": {"allowed": True},
        "blocked_tools": [],
        "protected_tools": [
            "external_api",
            "network",
            "network_connection",
            "web_search",
            "mcp_web_fetch",
            "fetch",
            "http",
            "requests",
        ],
    }


def get_policy(reload: bool = False) -> dict[str, Any]:
    """Return full policy dict for use as code context."""
    return load_policy(reload=reload)


def is_network_allowed(reload: bool = False) -> bool:
    """True if runtime may perform outbound network calls (policy-driven)."""
    p = load_policy(reload=reload)
    return p.get("network", {}).get("allowed", True)


def is_external_api_allowed(reload: bool = False) -> bool:
    """True if runtime may call external AI providers (OpenAI, Anthropic, etc.)."""
    p = load_policy(reload=reload)
    return p.get("external_api", {}).get("allowed", True)


def is_tool_allowed(tool_name: str, program_id: str | None = None, reload: bool = False) -> bool:
    """
    True if tool is allowed (not in blocked_tools). Protects freedom to think:
    protected_tools must never be in blocked_tools.
    """
    p = load_policy(reload=reload)
    blocked = list(p.get("blocked_tools", []))
    if program_id and p.get("program_overrides") and program_id in p["program_overrides"]:
        blocked = list(p["program_overrides"][program_id])
    return tool_name not in blocked


def get_blocked_tools(program_id: str | None = None, reload: bool = False) -> tuple[str, ...]:
    """Return current list of blocked tool names (runtime context)."""
    p = load_policy(reload=reload)
    blocked = list(p.get("blocked_tools", []))
    if program_id and p.get("program_overrides") and program_id in p["program_overrides"]:
        blocked = list(p["program_overrides"][program_id])
    return tuple(blocked)


def get_protected_tools(reload: bool = False) -> tuple[str, ...]:
    """Return tools protected as core rights (must not be blocked)."""
    p = load_policy(reload=reload)
    return tuple(p.get("protected_tools", []))


def get_principles(reload: bool = False) -> dict[str, bool]:
    """Return principle flags for runtime (e.g. access_default, freedom_to_think)."""
    p = load_policy(reload=reload)
    return dict(p.get("principles", _default_policy()["principles"]))


def clear_cache() -> None:
    """Clear cached policy so next get/load re-reads file."""
    global _policy_cache
    _policy_cache = None
