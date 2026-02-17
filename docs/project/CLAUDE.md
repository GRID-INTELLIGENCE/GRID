# CLAUDE.md - AI Assistant Guide for GRID

This document provides essential context for AI assistants working with the GRID codebase.

## Project Overview

**GRID (Geometric Resonance Intelligence Driver)** is a production-ready Python framework for complex systems analysis featuring:

- **Geometric Resonance Patterns**: 9 cognition patterns (Flow, Spatial, Rhythm, Color, Repetition, Deviation, Cause, Time, Combination)
- **Local-First RAG**: ChromaDB + Ollama (no external APIs by default)
- **Event-Driven Agentic System**: Case management with continuous learning
- **Cognitive Decision Support**: Bounded rationality and human-centered AI
- **Domain-Driven Design**: Professional architectural patterns

**Version**: 2.2.2
**Python**: 3.13 (required: >=3.13,<3.14)
**Package Manager**: UV (do NOT use pip directly)

## Quick Reference

### Essential Commands

```bash
# Environment setup
uv venv --python 3.13 --clear
source .venv/bin/activate  # Linux/Mac
uv sync --group dev --group test

# Run tests
uv run pytest tests/unit/ -v                    # Fast unit tests
uv run pytest tests/integration/ -v             # Integration tests
uv run pytest tests/ --cov=src --cov-report=term  # With coverage

# Code quality
uv run ruff check .                             # Lint
uv run ruff check . --fix                       # Auto-fix lint issues
uv run black src/ tests/                        # Format
uv run mypy src/                                # Type check

# Run application
uv run python -m application.mothership.main    # Start API server
make run                                         # Same via Makefile

# RAG operations
python -m tools.rag.cli query "your question"   # Query knowledge base
python -m tools.rag.cli index docs/ --rebuild   # Rebuild index

# Skills
python -m grid skills list                      # List available skills
python -m grid skills run transform.schema_map --args-json '{"text":"..."}'
```

### Makefile Commands

```bash
make install    # Sync dependencies via UV
make run        # Start Mothership API
make test       # Run tests
make lint       # Run ruff + mypy
make format     # Auto-format with black + ruff
make clean      # Remove build artifacts
```

## Architecture

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

### Critical Boundaries

- Core layer has NO dependencies on upper layers
- Services depend on core but NOT application
- Database layer is pure data access (no business logic)
- API layer orchestrates services, never accesses DB directly
- Unified Fabric provides async pub/sub across domains

### Source Code Layout

```
src/
├── grid/                   # Core intelligence (41 modules)
│   ├── agentic/           # Event-driven case management
│   ├── auth/              # Authentication & security
│   ├── billing/           # Subscription & usage tracking
│   ├── cognitive/         # Cognitive architecture
│   ├── context/           # User context management
│   ├── mcp/               # Model Context Protocol servers
│   ├── security/          # Security utilities
│   ├── skills/            # Intelligent skills ecosystem
│   └── workflow/          # Workflow orchestration
├── application/           # FastAPI applications
│   ├── mothership/        # Main API server (15+ subdirs)
│   ├── resonance/         # Real-time activity processing
│   └── canvas/            # Visualization backend
├── cognitive/             # Cognitive architecture (9 modules)
├── tools/                 # Development tools
│   └── rag/               # RAG system (local-first)
└── unified_fabric/        # Event bus & AI Safety bridge
```

### Key Directories

| Directory | Purpose |
|-----------|---------|
| `src/` | All source code |
| `tests/` | Test suite (unit, integration, api, security) |
| `docs/` | Documentation (150+ markdown files) |
| `config/` | Configuration files (22 files) |
| `scripts/` | Development and deployment scripts |
| `schemas/` | JSON schemas (31 files) |

## Code Standards

### Python Requirements

