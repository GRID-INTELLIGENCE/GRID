# Project Config Consolidation Report

**Date:** 2026-02-24
**Scope:** Root `.gitignore`, `pyproject.toml`, `.gitattributes`; cross-dir configs (frontend, landing, safety, boundaries).

---

## Executive Summary

| Category              | Status | Notes |
|-----------------------|--------|--------|
| .gitignore vs pyproject | Aligned | No conflicting include/ignore; hatch packages vs ignore consistent. |
| .gitattributes        | Aligned | LF enforced; binaries and lock merge strategy defined. |
| Multi-pyproject       | OK     | Root depends on `safety` (path); `boundaries` standalone. |
| Frontend/landing     | OK     | Local .gitignore additive; root covers node_modules, dist, .env. |
| Known issues          | 3 low  | See below. |

---

## 1. .gitignore ↔ pyproject.toml

### 1.1 Build / packaging

- **Root pyproject** `[tool.hatch.build.targets.wheel]` ships `src/grid`, `src/application`, `src/cognitive`, `src/tools` and excludes Arena, frontend, EUFLE, etc.
- **.gitignore** does not ignore those shipped paths; it ignores `build/`, `dist/`, `*.egg-info/`, `lib/` (with `!frontend/src/lib/`).
- **Conclusion:** No mismatch. Shipped source is tracked; build artifacts and Python `lib/` are ignored; `frontend/src/lib/` is correctly tracked (exception).

### 1.2 Lock files

- **.gitignore:** `**/uv.lock` then `!uv.lock` → only **root** `uv.lock` is tracked.
- **safety/uv.lock** exists and is **ignored** (matches `**/uv.lock`). Root depends on `grid-safety = { path = "safety" }`, so a single root lock is the intended layout.
- **Conclusion:** Intentional; no change unless you want to track safety’s lock for standalone publishes.

### 1.3 Test / debug

