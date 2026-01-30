# MCP Servers Cheatsheet - GRID Workspace

Quick reference for using configured MCP servers in GRID.

## Server Capabilities

### 🌐 Fetch Server
- **Purpose**: Retrieve web content via HTTP/HTTPS URLs
- **Usage**: "Fetch [URL]" or "Get content from [URL]"
- **Examples**:
  - "Fetch https://api.github.com/repos/irfankabir02/GRID"
  - "Get the JSON from https://jsonplaceholder.typicode.com/posts/1"

### 📦 Git Server
- **Purpose**: Query git repository history and status
- **Usage**: Natural language git queries
- **Examples**:
  - "Show last 10 commits"
  - "Who modified scripts/mission_control.py?"
  - "List all branches"
  - "Show commit history for README.md"

### 🐙 GitHub Server
- **Purpose**: Interact with GitHub API (requires token in config)
- **Usage**: GitHub-specific queries
- **Examples**:
  - "List open issues in irfankabir02/GRID"
  - "Show pull requests from last week"
  - "Get repository stats"

### 🏗️ Grid-Core Server
- **Purpose**: Filesystem access to GRID codebase
- **Usage**: File operations on e:/grid
- **Examples**:
  - "Read .windsurf/structural-intelligence/grid-mission-control.json"
  - "List files in scripts/"
  - "Search for 'Mission Control' in all Python files"

### 🧠 Memory Server
- **Purpose**: Persistent memory across conversations
- **Usage**: Remember/recall information
- **Examples**:
  - "Remember: GRID uses Python 3.11"
  - "Recall the Mission Control configuration"
  - "Store: API key = [value]"

### 🤔 Sequential Thinking
- **Purpose**: Structured reasoning for complex problems
- **Usage**: "Use sequential thinking to analyze..."
- **Examples**:
  - "Use sequential thinking to debug this issue"
  - "Analyze the architecture step by step"

## Quick Start

1. **Test all servers**:
   ```
   Fetch a test URL, show git history, read a file, remember something, and use sequential thinking to analyze it all.
   ```

2. **Daily workflow**:
   ```
   Use git to see today's commits, read changed files, remember important changes, and summarize with sequential thinking.
   ```

3. **Mission Control integration**:
   ```
   Fetch external API status, check git for recent changes, read Mission Control reports, remember trends, and analyze health.
   ```

## Pro Tips

- **Chain operations**: "Fetch X, then parse with Y, then remember Z"
- **Cross-reference**: "Use git to find who wrote X, then read their other files"
- **Analysis**: "Use sequential thinking to connect A, B, and C"
- **Persistence**: Remember important decisions for future reference

## Configuration

MCP servers are configured in: `c:\Users\irfan\.codeium\windsurf\mcp_config.json`

To add GitHub token: Edit the `GITHUB_PERSONAL_ACCESS_TOKEN` field.

## Troubleshooting

- If fetch fails: Check URL and network
- If git fails: Ensure you're in a git repository
- If grid-core fails: Check file paths exist
- If memory seems lost: Ensure memory server is enabled
