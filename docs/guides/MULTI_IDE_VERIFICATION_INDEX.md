# Multi-IDE Verification Index

> **Purpose:** Central hub for IDE-specific gap analysis prompts
> **Created:** 2026-02-12
> **Context:** THE GRID supports multiple IDEs (VS Code, Cursor, Windsurf, OpenCode, Antigravity) — this index organizes verification workflows

---

## Overview

THE GRID's development discipline depends on **automated enforcement** of core principles through IDE configuration. To ensure consistency across editors, we've created specialized verification prompts for each IDE in the multi-IDE workflow.

**Goal:** Every IDE should enforce the same standards (ruff formatting, 120-char lines, format-on-save, cache exclusions, etc.) so developers can switch editors mid-session without conflicts.

---

## Verification Prompt Files

### 1. VS Code (Reference Implementation) ✅ PRIMARY

**File:** [`VSCODE_AGENT_VERIFICATION_PROMPT.md`](./VSCODE_AGENT_VERIFICATION_PROMPT.md)

**Agent:** GitHub Copilot Chat (or Claude Code)

**Purpose:** Comprehensive audit of VS Code configuration — this is the **master reference** that all other IDEs should match.

**Scope:**
- 18 workspace-recommended extensions (7/18 installed, 11 missing)
- 15 core settings across User → Profile → Workspace inheritance
- 14 runnable tasks (pytest, ruff, mypy, frontend dev, etc.)
- Python ecosystem (Pylance, pytest, mypy, ruff)
- Frontend ecosystem (TypeScript, ESLint, Prettier)
- Terminal & environment variables
- Performance exclusions (archive/, .venv/, node_modules/, etc.)
- Development discipline automation (daily wall check)
- Git integration

**Status:** ✅ Ruff extension installed (v2026.36.0), settings configured, CLI working

**Use this prompt when:**
- Setting up VS Code for THE GRID for the first time
- Auditing current VS Code setup for gaps
- VS Code has been updated and behavior changed
- Other IDEs are drifting from standards (re-verify reference first)

---

### 2. Cursor ⚠️ VERIFICATION NEEDED

**File:** [`CURSOR_AGENT_VERIFICATION_PROMPT.md`](./CURSOR_AGENT_VERIFICATION_PROMPT.md)

**Agent:** Cursor's Composer or Claude (Cursor has built-in AI)

**Purpose:** Systematic audit of Cursor IDE to identify gaps vs. VS Code reference.

**Scope:**
- Extension coverage (18 recommendations)
- Settings inheritance (User vs. Profile vs. Workspace)
- Cross-IDE consistency (Cursor vs. VS Code)
- Workspace config (tasks, paths, formatters)
- Ruff integration (functional testing)
- Development discipline (wall check automation)
- Terminal & env vars
- File watching & performance
- Type checking & language server
- Documentation completeness

**Status:** ⚠️ Settings documented in `CONFIGURATION_OPTIMIZATION_SUMMARY.md` but not verified

**Use this prompt when:**
- Verifying Cursor matches VS Code settings
- Cursor updated and behavior changed
- Switching between VS Code and Cursor causes format conflicts
- Performance issues in Cursor (check exclusion patterns)

---

### 3. Windsurf ⚠️ VERIFICATION NEEDED

**File:** [`WINDSURF_AGENT_VERIFICATION_PROMPT.md`](./WINDSURF_AGENT_VERIFICATION_PROMPT.md)

**Agent:** Windsurf's Cascade AI

**Purpose:** Verify Windsurf IDE configuration matches THE GRID standards.

**Scope:**
- 15 core settings alignment (autoSave, formatOnSave, ruff formatter, etc.)
- Windsurf-specific settings (`chat.agent.maxRequests = 35`, terminal optimization)
- Python ecosystem configuration
- Cache & performance optimization
- Cross-IDE consistency check (vs. VS Code/Cursor)
- Extension/plugin availability (does Windsurf support VS Code extensions?)
- Workspace integration (`.vscode/` config loading)
- Terminal & environment
- Git integration
- Cascade AI agent configuration

**Status:** ⚠️ Recent sync added `chat.agent.maxRequests = 35` but full verification pending

**Use this prompt when:**
- Verifying Windsurf after initial setup
- Cascade AI suggestions violate THE GRID standards
- Windsurf terminal doesn't load PYTHONPATH
- Format conflicts between Windsurf and other IDEs

---

### 4. OpenCode ❓ STATUS UNKNOWN

**File:** [`OPENCODE_AGENT_VERIFICATION_PROMPT.md`](./OPENCODE_AGENT_VERIFICATION_PROMPT.md)

**Agent:** OpenCode's built-in AI (if available) or manual audit

**Purpose:** Determine OpenCode's architecture (standalone/extension/fork) and assess compatibility with THE GRID workflow.

