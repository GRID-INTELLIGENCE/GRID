#!/usr/bin/env python
"""
Check PostgreSQL, Redis, Databricks connection pools. Used by Debug: Connection Pool Status task.

Usage:
  uv run python scripts/debug_pools.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# Ensure workspace root first (local safety/), then work/GRID/src (grid)
_root = Path(__file__).resolve().parent.parent
_src = _root / "work" / "GRID" / "src"
for p in (_root, _src):
    if p.exists():
        s = str(p)
        if s in sys.path:
            sys.path.remove(s)
        sys.path.insert(0, s)


def main() -> int:
    """Show connection pool status via debug_cli."""
    script_dir = Path(__file__).resolve().parent
    cli = script_dir / "debug_cli.py"
    return subprocess.call([sys.executable, str(cli), "pools"], cwd=script_dir.parent)


if __name__ == "__main__":
    sys.exit(main())
