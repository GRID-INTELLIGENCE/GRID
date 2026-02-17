# Cursor Agent: IDE Setup Gap Analysis Prompt

> **Purpose:** Systematically verify THE GRID IDE setup for gaps, inconsistencies, or missing configurations
> **Created:** 2026-02-12
> **Context:** Recent IDE standardization (ruff extension installation + 15 settings across VS Code/Cursor/Windsurf)

---

## Prompt for Cursor Agent

```
You are auditing THE GRID monorepo's IDE setup for completeness and consistency. This project enforces strict development discipline through automated tooling (ruff formatter/linter, pytest, mypy). Your task is to identify ANY gaps, inconsistencies, or missing configurations that could break the development workflow.

### Context

**Recent Changes (2026-02-12):**
- Installed `charliermarsh.ruff` VS Code extension (v2026.36.0)
- Standardized 15 IDE settings across VS Code, Cursor, Windsurf
- Created verification checklist: `docs/guides/IDE_SETUP_VERIFICATION.md`
- Verified ruff CLI working: `uv run ruff --version` → `ruff 0.15.0`

**Project Standards (from CLAUDE.md):**
- Python 3.13, line length 120, type hints required
- `uv` for package management (NOT pip)
- Ruff for formatting/linting (NOT black, NOT pylint)
- Async-first architecture (FastAPI, async SQLAlchemy)
- AI: local (Ollama + ChromaDB) and/or external providers (OpenAI, Anthropic) per `docs/PRINCIPLES.md` — open-source principles and freedom to think; access to AI providers and the open web is a core value; config does not restrict external API/network by default
- Zero tolerance: no `eval()`, no `exec()`, no `pickle`, no auth bypass

**Development Discipline (from .claude/rules/discipline.md):**
- Session Start Protocol: `uv run pytest -q --tb=short && uv run ruff check ...` MUST pass before ANY new code
- One commit, one concern (security fixes separate from features)
- Decision logging in `docs/decisions/DECISIONS.md`
- Complexity guard: reuse existing abstractions before creating new ones

---

### Verification Tasks

#### 1. Extension Coverage Gap Analysis

**Check:**
- Compare installed extensions (`code --list-extensions`) against workspace recommendations (`.vscode/extensions.json`)
- Identify missing extensions from the 18 recommended (Python, frontend, git, config, docs, devops)
- Verify no conflicting extensions installed (e.g., `ms-python.black-formatter`, `ms-python.isort`, `ms-python.vscode-pylint`)
- Check if `charliermarsh.ruff` is installed AND enabled (not just listed)

**Questions to answer:**
1. Which of the 18 recommended extensions are NOT installed?
2. Are there any installed extensions that conflict with project standards?
3. Is the ruff extension version compatible with ruff CLI version (0.15.0)?
4. Are there workspace-specific extension dependencies (e.g., Prettier depends on what config files)?

**Expected output:** List of missing/conflicting extensions with impact assessment

---

#### 2. Settings Inheritance Chain Verification

**Check:**
- Read all 3 settings levels: User (`C:\Users\irfan\AppData\Roaming\Code\User\settings.json`), Python Profile (`profiles\-8fe089f\settings.json`), Workspace (`E:\grid\.vscode\settings.json`)
- Verify settings precedence: Workspace > Profile > User
- Identify settings that are set at wrong level (e.g., project-specific in User, global in Workspace)
- Check for conflicting settings across levels (e.g., User sets `black`, Workspace sets `ruff`)

**Questions to answer:**
1. Are there settings conflicts between levels? (e.g., User says formatOnSave=false, Workspace says true)
2. Are cache exclusions (`.venv`, `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`) present at ALL levels?
3. Is `[python].defaultFormatter` set to `"charliermarsh.ruff"` at ALL levels? (Should be User + Profile + Workspace)
4. Are there settings in Workspace that should be in User (or vice versa)?
5. Are line ending settings consistent? (Should be `"\n"` LF, NOT `"\r\n"` CRLF)

**Expected output:** Settings conflict matrix with recommended fixes

---

#### 3. Cross-IDE Consistency Check

**Check:**
- Read Cursor settings (`C:\Users\irfan\AppData\Roaming\Cursor\User\settings.json`)
- Read Windsurf settings (`C:\Users\irfan\AppData\Roaming\Windsurf\User\settings.json`)
- Compare against VS Code user settings
- Identify drift in the 15 standardized settings (autoSave, trimTrailingWhitespace, formatOnSave, etc.)

**Questions to answer:**
1. Do Cursor and Windsurf have the same `[python].defaultFormatter` as VS Code?
2. Are cache exclusions identical across all 3 IDEs?
3. Are there settings in VS Code that are missing in Cursor/Windsurf?
4. Is `chat.agent.maxRequests = 35` present in Windsurf (recent sync addition)?
5. Are there IDE-specific settings that SHOULD differ? (e.g., terminal profiles, shell paths)

**Expected output:** IDE settings diff matrix showing inconsistencies

---

#### 4. Workspace Configuration Completeness

**Check:**
- `.vscode/extensions.json` — 18 recommendations present? `unwantedRecommendations` includes black/isort/pylint?
- `.vscode/settings.json` — Python paths correct for monorepo? Terminal env vars set? Formatters configured for Python/TypeScript/JSON/Markdown?
- `.vscode/tasks.json` — 14 tasks present? Default build task = "Daily: Verify the Wall"? All task commands use `uv run` prefix?
- `.vscode/mcp.json` — MCP servers configured (if applicable)?
- `.vscode/spell.json` — Custom dictionary present?

**Questions to answer:**
1. Are Python analysis paths correct? (Should include `./work/GRID/src`, `./safety`, `./security`, `./boundaries`)
2. Is `PYTHONPATH` terminal env var set correctly for Windows?
3. Are all tasks runnable? (Test by simulating: `uv run pytest -q`, `uv run ruff check ...`, etc.)
4. Is the default build task (Ctrl+Shift+B) set to "Daily: Verify the Wall"?
5. Are frontend formatter settings (Prettier for TypeScript/React) configured?
6. Are there tasks that reference non-existent files or paths?

**Expected output:** Workspace config gap report with missing/broken items

---

#### 5. Ruff Integration Functional Test

**Check:**
- Create a temporary Python file with intentional violations:
  - Formatting issues (extra spaces, missing spaces around operators)
  - Unused imports (should trigger F401)
  - Line too long (>120 chars, should trigger E501 if configured)
  - Import order violations (third-party before stdlib)
- Run `uv run ruff check <temp_file>` and verify it catches violations
- Run `uv run ruff check --fix <temp_file>` and verify auto-fixes work
- Check if ruff configuration exists (`.ruff.toml` or `pyproject.toml` with `[tool.ruff]`)

**Questions to answer:**
1. Does ruff CLI detect all expected violations?
2. Does `--fix` auto-correct fixable issues?
3. Is ruff configured with project-specific rules? (120-char line length, specific rule codes)
4. Does ruff respect exclude patterns (archive/, .venv/, etc.)?
5. Are there ruff rules that should be enabled but aren't? (e.g., UP042 for StrEnum migration)

**Expected output:** Ruff functional test results + configuration gap analysis

---

#### 6. Development Discipline Automation Test

**Check:**
- Verify `.vscode/tasks.json` "Daily: Verify the Wall" task exists and is set as default
- Test task command: `uv run pytest -q --tb=short && uv run ruff check work/ safety/ security/ boundaries/`
- Check if Makefile exists with `wall`, `test`, `lint`, `format`, `guard` targets
- Verify pre-commit hooks (if configured in `.git/hooks/` or `.pre-commit-config.yaml`)
- Check GitHub Actions workflows (if in `.github/workflows/`) for CI enforcement

**Questions to answer:**
1. Does Ctrl+Shift+B trigger the daily wall check? (Test: check task.json `"group": {"kind": "build", "isDefault": true}`)
2. Are all task commands using `uv run` prefix (NOT bare `python` or `pip`)?
3. Does the Makefile (if present) match .vscode/tasks.json commands?
4. Are there pre-commit hooks that duplicate or conflict with IDE automation?
5. Is CI/CD configured to enforce the same standards as local IDE? (Prevent "works on my machine")

**Expected output:** Discipline automation gap report with broken/missing automations

---

#### 7. Terminal & Environment Integration

**Check:**
- `.vscode/settings.json` terminal configuration:
  - `terminal.integrated.env.windows.PYTHONPATH` — includes all monorepo module paths?
  - `terminal.integrated.env.windows.PROJECT_ROOT` — set to `${workspaceFolder}`?
  - `terminal.integrated.env.windows.GRID_ENV` — set to `"development"`?
- Terminal profiles: PowerShell (default), WSL (optional)
- Shell integration disabled? (Can cause issues with some tools)

**Questions to answer:**
1. Is PYTHONPATH correctly formatted for Windows? (semicolon-separated, NOT colon)
2. Do terminal env vars load when opening a new terminal in VS Code?
3. Are there missing env vars required by THE GRID? (Check `.env.example` if present)
4. Is the default terminal profile correct for the OS (PowerShell on Windows)?
5. Are there conflicting env vars in system PATH vs. workspace terminal?

**Expected output:** Terminal integration gap report with env var issues

---

#### 8. File Watching & Performance Optimization

**Check:**
- `files.watcherExclude` — Does it exclude all cache/build folders?
- `search.exclude` — Does it exclude archive/ and build artifacts?
- `files.exclude` — Does it hide cache folders from file explorer?
- Compare exclusion patterns across all 3 (should be consistent for performance)

**Questions to answer:**
1. Are there folders being watched that shouldn't be? (archive/, .venv/, node_modules/, dist/, build/)
2. Are exclusion patterns identical in `watcherExclude`, `search.exclude`, and `files.exclude`?
3. Are there new cache folders created by tools that aren't excluded? (e.g., `.uv-cache`, `.ruff_cache`)
4. Would adding more exclusions improve IDE performance on this large monorepo?

**Expected output:** Performance optimization recommendations

---

#### 9. Type Checking & Language Server Configuration

**Check:**
- `python.analysis.typeCheckingMode` — set to `"basic"` or `"strict"`?
- `python.languageServer` — set to `"Pylance"`?
- `python.analysis.diagnosticMode` — set to `"workspace"` (for monorepo)?
- mypy configuration (`pyproject.toml` or `mypy.ini`) — does it match IDE settings?
- Are there type stub files (`.pyi`) that might be missing?

**Questions to answer:**
1. Is type checking enabled consistently across IDE and CLI (`uv run mypy ...`)?
2. Does Pylance respect the monorepo structure? (`python.analysis.extraPaths` configured?)
3. Are there mypy configuration mismatches between pyproject.toml and IDE settings?
4. Are third-party libraries with missing type stubs configured in mypy?
5. Is `disallow_untyped_defs = true` enforced (per backend.md rules)?

**Expected output:** Type checking configuration gap analysis

---

#### 10. Documentation & Onboarding Gaps

**Check:**
- Does `docs/guides/IDE_SETUP_VERIFICATION.md` cover all verification steps?
- Are there missing sections? (e.g., Cursor/Windsurf specific instructions)
- Is there a quick-start guide for new developers?
- Are troubleshooting sections complete?
- Are all referenced files/paths valid? (Check for broken links to config files)

**Questions to answer:**
1. Can a new developer follow the verification checklist without gaps?
2. Are there undocumented manual steps? (e.g., "reload VS Code", "restart terminal")
3. Are troubleshooting sections tested? (Do the fixes actually work?)
4. Is there a script to automate verification? (e.g., PowerShell script in the checklist)
5. Are success criteria measurable? (Checkboxes vs. vague "should work")

**Expected output:** Documentation completeness report

---

#### 11. Agent/Tool Policy (Dev Programs)

**Check:**
- `.cursor/devprograms/GLOBAL_CONFIG.md` — global `blocked_tools` and per-program overrides
- Confirm `external_api` and `network` are **not** in `blocked_tools` (access protected as core right per `docs/PRINCIPLES.md`)
- Verify alignment with open-source principles and freedom to think (access to ideas, AI providers, open web)

**Questions to answer:**
1. What is the current global and per-program `blocked_tools` state?
2. Does it match project values in `docs/PRINCIPLES.md` (no restriction of external API/network by default)?
3. Are any programs incorrectly restricting access (external_api/network in blocked_tools)?
4. Is `code_quality.formatting` in GLOBAL_CONFIG aligned with ruff-only standard?

**Expected output:** Dev programs tool policy summary; any mismatch with core values (freedom to think, open-source principles)

---

### Gap Prioritization Framework

For each gap found, classify by:

**Severity:**
- 🔴 **Critical:** Breaks core workflow (e.g., format-on-save doesn't work)
- 🟠 **High:** Causes inconsistency/confusion (e.g., Cursor uses different formatter than VS Code)
- 🟡 **Medium:** Reduces efficiency (e.g., missing GitLens extension)
- 🟢 **Low:** Nice-to-have (e.g., spell-checker not installed)

**Impact:**
- 🎯 **Blocking:** Prevents development discipline from working (e.g., linting disabled)
- ⚠️ **Degrading:** Works but unreliable (e.g., settings inheritance broken)
- 💡 **Enhancement:** Improves experience (e.g., additional exclusions for performance)

---

### Output Format

Provide a structured report:

```markdown
# IDE Setup Gap Analysis Report
Date: 2026-02-12

