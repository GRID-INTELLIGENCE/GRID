# OpenCode Agent: IDE Setup Gap Analysis Prompt

> **Purpose:** Verify OpenCode AI IDE configuration for THE GRID development workflow
> **Created:** 2026-02-12
> **Context:** OpenCode is installed globally (`npm list -g` shows `opencode-ai@1.1.53`)

---

## Prompt for OpenCode Agent

```
You are auditing OpenCode AI IDE configuration for THE GRID monorepo. OpenCode is a VS Code-based AI coding assistant, so it should inherit VS Code settings, but may have its own configuration layer. Your task is to verify OpenCode-specific settings and ensure consistency with THE GRID's development standards.

### Context

**Project:** THE GRID — Local-first AI codebase analysis (Python + React + AI Safety)
**Standards:** Python 3.13, ruff formatter/linter, 120-char lines, `uv` package manager
**OpenCode Version:** `opencode-ai@1.1.53` (installed globally via npm)
**Base IDE:** VS Code (OpenCode likely extends VS Code)

**Key Question:** Does OpenCode have its own settings/config separate from VS Code, or does it purely extend VS Code?

---

### Verification Tasks

#### 1. Installation & Version Check

**Check:**
```bash
npm list -g | findstr opencode
# Expected: opencode-ai@1.1.53
```

**Questions:**
- Is OpenCode AI installed globally or per-workspace?
- What is the current version? (1.1.53 confirmed)
- Are there updates available?
- Is OpenCode a standalone IDE or a VS Code extension?

**Expected Output:** Installation status report

---

#### 2. Configuration File Location

**Check:** Where does OpenCode store its settings?

**Possible locations:**
- `C:\Users\irfan\AppData\Roaming\OpenCode\User\settings.json` (if standalone)
- `C:\Users\irfan\.opencode\config.json` (if separate config)
- Inherits from VS Code settings (if extension-only)
- `%APPDATA%\Code\User\settings.json` (if VS Code extension)

**Questions:**
- Does OpenCode have its own settings file separate from VS Code?
- If yes, where is it located?
- If no, does it read VS Code settings directly?
- Are there OpenCode-specific settings that override VS Code?

**Expected Output:** Config file location + structure

---

#### 3. Settings Inheritance Model

**Check:** How does OpenCode handle settings?

**Possible models:**
1. **Standalone:** Has its own settings, ignores VS Code
2. **Extension:** Reads VS Code settings, adds AI-specific settings on top
3. **Fork:** Forked from VS Code, has separate settings but similar structure
4. **Hybrid:** Reads VS Code settings + has OpenCode-specific overrides

**Questions:**
- Which model does OpenCode follow?
- If it has separate settings, are the 15 core settings (autoSave, formatOnSave, etc.) present?
- Does it respect `.vscode/settings.json` workspace configs?
- Are there OpenCode AI settings that might interfere with ruff/formatting?

**Expected Output:** Inheritance model documentation

---

#### 4. Python Ecosystem Configuration

**Check:** Python formatter and linter settings

**Expected:**
- `[python].defaultFormatter` = `"charliermarsh.ruff"` (if configurable)
- Python extension installed (if OpenCode supports VS Code extensions)
- Ruff extension installed (if OpenCode supports VS Code extensions)

**Questions:**
- Does OpenCode support VS Code extensions?
- If yes, is `charliermarsh.ruff` extension installed?
- If no, does OpenCode have built-in Python formatting?
- Does OpenCode AI suggest code that bypasses ruff formatting?
- Can OpenCode AI be configured to respect THE GRID's linting rules?

**Expected Output:** Python tooling integration report

---

#### 5. AI Code Generation Settings

**Check:** OpenCode AI-specific settings that might affect code quality

**Questions:**
- Does OpenCode AI have configurable rules/prompts?
- Can it be told to follow THE GRID's core principles (no `eval()`, no `exec()`, etc.)?
- Does it respect `.claude/rules/` files (unlikely, but check)?
- Are there OpenCode AI settings for:
  - Code style (120-char lines)?
  - Import organization (stdlib → third-party → local)?
  - Type hint generation?
  - Docstring style?
- Can OpenCode AI be disabled/limited for safety-critical code (`safety/`, `security/`, `boundaries/`)?

**Expected Output:** AI code generation config report

---

#### 6. Extension Compatibility

**Check:** Can OpenCode use VS Code extensions?

**If yes, verify:**
- `charliermarsh.ruff` extension installable?
- `ms-python.python` extension works?
- `ms-python.vscode-pylance` extension works?
- Other workspace-recommended extensions compatible?

**If no:**
- What is OpenCode's alternative for Python formatting?
- How does it handle linting?
- Can it integrate with `uv run ruff` CLI?

**Expected Output:** Extension compatibility matrix

---

#### 7. Workspace Integration

**Check:** `.vscode/` workspace config support

**Questions:**
- Does OpenCode read `.vscode/settings.json`?
- Does it support `.vscode/tasks.json` (14 tasks)?
- Can you run "Daily: Verify the Wall" task (Ctrl+Shift+B)?
- Does it respect `.vscode/extensions.json` recommendations?
- Are terminal env vars (`PYTHONPATH`, `PROJECT_ROOT`) loaded?

**Expected Output:** Workspace integration status

---

#### 8. Terminal & CLI Integration

**Check:** Terminal functionality in OpenCode

**Questions:**
- Does OpenCode have an integrated terminal?
- If yes, does it load workspace env vars?
- Can you run `uv run pytest`, `uv run ruff check`, etc.?
- Is the default shell PowerShell (Windows)?
- Are there terminal-specific settings separate from VS Code?

**Expected Output:** Terminal integration report

---

#### 9. Cross-IDE Consistency

**Compare:** OpenCode vs. VS Code vs. Cursor vs. Windsurf

**Questions:**
- If you format a Python file in OpenCode, does it match VS Code's formatting?
- Can you switch from VS Code to OpenCode mid-session without conflicts?
- Are the 15 core settings (autoSave, trimTrailingWhitespace, etc.) consistent?
- Would using OpenCode break the cross-IDE workflow?

**Expected Output:** Cross-IDE consistency report

---

#### 10. Documentation & Support

**Check:** OpenCode documentation and community resources

**Questions:**
- Is OpenCode actively maintained? (Check GitHub repo, npm updates)
- Is there official documentation for configuration?
- Are there known conflicts with ruff or other Python tools?
- Is OpenCode recommended for THE GRID workflow, or should it be avoided?

**Expected Output:** Recommendation (Use / Avoid / Configure)

---

### Gap Prioritization

**Severity:**
- 🔴 **Critical:** OpenCode overrides ruff formatting or breaks standards
- 🟠 **High:** Missing settings or poor VS Code compatibility
- 🟡 **Medium:** Documentation gap or unclear config model
- 🟢 **Low:** Minor inconsistencies

---

### Output Format

```markdown
# OpenCode AI Gap Analysis Report
Date: 2026-02-12

