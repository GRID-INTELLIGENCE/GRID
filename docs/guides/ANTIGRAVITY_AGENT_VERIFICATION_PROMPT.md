# Antigravity Agent: IDE Setup Gap Analysis Prompt

> **Purpose:** Verify Antigravity IDE configuration for THE GRID development workflow
> **Created:** 2026-02-12
> **Context:** Antigravity settings status unclear — exploration found minimal config (3 → 17 settings sync mentioned)

---

## Prompt for Antigravity Agent

```
You are auditing Antigravity IDE configuration for THE GRID monorepo. According to recent sync notes, Antigravity went from "3 settings → 17 settings" during IDE standardization, but no specific configuration file was found during exploration. Your task is to locate Antigravity's config, verify the 17 settings, and assess compatibility with THE GRID's development standards.

### Context

**Project:** THE GRID — Local-first AI codebase analysis (Python + React + AI Safety)
**Standards:** Python 3.13, ruff formatter/linter, 120-char lines, `uv` package manager
**Recent Sync:** Antigravity settings updated from 3 → 17 (per IDE standardization notes)
**Status:** Configuration file location unknown (not found in initial exploration)

**Key Questions:**
1. Where does Antigravity store its settings?
2. Are the 17 settings actually applied?
3. Is Antigravity a VS Code fork, standalone IDE, or something else?

---

### Verification Tasks

#### 1. Installation & Configuration Discovery

**Check:** Is Antigravity installed? Where?

**Possible locations:**
- `C:\Program Files\Antigravity\`
- `C:\Users\irfan\AppData\Local\Antigravity\`
- `C:\Users\irfan\AppData\Roaming\Antigravity\`
- `C:\Users\irfan\.antigravity\`
- Installed via package manager (Scoop, Chocolatey, WinGet)?
- VS Code extension named "Antigravity"?

**Questions:**
- Is Antigravity actually installed on this system?
- What is Antigravity? (IDE, extension, code editor, AI tool?)
- Where is the executable? (`where antigravity`, `Get-Command antigravity`)
- Where are settings stored?

**Expected Output:** Installation discovery report

---

#### 2. Settings File Location & Structure

**Check:** Find Antigravity's configuration file

**Search strategy:**
```powershell
# Search for Antigravity config files
Get-ChildItem -Path "$env:APPDATA" -Recurse -Filter "*antigravity*" -ErrorAction SilentlyContinue
Get-ChildItem -Path "$env:LOCALAPPDATA" -Recurse -Filter "*antigravity*" -ErrorAction SilentlyContinue
Get-ChildItem -Path "$env:USERPROFILE" -Recurse -Filter ".antigravity*" -ErrorAction SilentlyContinue

