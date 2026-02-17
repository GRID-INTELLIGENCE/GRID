---
name: ide-verification
description: Execute systematic IDE configuration audits following THE GRID's verification prompts. Generates structured gap analysis reports with severity and impact classifications. Use when verifying IDE setup, auditing configuration files, checking cross-IDE consistency, or when the user mentions IDE verification, gap analysis, or configuration audit.
---

# IDE Verification

## Quick Start

When verifying IDE configuration:

1. Identify target IDE (VS Code, Cursor, Windsurf, OpenCode, Antigravity)
2. Load corresponding verification prompt from `docs/guides/[IDE]_AGENT_VERIFICATION_PROMPT.md`
3. Execute 11 verification categories systematically
4. Generate gap analysis report with Executive Summary → Findings → Actions
5. Provide verification commands to run after fixes

## Workflow

### Step 1: Identify Target IDE

Determine which IDE to verify:
- **VS Code**: Primary reference implementation
- **Cursor**: Cursor IDE (built-in AI)
- **Windsurf**: Windsurf IDE (Cascade AI)
- **OpenCode**: OpenCode AI extension
- **Antigravity**: Antigravity IDE

### Step 2: Load Verification Prompt

Read the appropriate verification prompt from `docs/guides/`:
- VS Code: `VSCODE_AGENT_VERIFICATION_PROMPT.md`
- Cursor: `CURSOR_AGENT_VERIFICATION_PROMPT.md`
- Windsurf: `WINDSURF_AGENT_VERIFICATION_PROMPT.md`
- OpenCode: `OPENCODE_AGENT_VERIFICATION_PROMPT.md`
- Antigravity: `ANTIGRAVITY_AGENT_VERIFICATION_PROMPT.md`

For overview, see `docs/guides/MULTI_IDE_VERIFICATION_INDEX.md`.

### Step 3: Execute Verification Categories

Systematically check all 10 categories:

1. **Extension Coverage Gap Analysis**
   - Compare installed extensions against workspace recommendations
   - Identify missing/conflicting extensions
   - Verify ruff extension installed and enabled

2. **Settings Inheritance Chain Verification**
   - Check User → Profile → Workspace settings precedence
   - Identify conflicts across levels
   - Verify ruff formatter set at all levels

3. **Cross-IDE Consistency Check**
   - Compare settings across VS Code, Cursor, Windsurf
   - Identify drift in 15 standardized settings
   - Verify `chat.agent.maxRequests = 35` in Windsurf

4. **Workspace Configuration Completeness**
   - Check `.vscode/extensions.json` (18 recommendations)
   - Verify `.vscode/settings.json` (Python paths, formatters)
   - Test `.vscode/tasks.json` (14 tasks, default build task)

5. **Ruff Integration Functional Test**
   - Create test file with violations
   - Run `uv run ruff check` and verify detection
   - Run `uv run ruff check --fix` and verify auto-fix
   - Check ruff config (`.ruff.toml` or `pyproject.toml`)

6. **Development Discipline Automation Test**
   - Verify "Daily: Verify the Wall" task exists and is default
   - Test task command: `uv run pytest -q --tb=short && uv run ruff check work/ safety/ security/ boundaries/`
   - Check Makefile targets (if present)
   - Verify pre-commit hooks

7. **Terminal & Environment Integration**
   - Check `PYTHONPATH` terminal env var (Windows: semicolon-separated)
   - Verify `PROJECT_ROOT`, `GRID_ENV` set correctly
   - Test terminal profiles (PowerShell default on Windows)

8. **File Watching & Performance Optimization**
   - Check `files.watcherExclude` (cache folders excluded)
   - Verify `search.exclude` matches `files.exclude`
   - Check archive/ folder excluded (10GB+)

9. **Type Checking & Language Server Configuration**
   - Verify `python.analysis.typeCheckingMode` set
   - Check `python.languageServer` = `"Pylance"`
   - Verify mypy config matches IDE settings

10. **Documentation & Onboarding Gaps**
    - Check `docs/guides/IDE_SETUP_VERIFICATION.md` completeness
    - Verify troubleshooting sections tested
    - Check for broken links to config files

