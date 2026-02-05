"""
Environment variable management and sanitization.
"""

import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List


def sanitize_path() -> None:
    """
    Sanitize the system PATH environment variable.

    Removes duplicates, non-existent paths, and potentially dangerous paths.
    """
    if "PATH" not in os.environ:
        return

    paths = os.environ["PATH"].split(os.pathsep)
    seen = set()
    clean_paths = []

    for path in paths:
        # Skip empty paths
        if not path.strip():
            continue

        # Normalize path
        try:
            # Handle Windows paths correctly
            norm_path = str(Path(path).expanduser().resolve())
        except (OSError, RuntimeError):
            # Fallback to absolute path if resolve fails (e.g. non-existent drive)
            norm_path = str(Path(path).absolute())

        # Skip duplicates (preserve first occurrence)
        if norm_path.lower() in seen:
            continue

        # Skip potentially dangerous paths
        if any(dangerous in norm_path.lower() for dangerous in ["/tmp", "/var/tmp", ";", "&&", "|"]):
            continue

        clean_paths.append(path)  # Keep original casing if possible
        seen.add(norm_path.lower())

    # Update PATH
    os.environ["PATH"] = os.pathsep.join(clean_paths)


def sanitize_environment() -> Dict[str, List[str]]:
    """
    Sanitize the entire environment.

    Returns:
        Dict containing lists of sanitized variables by category
    """
    changes = defaultdict(list)

    # Sanitize PATH
    old_path = os.environ.get("PATH", "")
    sanitize_path()
    if os.environ.get("PATH") != old_path:
        changes["path"].append("PATH sanitized")

    # Remove sensitive variables that might have leaked
    sensitive_vars = [
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "GITHUB_TOKEN",
        "DATABASE_URL",
        "SECRET_KEY",
        "PASSWORD",
        "API_KEY",
    ]

    for var in sensitive_vars:
        if var in os.environ:
            changes["security"].append(f"Removed sensitive variable: {var}")
            del os.environ[var]

    # Normalize Python-related variables
    python_vars = {
        "PYTHONPATH": os.pathsep.join(
            p for p in os.environ.get("PYTHONPATH", "").split(os.pathsep) if p.strip() and os.path.exists(p)
        )
    }

    for var, value in python_vars.items():
        if os.environ.get(var) != value:
            os.environ[var] = value
            changes["python"].append(f"Normalized {var}")

    return dict(changes)


def get_environment_report() -> Dict[str, Any]:
    """Generate a report of the current environment state."""
    return {
        "python": {
            "executable": sys.executable,
            "version": sys.version,
            "path": sys.path,
            "prefix": sys.prefix,
            "base_prefix": getattr(sys, "base_prefix", sys.prefix),
            "real_prefix": getattr(sys, "real_prefix", None),
        },
        "environment": {
            "path": os.environ.get("PATH", "").split(os.pathsep),
            "pythonpath": os.environ.get("PYTHONPATH", "").split(os.pathsep),
            "virtual_env": os.environ.get("VIRTUAL_ENV"),
        },
    }