# Check for settings.json
Get-ChildItem -Path "C:\Users\irfan" -Recurse -Filter "settings.json" | Where-Object { $_.FullName -like "*antigravity*" }
```

**Possible file names:**
- `settings.json`
- `config.json`
- `.antigravityrc`
- `antigravity.config.js`
- `preferences.json`

**Questions:**
- Does a settings file exist?
- If yes, what is the file structure? (JSON, TOML, YAML?)
- If no, does Antigravity use VS Code settings?

**Expected Output:** Config file path + structure example

---

#### 3. Settings Content Verification (17 Settings)

**Check:** Verify the 17 settings mentioned in sync notes

**Expected 17 settings (15 core + 2 additions):**

**Core 15:**
1. `files.autoSave` = `"onFocusChange"`
2. `files.trimTrailingWhitespace` = `true`
3. `files.insertFinalNewline` = `true`
4. `files.eol` = `"\n"`
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
15. `chat.agent.maxRequests` = `35` (if AI-enabled IDE)

**Additional 2 (to reach 17):**
16. ??? (unknown — identify from config file)
17. ??? (unknown — identify from config file)

**Questions:**
- Are all 17 settings present in Antigravity config?
- What are settings 16 and 17? (Not documented in standardization notes)
- Are settings values correct (match VS Code)?
- Are there Antigravity-specific settings that override these?

**Expected Output:** Settings verification matrix (17/17 present + correct)

---

#### 4. Antigravity Architecture & Compatibility

**Check:** What is Antigravity's relationship to VS Code?

**Possible architectures:**
1. **VS Code Fork:** Based on VS Code, uses same extensions
2. **Standalone Editor:** Independent codebase, own extension system
3. **VS Code Extension:** Runs inside VS Code, adds features
4. **Electron-Based:** Similar to VS Code but separate
5. **Cloud IDE:** Browser-based (like GitHub Codespaces)

**Questions:**
- Which architecture does Antigravity use?
- Does it support VS Code extensions? (Can you install `charliermarsh.ruff`?)
- If not, how does it handle Python formatting?
- Is it actively maintained? (Check website, GitHub, last update date)

**Expected Output:** Architecture documentation + compatibility matrix

---

#### 5. Python Ecosystem Integration

**Check:** Python tooling support in Antigravity

**Questions:**
- Does Antigravity have a Python extension/plugin?
- Can it install `charliermarsh.ruff` extension (if VS Code-compatible)?
- Does it have built-in Python support?
- Can it integrate with `uv run ruff` CLI?
- Does it support:
  - Syntax highlighting?
  - IntelliSense / autocomplete?
  - Type checking (Pylance equivalent)?
  - Debugging?
  - pytest integration?

**Expected Output:** Python tooling support matrix

---

#### 6. Workspace Configuration Support

**Check:** `.vscode/` workspace config compatibility

**Questions:**
- Does Antigravity read `.vscode/settings.json`?
- Does it support `.vscode/tasks.json` (14 tasks)?
- Can you run "Daily: Verify the Wall" task?
- Does it respect `.vscode/extensions.json` recommendations?
- Does it load terminal env vars from workspace settings?

**Expected Output:** Workspace integration report

---

#### 7. Cross-IDE Consistency Test

**Check:** Formatting consistency with VS Code/Cursor/Windsurf

**Test scenario:**
1. Open a Python file in Antigravity
2. Add formatting issues: `def   example( a,b ):`
3. Save the file
4. Check if it auto-formats

**Questions:**
- Does format-on-save work?
- If yes, does it match VS Code/ruff formatting?
- If no, does Antigravity have a different formatter?
- Would switching from VS Code to Antigravity mid-session cause conflicts?

**Expected Output:** Cross-IDE consistency report

---

#### 8. Terminal & CLI Integration

**Check:** Integrated terminal support

**Questions:**
- Does Antigravity have an integrated terminal?
- If yes, does it load workspace env vars (PYTHONPATH, PROJECT_ROOT)?
- Can you run `uv run pytest`, `uv run ruff check`?
- Is the default shell PowerShell (Windows)?
- Are there terminal-specific settings?

**Expected Output:** Terminal integration status

---

#### 9. Performance & Usability

**Check:** Performance characteristics

**Questions:**
- Startup time compared to VS Code?
- Memory usage for large monorepo (THE GRID)?
- File watching performance (does it exclude cache folders)?
- Search performance (does it respect search.exclude patterns)?
- Is it suitable for THE GRID's monorepo workflow?

**Expected Output:** Performance assessment

---

#### 10. Recommendation: Use, Configure, or Avoid?

**Synthesize findings:**

**Use If:**
- ✅ Settings fully synced (17/17)
- ✅ VS Code extension compatible (ruff works)
- ✅ Workspace config support (tasks work)
- ✅ Cross-IDE consistency (formatting matches)
- ✅ Good performance (suitable for monorepo)

**Configure If:**
- ⚠️ Settings partially synced (need manual updates)
- ⚠️ Some features missing (but core workflow works)
- ⚠️ Performance acceptable (with optimizations)

**Avoid If:**
- ❌ Settings cannot be synced (incompatible architecture)
- ❌ No ruff support (different formatter)
- ❌ Poor workspace integration (tasks don't work)
- ❌ Cross-IDE conflicts (breaks consistency)
- ❌ Abandoned project (no recent updates)

**Expected Output:** Clear recommendation with reasoning

---

### Gap Prioritization

**Severity:**
- 🔴 **Critical:** Antigravity breaks THE GRID workflow
- 🟠 **High:** Missing settings or poor compatibility
- 🟡 **Medium:** Documentation gap
- 🟢 **Low:** Minor usability issues

---

### Output Format

```markdown
# Antigravity IDE Gap Analysis Report
Date: 2026-02-12

## Executive Summary
- Installation Status: [Installed / Not Found]
- Config File Location: [path or "Not Found"]
- Settings Synced: [X/17]
- Architecture: [VS Code Fork / Standalone / Extension / Unknown]
- Recommendation: [✅ Use / ⚠️ Configure / ❌ Avoid / ❓ Not Installed]

## Detailed Findings

### 1. Installation Discovery
**Status:** [Installed / Not Found]
**Location:** [path or "N/A"]
**Version:** [version or "Unknown"]
**Type:** [IDE / Extension / Tool]

### 2. Settings File
**Path:** [path or "Not Found"]
**Format:** [JSON / TOML / YAML / N/A]
**Size:** [number of settings or "N/A"]

### 3. Settings Verification (17 Expected)
**Present:** [X/17]
**Missing:** [list]
**Incorrect:** [list with expected vs. actual values]
**Unknown Settings 16-17:** [description]

### 4. Architecture & Compatibility
**Type:** [VS Code Fork / Standalone / Extension]
**VS Code Extensions:** [Compatible: Yes/No/Unknown]
**Ruff Support:** [Extension / Built-in / CLI Only / None]

