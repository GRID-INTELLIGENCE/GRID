# Windsurf Agent: IDE Setup Gap Analysis Prompt

> **Purpose:** Verify Windsurf IDE configuration matches THE GRID's development standards
> **Created:** 2026-02-12
> **Context:** Cross-IDE standardization (VS Code, Cursor, Windsurf) — ensure consistency

---

## Prompt for Windsurf Agent (Cascade)

```
You are auditing Windsurf IDE configuration for THE GRID monorepo to ensure it matches the standardized setup applied to VS Code and Cursor. Your goal is to identify configuration drift, missing settings, or Windsurf-specific issues that could break development workflow consistency.

### Context

**Project:** THE GRID — Local-first AI codebase analysis (Python + React + AI Safety)
**Standards:** Python 3.13, ruff formatter/linter, 120-char lines, `uv` package manager
**Recent Standardization:** 15 IDE settings applied across VS Code/Cursor/Windsurf
**Expected Settings:** autoSave, trimTrailingWhitespace, formatOnSave, ruff as Python formatter, cache exclusions

**Windsurf-Specific Context:**
- Settings location: `C:\Users\irfan\AppData\Roaming\Windsurf\User\settings.json`
- Agent: Cascade (Windsurf's AI pair programmer)
- Recent addition: `chat.agent.maxRequests = 35` (sync with VS Code)
- Terminal optimization: smooth scrolling, 10000-line scrollback

---

### Verification Tasks

#### 1. Core Settings Alignment (15 Settings)

**Check:** `C:\Users\irfan\AppData\Roaming\Windsurf\User\settings.json`

**Expected Settings:**
1. `files.autoSave` = `"onFocusChange"`
2. `files.trimTrailingWhitespace` = `true`
3. `files.insertFinalNewline` = `true`
4. `files.eol` = `"\n"` (LF, not CRLF)
5. `editor.formatOnSave` = `true`
6. `editor.formatOnSaveMode` = `"file"`
7. `editor.minimap.enabled` = `false`
8. `editor.bracketPairColorization.enabled` = `true`
9. `editor.stickyScroll.enabled` = `true`
10. `[python].defaultFormatter` = `"charliermarsh.ruff"`
11. `[python].tabSize` = `4`
12. `files.exclude` patterns (`.venv`, `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`)
13. `chat.agent.maxRequests` = `35` (Windsurf-specific)
14. `git.enableSmartCommit` = `true`
15. `git.autofetch` = `false`

**Questions:**
- Which of the 15 settings are missing or have incorrect values?
- Are there conflicting settings (e.g., formatOnSave=false elsewhere)?
- Is `[python].defaultFormatter` set to ruff (NOT black, NOT autopep8)?
- Are cache exclusion patterns complete?

**Expected Output:** Settings diff vs. VS Code user settings

---

#### 2. Windsurf-Specific Settings Verification

**Check:** Windsurf-only settings that may conflict with standards

**Settings to verify:**
- `chat.agent.maxRequests` = `35` (prevents rate limiting during long coding sessions)
- `terminal.integrated.smoothScrolling` = (check if enabled)
- `terminal.integrated.scrollback` = (check if 10000 lines)
- `workbench.colorTheme` = (user preference, not critical)
- Cascade AI settings (if any custom prompts/rules configured)

**Questions:**
- Is `chat.agent.maxRequests` set to 35 (recent sync addition)?
- Are terminal settings optimized for THE GRID workflow?
- Are there Windsurf-specific AI settings that might interfere with development discipline?

**Expected Output:** Windsurf-specific config status

---

#### 3. Python Ecosystem Configuration

**Check:** Python-specific settings for monorepo

**Expected:**
- `[python].defaultFormatter` = `"charliermarsh.ruff"`
- `[python].tabSize` = `4` (Python standard)
- `python.analysis.typeCheckingMode` = `"basic"` or `"strict"`
- `python.languageServer` = `"Pylance"` (if Pylance installed)
- `python.analysis.extraPaths` = workspace-level (not user-level, but verify awareness)
- `python.defaultInterpreterPath` = `"${workspaceFolder}/.venv/Scripts/python.exe"` (if set)

**Questions:**
- Is ruff configured as the Python formatter?
- Are there conflicting Python formatters configured (black, autopep8)?
- Is type checking enabled?
- Are Python paths aware of monorepo structure?

**Expected Output:** Python config completeness report

---

#### 4. Cache & Performance Optimization

**Check:** File exclusions for performance

**Expected exclusion patterns:**
```json
"files.exclude": {
  "**/.venv": true,
  "**/__pycache__": true,
  "**/.pytest_cache": true,
  "**/.mypy_cache": true,
  "**/.ruff_cache": true,
  "**/*.pyc": true,
  "**/.DS_Store": true
}
```

**Questions:**
- Are all 7 cache patterns excluded from file explorer?
- Should `search.exclude` and `files.watcherExclude` mirror these patterns?
- Are there new cache folders created by Windsurf that should be excluded?
- Is `archive/**` excluded (10GB+ historical files)?

**Expected Output:** Performance optimization recommendations

---

#### 5. Cross-IDE Consistency Check

**Compare:** Windsurf settings vs. VS Code user settings

**Settings files to compare:**
- Windsurf: `C:\Users\irfan\AppData\Roaming\Windsurf\User\settings.json`
- VS Code: `C:\Users\irfan\AppData\Roaming\Code\User\settings.json`
- Cursor: `C:\Users\irfan\AppData\Roaming\Cursor\User\settings.json` (if available)

**Questions:**
- Are the 15 core settings identical across all 3 IDEs?
- Are there settings in VS Code that are missing in Windsurf?
- Are there settings unique to Windsurf that should be documented?
- Would switching from VS Code to Windsurf mid-session cause formatting conflicts?

**Expected Output:** Cross-IDE diff matrix

---

#### 6. Extension/Plugin Availability

**Check:** Windsurf extensions/plugins (if applicable)

**Note:** Windsurf may use a different extension ecosystem than VS Code

**Questions:**
- Does Windsurf support VS Code extensions?
- Is there a ruff extension/plugin available for Windsurf?
- Are there Windsurf-native formatters that might conflict with ruff?
- How does Windsurf handle Python formatting (built-in vs. extension)?

**Expected Output:** Extension compatibility report

---

#### 7. Workspace Integration

**Check:** How Windsurf handles `.vscode/` workspace configs

**Questions:**
- Does Windsurf read `.vscode/settings.json` when opening `E:\grid`?
- Does it respect workspace settings precedence (Workspace > User)?
- Are `.vscode/tasks.json` tasks runnable in Windsurf?
- Does Windsurf integrate with `.vscode/extensions.json` recommendations?

**Expected Output:** Workspace config integration status

---

#### 8. Terminal & Environment

**Check:** Terminal configuration in Windsurf

**Expected:**
- Default shell: PowerShell on Windows
- Terminal env vars: PYTHONPATH, PROJECT_ROOT, GRID_ENV (if workspace config read)
- Scrollback: 10000 lines (per documented optimization)
- Smooth scrolling: enabled (per documented optimization)

**Questions:**
- Does Windsurf terminal inject workspace env vars from `.vscode/settings.json`?
- Is PYTHONPATH correctly formatted for Windows (semicolon-separated)?
- Are terminal profiles (PowerShell, WSL) configured?
- Does the terminal integration work with `uv` commands?

**Expected Output:** Terminal integration report

---

#### 9. Git Integration

**Check:** Git settings alignment with development discipline

**Expected:**
- `git.autofetch` = `false` (manual control)
- `git.confirmSync` = `false` (streamlined workflow)
- `git.enableSmartCommit` = `true` (auto-stage on commit)
- `git.autoRepositoryDetection` = `false` or `true` (check current value)

**Questions:**
- Are git settings consistent with VS Code?
- Does Windsurf have additional git features that might conflict?
- Is there a git graph/history view (like GitLens in VS Code)?

**Expected Output:** Git integration status

---

#### 10. Cascade AI Agent Configuration

**Check:** Windsurf's Cascade AI agent settings

**Questions:**
- Is `chat.agent.maxRequests = 35` set (prevents rate limiting)?
- Are there custom Cascade rules/prompts that might interfere with THE GRID's development discipline?
- Does Cascade respect `.claude/` rules when suggesting code?
- Are there Cascade settings that should be documented for team consistency?

**Expected Output:** Cascade AI config report

---

### Gap Prioritization

**Severity:**
- 🔴 **Critical:** Breaks cross-IDE consistency (e.g., different formatter than VS Code)
- 🟠 **High:** Reduces workflow efficiency (e.g., cache folders not excluded)
- 🟡 **Medium:** Documentation gap (e.g., Windsurf-specific settings not documented)
- 🟢 **Low:** Nice-to-have (e.g., terminal theme)

---

### Output Format

```markdown
# Windsurf IDE Gap Analysis Report
Date: 2026-02-12

## Executive Summary
- Settings alignment: X/15 core settings match VS Code
- Missing settings: [list]
- Conflicting settings: [list]
- Windsurf-specific gaps: [list]

## Detailed Findings

### 1. Core Settings Alignment
**Status:** [X/15 match VS Code]
**Missing:** [list settings not present]
**Conflicts:** [list settings with different values]
**Fix:** [specific commands/actions]

### 2. Windsurf-Specific Settings
**Status:** [configured/not configured]
**chat.agent.maxRequests:** [current value]
**Terminal optimization:** [enabled/disabled]
**Fix:** [actions needed]

### 3. Python Ecosystem
**Formatter:** [charliermarsh.ruff / other]
**Type checking:** [enabled/disabled]
**Conflicts:** [black, autopep8, etc.]
**Fix:** [actions needed]

### 4. Cross-IDE Consistency
**VS Code alignment:** [%]
**Cursor alignment:** [%]
**Critical diffs:** [list]
**Fix:** [sync commands]

## Recommended Actions (Priority Order)

1. [🔴] Sync core settings: Copy VS Code user settings to Windsurf
2. [🟠] Configure cache exclusions: Add missing patterns
3. [🟡] Document Windsurf-specific settings
[...]

## Verification Commands

```bash
# Compare settings files
diff "C:\Users\irfan\AppData\Roaming\Windsurf\User\settings.json" \
     "C:\Users\irfan\AppData\Roaming\Code\User\settings.json"

# Test ruff integration (if available)
# Open Python file → save → verify formatting occurs
```

## Notes
- Cross-reference: `docs/guides/CROSS_DRIVE_CONFIG_INTEGRATION_FINDINGS.md`
- Windsurf terminal optimization documented but not verified
```

---

### Success Criteria

✅ All 15 core settings match VS Code user settings
✅ `chat.agent.maxRequests = 35` configured
✅ Python formatter set to ruff (NOT black/autopep8)
✅ Cache exclusions complete (7 patterns)
✅ Cross-IDE consistency verified (can switch from VS Code to Windsurf without conflicts)
✅ Terminal integration tested (`uv` commands work)
✅ Workspace config integration confirmed

---

### Quick Verification Script (PowerShell)

```powershell
# Compare Windsurf vs. VS Code settings
$windsurf = Get-Content "C:\Users\irfan\AppData\Roaming\Windsurf\User\settings.json" | ConvertFrom-Json
$vscode = Get-Content "C:\Users\irfan\AppData\Roaming\Code\User\settings.json" | ConvertFrom-Json

# Check core settings
$coreSettings = @(
    "files.autoSave",
    "files.trimTrailingWhitespace",
    "files.insertFinalNewline",
    "files.eol",
    "editor.formatOnSave",
    "editor.minimap.enabled",
    "[python].defaultFormatter"
)

foreach ($setting in $coreSettings) {
    $vsValue = $vscode.$setting
    $wsValue = $windsurf.$setting
    if ($vsValue -ne $wsValue) {
        Write-Host "⚠️ MISMATCH: $setting" -ForegroundColor Yellow
        Write-Host "  VS Code: $vsValue"
        Write-Host "  Windsurf: $wsValue"
    } else {
        Write-Host "✅ $setting" -ForegroundColor Green
    }
}

# Check Windsurf-specific
if ($windsurf."chat.agent.maxRequests" -eq 35) {
    Write-Host "✅ chat.agent.maxRequests = 35" -ForegroundColor Green
} else {
    Write-Host "⚠️ chat.agent.maxRequests NOT SET or incorrect" -ForegroundColor Yellow
}
```

---

### Context Files

- `C:\Users\irfan\AppData\Roaming\Windsurf\User\settings.json` — Windsurf user settings
- `C:\Users\irfan\AppData\Roaming\Code\User\settings.json` — VS Code reference
- `E:\grid\docs\guides\CROSS_DRIVE_CONFIG_INTEGRATION_FINDINGS.md` — Windsurf integration docs
- `E:\grid\docs\guides\CONFIGURATION_OPTIMIZATION_SUMMARY.md` — IDE optimization notes
- `E:\grid\.vscode\settings.json` — Workspace settings (should Windsurf respect these?)

---

**Focus Areas:**
1. **Consistency:** Ensure Windsurf matches VS Code/Cursor
2. **Windsurf-Specific:** Document unique settings (chat.agent.maxRequests)
3. **Performance:** Verify cache exclusions and terminal optimization
4. **Integration:** Test workspace config loading and terminal env vars

Run this audit and report back with the full gap analysis.
```
