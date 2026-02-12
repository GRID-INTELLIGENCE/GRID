# OpenCode CLI Usage Guide

Quick reference for using OpenCode CLI in the workspace.

## Current Status

⚠️ **OpenCode has runtime/dependency issues**

- OpenCode source cloned to `/mnt/c/Users/irfan/opencode`
- Requires Bun runtime (installed)
- Wrapper scripts created but OpenCode binary fails to run
- **Recommendation**: Use existing Claude/Claude Code integration for now
- **Alternative**: Direct API calls via Anthropic/OpenAI SDKs

### Workaround

If you need model experimentation:
- Use Claude Code directly in Cascade (recommended - already working)
- Use Anthropic API via Python SDK (see example below)
- Use OpenAI API via Python SDK

## Known Issues

### Runtime Errors

OpenCode currently fails with:
- Dependency conflicts
- Bun runtime errors
- Module resolution issues

### Workaround Status

The wrapper scripts (`opencode_wrapper.sh` and `opencode_wrapper.ps1`) have been updated to:
- Check for Bun installation
- Use correct OpenCode path
- Handle Windows/WSL path conversion

However, OpenCode binary itself still fails to run.

## Alternatives

### Alternative 1: Direct Claude Code Integration (Recommended)

**Description**: Use Claude Code directly within Cascade (no separate CLI needed)

**Benefits**:
- Already working
- No additional setup required
- Best Cascade integration

**Usage**: Simply use Claude Code directly in Cascade - no additional commands needed.

### Alternative 2: Python SDK Wrapper

Use Anthropic or OpenAI Python SDKs for model experimentation:

```python
# Example: Using Anthropic SDK
from anthropic import Anthropic

client = Anthropic(api_key="your-api-key")
response = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Explain Python async/await"}]
)

print(response.content[0].text)
```

### Alternative 3: Wait for OpenCode Stability

Monitor OpenCode repository for fixes:
- Check OpenCode GitHub issues
- Wait for stable release
- Test again when fixed

## Installation

### WSL2 (Recommended)

```bash
# Install via wrapper script
wsl bash e:/scripts/opencode_wrapper.sh --version

# Or install directly
curl -sSL https://opencode.dev/install | bash
```

### Windows PowerShell

```powershell
# Use wrapper script
.\scripts\opencode_wrapper.ps1 --version
```

## Basic Usage

### Check Version

```bash
opencode --version
```

### List Available Models

```bash
opencode models list
```

### Query a Model

```bash
# Using Claude
opencode query "What is Python?" --model claude

# Using GPT
opencode query "Explain TypeScript" --model gpt-4

# Using local model
opencode query "How does caching work?" --model ollama/mistral
```

## Integration with Workspace

### VS Code Terminal

Add to VS Code tasks.json for quick access:

```json
{
    "label": "OpenCode Query",
    "type": "shell",
    "command": "wsl bash ${workspaceFolder}/scripts/opencode_wrapper.sh",
    "args": ["query", "${input:opencodeQuery}", "--model", "claude"]
}
```

### Environment Variables

```bash
# Set default model
export OPENCODE_DEFAULT_MODEL=claude

# Set API key (if needed)
export OPENCODE_API_KEY=your_key_here
```

## Cost Optimization

OpenCode provides:

- **Free tier**: Limited queries per day
- **Provider flexibility**: Switch between Claude, GPT, and local models
- **Cost transparency**: See usage and costs per provider

## Cascade Integration

OpenCode outputs are JSON-compatible for Cascade parsing:

```bash
opencode query "Analyze this code" --format json > output.json
```

## Common Patterns

### Model Comparison

```bash
# Compare responses from different models
opencode query "Explain async/await" --model claude > claude_response.txt
opencode query "Explain async/await" --model gpt-4 > gpt4_response.txt
```

### Batch Processing

```bash
# Process multiple queries
for query in "Python" "TypeScript" "React"; do
    opencode query "$query best practices" --model claude >> results.txt
done
```

## Troubleshooting

### WSL2 Path Issues

If paths don't resolve correctly, use absolute WSL paths:

```bash
# Convert Windows path to WSL path
# E:\project\code.py -> /mnt/e/project/code.py
```

### API Key Not Found

Ensure API keys are set in WSL environment:

```bash
# Add to ~/.bashrc or ~/.zshrc
export OPENAI_API_KEY=your_key
export ANTHROPIC_API_KEY=your_key
```

## Further Reading

- [OpenCode Documentation](https://opencode.dev/docs)
- [Model Provider Setup](https://opencode.dev/docs/providers)
- [API Reference](https://opencode.dev/docs/api)