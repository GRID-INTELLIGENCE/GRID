# Source Control Guidelines for GRID

> **Purpose:** Standardize git and source control practices across GRID using modern workflows and uv for dependency management.

---

## Core Principles

1. **Deterministic Builds** - Use `uv.lock` for reproducible environments
2. **Clean History** - Atomic commits with clear messages
3. **Workflow Integration** - Align with GRID workflows and governance
4. **Security First** - Never commit secrets or sensitive data

---

## Environment Management with `uv`

### Quick Start (Recommended)

```bash
# Navigate to GRID root
cd e:\grid

# Create virtual environment
uv venv

# Activate (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Sync dependencies from lockfile
uv sync

# Verify installation
python -c "import grid; print(grid.__version__)"
```

### Adding Dependencies

```bash
# Add package and update lockfile
uv add package-name

# Add dev dependency
uv add --dev pytest ruff

# Commit both files
git add pyproject.toml uv.lock
git commit -m "Add package-name dependency"
```

### Updating Dependencies

```bash
# Update all packages
uv sync --upgrade

# Update specific package
uv add package-name --upgrade

# Review and commit changes
git diff uv.lock
git add uv.lock pyproject.toml
git commit -m "Update dependencies"
```

---

## File Tracking Rules

### ✅ **TRACK THESE FILES**

- `uv.lock` - Deterministic dependency lockfile
- `pyproject.toml` - Project configuration and dependencies
- `requirements.txt` - Legacy pip requirements (if used)
- `.python-version` - Python version specification
- Source code in `grid/`, `tools/`, `scripts/`
- Test files in `tests/`
- Documentation in `docs/`
- Configuration files (`.gitignore`, `.gitattributes`)

### ❌ **DO NOT TRACK**

- Virtual environments (`.venv/`, `venv/`)
- Cache directories (`.uv-cache/`, `__pycache__/`, `.pytest_cache/`)
- Environment files (`.env`, `.env.local`)
- IDE settings (`.vscode/`, `.idea/`)
- Build artifacts (`dist/`, `build/`, `target/`)
- Logs and temporary files
- Secrets and API keys

---

## Branch Strategy

### Main Branches

- `main` - Production-ready code
- `architecture/stabilization` - Current stabilization work
- `develop` - Integration branch for features

### Feature Branches

```bash
# Create feature branch
git checkout -b feature/rag-enhancements

# Work on feature...
git add .
git commit -m "Implement hybrid search with reranking"

# Merge when ready
git checkout architecture/stabilization
git merge feature/rag-enhancements
git branch -d feature/rag-enhancements
```

---

## Commit Guidelines

### Commit Message Format

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `refactor` - Code refactoring
- `docs` - Documentation
- `test` - Test additions/changes
- `chore` - Maintenance tasks

**Examples:**
```
feat(rag): add hybrid search with BM25 + vector reranking

- Implement hybrid search in RAGEngine
- Add cross-encoder reranking for top-k results
- Update CLI with --hybrid and --rerank flags

Fixes #123
```

### Atomic Commits

- One logical change per commit
- Include tests in the same commit
- Update docs in the same commit
- Keep dependency updates separate

---

## Workflow Integration

### grid-start Workflow

```bash
# Environment setup (using uv)
uv venv
.venv\Scripts\Activate.ps1
uv sync

# Run tests
pytest tests/ -v --cov=grid

# Lint/format
ruff check . --fix && ruff format .
```

### python-uv-venv Workflow

- Always use `uv sync` instead of `pip install`
- Commit `uv.lock` for reproducible builds
- Use `uv add` for new dependencies
- Pin Python version in `pyproject.toml`

---

## Security Practices

### Sensitive Data

```bash
# ✅ Good - Use environment variables
DATABASE_URL=postgresql://user:pass@localhost/db

# ❌ Bad - Hardcoded secrets
DATABASE_URL="postgresql://user:SECRET_PASSWORD@localhost/db"
```

### Pre-commit Hooks

```bash
# Install hooks (if configured)
scripts/install-hooks.sh

# Manual checks before commit
ruff check . --fix
ruff format .
pytest tests/ -q
```

### Git Security

```bash
# Ensure proper line endings
git config core.autocrlf true  # Windows
git config core.autocrlf input  # Linux/Mac

# Check for sensitive data
git grep --cached "password\|secret\|key\|token"
```

---

## Troubleshooting

### Common Issues

**Issue:** `uv.lock` conflicts after merge
```bash
# Resolve conflicts, then regenerate
uv lock --upgrade
git add uv.lock
git commit -m "Resolve lockfile conflicts"
```

**Issue:** Virtual environment not found
```bash
# Recreate environment
uv venv
uv sync
```

**Issue:** Tests failing after dependency update
```bash
# Check specific package versions
uv pip list

# Pin problematic package
uv add package-name==1.2.3
```

---

## Integration with CI/CD

### GitHub Actions Example

```yaml
- name: Set up Python
  uses: actions/setup-python@v4
  with:
    python-version: '3.11'

- name: Install uv
  run: pip install uv

- name: Install dependencies
  run: uv sync --no-dev

- name: Run tests
  run: pytest
```

---

## References

- [grid_start workflow](../.windsurf/workflows/grid_start.md)
- [python-uv-venv workflow](../.windsurf/workflows/python-uv-venv.md)
- [uv Documentation](https://github.com/astral-sh/uv)
- [Git Best Practices](https://git-scm.com/book)

---

**Last Updated:** 2026-01-07
**Maintainer:** GRID Team
**Review Schedule:** Quarterly
