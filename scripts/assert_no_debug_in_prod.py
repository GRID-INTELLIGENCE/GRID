#!/usr/bin/env python3
"""
Assert no debug or dev-only flags are set when GRID_ENV=production.

Used by CI (secrets-scan job) and make guard-no-debug to enforce production
guardrails. Exits 0 when safe, 1 with error message when a prohibited
variable is set.

Prohibited in production (from docs/guides/POST_DEBUG_ROUTINE.md):
- DEBUG (truthy: 1, true, yes)
- ENABLE_DEV_TOKEN
- ALLOW_DEV_LOGIN_BYPASS
- GRID_CHROMA_ALLOW_RESET
- ECHOES_API_DEBUG
"""

import os
import sys


def _truthy(val: str) -> bool:
    if not val:
        return False
    return val.strip().lower() in ("1", "true", "yes")


def main() -> int:
    grid_env = (os.environ.get("GRID_ENV") or "").strip().lower()
    if grid_env != "production":
        return 0

    debug_val = (os.environ.get("DEBUG") or "").strip().lower()
    if debug_val in ("1", "true", "yes"):
        print("ERROR: DEBUG must not be set in production", file=sys.stderr)
        return 1

    prohibited = [
        ("ENABLE_DEV_TOKEN", "ENABLE_DEV_TOKEN must not be set in production"),
        ("ALLOW_DEV_LOGIN_BYPASS", "ALLOW_DEV_LOGIN_BYPASS must not be set in production"),
        ("GRID_CHROMA_ALLOW_RESET", "GRID_CHROMA_ALLOW_RESET must not be set in production"),
        ("ECHOES_API_DEBUG", "ECHOES_API_DEBUG must not be set in production"),
    ]
    for var, msg in prohibited:
        if _truthy(os.environ.get(var, "")):
            print(f"ERROR: {msg}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