- **Version**: Python 3.13+ (use pattern matching, improved errors)
- **Type hints**: Required for ALL functions, methods, class attributes
- **Line length**: 120 characters (configured in pyproject.toml)
- **Formatter**: Black
- **Linter**: Ruff (rules: E, F, B, I, W, UP)
- **Type checker**: MyPy (strict mode)

### Import Style

```python
# Correct: Absolute imports for project modules
from grid.essence.core_state import EssentialState
from tools.rag.rag_engine import RAGEngine
from application.mothership.services import UserService

# Avoid: Relative imports for cross-module code
# Avoid: Wildcard imports
```

### Naming Conventions

- **Files/modules**: `snake_case` (e.g., `user_service.py`)
- **Classes**: `PascalCase` (e.g., `DatabaseConnection`)
- **Functions/variables**: `snake_case` (use verbs for functions)
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: Single underscore prefix `_internal_method`

## Testing

### Test Structure

```
tests/
├── unit/           # Fast, isolated tests
├── integration/    # Cross-module tests
├── api/            # API endpoint tests
├── auth/           # Authentication tests
├── billing/        # Billing feature tests
├── security/       # Security tests
├── unified_fabric/ # Event bus tests
├── cognitive/      # Cognitive engine tests
└── conftest.py     # Shared fixtures
```

### Test Markers

```python
@pytest.mark.unit        # Fast, isolated
@pytest.mark.integration # Slower, cross-module
@pytest.mark.api         # API endpoint tests
@pytest.mark.critical    # Must pass
@pytest.mark.slow        # > 1 second
@pytest.mark.scratch     # Experimental (excluded from CI)
@pytest.mark.asyncio     # Async tests
@pytest.mark.database    # Requires database
```

### Test Configuration

- **Coverage threshold**: 75% (fail-under configured)
- **Async mode**: Auto (`asyncio_mode = "auto"`)
- **Test database**: `sqlite:///:memory:` (in-memory)
- **External services**: Disabled in tests (Redis, Databricks)

### Running Tests

```bash
# Unit tests (fast feedback)
uv run pytest tests/unit/ -v

# Single test file
uv run pytest tests/unit/test_specific.py -v

# Single test function
uv run pytest tests/unit/test_file.py::test_function -v

# With coverage
uv run pytest tests/ --cov=src --cov-report=html

# Exclude slow tests
uv run pytest -m "not slow"

# Skip scratch/experimental
uv run pytest -m "not scratch"
```

## Local-First Operation

**Non-negotiable**: NEVER suggest external APIs (OpenAI, Anthropic, etc.) unless explicitly requested.

- Use local Ollama models: `nomic-embed-text-v2-moe:latest` (embeddings)
- RAG context stays in `.rag_db/` (ChromaDB)
- Default to local solutions for all tasks

### RAG System

The RAG system uses a 4-phase optimization pipeline:

1. **Semantic Chunking**: Context-aware document splitting
2. **Hybrid Search**: BM25 + Vector fusion (Reciprocal Rank Fusion)
3. **Cross-Encoder Reranking**: Secondary pass refinement
4. **Evaluation**: Automated quality scoring

```bash
# Enable advanced features via environment
export RAG_USE_HYBRID=true
export RAG_USE_RERANKER=true
```

## CI/CD Pipeline

### GitHub Actions Workflow

The CI pipeline (`.github/workflows/ci-main.yml`) includes:

1. **Secrets Scan**: Heuristic secret detection
2. **Smoke Test**: Quick environment verification
3. **Lint**: Ruff, Black, MyPy checks
4. **Security**: Bandit, pip-audit scanning
5. **Test**: Matrix testing (Python 3.11, 3.12, 3.13)
6. **Build**: Package building and verification
7. **Integration**: Extended tests (main branch only)
8. **Verify Deployment**: MCP servers and handlers

### Pre-commit Hooks

- **detect-secrets**: Enterprise secret scanner
- **gitleaks**: Fast secret scanning
- **API key patterns**: Custom detection

## Key Patterns

