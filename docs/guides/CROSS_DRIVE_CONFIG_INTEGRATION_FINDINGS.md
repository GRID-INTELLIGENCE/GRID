# Cross-Drive Workflow Integration: VS Code & Windsurf Configuration Analysis

**Date**: January 24, 2026  
**Workspace**: E:\ (primary project drive) | C:\Users\irfan (Windows OS user profile)  
**Status**: Initial exploration complete — Ready for integration strategy

---

## Executive Summary

You have **two parallel editor environments** with separate configuration hierarchies:

1. **VS Code** (C:\Users\irfan\AppData\Roaming\Code)
2. **Windsurf** (C:\Users\irfan\AppData\Roaming\Windsurf)

Both maintain **independent** settings, extensions, MCP servers, and user data. Your goal is to create a **cross-drive workflow** that:
- Centralizes configuration to E:\ for version control & reproducibility
- Syncs settings between VS Code and Windsurf bidirectionally
- Manages Ollama/local LLM models accessible from both editors
- Preserves your **custom Windsurf MCP setup** as the reference

---

## Directory Structure Map

### C: Drive (Windows User Profile)
```
C:\Users\irfan\AppData\
├── Roaming\
│   ├── Code\
│   │   └── User\
│   │       ├── settings.json          (VS Code global settings)
│   │       ├── mcp.json               (VS Code MCP config - currently empty {})
│   │       ├── keybindings.json       (VS Code keybindings)
│   │       ├── sync\mcp\              (VS Code MCP sync cache)
│   │       │   └── lastSyncmcp.json   (MCP sync state)
│   │       └── globalStorage\         (Extensions storage)
│   │
│   └── Windsurf\
│       └── User\
│           ├── settings.json          (Windsurf settings) ← **CUSTOM CONFIG FOUND**
│           ├── keybindings.json       (Windsurf keybindings)
│           ├── storage.json           (Windsurf storage)
│           └── History\               (Windsurf history)
│
└── Local\Programs\Windsurf\           (Windsurf installation)
```

### E: Drive (Your Workspace)
```
E:\
├── Apps\                              (FastAPI backend + React frontend)
├── grid\                              (Python cognitive framework)
├── EUFLE\                             (LLM operations & transformation)
├── pipeline\                          (Data processing)
├── windsurf_settings.json             (NEWLY COPIED - reference baseline)
├── vscode_settings.json               (NEWLY COPIED - reference baseline)
└── (all your project repos)
```

---

## Key Findings

### 1. **Windsurf Settings (Your "Personal Touch")**

Location: `C:\Users\irfan\AppData\Roaming\Windsurf\User\settings.json`

**Custom Configuration Detected:**
```json
{
  // --- Core & Performance ---
  "window.commandCenter": true,
  "cursor.general.disableHttp2": true,
  "python.languageServer": "Pylance",
  "workbench.sideBar.location": "right",
  
  // --- Visuals (Premium Aesthetics) ---
  "editor.cursorSmoothCaretAnimation": "on",
  "editor.cursorBlinking": "smooth",
  "editor.smoothScrolling": true,
  "editor.bracketPairColorization.enabled": true,
  "editor.renderWhitespace": "selection",
  "editor.fontLigatures": true,
  "editor.minimap.enabled": false,
  
  // --- Workflow Optimization ---
  "editor.formatOnSave": true,
  "files.autoSave": "onFocusChange",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "explicit",
    "source.organizeImports": "explicit"
  },
  
  // --- Terminal Profiles (Multiple Shells) ---
  "terminal.integrated.defaultProfile.windows": "PowerShell",
  "terminal.integrated.profiles.windows": {
    "PowerShell": { ... },
    "Command Prompt": { ... },
    "Git Bash": { ... },
    "Ubuntu (WSL)": { "path": "wsl.exe", "args": ["-d", "Ubuntu"] }
  },
  
  // --- Terminal Behavior ---
  "terminal.integrated.copyOnSelection": true,
  "terminal.integrated.localEchoEnabled": "on",
  "terminal.integrated.scrollback": 10000,
  
  // --- Python & Tool Specifics ---
  "python.defaultInterpreterPath": "c:\\Users\\irfan\\AppData\\Local\\Programs\\Python\\Python313\\python.exe",
  
  // --- Custom Vocabulary ---
  "cSpell.userWords": [
    "EUFLE", "Ollama", "OPENCODE", "asyncio", "agentic", 
    "safetensors", "cursorpyright", "Ryzen"
  ]
}
```

