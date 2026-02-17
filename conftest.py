"""
Root conftest: ensure src is first on sys.path before any test or app code is imported.

This fixes ModuleNotFoundError for 'grid.resilience' when a top-level grid/ (e.g. at
repo root) would otherwise shadow src/grid. Must run at import time so path is correct
before tests/unified_drt_accountability_test.py (or any module importing grid.*) loads.
"""

import os
import sys

_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
_src = os.path.join(_root, "src")

# Remove root and src so we can reinsert in the right order
for _p in (_src, _root):
    while _p in sys.path:
        sys.path.remove(_p)

# Ensure src is first so grid.* resolves to src/grid
sys.path.insert(0, _src)
if _root not in sys.path:
    sys.path.append(_root)

# Test environment configuration
os.environ["GRID_ENV"] = "test"
os.environ["SAFETY_BYPASS_REDIS"] = "true"
os.environ["PARASITE_GUARD"] = "0"
os.environ["PYTHONPATH"] = _src
