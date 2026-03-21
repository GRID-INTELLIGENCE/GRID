#!/usr/bin/env bash
set -euo pipefail

if ! command -v uv >/dev/null 2>&1; then
  python3 -m pip install uv
fi

export PYTHONPATH=src
export MOTHERSHIP_ENVIRONMENT=test
export MOTHERSHIP_DATABASE_URL="sqlite:///:memory:"
export MOTHERSHIP_USE_DATABRICKS="false"

uv sync --frozen --group dev --group test
uv run pytest tests/unit/ -q --tb=short
uv run pytest safety/tests/ boundaries/ -q --tb=short
uv run ruff check . --output-format=github
