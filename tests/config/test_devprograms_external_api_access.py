"""
Rigorous verification: dev programs must NOT block external API or network access.

Open-source principles and freedom to think are core rights and values we practice:
access to ideas, AI providers, and the open web is protected. Policy is defined
in .cursor/devprograms/GLOBAL_CONFIG.md; this test asserts the config state
matches those values (no restriction of external_api/network by default).
"""

import re
from pathlib import Path

# Path to the single source of truth (repo root relative to this file).
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GLOBAL_CONFIG_PATH = REPO_ROOT / ".cursor" / "devprograms" / "GLOBAL_CONFIG.md"


def _read_config() -> str:
    path = GLOBAL_CONFIG_PATH
    assert path.exists(), f"Missing {path}"
    return path.read_text(encoding="utf-8")


def _yaml_blocks(content: str) -> list[tuple[int, str]]:
    """Extract (start_line_1based, block_content) for each ```yaml ... ``` block."""
    pattern = re.compile(r"^```yaml\s*\n(.*?)^```", re.MULTILINE | re.DOTALL)
    blocks = []
    for m in pattern.finditer(content):
        start = content[: m.start()].count("\n") + 1
        blocks.append((start, m.group(1)))
    return blocks


def _blocked_tools_in_block(block: str) -> list[str] | None:
    """
    If block has a 'blocked_tools:' key, return the list of items (e.g. ['system_access']).
    Otherwise return None.
    """
    # Find blocked_tools section: "blocked_tools:" then indented list items "- item"
    m = re.search(
        r"blocked_tools:\s*\n((?:\s+-\s+\S+\s*\n?)*)",
        block,
        re.MULTILINE,
    )
    if not m:
        return None
    list_section = m.group(1)
    items = re.findall(r"-\s+(\S+)", list_section)
    return items


def test_global_blocked_tools_do_not_include_external_api_or_network():
    """Global config must allow external API and network (no blocking of AI providers worldwide)."""
    content = _read_config()
    blocks = _yaml_blocks(content)
    assert blocks, "At least one yaml block (global) must exist in GLOBAL_CONFIG.md"
    global_block = blocks[0][1]
    blocked = _blocked_tools_in_block(global_block)
    assert blocked is not None, "Global config must define blocked_tools"
    assert "external_api" not in blocked, (
        "Global blocked_tools must not contain 'external_api'; "
        "external API access is required for AI providers worldwide."
    )
    assert "network" not in blocked, (
        "Global blocked_tools must not contain 'network'; network access is required for AI providers worldwide."
    )


def test_program_blocks_do_not_block_external_api_or_network():
    """Every dev program block must not list external_api or network in blocked_tools."""
    content = _read_config()
    blocks = _yaml_blocks(content)
    # First block is global; rest are program blocks
    program_blocks = blocks[1:] if len(blocks) > 1 else []
    for i, (line_no, block) in enumerate(program_blocks):
        blocked = _blocked_tools_in_block(block)
        if blocked is None:
            continue
        assert "external_api" not in blocked, (
            f"Program block at line ~{line_no} must not block 'external_api'; "
            "access to AI providers worldwide must be maintained."
        )
        assert "network" not in blocked, f"Program block at line ~{line_no} must not block 'network'."
        assert "network_connection" not in blocked, (
            f"Program block at line ~{line_no} must not block 'network_connection'."
        )


def test_global_config_file_exists_and_readable():
    """GLOBAL_CONFIG.md must exist and be the single source of truth."""
    assert GLOBAL_CONFIG_PATH.exists()
    text = _read_config()
    assert "blocked_tools" in text
    assert "allowed_tools" in text


# --- Open-source principles and freedom to think: core rights and values practiced ---

# Only these tool names may appear in global blocked_tools. We practice minimal restriction;
# blocking is the exception, not the rule, in line with open-source and freedom to think.
ALLOWED_GLOBAL_BLOCKED_TOOLS = frozenset({"system_access"})
# Tools that must never be blocked: restricting them would violate freedom to think and
# open-source principles (access to ideas, AI providers, and the open web as core values).
TOOLS_PROTECTED_AS_CORE_RIGHTS = frozenset(
    {
        "external_api",
        "network",
        "network_connection",
        "web_search",
        "mcp_web_fetch",
        "fetch",
        "http",
        "requests",
    }
)


def test_no_bogus_limiters_in_global_blocked_tools():
    """Global blocked_tools may only contain tools from an allowlist (minimal restriction).

    Open-source principles and freedom to think are core rights and values we practice:
    we must not block external_api, network, web_search, mcp_web_fetch, fetch, http,
    or requests. Only explicitly permitted blockers (e.g. system_access) are allowed.
    """
    content = _read_config()
    blocks = _yaml_blocks(content)
    assert blocks
    global_block = blocks[0][1]
    blocked = _blocked_tools_in_block(global_block)
    assert blocked is not None
    blocked_set = set(blocked)
    for name in blocked_set:
        assert name in ALLOWED_GLOBAL_BLOCKED_TOOLS, (
            f"Global blocked_tools contains '{name}'; only {sorted(ALLOWED_GLOBAL_BLOCKED_TOOLS)} are permitted. "
            "We practice open-source principles and minimal restriction as core values."
        )
    for tool in TOOLS_PROTECTED_AS_CORE_RIGHTS:
        assert tool not in blocked_set, (
            f"'{tool}' must not be in global blocked_tools. "
            "Freedom to think and open-source principles require access to ideas, AI providers, and the open web."
        )


def test_principles_doc_exists_and_enshrines_rights():
    """docs/PRINCIPLES.md must exist and document transparency, openness, and access (2026 standards)."""
    principles_path = REPO_ROOT / "docs" / "PRINCIPLES.md"
    assert principles_path.exists(), "docs/PRINCIPLES.md must exist (core values and rights)"
    text = principles_path.read_text(encoding="utf-8")
    assert "transparency" in text.lower(), "PRINCIPLES must mention transparency"
    assert "openness" in text.lower(), "PRINCIPLES must mention openness"
    assert "access" in text.lower() or "AI providers" in text, "PRINCIPLES must affirm access to AI providers / rights"


def test_global_config_code_quality_meets_2026_standards():
    """Global code_quality must use ruff and 120-char line length (project 2026 standards)."""
    content = _read_config()
    blocks = _yaml_blocks(content)
    assert blocks
    global_block = blocks[0][1]
    assert "ruff" in global_block and "formatting" in global_block, (
        "code_quality.formatting must reference ruff (2026 standard)"
    )
    assert "max_line_length: 120" in global_block or "max_line_length:120" in global_block.replace(" ", ""), (
        "code_quality.max_line_length must be 120 (2026 standard)"
    )


def test_global_config_states_core_principles():
    """GLOBAL_CONFIG must state core principles (transparency, openness) in the document."""
    content = _read_config()
    # Intro before first yaml block
    intro = content.split("```yaml")[0]
    assert "transparency" in intro.lower() or "openness" in intro.lower(), (
        "GLOBAL_CONFIG must state core principles (transparency/openness) at top"
    )
