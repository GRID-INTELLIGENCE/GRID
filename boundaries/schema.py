"""
Load and validate boundary configuration against the boundary schema.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# When boundaries is at e:\boundaries, parent.parent = e:\ (workspace root)
_WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = _WORKSPACE_ROOT / "config" / "schemas" / "boundary-schema.json"
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "config" / "default_boundary_config.json"


def _find_schema() -> Path:
    candidate = _WORKSPACE_ROOT / "config" / "schemas" / "boundary-schema.json"
    if candidate.exists():
        return candidate
    return SCHEMA_PATH


def load_config(path: Path | str | None = None) -> dict[str, Any]:
    """Load boundary config from JSON. Uses default if path is None."""
    p = Path(path) if path else DEFAULT_CONFIG_PATH
    if not p.exists():
        p = DEFAULT_CONFIG_PATH
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def validate_against_schema(config: dict[str, Any], schema_path: Path | None = None) -> None:
    """Validate config against boundary JSON schema. Raises if invalid."""
    try:
        import jsonschema
    except ImportError:
        return  # no validator
    path = schema_path or _find_schema()
    if not path.exists():
        return
    with open(path, encoding="utf-8") as f:
        schema = json.load(f)
    jsonschema.validate(instance=config, schema=schema)


def load_validated_config(path: Path | str | None = None) -> dict[str, Any]:
    """Load and validate boundary config."""
    config = load_config(path)
    validate_against_schema(config)
    return config
