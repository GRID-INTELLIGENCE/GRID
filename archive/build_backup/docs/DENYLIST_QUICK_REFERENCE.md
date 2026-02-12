# Server Denylist Quick Reference

## Quick Start

### 1. Generate Report
```bash
python scripts/server_denylist_manager.py --config config/server_denylist.json --report
```

### 2. Check Server Status
```bash
python scripts/server_denylist_manager.py --config config/server_denylist.json --check <server-name>
```

### 3. Apply to Single Config
```bash
python scripts/server_denylist_manager.py \
  --config config/server_denylist.json \
  --mcp-config <path-to-mcp-config> \
  --output <output-path>
```

### 4. Apply Drive-Wide (Dry Run)
```bash
python scripts/apply_denylist_drive_wide.py \
  --config config/server_denylist.json \
  --root E:\ \
  --dry-run
```

### 5. Apply Drive-Wide (Live)
```bash
python scripts/apply_denylist_drive_wide.py \
  --config config/server_denylist.json \
  --root E:\
```

### 6. Restore Backups
```bash
python scripts/apply_denylist_drive_wide.py \
  --config config/server_denylist.json \
  --restore
```

## Rule Types Cheat Sheet

### Deny by Name
```json
{
  "name": "server-name",
  "reason": "user-disabled",
  "scope": "workspace",
  "enabled": true
}
```

### Deny by Category
```json
{
  "matchAttributes": {
    "category": ["web-based", "api-gateway"]
  },
  "reason": "network-dependent",
  "scope": "global",
  "enabled": true
}
```

### Deny by Pattern
```json
{
  "pattern": ".*-test$",
  "reason": "development-only",
  "scope": "project",
  "enabled": true
}
```

### Deny by Resource Profile
```json
{
  "matchAttributes": {
    "resourceProfile": ["high", "critical"]
  },
  "reason": "resource-intensive",
  "scope": "temporary",
  "enabled": false
}
```

### Deny by Command
```json
{
  "matchAttributes": {
    "commandPattern": "^python$"
  },
  "reason": "startup-failure",
  "scope": "global",
  "enabled": true
}
```

### Deny by Network Requirement
```json
{
  "matchAttributes": {
    "requiresNetwork": true
  },
  "reason": "network-dependent",
  "scope": "global",
  "enabled": true
}
```

## Server Categories

| Category | Description | Example |
|----------|-------------|---------|
| `web-based` | HTTP/web servers | nginx, apache |
| `database` | Database servers | postgres, mongodb |
| `mcp-server` | MCP protocol servers | grid-mcp |
| `rag-system` | RAG/vector DBs | grid-rag |
| `agentic-workflow` | Agentic AI | grid-agentic |
| `development-tools` | Dev tools | linters, formatters |
| `memory-storage` | In-memory stores | redis, memcached |
| `api-gateway` | API gateways | kong, traefik |
| `background-service` | Background workers | celery, sidekiq |

## Denylist Reasons

| Reason | Use Case |
|--------|----------|
| `resource-intensive` | High CPU/memory usage |
| `network-dependent` | Requires network |
| `startup-failure` | Fails to start |
| `missing-dependencies` | Missing packages |
| `security-concern` | Security issue |
| `deprecated` | Outdated |
| `redundant` | Duplicate functionality |
| `development-only` | Dev environment only |
| `user-disabled` | Manually disabled |

## Scopes

| Scope | Description |
|-------|-------------|
| `global` | All projects/workspaces |
| `workspace` | Current workspace only |
| `project` | Specific project |
| `temporary` | Time-limited (use `expiresAt`) |

## Common Patterns

### Disable All Web Servers
```json
{
  "matchAttributes": {
    "category": ["web-based", "api-gateway"],
    "requiresNetwork": true
  },
  "reason": "network-dependent",
  "scope": "global",
  "enabled": true
}
```

### Disable Failed Python Spawns
```json
{
  "pattern": ".*",
  "matchAttributes": {
    "commandPattern": "^python$"
  },
  "reason": "startup-failure",
  "scope": "global",
  "enabled": true
}
```

### Disable High Resource Servers
```json
{
  "matchAttributes": {
    "resourceProfile": ["high", "critical"]
  },
  "reason": "resource-intensive",
  "scope": "temporary",
  "enabled": true,
  "expiresAt": "2026-02-15T00:00:00Z"
}
```

### Disable Test Servers
```json
{
  "pattern": ".*-test$",
  "reason": "development-only",
  "scope": "project",
  "enabled": true
}
```

## File Locations

- **Schema**: `config/server_denylist_schema.json`
- **Config**: `config/server_denylist.json`
- **Manager**: `scripts/server_denylist_manager.py`
- **Drive-Wide**: `scripts/apply_denylist_drive_wide.py`
- **Test Script**: `scripts/test_denylist.bat`
- **Documentation**: `docs/SERVER_DENYLIST_SYSTEM.md`

## Python API Examples

### Basic Usage
```python
from scripts.server_denylist_manager import ServerDenylistManager

manager = ServerDenylistManager('config/server_denylist.json')

# Check server
is_denied, reason = manager.is_denied('grid-rag')

# Get all denied
denied = manager.get_denied_servers()

# Apply to config
manager.apply_to_mcp_config('mcp_config.json', 'output.json')
```

### Drive-Wide Application
```python
from scripts.apply_denylist_drive_wide import DriveWideEnforcer

enforcer = DriveWideEnforcer(
    'config/server_denylist.json',
    'E:\\'
)

# Dry run first
results = enforcer.apply_drive_wide(dry_run=True)

# Then apply for real
results = enforcer.apply_drive_wide(dry_run=False)

# Restore if needed
enforcer.restore_backups()
```

## Troubleshooting

### Rule Not Matching?
```bash
# Check pattern
python scripts/server_denylist_manager.py --config config/server_denylist.json --check <server-name>

# Verify attributes in inventory
cat config/server_denylist.json | grep -A 10 "<server-name>"
```

### Backup Not Created?
- Backups only created on first run
- Check for `*.backup.json` in config directory
- Use `--restore` to revert changes

### Python Not Found?
- Ensure Python is in PATH
- Use full path: `C:\Python39\python.exe`
- Check `python --version`

## Best Practices

1. ✅ Always use `--dry-run` first
2. ✅ Start with `scope: "temporary"`
3. ✅ Document with `notes` field
4. ✅ Keep backups of original configs
5. ✅ Version control denylist config
6. ✅ Test individual servers before drive-wide
7. ✅ Review report before applying

## Current Active Rules

From `config/server_denylist.json`:

1. ✅ **disable-web-servers** - Blocks web-based/API gateways
2. ❌ **disable-high-resource-servers** - Disabled (temporary)
3. ✅ **disable-mcp-servers** - Blocks MCP servers (workspace)
4. ✅ **disable-failed-python-spawns** - Blocks python spawn errors

## Next Steps

1. Run test script: `scripts\test_denylist.bat`
2. Review report output
3. Adjust rules in `config/server_denylist.json`
4. Apply to single config first
5. Then apply drive-wide with `--dry-run`
6. Finally apply live changes
