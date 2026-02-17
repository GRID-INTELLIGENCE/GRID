# Project Issue & Bug Pattern Metadata

**Version:** 2.4.0  
**Last Updated:** 2025-02-17

## Issue Categories

| Category | Severity | Count | Status |
|----------|----------|-------|--------|
| Test Infrastructure | Critical | 3 | Known |
| Middleware/DI | Critical | 2 | Fixed |
| Security | High | 2 | Fixed |
| Performance | Medium | 2 | Fixed |
| Lint/Code Style | Low | 664→0 | **Resolved** |
| Deprecated API | Low | 1 | Fixed |

---

## Bug Patterns

### Pattern 1: Double-Wrap Recursion

**ID:** BP-001  
**Severity:** Critical  
**Location:** `src/infrastructure/parasite_guard/integration.py:101-105`  
**Type:** Infinite Recursion

**Description:** Middleware wrapped twice, creating circular reference.

**Code:**
```python
# Line 101: First wrap
middleware = ParasiteGuardMiddleware(app, config)
# Line 105: Second wrap (redundant)
app.add_middleware(lambda app: middleware)
```

**Trigger:** Any HTTP request through the middleware stack.  
**Symptom:** `RecursionError: maximum recursion depth exceeded`  
**Fix:** Remove the `add_middleware` call, keep only direct instantiation.

---

### Pattern 2: Dict Key Slicing

**ID:** BP-002  
**Severity:** Critical  
**Location:** `src/grid/security/parasite_tracer.py:482`  
**Type:** TypeError

**Description:** Dictionary keys sliced without converting to list.

**Code:**
```python
# Broken
top_spans = {span: traces[span] for span in traces.keys()[:10]}
```

**Trigger:** Called in background task after login.  
**Symptom:** `KeyError: slice(None, 10, None)`  
**Fix:** `list(traces.keys())[:10]`

---

### Pattern 3: Missing Import Path

**ID:** BP-003  
**Severity:** High  
**Location:** `src/application/mothership/middleware/data_corruption.py:6`  
**Type:** ModuleNotFoundError

**Description:** Relative import points to non-existent module.

**Code:**
```python
from .data_corruption_penalty import DataCorruptionEvent  # Wrong
# Should be:
from grid.resilience.data_corruption_penalty import DataCorruptionEvent
```

**Trigger:** Import of middleware module.  
**Symptom:** `ModuleNotFoundError: No module named 'application.mothership.middleware.data_corruption_penalty'`  
**Fix:** Use absolute import from `grid.resilience`.

---

### Pattern 4: Missing Router Module

**ID:** BP-004  
**Severity:** High  
**Location:** `src/application/mothership/main.py:788`  
**Type:** ModuleNotFoundError

**Description:** Router imported but file never created.

**Code:**
```python
from .routers import safety  # File doesn't exist
```

**Trigger:** Application startup.  
**Symptom:** `ModuleNotFoundError: No module named 'application.mothership.routers.safety'`  
**Fix:** Create `src/application/mothership/routers/safety.py` as thin proxy.

---

### Pattern 5: Auth Bypass Returns None

**ID:** BP-005  
**Severity:** High  
**Location:** `src/application/mothership/security/auth.py:321-325`  
**Type:** Contract Violation

**Description:** Function returns `None` when callers expect `dict`.

**Code:**
```python
# Returns None if bypass_result is None
if bypass_result is not None:
    return bypass_result
# Caller expects dict, gets None -> AttributeError
```

**Trigger:** Dev bypass enabled but env vars missing.  
**Symptom:** `AttributeError: 'NoneType' object has no attribute 'get'`  
**Fix:** Add deny-by-default `raise AuthenticationError`.

---

### Pattern 6: Double Ollama Listing

**ID:** BP-006  
**Severity:** Medium  
**Location:** `src/tools/rag/model_router.py:58,81`  
**Type:** Redundant Computation

**Description:** `list_ollama_models()` called twice per query.

**Code:**
```python
# First call at line 59
ollama_models = list_ollama_models(config.ollama_base_url)
# ...
# Second call implicitly (same function called again at line 81)
if prefer_ollama and ollama_models:  # Relies on cached value
```

**Trigger:** Every RAG query with `prefer_ollama=True`.  
**Symptom:** 2x HTTP round-trip latency to Ollama API.  
**Fix:** Cache result in variable and reuse.

---

### Pattern 7: Directory Exclusion Ineffective

**ID:** BP-007  
**Severity:** Medium  
**Location:** `src/tools/rag/on_demand_engine.py:292-299`  
**Type:** Logic Error

**Description:** `rglob("*")` traverses excluded dirs despite check.

