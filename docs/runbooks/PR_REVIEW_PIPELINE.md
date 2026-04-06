# PR Review Pipeline — Orchestrated Execution Policy

> **Scope**: Branch → `main` lifecycle with live CI polling, gate enforcement, and merge orchestration.
> **Last updated**: 2026-04-06

---

## Overview

This runbook defines the **7-phase pipeline execution policy** (Phase 0 through Phase 6) for merging feature branches into `main`. It ensures the CI pipeline stays green, all critical tests pass, and no regressions or merge conflicts are introduced.

```
Phase 0: Pre-Flight          → environment + branch assertion
Phase 1: Local CI Dry-Run   → fail fast before PR creation
Phase 2: PR Synthesis        → create PR via GitHub API
Phase 3: Live CI Polling     → gate on critical job outcomes
Phase 4: Review Gate         → merge eligibility checklist
Phase 5: Merge Orchestration → squash merge + branch cleanup
Phase 6: Post-Merge Verify   → confirm main CI stays green
```

---

## CI Pipeline Architecture

Source: `.github/workflows/ci.yml`

### Job Dependency Graph

```
secrets-scan ──→ lint (non-blocking) ──→ test ────────────→ ci-status
            └──→ smoke-test ──────────→ test ────────────→ ci-status
                          │  └──→ integration (main only)
                          │  └──→ build (main only)
                          └──→ test-mcp-security ──────────→ ci-status
                          └──→ validation (dispatch only)
```

### Job Blocking Policy

| Job | Blocks Merge | Trigger |
|-----|-------------|---------|
| `secrets-scan` | **YES** | Always |
| `smoke-test` | **YES** | Always |
| `test` | **YES** | Always |
| `test-mcp-security` | NO (runs before ci-status, not a gate input) | Always |
| `ci-status` | **YES** (final gate; fails if secrets-scan, smoke-test, or test fail) | Always |
| `lint` | NO (`continue-on-error: true`) | Always |
| `security` | NO (unless critical CVE) | Always |
| `integration` | NO | main push / workflow_dispatch only |
| `build` | NO | main push only |
| `validation` | NO | workflow_dispatch only |

---

## Phase 0 — Environment Assertion

**Entry**: Session start  
**Exit**: Branch verified, tree clean, no remote drift

```bash
# 0.1 Confirm correct branch
git branch --show-current
# Expected: claude/pr-review-pipeline-plan-oCqTH (or feature branch name)

# 0.2 Verify clean working tree
git status
# Expected: nothing to commit, working tree clean

# 0.3 Confirm branch is up to date with main (no unmerged main commits)
git log --oneline -1 HEAD
git log --oneline -1 origin/main
# Expected: HEAD is a descendant of (or equal to) origin/main; no commits in
#           origin/main that are not reachable from HEAD (i.e., branch is current)

# 0.4 Fetch remote
git fetch origin main

# 0.5 Check for drift (should be empty)
git log --oneline main..origin/main
```

**Abort condition**: If `origin/main` is ahead of local `main`, rebase before continuing:
```bash
git rebase origin/main
git push -u origin <branch> --force-with-lease
```

---

## Phase 1 — Local CI Dry-Run

**Entry**: Phase 0 passed  
**Exit**: All CI-gated test suites green locally  
**Purpose**: Fail fast — catch failures before consuming CI runner minutes

```bash
# 1.1 Secrets and debug assertion
GRID_ENV=production uv run python scripts/assert_no_debug_in_prod.py

# 1.2 Lint
uv run ruff check .

# 1.3 CI-gated test suite (mirrors ci.yml `test` job)
# Note: env vars below are set by tests/conftest.py; explicit export here provides
# a clean local baseline matching CI runner state.
PYTHONPATH=src \
MOTHERSHIP_ENVIRONMENT=test \
MOTHERSHIP_DATABASE_URL="sqlite:///:memory:" \
RAG_VECTOR_STORE_PROVIDER=in_memory \
RAG_EMBEDDING_PROVIDER=simple \
SAFETY_BYPASS_REDIS=true \
MOTHERSHIP_REDIS_ENABLED=false \
ENABLE_DEV_TOKEN=1 \
BLOCKER_DISABLED=1 \
uv run pytest tests/unit/ tests/security/ tests/api/ -v --tb=short -x
# CI exact command (no extra env overrides): uv run pytest tests/unit/ tests/security/ tests/api/ -v --tb=short -x

# 1.4 MCP security tests (mirrors ci.yml `test-mcp-security` job)
uv run pytest tests/security/test_mcp_server_security.py -v --tb=short

# 1.5 Smoke imports (mirrors ci.yml `smoke-test` job)
uv run python -c "import pytest, pydantic, fastapi; print('OK')"
```