## Executive Summary
- Total gaps found: X
- Critical: X | High: X | Medium: X | Low: X
- Blocking issues: X | Degrading: X | Enhancements: X

## Gaps by Category

### 1. Extension Coverage
**Gap:** [Description]
**Severity:** [🔴/🟠/🟡/🟢]
**Impact:** [🎯/⚠️/💡]
**Fix:** [Specific action to resolve]
**Verification:** [How to confirm fix worked]

---

### 2. Settings Inheritance
[Same format...]

---

[Continue for all 11 categories...]

## Recommended Actions (Priority Order)

1. [🔴🎯] Fix critical blocking issue: ...
2. [🔴⚠️] Fix critical degrading issue: ...
3. [🟠🎯] Fix high-priority blocking issue: ...
[...]

## Verification Commands

```bash
# Run after fixes to confirm resolution
[List of commands to re-verify]
```

## Notes
- Cross-reference with: `docs/guides/IDE_SETUP_VERIFICATION.md`
- Align with: `.claude/rules/backend.md`, `.claude/rules/discipline.md`
- Test across: VS Code, Cursor, Windsurf
```

---

### Success Criteria

Your gap analysis is complete when:

1. ✅ All 11 verification categories checked
2. ✅ Every gap classified by severity + impact
3. ✅ Every gap has a specific fix + verification step
4. ✅ Gaps prioritized in actionable order
5. ✅ Report includes verification commands to run after fixes
6. ✅ Cross-references to existing docs (CLAUDE.md, rules/, verification checklist)

---

### Examples of Gaps You Might Find

**Extension Gap:**
- Missing: `eamodio.gitlens` (recommended for git blame/history)
- Fix: `code --install-extension eamodio.gitlens`
- Severity: 🟡 Medium | Impact: 💡 Enhancement

**Settings Conflict:**
- User settings: `editor.formatOnSave = false`
- Workspace settings: `[python].formatOnSave = true`
- Result: Unpredictable behavior (depends on precedence)
- Fix: Remove user-level setting, rely on workspace
- Severity: 🟠 High | Impact: ⚠️ Degrading

**Cross-IDE Drift:**
- VS Code: `[python].defaultFormatter = "charliermarsh.ruff"`
- Cursor: `[python].defaultFormatter = "ms-python.black-formatter"`
- Result: Different formatting when switching IDEs
- Fix: Update Cursor settings to match VS Code
- Severity: 🟠 High | Impact: ⚠️ Degrading

**Ruff Config Missing:**
- No `.ruff.toml` or `[tool.ruff]` in `pyproject.toml`
- Result: Ruff uses default config (may not match 120-char standard)
- Fix: Create ruff config with project-specific rules
- Severity: 🔴 Critical | Impact: 🎯 Blocking

**Task Broken:**
- Task command: `python -m pytest` (missing `uv run` prefix)
- Result: Uses wrong Python interpreter (system vs. venv)
- Fix: Update task.json to use `uv run pytest`
- Severity: 🔴 Critical | Impact: 🎯 Blocking

---

### Additional Context Files to Read

- `E:\grid\CLAUDE.md` — Project overview, tech stack, core principles
- `E:\grid\.claude\rules\backend.md` — Python standards
- `E:\grid\.claude\rules\frontend.md` — TypeScript/React standards
- `E:\grid\.claude\rules\discipline.md` — Development discipline workflow
- `E:\grid\.claude\rules\safety.md` — Security module rules
- `E:\grid\.vscode\extensions.json` — Workspace recommendations
- `E:\grid\.vscode\settings.json` — Workspace settings
- `E:\grid\.vscode\tasks.json` — Runnable tasks
- `E:\grid\pyproject.toml` — Python project config (if present, check for [tool.ruff], [tool.mypy])
- `E:\grid\docs\guides\IDE_SETUP_VERIFICATION.md` — Recent verification checklist

---

### Final Notes

- **Be exhaustive:** Check EVERY setting, EVERY extension, EVERY task
- **Be specific:** Don't say "settings might be wrong" — say exactly which setting and why
- **Be actionable:** Every gap needs a fix command (not just "configure X properly")
- **Be verifiable:** Every fix needs a verification step (not just "should work now")
- **Cross-reference:** Link gaps to CLAUDE.md rules/principles they violate

Good luck! Report back with the full gap analysis.
```

