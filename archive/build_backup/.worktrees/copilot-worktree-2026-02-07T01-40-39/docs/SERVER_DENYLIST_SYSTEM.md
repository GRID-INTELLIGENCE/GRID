# Server Denylist Management System

## Overview

This system provides machine-readable server categorization and denylist enforcement with attribute-based rules.

## Architecture

### Components

1. **Schema Definition** (`config/server_denylist_schema.json`)
   - JSON Schema for validation
   - Defines server categories, denylist reasons, and attributes
   - Machine-readable format for automation

2. **Configuration** (`config/server_denylist.json`)
   - Active denylist rules
   - Server inventory with attributes
   - Global settings

3. **Manager** (`scripts/server_denylist_manager.py`)
   - Python-based enforcement engine
   - Applies rules to MCP configurations
   - Generates reports

## Features

### Server Categories
- `web-based` - HTTP/web servers
- `database` - Database servers
- `mcp-server` - MCP protocol servers
- `rag-system` - RAG/vector database systems
- `agentic-workflow` - Agentic AI systems
- `development-tools` - Dev tooling servers
- `memory-storage` - In-memory data stores
- `api-gateway` - API gateway services
- `background-service` - Background workers

### Denylist Reasons
- `resource-intensive` - High CPU/memory usage
- `network-dependent` - Requires network connectivity
- `startup-failure` - Fails to start properly
- `missing-dependencies` - Missing required packages
- `security-concern` - Security vulnerabilities
- `deprecated` - Outdated/deprecated
- `redundant` - Duplicate functionality
- `development-only` - Dev environment only
- `user-disabled` - Manually disabled by user

### Server Attributes
Each server is catalogued with:
- **name**: Unique identifier
- **category**: Server classification
- **command**: Executable (python, node, etc.)
- **requiresNetwork**: Network dependency flag
- **requiresDatabase**: Database dependency flag
- **port**: Network port
- **dependencies**: Required packages
- **resourceProfile**: Resource consumption (low/medium/high/critical)
- **priority**: Importance level (0-10)

### Denylist Rule Types

#### 1. Name-Based Rules
```json
{
  "name": "grid-rag",
  "reason": "user-disabled",
  "scope": "workspace",
  "enabled": true
}
```

#### 2. Pattern-Based Rules
```json
{
  "pattern": ".*-test$",
  "reason": "development-only",
  "scope": "global",
  "enabled": true
}
```

#### 3. Attribute-Based Rules
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

#### 4. Combined Rules
```json
{
  "pattern": ".*",
  "matchAttributes": {
    "commandPattern": "^python$",
    "resourceProfile": ["high", "critical"]
  },
  "reason": "resource-intensive",
  "scope": "temporary",
  "enabled": false
}
```

## Usage

### Command Line Interface

#### Generate Report
```bash
python scripts/server_denylist_manager.py \
  --config config/server_denylist.json \
  --report
```

#### Check Specific Server
```bash
python scripts/server_denylist_manager.py \
  --config config/server_denylist.json \
  --check grid-rag
```

#### Apply to MCP Configuration
```bash
python scripts/server_denylist_manager.py \
  --config config/server_denylist.json \
  --mcp-config grid-rag-enhanced/mcp-setup/mcp_config.json \
  --output grid-rag-enhanced/mcp-setup/mcp_config.denied.json
```

### Python API

```python
from scripts.server_denylist_manager import ServerDenylistManager

# Initialize manager
manager = ServerDenylistManager('config/server_denylist.json')

# Check if server is denied
is_denied, reason = manager.is_denied('grid-rag')
if is_denied:
    print(f"Server denied: {reason}")

# Get all denied servers
denied = manager.get_denied_servers()
for name, reason in denied:
    print(f"{name}: {reason}")

# Apply to MCP config
manager.apply_to_mcp_config(
    'grid-rag-enhanced/mcp-setup/mcp_config.json',
    'output/mcp_config.json'
)

# Generate report
print(manager.generate_report())
```

## Drive-Wide Application

### Applying Rules Across Projects

The denylist system supports different scopes:

1. **Global** - Apply across all projects/workspaces
2. **Workspace** - Apply to current workspace only
3. **Project** - Apply to specific project
4. **Temporary** - Time-limited rules with `expiresAt`

### Example: Drive-Wide Web Server Denylist

```json
{
  "name": "deny-all-web-servers",
  "reason": "network-dependent",
  "scope": "global",
  "enabled": true,
  "matchAttributes": {
    "category": ["web-based", "api-gateway"],
    "requiresNetwork": true
  },
  "notes": "Block all web servers across E:\\ drive"
}
```

