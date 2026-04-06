#!/usr/bin/env python3
"""
GRID Enhanced RAG MCP Server

Thin re-export wrapper that runs the unified rag_mcp_server as the
``grid-rag-enhanced`` endpoint.  All RAG functionality (11 tools,
3 resources, 3 prompts) is provided by the canonical server at
``mcp-setup/server/rag_mcp_server.py``; this module simply imports and
re-uses that implementation so both ``grid-rag`` and ``grid-rag-enhanced``
entries can share the same codebase without duplication.

Server name exposed to the client: ``grid-rag-enhanced``

Runnable as:
  python -m grid.mcp.enhanced_rag_server
"""

import sys
from pathlib import Path

# ── Path setup ────────────────────────────────────────────────────────────────
# This file lives at  src/grid/mcp/enhanced_rag_server.py
# grid_root is four levels up from here.
_here = Path(__file__).parent
_grid_root = _here.parent.parent.parent  # src/grid/mcp -> src/grid -> src -> grid_root

try:
    from grid.security.path_manager import SecurePathManager  # noqa: F401  (side-effects: sys.path)

    _path_manager = SecurePathManager(base_dir=_grid_root)
    _path_manager.add_path(_grid_root / "src", validate=True)
except ImportError:
    sys.path.insert(0, str(_grid_root / "src"))

import site  # noqa: E402

site.main()

# ── Delegate to the canonical RAG server ─────────────────────────────────────
# We import everything from the production server so there is a single source
# of truth.  The only thing we change is the MCP server name.

try:
    import mcp  # noqa: F401
except ImportError:
    sys.stderr.write("MCP library not found. Please install: pip install mcp\n")
    sys.exit(1)

# ── Import canonical implementation ──────────────────────────────────────────
# Adjust sys.path so the mcp-setup/server directory is reachable.
_mcp_setup_server_dir = _grid_root / "mcp-setup" / "server"
if str(_mcp_setup_server_dir) not in sys.path:
    sys.path.insert(0, str(_mcp_setup_server_dir))

try:
    import importlib.util as _ilu

    _spec = _ilu.spec_from_file_location(
        "rag_mcp_server",
        str(_mcp_setup_server_dir / "rag_mcp_server.py"),
    )
    _rag_mod = _ilu.module_from_spec(_spec)  # type: ignore[arg-type]
    _spec.loader.exec_module(_rag_mod)  # type: ignore[union-attr]
except Exception as _e:
    sys.stderr.write(f"Failed to load rag_mcp_server: {_e}\n")
    sys.exit(1)

# Re-export the MCP server object and rename it so editors see a distinct name.
server = _rag_mod.server
server.name = "grid-rag-enhanced"  # type: ignore[attr-defined]

# Re-export session and helpers for transparency / introspection.
session = _rag_mod.session
main = _rag_mod.main

# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
