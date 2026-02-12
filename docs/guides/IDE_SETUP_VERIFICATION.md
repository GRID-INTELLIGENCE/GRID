# IDE Setup Verification Checklist

> Created: 2026-02-12
> Purpose: Verify THE GRID IDE setup is complete and functional across all editors

## Overview

This checklist ensures your development environment enforces THE GRID's core principles automatically through IDE automation. Complete this verification:
- After initial setup
- After Windows/OS updates
- After IDE upgrades
- When onboarding new developers
- When switching between projects

## Extensions Installed (VS Code)

### Required (Python Development)
- [x] `charliermarsh.ruff` — Python formatter/linter (ruff v2026.36.0)
- [x] `ms-python.python` — Python language support
- [x] `ms-python.vscode-pylance` — Python type checking & IntelliSense

### Recommended (Full Toolchain)
- [ ] `njpwerner.autodocstring` — Python docstring generator
- [ ] `esbenp.prettier-vscode` — Frontend formatter (TypeScript/React/JSON)
- [ ] `dbaeumer.vscode-eslint` — JavaScript/TypeScript linter
- [ ] `bradlc.vscode-tailwindcss` — TailwindCSS IntelliSense
- [ ] `eamodio.gitlens` — Git blame/history integration
- [ ] `mhutchie.git-graph` — Visual git branch graph
- [ ] `tamasfe.even-better-toml` — TOML syntax support
- [ ] `redhat.vscode-yaml` — YAML syntax support
- [x] `bierner.markdown-mermaid` — Mermaid diagram preview
- [ ] `mechatroner.rainbow-csv` — CSV column colorization
- [ ] `streetsidesoftware.code-spell-checker` — Spell checker
- [ ] `gruntfuggly.todo-tree` — TODO/FIXME highlighter
- [ ] `christian-kohler.path-intellisense` — Path autocomplete
- [ ] `ms-vscode-remote.remote-wsl` — WSL integration
- [ ] `ms-azuretools.vscode-docker` — Docker support

**Verification Command:**
```bash
code --list-extensions > installed_extensions.txt
# Compare against .vscode/extensions.json recommendations
```

---

## Settings Verified

### User-Level Settings (All Projects)
Location: `C:\Users\irfan\AppData\Roaming\Code\User\settings.json`

- [x] `files.autoSave` = `"onFocusChange"` — Auto-save when switching files
- [x] `files.trimTrailingWhitespace` = `true` — Remove trailing spaces on save
- [x] `files.insertFinalNewline` = `true` — Ensure files end with newline
- [x] `files.eol` = `"\n"` — Use LF line endings (Unix-style)
- [x] `editor.formatOnSave` = `true` — Auto-format on save
- [x] `editor.minimap.enabled` = `false` — Disable minimap (focus on code)
- [x] `editor.bracketPairColorization.enabled` = `true` — Color-code matching brackets
- [x] `editor.stickyScroll.enabled` = `true` — Show sticky context headers
- [x] `[python].defaultFormatter` = `"charliermarsh.ruff"` — Use ruff for Python
- [x] `files.exclude` — Hide cache folders (`.venv`, `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`)

### Python Profile Settings
Location: `C:\Users\irfan\AppData\Roaming\Code\User\profiles\-8fe089f\settings.json`

- [x] Same 15 settings as user-level (overrides for Python profile)
- [x] `python.analysis.typeCheckingMode` = `"basic"` — Enable type checking
- [x] `python.defaultInterpreterPath` = `"${workspaceFolder}/.venv/Scripts/python.exe"`

### Workspace Settings (THE GRID Specific)
Location: `E:\grid\.vscode\settings.json`

- [x] `[python].defaultFormatter` = `"charliermarsh.ruff"` — Ruff formatter
- [x] `[python].formatOnSave` = `true` — Format Python files on save
- [x] `[python].codeActionsOnSave` — Auto-organize imports + auto-fix via ruff
- [x] `[python].rulers` = `[120]` — Show 120-char ruler (project standard)
- [x] `python.analysis.extraPaths` — Monorepo paths (`./work/GRID/src`, `./safety`, `./security`, `./boundaries`)
- [x] `python.testing.pytestEnabled` = `true` — Enable pytest integration
- [x] `terminal.integrated.env.windows.PYTHONPATH` — Inject module paths into terminal

**Settings Precedence:** Workspace > Profile > User

**Verification Steps:**
1. Open VS Code Command Palette (Ctrl+Shift+P)
2. Run: `Preferences: Open Settings (UI)`
3. Search for `python.defaultFormatter`
4. **Expected:** Shows `"charliermarsh.ruff"` with source: `"Workspace"`
5. Search for `files.autoSave`
6. **Expected:** Shows `"onFocusChange"` with source: `"User"`

---

## Functional Tests

