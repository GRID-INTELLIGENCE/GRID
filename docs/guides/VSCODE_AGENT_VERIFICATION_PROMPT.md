# VS Code Agent: IDE Setup Gap Analysis Prompt

> **Purpose:** Comprehensive audit of VS Code configuration for THE GRID (reference implementation)
> **Created:** 2026-02-12
> **Context:** VS Code is the primary IDE — this is the master configuration that Cursor/Windsurf/etc. should match

---

## Prompt for VS Code Agent (GitHub Copilot Chat)

```
You are performing a comprehensive audit of VS Code configuration for THE GRID monorepo. This is the REFERENCE IMPLEMENTATION — all other IDEs (Cursor, Windsurf, OpenCode, Antigravity) should match this configuration. Your task is to verify completeness, correctness, and identify any gaps or improvements.

### Context

**Project:** THE GRID — Local-first AI codebase analysis framework
**Tech Stack:** Python 3.13 (backend), React 19 + TypeScript (frontend), Ollama + ChromaDB (AI), FastAPI, Celery, Redis
**Standards:** ruff formatter/linter, 120-char lines, `uv` package manager, pytest, mypy, ESLint, Prettier
**Development Discipline:** "Session Start Protocol" — tests + lint MUST pass before ANY new code

**Recent Changes:**
- ✅ Installed `charliermarsh.ruff` extension (v2026.36.0)
- ✅ Configured 15 core settings (user + Python profile)
- ✅ Created `docs/guides/IDE_SETUP_VERIFICATION.md`
- ✅ Verified ruff CLI working (`ruff 0.15.0`)

---

### Verification Tasks

#### 1. Extension Coverage & Conflicts

**Check:** Compare installed vs. recommended extensions

**Workspace Recommendations:** `.vscode/extensions.json` (18 extensions)

**Currently Installed:**
```bash
code --list-extensions
# Known: charliermarsh.ruff, ms-python.python, ms-python.vscode-pylance,
#        ms-python.debugpy, ms-python.vscode-python-envs, github.copilot-chat, bierner.markdown-mermaid
```

**Questions:**
1. Which of the 18 recommended extensions are NOT installed? (Missing count: ~11)
2. Are there unwanted extensions installed? (Check against `unwantedRecommendations`: black-formatter, isort, pylint)
3. Are extension versions up-to-date? (Run `code --list-extensions --show-versions`)
4. Are there extension conflicts? (e.g., multiple formatters for Python)
5. Should the missing extensions be installed, or are they truly optional?

**Expected Output:** Extension gap matrix with installation priority

---

#### 2. Settings Triadic Verification (User → Profile → Workspace)

**Check:** Settings inheritance across all 3 levels

**Level 1 — User Settings:**
`C:\Users\irfan\AppData\Roaming\Code\User\settings.json`

**Level 2 — Python Profile:**
`C:\Users\irfan\AppData\Roaming\Code\User\profiles\-8fe089f\settings.json`

**Level 3 — Workspace:**
`E:\grid\.vscode\settings.json`

**15 Core Settings to Verify:**
1. `files.autoSave` = `"onFocusChange"`
2. `files.trimTrailingWhitespace` = `true`
3. `files.insertFinalNewline` = `true`
4. `files.eol` = `"\n"` (LF)
5. `editor.formatOnSave` = `true`
6. `editor.formatOnSaveMode` = `"file"`
7. `editor.minimap.enabled` = `false`
8. `editor.bracketPairColorization.enabled` = `true`
9. `editor.stickyScroll.enabled` = `true`
10. `[python].defaultFormatter` = `"charliermarsh.ruff"`
11. `[python].tabSize` = `4`
12. `files.exclude` (`.venv`, `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`)
13. `git.enableSmartCommit` = `true`
14. `git.autofetch` = `false`
15. `chat.agent.maxRequests` = `35`

**Questions:**
- Are all 15 settings present at the correct level?
- Are there conflicts between levels? (User says X, Workspace says Y)
- Are there settings set at the wrong level? (Project-specific in User, global in Workspace)
- Is the effective value (after precedence) correct?

**Expected Output:** Settings inheritance matrix showing User/Profile/Workspace values + effective value

---

#### 3. Workspace Configuration Deep Dive

**Check:** `.vscode/*` files completeness and correctness

**Files to audit:**
1. `.vscode/extensions.json` — 18 recommendations + 3 unwanted
2. `.vscode/settings.json` — Python paths, formatters, terminal env vars, exclusions
3. `.vscode/tasks.json` — 14 tasks (pytest, ruff, mypy, frontend, etc.)
4. `.vscode/mcp.json` — MCP servers (if configured)
5. `.vscode/spell.json` — Custom dictionary (fastapi, pydantic, chromadb, etc.)

**Questions for each file:**

**extensions.json:**
- Are all 18 recommendations still relevant?
- Should any be added? (e.g., Docker extension for future containerization)
- Are `unwantedRecommendations` still correct? (black-formatter, isort, pylint)

**settings.json:**
- `python.analysis.extraPaths` correct for monorepo? (./work/GRID/src, ./safety, ./security, ./boundaries)
- `terminal.integrated.env.windows.PYTHONPATH` formatted correctly? (semicolon-separated)
- Formatters configured for all languages? (Python: ruff, TypeScript: prettier, JSON: prettier, Markdown: none)
- Search/watcher exclusions complete? (archive/, .venv/, node_modules/, dist/, build/, etc.)

**tasks.json:**
- All 14 tasks runnable? (Test by running each)
- Default build task set? ("Daily: Verify the Wall" should be Ctrl+Shift+B)
- All task commands use `uv run` prefix? (NOT bare `python` or `pip`)
- Task paths correct? (Relative to workspace root)

**mcp.json:**
- MCP servers configured? (If yes, which ones?)
- Do they integrate with THE GRID's local-only AI principle?

**spell.json:**
- Custom dictionary complete? (fastapi, pydantic, structlog, chromadb, ollama, etc.)
- Missing common terms? (Check for red squiggles in code)

**Expected Output:** Workspace config audit report with gaps/improvements

---

#### 4. Python Ecosystem Integration

**Check:** Python tooling configuration (Pylance, pytest, mypy, ruff)

**Pylance (Language Server):**
- `python.languageServer` = `"Pylance"`
- `python.analysis.typeCheckingMode` = `"basic"` (or `"strict"`?)
- `python.analysis.diagnosticMode` = `"workspace"` (for monorepo)
- `python.analysis.autoImportCompletions` = `true`
- `python.analysis.extraPaths` = monorepo modules

**pytest:**
- `python.testing.pytestEnabled` = `true`
- `python.testing.pytestArgs` correct? (work/GRID/tests, safety/tests, boundaries/tests, -q, --tb=short)
- Does Test Explorer show tests? (Click Testing icon in sidebar)

**mypy:**
- Is there a mypy configuration? (pyproject.toml or mypy.ini)
- Does it match IDE settings?
- `disallow_untyped_defs = true` enforced? (per backend.md)

**ruff:**
- CLI version: `ruff 0.15.0`
- Extension version: `charliermarsh.ruff v2026.36.0`
- Config file: `.ruff.toml` or `[tool.ruff]` in `pyproject.toml`?
- Line length: 120 (matches project standard?)
- Rules enabled: E, F, B, I, W, UP (per backend.md)

**Questions:**
- Are Python tools versions aligned? (Extension version vs. CLI version)
- Is type checking enforced consistently? (IDE + CLI)
- Are pytest tests discoverable in VS Code Test Explorer?
- Does ruff have a config file, or using defaults?
- Are import sorting rules consistent? (isort config in ruff vs. separate)

**Expected Output:** Python ecosystem integration report

---

#### 5. Frontend Ecosystem Integration

**Check:** TypeScript, React, ESLint, Prettier configuration

**TypeScript:**
- `[typescript].defaultFormatter` = `"esbenp.prettier-vscode"`
- `[typescriptreact].defaultFormatter` = `"esbenp.prettier-vscode"`
- TypeScript version: Check `frontend/package.json`
- Does TypeScript language server work? (IntelliSense, type errors)

**ESLint:**
- `eslint.workingDirectories` = `["./frontend"]`
- `editor.codeActionsOnSave` includes `"source.fixAll.eslint": "explicit"`
- ESLint config: `frontend/.eslintrc.json` or `frontend/eslint.config.js`?
- Does ESLint auto-fix on save?

**Prettier:**
- Prettier config: `frontend/.prettierrc` or `frontend/prettier.config.js`?
- Does Prettier format on save for .ts, .tsx, .json files?

**JSON:**
- `[json].defaultFormatter` = `"esbenp.prettier-vscode"`
- `[jsonc].defaultFormatter` = `"esbenp.prettier-vscode"`

**Markdown:**
- `[markdown].wordWrap` = `"on"`
- `[markdown].rulers` = `[]` (no ruler for Markdown)

**Questions:**
- Are frontend formatters/linters configured correctly?
- Do they auto-fix on save?
- Are there conflicts between Prettier and ESLint?
- Is the frontend/ directory excluded from Python tooling?

**Expected Output:** Frontend ecosystem integration report

---

#### 6. Terminal & Environment Variables

**Check:** Terminal configuration for THE GRID workflow

**Settings:**
- `terminal.integrated.cwd` = `"${workspaceFolder}"`
- `terminal.integrated.defaultProfile.windows` = `"PowerShell"`
- `terminal.integrated.profiles.windows` includes PowerShell + WSL
- `terminal.integrated.env.windows` sets PYTHONPATH, PROJECT_ROOT, GRID_ENV

**Questions:**
- Does PYTHONPATH load correctly when opening terminal? (Test: `echo $env:PYTHONPATH`)
- Is it formatted correctly for Windows? (semicolon-separated, NOT colon)
- Does PROJECT_ROOT resolve to `E:\grid`?
- Is GRID_ENV set to `"development"`?
- Can you run `uv`, `make`, `rg`, `ruff` commands from terminal?

**Shell Integration:**
- `terminal.integrated.shellIntegration.enabled` = `false` (current setting)
- `terminal.integrated.shellIntegration.decorationsEnabled` = `"never"`
- Why disabled? (Check if intentional or legacy setting)

**Expected Output:** Terminal environment validation report

---

#### 7. Performance & File Watching

**Check:** Exclusions for performance optimization

**Three exclusion types:**
1. `files.exclude` — Hides from file explorer
2. `search.exclude` — Excludes from search
3. `files.watcherExclude` — Excludes from file watching (performance)

**Patterns to verify (should be in all 3):**
- `**/.venv`, `**/venv`
- `**/node_modules`
- `**/__pycache__`, `**/*.pyc`
- `**/.pytest_cache`, `**/.mypy_cache`, `**/.ruff_cache`
- `**/.cache`, `**/.ipynb_checkpoints`
- `**/dist`, `**/build`
- `**/analysis_outputs`, `**/artifacts`, `**/logs`
- `**/.uv-cache`
- `**/archive/**` (10GB+ historical files)

**Questions:**
- Are exclusion patterns identical across all 3 settings?
- Are there new cache folders created by tools that aren't excluded?
- Is `archive/` excluded? (Critical for performance — 10GB+)
- Are exclusions in Cursor/Windsurf consistent with VS Code?

**Expected Output:** Performance optimization report + missing exclusions

---

#### 8. Development Discipline Automation

**Check:** "Session Start Protocol" automation

**Daily Wall Check:**
- Task name: "Daily: Verify the Wall"
- Command: `uv run pytest -q --tb=short && uv run ruff check work/ safety/ security/ boundaries/`
- Is default build task? (`"isDefault": true`)
- Keyboard shortcut: Ctrl+Shift+B

**Other Discipline Tasks:**
- "Lint: Ruff Check + Fix" — `uv run ruff check --fix ...`
- "Format: Black + Ruff" — `uv run black ... && uv run ruff check --fix ...`
- "Typecheck: mypy" — `uv run mypy work/GRID/src/grid`
- "Guard: Security Invariants" — `rg "eval\(|exec\(|pickle\."` (should return 0)

**Questions:**
- Does Ctrl+Shift+B trigger the daily wall check?
- Do all tasks run successfully? (Test each one)
- Are task commands using `uv run` prefix? (NOT bare `python`)
- Are there tasks that should be added? (e.g., "Test: Frontend", "Build: Frontend")
- Is there a Makefile that duplicates these tasks?

**Expected Output:** Discipline automation audit + task improvements

---

#### 9. Git Integration & Version Control

**Check:** Git settings alignment with development discipline

**Settings:**
- `git.autofetch` = `false` (manual control)
- `git.confirmSync` = `false` (streamlined workflow)
- `git.enableSmartCommit` = `true` (auto-stage on commit)
- `git.autoRepositoryDetection` = `false` (per current config)

**Questions:**
- Why is `git.autoRepositoryDetection` disabled?
- Should it be enabled for the monorepo?
- Are there git hooks configured? (`.git/hooks/` or `.pre-commit-config.yaml`)
- Do git hooks enforce the same standards as IDE? (tests + lint)

**GitLens Extension (if installed):**
- Does GitLens help with "why does this code exist?" debugging?
- Is it configured for monorepo?

**Expected Output:** Git integration report + recommendations

---

#### 10. Documentation Completeness

**Check:** `docs/guides/IDE_SETUP_VERIFICATION.md` accuracy

**Questions:**
- Does the verification checklist cover all settings verified above?
- Are there gaps in documentation? (Missing manual tests, unclear instructions)
- Are troubleshooting sections tested and accurate?
- Are verification commands tested and working?
- Is the PowerShell verification script functional?

**Expected Output:** Documentation gap report + recommended updates

---

### Gap Prioritization

**Severity:**
- 🔴 **Critical:** Breaks core workflow (e.g., default build task not set)
- 🟠 **High:** Causes inefficiency (e.g., missing extensions reduce productivity)
- 🟡 **Medium:** Suboptimal (e.g., exclusion patterns incomplete)
- 🟢 **Low:** Nice-to-have (e.g., GitLens not installed)

**Impact:**
- 🎯 **Blocking:** Prevents development discipline enforcement
- ⚠️ **Degrading:** Works but unreliable
- 💡 **Enhancement:** Improves experience

---

### Output Format

```markdown
# VS Code Configuration Audit Report
Date: 2026-02-12

## Executive Summary
- Extensions: X/18 installed (Y missing)
- Settings: X/15 core settings verified (Y conflicts)
- Tasks: X/14 tasks working (Y broken)
- Critical gaps: X
- High-priority gaps: X

## Detailed Findings

### 1. Extension Coverage
**Installed:** 7/18 (39%)
**Missing:** [list 11 missing extensions with priority]
**Conflicts:** [list any conflicting extensions]
**Recommendation:** [Install all / Install critical only]

### 2. Settings Inheritance
**User Level:** [X/15 correct]
**Python Profile:** [X/15 correct]
**Workspace Level:** [configuration status]
**Conflicts:** [list any conflicts]
**Effective Values:** [all correct: Yes/No]

### 3. Workspace Config
**extensions.json:** [gaps/improvements]
**settings.json:** [gaps/improvements]
**tasks.json:** [X/14 working, Y broken]
**mcp.json:** [configured: Yes/No]
**spell.json:** [complete: Yes/No]

### 4. Python Ecosystem
**Pylance:** [configured correctly: Yes/No]
**pytest:** [Test Explorer working: Yes/No]
**mypy:** [config aligned: Yes/No]
**ruff:** [config file exists: Yes/No, line length: 120]

### 5. Frontend Ecosystem
**TypeScript:** [formatter: prettier, working: Yes/No]
**ESLint:** [auto-fix on save: Yes/No]
**Prettier:** [config file: path or missing]

### 6. Terminal & Environment
**PYTHONPATH:** [loads correctly: Yes/No]
**Shell Integration:** [disabled intentionally: Yes/Unknown]
**Commands work:** [uv, make, rg, ruff all functional: Yes/No]

### 7. Performance
**Exclusions complete:** [Yes/No]
**archive/ excluded:** [Yes/No]
**New cache folders:** [list if found]

### 8. Discipline Automation
**Daily wall check:** [Ctrl+Shift+B works: Yes/No]
**All tasks runnable:** [Yes/No]
**uv run prefix:** [all tasks use it: Yes/No]

### 9. Git Integration
**Settings correct:** [Yes/No]
**Hooks configured:** [Yes/No]
**GitLens installed:** [Yes/No]

### 10. Documentation
**Verification checklist accurate:** [Yes/No]
**Gaps found:** [list]

## Recommended Actions (Priority Order)

1. [🔴🎯] Install missing critical extensions: charliermarsh.ruff (DONE), [list others]
2. [🔴🎯] Fix default build task if broken
3. [🟠💡] Install productivity extensions: GitLens, spell-checker, etc.
4. [🟡💡] Create ruff config file with 120-char line length
5. [🟢💡] Update documentation with new findings
[...]

## Verification Commands

```bash
# Extensions
code --list-extensions --show-versions

# Settings effective values
code --folder-uri E:\grid --open-settings-ui

# Tasks
# Ctrl+Shift+P → Tasks: Run Task → verify all 14 listed

# Ruff config
uv run ruff check --show-settings

# Terminal env vars
# Open VS Code terminal:
echo $env:PYTHONPATH
echo $env:PROJECT_ROOT
echo $env:GRID_ENV

# Daily wall check
# Ctrl+Shift+B → verify pytest + ruff run
```

## Notes
- VS Code is the REFERENCE IMPLEMENTATION for THE GRID
- Cursor, Windsurf, OpenCode, Antigravity should match this config
- Any changes to VS Code settings should propagate to other IDEs
```

---

### Success Criteria

✅ All 18 recommended extensions reviewed (install critical ones)
✅ 15 core settings verified across User/Profile/Workspace
✅ All 14 tasks runnable
✅ Python ecosystem fully integrated (Pylance, pytest, mypy, ruff)
✅ Frontend ecosystem configured (TypeScript, ESLint, Prettier)
✅ Terminal environment variables load correctly
✅ Performance exclusions complete
✅ Daily wall check works (Ctrl+Shift+B)
✅ Documentation updated with findings

---

### Context Files

- `.vscode/extensions.json` — 18 recommendations
- `.vscode/settings.json` — Workspace config
- `.vscode/tasks.json` — 14 tasks
- `C:\Users\irfan\AppData\Roaming\Code\User\settings.json` — User settings
- `C:\Users\irfan\AppData\Roaming\Code\User\profiles\-8fe089f\settings.json` — Python profile
- `docs/guides/IDE_SETUP_VERIFICATION.md` — Recent checklist
- `.claude/rules/backend.md`, `.claude/rules/discipline.md` — Standards

---

**This is the MASTER audit** — all other IDE audits should reference this one.
Run this comprehensive audit and provide the full gap analysis report.
```