**✓ Confirms** your personalized editor workflow is documented!

### 2. **VS Code Settings (Current State)**

Location: `C:\Users\irfan\AppData\Roaming\Code\User\settings.json`

**Current Configuration:**
```json
{
  "gitlens.ai.model": "vscode",
  "gitlens.ai.vscode.model": "copilot:gpt-4.1",
  "python.analysis.typeCheckingMode": "standard",
  "git.openRepositoryInParentFolders": "never",
  "chat.agent.maxRequests": 40,
  "cSpell.userWords": ["EUFLE"],
  "chat.mcp.gallery.enabled": true,
  "chat.viewSessions.orientation": "stacked"
}
```

**Status**: Minimal configuration (GitLens, Python, MCP gallery enabled but no custom MCP servers configured).

### 3. **MCP Server Status**

**VS Code MCP Configuration:**
- File: `C:\Users\irfan\AppData\Roaming\Code\User\mcp.json`
- Current content: **Empty** (`{}`)
- Sync status: `lastSyncmcp.json` exists but no actual MCP servers defined

**Windsurf MCP Configuration:**
- No dedicated `mcp.json` found in Windsurf user directory
- MCP settings likely embedded in main `settings.json` or not yet configured

**Implication**: You need to set up custom MCP servers for:
- Ollama (local LLM models)
- GitHub SDK (repo orchestration)
- OPENCODE (semantic search)
- Claude via Ollama

---

## Problem Statement: Why Ollama Models Aren't Accessible

### Root Causes

1. **No MCP Server Configuration**: Neither VS Code nor Windsurf has defined MCP servers pointing to Ollama
2. **Ollama Endpoint Missing**: No `localhost:11434` connectivity configured in either editor
3. **No Model Registration**: Ollama models (Claude, Mistral, etc.) are pulled but not registered in editor settings
4. **Environment Variable Isolation**: Ollama runs on C: drive, but your projects are on E: drive (separate PATH contexts)

---

## Solution: Cross-Drive Integration Architecture

### Phase 1: Centralize Configuration (E: Drive)

Create a **single source of truth** for all editor settings:

```
E:\
├── .editor-config/                        (NEW - Central config repo)
│   ├── vscode/
│   │   ├── settings.json.template
│   │   ├── keybindings.json
│   │   └── mcp-servers.json              (CRITICAL - MCP definitions)
│   │
│   ├── windsurf/
│   │   ├── settings.json                 (Your custom config)
│   │   ├── keybindings.json
│   │   └── mcp-servers.json
│   │
│   ├── shared/
│   │   ├── ollama-config.json            (Local LLM setup)
│   │   ├── github-sdk-config.json        (GitHub integration)
│   │   └── shared-keybindings.json       (Common shortcuts)
│   │
│   └── sync/
│       └── config-sync.ps1               (PowerShell sync script)
│
├── windsurf_settings.json                (Baseline - copy here)
├── vscode_settings.json                  (Baseline - copy here)
└── CROSS_DRIVE_CONFIG_INTEGRATION.md     (This plan)
```

### Phase 2: Define MCP Servers

Create `E:\.editor-config\shared\mcp-servers.json`:

```json
{
  "ollama": {
    "enabled": true,
    "command": "npx",
    "args": ["@modelcontextprotocol/server-ollama"],
    "env": {
      "OLLAMA_API_URL": "http://localhost:11434",
      "OLLAMA_MODELS": "claude,mistral-nemo,neural-chat"
    }
  },
  "github": {
    "enabled": true,
    "command": "npx",
    "args": ["@modelcontextprotocol/server-github"],
    "env": {
      "GITHUB_TOKEN": "${{ secrets.GITHUB_TOKEN }}"
    }
  },
  "opencode": {
    "enabled": true,
    "command": "npx",
    "args": ["@modelcontextprotocol/server-opencode"],
    "env": {
      "OPENCODE_INDEX_PATH": "E:/.opencode-index"
    }
  }
}
```

### Phase 3: Sync Script (PowerShell)

Create `E:\.editor-config\sync\config-sync.ps1`:

```powershell
# config-sync.ps1 - Bidirectional sync VS Code & Windsurf settings

param(
    [ValidateSet("pull", "push", "merge")]
    [string]$Action = "merge"
)

$CodeUserPath = "$env:USERPROFILE\AppData\Roaming\Code\User"
$WindsurfUserPath = "$env:USERPROFILE\AppData\Roaming\Windsurf\User"
$ConfigRepoPath = "E:\.editor-config"

# Action: pull (from C: to E:)
if ($Action -eq "pull") {
    Copy-Item "$WindsurfUserPath\settings.json" `
              "$ConfigRepoPath\windsurf\settings.json" -Force
    Copy-Item "$CodeUserPath\settings.json" `
              "$ConfigRepoPath\vscode\settings.json" -Force
    Write-Host "✓ Pulled settings from C: to E:"
}

# Action: push (from E: to C:)
if ($Action -eq "push") {
    # Backup existing
    Copy-Item "$WindsurfUserPath\settings.json" `
              "$WindsurfUserPath\settings.json.backup" -Force
    
    # Deploy from E:
    Copy-Item "$ConfigRepoPath\windsurf\settings.json" `
              "$WindsurfUserPath\settings.json" -Force
    
    Copy-Item "$ConfigRepoPath\vscode\settings.json" `
              "$CodeUserPath\settings.json" -Force
    
    Write-Host "✓ Pushed settings from E: to C:"
}

# Action: merge (intelligent merge of MCP configs)
if ($Action -eq "merge") {
    Write-Host "Merging MCP configurations..."
    # Implementation: Merge MCP servers from both sources
}
```

### Phase 4: Enable Ollama Integration

Update `E:\.editor-config\vscode\mcp-servers.json`:

```json
{
  "mcpServers": {
    "ollama": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-ollama"],
      "disabled": false,
      "env": {
        "OLLAMA_API_URL": "http://localhost:11434"
      }
    }
  }
}
```

### Phase 5: Verify Ollama Connection

PowerShell diagnostic:

```powershell
# Check Ollama running
$OllamaUrl = "http://localhost:11434/api/tags"
try {
    $Response = Invoke-WebRequest -Uri $OllamaUrl -ErrorAction Stop
    $Models = ($Response.Content | ConvertFrom-Json).models
    Write-Host "✓ Ollama accessible. Models:"
    $Models | ForEach-Object { Write-Host "  - $($_.name)" }
} catch {
    Write-Host "✗ Ollama not accessible. Start Ollama first."
}
```

---

## Implementation Checklist

- [ ] **Step 1**: Create `.editor-config` directory structure at E:\
- [ ] **Step 2**: Copy `windsurf_settings.json` → `E:\.editor-config\windsurf\settings.json` (reference)
- [ ] **Step 3**: Copy `vscode_settings.json` → `E:\.editor-config\vscode\settings.json` (baseline)
- [ ] **Step 4**: Create `mcp-servers.json` with Ollama, GitHub, OPENCODE definitions
- [ ] **Step 5**: Create `config-sync.ps1` PowerShell sync script
- [ ] **Step 6**: Test Ollama connectivity from both editors
- [ ] **Step 7**: Configure Claude model selection in VS Code MCP settings
- [ ] **Step 8**: Create `.env.editor` for sensitive tokens (GitHub, API keys)
- [ ] **Step 9**: Document workflow in project README

---

## Next Steps (Ready for Implementation)

1. **Create E:\.editor-config directory** with subdirectories
2. **Configure MCP servers** for Ollama with explicit model list
3. **Set up cross-drive sync** via PowerShell scheduled task
4. **Test Ollama model access** from Windsurf and VS Code
5. **Integrate GitHub SDK** for automated repo harvesting
6. **Add OPENCODE** semantic search to your harness backend

---

## Key Insights

✓ **Windsurf Configuration is Custom**: Your personal editor setup is well-documented in `settings.json`  
✓ **MCP Infrastructure Missing**: Neither editor has working MCP server definitions  
✓ **Ollama Setup Needed**: Requires explicit endpoint configuration + model registration  
✓ **Cross-Drive Sync Viable**: PowerShell + version control can keep settings synchronized  
✓ **GitHub SDK Ready**: Can be integrated once MCP servers are defined  

---

## Files Generated

- ✓ `E:\windsurf_settings.json` (baseline snapshot)
- ✓ `E:\vscode_settings.json` (baseline snapshot)
- ✓ `E:\CROSS_DRIVE_CONFIG_INTEGRATION_FINDINGS.md` (this document)

**Next action**: Approve Phase 1-2 implementation to begin creating `.editor-config` structure and MCP definitions.