**Scope:**
- Installation & version check (`opencode-ai@1.1.53` installed globally)
- Configuration file location (separate from VS Code or inherited?)
- Settings inheritance model (standalone/extension/fork/hybrid)
- Python ecosystem configuration (ruff support?)
- AI code generation settings (can it follow THE GRID standards?)
- Extension compatibility (VS Code extensions work?)
- Workspace integration (`.vscode/` configs supported?)
- Terminal & CLI integration
- Cross-IDE consistency
- Recommendation: **Use**, **Configure**, or **Avoid**?

**Status:** ❓ Installed (`npm list -g` shows `opencode-ai@1.1.53`) but config location unknown

**Use this prompt when:**
- Deciding whether to use OpenCode for THE GRID
- OpenCode is generating code that violates standards
- Determining if OpenCode should be part of multi-IDE workflow

---

### 5. Antigravity ❓ STATUS UNKNOWN

**File:** [`ANTIGRAVITY_AGENT_VERIFICATION_PROMPT.md`](./ANTIGRAVITY_AGENT_VERIFICATION_PROMPT.md)

**Agent:** Antigravity's AI (if available) or manual audit

**Purpose:** Locate Antigravity installation, verify 17 settings sync, and assess viability for THE GRID.

**Scope:**
- Installation & configuration discovery (where is Antigravity?)
- Settings file location & structure
- Settings content verification (17 expected: 15 core + 2 unknown)
- Antigravity architecture (VS Code fork? Standalone? Extension?)
- Python ecosystem integration
- Workspace configuration support
- Cross-IDE consistency test
- Terminal & CLI integration
- Performance & usability
- Recommendation: **Use**, **Configure**, or **Avoid**?

**Status:** ❓ Sync notes mention "3 settings → 17" but no config file found during exploration

**Use this prompt when:**
- Determining if Antigravity is actually installed
- Verifying the "17 settings" claim from sync notes
- Deciding whether Antigravity should be included in multi-IDE docs

---

## Verification Workflow

### Phase 1: Reference Verification (VS Code)

