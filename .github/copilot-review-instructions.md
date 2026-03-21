# Copilot Code Review Instructions — GRID

## Type Safety

- Type hints required on all function signatures — flag any untyped `def`.
- Block `eval()`, `exec()`, `pickle` — these are never allowed.
- Pydantic v2 only: flag `@validator` (use `model_validator` instead).

## Safety & Security

- Flag any change to `safety/`, `security/`, or `boundaries/` without tests.
- Never weaken validation logic or add bypass paths.
- Check that audit trail integrity is preserved.
- Flag any new network calls or external API usage (local-first principle).

## Architecture

- Enforce layer boundaries: `Application → Service → Database → Core` (one-way).
- Core (`src/grid/`) must not import from upper layers.
- Verify `structlog` usage — no bare `print()` in production code.
- Async-first: I/O operations should use `async def`.

## Code Quality

- 120-character line length maximum.
- Ruff-compatible formatting (no black, isort, pylint).
- `uv run` for all Python commands — never bare `python` or `pip`.
- Conventional commits: `feat(module):`, `fix(security):`, `test(safety):`.

## Shared Rules

- Flag scope expansion beyond PR description.
- Verify rollback plan for schema/migration changes.
- Check dependency justification.
- Flag any secret/credential patterns in code or config.
