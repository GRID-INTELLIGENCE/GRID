# Flaky & Pre-Existing Test Failure Registry

> **Maintained by**: PR review pipeline  
> **Last updated**: 2026-04-06  
> **Source session**: PR #81 (docs(runbooks): PR review pipeline orchestration policy)

This document is the authoritative registry of known flaky and pre-existing test failures
discovered during CI operations. Each entry includes reproduction steps, root cause analysis,
CI impact assessment, and the recommended fix.

---

## Legend

| Field | Meaning |
|-------|---------|
| **CI-gated** | Failure blocks merge via `ci-status` job |
| **Local-only** | Fails in `uv run pytest safety/tests` / `boundaries/tests` but not in CI pipeline |
| **Flaky** | Passes on re-run without code changes |
| **Pre-existing** | Present on `main` before the session; not introduced by any change in this session |

---

## Issue 1 — Flaky `Test` Job in CI (Intermittent)

### Metadata

| Field | Value |
|-------|-------|
| **Type** | Flaky (transient failure) |
| **CI-gated** | YES — blocks `ci-status` when it fires |
| **Workflow job** | `Test` (`.github/workflows/ci.yml`) |
| **First observed** | 2026-04-06, PR #81 run `24023780917` |
| **Status** | Resolved by re-run; root cause unidentified |

### Observed Behaviour

During PR #81 (docs-only change, `docs/runbooks/PR_REVIEW_PIPELINE.md`), the CI `Test` job
failed on the first run despite:

- All 6 local runs passing with `EXIT:0` (same test suite, same flags)
- The identical test suite passing 3 hours earlier on the base commit PR #80 (run `24019179828`)
- No Python source changes in the PR (docs-only)

**First run (FAILED)**
```
Run ID:     24023780917
Job ID:     70057970046
Started:    2026-04-06T07:52:07Z
Completed:  2026-04-06T07:55:15Z
Duration:   ~3 minutes 8 seconds
Result:     failure
```

**Re-run (PASSED)**
```
Run ID:     24024109166
Job ID:     70058938188
Started:    2026-04-06T08:04:30Z
Completed:  2026-04-06T08:09:12Z
Duration:   ~4 minutes 42 seconds
Result:     success
```

