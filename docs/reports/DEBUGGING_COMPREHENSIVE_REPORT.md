# GRID Comprehensive Debugging Report

**Generated:** 2026-03-10  
**Codebase:** GRID v2.6.1  
**Scope:** Debugging guidelines + codebase audit (bugs, TODOs, technical debt, test coverage)

---

## PART 1: GENERAL DEBUGGING GUIDE

### 1.1 Debugging Methodology

#### A. Problem Identification
1. **Reproduce the issue** - Document exact steps to trigger
2. **Capture symptoms** - Error messages, logs, stack traces
3. **Isolate scope** - Unit vs integration vs system level
4. **Check recent changes** - `git diff HEAD~5`, `git log --oneline -10`

#### B. Debugging Tools Stack

| Tool | Purpose | Command |
|------|---------|---------|
| **pytest** | Test execution | `uv run pytest tests/ -v` |
| **pytest -x** | Stop on first failure | `uv run pytest -x` |
| **pytest --pdb** | Drop into debugger | `uv run pytest <test> --pdb` |
| **pytest -s** | Show stdout/stderr | `uv run pytest -s` |
| **pytest --tb=short** | Short tracebacks | `uv run pytest --tb=short` |
| **python -m pdb** | Interactive debugger | `python -m pdb script.py` |
| **breakpoint()** | Built-in debugger (Python 3.7+) | Insert in code |
| **logging** | Structured logging | Use `structlog` |
| **tracing** | Action execution traces | `grid/tracing/` module |

#### C. Logging Best Practices

**Levels:**
- `DEBUG` - Verbose details (payloads, internal state)
- `INFO` - Lifecycle events (startup, shutdown, job completion)
- `WARNING` - Recoverable issues
- `ERROR` - Exceptions, failures
- `CRITICAL` - System unavailable

**GRID conventions:**
```python
import structlog

logger = structlog.get_logger()

# Always include trace_id if available
logger.debug("processing_event", trace_id=context.trace_id, payload=event)
logger.info("job_complete", job_id=job.id, duration=job.duration)
logger.error("operation_failed", error=str(e), context=context_dict)
```

**Security guardrail:** Never log secrets, tokens, passwords, or PII.

### 1.2 Common Debugging Scenarios

#### A. Test Failures

```bash
# Fast diagnosis workflow
uv run pytest --collect-only          # Verify environment/imports
uv run pytest -x                      # Stop on first failure
uv run pytest -v                      # Verbose output
uv run pytest -s                      # Show print statements
uv run pytest --tb=long               # Full traceback
uv run pytest <test> --pdb            # Interactive debug
uv run pytest --last-failed           # Re-run failed tests
uv run pytest -n auto                 # Parallel execution (xdist)
```

**Common issues:**
- `UnicodeDecodeError` - Add `encoding="utf-8"` to file opens
- `PydanticWarning` - Use `model_config = ConfigDict()` for Pydantic v2
- `PermissionError` - Windows file locking (retry or check process handles)
- `ModuleNotFoundError` - Check `PYTHONPATH`, `pyproject.toml` packages
- `async def` without `await` - Ensure async functions are awaited

#### B. Production Debugging

**Security guardrails (from AGENTS.md):**
- ❌ No `DEBUG=true` in production (checked by `scripts/assert_no_debug_in_prod.py`)
- ❌ No `ENABLE_DEV_TOKEN` in production
- ❌ No `str(e)` exposed to clients (generic 500 errors only)
- ✅ All agentic routes require `RequiredAuth`
- ✅ Admin routes use `AdminAuth`
- ✅ Body limits enforced (Mothership 10MB, Safety 50KB, RAG 1MB)
- ✅ Timeouts configured (Knowledge Base 60s, RAG 30s)

**Debug triage flow:**
```
1. Check logs → Identify error pattern
2. Check metrics → Isolate affected scope
3. Check recent deploys → Correlation with changes
4. Reproduce in staging → Verify fix before production
5. Enable DEBUG temporarily → Only if not exposing sensitive data
```

#### C. Performance Issues

**Profiling tools:**
```python
# Async debug mode
os.environ["PYTHONASYNCIODEBUG"] = "1"

# Line profiler
uv run python -m cProfile -o profile.stats script.py
uv run snakeviz profile.stats

# Memory profiler
from memory_profiler import profile
@profile
def my_func():
    ...
```

**GRID perf guides:**
- `docs/guides/DEBUG_PERFORMANCE_PROFILING.md`
- `docs/VERIFICATION_INSIGHTS_SUMMARY.md`

### 1.3 Debugging GRID-Specific Systems

