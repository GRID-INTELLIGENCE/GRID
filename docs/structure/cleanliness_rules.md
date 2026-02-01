# Cleanliness Rules: What Never Belongs in Git

This document describes what should never be committed to the repository and should be properly excluded via `.gitignore`.

## Cache Directories (Always Ignored)

These are rebuildable artifacts that should never be committed:

### Python Caches
- `__pycache__/` - Python bytecode cache directories
- `*.pyc`, `*.pyo`, `*.pyd` - Compiled Python files
- `.pytest_cache/` - pytest cache directory
- `.ruff_cache/` - Ruff linter cache
- `.mypy_cache/` - mypy type checker cache
- `.pyright/` - Pyright type checker cache

### Coverage Reports
- `htmlcov/` - HTML coverage reports
- `.coverage` - Coverage data file
- `*.cover` - Coverage files
- `.hypothesis/` - Hypothesis testing cache

### Node.js (if present)
- `node_modules/` - Node.js dependencies (should be in package.json/lock)
- `.npm/` - npm cache

### IDE/Editor
- `.vscode/` (project-specific, team-specific settings)
- `.idea/` (PyCharm/IntelliJ)
- `*.swp`, `*.swo` (Vim swap files)

### Build Artifacts
- `dist/`, `build/` - Build output directories
- `*.egg-info/` - Python package metadata
- `.eggs/` - Setuptools eggs directory

## Virtual Environments (Never Commit)

Virtual environments should **never** be committed:
- `venv/`
- `.venv/`
- `env/`
- `.env/` (unless it's for environment variables template)
- `ENV/`

**Rationale**: Virtual environments are:
1. Large and platform-specific
2. Rebuildable from `requirements.txt` or `pyproject.toml`
3. Should be created per developer/environment
4. Add unnecessary noise to the repository

## Generated Files (Context-Dependent)

These may or may not belong in git depending on use case:

### Documentation Build
- `docs/_build/` - Sphinx build output (should be ignored)

### Database
- `*.db`, `*.sqlite`, `*.sqlite3` - Database files (usually should be ignored)

### Logs
- `*.log` - Log files (usually should be ignored)
- `logs/` - Log directories (usually should be ignored)

## Always Keep in Git

These should **always** be committed:

### Configuration Files
- `.gitignore` - Git ignore rules
- `.gitattributes` - Git attributes
- `pyproject.toml` - Python project configuration
- `requirements.txt` - Python dependencies
- `package.json`, `package-lock.json` - Node.js dependencies (if applicable)
- `.env.example` - Environment variable template

### Source Code
- All `.py` files (source code)
- All `.md` files (documentation)
- All test files

### Project Artifacts (Root-Level Metrics)
- `benchmark_metrics.json` - Benchmark results (referenced by tests)
- `benchmark_results.json` - Benchmark results (referenced by tests)
- `stress_metrics.json` - Stress test results (referenced by scripts)

## Maintenance

After cleanup, ensure `.gitignore` includes all cache patterns. Run:

```bash
python scripts/cleanup_caches.py
```

This will:
1. Delete cache directories (excluding venv ones)
2. Update `.gitignore` with missing cache patterns
