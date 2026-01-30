# GRID Repository Structure Guide

This document is your "map legend" for navigating the GRID repository structure. It explains the organization, domain boundaries, and how to find things.

## Quick Navigation

- **Core Intelligence**: `grid/` - Geometric resonance patterns, essence, awareness, evolution
- **Applications**: `application/` - FastAPI applications (mothership, resonance)
- **Tools**: `tools/` - Local-first RAG system, developer tooling
- **Cognitive Layer**: `light_of_the_seven/light_of_the_seven/cognitive_layer/` - Cognitive decision support (import: `light_of_the_seven.cognitive_layer`)
- **Documentation**: `docs/` - All project documentation
- **Tests**: `tests/` - Test suite
- **Scripts**: `scripts/` - Developer automation scripts

## Structure Overview

```
grid/
├── grid/                   # Core intelligence layer
├── application/            # FastAPI applications
├── tools/                  # Development tools (RAG, etc.)
├── legacy_src/            # Legacy code (being deprecated)
├── light_of_the_seven/    # Cognitive architecture
│   └── light_of_the_seven/
│       └── cognitive_layer/  # Active cognitive layer (importable package)
├── docs/                  # Documentation
├── tests/                 # Test suite
├── scripts/               # Automation scripts
└── pyproject.toml         # Project configuration
```

## Domain Boundaries

### Core Intelligence (`grid/`)

The foundational layer providing geometric resonance patterns and intelligence:

- **essence/** - Core state management
- **patterns/** - Pattern recognition
- **awareness/** - Context awareness
- **evolution/** - Versioning and evolution
- **interfaces/** - Bridge interfaces
- **skills/** - Skill modules
- **entry_points/** - CLI, API, service entry points

**Import**: `from grid.essence import EssentialState`

### Applications (`src/application/`)

FastAPI applications following standard layered architecture:

- **mothership/** - Main FastAPI application
  - `main.py` - Application factory
  - `routers/` - API routes
  - `services/` - Business logic
  - `models/` - Data models
  - `repositories/` - Data access
  - `security/` - Authentication/authorization
- **resonance/** - Resonance API

**Import**: `from application.mothership.main import app`

### Tools (`tools/`)

Developer tools and utilities:

- **rag/** - Local-first RAG system (ChromaDB + Ollama)
  - `rag_engine.py` - RAG engine
  - `indexer.py` - Document indexing
  - `cli.py` - RAG CLI commands

**Import**: `from tools.rag.rag_engine import RAGEngine`

### Cognitive Layer (`light_of_the_seven.cognitive_layer`)

Cognitive decision support and mental models:

- **decision_support/** - Decision support algorithms
- **cognitive_load/** - Cognitive load management
- **mental_models/** - Mental model representations

**Import**: `from light_of_the_seven.cognitive_layer.decision_support import BoundedRationalityEngine`

## Import Patterns

### Canonical Imports (Preferred)

```python
# Core
from grid.essence.core_state import EssentialState
from grid.patterns.recognition import PatternRecognizer

# Applications
from application.mothership.main import app
from application.mothership.routers import intelligence_router

# Tools
from tools.rag.rag_engine import RAGEngine

# Cognitive
from light_of_the_seven.cognitive_layer.decision_support import BoundedRationalityEngine
```

### Deprecated Imports (Avoid)

```python
# OLD - Don't use
from src.grid...  # Use: from grid...
from src.application...  # Use: from application...
from src.tools...  # Use: from tools...
```

## Path-Sensitive Files

These files must remain at repository root (referenced by tests/scripts):

- `pyproject.toml`
- `README.md`
- `.gitignore`

**Note**: Benchmark/stress metric output files (`benchmark_metrics.json`, `benchmark_results.json`, `stress_metrics.json`) are now organized in the `data/` directory.

## Development Workflow

### Setting Up

1. Install dependencies:
   ```bash
   pip install -e .
   ```

2. Verify imports work:
   ```bash
   python -c "import grid; import application.mothership; import tools.rag"
   ```

### Running Tests

```bash
# All tests
pytest

# Specific test
pytest tests/unit/test_grid_intelligence.py
```

### Running Applications

```bash
# Mothership API
python backend/server.py

# Or directly
python -m application.mothership.main
```

## Documentation Structure

- **docs/structure/** - Structure documentation (this guide, terrain maps)
- **docs/architecture/** - Architecture documentation
- **docs/security/** - Security architecture
- **docs/research/** - Research findings and analysis
- **docs/reports/** - Status reports and summaries

## Legacy Code

Code in `legacy_src/` is being deprecated. Avoid importing from it in new code. If you need legacy modules:

1. Check if functionality exists in `src/`
2. If not, consider migrating it
3. If migration isn't feasible, add `legacy_src/` to `sys.path` temporarily

## Cleanliness Rules

See `docs/structure/cleanliness_rules.md` for what should never be committed (caches, venvs, etc.).

## Getting Help

- Check `docs/structure/terrain_map.md` for detailed structure analysis
- Check `docs/structure/MIGRATION_NOTES.md` for migration-related notes
- Check `docs/ARCHITECTURE.md` for architectural principles