### 5. Python Ecosystem
**Formatter:** [ruff / other / none]
**Type Checking:** [Supported: Yes/No]
**pytest Integration:** [Supported: Yes/No]
**CLI Integration:** [uv commands work: Yes/No/Unknown]

### 6. Workspace Integration
**Reads .vscode/settings.json:** [Yes/No/Unknown]
**Tasks runnable:** [Yes/No/Unknown]
**Terminal env vars:** [Load: Yes/No/Unknown]

### 7. Cross-IDE Consistency
**Format-on-save:** [Works: Yes/No/Unknown]
**Matches VS Code:** [Yes/No/Unknown]
**Conflicts:** [list or "None"]

### 8. Performance
**Startup Time:** [Fast / Slow / Unknown]
**Memory Usage:** [Acceptable / High / Unknown]
**Suitable for Monorepo:** [Yes/No/Unknown]

## Recommended Actions

**If Installed:**
1. [Priority] Locate config file: [search command]
2. [Priority] Verify 17 settings: [comparison command]
3. [Priority] Test ruff integration: [open Python file → save → verify formatting]
[...]

**If Not Installed:**
1. Determine if Antigravity should be installed
2. If yes, install and configure
3. If no, remove from IDE standardization docs

## Final Recommendation

**[✅ Use / ⚠️ Configure / ❌ Avoid / ❓ Not Installed]**

**Reasoning:**
[Detailed explanation based on findings]

**If Use:**
- Antigravity fully compatible with THE GRID workflow
- 17/17 settings synced
- Ruff integration working
- Can switch from VS Code to Antigravity seamlessly

**If Configure:**
- Antigravity usable but needs manual config updates
- Settings file found but some values incorrect
- Ruff works via CLI but not integrated
- [Specific config steps...]

**If Avoid:**
- Antigravity incompatible with THE GRID standards
- No ruff support
- Cannot sync settings
- Better to use VS Code/Cursor/Windsurf

**If Not Installed:**
- Antigravity not found on system
- Verify if it should be installed or removed from docs
```

---

### Success Criteria

✅ Antigravity installation status confirmed (installed or not)
✅ If installed: Config file located
✅ If installed: 17 settings verified
✅ Architecture and compatibility documented
✅ Python/ruff integration tested
✅ Cross-IDE consistency assessed
✅ Clear recommendation provided (Use/Configure/Avoid/Not Installed)

---

### Quick Discovery Script (PowerShell)

```powershell
Write-Host "=== Antigravity Discovery ===" -ForegroundColor Cyan

# Check if installed
$antigravityExe = Get-Command antigravity -ErrorAction SilentlyContinue
if ($antigravityExe) {
    Write-Host "✅ Antigravity executable found: $($antigravityExe.Source)" -ForegroundColor Green
} else {
    Write-Host "❌ Antigravity executable not found in PATH" -ForegroundColor Red
}

# Search for config files
Write-Host "`n=== Searching for config files ===" -ForegroundColor Cyan
$locations = @(
    "$env:APPDATA\Antigravity",
    "$env:LOCALAPPDATA\Antigravity",
    "$env:USERPROFILE\.antigravity",
    "C:\Program Files\Antigravity"
)

foreach ($loc in $locations) {
    if (Test-Path $loc) {
        Write-Host "✅ Found: $loc" -ForegroundColor Green
        Get-ChildItem -Path $loc -Filter "*.json" -Recurse | ForEach-Object {
            Write-Host "  Config file: $($_.FullName)" -ForegroundColor Yellow
        }
    }
}

# Check VS Code extensions
Write-Host "`n=== VS Code Extensions ===" -ForegroundColor Cyan
$extensions = code --list-extensions | Select-String -Pattern "antigravity" -CaseSensitive:$false
if ($extensions) {
    Write-Host "✅ Antigravity VS Code extension found" -ForegroundColor Green
    $extensions
} else {
    Write-Host "❌ No Antigravity extension in VS Code" -ForegroundColor Red
}

Write-Host "`nAntigravity discovery complete." -ForegroundColor Cyan
```

---

### Context Files

- Sync notes mention "Antigravity: 3 settings → 17" but no file path
- VS Code user settings: `C:\Users\irfan\AppData\Roaming\Code\User\settings.json` (reference)
- `.vscode/settings.json` — workspace config to test against
- No prior Antigravity config found in exploration

---

### Critical Questions to Answer

1. **Is Antigravity installed?**
   - If no: Should it be installed, or is it a legacy reference?

2. **If installed, where are settings?**
   - Standalone config file?
   - Inherits from VS Code?
   - Cloud-synced?

3. **What are settings 16 and 17?**
   - Standardization notes mention 17 total (15 core + 2 unknown)

4. **Should Antigravity be part of THE GRID's multi-IDE workflow?**
   - Or should it be documented as "not recommended"?

Run this discovery and provide a comprehensive report.
```
