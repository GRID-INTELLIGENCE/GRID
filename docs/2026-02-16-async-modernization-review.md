# Async Modernization & Quality Review — 2026-02-16

## Session Summary

Systematic code review and modernization pass focused on async patterns, blocking I/O, enum correctness, and lint compliance across the GRID codebase.

---

## Changes Applied

### 1. AbrasivenessCadence Enum Bug Fix

**File**: `src/application/mothership/config/inference_abrasiveness.py`

**Bug**: `from_dict()` did not handle `int` values from `to_dict()` round-trip. Since `AbrasivenessCadence` is an `IntEnum`, `to_dict()` serializes `.value` as `int`, but `from_dict()` only checked `str` and `Enum` types — silently falling back to defaults.

**Fix**: Added `isinstance(..., int)` branches for `global_cadence` and `cadence_override` deserialization. Also cleaned unused `IntEnum`/`StrEnum` imports from inline `from enum import`.

### 2. Blocking I/O Pattern Modernization

Replaced **7 instances** of deprecated `loop.get_event_loop().run_in_executor(None, ...)` with modern `asyncio.to_thread()` (Python 3.9+ standard):

| File | Change |
|------|--------|
| `src/grid/spark/core.py` | `invoke_async` parallel execution |
| `src/grid/events/core.py` | `emit_async` event emission |
| `src/tools/rag/retrieval/cross_encoder_reranker.py` | `async_rerank` CPU-bound wrapper |
| `src/tools/rag/llm/copilot.py` | `async_generate` text completion |
| `src/tools/rag/indexing/comprehensive_indexer.py` | `async_embed` and `async_embed_batch` |
| `src/application/mothership/api_core.py` | sync handler execution in `summon_handler` |
| `src/grid/billing/stripe_service.py` | 3 Stripe API calls (`create_customer`, `create_subscription`, `report_usage`) |

### 3. Undefined `timezone` Bug Fix

**File**: `src/tools/rag/indexing/comprehensive_indexer.py`

**Bug**: 3 references to `timezone.utc` without `timezone` being imported (F821). Likely remnant from a prior `timezone.utc` → `datetime.UTC` migration that missed these lines.

**Fix**: Added `UTC` to `from datetime import` and replaced all `timezone.utc` → `UTC`.

### 4. Lint Compliance Improvements

| Rule | File | Fix |
|------|------|-----|
| UP042 | `spark/core.py` | `SparkPhase(str, Enum)` → `SparkPhase(StrEnum)` |
| F401 | `api_core.py` | Removed unused `functools` import (after `asyncio.to_thread` migration) |
| F401 | `spark/core.py` | Removed unused `Enum` import (after `StrEnum` migration) |
| PERF102 | `events/core.py` | `.items()` → `.values()` where only values used |
| C414 | `spark/core.py` | Removed unnecessary `list()` in `sorted()` |

### 5. Gitignore Cleanup

Added patterns for `tmpclaude-*`, `pytest_out*.txt`, `diff_ac.txt`, and `nul` scratch artifacts.

---

## Sync `requests` Audit

All sync `requests` usage was audited and found to be in appropriate sync contexts:

- `staircase.py` — `StaircaseAPI` is an explicitly sync HTTP client
- `pipeline.py` — sync `ManifestPipeline` (requests imported but HTTP calls are stubbed)
- `openai.py` — sync `check_openai_safety()` function
- `distributed_spark_indexer.py` — Spark UDF context (must be sync)
- `health_check.py` — standalone CLI script

No migration to `httpx` needed for these files.

---

## Remaining Pre-existing Lint Issues (Not From This Session)

- 4× PERF401 in `comprehensive_indexer.py` — list append patterns
- 2× S324 in `comprehensive_indexer.py` — MD5 for chunk IDs (non-security context)
- 3× S607/S603 in `copilot.py` — subprocess with partial executable path

---

## Validation

- **9/9 modified files** compile clean (`py_compile`)
- **Ruff**: 0 new errors introduced; 7 pre-existing errors fixed; 9 remaining are all pre-existing in untouched code
