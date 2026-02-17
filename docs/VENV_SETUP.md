# Virtual Environment Setup Guide

> UV-managed virtual environment for the GRID project

## Overview

GRID uses **[UV](https://docs.astral.sh/uv/)** as the sole package and environment manager. UV automatically creates and manages the `.venv/` directory. **Do not** use `python -m venv` or `pip install` directly.

## Quick Start

```powershell
# From the project root (where pyproject.toml lives)
uv sync --group dev --group test   # Creates .venv, installs everything
```

UV reads `.python-version` (pinned to 3.13) and `pyproject.toml` to create an isolated `.venv/` with all dependencies from `uv.lock`.

## Running Commands

```powershell
uv run pytest                       # Run tests
uv run python -m grid --help        # Run GRID CLI
uv run ruff check .                 # Lint
```

Or activate the venv manually:

| Platform | Shell | Command |
|----------|-------|---------|
| Windows | PowerShell | `.\.venv\Scripts\Activate.ps1` |
| Windows | cmd.exe | `.\.venv\Scripts\activate.bat` |
| POSIX | bash/zsh | `source .venv/bin/activate` |

> **Preferred**: Use `uv run <command>` instead of manual activation. It ensures the correct environment is always used.

## Managing Dependencies

```powershell
uv add <package>                   # Add a runtime dependency
uv add --group dev <package>       # Add a dev-only dependency
uv lock                            # Regenerate uv.lock
uv sync                            # Sync .venv to match lockfile
```

> **Do not** run `pip install` inside `.venv`. Use `uv add` so packages are tracked in `pyproject.toml` and `uv.lock`.

## Recreating the Environment

The `.venv/` folder is **disposable** — delete it and run `uv sync` to recreate from scratch:

```powershell
Remove-Item -Recurse -Force .venv
uv sync --group dev --group test
```

## Workspace Integration

IDE settings should use relative paths:
- **Python interpreter**: `.\.venv\Scripts\python.exe` (Windows) / `.venv/bin/python` (POSIX)
- **PYTHONPATH**: `src` (configured in `pyproject.toml [tool.pytest.ini_options]`)

## Best Practices

1. **Convention**: Always `.venv` in project root (UV default)
2. **Git**: Already ignored via `.gitignore` (UV creates its own `.venv/.gitignore`)
3. **Disposable**: Recreate from `uv sync` — never move or copy `.venv/`
4. **Isolation**: `include-system-site-packages = false` (UV default)
5. **Single tool**: Use `uv` for all package operations — no `pip`, no `python -m venv`

## Validation

```powershell
uv run python --version             # Should show Python 3.13.x
uv run python -c "import grid"      # Should succeed
uv run python scripts/validate_venv.py  # Full health check
```

## Troubleshooting

### Execution Policy Error (Windows)

If PowerShell blocks activation scripts:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Wrong Python Version

UV uses `.python-version` to select the interpreter. Verify:

```powershell
uv run python --version
```

If the version is wrong, update `.python-version` and run `uv sync`.

### Packages Missing After Pull

```powershell
uv sync --group dev --group test   # Re-sync from updated uv.lock
```

## References

- [UV Documentation](https://docs.astral.sh/uv/)
- [Python venv documentation](https://docs.python.org/3/library/venv.html)
- [PEP 405 - Python Virtual Environments](https://peps.python.org/pep-0405/)
