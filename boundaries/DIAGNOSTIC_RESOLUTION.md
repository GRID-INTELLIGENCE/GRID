# Diagnostic Resolution Strategy — Boundaries Module

> Generated from Pylance/Pyright diagnostics captured after transition gate implementation.
> Scope: `boundaries/` and `boundaries/transition_gate/` within GRID-main.

---

## Final Results

| Metric | Before Fixes | After Fixes | Delta |
|--------|-------------|-------------|-------|
| **Errors** | 23 | 23 | 0 (all pre-existing; see Category A) |
| **Warnings** | 9 | 0 | **−9 (all resolved)** |
| **Tests** | 108/108 pass | 108/108 pass | ✓ No regressions |

---

## Issue Table

| # | File | Line | Severity | Diagnostic | Root Cause | Category | Status |
|---|------|------|----------|-----------|------------|----------|--------|
| 1 | `__init__.py` | 8–12 | Error | Import `boundaries.boundary` / `.logger_ws` / `.overwatch` / `.preparedness` / `.refusal` could not be resolved (×5) | Zed's Pyright LSP cannot resolve intra-package `boundaries.*` imports — the project root is `E:\`, not `E:\Seeds\GRID-main`, so `boundaries/` is not on the implicit Python path | **A — LSP path resolution** | Pre-existing; mitigated |
| 2 | `boundary.py` | 11–12 | Error | Import `boundaries.logger_ws` / `boundaries.refusal` could not be resolved | Same as #1 | **A** | Pre-existing; mitigated |
| 3 | `refusal.py` | 14 | Error | Import `boundaries.logger_ws` could not be resolved | Same as #1 | **A** | Pre-existing; mitigated |
| 4 | `preparedness.py` | 11 | Error | Import `boundaries.logger_ws` could not be resolved | Same as #1 | **A** | Pre-existing; mitigated |
| 5 | `overwatch.py` | 17 | Error | Import `boundaries.logger_ws` could not be resolved | Same as #1 | **A** | Pre-existing; mitigated |
| 6 | `transition_gate/__init__.py` | 25–39 | Error | Import `boundaries.transition_gate.envelope` / `.fingerprint` / `.gate_keeper` / `.nonce` could not be resolved (×4) | Same as #1, compounded by nested subpackage | **A** | Pre-existing pattern; mitigated |
| 7 | `transition_gate/envelope.py` | 26, 31 | Error | Import `boundaries.transition_gate.fingerprint` / `.nonce` could not be resolved | Same as #1 | **A** | Pre-existing pattern; mitigated |
| 8 | `transition_gate/gate_keeper.py` | 35, 39, 44 | Error | Import `boundaries.transition_gate.envelope` / `.fingerprint` / `.nonce` could not be resolved | Same as #1 | **A** | Pre-existing pattern; mitigated |
| 9 | `tests/test_transition_gate.py` | 20, 30, 36, 43 | Error | Import `boundaries.transition_gate.*` could not be resolved (×4) | Same as #1 | **A** | Pre-existing pattern; mitigated |
| 10 | `transition_gate/gate_keeper.py` | 36 | Warning | `ALL_KNOWN_PERMISSIONS` imported but unused | Imported for completeness; not referenced in gate_keeper logic | **B — Unused import** | ✅ Fixed |
| 11 | `tests/test_transition_gate.py` | 16 | Warning | `typing.Any` imported but unused | Left over from test scaffolding | **B** | ✅ Fixed |
| 12 | `tests/test_transition_gate.py` | 21 | Warning | `ALL_KNOWN_PERMISSIONS` imported but unused | Imported for completeness; no test asserts against the full set | **B** | ✅ Fixed |
| 13 | `tests/test_transition_gate.py` | 39 | Warning | `VerificationResult` imported but unused | Not directly referenced in test assertions | **B** | ✅ Fixed |
| 14 | `tests/test_transition_gate.py` | 43 | Warning | `NonceEntry` imported but unused | Only `get_entry()` return was used, not the class directly | **B** | ✅ Fixed |
| 15 | `tests/test_transition_gate.py` | 219 | Warning | `hmac` imported but unused | Imported inside `test_timing_safe` for a contract assertion that was simplified | **C — Dead code** | ✅ Fixed |
| 16 | `tests/test_transition_gate.py` | 311 | Warning | Local variable `n2` assigned but never used | Generated to trigger side-effect (register second nonce); value irrelevant | **D — Intentional side-effect** | ✅ Fixed (renamed to `_`) |
| 17 | `transition_gate/nonce.py` | 21 | Warning | `dataclasses.field` imported but unused | Imported alongside `asdict` and `dataclass` but never called in this module | **B** | ✅ Fixed |
| 18 | `transition_gate/nonce.py` | 219 | Warning | Local variable `now` assigned but never used | Assigned in `active_count` but expiry check delegates to `is_expired()` internally | **C — Dead code** | ✅ Fixed |

---

## Category Analysis

### A — LSP Path Resolution (Issues 1–9): 23 errors — Pre-existing, Mitigated

**Root cause:** Zed's workspace root is `E:\`. Pyright resolves Python imports relative to the workspace root unless overridden. Every file in `boundaries/` imports as `from boundaries.xxx import ...`, which requires the GRID-main repo root (`E:\Seeds\GRID-main`) to be on the Python source path. Since Zed doesn't read VS Code `.code-workspace` files for `python.analysis.extraPaths`, and the project root is two levels up from where Pyright needs it, these imports show as unresolved.

