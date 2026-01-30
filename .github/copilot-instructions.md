# Copilot Instructions for GRID

This document guides AI agents through the GRID (Geometric Resonance Intelligence Driver) codebase for productive development.

## Project Identity

GRID is a Python-based framework exploring complex systems through geometric resonance patterns. It combines a layered architecture (core → API → service → database), local-only RAG (Retrieval-Augmented Generation), cognitive decision support, and pattern recognition using 9 cognition patterns (Flow, Spatial, Rhythm, Color, Repetition, Deviation, Cause, Time, Combination).

## Architecture Overview

### Layered Structure
```
Application Layer (API/CLI)
↓
Service Layer (Business Logic)
↓
Database Layer (SQLAlchemy ORM)
↓
Core Layer (Foundation)
```

**Key Modules**:
- `grid/` - Core intelligence (essence, patterns, awareness, evolution, interfaces)
- `light_of_the_seven/cognitive_layer/` - Cognitive decision support and mental models
- `tools/rag/` - Local RAG system (ChromaDB + Ollama models)
- `application/` - Application-specific code (API routes, skills)
- `docs/` - Documentation (indexed by RAG, use for context)

### Critical Boundaries
- Core layer has NO dependencies on upper layers
- Services depend on core but NOT application
- Database layer is pure data access (no business logic)
- API layer orchestrates services, never accesses DB directly

## Local-First Operation

**Non-negotiable**: NEVER suggest external APIs (OpenAI, Anthropic, etc.) unless explicitly requested.

- Use local Ollama models: `nomic-embed-text-v2-moe:latest` (embeddings), `ministral` or `gpt-oss-safeguard` (LLM)
- RAG context stays in `.rag_db/` (ChromaDB)
- Default to local solutions for all tasks

## Developer Workflows

### Core Commands

**Tests** (default task, runs pytest with verbose output and coverage):
```bash
pytest tests/ -v --tb=short
```

**RAG Operations**:
```bash
# Query knowledge base
python -m tools.rag.cli query "How does pattern recognition work?"

# Index/rebuild docs
python -m tools.rag.cli index docs/ --rebuild --curate
```

**Skills** (domain transformations and utilities):
```bash
# Run a skill with JSON args
python -m grid skills run transform.schema_map --args-json '{"text":"...", "target_schema":"resonance"}'

# List available skills
python -m grid skills list
```

**Validation** (IDE context validation task):
```bash
python scripts/validate_ide_context.py
```

### Topic-Branch Workflow
The repo includes `scripts/git-topic` for theme-oriented work:
```bash
# Create feature branch with metadata
python scripts/git-topic create --theme research --short "entity clustering" --issue 123 --push

# Check branch metadata
python scripts/git-topic info

# Prepare PR from topic branch
python scripts/git-topic finish --open-pr
```

### Git Convention
- Branch naming: `{theme}-{short-desc}-#{issue}` (git-topic handles this)
- Commits should reference issue numbers
- Prefer making a backup branch before `git reset --hard`

## Code Standards

### Python Essentials
- **Version**: Python 3.11+ (pattern matching, improved errors)
- **Type hints**: Required for ALL functions, methods, class attributes
- **Formatter**: Black (120 char line length, configured in `pyproject.toml`)
- **Linter**: Ruff (pre-commit)
- **Type checker**: mypy (run before commits)
- **Style**: PEP 8 with project overrides (120 char limit)

### Import Discipline
```python
# ✓ Absolute imports for project modules
from grid.essence.core_state import EssentialState
from tools.rag.rag_engine import RAGEngine

# ✗ Avoid relative imports for cross-module code
# ✗ No wildcard imports
```

### Naming Conventions
- **Files/modules**: `snake_case` (e.g., `user_service.py`)
- **Classes**: `PascalCase` (e.g., `DatabaseConnection`)
- **Functions/variables**: `snake_case` (use verbs for functions)
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: Single underscore prefix `_internal_method`

### Test Organization
```
tests/
├── unit/           # Pure function tests
├── integration/    # Component interaction
├── api/           # API endpoint tests
├── benchmarks/    # Performance tests
└── fixtures/      # Shared test data
```

Pattern: `test_{module_name}.py` mirrors source structure with `≥80%` coverage target.

## Pattern References

