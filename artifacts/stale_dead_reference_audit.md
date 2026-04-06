# Stale / Dead / Mismatched Reference Audit
**Generated:** 2026-04-06 (live sweep of `src/` + `tests/`, 801 source files)
**Commit:** 7500f7c (v2.8.0)

---

## Summary

| Tier | Category | Count | Severity |
|------|----------|-------|----------|
| 1 | Broken intra-`src/` imports (guarded, won't crash import) | 7 callsites | High |
| 2 | Misplaced file in `src/` | 1 file | Medium |
| 3a | Permanently skipped test modules — `light_of_the_seven` | 4 files | Medium |
| 3b | Permanently skipped test modules — `legacy_src` / `grid.patterns.engine` | 3 files | Medium |
| 3c | Permanently skipped test modules — `Arena/the_chase` | 12 files | Medium |
| 3d | Permanently skipped integration test modules — known API gaps | 4 files | Medium |
| 3e | `xfail` tests referencing unrealised "Phase 2" work | 2 tests | Low |
| 4 | Tests importing non-existent `grid.navigation` submodules | 5 import sites | High |
| 5 | Tests for `grid.version_3_5`, `grid.version_4_5`, `grid.essence`, `acoustics.tap_model` | 4 files | Low |
| 6 | `integration/test_rag_evolution.py` — entire test class skip-annotated (API drift) | 8 skips | Medium |

---

## Tier 1 — Broken Intra-`src/` Imports (guarded)

All 7 are wrapped in `try/except ImportError` or use `# type: ignore[import-not-found]`.
They will silently degrade at callsite, not at module import. The referenced modules **do not exist**.

| File | Line | Missing Module | Impact |
|------|------|---------------|--------|
| `src/application/mothership/middleware/apiguard_adapter.py` | 30 | `grid.cognitive.engine` → `CognitiveEngine` | Rate-limit cognitive fallback disabled |
| `src/application/mothership/middleware/rate_limit_redis.py` | 22 | `grid.cognitive.engine` → `CognitiveEngine` | Same — Redis rate limiter loses cognitive branch |
| `src/application/resonance/api/performance.py` | 22 | `grid.persistence.database` → `get_db` | Performance API DB path silently unavailable |
| `src/search/query/intent.py` | 21 | `tools.rag.intelligence.intent_classifier` | Intent classification falls back to rule-based |
| `src/tools/rag/cli.py` | 371 | `tools.rag.file_tracker` → `FileTracker` | CLI file-tracking path dead |
| `src/tools/rag/indexing/comprehensive_indexer.py` | 19 | `tools.rag.comprehensive_indexer` | Self-referential import loop (module tries to import itself from a different path) |
| `src/tools/slash_commands/sync.py` | 98 | `tools.rag.enhanced.embeddings` → `EnhancedRAG, RetrievalConfig` | Sync slash command enhanced RAG path dead |

**Note:** `tools.rag.intelligence.intent_classifier` absence is expected per AGENTS.md (`--group finetuning` installs the classifier; without it, rule-based fallback applies). The rest are unintentional.

**Action:**
- `grid.cognitive.engine` — either create the module or remove the conditional branch in `apiguard_adapter.py` and `rate_limit_redis.py`
- `grid.persistence.database` — locate or alias `get_db` from the existing SQLAlchemy session infrastructure
- `tools.rag.file_tracker` — create stub or remove dead path in `cli.py:371`
- `tools.rag.comprehensive_indexer` — fix self-referential import in `comprehensive_indexer.py:19`
- `tools.rag.enhanced.embeddings` — create or remove dead path in `sync.py:98`

---

## Tier 2 — Misplaced File

| File | Issue | Action |
|------|-------|--------|
| `src/test_semantic_chunking.py` | Test script inside `src/`. Also imports `tools.rag.semantic_chunker` which does **not exist**. | Move to `tests/` (after fixing the import) or delete if superseded |

---

## Tier 3a — Permanently Skipped: `light_of_the_seven` (4 files)

All four skip at module level. `light_of_the_seven` and `cognitive_layer` namespaces do not exist in this repo.

| File | Skip Reason |
|------|-------------|
| `tests/unit/test_enhanced_path_navigator.py` | `light_of_the_seven module not available` |
| `tests/unit/test_input_processor.py` | `light_of_the_seven module not available` |
| `tests/unit/navigation/test_navigation_input.py` | `light_of_the_seven module not available` |
| `tests/unit/navigation/test_path_optimization_agent.py` | `light_of_the_seven module not available` |

**Action:** These are orphan tests from a prior monorepo layout. Either:
- Rewrite imports against the current `src/` layout (if the behaviour is still relevant), or
- Delete the files and record as intentional removal in the next PR

---

## Tier 3b — Permanently Skipped: `legacy_src` / `grid.patterns.engine` (3 files)

`grid.patterns.engine` **exists** at `src/grid/patterns/engine.py` — the import fails for a different reason (see note).

| File | Skip Reason | Note |
|------|-------------|------|
| `tests/unit/test_pattern_engine_matching.py` | `legacy_src module not available` | Imports from `grid.patterns.engine` which exists — investigate actual failure |
| `tests/unit/test_pattern_engine_rag.py` | `legacy_src module not available` | Same |
| `tests/unit/test_pattern_engine_mist.py` | `legacy_src module not available` | Same |

**Action:** These tests have a misleading skip reason — `grid.patterns.engine` *does* exist. The actual skip is triggered inside the `try` block before the `pytestmark` line. Verify by running one directly with `uv run pytest tests/unit/test_pattern_engine_matching.py -v` to get the real error. Likely a secondary import fails inside `grid.patterns.engine`.

---

## Tier 3c — Permanently Skipped: `Arena/the_chase` (12 files)

`the_chase` is an external/optional dependency not present in this repo's venv. All 12 files skip correctly at collection time — but they are completely inert and accumulate test collection overhead.

**Files:**
- `tests/misc/test_edge_cases.py`
- `tests/misc/test_wellness_integration.py`
- `tests/misc/test_windsurf_integration.py`
- `tests/resilience/test_honor_decay_edge_cases.py`
- `tests/resilience/test_honor_decay.py`
- `tests/arena/test_overwatch_resonance_arena.py`
- `tests/arena/test_adsr_sustain_fix.py`
- `tests/arena/benchmark_arena_structure.py`
- `tests/arena/run_arena_tests.py`
- `tests/arena/test_sustain_decay_arena.py`
- `tests/arena/test_arena_structure_fixes.py`
- `tests/arena/test_adsr_arena_integration.py`

**Action:** If `the_chase` will never be installed in this venv, move these files to a dedicated `tests/arena/_disabled/` directory or add to a pytest `ignore` pattern in `pyproject.toml` to keep collection fast.

---

## Tier 3d — Permanently Skipped Integration Test Modules (4 files)

These skip with actionable reasons — each identifies missing implementation.

| File | Reason | Action |
|------|--------|--------|
| `tests/integration/test_repositories.py` | `MockRepository broken on Python 3.13 — needs rewrite with real DB fixtures` | Rewrite using SQLite in-memory fixtures |
| `tests/integration/test_repository_patterns.py` | Same — also references `test_repositories.py` | Rewrite together |
| `tests/integration/test_skills_system_comprehensive.py` | `SkillExecutionResult class, full sandbox API missing` | Implement or remove |
| `tests/unit/test_gci_definition.py` | `DEFINITION module not fully implemented` — missing `CognitiveState`, `CognitiveTrace` | Implement or stub in `src/cognitive/context/DEFINITION.py` |

---

## Tier 3e — `xfail` Tests Referencing Unrealised "Phase 2" Work

| File | Lines | Reason |
|------|-------|--------|
| `tests/api/test_auth_jwt.py` | 370, 395 | `Requires Phase 2: AI Brain Integration - navigation module initialization` |

**Action:** `grid.navigation` module does **not exist** (see Tier 4). Either implement the navigation module or convert these to `skip` with a tracking issue reference.

---

## Tier 4 — Tests Importing Non-Existent `grid.navigation` Submodules (HIGH)

`src/grid/navigation/` does not exist. Five distinct import sites in `tests/integration/test_navigation_intelligence.py` will fail if tests are ever run (currently protected by conditional import guards).

| Line | Missing Module |
|------|---------------|
| 63 | `grid.navigation.enhanced_navigator` |
| 68 | `grid.navigation.schemas.navigation_input` |
| 340 | `grid.navigation.decision_matrix` |
| 355 | `grid.navigation.adaptive_scorer` |
| 375 | `grid.navigation.path_optimizer` |

**Related:** `tests/unit/test_enhanced_path_navigator.py` and siblings (Tier 3a) also target these — the `light_of_the_seven` namespace was an earlier alias for the same unbuilt navigation package.

**Action:** This is a structural gap. `grid.navigation` is either:
- A planned module that was never implemented → add a tracking issue
- Intended to live under a different namespace → update test imports accordingly

---

## Tier 5 — Tests for Unimplemented/Optional Modules (low noise)

These use `pytest.importorskip` — safe, but represent dead test surface.

| File | Missing Module |
|------|---------------|
| `tests/version/test_version_3_5.py` | `grid.version_3_5` (exists at `src/grid/version_3_5.py` — investigate) |
| `tests/version/test_version_4_5.py` | `grid.version_4_5` (exists at `src/grid/version_4_5.py` — investigate) |
| `tests/misc/test_grid_benchmark.py` | `grid.essence` (exists at `src/grid/essence/` — investigate) |
| `tests/misc/test_grid_intelligence.py` | `grid.essence` (same) |
| `tests/misc/test_tap_model.py` | `acoustics.tap_model` (no `acoustics` package in repo) |

**Note:** `grid.version_3_5`, `grid.version_4_5`, and `grid.essence` all **exist** in `src/`. The `importorskip` failures are likely secondary import errors inside those modules. Run individually to expose the actual failure.

---

## Tier 6 — `integration/test_rag_evolution.py` — API Drift (8 skipped classes)

All test classes in this file are skip-annotated because the evolution module APIs drifted from test expectations.

| Skip Reason |
|-------------|
| `FibonacciEvolutionEngine uses fibonacci.generate(n), not generate_sequence` |
| `FibonacciEvolutionEngine uses evolve_with_fibonacci, not evolve_state` |
| `FibonacciEvolutionState uses base_state/context, not complexity/stability; no save/load` |
| `FibonacciEvolutionEngine has no adapt_state; uses evolve_with_fibonacci` |
| `VersionState API uses essential_state/context, not current_version/evolution_sequence` |
| `LandscapeDetector API differs (no capture_landscape, detect_shift, register_analyzer)` |
| `RealTimeAdapter/WeightUpdate/AdaptationState APIs differ from test expectations` |

The **actual classes exist** in `src/grid/evolution/` — this is a test-vs-implementation API mismatch, not a missing module.

**Action:** Update the test file to match the current evolution API. All seven skip blocks should become real tests.

---

## Pending Action Items (Prioritised)

### P0 — Fix Now (runtime degradation, no tests covering the gap)
1. **`tools.rag.comprehensive_indexer` self-referential import** — `src/tools/rag/indexing/comprehensive_indexer.py:19`
2. **`grid.cognitive.engine` missing** — two middleware files silently lose cognitive rate-limiting branch
3. **`src/test_semantic_chunking.py` misplaced** — test file in `src/`, imports missing module

### P1 — Fix Soon (dead test surface, silent API drift)
4. **`integration/test_rag_evolution.py`** — rewrite 7 skip-annotated test classes against current `src/grid/evolution/` API
5. **`integration/test_repositories.py` + `test_repository_patterns.py`** — rewrite with real SQLite fixtures for Python 3.13
6. **Investigate real skip reason for `test_pattern_engine_*.py`** — `grid.patterns.engine` exists; find the actual import failure

### P2 — Track / Plan (unimplemented modules)
7. **`grid.navigation` package** — 5 import sites in integration tests, 4 unit test files, 2 `xfail` API tests all point here. Either build it or close these tests with a tracking issue.
8. **`tools.rag.file_tracker`** — dead path in `cli.py:371`
9. **`tools.rag.enhanced.embeddings`** — dead path in `sync.py:98`
10. **`grid.persistence.database`** — missing `get_db` in resonance performance API

### P3 — Cleanup (noise / dead weight)
11. **`tests/arena/` (12 files)** — add to pytest `ignore` pattern or move to `_disabled/` if `the_chase` won't be installed
12. **`tests/unit/navigation/` + `tests/unit/test_*_path_navigator.py` (4 files)** — `light_of_the_seven` orphans; delete or rewrite
13. **`tests/misc/test_tap_model.py`** — `acoustics` package doesn't exist; delete or move to pending
14. **`tests/integration/test_skills_system_comprehensive.py`** — `SkillExecutionResult` not implemented; track or delete
15. **`tests/unit/test_gci_definition.py`** — `CognitiveState`/`CognitiveTrace` not in `DEFINITION.py`; implement or delete

---

## Verification Commands

```bash
# Confirm pattern engine real failure
uv run pytest tests/unit/test_pattern_engine_matching.py -v --no-header 2>&1 | head -30

# Confirm grid.essence importorskip failure
uv run pytest tests/misc/test_grid_benchmark.py -v --no-header 2>&1 | head -20

# Confirm grid.version_3_5 importorskip failure
uv run pytest tests/version/test_version_3_5.py -v --no-header 2>&1 | head -20

# Count total skipped/dead tests across the full suite
uv run pytest tests/ --collect-only -q 2>&1 | tail -5
```
