# Contributing to GRID

Thanks for your interest in contributing to GRID. This guide covers everything you need to get started.

## Prerequisites

- **Python 3.13** (required)
- **uv** — [install guide](https://docs.astral.sh/uv/getting-started/installation/)
- **Git** 2.30+

## Setup

```bash
git clone https://github.com/GRID-INTELLIGENCE/GRID.git
cd GRID
uv sync --group dev --group test
```

## Session Start Protocol

Before writing any new code, verify the wall holds:

```bash
uv run pytest -q --tb=short && uv run ruff check work/ safety/ security/ boundaries/
```

If tests fail, fix them before doing anything else.

## Development Workflow

### Branch Naming

Use prefixes that match conventional commits:

- `feat/` — new features
- `fix/` — bug fixes
- `refactor/` — code restructuring
- `docs/` — documentation
- `test/` — test additions or fixes

### Commit Messages

Use [conventional commits](https://www.conventionalcommits.org/):

```
feat(cognition): add temporal pattern recognition
fix(security): close bypass in boundary engine
refactor(rag): simplify document chunking pipeline
test(safety): add detector coverage for edge cases
docs(adr): log Redis migration decision
```

One commit, one concern. Security fixes separate from features separate from refactoring.

### Running Tests

```bash
# Full suite
uv run pytest -q --tb=short

# Single module (faster during development)
uv run pytest tests/unit -q --tb=short

# With coverage
uv run pytest --cov=src/grid -q --tb=short
```

### Running the Linter

```bash
uv run ruff check work/ safety/ security/ boundaries/

# Auto-fix
uv run ruff check --fix work/ safety/ security/ boundaries/
```

## Pipeline Green Checklist

Before opening a PR, run this checklist end-to-end:

1. Confirm `pyproject.toml` version equals the top version in `CHANGELOG.md`
2. Run local quality gates:
   - `uv run ruff check .`
   - `uv run pytest -q --tb=short`
   - `npm --prefix frontend run lint`
   - `npm --prefix frontend run test`
   - `npm --prefix frontend run build`
3. Verify package build integrity:
   - `uv run python -m build`
   - `uv run twine check dist/*`
4. Ensure generated artifacts are not staged (coverage reports, release scratch logs, temp outputs)
5. Ensure all GitHub workflow runs are green on the PR before merge

See [`docs/release/pipeline-runbook.md`](docs/release/pipeline-runbook.md) for the full execution and post-execution routine.

## Safety-Critical Code

The `safety/`, `security/`, and `boundaries/` directories enforce GRID's security invariants. Extra rules apply:

- **Never** remove or weaken existing validation logic
- **Never** add bypass paths or "dev mode" shortcuts
- **Never** use `eval()`, `exec()`, or `pickle`
- **Always** add tests for any changes
- **Always** preserve audit trail integrity

## Submitting a Pull Request

1. Create a feature branch from `main`
2. Make your changes (one concern per commit)
3. Run tests and linter — both must pass
4. Push and open a PR against `main`
5. Fill in the PR template with a summary and test plan

## Decision Logging

When making architectural decisions (new abstractions, pattern choices, dependency additions), add an entry to `docs/decisions/DECISIONS.md`:

```markdown
## YYYY-MM-DD — [Topic]
**Decision**: [What was decided]
**Why**: [One sentence rationale]
**Alternatives considered**: [What was rejected and why]
```

## Getting Help

- Check [GitHub Issues](https://github.com/GRID-INTELLIGENCE/GRID/issues) for known problems
- Read the [getting-started guide](docs/getting-started.md) for setup details
- Review `.claude/rules/` for detailed coding standards
