# MCP Servers Demo - GRID Workspace

This demo showcases the configured MCP servers and their capabilities.

## Available MCP Servers

1. **fetch** - Fetch web content via URLs
2. **git** - Git repository operations and history
3. **github** - GitHub API interactions
4. **grid-core** - Filesystem access to GRID codebase
5. **memory** - Persistent memory storage
6. **sequential-thinking** - Structured reasoning

## Demo Commands

Try these prompts to see each MCP server in action:

### 1. Fetch Server
```
Fetch the latest release notes from https://api.github.com/repos/openai/openai-python/releases/latest
```

### 2. Git Server
```
Show me the last 5 commits to the main branch with author and message
```

### 3. GitHub Server
```
List the open issues in the irfankabir02/GRID repository
```

### 4. Grid-Core Server
```
Read the contents of scripts/mission_control.py and show me the main function
```

### 5. Memory Server
```
Remember: The GRID project uses Mission Control for structural intelligence
```

Then later:
```
Recall what you know about GRID's Mission Control
```

### 6. Sequential Thinking
```
Use sequential thinking to analyze how Mission Control integrates with the GRID architecture
```

## Advanced Demo: Multi-Server Workflow

```
1. Fetch the JSON from https://api.github.com/repos/irfankabir02/GRID/contents/package.json
2. Parse the dependencies and remember them
3. Use git to check if any dependency-related files changed in the last week
4. Provide a summary using sequential thinking
```

## Tips for Using MCP

- MCP servers are automatically invoked when you ask for relevant operations
- No special syntax needed - just ask naturally!
- The memory server persists across conversations
- Sequential thinking helps with complex analysis
- Grid-core provides direct file access to the entire workspace

## Example Integration

Here's how MCP enhances Mission Control:

```
Use git to analyze recent commit activity, then use sequential thinking to identify patterns, and finally remember the analysis for future reference in Mission Control reports.
```