#### A. Tracing System (`grid/tracing/`)

```python
from grid.tracing import TraceContext, trace_action

@trace_action(op_name="process_event")
async def process(event, context: TraceContext):
    # Access trace metadata
    trace_id = context.trace_id
    span_id = context.span_id
    
    # Trace automatically records:
    - Inputs/outputs
    - Duration
    - Exceptions
    - Nested spans
```

#### B. Cognitive Patterns

GRID implements 9 cognition patterns:
1. **Flow** - Event-driven architecture
2. **Spatial** - Layered DDD structure
3. **Rhythm** - Temporal sequencing
4. **Color** - Classification/tagging
5. **Repetition** - Pattern detection
6. **Deviation** - Anomaly detection
7. **Cause** - Dependency chains
8. **Time** - Temporal reasoning
9. **Combination** - Multi-pattern synthesis

Debug by checking pattern-specific logs in respective modules.

#### C. Safety Module (`safety/`)

**Debug checklist:**
- [ ] Review `docs/guides/SAFETY_DEBUG_CHECKLIST.md`
- [ ] Check safety pipeline logs
- [ ] Verify detector rules firing
- [ ] Audit guardian engine decisions
- [ ] Review observability metrics

```bash
# Enable safety debug mode
export SAFETY_DEBUG=true
export SAFETY_LOG_LEVEL=DEBUG
```

---

## PART 2: GRID CODEBASE DEBUGGING AUDIT

### 2.1 Technical Debt Summary

#### TODO/FIXME/BUG Count

| Pattern | Count | Severity |
|---------|-------|----------|
| TODO | ~238 | Medium |
| FIXME | ~15 | High |
| BUG | ~8 | Critical |
| XXX | ~3 | High |
| HACK | ~5 | Medium |

**Key files with debt:**
- `docs/TECHNICAL_DEBT_CLEANUP.md` - 26 top-level packages need consolidation
- `docs/search/TODO.md` - Search service deferred items (Phase 4-5)
- `src/tools/rag/embeddings/nomic_v2.py` - DEBUG print statements commented
- `docs/ANALYSIS_PRIORITIES_2026_02_02.md` - 63 TODO/FIXME comments noted

#### Critical Technical Debt Items

**1. Package Consolidation (Phase 2 - TECHNICAL_DEBT_CLEANUP.md)**

Current: 26 top-level packages with unclear boundaries  
Proposed: Consolidate to 12 packages

**Consolidation candidates:**
- `concept` + `pattern_engine` → `analysis/`
- `kernel` + `throughput_engine` → `orchestration/`
- `workflow_engine` + `nl_dev` → `automation/`
- `ares` → `external/ares/` (large external framework)
- `vision` → `external/vision/`

**Migration script pending:** `scripts/migrate_packages.py` (TODO at line 122)

**2. Configuration Issues**

- **Duplicate pyproject.toml sections** - mypy config duplicated (lines 100-114 vs 156-169)
- **Scattered dependencies** - `docs/requirements.txt` should be deleted, all deps in `pyproject.toml`
- **Multi-pyproject alignment** - `safety/` and `boundaries/` have separate configs (needs workspace consolidation)

**3. Lint Issues (Pre-Existing)**

**StrEnum inheritance (UP042)** - 20+ files:
```python
# Bad
class HandlerState(str, Enum): ...

# Good
from enum import StrEnum
class HandlerState(StrEnum): ...
```

**Affected files:**
- `src/application/mothership/api_core.py:50,59`
- `src/application/mothership/config/inference_abrasiveness.py:42,52`
- `src/application/mothership/middleware/circuit_breaker.py:47,55`
- `src/application/mothership/models/__init__.py` - 6 classes
- `src/application/mothership/models/cockpit.py` - 7 classes
- `src/application/mothership/schemas/__init__.py` - 5 classes
- `src/application/mothership/security/api_sentinels.py` - 3 classes

**Async blocking I/O (ASYNC230)** - 2+ files:
- `src/application/mothership/persistence/drt_storage.py:207,217`
- `src/application/mothership/routers/navigation.py:275`

**4. Root Directory Clutter**

**Issue:** 30+ loose scripts in root, test artifacts scattered

**Phase 1 cleanup needed:**
```bash
# Archive experimental scripts
mkdir -p _archive/experiments _archive/debug
mv debug_*.py _archive/debug/
mv comprehensive_fixer*.py _archive/experiments/

# Consolidate test artifacts
mkdir -p test_results/databases
mv test.db test_integration.db output*.json test_results/
```

