# Arena (The Chase) — Diagnostics Checkpoint

**Date**: 2026-01-02
**Status**: ✅ CHECKPOINT

## Why this exists

Arena development surfaced recurring setup/runtime issues (e.g., **path mismatches**, **import errors**, **missing config**). Instead of handling these ad-hoc, we defined them as **system diagnostics** and applied the same pattern language used for gameplay enforcement:

- detect → flag → propose → verify (optionally apply)

This is explicitly **hotfix-ready**: the system can recommend safe, reviewable changes and later support gated auto-apply flows.

## What was added

### 1) Diagnostic engine + solution manufacturing

- **Rule-driven diagnostics**: issues are represented as structured `Diagnostic` objects with category, severity, context, expected vs actual.
- **Solution manufacturing**: each diagnostic can produce ranked `Solution` objects with confidence, steps, and optional auto-apply metadata.

Primary implementation:
- `Arena/the_chase/python/src/the_chase/overwatch/diagnostics.py`

### 2) CLI for diagnostics (human + automation)

A dedicated CLI supports local checks with both **text** and **JSON** output:

- `python -m the_chase.cli.diagnostics_cli check <path>`
- `python -m the_chase.cli.diagnostics_cli import <module>`
- `python -m the_chase.cli.diagnostics_cli config <path>`
- `python -m the_chase.cli.diagnostics_cli run --context '<json>' --output json`

Implementation:
- `Arena/the_chase/python/src/the_chase/cli/diagnostics_cli.py`

### 3) Export surface

Diagnostics were added to the Overwatch package export surface for consistent reuse:
- `Arena/the_chase/python/src/the_chase/overwatch/__init__.py`

## Live hotfix readiness (what it enables)

This checkpoint enables a “guided hotfix” workflow:

- When a CLI/tool fails, run diagnostics with context (path/module/config).
- Collect solutions and pick the highest-confidence candidate(s).
- Apply fixes only behind explicit confirmation (or in CI with a policy gate).
- Record outcomes to improve future confidence ranking.

## Notes

- Output formatting is **Windows-friendly** (ASCII-safe), so diagnostics can be used reliably in PowerShell and CI logs.
- The system remains local-first and does not require any external API calls.
