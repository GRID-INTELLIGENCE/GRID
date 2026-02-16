"""
Validate the virtual environment health for the GRID project.

Checks:
  - .venv exists and is UV-managed
  - Python version matches .python-version / pyproject.toml requires-python
  - Critical packages are importable
  - No system site-packages contamination

Usage:
  uv run python scripts/validate_venv.py
"""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Windows console encoding fix: ensure emoji / UTF-8 output works on Windows
# even when the console code-page is something other than UTF-8 (e.g. cp1252).
# Setting the env-var propagates to any child processes, and reconfigure()
# fixes the *already-open* stdout/stderr streams in this process.
# ---------------------------------------------------------------------------
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VENV_DIR = PROJECT_ROOT / ".venv"

# Critical packages that must be importable for the project to function
CRITICAL_PACKAGES = [
    "fastapi",
    "pydantic",
    "pydantic_settings",
    "uvicorn",
    "sqlalchemy",
    "httpx",
    "structlog",
    "chromadb",
    "redis",
    "alembic",
]

PASS = "\u2705"
FAIL = "\u274c"
WARN = "\u26a0\ufe0f"


def check_venv_exists() -> bool:
    """Check that .venv directory exists."""
    if not VENV_DIR.is_dir():
        print(f"{FAIL} .venv directory not found at {VENV_DIR}")
        print("   Fix: run 'uv sync --group dev --group test'")
        return False
    print(f"{PASS} .venv directory exists")
    return True


def check_uv_managed() -> bool:
    """Check that .venv was created by UV (has .gitignore with '*')."""
    gitignore = VENV_DIR / ".gitignore"
    if not gitignore.exists():
        print(f"{WARN} .venv/.gitignore not found (may not be UV-managed)")
        return False
    content = gitignore.read_text().strip()
    if content == "*":
        print(f"{PASS} .venv is UV-managed (.gitignore contains '*')")
        return True
    print(f"{WARN} .venv/.gitignore has unexpected content: {content!r}")
    return False


def check_no_system_site_packages() -> bool:
    """Check that include-system-site-packages is false."""
    cfg = VENV_DIR / "pyvenv.cfg"
    if not cfg.exists():
        print(f"{FAIL} pyvenv.cfg not found")
        return False
    text = cfg.read_text()
    for line in text.splitlines():
        if line.strip().startswith("include-system-site-packages"):
            value = line.split("=", 1)[1].strip().lower()
            if value == "false":
                print(f"{PASS} System site-packages excluded (isolated)")
                return True
            print(f"{FAIL} System site-packages included — contamination risk")
            return False
    print(f"{WARN} include-system-site-packages not found in pyvenv.cfg")
    return False


def check_python_version() -> bool:
    """Check that running Python version matches .python-version."""
    ok = True
    # Read .python-version
    pv_file = PROJECT_ROOT / ".python-version"
    if pv_file.exists():
        expected = pv_file.read_text().strip()
        actual = f"{sys.version_info.major}.{sys.version_info.minor}"
        if actual.startswith(expected):
            print(
                f"{PASS} Python version {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} matches .python-version ({expected})"
            )
        else:
            print(f"{FAIL} Python {actual} does not match .python-version ({expected})")
            ok = False
    else:
        print(f"{WARN} .python-version file not found")
        ok = False

    # Check we're running inside the venv
    venv_prefix = os.environ.get("VIRTUAL_ENV", "")
    if venv_prefix:
        print(f"{PASS} Running inside virtual environment: {venv_prefix}")
    else:
        # uv run sets sys.prefix but not always VIRTUAL_ENV
        if hasattr(sys, "real_prefix") or sys.prefix != sys.base_prefix:
            print(f"{PASS} Running inside virtual environment (sys.prefix)")
        else:
            print(f"{WARN} Not running inside a virtual environment — use 'uv run'")
            ok = False

    return ok


def check_critical_packages() -> bool:
    """Check that critical packages are importable."""
    all_ok = True
    for pkg in CRITICAL_PACKAGES:
        try:
            mod = importlib.import_module(pkg)
            version = getattr(mod, "__version__", "?")
            print(f"  {PASS} {pkg} ({version})")
        except ImportError:
            print(f"  {FAIL} {pkg} — NOT INSTALLED")
            all_ok = False
    return all_ok


def main() -> int:
    print("=" * 60)
    print("GRID Virtual Environment Health Check")
    print("=" * 60)
    print()

    results: list[bool] = []

    # 1. venv existence
    if not check_venv_exists():
        print("\nCannot continue — .venv missing.")
        return 1
    results.append(True)

    # 2. UV-managed
    results.append(check_uv_managed())

    # 3. System site-packages
    results.append(check_no_system_site_packages())

    # 4. Python version
    results.append(check_python_version())

    # 5. Critical packages
    print("\nCritical package imports:")
    results.append(check_critical_packages())

    print()
    print("=" * 60)
    failures = sum(1 for r in results if not r)
    if failures == 0:
        print(f"{PASS} All checks passed")
        return 0
    print(f"{FAIL} {failures} check(s) failed")
    print("   Fix: run 'uv sync --group dev --group test'")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