**Code:**
```python
# Broken: rglob still yields children of excluded dirs
for p in root.rglob("*"):
    if p.is_dir() and p.name in exclude_dirs:
        continue  # Only skips the dir itself, not its children
```

**Trigger:** Large repositories with `.git`, `node_modules`.  
**Symptom:** Slow file collection, files from excluded dirs included.  
**Fix:** Use `os.walk` with `dirnames[:]` pruning.

---

### Pattern 8: Redundant Config Parsing

**ID:** BP-008  
**Severity:** Medium  
**Location:** `src/tools/rag/on_demand_engine.py:79,89`  
**Type:** Redundant Computation

**Description:** `RAGConfig.from_env()` called 3x per query.

**Code:**
```python
# Line 74: Initial route
routing = route_models(query_text, base_config=self.config, prefer_ollama=True)
# Line 80: Re-parse env (could use self.config.copy())
routed_config = self.config.copy() if hasattr(self.config, "copy") else RAGConfig.from_env()
# Line 90: Third parse
fallback_cfg = self.config.copy() if hasattr(self.config, "copy") else RAGConfig.from_env()
```

**Trigger:** Every RAG query.  
**Symptom:** Repeated environment variable parsing overhead.  
**Fix:** Use `self.config.copy()` consistently.

---

### Pattern 9: Middleware Double Instantiation

**ID:** BP-009  
**Severity:** Medium  
**Location:** `src/application/mothership/main.py:747-769`  
**Type:** Resource Waste

**Description:** DRT middleware created twice with same parameters.

**Code:**
```python
# Line 747: First instance (stored but not used)
drt_middleware = UnifiedDRTMiddleware(...)
# Line 748: Second instance via add_middleware (actual registration)
app.add_middleware(UnifiedDRTMiddleware, ...)
```

**Trigger:** Application startup.  
**Symptom:** Two middleware instances with divergent state.  
**Fix:** Remove manual instantiation, use only `add_middleware`.

---

## Test Patterns

### TP-001: Module-Level Exit

**Location:** `tests/test_ollama.py`  
**Severity:** Critical  
**Pattern:** `sys.exit(1)` at module import time

---

### TP-002: Missing Dependencies

**Location:** `tests/security/test_security_suite.py`  
**Severity:** High  
**Pattern:** Import errors prevent collection

---

### TP-003: Long-Running Rate Tests

**Location:** `tests/api/test_rate_limit*.py`  
**Severity:** Low  
**Pattern:** Tests actually sleep for rate-limit durations

---

## Lint Patterns (All Resolved in v2.4.0)

All 664 ruff lint errors have been resolved across 251 files. Summary:

| Pattern | Rule | Count | Resolution |
|---------|------|-------|------------|
| StrEnum Inheritance | UP042 | 122 | Auto-fixed to `StrEnum` |
| Import Sorting | I001 | ~100 | Auto-fixed |
| Unused Imports | F401 | ~80 | Auto-fixed |
| Timezone Modernization | UP017 | ~50 | Auto-fixed to `datetime.UTC` |
| Manual List Comprehension | PERF401 | 85 | Converted to comprehensions/extend() |
| Undefined Names | F821 | 18 | Missing imports added |
| Style Issues | E712/C401/PERF102 | ~50 | Auto-fixed |
| Try-Except-Pass | S110/S112 | 78 | Annotated with `noqa` (intentional) |
| Hashlib Non-Crypto | S324 | 34 | Annotated with `noqa` (non-security use) |
| Hardcoded SQL | S608 | 24 | Per-file-ignores (internal query builders) |
| Security Patterns | S311/S603/S607/S104/S108 | 48 | Annotated with `noqa` (intentional) |
| Async Patterns | ASYNC109/110/250 | 20 | Annotated with `noqa` (intentional) |
| Misc (F841/E722/E721/F402/B039/UP047) | Various | ~12 | Manual fixes |

---

## Issue → Fix Mapping

| Issue ID | Pattern | Status | Fix Applied |
|----------|---------|--------|-------------|
| BP-001 | Double-Wrap Recursion | Fixed | Removed redundant add_middleware |
| BP-002 | Dict Key Slicing | Fixed | Added list() conversion |
| BP-003 | Missing Import Path | Fixed | Changed to absolute import |
| BP-004 | Missing Router Module | Fixed | Created safety.py stub |
| BP-005 | Auth Bypass Returns None | Fixed | Added deny-by-default raise |
| BP-006 | Double Ollama Listing | Fixed | Cached in variable |
| BP-007 | Directory Exclusion | Fixed | Switched to os.walk |
| BP-008 | Redundant Config Parsing | Fixed | Used self.config.copy() |
| BP-009 | Middleware Double Instantiation | Fixed | Single add_middleware call |
