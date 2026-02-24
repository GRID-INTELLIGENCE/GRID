# GitHub Actions CI/CD Workflows

This directory contains automated testing and quality gates for the GRID project.

## Active Workflows

### 1. **ci.yml** — Primary CI Pipeline ("GRID CI")

Consolidated quality checks, security scanning, tests, and build verification.

**Triggers:**
- Push to `main` or `master` (ignores docs/markdown changes)
- Pull requests to `main` or `master`
- Manual workflow dispatch (optional flags: `run_slow_tests`, `run_security_scan`, `run_validation`)

**Jobs (dependency chain):**

| Job | Blocking | Description |
|-----|----------|-------------|
| **secrets-scan** | yes | Heuristic secret detection + version/changelog consistency check |
| **lint** | no | Ruff check/format, mypy (continue-on-error) |
| **security** | no | Bandit + pip-audit (continue-on-error) |
| **smoke-test** | yes | Import checks, Python version assertion, test collection |
| **test** | yes | Unit tests (`-x`), async tests, policy tests |
| **integration** | no | Integration tests (main/master push only) |
| **build** | conditional | Package build + dist verification |
| **validation** | no | Schema/contract validation (manual dispatch only) |
| **ci-status** | gate | Summary — fails if secrets-scan, smoke-test, or test failed |

**Setup:** All Python jobs use `astral-sh/setup-uv@v7.3.0` with `python-version: "3.13"`.

**Duration:** ~2-5 minutes

---

### 2. **frontend.yml** — Frontend CI

**Triggers:** Push/PR to `main` or `develop` affecting `frontend/**`.

**Jobs:** lint-typecheck, test, build (Node 22, `actions/setup-node@v6`)

The lint/typecheck job also enforces that `frontend/coverage/` artifacts are not tracked in git.

**Duration:** ~3-5 minutes

---

### 3. **release.yml** — Release & Publish

**Triggers:** Tags matching `v*.*.*` or `grid-safety-*`, or manual dispatch.

**Jobs:** prepare, test, build, publish-pypi, release, summary

**Setup:** `astral-sh/setup-uv@v7.3.0` with `python-version: "3.13"`.

**Duration:** ~10-15 minutes

---

### 4. **docker-build.yml.disabled** — Docker Build (archived)

Disabled (`.disabled` extension). Builds Docker images + Trivy scan.

---

## Running Workflows

### On push/PR (automatic)

```bash
git push origin main
# ci.yml triggers automatically
```

### Manual (GitHub CLI)

```bash
gh workflow run ci.yml --ref main
gh run list --workflow ci.yml
gh run view <run-id> --log
```

---

## Environment

All workflows enforce:
- **Python 3.13** via `astral-sh/setup-uv@v7.3.0` (no bare `pip` or `python`)
- **uv** for all package management (`uv sync`, `uv run`, `uv pip install`)
- `PYTHONUNBUFFERED=1`, `PYTHONDONTWRITEBYTECODE=1`, `GRID_ENVIRONMENT=testing`
- CPU-only torch (no CUDA downloads in CI)
- In-memory test database and RAG store

## Quick Reference

| Workflow | File | Trigger | Critical |
|----------|------|---------|----------|
| GRID CI | ci.yml | push/PR to main | yes (gate) |
| Frontend CI | frontend.yml | push/PR (frontend/) | yes |
| Release | release.yml | tag/dispatch | publishes |
| Docker | docker-build.yml.disabled | — | archived |
