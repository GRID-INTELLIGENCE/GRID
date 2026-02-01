# Copilot Instructions for GRID

This document guides AI agents through the GRID (Geometric Resonance Intelligence Driver) codebase for productive development.

## Project Identity

GRID is a Python-based framework exploring complex systems through geometric resonance patterns. It combines a layered architecture (core → API → service → database), local-only RAG (Retrieval-Augmented Generation), cognitive decision support, event-driven agentic systems, and pattern recognition using 9 cognition patterns (Flow, Spatial, Rhythm, Color, Repetition, Deviation, Cause, Time, Combination).

## Architecture Overview

### Layered Structure
```
Application Layer (FastAPI/CLI)
↓
Service Layer (Business Logic)
↓
Database Layer (SQLAlchemy ORM)
↓
Core Layer (Foundation)
```

**Key Modules**:
- `src/grid/` - Core intelligence (essence, patterns, awareness, evolution, agentic system)
- `src/cognitive/` - Cognitive architecture and decision support
- `src/tools/rag/` - Local RAG system (ChromaDB + Ollama models)
- `src/application/` - FastAPI applications (Mothership, Canvas, Resonance)
- `src/unified_fabric/` - Async event bus with domain routing (safety, grid, coinbase)
- `docs/` - Documentation (indexed by RAG, use for context)

### Critical Boundaries
- Core layer has NO dependencies on upper layers
- Services depend on core but NOT application
- Database layer is pure data access (no business logic)
- API layer orchestrates services, never accesses DB directly
- Unified Fabric provides async pub/sub across domains (safety, grid, coinbase)

## Local-First Operation

**Non-negotiable**: NEVER suggest external APIs (OpenAI, Anthropic, etc.) unless explicitly requested.

- Use local Ollama models: `nomic-embed-text-v2-moe:latest` (embeddings), `ministral` or `gpt-oss-safeguard` (LLM)
- RAG context stays in `.rag_db/` (ChromaDB)
- Default to local solutions for all tasks

## Developer Workflows

### Environment Setup (UV-based)

**This repo uses UV as the Python venv/package manager.** Do not use `python -m venv` or `pip` directly—use UV for all venv and package operations.

```bash
# Quick setup with UV (recommended)
cd e:\grid
uv venv --python 3.13 --clear
.\.venv\Scripts\Activate.ps1
uv sync --group dev --group test

# Verify setup
pytest tests/unit/ -v
ruff check .
```

### Core Commands

**Tests** (default task, runs pytest with verbose output and coverage):
```bash
# All tests
pytest tests/ -v --tb=short

# Unit tests only (fast)
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Exclude slow tests
pytest -m "not slow"

# Coverage report
pytest --cov=src --cov-report=html
```

**RAG Operations**:
```bash
# Query knowledge base
python -m tools.rag.cli query "How does pattern recognition work?"

# Index/rebuild docs
python -m tools.rag.cli index docs/ --rebuild --curate

# RAG statistics
python -m tools.rag.cli stats
```

**Skills** (domain transformations and utilities with automated discovery):
```bash
# List available skills (auto-discovered from src/grid/skills/)
python -m grid skills list

# Run a skill with JSON args
python -m grid skills run transform.schema_map --args-json '{"text":"...", "target_schema":"resonance"}'

# Common skills: transform.schema_map, context.refine, compress.articulate, cross_reference.explain
```

**API Server**:
```bash
# Start Mothership API (main application)
python -m application.mothership.main

# Development server with reload
uvicorn application.mothership.main:app --reload --host 0.0.0.0 --port 8080
```

**Code Quality**:
```bash
# Linting (Ruff)
ruff check .
ruff check --fix .

# Formatting (Black)
black .

# Type checking (mypy)
mypy src/

# All quality checks (via Makefile)
make lint
make format
```

### Git Convention
- Branch naming: `{theme}-{short-desc}-#{issue}` (if using git-topic script)
- Commits should reference issue numbers
- Prefer making a backup branch before `git reset --hard`

## Code Standards

### Python Essentials
- **Version**: Python 3.13+ (pattern matching, improved errors)
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
├── unit/           # Pure function tests (fast, isolated)
├── integration/    # Component interaction (slower, cross-module)
├── api/           # API endpoint tests
├── security/      # Security and authentication tests
├── unified_fabric/ # Event bus and safety bridge tests
├── skills/        # Skills system tests
└── fixtures/      # Shared test data
```

Pattern: `test_{module_name}.py` mirrors source structure with `≥80%` coverage target.

**Test Markers** (use pytest markers):
- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests (slower, cross-module)
- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.critical` - Critical path tests (must pass)
- `@pytest.mark.slow` - Slow running tests (> 1 second)
- `@pytest.mark.scratch` - Experimental tests (excluded from CI)

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
Use `src/cognitive/cognitive_layer/` for:
- User-facing decision support
- Information presentation design
- Cognitive load estimation
- Bounded rationality constraints

```python
from cognitive.cognitive_layer.decision_support import BoundedRationalityEngine
# Apply cognitive factors to user-facing features
```

### Skills Registry Pattern
Domain transformations use `grid.skills.registry`:
- Implement `Skill` protocol (has `run(args: Mapping[str, Any]) -> Dict[str, Any]`)
- Auto-discovery from `src/grid/skills/` (no manual registration needed)
- Common skills: `transform.schema_map`, `context.refine`, `compress.articulate`, `intelligence.git_analyze`