### Automation Script

Create a drive-wide enforcement script:

```python
# scripts/apply_denylist_drive_wide.py
import os
from pathlib import Path
from server_denylist_manager import ServerDenylistManager

def find_mcp_configs(root_path):
    """Find all MCP configs in drive"""
    configs = []
    for path in Path(root_path).rglob('**/mcp_config.json'):
        configs.append(path)
    return configs

def apply_drive_wide(denylist_config, root_path):
    """Apply denylist to all MCP configs"""
    manager = ServerDenylistManager(denylist_config)
    configs = find_mcp_configs(root_path)
    
    for config in configs:
        print(f"Processing: {config}")
        output = config.parent / 'mcp_config.denied.json'
        manager.apply_to_mcp_config(str(config), str(output))
        print(f"  ✓ Applied to: {output}\n")

if __name__ == '__main__':
    apply_drive_wide(
        'config/server_denylist.json',
        'E:\\'
    )
```

## Current Configuration

### Active Rules

1. **disable-web-servers** (ENABLED)
   - Blocks all web-based and API gateway servers
   - Reason: Network dependency

2. **disable-high-resource-servers** (DISABLED)
   - Would block high/critical resource servers
   - Reason: Resource intensive
   - Scope: Temporary

3. **disable-mcp-servers** (ENABLED)
   - Blocks all MCP servers
   - Reason: User disabled
   - Scope: Workspace

4. **disable-failed-python-spawns** (ENABLED)
   - Blocks servers with python spawn errors
   - Reason: Startup failure
   - Pattern: Python command errors (ENOENT)

### Server Inventory

| Server | Category | Port | Resource | Priority | Status |
|--------|----------|------|----------|----------|--------|
| grid-rag | rag-system | 8000 | high | 8 | DENIED |
| grid-agentic | agentic-workflow | 8004 | medium | 7 | DENIED |
| memory | memory-storage | 8003 | low | 6 | ALLOWED |
| grid-rag-enhanced | rag-system | 8002 | high | 9 | DENIED |
| grid-enhanced-tools | development-tools | 8001 | medium | 5 | ALLOWED |

## Integration with Existing Systems

### MCP Configuration
The denylist manager automatically:
- Sets `enabled: false` for denied servers
- Adds `_denylist_reason` field for tracking
- Preserves original configuration structure

### Monitoring Integration
```python
# Example: Log denylist events
def monitor_denylist_events(manager):
    denied = manager.get_denied_servers()
    for name, reason in denied:
        log_event({
            'event': 'server_denied',
            'server': name,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        })
```

## Extension Points

### Custom Categories
Add to schema's `serverCategory` enum:
```json
"serverCategory": {
  "type": "string",
  "enum": [..., "custom-category"]
}
```

### Custom Attributes
Extend `serverAttributes` in schema:
```json
"customAttribute": {
  "type": "string",
  "description": "Custom server attribute"
}
```

### Rule Plugins
Subclass `ServerDenylistManager` for custom logic:
```python
class CustomDenylistManager(ServerDenylistManager):
    def is_denied(self, server_name):
        # Custom logic
        base_result = super().is_denied(server_name)
        # Add custom checks
        return custom_result
```

## Best Practices

1. **Start Permissive**: Use `defaultAction: "allow"` initially
2. **Incremental Rules**: Add rules gradually to avoid breaking systems
3. **Document Reasons**: Always include `notes` field
4. **Use Temporary Scope**: Test with `temporary` scope first
5. **Regular Audits**: Review denied servers periodically
6. **Version Control**: Track denylist config in git
7. **Backup Configs**: Keep original MCP configs before applying denylist

## Troubleshooting

### Server Still Starting Despite Denylist
- Check `enabled: true` in denylist rule
- Verify rule matching logic with `--check` command
- Ensure MCP config was updated with `--apply` command

### Rule Not Matching
- Test pattern with regex tester
- Verify attribute names match exactly
- Check rule scope (global vs workspace)

### Performance Issues
- Use specific patterns instead of `.*`
- Reduce number of attribute checks
- Cache manager instance instead of recreating

## Future Enhancements

- [ ] Web UI for rule management
- [ ] Real-time monitoring dashboard
- [ ] Automated rule suggestions based on failures
- [ ] Integration with CI/CD pipelines
- [ ] Multi-environment rule sets
- [ ] Rule conflict detection
- [ ] Historical denylist analytics