## Executive Summary
- OpenCode Model: [Standalone / Extension / Fork / Hybrid]
- VS Code Compatibility: [Full / Partial / None]
- Settings Alignment: [X/15 core settings match]
- Recommendation: [✅ Use / ⚠️ Configure / ❌ Avoid]

## Detailed Findings

### 1. Installation & Version
**Status:** Installed globally via npm
**Version:** opencode-ai@1.1.53
**Type:** [Standalone IDE / VS Code Extension]
**Updates Available:** [Yes/No]

### 2. Configuration Model
**Settings File:** [path or "inherits from VS Code"]
**Inheritance:** [Standalone / Extension / Fork / Hybrid]
**Workspace Support:** [Yes/No]
**Override Behavior:** [description]

### 3. Python Ecosystem
**Formatter:** [ruff / built-in / none]
**Extensions Supported:** [Yes/No]
**Ruff Extension:** [Installed / Not Installed / Not Supported]
**CLI Integration:** [`uv run ruff` works: Yes/No]

### 4. AI Code Generation
**Configurable Rules:** [Yes/No]
**Respects .claude/rules/:** [Yes/No]
**Code Style Awareness:** [120-char lines: Yes/No]
**Safety Module Restrictions:** [Can disable AI in safety/: Yes/No]

### 5. Cross-IDE Consistency
**Format-on-save matches VS Code:** [Yes/No]
**Can switch mid-session:** [Yes/No]
**Conflicts detected:** [list]

## Recommended Actions

1. [Priority] [Action description]
2. [Priority] [Action description]
[...]

## Verification Commands

```bash
# Check OpenCode installation
npm list -g | findstr opencode

# Find config file (Windows)
Get-ChildItem -Path "$env:APPDATA" -Recurse -Filter "*opencode*" -Directory

# Test formatting (if OpenCode supports Python)
# Open Python file in OpenCode → save → verify ruff formatting occurs
```

## Recommendation

**[✅ Use / ⚠️ Configure / ❌ Avoid]**

**Reasoning:** [Explain why OpenCode should/shouldn't be used for THE GRID]

**If Configure:** [List specific settings to apply]

**If Avoid:** [Suggest alternative (VS Code, Cursor, Windsurf)]
```

---

### Success Criteria

✅ OpenCode installation and type identified (standalone vs. extension)
✅ Config file location and inheritance model documented
✅ Python formatting compatibility verified (ruff works or not)
✅ AI code generation settings reviewed (respects standards or not)
✅ Cross-IDE consistency tested (can switch from VS Code to OpenCode)
✅ Recommendation provided (Use/Configure/Avoid)

---

### Context Files

- `package.json` (if OpenCode has one in global npm)
- `C:\Users\irfan\AppData\Roaming\OpenCode\*` (if config exists)
- `C:\Users\irfan\AppData\Roaming\Code\User\settings.json` (VS Code reference)
- `E:\grid\.vscode\settings.json` (Workspace settings to test against)

---

### Critical Questions to Answer

1. **Is OpenCode a separate IDE or a VS Code extension?**
   - If separate: Does it have its own settings file?
   - If extension: Does it modify VS Code's behavior?

2. **Does OpenCode support the ruff extension?**
   - If yes: Verify `charliermarsh.ruff` is installed
   - If no: How does it format Python code?

3. **Can OpenCode AI be configured to follow THE GRID's standards?**
   - 120-char lines
   - No `eval()`, `exec()`, `pickle`
   - Type hints required
   - Async-first patterns

4. **Should OpenCode be part of THE GRID's multi-IDE workflow?**
   - Or should it be avoided due to conflicts?

Run this audit and provide a clear recommendation: **Use**, **Configure**, or **Avoid** OpenCode for THE GRID development.
```