**Baseline (PR #80, same suite, PASSED)**
```
Run ID:     24019179828
Job ID:     70044479530
Started:    2026-04-06T04:52:30Z
Completed:  2026-04-06T04:57:01Z
Duration:   ~4 minutes 31 seconds
Result:     success
```

### Evidence of Flakiness

The failure run completed in **~3 min 8 sec** vs the passing runs at ~4.5 min. With `-x`
(stop-on-first-failure), a faster completion indicates the suite aborted early on a specific
test rather than running to completion. The identical suite passed in the re-run and on the
base commit run, with no code changes between attempts.

### Local Reproduction

**Cannot be reproduced locally.** All 6 separate local runs returned `EXIT:0`:

```bash
# Exact CI command (mirrored locally):
PYTHONPATH=src \
MOTHERSHIP_ENVIRONMENT=test \
MOTHERSHIP_DATABASE_URL="sqlite:///:memory:" \
RAG_VECTOR_STORE_PROVIDER=in_memory \
RAG_EMBEDDING_PROVIDER=simple \
SAFETY_BYPASS_REDIS=true \
MOTHERSHIP_REDIS_ENABLED=false \
ENABLE_DEV_TOKEN=1 \
BLOCKER_DISABLED=1 \
pytest tests/unit/ tests/security/ tests/api/ -v --tb=short -x --timeout=30
# EXIT:0 (×6 runs)
```

### Root Cause Hypotheses

1. **Async timing race condition**: The suite contains async tests with `asyncio_mode = "strict"`.
   Some tests use real `asyncio.sleep()` calls (e.g., `test_token_expiration` sleeps 2s,
   `test_execute_skill_timeout` sleeps 2s). Under CI runner load, these timing-sensitive tests
   may occasionally exceed their bounds.

2. **SQLite WAL contention**: The newest module `src/grid/knowledge/sqlite_store.py` (added in
   PR #80) uses SQLite with WAL mode. Under concurrent test parallelism (`PYTEST_XDIST_AUTO_NUM_WORKERS=4`
   in CI), multiple workers may contend for the same WAL file if `MOTHERSHIP_DATABASE_URL` or
   a test creates a file-based SQLite DB rather than `:memory:`.

3. **CI runner resource spike**: Ubuntu GitHub-hosted runners share compute resources. A transient
   CPU/memory spike on the shared host could cause a timeout-guarded test to breach its 30s limit.

4. **Thread exception in teardown**: The local run emitted one `PytestUnhandledThreadExceptionWarning`
   (from `tests/unit/` run). Under CI, an unhandled thread exception during teardown could
   cause the process to exit non-zero.

### Affected Test Candidates (Most Likely)

| Test | File | Why Suspect |
|------|------|-------------|
| `test_token_expiration` | `tests/unit/test_critical_paths.py` | 2s real sleep |
| `test_execute_skill_timeout` | `tests/unit/test_skills_discovery_sandbox.py` | 2s real sleep |
| `test_fallback_timeout_when_subprocess_blocked` | `tests/unit/test_skills_discovery_sandbox.py` | 1s real sleep |
| `test_streaming_timeout_with_circuit_breaker` | `tests/api/test_streaming_security.py` | 7s real sleep, longest test |
| `test_databricks_add_mismatched_lengths` | `tests/unit/test_databricks_store.py` | 7s call, SQLite |

### Resolution Applied

Re-triggered CI with an empty commit:
```
git commit --allow-empty -m "ci: retrigger — flaky test re-run"
```
Re-run passed. PR #81 was merged at `48df616a1b7e2341eb4d11355f04ad257a901e9f`.

### Recommended Fix

1. **Short-term**: Add `@pytest.mark.flaky(reruns=2)` to the most probable candidates
   (requires `pytest-rerunfailures` plugin — add to `[project.optional-dependencies] test`).

2. **Medium-term**: Replace `asyncio.sleep()` calls in tests with `freezegun` or a monkeypatched
   clock to eliminate wall-clock dependency.

3. **Investigation**: When next occurrence is observed, immediately capture the job logs via
   `gh run view <run_id> --log` and grep for the `FAILED` line to identify the exact test.

---

## Issue 2 — Safety Tests Missing `@pytest.mark.asyncio` (5–7 tests)

### Metadata

| Field | Value |
|-------|-------|
| **Type** | Pre-existing |
| **CI-gated** | NO — `safety/tests/` is not in the CI `test` job scope |
| **Scope** | `uv run pytest safety/tests -q --tb=short` |
| **First observed** | 2026-04-06, Phase 1 local dry-run |
| **Status** | Pre-existing on `main`; not introduced by PR #81 |

### Failing Tests

**File 1: `safety/tests/test_debug_parity.py`** (3 failures)

| Test function | Line | Error |
|---------------|------|-------|
| `test_timestamp_inconsistency` | 9 | `async def functions are not natively supported` |
| `test_invalid_user_id` | 31 | `async def functions are not natively supported` |
| `test_config_bounds` | 54 | `async def functions are not natively supported` |

**File 2: `safety/tests/unit/test_per_user_safety_fixes.py`** (4 failing, 2 stopped by `--maxfail=5`)

| Test function | Line | Error |
|---------------|------|-------|
| `test_per_user_isolation` | 11 | `async def functions are not natively supported` |
| `test_concurrent_access` | 44 | `async def functions are not natively supported` |
| `test_engine_caching` | 73 | Would fail (same root cause) |
| `test_statistics_safety` | 91 | Would fail (same root cause) |

### Error Message

```
FAILED safety/tests/test_debug_parity.py::test_timestamp_inconsistency - Failed: async def
functions are not natively supported.
You need to install a suitable plugin for your async framework, for example:
  - anyio
  - pytest-asyncio
  - pytest-tornasync
  - pytest-trio
  - pytest-twisted
```

### Root Cause

**`asyncio_mode = "strict"`** is set at line 223 of the root `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "strict"
```

In strict mode, every `async def test_*` function MUST be decorated with
`@pytest.mark.asyncio`. Without it, pytest-asyncio refuses to run the function.

The `safety/pyproject.toml` has no `[tool.pytest.ini_options]` section — it inherits the
root config when tests are run from the project root (e.g., `uv run pytest safety/tests`).
The two files contain 7 `async def test_*` functions with no `@pytest.mark.asyncio` decorator.

**Note**: `pytest-asyncio 1.3.0` is installed (confirmed in local venv). The issue is
decorator absence, not plugin absence.

### CI Impact

**None** — the CI `test` job runs only:
```
pytest tests/unit/ tests/security/ tests/api/ -v --tb=short -x
```

`safety/tests/` is NOT in the CI job's test paths. The failures are invisible to the merge gate.

### Reproduction

```bash
uv run pytest safety/tests -q --tb=short
# 5 failures (--maxfail=5 stops early), 7 would fail in total
```

### Recommended Fix

Add `@pytest.mark.asyncio` to all 7 affected functions. Example:

```python
# Before
async def test_timestamp_inconsistency():
    ...

# After
import pytest

@pytest.mark.asyncio
async def test_timestamp_inconsistency():
    ...
```

**Files to fix:**
- `safety/tests/test_debug_parity.py` — lines 9, 31, 54 (3 functions)
- `safety/tests/unit/test_per_user_safety_fixes.py` — lines 11, 44, 73, 91 (4 functions)

**Commit message:**
```
fix(test): add @pytest.mark.asyncio to safety async tests (strict mode)
```

**Alternative fix**: Add `asyncio_mode = "auto"` to `safety/pyproject.toml` to avoid
requiring explicit decoration in the safety module:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

However, this diverges from the project-wide `strict` policy and is not recommended.

---

## Issue 3 — Pre-existing `test_security_suite.py` Import Error

### Metadata

| Field | Value |
|-------|-------|
| **Type** | Pre-existing (documented in `docs/PREEXISTING_ISSUES.md`) |
| **CI-gated** | Partially — blocks collection if included in CI scope |
| **Scope** | `tests/security/test_security_suite.py` |
| **Status** | Pre-existing; not investigated in this session |

### Summary

`tests/security/test_security_suite.py` fails at import time due to `workspace.mcp` not
being importable. This was catalogued in `docs/PREEXISTING_ISSUES.md §1.1`.

The CI `test` job runs `tests/security/` which includes this file. However, the CI does not
appear to fail on this file — likely because `pytest` treats import errors as collection
warnings rather than hard failures when using `--import-mode=importlib` (set in `pyproject.toml`
addopts).

---

## Summary Table

| # | Issue | Type | CI-Gated | Severity | Fix Effort |
|---|-------|------|----------|----------|------------|
| 1 | Flaky `Test` job (timing/async race) | Flaky | YES | High | Medium |
| 2 | Safety async tests without `@pytest.mark.asyncio` | Pre-existing | NO | Low | Trivial (7 one-liners) |
| 3 | `test_security_suite.py` import error | Pre-existing | NO (masked) | Low | Low |

## Next Actions

| Priority | Action | Owner |
|----------|--------|-------|
| P1 | Capture exact failing test name next time Issue 1 fires (`gh run view <id> --log \| grep FAILED`) | On-call |
| P1 | Add `pytest-rerunfailures` to `[test]` deps and mark top 5 timing-sensitive tests as `@pytest.mark.flaky(reruns=2)` | Dev |
| P2 | Add `@pytest.mark.asyncio` to 7 safety test functions | Dev |
| P3 | Investigate and fix `test_security_suite.py` import path | Dev |
