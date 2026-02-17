# CI/CD

This document has been superseded by the comprehensive CI/CD Guide.

**See: [CI_CD_GUIDE.md](CI_CD_GUIDE.md)**

## Quick Reference

### Workflows

| Workflow | File | Purpose |
|----------|------|---------|
| Main CI | `.github/workflows/main.yaml` | Lint, test, security, build |
| Release | `.github/workflows/release.yaml` | Version bumping, publishing |

### Run Locally

```bash
# Install nektos/act
# macOS: brew install act
# Windows: choco install act-cli

# Run jobs locally
act -l          # List jobs
act -j lint     # Run lint job
act -j test     # Run test job
act push        # Run full workflow
```

### Quick Commands

```bash
# Format code
black .
isort .

# Lint
ruff check .
ruff check --fix .

# Test
pytest tests/unit -v

# Type check
mypy circuits/grid --ignore-missing-imports
```

### Environment Variables

```bash
# Windows (PowerShell)
$env:BLOCKER_DISABLED="1"
$env:GRID_ENVIRONMENT="testing"
$env:PYTHONPATH="circuits;."

# Linux/macOS
export BLOCKER_DISABLED="1"
export GRID_ENVIRONMENT="testing"
export PYTHONPATH="circuits:."
```

For complete documentation, see [CI_CD_GUIDE.md](CI_CD_GUIDE.md).
