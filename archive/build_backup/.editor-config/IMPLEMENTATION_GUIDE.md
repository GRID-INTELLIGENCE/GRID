# Cross-Drive Workflow Integration: Implementation Guide

**Status**: ✓ Infrastructure Created  
**Date**: January 24, 2026  
**Last Updated**: January 24, 2026

---

## 📋 What's Been Set Up

### ✓ Directory Structure Created
```
E:\.editor-config\
├── vscode/
│   ├── settings.json              (Your baseline settings)
│   ├── mcp.json                   (MCP servers - to be deployed)
│   └── keybindings.json           (Will be added)
├── windsurf/
│   ├── settings.json              (Your custom Windsurf config)
│   ├── mcp.json                   (MCP servers - to be deployed)
│   └── keybindings.json           (Will be added)
├── shared/
│   ├── mcp-servers.json           (All MCP definitions)
│   ├── ollama-config.json         (Ollama setup)
│   └── github-sdk-config.json     (GitHub integration)
└── sync/
    └── config-sync.ps1            (PowerShell sync script)
```

### ✓ Configuration Files Created
- `mcp-servers.json` - Defines Ollama, GitHub, OPENCODE, Workspace MCP servers
- `ollama-config.json` - Ollama endpoint + model configuration
- `github-sdk-config.json` - GitHub SDK integration points
- `config-sync.ps1` - PowerShell script for pull/push/merge/compare operations

### ✓ Baseline Snapshots Captured
- `vscode_settings.json` (E:\) - Current VS Code configuration
- `windsurf_settings.json` (E:\) - Your Windsurf personal settings
- Both copied to `.editor-config\` subdirectories for version control

---

## 🚀 Next: Implementation Steps

### STEP 1: Create Environment File (2 min)

Copy and customize the environment template:

```bash
copy E:\.env.editor.template E:\.env.editor
```

Then edit `E:\.env.editor` and add:
- `GITHUB_TOKEN=ghp_...` (your GitHub token)
- Verify Ollama is running: `http://localhost:11434`

**✗ DO NOT COMMIT `.env.editor` to version control** (add to `.gitignore`)

### STEP 2: Verify Ollama Installation (3 min)

Check if Ollama is running and models are pulled:

```powershell
# Test Ollama endpoint
$response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -ErrorAction SilentlyContinue
$models = ($response.Content | ConvertFrom-Json).models
$models | ForEach-Object { Write-Host "Model: $($_.name)" }
```

**If Ollama not running:**
```powershell
# Start Ollama
ollama serve

# In another terminal, pull models
ollama pull mistral-nemo:latest
ollama pull claude
ollama pull neural-chat:latest
```

### STEP 3: Run Initial Configuration Sync (5 min)

Check current status before making changes:

```powershell
# Navigate to sync directory
cd E:\.editor-config\sync

# Check status (safe - read only)
.\config-sync.ps1 -Action status
```

Expected output:
```
✓ Windsurf settings (C:)
✓ VS Code settings (C:)
✓ Config repo (E:)
✓ Shared MCP config
✓ Ollama config
✓ Sync script
✓ Ollama is running. Available models:
  - mistral-nemo:latest
  - claude:latest
  - neural-chat:latest
```

### STEP 4: Pull Current Settings to Repository (5 min)

Capture both editors' current state:

```powershell
.\config-sync.ps1 -Action pull
```

This will:
- Backup existing files on C: drive
- Copy current VS Code settings to `E:\.editor-config\vscode\`
- Copy current Windsurf settings to `E:\.editor-config\windsurf\`

### STEP 5: Deploy MCP Servers (10 min)

Generate and deploy MCP configurations:

```powershell
.\config-sync.ps1 -Action merge
```

This creates:
- `E:\.editor-config\vscode\mcp.json` with all MCP server definitions
- `E:\.editor-config\windsurf\mcp.json` with all MCP server definitions

Then deploy to both editors:

```powershell
# Backup existing configs first
Backup-File "$env:USERPROFILE\AppData\Roaming\Code\User\mcp.json"
Backup-File "$env:USERPROFILE\AppData\Roaming\Windsurf\User\mcp.json"

