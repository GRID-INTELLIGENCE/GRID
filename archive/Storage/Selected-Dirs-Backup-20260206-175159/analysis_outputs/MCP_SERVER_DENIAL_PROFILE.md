# MCP Server Denial Profile
**Generated:** 2026-02-02  
**Scope:** Total Deny - All MCP servers across all editor configurations  
**Status:** Active Enforcement

## Executive Summary
Comprehensive mapping of all MCP server instances across development environment, consolidated into unified denial profile. All servers marked for active denial with multi-layer enforcement (config sanitization, startup hooks, runtime monitoring).

## Server Inventory & Denial Mapping

### Server 1: grid-rag
**Risk Level:** CRITICAL (spawn failure, network-dependent, high resource)

| Attribute | Value |
|-----------|-------|
| Server Name | grid-rag |
| Category | rag-system |
| Primary Command | python |
| Port | 8000 |
| Spawn Variants | `python mcp-setup/server/grid_rag_mcp_server.py` (Grid), `py -3 e:\_projects\grid\mcp-setup\server\grid_rag_mcp_server.py` (Cursor) |
| Locations | E:\grid\mcp-setup\mcp_config.json, c:\Users\irfan\.cursor\mcp.json, E:\.worktrees\...\mcp_config.json |
| Current Status | DISABLED (E:\grid), ENABLED (Cursor) |
| Dependencies | python, chromadb, huggingface, ollama |
| Resource Profile | high |
| Priority | 8 |
| Denial Reason | startup-failure, network-dependent, spawn(python) → ENOENT |

---

### Server 2: grid-agentic
**Risk Level:** HIGH (spawn failure, network-dependent)

| Attribute | Value |
|-----------|-------|
| Server Name | grid-agentic |
| Category | agentic-workflow |
| Command | python |
| Port | 8004 |
| Spawn Variants | `python workspace/mcp/servers/agentic/server.py` |
| Locations | E:\grid\mcp-setup\mcp_config.json |
| Current Status | DISABLED |
| Dependencies | python |
| Resource Profile | medium |
| Priority | 7 |
| Denial Reason | startup-failure, spawn(python) → ENOENT |

---

### Server 3: memory
**Risk Level:** MEDIUM (spawn failure)

| Attribute | Value |
|-----------|-------|
| Server Name | memory |
| Category | memory-storage |
| Command | python |
| Port | 8003 |
| Spawn Variants | `python workspace/mcp/servers/memory/server.py` |
| Locations | E:\grid\mcp-setup\mcp_config.json |
| Current Status | DISABLED |
| Dependencies | python |
| Resource Profile | low |
| Priority | 6 |
| Denial Reason | startup-failure, spawn(python) → ENOENT |

---

### Server 4: grid-rag-enhanced
**Risk Level:** CRITICAL (spawn failure, network-dependent, high resource)

| Attribute | Value |
|-----------|-------|
| Server Name | grid-rag-enhanced |
| Category | rag-system |
| Command | python |
| Port | 8002 |
| Spawn Variants | `python -m grid.mcp.enhanced_rag_server` |
| Locations | E:\grid\mcp-setup\mcp_config.json, E:\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\mcp-setup\mcp_config.json |
| Current Status | DISABLED |
| Dependencies | python, chromadb, huggingface, ollama |
| Resource Profile | high |
| Priority | 9 |
| Denial Reason | startup-failure, spawn(python) → ENOENT |

---

### Server 5: grid-enhanced-tools
**Risk Level:** HIGH (spawn failure, tool execution)

| Attribute | Value |
|-----------|-------|
| Server Name | grid-enhanced-tools |
| Alias | enhanced-tools (Cursor) |
| Category | development-tools |
| Command | python |
| Port | 8001 |
| Spawn Variants | `python mcp-setup/server/enhanced_tools_mcp_server.py` (Grid), `py -3 e:\_projects\grid\mcp-setup\server\enhanced_tools_mcp_server.py` (Cursor) |
| Locations | E:\grid\mcp-setup\mcp_config.json, c:\Users\irfan\.cursor\mcp.json |
| Current Status | DISABLED (E:\grid), ENABLED (Cursor) |
| Dependencies | python |
| Resource Profile | medium |
| Priority | 5 |
| Denial Reason | startup-failure, spawn(python) → ENOENT |

---

### Server 6: portfolio-safety-lens
**Risk Level:** HIGH (network-dependent, currently enabled despite spawn issues)