### Pattern Language (9 Cognition Patterns)
When implementing features, consider which patterns apply:
1. **Flow**: Continuous processes and transitions
2. **Spatial**: Layout and positioning
3. **Rhythm**: Timing and repetition
4. **Color**: Category and attribute distinction
5. **Repetition**: Recurring structures
6. **Deviation**: Exceptions and anomalies
7. **Cause**: Causality and dependencies
8. **Time**: Temporal sequencing
9. **Combination**: Composite emergence

Check `docs/pattern_language.md` and search for similar implementations using RAG before creating new patterns.

### Cognitive Layer Integration
Use `light_of_the_seven/cognitive_layer/` for:
- User-facing decision support
- Information presentation design
- Cognitive load estimation
- Bounded rationality constraints

```python
from light_of_the_seven.cognitive_layer.decision_support import BoundedRationalityEngine
# Apply cognitive factors to user-facing features
```

### Skills Registry Pattern
Domain transformations use `grid.skills.registry`:
- Implement `Skill` protocol (has `run(args: Mapping[str, Any]) -> Dict[str, Any]`)
- Register in `default_registry`
- Examples: `transform.schema_map`, `context.refine`, `compress.articulate`

## Before Making Changes

### Reference First
1. **Check similar implementations**: Search codebase for existing patterns
2. **Query RAG**: Use RAG system to understand project context
3. **Read relevant architecture**: Check `.cursor/rules/architecture.md`
4. **Review tests**: Examine test patterns for the module

### Validate Architecture Fit
- Verify layered architecture alignment (core → service → API)
- Check module boundaries and dependencies
- Ensure separation of concerns
- Maintain stateless compute where possible

### Testing Requirements
- Write tests alongside code
- Use pytest fixtures for setup
- Mock external dependencies (including Ollama in unit tests)
- Aim for ≥80% coverage

## Integration Points

### RAG System Usage
Use RAG to:
- Understand project architecture
- Find existing patterns
- Retrieve relevant docs
- Understand decision history

```bash
python -m tools.rag.cli query "Where is X pattern implemented?"
```

### API Patterns
- Use FastAPI routers organized by domain
- Request/response models via Pydantic
- Middleware for CORS, logging, security
- Never access DB directly from routes (use services)

### Database Operations
- Use SQLAlchemy ORM (async-compatible)
- Manage sessions through dependency injection
- Keep database layer free of business logic
- Use migrations via Alembic for schema changes

### Cognitive Decision Points
For user-facing features, consider:
- Cognitive load (information density)
- Mental model alignment (user expectations)
- Bounded rationality (simplify complex decisions)
- Information chunking (break into manageable pieces)

## File Reference Guide

| File/Directory | Purpose | Key Files |
|---|---|---|
| `.cursorrules` | Core project conventions | Main reference |
| `.cursor/rules/` | Detailed architecture guides | `architecture.md`, `coding_standards.md` |
| `.windsurf/rules/` | Exhibit & canon governance | `grid-canon-policy.md` |
| `docs/` | Project documentation | `WHAT_CAN_I_DO.md`, `SKILLS_RAG_QUICKSTART.md` |
| `grid/` | Core intelligence | `essence/`, `patterns/`, `awareness/` |
| `light_of_the_seven/` | Cognitive architecture | `cognitive_layer/` |
| `tools/rag/` | RAG system | `rag_engine.py`, `cli.py` |
| `application/` | Application code | API, CLI, services |
| `tests/` | Test suite | Follow mirror structure |

## Decision-Making Framework

**When starting a task**:
1. Read relevant files (not the whole codebase—be targeted)
2. Check architecture constraints
3. Search for similar implementations
4. Query RAG if needed for project context
5. Verify fit with cognitive layer (if user-facing)
6. Create/update tests first (TDD where practical)

**When uncertain**:
- Prefer adapting existing patterns over creating new ones
- Check `.cursor/rules/` for guidance
- Use RAG to understand project decisions
- Reference existing similar implementations

## Quick Debugging Checklist

- Run `python scripts/validate_ide_context.py` to check environment setup
- Check `.rag_db/` exists (RAG database)
- Verify Ollama models installed: `ollama list`
- Run tests with `pytest tests/ -v --tb=short`
- Check `benchmark_metrics.json` for performance SLA compliance (0.1ms guard)
