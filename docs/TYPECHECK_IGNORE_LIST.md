# Type Checker: Notable Culprits & Focused Ignore List

**Purpose:** Paths and diagnostic patterns that dominate type-check noise. Use this to extend `pyrightconfig.json` excludes or to prioritize fixes.  
**Sources:** [ISSUES_BREAKDOWN.md](ISSUES_BREAKDOWN.md), [TOP_10_ISSUES_ANALYSIS.md](TOP_10_ISSUES_ANALYSIS.md), [TYPE_CHECKER_GUIDE.md](../.github/TYPE_CHECKER_GUIDE.md).

---

## 1. Notable Culprits (by path)

### Already excluded (root `pyrightconfig.json`)

| Path pattern | Reason |
|--------------|--------|
| `**/research/snapshots` | Snapshot copies of broken files (simple_calc, manim_circle, etc.) |
| `**/archive` | Old/archived code (Arena, datakit, etc.); not active codebase |
| `**/SEGA/simple_calc.py` | Corrupted/malformed file (141 issues, syntax + undefined vars) |

### Strong candidates for exclude (focused ignore list)

| Path pattern | Issue count (approx) | Reason |
|--------------|----------------------|--------|
| `**/EUFLE/lightofthe7/SEGA/**` | 141 | Same broken simple_calc / SEGA tree outside archive |
| `**/datakit/visualizations/animated/manim_*.py` | 70 each | Manim not installed; optional viz dependency |
| `**/EUFLE/llama.cpp/**` | 200+ | Vendor/upstream (converters, gguf-py, tools); not owned code |
| `**/EUFLE/studio/transformer_debug.py` | 63 | Optional torch/matplotlib/psutil; debug script |
| `**/EUFLE/tests/test_flow_diffusion.py` | 63 | Outdated test API / abstract usage; fix or exclude |
| `**/grid/tests/test_overwatch_resonance_arena.py` | 58 | Outdated config/API expectations |
| `**/grid/tests/api/test_property_based_auth.py` | 53 | Missing hypothesis; optional member access throughout |
| `**/EUFLE/lightofthe7/datakit/**` | 70+ | Duplicate of archive datakit (manim, explorer) |
| `**/archive/misc/datakit/**` | (in archive) | Already excluded via `**/archive` |

### Fix, don’t ignore (active app code)

| Path | Issues | Action |
|------|--------|--------|
| `grid/src/application/mothership/routers/navigation.py` | 44 | Fix types / optional access |
| `grid/src/application/mothership/main.py` | 42 | Fix types / optional access |
| `grid/src/tools/rag/indexer.py` | 28 | Fix types |
| `grid/src/application/mothership/services/payment/stripe_gateway.py` | 23 | Fix types |

---

## 2. Persistent bug patterns (by diagnostic code)

From ISSUES_BREAKDOWN (approximate counts):

| Diagnostic | Count | Pattern | Ignore? | Prefer |
|------------|-------|---------|--------|--------|
| reportMissingImports | 917 | Optional/vendor deps (manim, torch, pytest, hypothesis) | Only in excluded/vendor paths | Conditional import or exclude path |
| reportUndefinedVariable | 708 | Often from missing imports or corrupted file | No | Fix import or exclude file |
| reportAttributeAccessIssue | 554 | Wrong/missing attributes on types | No | Fix types or add stubs |
| reportOptionalMemberAccess | 520 | Access on possibly None | No | Add `is not None` guards (see TYPE_CHECKER_GUIDE) |
| reportArgumentType | 325 | Wrong argument types | No | Fix signatures / overloads |
| unknown | 147 | Syntax/parsing (e.g. simple_calc) | Exclude file | Exclude path |
| reportCallIssue | 110 | Invalid calls | No | Fix API usage |
| reportMissingModuleSource | 101 | Module has no py.typed / source | Per-path or suppress in vendor | Exclude vendor or add stubs |
| reportAssignmentType | 90 | Wrong assignment type | No | Fix types |
| reportUnusedExpression | 86 | Unused expr (often in bad file) | Exclude file | Exclude path |
| reportUnsupportedDunderAll | 79 | __all__ type | Low priority | Fix or suppress in legacy |
| reportReturnType | 69 | Wrong return type | No | Fix return types |
| reportInvalidTypeForm | 45 | Variable in type expr (e.g. transformer_debug) | In optional/debug only | Fix or exclude file |

**Summary:** Do **not** add project-wide diagnostic suppressions for the big ones (reportOptionalMemberAccess, reportArgumentType, reportMissingImports). Reduce noise by **path excludes** (vendor, optional deps, broken/outdated files) and fix patterns in active code (see [.github/TYPE_CHECKER_GUIDE.md](../.github/TYPE_CHECKER_GUIDE.md)).

---

## 3. Focused ignore list (actionable)

### A. Suggested `pyrightconfig.json` exclude additions

Add these to the existing `exclude` list in root `pyrightconfig.json` to get a focused ignore list without hiding active code:

```json
"exclude": [
  "**/research/snapshots",
  "**/archive",
  "**/node_modules",
  "**/__pycache__",
  "**/.venv",
  "**/venv",
  "**/site-packages",
  "**/build",
  "**/.git",
  "**/SEGA/simple_calc.py",
  "**/EUFLE/llama.cpp",
  "**/datakit/visualizations/animated/manim_*.py",
  "**/EUFLE/studio/transformer_debug.py",
  "**/EUFLE/lightofthe7/SEGA",
  "**/EUFLE/lightofthe7/datakit"
]
```

- **EUFLE/llama.cpp** — vendor; 200+ issues.
- **manim_*.py** — optional Manim dependency.
- **transformer_debug.py** — optional torch/psutil/matplotlib debug script.
- **EUFLE/lightofthe7/SEGA** and **EUFLE/lightofthe7/datakit** — duplicate/broken trees (same as archive/snapshots).

Outdated tests (`test_flow_diffusion.py`, `test_overwatch_resonance_arena.py`, `test_property_based_auth.py`) can be excluded only if you do not plan to fix or run them soon; otherwise fix or exclude per test dir.

### B. Optional per-file suppressions (use sparingly)

- **reportMissingImports** in a file that truly uses optional deps:
  - Prefer: `try/except ImportError` and `X = None  # type: ignore` (see TYPE_CHECKER_GUIDE).
  - If the whole file is optional: exclude the path instead of suppressing globally.
- **reportMissingModuleSource** in vendor/third-party code: exclude the vendor path rather than turning off the rule everywhere.

### C. What not to add to the ignore list

- No project-wide disable of: `reportOptionalMemberAccess`, `reportArgumentType`, `reportReturnType`, `reportAssignmentType`, `reportCallIssue`, `reportAttributeAccessIssue`.
- Do not exclude: `grid/src`, `grid/tests` (whole tree) — only specific broken or vendor files/dirs.

---

## 4. Quick reference

| Goal | Action |
|------|--------|
| Fewer noise from vendor/optional code | Add path excludes from §3.A to `pyrightconfig.json`. |
| Fewer noise from broken/duplicate trees | Exclude `**/EUFLE/lightofthe7/SEGA`, `**/EUFLE/lightofthe7/datakit`, and optionally specific test files. |
| Fix most impact in active code | Fix `navigation.py`, `main.py`, `indexer.py`, `stripe_gateway.py` using TYPE_CHECKER_GUIDE. |
| Optional deps (torch, manim, pytest, hypothesis) | Use conditional imports and type: ignore for the fallback, or exclude those files. |
| Re-check after changes | Run `pyright --outputjson` and compare with ISSUES_BREAKDOWN / TOP_10. |

---

*Last updated: 2026-02-07.*
