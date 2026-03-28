#!/usr/bin/env python3
"""Inject $schema field into OpenAPI JSON specs after generation.

FastAPI generates valid OpenAPI 3.1.0 specs but omits the $schema key.
This script patches the generated files to include it.

Usage:
    python scripts/inject_openapi_schema.py [--check]

    --check   Dry-run: report files that need patching without modifying them.
              Exits non-zero if any file is missing the $schema field.
"""

import json
import sys
from pathlib import Path

SCHEMA_URL = "https://spec.openapis.org/oas/3.1/schema/2024-11-14"

SPEC_FILES = [
    Path("docs/api/mothership/openapi.json"),
    Path("schemas/resonance_api_openapi.json"),
]


def patch_spec(path: Path, *, check_only: bool = False) -> bool:
    """Return True if file was (or would be) patched."""
    if not path.exists():
        print(f"  SKIP  {path} (not found)")
        return False

    with open(path) as f:
        data = json.load(f)

    if data.get("$schema") == SCHEMA_URL:
        print(f"  OK    {path}")
        return False

    if check_only:
        print(f"  NEEDS {path}")
        return True

    # Insert $schema as the first key
    patched = {"$schema": SCHEMA_URL, **data}
    with open(path, "w") as f:
        json.dump(patched, f, indent=2)
        f.write("\n")

    print(f"  FIXED {path}")
    return True


def main() -> int:
    check_only = "--check" in sys.argv
    mode = "CHECK" if check_only else "PATCH"
    print(f"OpenAPI $schema injection ({mode})")

    needs_fix = 0
    for spec in SPEC_FILES:
        if patch_spec(spec, check_only=check_only):
            needs_fix += 1

    if check_only and needs_fix:
        print(f"\n{needs_fix} file(s) missing $schema — run without --check to fix.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
