# GRID Configuration & Staging Guide

> Comprehensive documentation for configuring and staging the GRID development environment

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Configuration Architecture](#configuration-architecture)
- [Settings Reference](#settings-reference)
- [Environment Variables](#environment-variables)
- [Staging Best Practices](#staging-best-practices)
- [CI/CD Configuration](#cicd-configuration)
- [Troubleshooting](#troubleshooting)

---

## Overview

GRID uses a layered configuration system built on `pydantic-settings`. Configuration flows through:

```
Environment Variables → .env file → config/settings.py → Runtime
```

### Key Principles

1. **Environment-First**: All settings can be overridden via environment variables
2. **Type-Safe**: Pydantic validates all configuration at startup
3. **Staged Loading**: Settings are loaded once and cached
4. **Test-Friendly**: Automatic blocker bypass in test/CI environments

---

## Quick Start

### 1. Create Virtual Environment (UV)

```powershell
# From the project root (where pyproject.toml lives)
uv sync --group dev --group test   # Creates .venv, installs everything
```

### 2. Configure Environment

Create a `.env` file at the repository root:

```env
# Core Settings
GRID_ENVIRONMENT=dev
GRID_HOME=.
DEBUG=true

# Database
DATABASE__URL=sqlite:///./grid.db

# API Server
API__HOST=0.0.0.0
API__PORT=8000

# AI/LLM (optional)
AI__OPENAI_API_KEY=sk-your-key-here

# Blocker (disable for development)
BLOCKER_DISABLED=0
```

### 3. Stage the Environment

```python
from config.settings import settings

# Stage paths, env vars, and create directories
settings.stage()

# Verify
print(settings.environment)  # 'dev'
print(settings.grid_home)    # <project root>
```

---

## Configuration Architecture

### Directory Structure

```
<project-root>/
├── .env                    # Local environment overrides (git-ignored)
├── .venv/                  # Virtual environment (git-ignored)
├── config/
│   ├── settings.py         # Main settings module
│   ├── logging_config.py   # Logging configuration
│   ├── pattern_rule.yaml   # Pattern routing rules
│   └── production.yaml     # Production overrides
├── grid.code-workspace     # VS Code workspace settings
└── pyproject.toml          # Python project configuration
```

### Settings Module (`config/settings.py`)

The central configuration module provides:

- **Path Constants**: `REPO_ROOT`, `CONFIG_DIR`, `CIRCUITS_DIR`, etc.
- **Nested Settings**: `DatabaseSettings`, `APISettings`, `LoggingSettings`
- **Main Settings**: `Settings` class with all configuration
- **Singleton**: `settings = get_settings()` cached instance

```python
from config.settings import settings, REPO_ROOT, CIRCUITS_DIR

# Access settings
print(settings.api.port)           # 8000
print(settings.database.url)       # sqlite:///./grid.db
print(settings.blocker.disabled)   # False

# Check environment
if settings.is_production:
    # Production-specific logic
    pass
```

---

## Settings Reference

### Core Settings

| Setting | Type | Default | Environment Variable |
|---------|------|---------|---------------------|
| `grid_home` | Path | `.` (project root) | `GRID_HOME` |
| `environment` | str | `dev` | `GRID_ENVIRONMENT` |
| `debug` | bool | `False` | `DEBUG` |
| `testing` | bool | `False` | `TESTING` |

### Database Settings

| Setting | Type | Default | Environment Variable |
|---------|------|---------|---------------------|
| `url` | str | `sqlite:///./grid.db` | `DATABASE__URL` |
| `echo` | bool | `False` | `DATABASE__ECHO` |
| `pool_size` | int | `5` | `DATABASE__POOL_SIZE` |

### API Settings

| Setting | Type | Default | Environment Variable |
|---------|------|---------|---------------------|
| `host` | str | `0.0.0.0` | `API__HOST` |
| `port` | int | `8000` | `API__PORT` |
| `reload` | bool | `True` | `API__RELOAD` |
| `workers` | int | `1` | `API__WORKERS` |

### Logging Settings

| Setting | Type | Default | Environment Variable |
|---------|------|---------|---------------------|
| `level` | str | `INFO` | `LOGGING__LEVEL` |
| `format` | str | (see code) | `LOGGING__FORMAT` |
| `file` | Path | `None` | `LOGGING__FILE` |
| `json_output` | bool | `False` | `LOGGING__JSON_OUTPUT` |

### AI Settings

| Setting | Type | Default | Environment Variable |
|---------|------|---------|---------------------|
| `openai_api_key` | str | `None` | `AI__OPENAI_API_KEY` |
| `default_model` | str | `gpt-4` | `AI__DEFAULT_MODEL` |
| `onnx_providers` | list | `["CPUExecutionProvider"]` | `AI__ONNX_PROVIDERS` |

### Blocker Settings

| Setting | Type | Default | Environment Variable |
|---------|------|---------|---------------------|
| `disabled` | bool | `False` | `BLOCKER_DISABLED` |
| `allowed_packages` | list | `[]` | `BLOCKER__ALLOWED_PACKAGES` |
| `blocked_packages` | list | `[]` | `BLOCKER__BLOCKED_PACKAGES` |

---

## Environment Variables

### Naming Convention

- **Simple settings**: `GRID_HOME`, `DEBUG`
- **Nested settings**: Use double underscore `__` as delimiter
  - `DATABASE__URL` → `settings.database.url`
  - `API__PORT` → `settings.api.port`

### Environment Detection

The system automatically detects the environment:

| Condition | Detected Environment |
|-----------|---------------------|
| `CI=true` | `ci` |
| `PYTEST_CURRENT_TEST` set | `testing` |
| `GRID_ENVIRONMENT` set | (value) |
| Default | `dev` |

### Example `.env` Files

**Development (`.env`)**:
```env
GRID_ENVIRONMENT=dev
DEBUG=true
DATABASE__URL=sqlite:///./grid.db
API__RELOAD=true
BLOCKER_DISABLED=1
```

**Production (`.env.production`)**:
```env
GRID_ENVIRONMENT=production
DEBUG=false
DATABASE__URL=postgresql://user:pass@host:5432/grid
API__RELOAD=false
API__WORKERS=4
LOGGING__LEVEL=WARNING
LOGGING__JSON_OUTPUT=true
```

---

## Staging Best Practices

### 1. Pre-Stage on Application Entry

```python
# In your main entry point (e.g., __main__.py)
from config.settings import settings

def main():
    # Stage environment first
    settings.stage()

    # Then run application
    from circuits.cli.main import main as cli_main
    return cli_main()

if __name__ == "__main__":
    raise SystemExit(main())
```

### 2. Use Dependency Injection for Testing

```python
# tests/conftest.py
import pytest
from config.settings import Settings, get_settings

@pytest.fixture
def test_settings():
    """Override settings for testing."""
    settings = Settings(
        environment="testing",
        debug=True,
        database={"url": "sqlite:///:memory:"},
        blocker={"disabled": True},
    )
    settings.stage()
    return settings
```

### 3. Validate Settings at Startup

```python
from config.settings import settings

def validate_production_settings():
    """Ensure production requirements are met."""
    if settings.is_production:
        assert settings.database.url.startswith("postgresql://"), \
            "Production requires PostgreSQL"
        assert settings.ai.openai_api_key, \
            "Production requires OpenAI API key"
        assert not settings.debug, \
            "Debug must be disabled in production"
```

### 4. Layer Configuration

```
.env.defaults     # Checked into git (safe defaults)
.env              # Local overrides (git-ignored)
.env.production   # Production secrets (managed externally)
```

### 5. Use Settings Properties

```python
# Instead of checking environment directly
if settings.environment == "testing":
    ...

# Use the property
if settings.is_testing:
    ...
```

---

## CI/CD Configuration

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

env:
  GRID_ENVIRONMENT: ci
  BLOCKER_DISABLED: "1"
  DATABASE__URL: sqlite:///:memory:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Install dependencies (UV)
        run: uv sync --group dev --group test

      - name: Run tests
        run: |
          source .venv/bin/activate
          pytest tests/ -v --tb=short
```

### Environment Variable Precedence

1. Shell environment variables (highest priority)
2. `.env` file
3. Default values in `Settings` class (lowest priority)

---

## Troubleshooting

### Common Issues

#### Import Blocked by Blocker

```
[BLOCKED] Payload transfer enforcement: Grid package restricted (scope: circuits.grid)
```

**Solution**: Set `BLOCKER_DISABLED=1` in environment or `.env`:
```powershell
$env:BLOCKER_DISABLED = "1"
```

#### Module Not Found in Tests

```
ModuleNotFoundError: No module named 'grid'
```

**Solution**: Ensure `conftest.py` adds paths and disables blocker:
```python
import os
os.environ["BLOCKER_DISABLED"] = "1"

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

#### Settings Not Reloading

Settings are cached via `lru_cache`. To reload:
```python
from config.settings import get_settings

get_settings.cache_clear()
settings = get_settings()
```

#### Virtual Environment Not Activating

Ensure execution policy is set (Windows):
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Debug Settings

Run the settings module directly to see current configuration:
```powershell
python -m config.settings
```

Output:
```
GRID Settings Configuration
==================================================
Environment: dev
GRID Home: <project root>
Debug: False
Testing: False
Blocker Disabled: False

Full Configuration (JSON):
{
  "grid_home": "E:\\grid",
  "environment": "dev",
  ...
}
```

---

## Summary

| Task | Command/Location |
|------|-----------------|
| Create venv | `uv sync --group dev --group test` |
| Configure | Edit `.env` file |
| Stage | `settings.stage()` |
| Run tests | `pytest tests/ -v` (auto-disables blocker) |
| Debug settings | `python -m config.settings` |

---

## References

- [Python venv documentation](https://docs.python.org/3/library/venv.html)
- [Python ensurepip documentation](https://docs.python.org/3/library/ensurepip.html)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [VS Code Workspace Settings](https://code.visualstudio.com/docs/getstarted/settings)
