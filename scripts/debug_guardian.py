#!/usr/bin/env python
"""
Debug script for Guardian rule engine. Used by Debug: Safety Guardian launch config.

Usage:
  uv run python scripts/debug_guardian.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure work/GRID/src and workspace root are on path
_root = Path(__file__).resolve().parent.parent
_src = _root / "work" / "GRID" / "src"
for p in (_src, _root):
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))


def main() -> None:
    """Show Guardian stats and verify rules."""
    try:
        from safety.guardian.engine import get_guardian_engine

        engine = get_guardian_engine()
        stats = engine.get_stats() if hasattr(engine, "get_stats") else {}

        print("=== Guardian Rule Engine ===")
        for k, v in stats.items():
            print(f"  {k}: {v}")
    except ImportError as e:
        print(f"Guardian unavailable: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
