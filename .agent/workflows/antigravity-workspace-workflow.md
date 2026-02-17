---
description: GRID workspace workflow — The Wall verification, safety review, security audit, and module testing
---

# GRID Workspace Workflows

Workspace-specific workflows for the GRID project.

// turbo-all

## /verify-wall — Daily Verification ("The Wall")
Run before starting any new work. Tests + lint must pass.

```powershell
uv run pytest -q --tb=short
```

```powershell
uv run ruff check src/ safety/ security/ boundaries/
```

If anything fails, fix it before doing anything else. The wall must hold.

---

## /safety-review — Safety Module Review
Review safety-critical code for violations.

1. Scan for `eval()`, `exec()`, `pickle` in production code:
```powershell
rg -n "eval\(|exec\(|pickle\." src/ safety/ security/ boundaries/ --glob "*.py" --glob "!*test*" --glob "!*archive*"
```

2. Run safety-specific tests:
```powershell
uv run pytest safety/tests boundaries/tests -q --tb=short
```

3. Check for shared mutable global state in safety engines — each user must have isolated instances.

4. Verify audit trail integrity — log formats must not be modified without review.

---

## /format-lint — Format & Lint
Auto-format and lint Python source directories.

```powershell
uv run ruff format src/ safety/ security/ boundaries/ scripts/
```

```powershell
uv run ruff check --fix src/ safety/ security/ boundaries/
```

---

## /test-module — Test a Specific Module
Run tests for a specific module. Replace `<path>` with the target.

```powershell
uv run pytest <path> -q --tb=short -v
```

Common module test paths:
- Safety: `safety/tests/`
- Boundaries: `boundaries/tests/`
- Core: `tests/`
- RAG: `tests/test_rag*.py`
- Auth: `tests/integration/test_auth*.py`

---

## /security-audit — Weekly Security Audit
Full security audit: dependency check, bandit scan, invariant grep, performance.

1. Dependency audit:
```powershell
uv run pip-audit --progress-spinner off
```

2. Bandit scan on safety-critical modules:
```powershell
uv run bandit -r safety/ security/ boundaries/ -q
```

3. Security invariant scan (eval/exec/pickle):
```powershell
rg -n "eval\(|exec\(|pickle\." src/ safety/ security/ boundaries/ --glob "*.py" --glob "!*test*" --glob "!*archive*"
```

4. Performance budget — slowest 10 tests:
```powershell
uv run pytest -q --tb=short --durations=10
```

---

## /git-check — Git Status & Diff
Quick overview of working tree state.

```powershell
git status --short
```

```powershell
git diff --stat
```

---

## /frontend-dev — Frontend Development
Start frontend dev server and tooling.

Dev server:
```powershell
Set-Location frontend; npm run dev
```

Lint + typecheck:
```powershell
Set-Location frontend; npm run lint
```

Test:
```powershell
Set-Location frontend; npm test
```

---

## /typecheck — Python Type Checking
Run mypy strict type checking on core modules.

```powershell
uv run mypy src/grid --no-error-summary
```
