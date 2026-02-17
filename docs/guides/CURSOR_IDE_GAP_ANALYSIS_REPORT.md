# Cursor IDE Gap Analysis Report

**Date:** 2026-02-13
**Target IDE:** Cursor
**Reference:** VS Code (multi-IDE standards)
**Executed via:** IDE Verification Skill

---

## Executive Summary

- **Total gaps found:** 14
- **Critical:** 2 | **High:** 4 | **Medium:** 5 | **Low:** 3
- **Blocking issues:** 2 | **Degrading:** 4 | **Enhancements:** 8

**Primary concerns:** Daily wall check is not bound to Ctrl+Shift+B (build hotkey), Cursor/Windsurf user settings lack Python formatter fallback, Makefile still uses black instead of ruff format, and extension coverage is incomplete.

---

## Gaps by Category

### 1. Extension Coverage

**Gap:** 10 of 18 recommended extensions not installed; Cursor/VS Code `code --list-extensions` shows 8 extensions. Ruff is installed âœ“.

**Installed:** `charliermarsh.ruff`, `ms-python.python`, `ms-python.vscode-pylance`, `ms-python.debugpy`, `ms-python.vscode-python-envs`, `anthropic.claude-code`, `github.copilot-chat`, `bierner.markdown-mermaid`

**Missing (recommended):** `njpwerner.autodocstring`, `ms-vscode.vscode-typescript-next`, `esbenp.prettier-vscode`, `dbaeumer.vscode-eslint`, `bradlc.vscode-tailwindcss`, `eamodio.gitlens`, `mhutchie.git-graph`, `tamasfe.even-better-toml`, `redhat.vscode-yaml`, `mechatroner.rainbow-csv`, `streetsidesoftware.code-spell-checker`, `gruntfuggly.todo-tree`, `christian-kohler.path-intellisense`, `ms-vscode-remote.remote-wsl`, `ms-azuretools.vscode-docker`

**Severity:** ðŸŸ¡ Medium
**Impact:** ðŸ’¡ Enhancement

**Fix:** Install high-value extensions first:

```bash
code --install-extension esbenp.prettier-vscode
code --install-extension eamodio.gitlens
code --install-extension tamasfe.even-better-toml
code --install-extension streetsidesoftware.code-spell-checker
```

**Verification:** `code --list-extensions | Select-String "prettier|gitlens|even-better|spell-checker"`

---

### 2. Settings Inheritance Chain

**Gap:** Cursor User settings (`C:\Users\irfan\AppData\Roaming\Cursor\User\settings.json`) lack `[python].defaultFormatter`. Workspace settings provide it, but opening a non-workspace Python file would not use ruff.

**Severity:** ðŸŸ  High
**Impact:** âš ï¸ Degrading

**Fix:** Add to Cursor User settings:

```json
"[python]": {
  "editor.defaultFormatter": "charliermarsh.ruff",
  "editor.formatOnSave": true
}
```

**Verification:** Open a standalone `.py` file outside workspace â†’ save â†’ verify ruff formatting applied.

---

### 3. Cross-IDE Consistency Check

**Gap 3a:** Cursor and Windsurf User settings both lack `[python].defaultFormatter`. VS Code user settings also lack it (relies on workspace). For consistency, all three should have ruff as fallback at user level.

**Gap 3b:** Windsurf has `chat.agent.maxRequests = 35` âœ“. Cursor has it âœ“. Both match.