**Current state:** 44 scripts in `scripts/` directory (organized), but root still has clutter

### 2.2 Known Bugs & Issues

#### A. Pre-Existing Issues (from PREEXISTING_ISSUES.md)

**Test Infrastructure:**
| File | Issue | Status |
|------|-------|--------|
| `tests/test_ollama.py` | Module-level `sys.exit(1)` on import | ❌ Not fixed |
| `tests/security/test_security_suite.py` | Import error on collection | ❌ Not fixed |
| Rate-limit tests | Actually sleep for minutes | ⚠️ Skip with markers |

**Fixed during session:**
- ✅ `data_corruption.py` import path corrected
- ✅ `routers/safety.py` module created
- ✅ `ParasiteGuardMiddleware` double-wrap recursion fixed
- ✅ `ParasiteTracer` dict slicing bug fixed

#### B. Security Guardrail Violations (Potential)

**Files with DEBUG statements:**
```
security/network_interceptor.py:25 - Hardcoded DEBUG level
security/network_access_control.yaml:24 - DEBUG log level
mcp-setup/README.md:294 - Example DEBUG commands
infrastructure/docker/docker-entrypoint.sh:128 - DEBUG echo
```

**Action:** Review if these can trigger in production (most are examples/docs, but `network_interceptor.py` needs audit)

#### C. Search Service Deferred (docs/search/TODO.md)

**Pending:**
- [ ] SEARCH_FULL_PIPELINE - Fusion/ranking/facets implementation
- [ ] AccessControl - Real index/field allowlists (currently stub)
- [ ] GUARDRAIL_DEFAULT - Set `GUARDRAIL_ENABLED=true` by default

### 2.3 Test Coverage Analysis

#### Test Inventory

```
tests/
├── unit/                 # ~150 tests
├── integration/          # ~80 tests
├── e2e/                  # ~40 tests
├── api/                  # ~60 tests
├── security/             # ~30 tests (guardrail tests critical)
├── safety/               # ~50 tests
├── agentic/              # ~25 tests
├── auth/                 # ~20 tests
├── cognitive/            # ~35 tests
├── mycelium/             # ~30 tests
├── resilience/           # ~15 tests
├── load/                 # ~10 tests
└── fixtures/             # Shared fixtures
```

**Total:** 438+ tests (all passing per task_result)

**Test markers:**
- `unit` - Fast, isolated
- `integration` - Cross-module
- `safety` - Safety enforcement
- `security` - Security guardrails
- `critical` - Must-pass tests
- `slow` - Skip in CI by default
- `flaky` - Quarantined
- `asyncio` - Async tests
- `database` - DB-dependent
- `redteam` - Offensive security

**Coverage target:** ≥80%

#### Critical Security Test Commands

```bash
# Security guardrails
uv run pytest tests/api/test_phase3_security_guardrails.py \
              tests/security/test_attack_surface_guardrails.py \
              tests/api/test_security_governance.py -v

# Safety tests
uv run pytest -m safety -q --tb=short

# All except slow/flaky
uv run pytest -m "not slow and not flaky" -q --tb=short
```

### 2.4 Debug Hotspots

#### Files Requiring Debug Attention

**1. RAG Embedding Module** (`src/tools/rag/embeddings/nomic_v2.py`)
```python
# Lines 79-91 - DEBUG print statements commented out
# DEBUG: Print what we are attempting
# print(f"DEBUG: Attempting ollama.embeddings with {model_name}")
# DEBUG: Print result status
# print(f"DEBUG: Embedding is empty/None...")
```
**Action:** Remove or convert to proper logging

**2. Resonance API** (`src/application/resonance/api/router.py`)
```python
# Lines 833-840 - Debug endpoints gated by DEBUG env
if os.getenv("DEBUG", "").lower() not in ("1", "true", "yes"):
    return 404
```
**Security:** Properly gated, but verify no production exposure

**3. Intent Classifier** (`src/tools/rag/intelligence/intent_classifier.py`)
```python
# Line 26, 109, 167 - DEBUGGING intent classification
Intent.DEBUGGING = "debugging"
```
**Note:** This is legitimate intent classification, not code debugging

**4. CSV Pipeline** (`src/utils/csv_pipeline.py`)
```python
# Line 435 - CLI debug flag
"--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"]
```
**Note:** User-configurable, acceptable

#### Log Files Found

