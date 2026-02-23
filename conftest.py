"""
Root conftest: configure test environment.

Path resolution is handled by pyproject.toml's pythonpath = ["src"] setting.
No sys.path manipulation needed.
"""

import os

# Test environment configuration
os.environ["GRID_ENV"] = "test"
os.environ["SAFETY_BYPASS_REDIS"] = "true"
os.environ["PARASITE_GUARD"] = "0"

# ---------------------------------------------------------------------------
# Collection-time ignore list: prevent stray test files from being collected
# ---------------------------------------------------------------------------
collect_ignore = [
    "scripts/test_drt_functional.py",
    "scripts/test_timeout.py",
    "security/test_security.py",
    "src/test_semantic_chunking.py",
    "Arena",
    "examples",
    "research",
    "frontend",
    "landing",
    "web-client",
]