**Abort condition**: Any failure in steps 1.1, 1.3, 1.4 → fix before Phase 2.  
**Warning**: Lint warnings (step 1.2) are noted but do not block PR creation.

**Not CI-gated** (run locally for hygiene, not required for merge):
```bash
uv run pytest safety/tests -q --tb=short
uv run pytest boundaries/tests -q --tb=short
```

---

## Phase 2 — PR Synthesis

**Entry**: Phase 1 passed  
**Exit**: PR open, CI triggered  
**Tools**: `mcp__github__list_pull_requests`, `mcp__github__create_pull_request`

### Step 2.1 — Check for existing PR

```
mcp__github__list_pull_requests(
  owner="grid-intelligence",
  repo="grid",
  state="open",
  head="grid-intelligence:<branch-name>"
)
```

If PR exists → capture `pr_number`, skip to 2.5.

### Step 2.2 — Ensure branch is pushed

```bash
git push -u origin <branch-name>
```

### Step 2.3 — Create PR

```
mcp__github__create_pull_request(
  owner="grid-intelligence",
  repo="grid",
  title="<conventional-commit-title> (#<issue>)",
  head="<branch-name>",
  base="main",
  body="<see template below>",
  draft=false
)
```

**PR body template**:
```markdown
## Summary
- <1-3 bullet points describing the change>

## Changes
- [ ] <change 1>
- [ ] <change 2>

## Test Plan
- [x] Unit tests: `uv run pytest tests/unit/ -q`
- [x] Security tests: `uv run pytest tests/security/ -q`
- [x] API tests: `uv run pytest tests/api/ -q`

## CI Policy
- Critical (must pass): secrets-scan, smoke-test, test, test-mcp-security
- Non-blocking: lint, integration, security
```

### Step 2.5 — Verify PR targets main

```
mcp__github__pull_request_read(method="get", owner="grid-intelligence", repo="grid", pullNumber=<pr_number>)
```

Confirm: `base.ref == "main"`, `state == "open"`.

---

## Phase 3 — Live CI Polling

**Entry**: PR open, CI running  
**Exit**: All critical jobs terminal (success or failure)  
**Interval**: 30 seconds  **Timeout**: 30 minutes (60 polls)

### Polling Algorithm

```python
# Gate jobs: ci-status fails only when secrets-scan, smoke-test, or test fail.
# test-mcp-security is a ci-status dependency but does NOT cause ci-status to fail.
CRITICAL_JOBS = {"secrets-scan", "smoke-test", "test", "ci-status"}
NON_BLOCKING_JOBS = {"lint", "test-mcp-security", "security", "integration", "build", "validation"}
MAX_POLLS = 60

for poll in range(MAX_POLLS):
    check_runs = mcp__github__pull_request_read(
        method="get_check_runs",
        owner="grid-intelligence",
        repo="grid",
        pullNumber=pr_number
    )

    jobs = classify(check_runs)
    # jobs: {name: status}  status ∈ {queued, in_progress, success, failure, skipped}

    # Guard: if no check runs have appeared yet, CI hasn't started — keep waiting.
    if not jobs:
        sleep(30)
        continue

    present_critical = [j for j in CRITICAL_JOBS if j in jobs]
    # Guard: wait until at least one critical job is visible before evaluating.
    if not present_critical:
        sleep(30)
        continue

    critical_done   = all(jobs[j] in {"success","failure","skipped"} for j in present_critical)
    critical_failed = any(jobs[j] == "failure" for j in present_critical)

    if critical_failed:
        → ABORT: invoke Phase 3B (failure triage)

    if critical_done and not critical_failed:
        → PASS: proceed to Phase 4

    sleep(30)

→ TIMEOUT: manual intervention required
```

### Per-Job Response Matrix

| Job | Status | Action |
|-----|--------|--------|
| `secrets-scan` | failure | Fix: remove secrets, fix version drift, remove debug flags |
| `smoke-test` | failure | Fix: check import paths, dependency conflicts |
| `test` | failure | Fix: run `uv run pytest tests/unit/ -x --tb=long` locally |
| `test-mcp-security` | failure | Fix: check `mcp-setup/server/*.py` for `print()` calls |
| `ci-status` | failure | Investigate gate job — check which critical job failed |
| `lint` | failure | Non-blocking — log warning, continue |
| `security` | failure | Check if pip-audit found CRITICAL/HIGH CVE; escalate if yes |
| `integration` | failure | Non-blocking — log warning, continue |

### Phase 3B — Failure Triage

1. Read failing job logs
2. Apply minimal fix on branch
3. Commit with conventional format: `fix(<scope>): <description>`
4. Push: `git push -u origin <branch>`
5. CI auto-re-triggers → restart poll loop from Phase 3.1

---

## Phase 4 — Review Gate