```
./.cursor/debug-7ca162.log          # IDE session debug
./.cursor/debug-7d9fb0.log          # IDE session debug
./debug-14d2f0.log                  # Root debug log
./data/audit.log                    # Audit trail
./data/benchmark_diagnostics.log    # Performance diagnostics
./docs/grid.log                     # Docs generation log
./docs/pytest_debug.log             # Test debug output
./logs/security/mothership_audit.log # Security audit
./logs/security/vection_audit.log   # Vection security audit
```

**Action:** Ensure `.log` is in `.gitignore` (already covered by `*.log`)

### 2.5 Configuration Debug Checklist

#### Environment Variables (.env.example)

**Critical debug-related:**
```bash
DEBUG=false                          # Must be false in production
GRID_ENV=production                  # production/staging/development
MOTHERSHIP_DEBUG=false              # Mothership debug flag
SAFETY_DEBUG=false                  # Safety module debug
RAG_LLM_MODE=local                  # local/external (debug external carefully)
```

**Verification script:**
```bash
# Production gate (CI/CD)
scripts/assert_no_debug_in_prod.py

# Manual check
grep -E "^DEBUG=|^GRID_ENV=" .env
```

#### pyproject.toml Test Config

```toml
[tool.pytest.ini_options]
timeout = 30              # 30s timeout per test
timeout_method = "thread" # Thread-based timeout
addopts = [
    "--tb=short",         # Short tracebacks
    "-q",                 # Quiet mode
    "--durations=10",     # Show 10 slowest
    "--maxfail=5",        # Stop after 5 failures
]
```

**Debug tip:** Temporarily remove `--tb=short` for full stack traces

### 2.6 CI/CD Debug Gates

**GitHub Actions (`.github/workflows/ci.yml`)**

**Phase 4 gates:**
```yaml
- name: "Assert no DEBUG in production (Phase 4 gate)"
  # Fails if DEBUG=true in production environment

- name: "Assert no DEBUG in production build (Phase 4)"
  # Checks DEBUG and ECHOES_API_DEBUG env vars
```

**Debug workflow:**
1. Test suite fails → Check test logs
2. Lint fails → Run `uv run ruff check .`
3. Type check fails → Run `uv run mypy src/`
4. Security gate fails → Run `scripts/assert_no_debug_in_prod.py`
5. Performance regression → Check benchmark diffs

---

## PART 3: ACTION ITEMS & PRIORITIES

### Critical (Immediate)

- [ ] **Fix test collection crashes** - `tests/test_ollama.py`, `tests/security/test_security_suite.py`
- [ ] **Remove hardcoded DEBUG** - `security/network_interceptor.py:25`
- [ ] **Complete StrEnum migration** - 20+ files (UP042 lint errors)
- [ ] **Verify no DEBUG in production** - Run `scripts/assert_no_debug_in_prod.py` in CI

### High (This Sprint)

- [ ] **Implement SEARCH_FULL_PIPELINE** - Fusion/ranking/facets
- [ ] **Implement AccessControl allowlists** - Replace stubs in search service
- [ ] **Remove debug print statements** - `src/tools/rag/embeddings/nomic_v2.py`
- [ ] **Consolidate duplicate pyproject.toml** - Remove mypy config duplication
- [ ] **Archive root experimental scripts** - Phase 1 cleanup from TECHNICAL_DEBT_CLEANUP.md

### Medium (Next Sprint)

- [ ] **Package consolidation** - 26 → 12 packages (Phase 2)
- [ ] **Mylint async blocking I/O** - Convert `open()` to `aiofiles`
- [ ] **Set GUARDRAIL_ENABLED=true** by default
- [ ] **Review all 238 TODOs** - Categorize and prioritize
- [ ] **Root directory cleanup** - Move test artifacts to `test_results/`

### Low (Backlog)

- [ ] **Document .cursor/ tracking decision** - Track shared skills or keep local?
- [ ] **Add explicit debug-*.log pattern** - For clarity in .gitignore
- [ ] **Create migration script** - For package consolidation
- [ ] **Update CONTRIBUTING.md** - Package organization rules

---

## PART 4: DEBUGGING RESOURCES

### Documentation Files

| File | Purpose |
|------|---------|
| `docs/DEBUGGING.md` | General debugging guide |
| `docs/guides/DEBUG_TROUBLESHOOTING_TREE.md` | Decision tree for debug scenarios |
| `docs/guides/DEBUG_PERFORMANCE_PROFILING.md` | Performance profiling guide |
| `docs/guides/SAFETY_DEBUG_CHECKLIST.md` | Safety module debugging |
| `docs/PREEXISTING_ISSUES.md` | Known pre-existing bugs |
| `docs/TECHNICAL_DEBT_CLEANUP.md` | Technical debt remediation |
| `docs/CONFIG_CONSOLIDATION_REPORT.md` | Configuration alignment status |
| `docs/VERIFICATION_INSIGHTS_SUMMARY.md` | Test verification insights |

