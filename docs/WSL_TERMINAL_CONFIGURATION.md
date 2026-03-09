# WSL Terminal Configuration Guide

## Context

When opening a project folder via WSL (e.g., "Open Folder in WSL" or `code .` from WSL), VS Code/Cursor runs in **Remote – WSL context**. This has important implications for terminal configuration.

## Key Findings

### Terminal Profile Selection

| Window Context              | Setting Used                                 | Profile Examples           |
| --------------------------- | -------------------------------------------- | -------------------------- |
| Windows (C:\Users\...)      | `terminal.integrated.defaultProfile.windows` | PowerShell, Command Prompt |
| WSL Remote (/home/user/...) | `terminal.integrated.defaultProfile.linux`   | bash, zsh, fish            |

**Important:** When in WSL Remote context, `defaultProfile.windows` is **ignored**. The integrated terminal is always a Linux terminal (WSL).

### Python Interpreter Path

| Context         | Virtual Environment Path   |
| --------------- | -------------------------- |
| Windows         | `.venv/Scripts/python.exe` |
| WSL/Linux       | `.venv/bin/python`         |
| **Both (auto)** | `${workspaceFolder}/.venv` |

**Note:** Setting `python.defaultInterpreterPath` to `${workspaceFolder}/.venv` lets VS Code's Python extension auto-detect the correct binary (`bin/python` on Linux, `Scripts/python.exe` on Windows) regardless of which context the window is opened in.

### PYTHONPATH Separator

| OS        | Separator       | Example             |
| --------- | --------------- | ------------------- |
| Windows   | `;` (semicolon) | `path1;path2;path3` |
| Linux/WSL | `:` (colon)     | `path1:path2:path3` |

## Configuration Changes

The `.vscode/settings.json` has been updated with explicit bash profile configuration for WSL:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv",

  "terminal.integrated.profiles.linux": {
    "bash": {
      "path": "/bin/bash",
      "args": ["-l"],
      "icon": "terminal-bash"
    }
  },
  "terminal.integrated.defaultProfile.linux": "bash",
  "terminal.integrated.defaultProfile.windows": "PowerShell",

  "terminal.integrated.env.windows": {
    "PYTHONPATH": "${workspaceFolder}/src;${workspaceFolder}/safety;..."
  },
  "terminal.integrated.env.linux": {
    "PYTHONPATH": "${workspaceFolder}/src:${workspaceFolder}/safety:..."
  }
}
```

### Why Explicit Profile Definition?

Explicitly defining the bash profile ensures:

- **Consistency**: Uses `/bin/bash` directly, avoiding shell wrapper issues
- **Login shell**: `-l` flag ensures `.bashrc` and `.bash_profile` are loaded
- **Predictability**: No ambiguity about which bash binary is used
- **Stability**: Prevents UTF-16 encoding issues from shell wrappers

## Troubleshooting

### Symptom: Commands Fail with "Invalid command line argument: -c"

This error with UTF-16 spacing in output indicates:

1. The shell wrapper is injecting incorrect flags
2. Commands are being routed through WSL incorrectly
3. Terminal profile mismatch between window context and settings

**Fix:** Ensure `terminal.integrated.defaultProfile.linux` is set when working in WSL Remote context.

### Symptom: "uv: command not found"

UV must be installed in the WSL environment, not just Windows.

**Fix:**

```bash
# In WSL terminal
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Symptom: Python interpreter not found

The `python.defaultInterpreterPath` must match the current context.

**Fix:** Use `${workspaceFolder}/.venv` — VS Code resolves the correct binary per-platform automatically. Avoid hard-coding `bin/python` or `Scripts/python.exe` in shared workspace settings.

## Testing Commands

After configuration, verify the setup works:

```bash
# Check UV is available
uv --version

# Verify Python interpreter
uv run python --version

# Run tests
uv run pytest tests/unit/search/ -v --tb=short
uv run pytest tests/unit/rag/test_embedding_provider.py -v --tb=short
```

## Alternative: Using PowerShell with WSL Project

If you prefer PowerShell over bash:

1. Open the project via Windows path: `\\wsl$\Ubuntu\home\user\projects\GRID-main`
2. Or open from Windows side in Cursor (not via WSL terminal)
3. The window will be in Windows context, and `defaultProfile.windows` will apply

## References

- [VS Code Terminal Profiles](https://code.visualstudio.com/docs/terminal/profiles)
- [VS Code Remote WSL](https://code.visualstudio.com/docs/remote/wsl)
- [UV Installation](https://docs.astral.sh/uv/getting-started/installation/)
