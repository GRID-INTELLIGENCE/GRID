---
description: Coding standards for IDE configuration files
globs:
  - "**/*.json"
  - "**/.vscode/**"
  - "**/.cursor/**"
  - "**/pyproject.toml"
  - "**/.ruff.toml"
  - "**/settings.json"
alwaysApply: false
---

# IDE Configuration Standards

Applies to: IDE configuration files (settings.json, extensions.json, tasks.json, pyproject.toml, .ruff.toml)

## Python Formatter

**Required:** Use ruff as the Python formatter.

```json
{
  "[python]": {
    "defaultFormatter": "charliermarsh.ruff"
  }
}
```

**NOT allowed:**
- ❌ `"ms-python.black-formatter"`
- ❌ `"ms-python.isort"`
- ❌ `"ms-python.vscode-pylint"`

## Line Length

**Required:** 120 characters maximum.

```json
{
  "[python]": {
    "editor.rulers": [120]
  }
}
```

## Line Endings

**Required:** Use LF (`\n`), not CRLF (`\r\n`).

```json
{
  "files.eol": "\n"
}
```

## File Formatting

**Required:** Trim trailing whitespace and insert final newline.

```json
{
  "files.trimTrailingWhitespace": true,
  "files.insertFinalNewline": true
}
```

## Cache Exclusions

**Required:** Exclude all cache and build folders from file watching, search, and file explorer.

```json
{
  "files.exclude": {
    "**/.venv": true,
    "**/__pycache__": true,
    "**/.pytest_cache": true,
    "**/.mypy_cache": true,
    "**/.ruff_cache": true,
    "**/node_modules": true,
    "**/dist": true,
    "**/build": true,
    "**/archive": true
  },
  "search.exclude": {
    "**/.venv": true,
    "**/__pycache__": true,
    "**/.pytest_cache": true,
    "**/.mypy_cache": true,
    "**/.ruff_cache": true,
    "**/node_modules": true,
    "**/dist": true,
    "**/build": true,
    "**/archive": true
  },
  "files.watcherExclude": {
    "**/.venv/**": true,
    "**/__pycache__/**": true,
    "**/.pytest_cache/**": true,
    "**/.mypy_cache/**": true,
    "**/.ruff_cache/**": true,
    "**/node_modules/**": true,
    "**/dist/**": true,
    "**/build/**": true,
    "**/archive/**": true
  }
}
```

## Python Paths

**Required:** Configure Python analysis paths for THE GRID monorepo structure.

```json
{
  "python.analysis.extraPaths": [
    "./work/GRID/src",
    "./safety",
    "./security",
    "./boundaries"
  ]
}
```

## Type Checking

**Required:** Enable type checking with Pylance.

```json
{
  "python.languageServer": "Pylance",
  "python.analysis.typeCheckingMode": "basic"
}
```

## Tasks

**Required:** All Python tasks must use `uv run` prefix.

```json
{
  "tasks": [
    {
      "label": "Daily: Verify the Wall",
      "type": "shell",
      "command": "uv run pytest -q --tb=short && uv run ruff check work/ safety/ security/ boundaries/",
      "group": {
        "kind": "build",
        "isDefault": true
      }
    }
  ]
}
```

**NOT allowed:**
- ❌ `"command": "python -m pytest"`
- ❌ `"command": "pip install ..."`
- ❌ `"command": "pytest"` (without `uv run`)

## Format on Save

**Required:** Enable format on save for Python files.

```json
{
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit",
      "source.fixAll": "explicit"
    }
  }
}
```

## Auto Save

**Required:** Auto-save on focus change.

```json
{
  "files.autoSave": "onFocusChange"
}
```

## References

- Python standards: `.claude/rules/backend.md`
- Development discipline: `.claude/rules/discipline.md`
- Verification checklist: `docs/guides/IDE_SETUP_VERIFICATION.md`
