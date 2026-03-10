# CI Environment – Import Order & Caching Notes

## Summary

Investigation of CI vs local differences for **import order** and **caching** (so CI and local stay aligned).

## Findings

### 1. Import order (isort / I001)

- **Root** `pyproject.toml` defines `[tool.ruff.lint.isort]` with `known-first-party` for `src/` packages.
- **Nested config:** Ruff uses the **nearest** `pyproject.toml` when checking a file. So:
  - `src/`, `tests/`, `scripts/`, `safety/` → root config (isort known-first-party applied).
  - `boundaries/` → **boundaries/pyproject.toml** (previously had no isort section), so import order could differ there.
- **Fix:** `boundaries/pyproject.toml` now includes the same `[tool.ruff.lint.isort]` and `known-first-party` list (plus `safety`) so boundaries get the same first-party treatment and I001 is consistent in CI and locally.

### 2. Ruff format scope

- **CI** was running `ruff format --check src/ tests/ scripts/` only.
- **Makefile** runs `ruff format .` (whole tree).
- **Fix:** CI now runs `ruff format --check .` so the same paths are format-checked as with `make format`.

### 3. Caching

- **UV:** CI uses `astral-sh/setup-uv` with `enable-cache: true` and `cache-dependency-glob: "uv.lock"`. Same lockfile ⇒ same cache key; no special action needed.
- **Ruff:** No `.ruff_cache` (or equivalent) is cached in CI. Each run is cold; results depend only on config and sources, not a stale cache.
- **Env:** `UV_CACHE_DIR: ".cache/uv"` only sets where uv stores cache in the workspace; the setup-uv action still manages its own cache.

### 4. Lint scope

- **CI and Makefile** both run `ruff check .` (with root and nested configs applied as above). No scope mismatch for lint.

## Commands reference

| Action        | CI (ci.yml)           | Local (Makefile)     |
|--------------|------------------------|----------------------|
| Lint         | `ruff check .`         | `ruff check .`       |
| Format check | `ruff format --check .`| `ruff format .`      |
| Fix          | —                      | `ruff check . --fix` |

## If import order still differs locally vs CI

1. Run from **repo root**: `uv run ruff check .` (so root and nested configs resolve the same as in CI).
2. Ensure **boundaries** uses the updated config: `boundaries/pyproject.toml` includes `[tool.ruff.lint.isort]` and `known-first-party`.
3. Resolve with: `uv run ruff check . --fix` and `uv run ruff format .`, then commit.