### Scripts

| Script | Purpose |
|--------|---------|
| `scripts/assert_no_debug_in_prod.py` | Production debug gate |
| `scripts/debug_async_tasks.py` | Async task debugging |
| `scripts/debug_guardian.py` | Guardian engine debug |
| `scripts/debug_health_check.py` | Health check debugging |
| `scripts/analyze_issues.py` | Issue analysis automation |

### Test Commands Quick Reference

```bash
# Full test suite
uv run pytest tests/unit tests/integration tests/security tests/api -q --tb=short

# Unit tests only
uv run pytest -m unit -q --tb=short

# Safety tests
uv run pytest -m safety -q --tb=short

# Security guardrails
uv run pytest tests/api/test_phase3_security_guardrails.py \
              tests/security/test_attack_surface_guardrails.py \
              tests/api/test_security_governance.py -v

# Last failed
uv run pytest --last-failed

# Parallel execution
uv run pytest -n auto

# With debugger
uv run pytest <test> --pdb

# Show coverage
uv run pytest --cov=src/ --cov-report=html
```

---

## PART 5: DEBUGGING WORKFLOW TEMPLATE

### For Production Issues

```
1. **Triage**
   - Capture error message
   - Identify affected users/scopes
   - Check recent deploys (`git log --oneline -10`)
   - Review monitoring dashboards

2. **Reproduce**
   - Attempt reproduction in staging
   - Document exact steps
   - Capture logs (`DEBUG=false` in staging, then temporarily enable)

3. **Isolate**
   - Identify component (grid/application/cognitive/search/safety)
   - Check related tests
   - Review recent changes to component

4. **Debug**
   - Add logging (structured, no secrets)
   - Use tracer if applicable
   - Run with `--pdb` if interactive needed
   - Profile if performance issue

5. **Fix**
   - Write failing test first
   - Implement minimal fix
   - Run security guardrail tests
   - Verify no DEBUG exposure

6. **Deploy**
   - Run full test suite
   - Run lint + typecheck
   - Run assert_no_debug_in_prod.py
   - Deploy to staging, verify
   - Deploy to production, monitor
```

### For Test Failures

```
1. **Fast diagnosis**
   uv run pytest --collect-only              # Verify imports
   uv run pytest -x                          # Stop on first
   uv run pytest <test> -v --tb=short        # Verbose short trace

2. **Deep dive**
   uv run pytest <test> -s                   # Show outputs
   uv run pytest <test> --pdb                # Interactive debug
   uv run pytest <test> --tb=long            # Full traceback

3. **Fix**
   - Identify root cause (import? assertion? timeout?)
   - Check if pre-existing (see PREEXISTING_ISSUES.md)
   - Fix minimally
   - Add regression test if needed

4. **Verify**
   - Run related tests
   - Run full suite if critical
   - Check coverage impact
```

---

## Appendix A: Debugging Checklist

### Pre-Commit Debug Checklist

- [ ] No `print()` statements (use structlog)
- [ ] No hardcoded `DEBUG=True`
- [ ] No commented-out DEBUG blocks
- [ ] All exceptions logged with context
- [ ] No secrets in logs
- [ ] Tests pass locally
- [ ] Lint clean (`uv run ruff check .`)
- [ ] Type check clean (`uv run mypy src/`)

### Pre-Deploy Debug Checklist

- [ ] `DEBUG=false` in production env
- [ ] `GRID_ENV=production`
- [ ] Run `scripts/assert_no_debug_in_prod.py`
- [ ] All security guardrail tests pass
- [ ] All safety tests pass
- [ ] No `str(e)` exposed to clients
- [ ] Body limits configured
- [ ] Timeouts configured
- [ ] Auth required on agentic routes
- [ ] Admin auth on admin routes
- [ ] Logs reviewed for sensitive data
- [ ] Monitoring in place

---

## Appendix B: Contact & Escalation

**For debugging help:**
1. Check `docs/DEBUGGING.md`
2. Review `docs/PREEXISTING_ISSUES.md`
3. Search existing issues in tracker
4. Consult `docs/guides/DEBUG_TROUBLESHidTING_TREE.md`
5. Ask in team channels with:
   - Error message
   - Steps to reproduce
   - What you've tried
   - Relevant logs (redact secrets)

---

**Report generated by:** opencode (qwen3.5:cloud)  
**For:** GRID codebase debugging audit  
**Date:** 2026-03-10