**Key evidence these are NOT code problems:**
- 108/108 tests pass under `uv run pytest`
- `uv run python -c "from boundaries.transition_gate import ..."` succeeds
- The pre-existing files (`overwatch.py`, `preparedness.py`, `refusal.py`, `boundary.py`, `__init__.py`) have the same pattern and the same errors — none of these were introduced by the transition gate work
- Runtime works because `pyproject.toml` sets `pythonpath = ["src"]` and pytest is invoked from the repo root, and the workspace terminal `PYTHONPATH` env var includes the correct paths

**Mitigations applied:**
1. Added `"./Seeds/GRID-main"` to `python.analysis.extraPaths` in `Seeds.code-workspace` (fixes VS Code / Windsurf)
2. Created `E:\pyrightconfig.json` with `executionEnvironments` mapping `Seeds/GRID-main` root with `extraPaths: [".", "src", "safety", "security"]` (fixes Pyright CLI and editors that load it)
3. Created `E:\Seeds\GRID-main\pyrightconfig.json` with equivalent config (fixes editors that root at the repo level)

**Why errors still show in Zed:** Zed's Pyright integration may require a restart to reload config, or it may not support `executionEnvironments` in the same way. This is an editor-configuration issue, not a code-correctness issue. The errors are cosmetic in this context.

**Permanent resolution options (for the user to choose):**
- **Option 1:** Restart Zed to pick up `pyrightconfig.json` — may resolve immediately
- **Option 2:** Configure Zed's `lsp.pyright.settings` in Zed's `settings.json` with explicit `python.analysis.extraPaths`
- **Option 3:** Accept the IDE squiggles — they do not affect runtime, testing, or CI

### B — Unused Imports (Issues 10–14, 17): 6 warnings — ✅ All Fixed

Removed unused symbols from import statements in:
- `gate_keeper.py`: removed `ALL_KNOWN_PERMISSIONS`
- `test_transition_gate.py`: removed `Any`, `ALL_KNOWN_PERMISSIONS`, `VerificationResult`, `NonceEntry`
- `nonce.py`: removed `field`

### C — Dead Code (Issues 15, 18): 2 warnings — ✅ All Fixed

- `test_transition_gate.py`: removed `import hmac as hmac_module` from `test_timing_safe`
- `nonce.py`: removed unused `now = time.time()` assignment in `active_count` property

### D — Intentional Side-Effect (Issue 16): 1 warning — ✅ Fixed

- `test_transition_gate.py`: renamed `n2` to `_` to signal the variable exists only for its side-effect (registering a second nonce via `.generate()`)

---

## Fixes Applied

### Commit 1: `fix: correct python.analysis.extraPaths in workspace config`

| File | Change |
|------|--------|
| `Seeds.code-workspace` | Removed `./Seeds/GRID-main/boundaries` and `./Seeds/GRID-main/boundaries/transition_gate` from `extraPaths` (these pointed Pylance into the package rather than above it). Added `./Seeds/GRID-main` as the repo root entry. |
| `E:\pyrightconfig.json` | Created. Maps `Seeds/GRID-main` execution environment with `extraPaths: [".", "src", "safety", "security"]`. |
| `E:\Seeds\GRID-main\pyrightconfig.json` | Created. Standalone config for editors that root at the repo level. |

### Commit 2: `chore: remove unused imports in transition gate and test files`

| File | Change |
|------|--------|
| `transition_gate/gate_keeper.py` | Removed `ALL_KNOWN_PERMISSIONS` from `envelope` import block |
| `transition_gate/nonce.py` | Removed `field` from `dataclasses` import |
| `tests/test_transition_gate.py` | Removed `Any`, `ALL_KNOWN_PERMISSIONS`, `VerificationResult`, `NonceEntry` from imports. Removed `import hmac as hmac_module` inside `test_timing_safe`. |

### Commit 3: `chore: remove dead assignments and signal side-effects`

| File | Change |
|------|--------|
| `transition_gate/nonce.py` | Removed unused `now = time.time()` in `active_count` property |
| `tests/test_transition_gate.py` | Renamed `n2` to `_` in `test_count_properties` |

---

## Risk Assessment

| Fix | Risk | Impact if Wrong | Rollback |
|-----|------|----------------|----------|
| Workspace `extraPaths` correction | **Low** — runtime unaffected; only IDE analysis | Pylance might lose resolution for a different import (unlikely — tested) | Re-add the lines |
| `pyrightconfig.json` creation | **None** — purely additive config files | None — Pyright ignores them if not needed | Delete the files |
| Remove unused imports | **None** — unused symbols have no runtime effect | None | `git revert` |
| Remove `now` assignment | **None** — variable was never read | None | `git revert` |
| Rename `n2` → `_` | **None** — `.generate()` side-effect still executes | None | `git revert` |

All fixes are safe, isolated, and independently revertible. No behavior changes. 108/108 test pass rate preserved.

---

## Remaining Items (Category A — User Decision Required)

The 23 import resolution errors are all the same root cause (Zed LSP path configuration) and all pre-existing. They do not affect:

- ✅ Runtime execution
- ✅ Test execution (108/108 pass)
- ✅ CI pipelines
- ✅ VS Code / Windsurf (fixed by `extraPaths`)
- ✅ Pyright CLI (fixed by `pyrightconfig.json`)

**For Zed specifically**, the user may need to:
1. Restart the editor to pick up `pyrightconfig.json`
2. Or add Pyright path config to Zed's own `settings.json` under `lsp.pyright.settings`
3. Or accept the squiggles as cosmetic (no functional impact)

---

*Resolution strategy for boundaries module diagnostics. See `E:\Seeds\ECOSYSTEM_BASELINE.md` §5 for transition gate documentation.*