# GRID Ecosystem - E:\ Drive Documentation

**Date:** February 7, 2026  
**Primary Repository:** `GRID-INTELLIGENCE/GRID`  
**Location:** `E:\grid`

---

## Table of Contents

1. [Overview](#overview)
2. [Directory Structure](#directory-structure)
3. [Git Repository](#git-repository)
4. [Test Suite](#test-suite)
5. [Recovery History](#recovery-history)
6. [Configuration](#configuration)
7. [Quick Start](#quick-start)

---

## Overview

This is the primary development drive containing the GRID (Generalized Reasoning Intelligence Domain) ecosystem - an enterprise AI framework with local-first RAG, event-driven agentic systems, and cognitive decision support.

**Key Components:**
- **GRID Core:** Main repository with 1,989+ tests
- **Coinbase:** Trading and analysis tools
- **Wellness Studio:** Health data analysis
- **SSL:** Security certificates and tools
- **Analysis Outputs:** Comprehensive reports and documentation

---

## Directory Structure

```
E:\
├── grid/                           # Primary GRID repository
│   ├── src/                        # Core source code
│   │   ├── application/            # Mothership, resonance, APIs
│   │   ├── grid/                   # Security, MCP, core modules
│   │   ├── infrastructure/         # Parasite guard, event bus
│   │   ├── cognitive/              # AI/ML cognitive components
│   │   └── unified_fabric/         # Cross-domain integration
│   ├── tests/                      # Test suites (1,989+ tests)
│   ├── docs/                       # Documentation
│   ├── Arena/                      # AI Arena components
│   └── EUFLE/                      # Edge Unified Fabric Layer
│
├── Coinbase/                       # Coinbase integration
├── wellness_studio/                # Wellness/health analysis
├── SSL/                            # SSL certificates
├── mothership/                     # Core application components
│
├── analysis_outputs/               # Analysis reports
│   ├── comprehensive_analysis_report.json
│   ├── TOP_10_ISSUES_ANALYSIS.md
│   └── SECURITY_REMEDIATION_PLAN.md
│
├── tests/                          # Additional test suites
├── docs/                           # Cross-project documentation
├── _projects/                      # Sub-projects and worktrees
├── data/                           # Shared data storage
└── README.md                       # This documentation
```

---

## Git Repository

### Remotes

```
origin         https://github.com/GRID-INTELLIGENCE/GRID.git (primary)
origin_irfan   https://github.com/irfankabir02/GRID.git (mirror)
```

### Branches

| Branch | Remote | Purpose |
|--------|--------|---------|
| `main` | `origin/main` | Primary development branch |
| `claude/add-claude-documentation-nHZSE` | `origin/claude/add-claude-documentation-nHZSE` | Claude documentation |
| `claude/analyze-codebase-priorities-8i5MO` | `origin/claude/analyze-codebase-priorities-8i5MO` | Analysis priorities |

### Recent Commits

```
20dfd58 (HEAD -> main) test: update test files for import and RAG initialization
d3c7424 docs: update README and benchmark data
f1389be chore(config): update configuration and server files
cb9276f fix(tests): correct import path for parasite_guard tests
dd6c498 fix(middleware): resolve import errors for StreamMonitor and ParasiteDetector
5a76558 fix(security): add missing sanitize functions to environment module
1b739a3 feat(middleware): add data corruption penalty tracking module
c9d1308 (origin/main) docs: add Git and branch best practices
```

### Git Configuration

```ini
[user]
    name = caraxesthebloodwyrm
    email = caraxesthebloodwyrm@users.noreply.github.com
```

---

## Test Suite

**Status:** 1,989 tests collected (exceeds 1400+ target)

### Running Tests

```powershell
# Full test collection
cd E:\grid
python -m pytest tests/ --collect-only -q

# Run tests (excluding slow/integration)
python -m pytest tests/ -m "not integration and not slow" -x

# Run specific test modules
python -m pytest tests/unit/ -v
python -m pytest tests/grid/security/ -v
```

### Dependencies Installed

- fastapi, uvicorn, pydantic
- pytest, pytest-asyncio, pytest-cov
- numpy, scikit-learn, tiktoken
- chromadb, mcp, ollama
- httpx, asyncpg, sqlalchemy
- opentelemetry (API, SDK, exporters)

---

## Recovery History

### February 7, 2026 Recovery

**Tasks Completed:**
1. ✅ Located USB drive (F:\ with ESD-USB)
2. ✅ Verified E:\grid repo exists with GRID-INTELLIGENCE/GRID origin
3. ✅ Confirmed dual remotes: origin (GRID-INTELLIGENCE) and origin_irfan (irfankabir02)
4. ✅ Verified all directories restored: Coinbase, wellness_studio, SSL, analysis_outputs, tests, docs
5. ✅ Applied E:\ layout redesign with PROJECT_GRID paths correct
6. ✅ Created E:\README.md documentation
7. ✅ Fixed test suite - 1,989 tests collected

**Fixes Applied:**

| File | Fix |
|------|-----|
| `src/grid/security/environment.py` | Added `sanitize_environment()` and `sanitize_path()` functions |
| `src/application/mothership/middleware/data_corruption_penalty.py` | Created missing penalty tracking module |
| `src/application/mothership/main.py` | Added `StreamMonitorMiddleware` import |
| `src/infrastructure/parasite_guard/middleware.py` | Added `ParasiteDetectorMiddleware` alias |
| `tests/grid/security/test_parasite_guard.py` | Fixed import path (removed `src.` prefix) |

**Commits Created:**
- `1b739a3` - feat(middleware): add data corruption penalty tracking module
- `5a76558` - fix(security): add missing sanitize functions
- `dd6c498` - fix(middleware): resolve import errors
- `cb9276f` - fix(tests): correct import path
- `f1389be` - chore(config): update configuration files
- `d3c7424` - docs: update README and benchmark data
- `20dfd58` - test: update test files

---

## Configuration

### Environment Variables (.env.editor)

```env
WORKSPACE_ROOT=E:\
PROJECT_GRID=E:\grid
PROJECT_COINBASE=E:\Coinbase
PROJECT_EUFLE=E:\EUFLE
PROJECT_WORKSPACE_UTILS=E:\workspace_utils

GITHUB_TOKEN=ghp_your_token_here
GITHUB_ORG=your-org-name

OLLAMA_API_URL=http://localhost:11434
OLLAMA_DEFAULT_MODEL=mistral-nemo:latest

VSCODE_USER_PATH=C:\Users\irfan\AppData\Roaming\Code\User
WINDSURF_USER_PATH=C:\Users\irfan\AppData\Roaming\Windsurf\User
```

### Python Path

```powershell
$env:PYTHONPATH = "E:\grid\src"
```

---

## Quick Start

### Navigate and Check Status

```powershell
cd E:\grid
& 'C:\Program Files\Git\bin\git.exe' status
& 'C:\Program Files\Git\bin\git.exe' log --oneline -5
```

### Run Tests

```powershell
# Quick test run
python -m pytest tests/ -x --tb=short

# Full test suite
python -m pytest tests/ -m "not integration and not slow" --ignore=tests/api
```

### Start Application

```powershell
# Start mothership
cd E:\grid\src\application\mothership
python main.py

# Or with uvicorn
uvicorn application.mothership.main:app --host 0.0.0.0 --port 8080
```

---

## Notes

- **Primary remote:** `origin` (GRID-INTELLIGENCE/GRID)
- **Mirror remote:** `origin_irfan` (irfankabir02/GRID)
- **Default branch:** `main` (7 commits ahead of origin/main)
- **Test status:** 1,989 tests collected, dependencies installed
- **Last updated:** February 7, 2026

---

**Maintainer:** caraxesthebloodwyrm  
**Repository:** https://github.com/GRID-INTELLIGENCE/GRID
