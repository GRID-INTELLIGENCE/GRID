#!/usr/bin/env python
"""
Run integration health checks. Used by Debug: Verify Wall + Health Checks task.

Usage:
  uv run python scripts/debug_health_check.py
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


async def main() -> int:
    """Run health checks and exit with 0 if all healthy, 1 otherwise."""
    from grid.debug.integration_health import health_checker

    results = await health_checker.check_all()
    unhealthy = [r for r in results if not r.healthy]
    for r in results:
        status = "OK" if r.healthy else "FAIL"
        err = f" ({r.error})" if r.error else ""
        print(f"  {status} {r.service}: {r.latency_ms:.2f}ms{err}")
    if unhealthy:
        print(f"\n{len(unhealthy)} service(s) unhealthy")
        return 1
    print("\nAll services healthy")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