# Copy MCP configs to editors
Copy-Item "E:\.editor-config\vscode\mcp.json" "$env:USERPROFILE\AppData\Roaming\Code\User\mcp.json" -Force
Copy-Item "E:\.editor-config\windsurf\mcp.json" "$env:USERPROFILE\AppData\Roaming\Windsurf\User\mcp.json" -Force
```

### STEP 6: Restart Editors (2 min)

Close and reopen both:
- **VS Code**: Close all windows, reopen
- **Windsurf**: Close all windows, reopen

VS Code will load the MCP configuration. You should see:
- "MCP" section in settings
- Available models: claude, mistral-nemo, neural-chat
- GitHub integration enabled

### STEP 7: Test Ollama Integration (5 min)

In VS Code or Windsurf:

1. Open Chat (Cmd+K on Mac, Ctrl+K on Windows)
2. Click model selector (should show Ollama models)
3. Select "Claude (via Ollama)"
4. Type test prompt: "Tell me about VS Code MCP servers"
5. Verify response comes from Ollama (no cloud connection needed)

### STEP 8: Enable GitHub SDK (optional, 10 min)

To use GitHub integration for repo discovery:

```powershell
# Test GitHub API connectivity
$token = (Get-Content E:\.env.editor | Select-String "GITHUB_TOKEN").ToString().Split("=")[1]
$headers = @{"Authorization" = "token $token"}
$response = Invoke-WebRequest -Uri "https://api.github.com/user" -Headers $headers
$response.Content | ConvertFrom-Json | Select-Object login
```

Then configure in your FastAPI backend ([harness_service.py](../Apps/backend/services/harness_service.py)):

```python
from github import Github
import os

github_token = os.getenv("GITHUB_TOKEN")
g = Github(github_token)

# Discover repos
for repo in g.get_user().get_repos():
    print(f"Found repo: {repo.name}")
```

### STEP 9: Set Up Scheduled Sync (optional, 5 min)

Create a PowerShell scheduled task to keep E: and C: drive in sync:

```powershell
# Create scheduled task to run config-sync pull every 4 hours
$TaskName = "VS Code Windsurf Config Sync"
$Trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Hours 4) -At 09:00 -Daily
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File E:\.editor-config\sync\config-sync.ps1 -Action pull"
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable

Register-ScheduledTask -TaskName $TaskName -Trigger $Trigger -Action $Action -Settings $Settings
```

---

## 🔄 Workflow Commands

### Daily Operations

```powershell
# Check status of all configurations
E:\.editor-config\sync\config-sync.ps1 -Action status

# Pull latest changes from C: to E: (backup first)
E:\.editor-config\sync\config-sync.ps1 -Action pull

# Compare current state vs repository
E:\.editor-config\sync\config-sync.ps1 -Action compare
```

### After Changing Settings

```powershell
# Save your custom settings to repository
E:\.editor-config\sync\config-sync.ps1 -Action pull

# Git commit your changes
cd E:\
git add .editor-config\
git commit -m "Update editor configuration"
```

### Deploying Configuration to New Machine

```powershell
# Set up new environment
copy E:\.env.editor.template E:\.env.editor
# (edit E:\.env.editor with new machine's paths)

# Deploy all settings
E:\.editor-config\sync\config-sync.ps1 -Action push -Force
```

---

## 🎯 Verification Checklist

- [ ] `.env.editor` created with GITHUB_TOKEN and OLLAMA settings
- [ ] Ollama running at http://localhost:11434
- [ ] `config-sync.ps1 -Action status` shows all ✓ checks
- [ ] Ran `config-sync.ps1 -Action pull` successfully
- [ ] Ran `config-sync.ps1 -Action merge` to generate MCP configs
- [ ] Deployed MCP configs to VS Code & Windsurf
- [ ] Restarted both editors
- [ ] Can see Ollama models in chat/MCP selector
- [ ] Test prompt works with Claude/Mistral in offline mode
- [ ] GitHub integration enabled (optional)

---

## 🐛 Troubleshooting

### "Ollama not accessible"
- Verify Ollama is running: `ollama serve`
- Check endpoint: `curl http://localhost:11434/api/tags`
- Ensure models are pulled: `ollama list`

### "MCP servers not appearing in VS Code"
- Restart VS Code completely (close all windows)
- Check `mcp.json` exists at `$APPDATA\Code\User\mcp.json`
- Verify JSON syntax: `Test-Json (Get-Content $path)`

### "GitHub API fails"
- Verify token is valid: `gh auth status`
- Check token scopes: https://github.com/settings/tokens
- Ensure `.env.editor` has correct `GITHUB_TOKEN`

### "Config sync script permission denied"
- Run PowerShell as Administrator
- Set execution policy: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

---

## 📚 Additional Resources

- [VS Code MCP Documentation](https://modelcontextprotocol.io/)
- [Ollama Models Library](https://ollama.com/library)
- [GitHub API Reference](https://docs.github.com/en/rest)
- [PowerShell Configuration Management](https://docs.microsoft.com/en-us/powershell/scripting)

---

## 🎉 What's Next

After completing these steps:

1. **Enhance the Harness Service**: Integrate GitHub SDK for automated repo discovery
2. **Build OPENCODE Integration**: Add semantic search to your orchestrator UI
3. **Claude Code Workflow**: Use offline Claude for sensitive analysis without cloud upload
4. **Cross-Device Sync**: Extend this framework to sync settings across machines via GitHub

You now have a **master configuration hub** at E:\.editor-config that controls both VS Code and Windsurf, with Ollama-powered offline LLM access!
