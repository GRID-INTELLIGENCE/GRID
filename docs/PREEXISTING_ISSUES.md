# Pre-Existing Issues Document

## Overview

This document catalogs issues discovered during testing that existed **prior to recent changes** and should be addressed in future work.

---

## 1. Test Suite Infrastructure Issues

### 1.1 Test Collection Crashes

| File | Issue | Impact | Status |
|------|-------|--------|--------|
| `tests/providers/test_ollama.py` | Module-level skip on import | Previously `sys.exit(1)`; now uses `pytest.skip(..., allow_module_level=True)` when Ollama unavailable | **Fixed** |
| `tests/security/test_security_suite.py` | Import error on collection | Blocks test discovery | Open |

### 1.2 Missing Module Imports

| File | Missing | Status |
|------|---------|--------|
| `src/application/mothership/middleware/data_corruption.py` | `data_corruption_penalty` (wrong import path) | Fixed during this session |
| `src/application/mothership/routers/safety.py` | Entire module missing | Fixed during this session |

### 1.3 Test Timeout Issues

- **Rate-limit tests**: Actually sleep for rate-limit durations (minutes)
- **API tests**: Timeout in `starlette.testclient` portal calls (pre-existing)

---

## 2. Middleware/Dependency Injection Issues

### 2.1 ParasiteGuardMiddleware Double-Wrap Recursion

**File:** `src/infrastructure/parasite_guard/integration.py:101-105`

**Issue:** The `add_parasite_guard()` function wraps the app twice:
1. Line 101: `middleware = ParasiteGuardMiddleware(app, config)` - wraps app in middleware instance
2. Line 105: `app.add_middleware(lambda app: middleware)` - wraps again via middleware stack

This creates a cycle where `middleware.app` points to the app that contains the middleware, causing infinite recursion on any request.

**Stack trace pattern:**
```
RecursionError: maximum recursion depth exceeded
  File ".../middleware.py", line 89, in dispatch
    response = await self.app(request)
  File ".../middleware.py", line 89, in dispatch
    response = await self.app(request)
    [repeats ~1000 times]
```

**Status:** Fixed during this session by removing the redundant wrapping.

---

### 2.2 ParasiteTracer Dict Slicing Bug

**File:** `src/grid/security/parasite_tracer.py:482`

**Issue:** Code attempts to slice a dictionary:
```python
# Broken
top_spans = {span: traces[span] for span in list(traces.keys())[:10]}
```

**Error:**
```
KeyError: slice(None, 10, None)
```

**Status:** Fixed during this session by converting keys to list before slicing.

---

## 3. Lint Issues (Pre-Existing)

### 3.1 StrEnum Inheritance (UP042)

Many enums inherit from both `str` and `Enum`, causing lint warnings. Should use `StrEnum` (Python 3.11+).

**Status:** `ruff check --select UP042` passes; mothership and core code use `StrEnum` where appropriate. Remaining `Enum` (non-string) usages are intentional.

### 3.2 Async Function Blocking I/O (ASYNC230)

Async functions using blocking `open()` instead of `aiofiles`:

- `src/application/mothership/persistence/drt_storage.py:207,217`
- `src/application/mothership/routers/navigation.py:275`

### 3.3 Async Function Timeout Parameter (ASYNC109)

Async functions with `timeout` parameter instead of `asyncio.timeout`:

- `src/application/mothership/routers/health.py:42,95,129,167`

### 3.4 Import Sorting (I001)

Multiple files have unsorted import blocks in migrations and other modules.

### 3.5 Equality to True (E712)

Multiple repository files use `== True` instead of implicit boolean checks:

- `src/application/mothership/repositories/drt.py:174,184,213,348,370,381,551,601,636`

---

## 4. Runtime Issues

### 4.1 Auth Endpoint Test Failure

**File:** `tests/api/test_auth_jwt.py::TestAuthEndpoints::test_login_success`

**Issue:** Test expects `data["success"] is True` but response returns `False`.

**Root cause:** Unclear - the endpoint returns 200 but response body structure differs from test expectation.

**Status:** Pre-existing, not investigated further.

### 4.2 Deprecated datetime.utcnow()

**File:** `src/grid/resilience/drt_monitor.py:32`

**Warning:**
```
DeprecationWarning: datetime.datetime.utcnow() is deprecated
```

**Status:** Pre-existing, affects telemetry logging.

---

## 5. Missing Functionality

### 5.1 DRT Monitoring Router References Non-Existent Middleware

**File:** `src/application/mothership/routers/drt_monitoring.py`

**Issue:** References `ComprehensiveDRTMiddleware` which doesn't exist. Should use `UnifiedDRTMiddleware` or the new unified architecture.

---

## Summary

| Category | Count | Fixed |
|----------|-------|-------|
| Test collection crashes | 2 | 1 (test_ollama uses pytest.skip) |
| Missing module imports | 2 | 2 |
| Middleware recursion | 1 | 1 |
| Dict slicing bug | 1 | 1 |
| Lint issues (StrEnum, ASYNC, etc.) | ~50+ | UP042 clean |
| Deprecated APIs | 1 | 0 |
| Hardcoded DEBUG / debug prints | — | Fixed in network_interceptor.py, nomic_v2.py |
| CI DEBUG gate | — | Added: `scripts/assert_no_debug_in_prod.py` runs in CI (secrets-scan job). Currently `continue-on-error: true` until `src/tools/rag/rag_engine.py` and `src/tools/rag/indexing/indexer.py` DEBUG prints are removed. |
| Duplicate mypy config | 1 | Consolidated `[[tool.mypy.overrides]]` in pyproject.toml |
| Experimental scripts | — | `scripts/debug_*.py` archived to `archival/experimental_scripts/` |

**Priority fixes for test suite reliability:**
1. ~~Remove or guard `sys.exit(1)` in `test_ollama.py`~~ — **Done** (uses `pytest.skip`).
2. Add proper imports or skip for `test_security_suite.py`
3. Shorten/skip rate-limit tests in CI
4. Fix `drt_monitoring.py` middleware references