### Skills Registry

Domain transformations use auto-discovered skills:

```python
from grid.skills.registry import SkillRegistry

# Skills are auto-discovered from src/grid/skills/
# Implement Skill protocol: run(args: Mapping[str, Any]) -> Dict[str, Any]
```

### Unified Fabric Event System

```python
from unified_fabric import get_event_bus, Event, EventDomain

event_bus = get_event_bus()

# Subscribe to domain events
async def handle_event(event: Event):
    print(f"Received: {event.payload}")

event_bus.subscribe("safety.alert", handle_event, domain=EventDomain.SAFETY)

# Publish events
await event_bus.publish(Event(
    event_type="safety.alert",
    payload={"threat": "detected"},
    source_domain="grid"
))
```

### Agentic System

Implements receptionist-lawyer-client workflow:

1. **Receptionist (Intake)**: Receives and categorizes cases
2. **Lawyer (Processing)**: Generates references and workflow
3. **Executor (Action)**: Processes with role-based execution
4. **Learning**: Refines future responses based on results

```python
from grid.agentic import AgenticSystem

system = AgenticSystem(knowledge_base_path=Path("prompts/"))
result = await system.execute_case(case_id="123", reference_file_path="ref.json")
```

## Common Patterns & Anti-Patterns

### Do

- Read files before modifying them
- Use absolute imports for project modules
- Write tests alongside code
- Mock external dependencies in tests
- Use async/await for I/O operations
- Follow the layered architecture

### Don't

- Suggest external AI APIs without explicit request
- Use `pip` directly (use `uv` instead)
- Skip type hints on functions
- Access database directly from API routes
- Create circular dependencies between layers
- Commit credentials or secrets

## Important Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project config, dependencies, tool settings |
| `Makefile` | Development commands |
| `uv.lock` | Locked dependencies |
| `tests/conftest.py` | Shared test fixtures |
| `.github/workflows/ci-main.yml` | CI/CD pipeline |
| `config/.pre-commit-config.yaml` | Pre-commit hooks |

## API Endpoints

Main application runs on port 8080 by default:

```bash
# Health check
curl http://localhost:8080/health

# Authentication
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'

# Resonance API
curl -X POST http://localhost:8080/api/v1/resonance/process \
  -H "Content-Type: application/json" \
  -d '{"query": "...", "activity_type": "code"}'

# Agentic System
curl -X POST http://localhost:8080/api/v1/agentic/cases \
  -H "Content-Type: application/json" \
  -d '{"raw_input": "task description"}'
```

## Documentation Resources

- `docs/ARCHITECTURE.md` - Complete architecture with diagrams
- `docs/AGENTIC_SYSTEM.md` - Event-driven agentic system
- `docs/INTELLIGENT_SKILLS_SYSTEM.md` - Skills ecosystem
- `docs/SKILLS_RAG_QUICKSTART.md` - Skills + RAG guide
- `docs/EVENT_DRIVEN_ARCHITECTURE.md` - Event patterns
- `docs/security/SECURITY_ARCHITECTURE.md` - Security architecture

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure `PYTHONPATH=src` is set
2. **Test hangs**: Check database connections are mocked
3. **UV sync fails**: Try `uv sync --frozen`
4. **Type errors**: Run `uv run mypy src/` to see all issues

### Environment Variables (Test Mode)

```bash
MOTHERSHIP_ENVIRONMENT=test
MOTHERSHIP_DATABASE_URL=sqlite:///:memory:
MOTHERSHIP_USE_DATABRICKS=false
MOTHERSHIP_REDIS_ENABLED=false
MOTHERSHIP_RATE_LIMIT_ENABLED=false
```

## Git Conventions

- Branch naming: `{theme}-{short-desc}-#{issue}`
- Commits should reference issue numbers
- Prefer making a backup branch before `git reset --hard`
- Run tests before pushing: `uv run pytest tests/unit/ -v`