1. Run **VS Code verification prompt** first (it's the reference implementation)
2. Identify and fix all gaps in VS Code setup
3. Document the "correct" state (settings, extensions, tasks, etc.)
4. This becomes the baseline for other IDEs

### Phase 2: Cross-IDE Consistency (Cursor, Windsurf)

1. Run **Cursor verification prompt**
   - Compare settings against VS Code reference
   - Identify drift (missing/conflicting settings)
   - Sync settings to match VS Code

2. Run **Windsurf verification prompt**
   - Compare settings against VS Code reference
   - Verify Windsurf-specific settings (`chat.agent.maxRequests`)
   - Sync settings to match VS Code

3. Test cross-IDE workflow:
   - Open Python file in VS Code → format → save
   - Open same file in Cursor → verify no format changes
   - Open same file in Windsurf → verify no format changes

### Phase 3: Status Determination (OpenCode, Antigravity)

1. Run **OpenCode verification prompt**
   - Determine if OpenCode is viable for THE GRID
   - Recommendation: Use, Configure, or Avoid
   - If Use/Configure: Sync settings to match VS Code
   - If Avoid: Document why and remove from multi-IDE docs

2. Run **Antigravity verification prompt**
   - Determine if Antigravity is installed
   - If installed: Verify 17 settings, test compatibility
   - If not installed: Remove from multi-IDE docs or document as optional
   - Recommendation: Use, Configure, or Avoid

### Phase 4: Documentation Update

1. Update `IDE_SETUP_VERIFICATION.md` with findings
2. Update `CLAUDE.md` with supported IDEs list
3. Create decision log entry in `docs/decisions/DECISIONS.md`:
   ```
   ## 2026-02-12 — Multi-IDE Verification
   **Decision**: [Which IDEs are officially supported for THE GRID]
   **Why**: [Based on gap analysis findings]
   **Alternatives considered**: [IDEs tested but not recommended]
   ```

---

## Gap Analysis Output Format

Each IDE verification prompt produces a structured report:

```markdown
# [IDE Name] Gap Analysis Report
Date: 2026-02-12

## Executive Summary
- [Key metrics: settings synced, extensions installed, etc.]

## Detailed Findings
### 1. [Category Name]
**Status:** [status]
**Gaps:** [list]
**Fix:** [specific actions]

[Repeat for all categories...]

## Recommended Actions (Priority Order)
1. [🔴🎯] [Critical blocking action]
2. [🟠⚠️] [High-priority degrading action]
[...]

## Verification Commands
```bash
[Commands to run after fixes]
```

## Final Recommendation
[✅ Use / ⚠️ Configure / ❌ Avoid]
```

---

## Success Criteria (Multi-IDE)

### Required for All Supported IDEs

✅ **Settings Consistency:**
- All 15 core settings present and identical
- Python formatter set to `charliermarsh.ruff`
- Cache exclusions complete (`.venv`, `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`)

✅ **Format-on-Save Consistency:**
- Python file formatted in IDE A → open in IDE B → no changes
- No cross-IDE format conflicts

✅ **Workspace Integration:**
- `.vscode/settings.json` respected
- Tasks runnable (or equivalent)
- Terminal env vars loaded (PYTHONPATH, PROJECT_ROOT)

✅ **Development Discipline:**
- Daily wall check runnable (tests + lint)
- Ruff CLI integration working (`uv run ruff check`)

### IDE-Specific Criteria

**VS Code (Primary):**
- ✅ All 18 recommended extensions reviewed (critical ones installed)
- ✅ 14 tasks runnable
- ✅ Ctrl+Shift+B triggers daily wall check

**Cursor:**
- ✅ Settings match VS Code user settings
- ✅ Performance optimizations documented

**Windsurf:**
- ✅ `chat.agent.maxRequests = 35` configured
- ✅ Cascade AI respects THE GRID standards

**OpenCode:**
- ✅ Architecture documented (standalone/extension/fork)
- ✅ Clear recommendation (Use/Configure/Avoid)

**Antigravity:**
- ✅ Installation status confirmed
- ✅ If installed: 17 settings verified
- ✅ Clear recommendation (Use/Configure/Avoid)

---

## Priority Matrix

| IDE | Priority | Status | Action |
|-----|----------|--------|--------|
| **VS Code** | 🔴 **Critical** | ✅ Configured | Run comprehensive audit (reference implementation) |
| **Cursor** | 🟠 **High** | ⚠️ Partial | Verify settings match VS Code, test cross-IDE consistency |
| **Windsurf** | 🟠 **High** | ⚠️ Partial | Verify Cascade settings, test workspace integration |
| **OpenCode** | 🟡 **Medium** | ❓ Unknown | Determine viability, recommend Use/Configure/Avoid |
| **Antigravity** | 🟢 **Low** | ❓ Unknown | Determine if installed, recommend Use/Configure/Avoid |

---

## Quick Start

**To verify all IDEs:**

1. **VS Code** (30 minutes):
   ```bash
   # Copy VSCODE_AGENT_VERIFICATION_PROMPT.md prompt
   # Paste into GitHub Copilot Chat or Claude Code
   # Wait for comprehensive audit report
   # Fix gaps in priority order
   ```

2. **Cursor** (20 minutes):
   ```bash
   # Copy CURSOR_AGENT_VERIFICATION_PROMPT.md prompt
   # Paste into Cursor's Composer
   # Wait for gap analysis report
   # Sync settings to match VS Code
   ```

3. **Windsurf** (20 minutes):
   ```bash
   # Copy WINDSURF_AGENT_VERIFICATION_PROMPT.md prompt
   # Paste into Windsurf's Cascade AI
   # Wait for gap analysis report
   # Verify chat.agent.maxRequests = 35
   ```

4. **OpenCode** (15 minutes):
   ```bash
   # Copy OPENCODE_AGENT_VERIFICATION_PROMPT.md prompt
   # Run manual audit (or paste into OpenCode AI if available)
   # Determine: Use, Configure, or Avoid
   # Document recommendation
   ```

5. **Antigravity** (15 minutes):
   ```bash
   # Copy ANTIGRAVITY_AGENT_VERIFICATION_PROMPT.md prompt
   # Run discovery script (PowerShell)
   # If found: Verify 17 settings
   # If not found: Document as "not installed"
   ```

**Total estimated time:** 100 minutes (1.5 hours)

---

## Related Documentation

- [`IDE_SETUP_VERIFICATION.md`](./IDE_SETUP_VERIFICATION.md) — Post-setup verification checklist
- [`CONFIGURATION_OPTIMIZATION_SUMMARY.md`](./CONFIGURATION_OPTIMIZATION_SUMMARY.md) — Cursor optimization notes
- [`CROSS_DRIVE_CONFIG_INTEGRATION_FINDINGS.md`](./CROSS_DRIVE_CONFIG_INTEGRATION_FINDINGS.md) — Windsurf integration
- `E:\grid\CLAUDE.md` — Project standards and tech stack
- `E:\grid\.claude\rules\backend.md` — Python standards (ruff, mypy, line length)
- `E:\grid\.claude\rules\discipline.md` — Development discipline workflow
- `C:\Users\irfan\.claude\plans\prancy-jumping-torvalds.md` — Recent IDE setup plan

---

## Maintenance

**When to re-verify:**
- After IDE updates (major version bumps)
- After Windows/OS updates (settings might reset)
- When adding new developers (ensure consistent setup)
- When format conflicts appear (cross-IDE drift)
- Monthly (first Monday — per discipline.md)

**How to maintain:**
- VS Code remains reference implementation
- Changes to VS Code settings → propagate to other IDEs
- Document all cross-IDE settings in this index
- Run quick verification script monthly

---

**Last Updated:** 2026-02-12
**Status:** Documentation complete, verification pending for Cursor/Windsurf/OpenCode/Antigravity