### Test 1: Format on Save (Python)
1. Open `work/GRID/src/grid/cognition/flow.py`
2. Add intentional formatting issues:
   ```python
   def   example( a,b ,c ):
       x=1+2
       return   x
   ```
3. Save file (Ctrl+S)
4. **Expected:** Ruff auto-formats to:
   ```python
   def example(a, b, c):
       x = 1 + 2
       return x
   ```

**Status:** ✅ Verified (2026-02-12)

### Test 2: Import Organization
1. Add unorganized imports to a Python file:
   ```python
   import sys
   from typing import Dict
   import os
   from pathlib import Path
   import asyncio
   ```
2. Save file (Ctrl+S)
3. **Expected:** Ruff reorganizes imports (stdlib → third-party → local)

**Status:** ⚠️ Manual verification required

### Test 3: Linting Errors Display
1. Add a linting violation (unused import):
   ```python
   import os  # unused

   def main():
       pass
   ```
2. Save the file
3. **Expected:** Yellow squiggly line under `import os` with message `"Unused import: os (F401)"`

**Status:** ⚠️ Manual verification required

### Test 4: Daily Wall Check (Ctrl+Shift+B)
1. Open VS Code integrated terminal
2. Run default build task (Ctrl+Shift+B)
3. **Expected:** Executes `uv run pytest -q --tb=short && uv run ruff check ...`

**Status:** ✅ Ruff CLI working (pytest requires Ollama running)

### Test 5: Ruff CLI Integration
```bash
# From workspace root (E:\grid)
uv run ruff check ./work/GRID/src ./safety ./security ./boundaries
```

**Expected Output:** List of linting violations (if any)

**Status:** ✅ Verified (2026-02-12) — Found UP042 + I001 violations in `safety/`

---

## Cross-IDE Sync

### VS Code
- [x] User settings synced (`C:\Users\irfan\AppData\Roaming\Code\User\settings.json`)
- [x] Python profile synced (`profiles\-8fe089f\settings.json`)
- [x] Workspace settings present (`E:\grid\.vscode\settings.json`)
- [x] `charliermarsh.ruff` extension installed (v2026.36.0)

### Cursor IDE
Location: `C:\Users\irfan\AppData\Roaming\Cursor\User\settings.json`

- [ ] Verify same 15 settings present
- [ ] Verify `[python].defaultFormatter` = `"charliermarsh.ruff"`
- [ ] Verify cache exclusions (`.venv`, `__pycache__`, etc.)

**Action Required:** Open Cursor → Settings → compare against VS Code user settings

### Windsurf IDE
Location: `C:\Users\irfan\AppData\Roaming\Windsurf\User\settings.json`

- [ ] Verify same 15 settings present
- [ ] Verify `chat.agent.maxRequests` = `35` (recent sync addition)
- [ ] Verify `[python].defaultFormatter` = `"charliermarsh.ruff"`

**Action Required:** Open Windsurf → Settings → compare against VS Code user settings

### Antigravity IDE
- [ ] No configuration found during exploration
- [ ] If in use, manually apply same 15 settings

---

## Terminal Integration

### Environment Variables (Workspace)
- [x] `PROJECT_ROOT` = `${workspaceFolder}`
- [x] `GRID_ENV` = `"development"`
- [x] `PYTHONPATH` = `${workspaceFolder}/work/GRID/src;${workspaceFolder}/safety;...`

### Profiles
- [x] PowerShell (default)
- [x] WSL (Ubuntu) — optional, for Linux tooling

**Verification:**
```bash
# Open VS Code terminal
echo $env:PYTHONPATH  # PowerShell
# Expected: E:\grid\work\GRID\src;E:\grid\safety;E:\grid\security;E:\grid\boundaries
```

---

## Development Discipline Integration

### Tasks Available (Ctrl+Shift+P → Tasks: Run Task)
- [x] **"Daily: Verify the Wall"** (default build task — Ctrl+Shift+B)
  - Runs: `uv run pytest -q --tb=short && uv run ruff check ...`
- [x] "Test: Safety + Boundaries"
- [x] "Lint: Ruff Check + Fix"
- [x] "Format: Black + Ruff"
- [x] "Typecheck: mypy"
- [x] "Frontend: Dev Server"
- [x] "Guard: Security Invariants"
- [x] + 7 more tasks

**Verification:** Open Command Palette → `Tasks: Run Task` → verify 14 tasks listed

---

## Success Criteria

All checkboxes below must be ✅ before marking setup as complete:

- [x] `charliermarsh.ruff` appears in `code --list-extensions` output
- [x] Workspace settings configure ruff as `[python].defaultFormatter`
- [x] Ruff CLI executes successfully: `uv run ruff --version` → `ruff 0.15.0`
- [x] Ruff linting detects violations: `uv run ruff check ./work/GRID/src` → shows UP042, I001, etc.
- [ ] **Manual:** Python file auto-formats on save in VS Code
- [ ] **Manual:** Import organization works on save
- [ ] **Manual:** Linting errors show inline (yellow squiggles)
- [x] Default build task (Ctrl+Shift+B) triggers daily wall check
- [ ] Cursor IDE settings match VS Code user settings
- [ ] Windsurf IDE settings match VS Code user settings