**Entry**: All critical CI jobs green  
**Exit**: Decision: MERGE or HOLD

### CI Report Template

```
✅ secrets-scan:       PASS
✅ smoke-test:         PASS
✅ test:               PASS (N tests, 0 failures)
✅ test-mcp-security:  PASS
✅ ci-status:          PASS
⚠️  lint:              [warnings / PASS]
⚠️  integration:       [SKIPPED — PR, not main push]
```

### Merge Eligibility Checklist

```
[ ] ci-status job: success
[ ] No new commits on main since PR opened
    → git log HEAD..origin/main  (must be empty)
[ ] PR mergeable_state == "clean"
    → mcp__github__pull_request_read(method="get") → check mergeable_state
[ ] No unresolved blocking review comments
[ ] Branch is up to date with main (no unmerged main commits; rebased if needed)
```

**Abort condition**: `mergeable_state == "dirty"` → rebase and re-push:
```bash
git fetch origin main
git rebase origin/main
git push -u origin <branch> --force-with-lease
```
Then restart Phase 3 poll loop.

---

## Phase 5 — Merge Orchestration

**Entry**: Phase 4 checklist complete  
**Exit**: PR merged, branch deleted  
**Strategy**: Squash merge (linear history, consolidated commit)

### Step 5.1 — Final conflict check

```
mcp__github__pull_request_read(method="get", ...)
```
Confirm: `mergeable == true`, `mergeable_state == "clean"`.

### Step 5.2 — Execute squash merge

```
mcp__github__merge_pull_request(
  owner="grid-intelligence",
  repo="grid",
  pullNumber=<pr_number>,
  merge_method="squash",
  commit_title="<conventional-commit-title> (#<pr_number>)",
  commit_message="<summary of changes>"
)
```

Capture `sha` from response.

### Step 5.3 — Delete feature branch

```bash
git push origin --delete <branch-name>
```

Or via GitHub API if local access unavailable.

**Abort condition**: `mergeable_state != "clean"` at step 5.1 → do NOT proceed; return to Phase 4.

---

## Phase 6 — Post-Merge Verification

**Entry**: Merge SHA captured  
**Exit**: `main` CI confirmed green  
**Interval**: 30 seconds  **Timeout**: 20 minutes

```bash
# 6.1 Verify main HEAD
git fetch origin main
git log --oneline -1 origin/main
# Expected: shows the merge commit SHA
```

```
# 6.2 Find main CI run
mcp__github__list_workflow_runs (ref=main, event=push)
→ capture run_id for the post-merge push

# 6.3 Poll main CI
for poll in range(40):  # 20 minutes
    check_runs = list_check_runs_for_ref(ref="main")
    if ci-status == "success": → DONE ✅
    if ci-status == "failure": → ABORT (regression)
    sleep(30)
```

### Regression Response

If `main` CI fails post-merge:
1. Read failing job logs immediately
2. Create hotfix: `git checkout -b fix/post-merge-regression origin/main`
3. Apply minimal fix
4. Run Phase 1 locally
5. Create emergency PR → re-run this pipeline from Phase 2

---

## Decision Tree

```
Phase 0: Remote drift?       YES → rebase first          NO → continue
Phase 1: Tests red?          YES → fix and rerun          NO → continue
Phase 2: PR exists?          YES → use existing PR        NO → create PR
Phase 3: Critical job fail?  YES → triage + fix + repush  NO → wait / continue
Phase 4: Conflict?           YES → rebase + re-poll       NO → approve merge
Phase 5: Not mergeable?      YES → abort                  NO → squash merge
Phase 6: Main red?           YES → hotfix branch          NO → done ✅
```

---

## Related Files

| File | Purpose |
|------|---------|
| `.github/workflows/ci.yml` | CI pipeline — 10 jobs, critical gate logic |
| `pyproject.toml` | Pytest config, markers, test paths |
| `tests/conftest.py` | Test fixtures, env vars, auto-markers |
| `scripts/assert_no_debug_in_prod.py` | Debug assertion (secrets-scan dependency) |
| `tests/security/test_mcp_server_security.py` | MCP security tests |
| `docs/decisions/DECISIONS.md` | Architectural decision log |
| `docs/CI_CD.md` | CI/CD overview |

---

## Conventional Commit Reference

| Type | Scope examples | When |
|------|---------------|------|
| `feat` | `pipeline`, `knowledge`, `cognition` | New functionality |
| `fix` | `ci`, `security`, `deps` | Bug / regression fix |
| `test` | `safety`, `api`, `unit` | Test additions/fixes |
| `docs` | `runbooks`, `adr`, `api` | Documentation only |
| `refactor` | `rag`, `auth`, `fabric` | Non-functional restructuring |
| `chore` | `gitignore`, `deps` | Maintenance |
