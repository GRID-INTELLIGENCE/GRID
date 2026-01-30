# GRID CI/CD Guide

This guide explains GRID's Continuous Integration and Continuous Development pipeline.

## Table of Contents

- [Overview](#overview)
- [Workflow Architecture](#workflow-architecture)
- [GitHub Actions Workflows](#github-actions-workflows)
- [Local Testing with Act](#local-testing-with-act)
- [Quality Gates](#quality-gates)
- [Release Process](#release-process)
- [Troubleshooting](#troubleshooting)

---

## Overview

GRID uses GitHub Actions for automated CI/CD, aligned with industry best practices:

- **Fast Feedback** — Catch issues early with automated checks
- **Quality Assurance** — Enforce code style, security, and test coverage
- **Continuous Improvement** — Automated dependency updates and security scanning
- **Seamless Releases** — Automated versioning and publishing

### Key Features

| Feature | Tool/Service | Purpose |
|---------|--------------|---------|
| CI Pipeline | GitHub Actions | Automated testing and quality checks |
| Local CI Testing | nektos/act | Run workflows locally before pushing |
| Code Coverage | Codecov | Track and report test coverage |
| Security Scanning | Bandit, pip-audit | Find vulnerabilities |
| Dependency Updates | Dependabot | Keep dependencies current |
| Release Automation | GitHub Releases | Automated publishing |

---

## Workflow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     GRID CI/CD Pipeline                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Push/PR          Parallel Jobs              Sequential        │
│   ─────────────────────────────────────────────────────────     │
│                                                                 │
│   ┌────────┐      ┌──────────┐                                  │
│   │  Push  │─────▶│   Lint   │──────┐                           │
│   │   PR   │      └──────────┘      │                           │
│   └────────┘      ┌──────────┐      ▼                           │
│       │          │ Security │   ┌──────────┐   ┌──────────┐    │
│       └─────────▶│   Scan   │   │  Tests   │──▶│  Build   │    │
│                  └──────────┘   │ (Matrix) │   │ Package  │    │
│                  ┌──────────┐   └──────────┘   └──────────┘    │
│                  │   Docs   │        │                          │
│                  │  Check   │        ▼                          │
│                  └──────────┘   ┌──────────┐                    │
│                                 │Integration│ (main branch)     │
│                                 │  Tests    │                   │
│                                 └──────────┘                    │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│   Release Pipeline (on tag v*.*.* or manual dispatch)           │
│                                                                 │
│   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   │
│   │ Prepare  │──▶│   Test   │──▶│  Build   │──▶│ Release  │   │
│   │ Version  │   │  Suite   │   │ Package  │   │  GitHub  │   │
│   └──────────┘   └──────────┘   └──────────┘   └──────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## GitHub Actions Workflows

### Main CI Pipeline

**File:** `.github/workflows/main.yaml`

**Triggers:**
- Push to `master`, `main`, `develop`, `feature/**`, `release/**`, `hotfix/**`
- Pull requests to `master`, `main`, `develop`
- Manual workflow dispatch

**Jobs:**

| Job | Description | Dependencies |
|-----|-------------|--------------|
| `lint` | Code quality (Black, isort, Ruff, mypy) | None |
| `security` | Security scanning (Bandit, pip-audit) | None |
| `test` | Unit tests (Python 3.10, 3.11, 3.12) | `lint` |
| `integration` | Integration tests (main branch only) | `test` |
| `build` | Package building and verification | `test` |
| `docs` | Documentation checks | None |
| `ci-status` | Pipeline summary | All jobs |

**Test Matrix:**

| OS | Python Versions |
|----|-----------------|
| Ubuntu | 3.10, 3.11, 3.12 |
| Windows | 3.11 |
| macOS | 3.11 |

### Release Pipeline

**File:** `.github/workflows/release.yaml`

**Triggers:**
- Push tags matching `v*.*.*`
- Manual dispatch with version bump type (patch/minor/major)

**Jobs:**

| Job | Description |
|-----|-------------|
| `prepare` | Determine version, generate changelog |
| `test` | Run tests before release |
| `build` | Build distribution packages |
| `publish-pypi` | Publish to PyPI (optional) |
| `release` | Create GitHub Release |
| `summary` | Release summary |

### Docker Build

**File:** `.github/workflows/build.yaml`

**Triggers:**
- Push to `master`

**Purpose:** Build and push Docker image to Docker Hub.

---

## Local Testing with Act

[nektos/act](https://github.com/nektos/act) allows you to run GitHub Actions locally.

### Installation

```bash
# macOS
brew install act

# Windows (Chocolatey)
choco install act-cli

# Windows (Scoop)
scoop install act

# Linux
curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
```

### Prerequisites

- Docker installed and running
- Sufficient disk space (~2-5GB for container images)

### Usage

```bash
# List available jobs
act -l

# Run all jobs (push event)
act push

# Run specific job
act -j lint
act -j test
act -j security

# Simulate pull request
act pull_request

# Dry run
act -n

# Verbose output
act -v
```

### Configuration

GRID includes an `.actrc` file with recommended settings:

```bash
# Lightweight images for faster local testing
-P ubuntu-latest=catthehacker/ubuntu:act-latest

# Reuse containers
--reuse

# GRID environment variables
--env GRID_ENVIRONMENT=testing
--env BLOCKER_DISABLED=1
--env PYTHONPATH=circuits:.
```

### Using Secrets Locally

```bash
# Create .secrets file (never commit this)
echo "CODECOV_TOKEN=your-token" > .secrets

# Run with secrets
act --secret-file .secrets
```

---

## Quality Gates

### Required Checks

| Check | Purpose |
|-------|---------|
| Lint | Code formatting and style |
| Test | Unit tests must pass |
| Build | Package must build successfully |

### Coverage Thresholds

| Metric | Threshold |
|--------|-----------|
| Project coverage | 25% minimum |
| Patch coverage (new code) | 50% minimum |
| Core modules | 30% minimum |

### Code Quality Tools

| Tool | Purpose |
|------|---------|
| Black | Code formatting |
| isort | Import sorting |
| Ruff | Fast Python linter |
| mypy | Type checking |
| Bandit | Security linting |
| pip-audit | Dependency vulnerabilities |

---

## Release Process

### Automated Release (Recommended)

**Option 1: Manual Dispatch**

1. Go to GitHub Actions
2. Select "Release & Publish" workflow
3. Click "Run workflow"
4. Choose version bump type (patch/minor/major)
5. Optionally mark as pre-release

**Option 2: Push Tag**

```bash
git tag -a v0.3.0 -m "Release v0.3.0"
git push origin v0.3.0
```

### Version Bumping

| Type | When to Use | Example |
|------|-------------|---------|
| `patch` | Bug fixes, minor changes | 0.2.0 → 0.2.1 |
| `minor` | New features, backward compatible | 0.2.0 → 0.3.0 |
| `major` | Breaking changes | 0.2.0 → 1.0.0 |

### Manual Release Steps

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Commit changes
4. Create and push tag
5. GitHub Actions creates release automatically

---

## Troubleshooting

### Lint Failures

```bash
# Fix formatting locally
black .
isort .

# Check and auto-fix
ruff check .
ruff check --fix .
```

### Test Failures

```bash
# Run tests with verbose output
pytest tests/unit -v --tb=long

# Run specific test
pytest tests/unit/test_pattern_engine.py::test_specific -v

# Run with environment variables
$env:BLOCKER_DISABLED="1"  # Windows
export BLOCKER_DISABLED="1"  # Linux/macOS
pytest tests/unit -v
```

### Security Scan Issues

```bash
# Run bandit locally
bandit -r circuits/grid -c .bandit

# Check dependencies
pip-audit
```

### Act Issues

```bash
# Clean Docker resources
docker system prune -a

# Pull latest images
docker pull catthehacker/ubuntu:act-latest

# Debug mode
act -v --verbose
```

### Environment Setup

**Windows (PowerShell):**
```powershell
$env:BLOCKER_DISABLED="1"
$env:GRID_ENVIRONMENT="testing"
$env:PYTHONPATH="circuits;."
pytest tests/unit -v
```

**Linux/macOS:**
```bash
export BLOCKER_DISABLED="1"
export GRID_ENVIRONMENT="testing"
export PYTHONPATH="circuits:."
pytest tests/unit -v
```

---

## Dependabot

GRID uses Dependabot for automated dependency updates:

- **Python dependencies:** Weekly on Monday
- **GitHub Actions:** Weekly on Monday
- **Docker:** Weekly on Tuesday

Updates are grouped by category:
- Development dependencies (pytest, mypy, ruff, black, etc.)
- FastAPI ecosystem (fastapi, uvicorn, pydantic)
- Data science (numpy, pandas, networkx)

---

## Best Practices

### Before Pushing

1. Run `black .` and `isort .`
2. Run `ruff check .`
3. Run `pytest tests/unit -v`
4. (Optional) Run `act -j lint` for full CI simulation

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(pattern): add new detection algorithm
fix(api): handle null response correctly
docs(readme): update installation steps
test(engine): add edge case coverage
ci(actions): update Python version matrix
```

### Pull Requests

1. Use the PR template
2. Keep changes focused
3. Link related issues
4. Ensure CI passes before requesting review

---

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [nektos/act Repository](https://github.com/nektos/act)
- [Codecov Documentation](https://docs.codecov.com)
- [Conventional Commits](https://www.conventionalcommits.org)
- [Semantic Versioning](https://semver.org)
