# GRID Workspace - Dependency Version Matrix

**Last Updated:** 2026-01-24

This document tracks version decisions, compatibility constraints, and divergence reasons across all Python projects in the GRID workspace.

## Overview

This workspace contains multiple Python projects with varying dependency requirements. While some core dependencies align (FastAPI, Pydantic), others diverge due to specific project needs (e.g., ML/AI libraries for EUFLE).

### Workspace Strategy

* **Python Version:** Unified on Python 3.13.11 across all projects.
* **Package Manager:** `uv` is the primary recommended tool for speed and resolution, with `pip` as a fallback.
* **Virtual Environments:** Each core project maintains its own isolated virtual environment to prevent cross-project dependency conflicts.

## Core Projects

### GRID Framework (`grid/`)

* **Version**: 2.2.0
* **Location**: `e:\grid`
* **Python**: 3.13.11 (Constraint: `>=3.13,<3.14`)
* **Primary requirements**: `pyproject.toml`, `requirements.txt`
* **Virtual environment**: `e:\grid\.venv`
* **Key dependencies**: 
  - `fastapi>=0.104.0` (Web framework)
  - `scikit-learn==1.8.0` (ML library - pinned for stability)
  - `mcp[cli]>=1.25.0` (Model Context Protocol)
  - `sentence-transformers>=5.2.0` (RAG embeddings)
  - `chromadb>=1.4.1` (Vector database)
  - `ollama>=0.6.1` (Local LLM integration)

### EUFLE ML/AI Operations (`EUFLE/`)