| Attribute | Value |
|-----------|-------|
| Server Name | portfolio-safety-lens |
| Alias | portfolio-safety (Cursor) |
| Category | portfolio-analysis |
| Command | python |
| Port | 8005 |
| Spawn Variants | `python mcp-setup/server/portfolio_safety_mcp_server.py` (Grid), `py -3 e:\_projects\grid\mcp-setup\server\portfolio_safety_mcp_server.py` (Cursor) |
| Locations | E:\grid\mcp-setup\mcp_config.json, c:\Users\irfan\.cursor\mcp.json |
| Current Status | ENABLED (E:\grid), ENABLED (Cursor) ⚠️ VIOLATION |
| Dependencies | python, requests, pandas |
| Resource Profile | medium |
| Priority | High |
| Denial Reason | total deny scope - all MCP servers must be disabled |

---

## Path Variants & Normalization

### Grid Paths (Primary)
- `e:\grid\mcp-setup\mcp_config.json` → servers in `e:\grid` workspace
- `e:\grid\mcp-setup\server\*.py` → server scripts

### Cursor Paths (Editor)
- `c:\Users\irfan\.cursor\mcp.json` → Cursor IDE configuration
- `e:\_projects\grid\mcp-setup\server\*.py` → alternate project location
- Path prefix: `e:\_projects\grid\` = `e:\grid` (requires verification if symlink or duplicate)

### Worktree Paths (Branch-specific)
- `e:\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\mcp-setup\mcp_config.json`
- Servers in worktree-specific workspace

---

## Denylist Rules to Implement

### Rule 1: Deny All Grid RAG Servers
```json
{
  "name": "deny-grid-rag-servers",
  "reason": "spawn-failure-enoent",
  "scope": "global",
  "enabled": true,
  "matchAttributes": {
    "name": ["grid-rag", "grid-rag-enhanced"]
  }
}
```

### Rule 2: Deny All Grid Agentic Servers  
```json
{
  "name": "deny-grid-agentic",
  "reason": "spawn-failure-enoent",
  "scope": "global",
  "enabled": true,
  "matchAttributes": {
    "category": "agentic-workflow"
  }
}
```

### Rule 3: Deny All Grid Development Tools
```json
{
  "name": "deny-grid-dev-tools",
  "reason": "total-deny-scope",
  "scope": "global",
  "enabled": true,
  "matchAttributes": {
    "name": ["grid-enhanced-tools", "memory"]
  }
}
```

### Rule 4: Deny Portfolio Analysis Servers
```json
{
  "name": "deny-portfolio-servers",
  "reason": "total-deny-scope",
  "scope": "global",
  "enabled": true,
  "matchAttributes": {
    "name": ["portfolio-safety-lens"]
  }
}
```

### Rule 5: Deny All Python-based MCP Spawns
```json
{
  "name": "deny-python-mcp-spawns",
  "reason": "startup-failure",
  "scope": "global",
  "enabled": true,
  "matchAttributes": {
    "commandPattern": "(py|python).*mcp"
  }
}
```

---

## Enforcement Points

### 1. Configuration Sanitization
- **Target:** c:\Users\irfan\.cursor\mcp.json
- **Action:** Set `enabled: false` for all 3 servers
- **Metadata:** Add `_denylist_applied: true` and `_denylist_reason`

### 2. Startup Validation (PowerShell)
- **Script:** E:\scripts\validate_startup.ps1
- **Action:** Pre-launch scan of all MCP configs against denylist
- **Block:** Prevent editor startup if denied servers found enabled

### 3. Runtime Monitoring
- **System:** E:\wellness_studio\ai_safety\monitoring\spawn_monitor.py
- **Action:** Watch for unauthorized server re-enablement
- **Alert:** Log violations to E:\wellness_studio\ai_safety\logs\violation

---

## Compliance Checklist

- [ ] Step 1: Cursor mcp.json sanitized (all servers disabled)
- [ ] Step 2: E:\config\server_denylist.json extended with new rules
- [ ] Step 3: E:\grid\mcp-setup\mcp_config.json portfolio-safety-lens disabled
- [ ] Step 4: E:\scripts\validate_startup.ps1 enhanced with pre-launch checks
- [ ] Step 5: E:\wellness_studio\ai_safety\monitoring\spawn_monitor.py created
- [ ] Step 6: Audit logging configured in E:\wellness_studio\ai_safety\logs

---

## Version Control
- **Profile Version:** 1.0.0
- **Created:** 2026-02-02
- **Enforcement Status:** READY FOR IMPLEMENTATION