---

## How to Use This Prompt with Cursor Agent

1. **Copy the entire prompt** (from "You are auditing..." to "Good luck!")
2. **Paste into Cursor chat** (or create a new Cursor Agent task)
3. **Wait for comprehensive analysis** (agent will read all config files, test commands, etc.)
4. **Review gap report** — prioritize fixes by severity + impact
5. **Apply fixes** — use provided commands/actions
6. **Re-verify** — run verification commands after fixes
7. **Update IDE_SETUP_VERIFICATION.md** — document any new gaps found

---

## Expected Output

Cursor Agent should produce a ~2000-4000 word report covering:
- **Extension gaps** (missing or conflicting extensions)
- **Settings conflicts** (User vs. Profile vs. Workspace)
- **Cross-IDE drift** (VS Code vs. Cursor vs. Windsurf)
- **Workspace config issues** (broken tasks, incorrect paths, missing files)
- **Ruff integration problems** (config missing, rules not enforced)
- **Discipline automation failures** (wall check doesn't run, tasks broken)
- **Terminal/env issues** (PYTHONPATH wrong, env vars missing)
- **Performance optimizations** (exclusion patterns incomplete)
- **Type checking gaps** (mypy config mismatch, Pylance misconfigured)
- **Documentation holes** (verification checklist incomplete)
- **Agent/tool policy** (dev programs blocked_tools vs. project intent)

Each gap should have:
- Specific description
- Severity + impact classification
- Exact fix command
- Verification step

---

**Last Updated:** 2026-02-12
**For:** Cursor Agent systematic gap analysis
**Context:** Post-ruff-installation IDE setup verification