**Gap 3c:** `files.exclude` is consistent (`.venv`, `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `*.pyc`, `.DS_Store`) across Cursor, Windsurf, and VS Code.

**Severity:** ðŸŸ  High (3a), ðŸŸ¢ Low (3b/3c)
**Impact:** âš ï¸ Degrading

**Fix:** Add `[python].defaultFormatter` to Cursor and Windsurf User settings as in section 2.

---

### 4. Workspace Configuration Completeness

**Gap 4a:** Default build task (Ctrl+Shift+B) is NOT "Daily: Verify the Wall". The task has `"group": {"kind": "test", "isDefault": true}`. Build hotkey runs `group.kind: "build"` tasks. Only "Lint: Ruff Check + Fix" has `group: "build"`.

**Severity:** ðŸ”´ Critical
**Impact:** ðŸŽ¯ Blocking

**Fix:** Change "Daily: Verify the Wall" task in `.vscode/tasks.json`:

```json
"group": {"kind": "build", "isDefault": true}
```

And ensure "Lint: Ruff Check + Fix" is not default build, or add a dedicated build task that runs the wall check.

**Verification:** Ctrl+Shift+B â†’ must run `uv run pytest -q --tb=short && uv run ruff check ...`

**Gap 4b:** `python.languageServer` = `"None"` in workspace. Cursor uses `cursorpyright`; workspace has `cursorpyright.analysis.*` settings. This is correct for Cursor.

**Gap 4c:** Tasks use `uv run` prefix âœ“. Python paths, PYTHONPATH, PROJECT_ROOT, GRID_ENV are configured âœ“.

---

### 5. Ruff Integration

**Gap:** Ruff config in `pyproject.toml` is present with `line-length = 120`, `target-version = "py313"`, excludes. E501 (line length) is in `extend-ignore` â€” line length enforced by `ruff format` only, not `ruff check`.

**Severity:** ðŸŸ¢ Low
**Impact:** ðŸ’¡ Enhancement

**Fix:** Optional â€” if you want E501 enforced by check, remove it from `extend-ignore`. Ruff format already enforces 120 chars.

**Verification:** `uv run ruff check work/ safety/ security/ boundaries/` and `uv run ruff format --check work/ safety/ security/ boundaries/`

---

### 6. Development Discipline Automation

**Gap 6a:** "Daily: Verify the Wall" is default _test_ task, not default _build_ task â€” see Gap 4a.

**Gap 6b:** Makefile `format` target uses `uv run black` + `uv run ruff check --fix`. Project standard is Ruff for formatting (NOT black). Makefile contradicts `.claude/rules/backend.md` and IDE config.

**Severity:** ðŸ”´ Critical (6a), ðŸŸ  High (6b)
**Impact:** ðŸŽ¯ Blocking (6a), âš ï¸ Degrading (6b)

**Fix (6b):** Update root `Makefile` format target:

```makefile
format: ## Auto-format code (ruff format + ruff check fix)
	@echo "$(BLUE)Formatting...$(NC)"
	uv run ruff format work/ boundaries/ safety/ scripts/
	uv run ruff check --fix work/ boundaries/ safety/ scripts/
	@echo "$(GREEN)Formatted.$(NC)"
```

**Verification:** `make format` â†’ no black; only ruff format + ruff check --fix.

**Gap 6c:** Pre-commit hooks in `work/GRID/.pre-commit-config.yaml` use ruff âœ“. Root workspace has no `.pre-commit-config.yaml` at repo root.

---

### 7. Terminal & Environment Integration

**Gap:** None found. Workspace settings have:

- `PYTHONPATH` (semicolon-separated for Windows) âœ“
- `PROJECT_ROOT`, `GRID_ENV` âœ“
- PowerShell default âœ“

**Verification:** New terminal â†’ `echo $env:PYTHONPATH` (PowerShell)

---

### 8. File Watching & Performance Optimization

**Gap:** `search.exclude`, `files.watcherExclude`, `files.exclude` are comprehensive. Archive, `.venv`, caches, `node_modules` excluded âœ“. `.uv-cache` in search/watcher exclude âœ“.

**Severity:** ðŸŸ¢ Low (no critical gaps)
**Impact:** ðŸ’¡ Enhancement

**Fix:** Optional â€” add `**/artifacts/**` and `**/logs/**` to `files.watcherExclude` if those dirs are large (they are in search.exclude).

---

### 9. Type Checking & Language Server Configuration

**Gap 9a:** Workspace sets `python.languageServer = "None"`. Cursor uses CursorPyright; workspace has `cursorpyright.analysis.typeCheckingMode = "basic"` and `cursorpyright.analysis.extraPaths` configured âœ“.

**Gap 9b:** `pyproject.toml` mypy config has `disallow_untyped_defs = true` âœ“.

**Severity:** ðŸŸ¢ Low
**Impact:** ðŸ’¡ Enhancement

**Fix:** Ensure Pylance/CursorPyright is selected in Cursor if type checking is desired. Workspace explicitly sets language server to None â€” verify Cursor overrides with cursorpyright for Python.

---

### 10. Documentation & Onboarding Gaps

**Gap 10a:** `IDE_SETUP_VERIFICATION.md` references "Format: Black + Ruff" task; actual task label is "Format: Ruff". Doc is slightly stale.

**Gap 10b:** `bierner.markdown-mermaid` is checked in IDE_SETUP_VERIFICATION but not in `.vscode/extensions.json` recommendations.

**Gap 10c:** Checklist says "default build task (Ctrl+Shift+B) triggers daily wall check" but current config does not â€” see Gap 4a.

**Severity:** ðŸŸ¡ Medium
**Impact:** âš ï¸ Degrading

**Fix:** Update `IDE_SETUP_VERIFICATION.md` to reflect actual task labels and fix default build task (Gap 4a). Add `bierner.markdown-mermaid` to `extensions.json` if desired.

---

## Recommended Actions (Priority Order)

1. **[ðŸ”´ðŸŽ¯]** Fix default build task: Set "Daily: Verify the Wall" to `group: {"kind": "build", "isDefault": true}` in `.vscode/tasks.json`
2. **[ðŸ”´âš ï¸]** Fix Makefile format target: Replace black with `ruff format` in root `Makefile`
3. **[ðŸŸ ðŸŽ¯]** Add `[python].defaultFormatter` to Cursor User settings for non-workspace Python files
4. **[ðŸŸ âš ï¸]** Add `[python].defaultFormatter` to Windsurf User settings
5. **[ðŸŸ âš ï¸]** Update `IDE_SETUP_VERIFICATION.md`: correct task labels and default build behavior
6. **[ðŸŸ¡ðŸ’¡]** Install high-value extensions: Prettier, GitLens, Even Better TOML, Spell Checker
7. **[ðŸŸ¢ðŸ’¡]** Add `bierner.markdown-mermaid` to `extensions.json` if using Mermaid
8. **[ðŸŸ¢ðŸ’¡]** Optional: add root `.pre-commit-config.yaml` for workspace-level pre-commit

---

## Verification Commands

```powershell
# Run from workspace root (E:\grid)

# 1. Verify Ruff
uv run ruff --version
uv run ruff check work/ safety/ security/ boundaries/ --quiet

# 2. Verify extensions
code --list-extensions | Select-String "ruff|prettier|gitlens"

# 3. Verify default build task
# Manual: Ctrl+Shift+B â†’ must run pytest + ruff check

# 4. Verify Makefile format (after fix)
make format
# Expected: ruff format + ruff check --fix only, no black

# 5. Verify Cursor settings
Get-Content "$env:APPDATA\Cursor\User\settings.json" | Select-String "defaultFormatter"
```

---

## Notes

- Cross-reference: `docs/guides/IDE_SETUP_VERIFICATION.md`
- Align with: `.claude/rules/backend.md`, `.claude/rules/discipline.md`
- Multi-IDE index: `docs/guides/MULTI_IDE_VERIFICATION_INDEX.md`

---

## Final Recommendation

**âœ… Configure** â€” Cursor is usable with the workspace; fix the default build task and Makefile to align with development discipline. Add user-level Python formatter in Cursor/Windsurf for consistency across all Python files.

---

**Last Updated:** 2026-02-13
**Report Generated By:** IDE Verification Skill (config-reviewer)
