# Virtual Environment Setup Guide

> Official Python.org workflow for GRID workspace

## Overview

This guide documents the virtual environment setup for the GRID project, following the official Python documentation at [docs.python.org/3/library/venv.html](https://docs.python.org/3/library/venv.html).

## Quick Start

```powershell
# Navigate to grid workspace
cd E:\grid

# Activate the existing venv
.\.venv\Scripts\Activate.ps1
```

## Official Python.org Steps

### 1. Create Virtual Environment

The `venv` module creates lightweight virtual environments with their own site directories:

```powershell
# Official command (Windows PowerShell)
python -m venv .venv --upgrade-deps
```

**Key flags:**
- `--upgrade-deps` - Upgrades pip to the latest version via `ensurepip`
- `--system-site-packages` - Include system packages (optional)
- `--without-pip` - Skip pip installation (not recommended)

### 2. Activate the Environment

| Platform | Shell | Command |
|----------|-------|---------|
| Windows | PowerShell | `.venv\Scripts\Activate.ps1` |
| Windows | cmd.exe | `.venv\Scripts\activate.bat` |
| POSIX | bash/zsh | `source .venv/bin/activate` |

### 3. Bootstrap pip with ensurepip

By default, `venv` uses `ensurepip` to install pip. To manually upgrade:

```powershell
python -m ensurepip --upgrade
```

### 4. Verify Installation

```powershell
python --version    # Should show Python 3.13.x
pip --version       # Should show pip 25.x
```

### 5. Deactivate

```powershell
deactivate
```

## PowerShell Profile Commands

The PowerShell profile (`Microsoft.PowerShell_profile.ps1`) provides these commands:

| Command | Description |
|---------|-------------|
| `mkvenv` | Create new venv using official method |
| `venv` | Activate .venv in current directory |
| `rmvenv` | Deactivate current venv |
| `venvstatus` | Show venv status and versions |
| `grid` | Navigate to E:\grid (auto-activates venv) |

## Auto-Activation

The PowerShell profile automatically:
1. Navigates to `E:\grid` on startup
2. Activates `.venv` if present
3. Sets environment variables from `grid.code-workspace`

## Workspace Integration

The `grid.code-workspace` configures:
- Default Python interpreter: `E:\grid\.venv\Scripts\python.exe`
- Terminal auto-activation via `VIRTUAL_ENV` environment variable
- PYTHONPATH: `E:\grid;E:\grid\src;E:\grid\light_of_the_seven`

## Best Practices (Python.org)

1. **Convention**: Name your venv `.venv` or `venv`
2. **Location**: Keep in project root directory
3. **Git**: Already ignored via `.gitignore` (created by venv since Python 3.13)
4. **Disposable**: Recreate from `requirements.txt` rather than moving
5. **Not portable**: Always recreate venv at new locations

## Recreating the Environment

```powershell
# Remove old venv
Remove-Item -Recurse -Force .venv

# Create fresh venv with pip
python -m venv .venv --upgrade-deps

# Activate
.\.venv\Scripts\Activate.ps1

# Install project dependencies
pip install -e .[api]

# Or from requirements
pip install -r requirements.txt
```

## Troubleshooting

### Execution Policy Error

If PowerShell blocks activation scripts:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### pip Not Found

Reinstall pip using ensurepip:

```powershell
python -m ensurepip --upgrade
```

### Wrong Python Version

Verify the venv Python matches your system:

```powershell
.\.venv\Scripts\python.exe --version
```

## References

- [Python venv documentation](https://docs.python.org/3/library/venv.html)
- [Python ensurepip documentation](https://docs.python.org/3/library/ensurepip.html)
- [PEP 405 - Python Virtual Environments](https://peps.python.org/pep-0405/)
- [Microsoft PowerShell Execution Policies](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies)