```bash
# Run with strict JSON parameters
python -m grid skills run transform.schema_map --args-json '{"text": "...", "target_schema": "resonance"}'
```

### Unified Fabric Event System
Async event bus for cross-domain communication using a pub/sub pattern:
- **Domains**: `safety`, `grid`, `coinbase`, `all`
- **Subscription**: Use wildcards like `safety.*` to catch related events
- **Request-Reply**: Supports async futures for pseudo-synchronous needs

```python
from unified_fabric import get_event_bus, Event, EventDomain

event_bus = get_event_bus()

# Subscribe to domain-specific events
async def handle_safety_alert(event: Event):
    print(f"Safety breach in {event.source_domain}: {event.payload}")

event_bus.subscribe("safety.alert", handle_safety_alert, domain=EventDomain.SAFETY)

# Publish an event
await event_bus.publish(Event(
    event_type="safety.alert",
    payload={"threat": "path_traversal", "path": "/etc/passwd"},
    source_domain="grid"
))
```

### Agentic System Pattern
Implements a structured receptionist-lawyer-client workflow:
1. **Receptionist (Intake)**: Receives `CaseCreatedEvent` (raw input), converts to `CaseCategorizedEvent`.
2. **Lawyer (Processing)**: Generates `CaseReferenceGeneratedEvent` (references, workflow, roles).
3. **Executor (Action)**: Triggers `CaseExecutedEvent` and final `CaseCompletedEvent`.
4. **Learning**: Uses `intelligence_evaluator.py` to refine future responses based on results.

```python
from grid.agentic import AgenticSystem
from pathlib import Path

system = AgenticSystem(knowledge_base_path=Path("prompts/"))
# Triggers receptionist -> lawyer -> executor pipeline
result = await system.execute_case(case_id="123", reference_file_path="cases/ref.json")
```

### 4-Phase RAG Optimization
The RAG system in `src/tools/rag/` follows a strict performance pipeline:
1. **Semantic Chunking**: Split documentation at logical boundaries (functions, headers) via `SemanticChunker`.
2. **Hybrid Search**: Combine BM25 (sparse) and vector (dense) retrieval with `RRF` (Reciprocal Rank Fusion).
3. **Cross-Encoder Reranking**: Refine top-K results with a secondary pass using `OllamaReranker`.
4. **Evaluation**: Automated scoring of `Context Relevance` and `Answer Accuracy` via `evaluation.py`.

```python
# Enable via environment
export RAG_USE_HYBRID=true
export RAG_USE_RERANKER=true
```

### Testing Patterns & Fixtures
Use `tests/conftest.py` for shared isolation logic:
- `setup_env`: Disables DB and Redis connections to prevent test hangs.
- `reset_services`: Clears singleton states between tests.
- **Async Testing**: Always use `@pytest.mark.asyncio`.

```python
@pytest.mark.asyncio
async def test_event_flow(event_bus, sample_event):
    await event_bus.start()
    # Test logic here...
    await event_bus.stop()
```

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
- Main app: `src/application/mothership/main.py`

### Database Operations
- Use SQLAlchemy ORM (async-compatible)
- Manage sessions through dependency injection
- Keep database layer free of business logic
- Use migrations via Alembic for schema changes
- Test mode uses `sqlite:///:memory:` (configured in `tests/conftest.py`)

### Cognitive Decision Points
For user-facing features, consider:
- Cognitive load (information density)
- Mental model alignment (user expectations)
- Bounded rationality (simplify complex decisions)
- Information chunking (break into manageable pieces)

### Unified Fabric Integration
- Use `unified_fabric` for async event-driven communication
- Domain routing: `safety`, `grid`, `coinbase`
- Safety bridge: `AISafetyBridge` for cross-project validation
- Event schemas: `unified_fabric.event_schemas.validate_event()`

## File Reference Guide

| File/Directory | Purpose | Key Files |
|---|---|---|
| `.cursorrules` | Core project conventions | Main reference |
| `docs/` | Project documentation | `INTELLIGENT_SKILLS_SYSTEM.md`, `SKILLS_RAG_QUICKSTART.md`, `DEVELOPMENT_GUIDE.md` |
| `src/grid/` | Core intelligence | `essence/`, `patterns/`, `awareness/`, `agentic/`, `skills/` |
| `src/cognitive/` | Cognitive architecture | `cognitive_layer/`, `cognitive_engine.py` |
| `src/tools/rag/` | RAG system | `rag_engine.py`, `cli.py` |
| `src/application/` | FastAPI applications | `mothership/`, `canvas/`, `resonance/` |
| `src/unified_fabric/` | Event bus & safety | `event_bus.py`, `safety_bridge.py`, `domain_routing.py` |
| `tests/` | Test suite | Follow mirror structure with markers |
| `pyproject.toml` | Project config | Dependencies, tool configs, pytest settings |
| `Makefile` | Build commands | `make test`, `make lint`, `make format` |

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
- Verify UV environment: `uv sync --group dev --group test`
- Check test isolation: `pytest tests/unit/ -v` (should not require external services)
- Verify unified_fabric event bus: `pytest tests/unified_fabric/ -v`
