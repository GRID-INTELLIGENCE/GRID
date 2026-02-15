#!/usr/bin/env python
"""
Verify Guardian dynamic rules are loaded. Used by Safety Debug Checklist.

Usage:
  uv run python scripts/debug_guardian_rules.py
"""

from __future__ import annotations

# Delegate to debug_guardian which shows engine stats and verifies rules
import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    script_dir = Path(__file__).resolve().parent
    sys.exit(subprocess.call([sys.executable, str(script_dir / "debug_guardian.py")]))
