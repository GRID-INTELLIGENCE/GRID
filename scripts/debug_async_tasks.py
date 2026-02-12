#!/usr/bin/env python
"""
List all running async tasks and event loops. Used by Debug: Async Task Inventory task.

Usage:
  uv run python scripts/debug_async_tasks.py
  DEBUG_ASYNC=true uv run python scripts/debug_async_tasks.py  # Enable tracking
"""

from __future__ import annotations

import asyncio
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


async def main() -> None:
    """Dump async task inventory."""
    from grid.debug.async_tracker import debug_dump_tasks, enable_async_tracking

    enable_async_tracking()
    data = await debug_dump_tasks()

    print("=== Async Task Inventory ===")
    print(f"Stats: {data['stats']}")
    print("\nActive tasks:")
    for t in data["active_tasks"]:
        print(f"  - {t['name']} ({t['coro']}) age={t['age_seconds']:.2f}s trace={t['trace_id']}")
    if data["stuck_tasks"]:
        print("\nStuck tasks (>30s):")
        for t in data["stuck_tasks"]:
            print(f"  - {t['name']} ({t['coro']}) age={t['age_seconds']:.2f}s")


if __name__ == "__main__":
    asyncio.run(main())