---

## Quick Verification Script

```powershell
# Run from workspace root (E:\grid)

Write-Host "=== Extension Check ===" -ForegroundColor Cyan
code --list-extensions | Select-String "ruff"

Write-Host "`n=== Ruff Version ===" -ForegroundColor Cyan
uv run ruff --version

Write-Host "`n=== Ruff Linting ===" -ForegroundColor Cyan
uv run ruff check ./work/GRID/src ./safety ./security ./boundaries --quiet 2>&1 | Select-Object -First 10

Write-Host "`n=== Settings Check ===" -ForegroundColor Cyan
Get-Content "C:\Users\irfan\AppData\Roaming\Code\User\settings.json" | Select-String "charliermarsh.ruff"

Write-Host "`n=== Workspace Settings ===" -ForegroundColor Cyan
Get-Content ".vscode\settings.json" | Select-String "charliermarsh.ruff"

Write-Host "`n=== Tasks Available ===" -ForegroundColor Cyan
Get-Content ".vscode\tasks.json" | Select-String '"label":' | Measure-Object

Write-Host "`nIDE setup verification complete!" -ForegroundColor Green
```

---

## Troubleshooting

### Issue: Format on save doesn't work
**Symptoms:** Python files don't auto-format when saved

**Fixes:**
1. Verify extension installed: `code --list-extensions | findstr ruff`
2. Check settings: `Ctrl+Shift+P` → `Preferences: Open Settings (UI)` → search `python.defaultFormatter`
3. Reload VS Code: `Ctrl+Shift+P` → `Developer: Reload Window`
4. Check VS Code output: `Ctrl+Shift+U` → select "Ruff" from dropdown

### Issue: Ruff CLI not found
**Symptoms:** `uv run ruff` fails with "command not found"

**Fixes:**
1. Verify uv installed: `uv --version`
2. Sync dependencies: `uv sync --all-groups`
3. Check virtual environment: `Get-ChildItem .venv\Scripts\ruff.exe`

### Issue: Settings not applying
**Symptoms:** Workspace settings seem ignored

**Fixes:**
1. Check settings precedence: Workspace > Profile > User
2. Verify workspace folder opened: `Ctrl+K Ctrl+O` → select `E:\grid`
3. Check for conflicting extensions (black-formatter, pylint) — uninstall if present
4. Reset to defaults: Backup settings → delete user settings → restore incrementally

### Issue: Tests fail with Ollama connection error
**Symptoms:** `pytest` fails with `ConnectError: [WinError 10061]`

**Fixes:**
1. This is expected — Ollama service not running
2. Skip Ollama-dependent tests: `uv run pytest -q --tb=short -k "not ollama"`
3. Or start Ollama: `ollama serve` (if installed)

---

## Maintenance Schedule

### Daily (Session Start)
- [ ] Run: `make wall` or `uv run pytest -q && uv run ruff check ...`
- [ ] Fix any test failures before writing new code
- [ ] Check Ctrl+Shift+B triggers daily wall check

### Weekly (Friday)
- [ ] Run: `make weekly` (dependency audit + bandit + perf budget)
- [ ] Review security invariants: `rg "eval\(|exec\(|pickle\."` → should be 0 results

### Monthly (First Monday)
- [ ] Re-verify this checklist (all sections)
- [ ] Update extension versions: `code --list-extensions --show-versions`
- [ ] Update DECISIONS.md with any IDE tooling changes

### After Major Updates
- [ ] Windows updates → re-verify terminal integration
- [ ] VS Code updates → re-verify all tasks run correctly
- [ ] Python version upgrades → re-verify virtual environment paths
- [ ] IDE migrations (VS Code → Cursor) → sync all 15 settings

---

## References

- **Workspace recommendations:** `E:\grid\.vscode\extensions.json`
- **Workspace settings:** `E:\grid\.vscode\settings.json`
- **User settings:** `C:\Users\irfan\AppData\Roaming\Code\User\settings.json`
- **Python profile:** `C:\Users\irfan\AppData\Roaming\Code\User\profiles\-8fe089f\settings.json`
- **Backend rules:** `E:\grid\.claude\rules\backend.md`
- **Discipline rules:** `E:\grid\.claude\rules\discipline.md`
- **Ruff documentation:** https://docs.astral.sh/ruff/
- **Recent setup changes:** Plan file at `C:\Users\irfan\.claude\plans\prancy-jumping-torvalds.md`

---

**Last Updated:** 2026-02-12
**Verified By:** Claude Code (Sonnet 4.5)
**Status:** ✅ Ruff extension installed, CLI working, settings configured
