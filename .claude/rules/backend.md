# Backend Rules (Python)

Applies to: `work/GRID/src/**`, `safety/**`, `security/**`, `boundaries/**`, `scripts/**`

## Standards

- Python 3.13 â€” use modern syntax (match/case, type unions with `|`, etc.)
- Type hints required on all function signatures
- Use `uv run` prefix for all Python CLI commands (never bare `python` or `pip`)
- Pydantic v2 for data models (use `model_validator`, not `@validator`)
- FastAPI with dependency injection (`Depends()`)
- Async-first: prefer `async def` for I/O operations
- Structured logging with `structlog` â€” no bare `print()` in production code
- Line length: 120 characters (ruff configured)

## Testing

- Use pytest markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.safety`
- `asyncio_mode = "auto"` â€” no need for explicit `@pytest.mark.asyncio`
- Run with: `uv run pytest -q --tb=short`

## Safety-Critical Code

- **Never** use `eval()`, `exec()`, or `pickle`
- **Never** bypass authentication checks
- **Never** weaken validation in safety/ or security/ modules
- Use AST-based expression evaluation only (see `arena_integration.py` for reference)