- **pyproject** `testpaths = ["tests", "safety/tests", "boundaries/tests"]`; `norecursedirs` includes `Arena`, `frontend`, `scripts`, etc. (no recursion into those dirs for test discovery).
- Tests under **tests/** that import **Arena** (e.g. `test_adsr_sustain_fix.py`) are still collected from `tests/`; only recursion into `Arena/` is skipped.
- **.gitignore:** `*.log`, `**/debug_output/`, `artifacts/debug_logs/` → session debug logs (e.g. `debug-*.log`) are covered by `*.log`.
- **Conclusion:** Aligned.

### 1.4 Scripts

- **.gitignore:** `scripts/*.py` with explicit `!scripts/...` for tracked scripts (e.g. `track_commit.py`, `validate_venv.py`, `validate_security.py`, etc.).
- **pyproject** `norecursedirs` includes `scripts` → pytest does not discover tests inside `scripts/`.
- **Conclusion:** Aligned. When adding new **tracked** scripts, add a corresponding `!scripts/<name>.py` (or equivalent).

---

## 2. .gitattributes

- **Default:** `* text=auto eol=lf` → LF normalized.
- **Overrides:** `.bat`/`.cmd`/`.ps1` → `eol=crlf`; binaries (images, DBs, `.pem`, etc.) → `binary`.
- **Merge:** `package-lock.json` and `uv.lock` → `merge=theirs`; `CHANGELOG.md` → `merge=union`.
- **Conclusion:** Consistent with root .gitignore and pyproject; no conflicts identified.

---

## 3. Cross-directory consistency

### 3.1 Frontend (`frontend/.gitignore`)

- Local rules: `node_modules/`, `dist/`, `release/`, `*.env`, `.DS_Store`, Storybook artifacts.
- Root already ignores `node_modules/`, `dist/`, `.env*`, `.DS_Store`.
- **Conclusion:** Additive; no conflict. Frontend `src/lib/` is explicitly un-ignored at root (`!frontend/src/lib/`).

### 3.2 Landing (`landing/.gitignore`)

- Local: `node_modules/`, `.DS_Store`, `*.log`, `.env`, `.env.local`.
- **Conclusion:** Additive; aligned with root.

### 3.3 Safety (`safety/pyproject.toml`)

- `requires-python = ">=3.13,<3.14"` matches root.
- Root: `grid-safety = { path = "safety" }`; single root `uv.lock` covers the workspace.
- **Conclusion:** Aligned.

### 3.4 Boundaries (`boundaries/pyproject.toml`)

- Standalone package; not in root `dependencies`. Ruff `target-version = "py313"`, line-length 120.
- **Conclusion:** OK; no conflict with root.

---

## 4. Known issues / consolidation notes

### 4.1 (Low) .cursor/ fully ignored

- **.gitignore:** `.cursor/` → entire `.cursor/` (including `.cursor/skills/`, `.cursor/rules/`) is untracked.
- **Impact:** Team-wide Cursor rules/skills (e.g. `ide-verification`, `plan-to-reference`) are not in version control unless committed before adding to .gitignore or the rule is relaxed.
- **Options:** (a) Keep as-is (user-local only); (b) Add `!.cursor/skills/` and `!.cursor/rules/` to track shared agent skills/rules.

### 4.2 (Low) .vscode partially ignored

- **.gitignore:** `.vscode/` then `!.vscode/extensions.json` and `!.vscode/tasks.json`; `.vscode/settings.json` and `launch.json` ignored.
- **Impact:** Matches common practice (recommend extensions/tasks, keep settings/launch local). IDE verification skill references `.vscode/`; ensure extensions.json and tasks.json are kept in sync with docs.

### 4.3 (Low) Debug log pattern

- Session debug logs (`debug-<session>.log`) are covered by `*.log`. If you want an explicit pattern for agent debug logs, consider adding `debug-*.log` under a “Debug” section for clarity (optional).

---

## 5. Verification commands (post-change)

Run from repo root:

```powershell
# Ensure no tracked file is accidentally ignored by global patterns (sample)
git check-ignore -v frontend/src/lib/grid-client.ts
# Expect: no output (file not ignored), or rule shown if you expect it

# Ruff and pytest (from pyproject)
uv run ruff check src --statistics
uv run pytest tests/ -q --tb=short -x -n 0 --ignore=tests/scratch
```

---

## 6. References

- Root: `.gitignore`, `pyproject.toml`, `.gitattributes`
- Frontend: `frontend/.gitignore`
- Landing: `landing/.gitignore`
- Packages: `safety/pyproject.toml`, `boundaries/pyproject.toml`
- IDE verification: `.cursor/skills/ide-verification/SKILL.md`, `docs/guides/MULTI_IDE_VERIFICATION_INDEX.md`
- Web: pyproject.toml / .gitignore best practices (Poetry/setuptools include vs ignore; uv/hatch single lock and path deps).

---

---

## 7. Execution summary (2026-02-24)

- **`git check-ignore -v frontend/src/lib/grid-client.ts`:** Exit 1 (not ignored) → `frontend/src/lib/` is correctly tracked.
- **`uv run ruff check src --statistics`:** 8 existing Ruff findings (S607, S311); unrelated to .gitignore/pyproject alignment.
- **Report path:** `docs/CONFIG_CONSOLIDATION_REPORT.md`

---

## 8. Implementation changes (2026-02-24 follow-up)

### 8.1 Cursor shared configurations

Added exceptions to `.gitignore` for team-shared Cursor configurations:

```
!.cursor/skills/
!.cursor/rules/
!.cursor/agents/
```

**Rationale:** Enables version control for:
- Skills: `ide-verification`, `plan-to-reference`
- Rules: `ai-safety-user-wellbeing`, `external-api-policy`
- Agents: `ai-safety-reviewer`

**Verification:**
```powershell
git check-ignore -v .cursor/skills/ide-verification/SKILL.md
# Should exit 1 (not ignored) after change
```

### 8.2 Debug log pattern

Added explicit `debug-*.log` pattern in LOGS section for clarity (already covered by `*.log`).

### 8.3 .vscode verification

Confirmed `.vscode/settings.json` is tracked in git (committed before ignore rule). This is intentional for team consistency. Only `extensions.json` and `tasks.json` are explicitly un-ignored at root level.

*Generated from project file evaluation and cross-dir comparison.*