11. **Agent/Tool Policy (Dev Programs)**
    - Check `.cursor/devprograms/GLOBAL_CONFIG.md` for global and per-program `blocked_tools`
    - Confirm `external_api`/`network` are not restricted (access protected as core right per `docs/PRINCIPLES.md`)
    - Verify alignment with open-source principles and freedom to think

### Step 4: Generate Gap Analysis Report

Format report with:

```markdown
# [IDE Name] Gap Analysis Report
Date: YYYY-MM-DD

## Executive Summary
- Total gaps found: X
- Critical: X | High: X | Medium: X | Low: X
- Blocking issues: X | Degrading: X | Enhancements: X

## Gaps by Category

### 1. Extension Coverage
**Gap:** [Description]
**Severity:** [🔴/🟠/🟡/🟢]
**Impact:** [🎯/⚠️/💡]
**Fix:** [Specific action]
**Verification:** [How to confirm fix worked]

[Continue for all categories...]

## Recommended Actions (Priority Order)

1. [🔴🎯] Fix critical blocking issue: ...
2. [🔴⚠️] Fix critical degrading issue: ...
3. [🟠🎯] Fix high-priority blocking issue: ...
[...]

## Verification Commands

```bash
# Run after fixes to confirm resolution
[Commands to re-verify]
```
```

### Step 5: Provide Verification Commands

Include specific commands to verify fixes:
- `code --list-extensions` (VS Code)
- `uv run ruff --version`
- `uv run pytest -q --tb=short`
- Settings file paths for manual verification

## Gap Prioritization

Classify each gap by:

**Severity:**
- 🔴 **Critical:** Breaks core workflow (format-on-save doesn't work)
- 🟠 **High:** Causes inconsistency/confusion (different formatter than VS Code)
- 🟡 **Medium:** Reduces efficiency (missing GitLens extension)
- 🟢 **Low:** Nice-to-have (spell-checker not installed)

**Impact:**
- 🎯 **Blocking:** Prevents development discipline from working
- ⚠️ **Degrading:** Works but unreliable (settings inheritance broken)
- 💡 **Enhancement:** Improves experience (additional exclusions)

## Examples

### Example Gap: Missing Ruff Extension

**Gap:** Ruff extension not installed
**Severity:** 🔴 Critical
**Impact:** 🎯 Blocking
**Fix:** `code --install-extension charliermarsh.ruff`
**Verification:** Check `code --list-extensions | grep ruff` returns `charliermarsh.ruff`

### Example Gap: Settings Conflict

**Gap:** User settings set `editor.formatOnSave = false`, Workspace sets `[python].formatOnSave = true`
**Severity:** 🟠 High
**Impact:** ⚠️ Degrading
**Fix:** Remove user-level `editor.formatOnSave`, rely on workspace setting
**Verification:** Open Python file, save, verify formatting applied

### Example Gap: Cross-IDE Drift

**Gap:** VS Code uses ruff, Cursor uses black formatter
**Severity:** 🟠 High
**Impact:** ⚠️ Degrading
**Fix:** Update Cursor settings: `[python].defaultFormatter = "charliermarsh.ruff"`
**Verification:** Format Python file in VS Code, open in Cursor, verify no changes

## Standards Reference

Cross-reference gaps with THE GRID standards:

- **Core values and rights:** `docs/PRINCIPLES.md` (open-source principles, freedom to think; external API/network access protected)
- **Python 3.13:** `.claude/rules/backend.md`
- **Development Discipline:** `.claude/rules/discipline.md`
- **Frontend:** `.claude/rules/frontend.md`
- **Safety:** `.claude/rules/safety.md`
- **IDE Config Standards:** `.claude/rules/ide-config-standards.md`

Key standards to verify:
- Ruff as formatter (NOT black, NOT isort)
- 120-character line length
- LF line endings (`\n`)
- Cache exclusions (`.venv`, `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`)
- Tasks use `uv run` prefix (NOT bare `python` or `pip`)

## Additional Resources

- Master verification hub: `docs/guides/MULTI_IDE_VERIFICATION_INDEX.md`
- Post-setup checklist: `docs/guides/IDE_SETUP_VERIFICATION.md`
- Cursor-specific prompt: `docs/guides/CURSOR_AGENT_VERIFICATION_PROMPT.md`
- Project standards: `CLAUDE.md` (if exists)
