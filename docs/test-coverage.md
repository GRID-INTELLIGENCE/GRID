# Backend Coverage Guide (Live)

## Purpose

This document defines the canonical backend coverage commands for `GRID-main` and explains a common measurement trap:

- module tests can exist
- but module coverage can still appear as `0%` in a narrower coverage slice

## Current Source of Truth

- Coverage config lives in [pyproject.toml](/home/caraxes/CascadeProjects/Projects/GRID-main/pyproject.toml) under `[tool.coverage.*]`.
- The configured report threshold is `fail_under = 75`.
- The main CI test job currently runs backend tests but does not explicitly pass `--cov` in the visible test step.

Use this file plus `Makefile` coverage targets as the operational reference.

## Canonical Commands

Run from `Projects/GRID-main`.

```bash
# CI-like backend slice (unit + security + api) and refresh root coverage artifact
make coverage-backend

# Focused module diagnostic (used for resolving module-level coverage disputes)
make coverage-mycelium
```

Equivalent raw commands:

```bash
uv run pytest tests/unit tests/security tests/api \
  --cov=src \
  --cov-report=term-missing \
  --cov-report=json:coverage.json \
  --cov-fail-under=0

uv run pytest tests/mycelium \
  --cov=src/mycelium \
  --cov-report=term-missing \
  --cov-report=json:artifacts/coverage_mycelium.json \
  --cov-fail-under=0
```

`--cov-fail-under=0` is intentional for diagnostics and baseline refreshes.
Use stricter gates only after baseline validity is confirmed.

## Measurement Integrity Notes

The backend forecast artifact can show `src/mycelium` at `0%` when the run only covers `tests/unit + tests/security + tests/api`.

That does not mean mycelium is untested.

Focused coverage run on 2026-04-06:

- `tests/mycelium` passed (`252` tests)
- `src/mycelium` measured at about `90.21%` in `artifacts/coverage_mycelium.json`

Interpretation:

- `0%` in a slice can reflect test-selection scope, not test absence.
- Always validate disputed modules with a focused coverage command before planning large test-count expansions.

## Recommended Workflow

1. Refresh baseline with `make coverage-backend`.
2. If a module looks unexpectedly low/zero, run a focused module coverage command.
3. Only then decide whether the gap is:
   - test selection scope
   - import/measurement drift
   - true missing tests

This keeps coverage planning honest and prevents chasing false negatives.