* **Location**: `e:\grid\EUFLE`
* **Python**: 3.13.11
* **Requirements**: [DEPENDENCIES.md](file:///e:/grid/EUFLE/docs/DEPENDENCIES.md), `config/requirements.txt`
* **Status**: Separate subproject with independent ML/AI dependency management.
* **Key dependencies**:
  - `torch==2.9.1+cpu` (Deep learning framework - CPU build)
  - `transformers==4.57.3` (Hugging Face transformers)
  - `peft==0.18.0` (Parameter-efficient fine-tuning)
  - `trl==0.24.0` (Transformer reinforcement learning)
  - `bitsandbytes>=0.43` (4-bit quantization for QLoRA)

### Legacy Pipeline (`archive/legacy/pipeline/`)

* **Location**: `e:\grid\archive\legacy\pipeline`
* **Python**: 3.13.11 (Legacy support for 3.8-3.12)
* **Requirements**: `pyproject.toml`, `requirements.txt`
* **Status**: Archived data processing system for unstructured data.
* **Key dependencies**:
  - `pydantic>=2.0.0` (Data validation)
  - `scikit-learn>=1.3.0` (ML classification)
  - `boto3>=1.28.0` (AWS S3 integration)
  - `pytesseract>=0.3.10` (OCR engine)

### Apps Frontend (`projects/Apps/`)

* **Location**: `e:\projects\Apps`
* **Type**: React/TypeScript application
* **Package Manager**: npm
* **Key dependencies**:
  - `react@^19.2.3` (UI framework)
  - `three@^0.169.0` (3D rendering)
  - `@react-three/fiber@^8.17.10` (React Three.js integration)
  - `typescript@~5.8.2` (Type system)

### Apps Backend (`projects/Apps/backend/`)

* **Location**: `e:\projects\Apps\backend`
* **Python**: 3.13.11
* **Requirements**: `requirements.txt`
* **Key dependencies**:
  - `fastapi>=0.104.0` (Web framework)
  - `sqlalchemy>=2.0.0` (ORM)
  - `alembic>=1.13.0` (Database migrations)
  - `stripe>=7.0.0` (Payment processing)

## Python Version Configuration

The workspace enforces Python 3.13.11 through a layered configuration:

1. **Root Configuration**: `.python-version` in `e:\grid` specifies `3.13.11`, detected by `pyenv` and `uv`.
2. **Package Manager Constraint**: `pyproject.toml` specifies `requires-python = ">=3.13,<3.14"`.
3. **Environment Setup**: Initialized via `uv venv --python 3.13 --clear` as documented in `README.md`.
4. **Docker Runtime**: `FROM python:3.13-slim` base image in Dockerfile.

## Version Alignment Strategy

### Aligned Dependencies
* **FastAPI**: `>=0.104.0` across GRID and Apps Backend
* **Pydantic**: `>=2.4.0` (GRID) / `>=2.0.0` (Legacy) - convergence in progress
* **Python**: 3.13.11 across all projects

### Intentional Divergences
* **scikit-learn**: GRID pinned at `1.8.0` (stability), Legacy at `>=1.3.0` (compatibility)
* **ML Libraries**: EUFLE uses specific versions for model compatibility
* **Frontend**: Independent npm ecosystem with TypeScript

### Dependency Management Tools

#### UV (Primary Package Manager)
```bash
# Install dependencies
uv sync --group dev --group test

# Resolve and add new dependency
uv add package-name

# Export for compatibility
uv pip freeze > requirements.txt
```

#### Docker Build Integration
```dockerfile
# Multi-stage build with UV
FROM python:3.13-slim AS base
RUN pip install --no-cache-dir uv

FROM base AS builder
COPY requirements.txt pyproject.toml uv.lock ./
RUN uv venv .venv && uv pip install -r requirements.txt

FROM base AS final
COPY --from=builder /app/.venv /app/.venv
```

## Compatibility Matrix

| Project | Python | FastAPI | Pydantic | scikit-learn | Notes |
|---------|---------|---------|----------|---------------|-------|
| GRID | 3.13.11 | >=0.104.0 | >=2.4.0 | ==1.8.0 | Core framework, pinned ML |
| EUFLE | 3.13.11 | >=0.104.0 | >=2.0.0 | - | ML/AI operations |
| Apps Backend | 3.13.11 | >=0.104.0 | - | - | API services |
| Legacy Pipeline | 3.13.11 | - | >=2.0.0 | >=1.3.0 | Archived, broader range |
| Apps Frontend | - | - | - | - | npm ecosystem |

## Service Dependencies

### Development Services
* **ChromaDB**: `chromadb/chroma:latest` (Vector database for RAG)
* **Ollama**: `ollama/ollama:latest` (Local LLM service)
* **PostgreSQL**: Default database for Apps Backend
* **Redis**: Caching layer

### External Service Integration
* **Stripe**: Payment processing (Apps Backend)
* **AWS S3**: Document storage (Legacy Pipeline)
* **Sentry**: Error tracking (Apps Frontend)

## Version Update Process

### Automated Updates
```bash
# Check for outdated packages
uv pip list --outdated

# Update with constraints
uv sync --upgrade
```

### Manual Version Changes
1. Update `pyproject.toml` with new version
2. Test compatibility with `uv sync`
3. Update `requirements.txt` if needed
4. Test in isolated environment
5. Update this matrix

### Change Documentation
* Update this document when changing core dependencies
* Document reasons for version pinning
* Note any breaking changes or compatibility issues

## Troubleshooting

### Common Issues
* **Version Conflicts**: Use isolated virtual environments per project
* **Build Failures**: Check Docker base image matches Python version
* **Import Errors**: Verify dependency installation in correct environment

### Resolution Strategies
```bash
# Clean environment
uv venv --python 3.13 --clear
uv sync --group dev --group test

# Specific version debugging
uv pip show package-name
```

## Development Guidelines

### Adding New Dependencies
1. Check existing matrix for similar packages
2. Verify version constraints in dependent projects
3. Test in isolated environment first
4. Update project-specific requirements
5. Document addition in this matrix

### Security Updates
* Monitor security advisories for critical dependencies
* Update vulnerable packages promptly
* Test compatibility before deployment
* Document security-related version changes

---

**Related Documents:**
* [AGENTS.md](AGENTS.md) - Development workflows and code style guidelines
* [DEPENDENCIES.md](E:/grid/EUFLE/docs/DEPENDENCIES.md) - EUFLE-specific dependency documentation
