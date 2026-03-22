## User

You are auditing the GRID project's ARCHITECTURAL DESIGN and CONTRACT system. The project lives at:
- `roots/GRID/` (infrastructure library)  
- `CascadeProjects/GRID-main/` (nested repo)

Your job: Deep filesystem audit of the architecture and contract layers. Specifically:

1. Read `roots/GRID/CLAUDE.md` and `roots/GRID/docs/project/CLAUDE.md` for architectural overview.
2. List `roots/GRID/src/` directory structure to understand module layout.
3. List `CascadeProjects/GRID-main/src/` directory structure.
4. Read the boundary/transition gate contracts:
   - `CascadeProjects/GRID-main/boundaries/transition_gate/contracts/transition-gate-contract.template.json`
   - `CascadeProjects/GRID-main/boundaries/transition_gate/contracts/c-receiving-agent.contract.json`
   - `CascadeProjects/GRID-main/boundaries/transition_gate/contracts/e-source-agent.contract.json`
5. Read the contract system implementation:
   - `roots/GRID/src/grid/resilience/accountability/contracts.py`
   - `roots/GRID/src/grid/resilience/accountability/contract_loader.py`
   - `CascadeProjects/GRID-main/src/grid/resilience/accountability/contracts.py`
   - `CascadeProjects/GRID-main/src/grid/resilience/accountability/contract_loader.py`
6. Read `roots/GRID/config/contracts/openapi.yaml`
7. Read the parasite guard: `roots/GRID/src/infrastructure/parasite_guard/contracts.py`
8. Read the accountability middleware: `roots/GRID/src/application/mothership/middleware/accountability_contract.py`
9. Read the debug and post-11pm contracts:
   - `roots/GRID/.grid/debug-contract.json`
   - `roots/GRID/.grid/post-11pm-contract.json`
10. List `roots/GRID/boundaries/` directory tree.
11. Search for "boundary", "gate", "envelope", "nonce" patterns in `roots/GRID/src/` to find all boundary enforcement code.

Produce a structured report with:
- **Module Architecture**: How src/ is organized (domain layers, boundaries, infrastructure)
- **Contract System Design**: How contracts are defined, loaded, enforced
- **Transition Gate**: The boundary crossing mechanism and its guarantees
- **Accountability Chain**: How actions are tracked and attributed
- **Parasite Guard**: What it protects against
- **Contract Variants**: Debug vs production vs post-11pm — what changes
- **Design Patterns**: Key patterns used (envelope, nonce, etc.)
- **Structural Gaps**: Anything architecturally incomplete or inconsistent between roots/GRID and CascadeProjects/GRID-main

## Assistant





<thinking>
This is a comprehensive architectural audit of the GRID project. Let me break this down into parallel and sequential steps. I'll start by making all the independent reads and listings in parallel.

Let me group the independent calls:

Group 1 (all independent):
- Read roots/GRID/CLAUDE.md
- Read roots/GRID/docs/project/CLAUDE.md
- List roots/GRID/src/
- List CascadeProjects/GRID-main/src/
- List roots/GRID/boundaries/
- Read the three transition gate contracts
- Read roots/GRID/config/contracts/openapi.yaml
- Read the debug and post-11pm contracts


- Read contract system implementation files
- Read parasite guard
- Read accountability middleware

Once I have the structure mapped out, I'll search for specific patterns across the codebase to understand how these components interact.
</thinking>

I'll start by reading all the independent files and listings in parallel. This is a big audit — let me gather everything at once.

**Tool Call: Read file `roots/GRID/CLAUDE.md`**
Status: Completed

````roots/GRID/CLAUDE.md
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GRID (Geometric Resonance Intelligence Driver) is a local-first AI framework built on Python 3.13, FastAPI, SQLAlchemy, and ChromaDB+Ollama for RAG. It uses domain-driven design with event-driven agentic workflows, a 9-pattern cognitive intelligence engine, and layered security/safety enforcement. Version 2.7.0, MIT license, repo at `github.com/GRID-INTELLIGENCE/GRID`.

## Commands

```bash
# Install / sync environment
uv sync --group dev --group test

# Run all tests (unit + integration + security + API)
uv run pytest tests/unit tests/integration tests/security tests/api -q --tb=short

# Run a single test file
uv run pytest tests/unit/test_example.py -q --tb=short

# Run a single test function
uv run pytest tests/unit/test_example.py::test_function_name -v

# Run tests by marker
uv run pytest -m unit -q --tb=short
uv run pytest -m safety -q --tb=short
uv run pytest -m security -q --tb=short

# Safety module tests (separate test root)
uv run pytest safety/tests -q --tb=short

# Boundary module tests
uv run pytest boundaries/tests -q --tb=short

# Lint
uv run ruff check .

# Auto-fix lint + format
uv run ruff format . && uv run ruff check . --fix

# Type check
uv run mypy src/grid/ src/application/ src/tools/ src/search/ src/cognitive/ src/mycelium/

# Start Mothership API (port 8080)
uv run python -m application.mothership.main

# Start API Gateway (port 8000, routes to Mothership)
uv run python -m src.main

# CLI
uv run python -m grid --help

# Session start verification (run before writing new code)
uv run python -m pytest -q --tb=short && uv run ruff check work/ safety/ security/ boundaries/

# Makefile shortcuts
make test        # Run tests
make lint        # Ruff + Mypy
make format      # Auto-format
make clean       # Remove caches
```

## Architecture

### Layer Diagram

```
CLI (grid/__main__)  →  API Gateway (port 8000)  →  Mothership API (port 8080)
                                                          │
                    ┌─────────────┬───────────────┬───────┴────────┐
                    │             │               │                │
              Grid Core     Cognitive        Search/RAG      Mycelium
             (src/grid/)   (src/cognitive/)  (src/search/)  (src/mycelium/)
                    │             │               │                │
                    └─────────────┴───────┬───────┴────────────────┘
                                          │
                                  Unified Fabric
                               (src/unified_fabric/)
                           routing, adapters, safety bridge
```

### Source Packages (`src/`)

| Package | Role |
|---------|------|
| `grid/` | Core intelligence: state machine (essence), 9 cognition patterns, awareness, evolution, quantum architecture, multi-tenant organization, auth, skills |
| `application/` | Mothership Cockpit FastAPI app: versioned routers (v1, v2), session management, alerts, component registry |
| `cognitive/` | Cognitive processing: interaction tracking, temporal reasoning, flow management, resonance bridging, 9 patterns (Flow, Spatial, Rhythm, Color, Repetition, Deviation, Cause, Time, Combination) |
| `search/` | RAG-augmented search: query parsing, retrieval, ranking, indexing, chunking, embedding, safety guardrails |
| `mycelium/` | Knowledge federation: persona system, lens discovery, multi-perspective synthesis |
| `unified_fabric/` | Cross-project routing: domain router (SAFETY, GRID, COINBASE, PATHWAYS), async pub/sub with Redis, AI safety bridge |
| `tools/` | CLI utilities: RAG tools, crypto, forensics, dashboards, skill store |
| `infrastructure/` | API gateway (circuit breaker, dynamic routing), event bus (Redis pub/sub + in-memory fallback), service mesh, parasite guard, logging/metrics |
| `vection/` | Distributed worker protocols and concurrency coordination |

### Peer Security Modules (outside `src/`)

| Module | Purpose |
|--------|---------|
| `safety/` | AI safety: GUARDIAN rule engine (Aho-Corasick + regex), content detectors (pre/post-check), escalation, PII privacy engine, audit logging, observability, canary tokens |
| `security/` | Network interceptor (deny-by-default, monkey-patches network libs), forensic analysis, incident response |
| `boundaries/` | Boundary contracts (consent, refusal rights), overwatch, transition gate (9-step sealed-envelope handshake with HMAC-SHA256, nonce replay prevention) |

These three modules enforce security invariants independently. Never weaken validation, add bypass paths, or remove existing checks. See `.claude/rules/safety.md` and `.claude/rules/behavioral-shield.md`.

### Additional Top-Level Modules

| Module | Purpose |
|--------|---------|
| `knowledge_base/` | Databricks SQL-backed RAG system (separate from `src/search/` local RAG). Has its own embeddings, ingestion pipeline, search retriever, and API routes |
| `frontend/` | React 19 + TypeScript + Electron desktop app. Dev: `npm run dev`, Lint: `npm run lint`, Test: `npm test` |

### Key Entry Points

- **CLI**: `src/grid/__main__.py` — commands: `serve`, `analyze`, `chat`, `skills`, `process`, `run`
- **Mothership API**: `src/application/mothership/main.py` — port 8080
- **API Gateway**: `src/infrastructure/api_gateway/gateway.py` → `src/main.py` — port 8000
- **RAG Chat**: `grid chat` or `grid run rag` — uses Ollama (default model: ministral-3:3b)
- **Boundary Toolkit CLI**: `boundaries/toolkit/__main__.py` — commands: `seal`, `verify`, `test`, `demo`, `report`

### Mothership Middleware Chain (order matters)

```
Request → RequestID → RequestLogging → Timing → ErrorHandling → SecurityHeaders
       → UsageTracking → RateLimit → SafetyMiddleware → DRTMiddleware
       → AccountabilityContract → ParasiteGuard → Router
```

SafetyMiddleware is mandatory in production. ParasiteGuard detects malicious code injection. DRTMiddleware monitors behavioral anomalies.

### Dependency Injection (Mothership)

Core dependencies in `src/application/mothership/dependencies.py`:
- `get_settings()` → `MothershipSettings` (env-based config: dev/staging/prod/test)
- `get_store()` → `StateStore` (persistence)
- `get_uow()` → `DbUnitOfWork` (database transactions)
- `get_cockpit_service()` → `CockpitService` (facade over SessionService, OperationService, ComponentService, AlertService)

### Dual Event Bus Architecture

Two event systems exist for different scopes:
1. **Infrastructure EventBus** (`src/infrastructure/event_bus/event_system.py`): Priority-based events with correlation/causation tracking. Redis pub/sub with in-memory fallback.
2. **Unified Fabric DynamicEventBus** (`src/unified_fabric/__init__.py`): Domain-aware async routing across SAFETY, GRID, COINBASE, PATHWAYS domains.

### Test Structure

Tests live in `tests/` with 37 subdirectories per concern: `unit/`, `integration/`, `e2e/`, `api/`, `security/`, `safety/`, `agentic/`, `auth/`, `billing/`, `cognitive/`, `mycelium/`, `resilience/`, `chaos/`, `load/`, `performance/`, `unified_fabric/`, and more. Safety module has its own tests at `safety/tests/`. Boundary tests at `boundaries/tests/`.

### Pytest Configuration

- `asyncio_mode = "auto"` — no need for `@pytest.mark.asyncio`
- Default timeout: 30s per test
- Markers: `unit`, `integration`, `safety`, `security`, `api`, `critical`, `slow`, `flaky`, `redteam`, `smoke`
- `--maxfail=5` and `-m "not scratch and not flaky and not slow"` by default
- `pythonpath = ["src"]` — imports resolve from `src/`
- Coverage minimum: 75% (`--cov-fail-under=75`)
- Performance budget: full suite < 30 seconds; profile with `--durations=10`

### Test Environment

`tests/conftest.py` sets critical env vars for isolation:
- `MOTHERSHIP_ENVIRONMENT=test`, `MOTHERSHIP_DATABASE_URL=sqlite:///:memory:`
- `RAG_VECTOR_STORE_PROVIDER=in_memory`, `RAG_EMBEDDING_PROVIDER=simple`
- `SAFETY_BYPASS_REDIS=true`, `MOTHERSHIP_REDIS_ENABLED=false`
- `ENABLE_DEV_TOKEN=1` (enables dev-test-token auth in test API client)
- Auto-marker system maps test directory names to pytest markers automatically
- `reset_services()` autouse fixture ensures per-test singleton isolation (see `tests/utils/reset_helpers.py`)

## Conventions

- **Package manager**: `uv` exclusively — never bare `python`, `pip`, or `python -m venv`
- **Python**: 3.13 — use modern syntax (match/case, `X | Y` unions, StrEnum)
- **Type hints**: Required on all function signatures
- **Line length**: 120 characters (ruff configured)
- **Linter/formatter**: ruff only (not black, isort, or pylint)
- **Logging**: `structlog` — no bare `print()` in production code
- **Data models**: Pydantic v2 (`model_validator`, not `@validator`)
- **Async-first**: Prefer `async def` for I/O operations
- **Commits**: Conventional format — `feat(module):`, `fix(security):`, `test(safety):`, `docs(adr):`
- **Local-first AI**: Ollama + ChromaDB by default — never suggest external APIs unless explicitly requested
- **Prohibited**: `eval()`, `exec()`, `pickle` — use AST-based evaluation only
- **Imports**: `conftest.py` ensures `src/` is first on `sys.path` so `grid.*` resolves to `src/grid/`
- **Layer boundaries**: Core has no dependencies on upper layers. Services depend on core but not application. API layer orchestrates services, never accesses DB directly.
- **Line endings**: LF (`\n`), not CRLF. See `.editorconfig`.

## CI Pipeline

GitHub Actions at `.github/workflows/ci.yml` runs on push/PR to main:
- **secrets-scan** → **lint** (ruff) → **type-check** (mypy) → **test-unit** → **test-integration** → **test-security** → **test-api** → **build-wheel**
- Environment: ubuntu-latest, Python 3.13, `uv` for package management
- Concurrency: cancel-in-progress grouped by workflow ref

## Decision Logging

Architectural decisions go in `docs/decisions/DECISIONS.md` with date, decision, rationale, and alternatives considered.

````


**Tool Call: Read file `roots/GRID/docs/project/CLAUDE.md`**
Status: Completed

````roots/GRID/docs/project/CLAUDE.md
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**GRID (Geometric Resonance Intelligence Driver)** is a production-ready Python framework for complex systems analysis featuring:

- **Geometric Resonance Patterns**: 9 cognition patterns (Flow, Spatial, Rhythm, Color, Repetition, Deviation, Cause, Time, Combination)
- **Local-First RAG**: ChromaDB + Ollama (no external APIs by default)
- **Event-Driven Agentic System**: Case management with continuous learning
- **Cognitive Decision Support**: Bounded rationality and human-centered AI
- **Domain-Driven Design**: Professional architectural patterns

**Version**: 2.6.1
**Python**: 3.13 (required: >=3.13,<3.14)
**Package Manager**: UV (do NOT use pip directly)

**Packaging (pyproject.toml):** Wheel ships 9 packages: `src/grid`, `src/application`, `src/cognitive`, `src/tools`, `src/mycelium`, `src/search`, `src/infrastructure`, `src/unified_fabric`, `src/vection`. Dependency groups: **test** (pytest, etc.), **dev** (hatch, ruff, mypy), **finetuning** (torch, transformers, peft — optional; RAG intent classifier uses rule-based fallback without it).

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
uv run ruff format src/ tests/                   # Format
uv run mypy src/grid/ src/application/ src/tools/ src/search/ src/cognitive/ src/mycelium/   # Type check (or make lint)

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
make format     # Auto-format with ruff format + ruff check --fix
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
│   └── rag/               # RAG system (local-first, optional torch/transformers)
├── mycelium/              # Pattern recognition & synthesis
├── search/                # Search API, guardrails, retrieval
├── infrastructure/        # Parasite guard, metrics, event bus
├── unified_fabric/        # Event bus & cross-project bridge
└── vection/               # Velocity and emergence components
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
- **Formatter**: Ruff (not Black)
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

## Session Start Protocol

Before writing ANY new code, run:
```bash
uv run python -m pytest -q --tb=short && uv run ruff check work/ safety/ security/ boundaries/
```
If tests fail, fix them before doing anything else.

## Behavioral Shield

Never produce aggregate behavioral readings of `safety/`, `security/`, or `boundaries/` modules. Reading files for bugs/features is fine. Bulk extraction of defensive parameters (rate limits, canary patterns, guardian rules, auth tiers, risk weights) is denied. See `.claude/rules/behavioral-shield.md`.

## Git Conventions

- Branch naming: `{theme}-{short-desc}-#{issue}`
- Commits should reference issue numbers
- Prefer making a backup branch before `git reset --hard`
- Run tests before pushing: `uv run pytest tests/unit/ -v`

````


**Tool Call: List the `roots/GRID/src` directory's contents**
Status: Completed

# Folders:
caraxes/roots/GRID/src/application
caraxes/roots/GRID/src/cognitive
caraxes/roots/GRID/src/grid
caraxes/roots/GRID/src/infrastructure
caraxes/roots/GRID/src/integration
caraxes/roots/GRID/src/mycelium
caraxes/roots/GRID/src/search
caraxes/roots/GRID/src/security
caraxes/roots/GRID/src/tools
caraxes/roots/GRID/src/unified_fabric
caraxes/roots/GRID/src/vection

# Files:
caraxes/roots/GRID/src/__init__.py
caraxes/roots/GRID/src/benchmark_rag.py
caraxes/roots/GRID/src/main.py
caraxes/roots/GRID/src/rag_chat.py
caraxes/roots/GRID/src/test_semantic_chunking.py


**Tool Call: List the `CascadeProjects/GRID-main/src` directory's contents**
Status: Completed

# Folders:
caraxes/CascadeProjects/GRID-main/src/application
caraxes/CascadeProjects/GRID-main/src/cognitive
caraxes/CascadeProjects/GRID-main/src/grid
caraxes/CascadeProjects/GRID-main/src/infrastructure
caraxes/CascadeProjects/GRID-main/src/integration
caraxes/CascadeProjects/GRID-main/src/mycelium
caraxes/CascadeProjects/GRID-main/src/search
caraxes/CascadeProjects/GRID-main/src/security
caraxes/CascadeProjects/GRID-main/src/tools
caraxes/CascadeProjects/GRID-main/src/unified_fabric
caraxes/CascadeProjects/GRID-main/src/vection

# Files:
caraxes/CascadeProjects/GRID-main/src/__init__.py
caraxes/CascadeProjects/GRID-main/src/benchmark_rag.py
caraxes/CascadeProjects/GRID-main/src/main.py
caraxes/CascadeProjects/GRID-main/src/rag_chat.py
caraxes/CascadeProjects/GRID-main/src/test_semantic_chunking.py


**Tool Call: List the `roots/GRID/boundaries` directory's contents**
Status: Completed

# Folders:
caraxes/roots/GRID/boundaries/config
caraxes/roots/GRID/boundaries/examples
caraxes/roots/GRID/boundaries/tests
caraxes/roots/GRID/boundaries/toolkit
caraxes/roots/GRID/boundaries/transition_gate

# Files:
caraxes/roots/GRID/boundaries/DIAGNOSTIC_RESOLUTION.md
caraxes/roots/GRID/boundaries/README.md
caraxes/roots/GRID/boundaries/Understand Branch Context.md
caraxes/roots/GRID/boundaries/__init__.py
caraxes/roots/GRID/boundaries/boundary.py
caraxes/roots/GRID/boundaries/logger_ws.py
caraxes/roots/GRID/boundaries/overwatch.py
caraxes/roots/GRID/boundaries/preparedness.py
caraxes/roots/GRID/boundaries/pyproject.toml
caraxes/roots/GRID/boundaries/refusal.py
caraxes/roots/GRID/boundaries/schema.py
caraxes/roots/GRID/boundaries/server_ws.py
caraxes/roots/GRID/boundaries/uv.lock


**Tool Call: Read file `CascadeProjects/GRID-main/boundaries/transition_gate/contracts/transition-gate-contract.template.json`**
Status: Completed

```CascadeProjects/GRID-main/boundaries/transition_gate/contracts/transition-gate-contract.template.json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "transition-gate-contract-template-v1",
  "title": "Transition Gate Agent Contract Template",
  "description": "Schema for machine-readable contracts governing sealed-envelope transfers between partitions. Each agent (source/seal side, receiving/verify side) gets its own contract file conforming to this template.",
  "version": "1.0.0",
  "type": "object",
  "required": [
    "contract_id",
    "contract_version",
    "agent_role",
    "partition",
    "security_primitives",
    "pipeline",
    "never_rules",
    "scope_enforcement",
    "audit"
  ],
  "properties": {
    "contract_id": {
      "type": "string",
      "description": "Unique identifier for this contract instance (UUID4 recommended)."
    },
    "contract_version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+$",
      "description": "Semantic version of this contract."
    },
    "agent_role": {
      "type": "string",
      "enum": ["source", "receiver"],
      "description": "Whether this agent seals envelopes (source) or verifies them (receiver)."
    },
    "partition": {
      "type": "object",
      "required": ["label", "root_path", "purpose"],
      "properties": {
        "label": {
          "type": "string",
          "description": "Human-readable partition label (e.g. 'E:\\' or 'C:\\')."
        },
        "root_path": {
          "type": "string",
          "description": "Filesystem root path for this partition's workspace."
        },
        "purpose": {
          "type": "string",
          "enum": ["source_build", "deployment_target", "hybrid"],
          "description": "The role this partition plays in the transfer pipeline."
        },
        "staging_path": {
          "type": "string",
          "description": "Path where sealed envelopes are staged (DROP for source, PICKUP for receiver)."
        }
      }
    },
    "security_primitives": {
      "type": "object",
      "required": ["user_fingerprint", "machine_fingerprint", "nonce", "payload_hash", "envelope_expiry"],
      "properties": {
        "user_fingerprint": {
          "type": "object",
          "properties": {
            "algorithm": { "type": "string", "const": "HMAC-SHA256" },
            "key_source": {
              "type": "string",
              "description": "How the shared secret is obtained (e.g. 'windows_credential_manager', 'env_var', 'keyring')."
            },
            "key_name": {
              "type": "string",
              "description": "Name/identifier of the stored secret."
            },
            "binding_factors": {
              "type": "array",
              "items": { "type": "string" },
              "description": "What the HMAC message includes (e.g. ['machine_fingerprint', 'partition_label'])."
            }
          }
        },
        "machine_fingerprint": {
          "type": "object",
          "properties": {
            "algorithm": { "type": "string", "const": "SHA-256" },
            "attributes": {
              "type": "array",
              "items": { "type": "string" },
              "description": "OS attributes hashed (e.g. ['node_name', 'platform_system', 'platform_machine', 'username'])."
            }
          }
        },
        "nonce": {
          "type": "object",
          "properties": {
            "format": { "type": "string", "const": "uuid4_hex" },
            "registry_path": {
              "type": "string",
              "description": "Filesystem path to the persistent nonce registry JSON."
            },
            "single_use": { "type": "boolean", "const": true },
            "burn_on_verify": { "type": "boolean", "const": true }
          }
        },
        "payload_hash": {
          "type": "object",
          "properties": {
            "algorithm": { "type": "string", "const": "SHA-256" },
            "serialization": {
              "type": "string",
              "const": "canonical_json",
              "description": "Payload is serialized to JSON with sorted keys and no extra whitespace before hashing."
            }
          }
        },
        "envelope_expiry": {
          "type": "object",
          "properties": {
            "max_age_seconds": {
              "type": "number",
              "minimum": 60,
              "maximum": 3600,
              "default": 600,
              "description": "Maximum age of an envelope before it is rejected as stale."
            }
          }
        }
      }
    },
    "pipeline": {
      "type": "object",
      "required": ["steps"],
      "properties": {
        "description": {
          "type": "string",
          "description": "Human-readable summary of this pipeline."
        },
        "fail_mode": {
          "type": "string",
          "enum": ["fail_closed", "fail_open"],
          "default": "fail_closed",
          "description": "What happens when a step fails. Must be fail_closed for security."
        },
        "steps": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["step_number", "name", "description", "on_failure"],
            "properties": {
              "step_number": { "type": "integer", "minimum": 1 },
              "name": { "type": "string" },
              "description": { "type": "string" },
              "command": {
                "type": "string",
                "description": "Optional shell command or function call for this step."
              },
              "expected_output": {
                "type": "string",
                "description": "What a passing result looks like."
              },
              "on_failure": {
                "type": "string",
                "enum": ["abort", "reject_envelope", "log_and_continue", "escalate"],
                "description": "Action to take if this step fails."
              },
              "timeout_seconds": {
                "type": "number",
                "description": "Maximum time allowed for this step."
              }
            }
          }
        }
      }
    },
    "never_rules": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "rule", "severity"],
        "properties": {
          "id": {
            "type": "string",
            "description": "Unique rule identifier (e.g. 'NR-01')."
          },
          "rule": {
            "type": "string",
            "description": "Plain-language description of what must never happen."
          },
          "severity": {
            "type": "string",
            "enum": ["critical", "high", "medium"],
            "description": "How severe a violation of this rule would be."
          },
          "enforcement": {
            "type": "string",
            "enum": ["automated", "review", "both"],
            "description": "How this rule is enforced."
          }
        }
      },
      "description": "Invariants that must never be violated by this agent."
    },
    "scope_enforcement": {
      "type": "object",
      "required": ["known_permissions", "default_permission", "principle"],
      "properties": {
        "known_permissions": {
          "type": "array",
          "items": { "type": "string" },
          "description": "All recognized permission strings (e.g. ['deploy', 'run_tests', 'read_only', ...])."
        },
        "default_permission": {
          "type": "string",
          "description": "Permission used when no scope is explicitly declared."
        },
        "principle": {
          "type": "string",
          "const": "least_privilege",
          "description": "The principle governing scope assignment."
        },
        "unknown_permission_action": {
          "type": "string",
          "enum": ["reject", "log_and_reject", "escalate"],
          "default": "reject",
          "description": "What to do when an unrecognized permission is requested."
        }
      }
    },
    "audit": {
      "type": "object",
      "required": ["enabled", "format", "log_path"],
      "properties": {
        "enabled": { "type": "boolean", "default": true },
        "format": {
          "type": "string",
          "enum": ["ndjson", "json", "csv"],
          "default": "ndjson"
        },
        "log_path": {
          "type": "string",
          "description": "Path to the audit log file."
        },
        "retention_days": {
          "type": "integer",
          "minimum": 7,
          "default": 90,
          "description": "How long audit entries are retained."
        },
        "overwatch_integration": {
          "type": "boolean",
          "default": true,
          "description": "Whether audit events are also fed to Overwatch for alerting."
        }
      }
    },
    "kpis": {
      "type": "object",
      "description": "Key performance indicators tracked by this agent.",
      "properties": {
        "transfer_success_rate": {
          "type": "object",
          "properties": {
            "target": { "type": "number", "minimum": 0, "maximum": 1 },
            "window": { "type": "string" }
          }
        },
        "verification_latency_ms": {
          "type": "object",
          "properties": {
            "p50_target": { "type": "number" },
            "p99_target": { "type": "number" }
          }
        },
        "replay_attempt_rate": {
          "type": "object",
          "properties": {
            "alert_threshold": { "type": "number" },
            "window": { "type": "string" }
          }
        }
      }
    },
    "overwatch_escalation": {
      "type": "object",
      "properties": {
        "threshold_count": {
          "type": "integer",
          "minimum": 1,
          "default": 3,
          "description": "Number of events of the same type within the window to trigger escalation."
        },
        "window_minutes": {
          "type": "integer",
          "minimum": 1,
          "default": 60,
          "description": "Time window for escalation threshold."
        },
        "notify_channels": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Channels to notify on escalation (e.g. ['slack', 'email', 'pagerduty'])."
        },
        "escalation_events": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Event types that count toward escalation (e.g. ['rejected:fingerprint_mismatch', 'rejected:nonce_replay_or_expired'])."
        }
      }
    }
  },
  "additionalProperties": false
}

```


**Tool Call: Read file `CascadeProjects/GRID-main/boundaries/transition_gate/contracts/c-receiving-agent.contract.json`**
Status: Completed

```CascadeProjects/GRID-main/boundaries/transition_gate/contracts/c-receiving-agent.contract.json
{
  "contract_id": "c-receiving-agent-v1-2026",
  "contract_version": "1.0.0",
  "agent_role": "receiver",
  "partition": {
    "label": "C:\\",
    "root_path": "C:\\Users\\USER\\cascadeprojects",
    "purpose": "deployment_target",
    "staging_path": "C:\\Users\\USER\\cascadeprojects\\gate\\incoming"
  },
  "security_primitives": {
    "user_fingerprint": {
      "algorithm": "HMAC-SHA256",
      "key_source": "windows_credential_manager",
      "key_name": "TransitionGate",
      "binding_factors": ["machine_fingerprint", "partition_label"]
    },
    "machine_fingerprint": {
      "algorithm": "SHA-256",
      "attributes": ["node_name", "platform_system", "platform_machine", "username"]
    },
    "nonce": {
      "format": "uuid4_hex",
      "registry_path": "C:\\Users\\USER\\cascadeprojects\\gate\\.nonce_registry.json",
      "single_use": true,
      "burn_on_verify": true
    },
    "payload_hash": {
      "algorithm": "SHA-256",
      "serialization": "canonical_json"
    },
    "envelope_expiry": {
      "max_age_seconds": 600
    }
  },
  "pipeline": {
    "description": "9-step verification pipeline: validate envelope integrity, verify identity, enforce scope, burn nonce, audit.",
    "fail_mode": "fail_closed",
    "steps": [
      {
        "step_number": 1,
        "name": "envelope_exists",
        "description": "Check that a sealed envelope JSON file exists in gate/incoming/ and can be parsed. Verify all required fields are present: envelope_id, payload, payload_hash, nonce, timestamp, user_fingerprint, machine_fingerprint, scope.",
        "command": "python -c \"from boundaries.transition_gate import TransitionEnvelope; e = TransitionEnvelope.from_file('gate/incoming/envelope_*.json'); print('OK')\"",
        "expected_output": "Envelope loaded with all required fields present.",
        "on_failure": "reject_envelope",
        "timeout_seconds": 10
      },
      {
        "step_number": 2,
        "name": "payload_integrity",
        "description": "Recompute SHA-256 hash of the payload using canonical JSON serialization (sorted keys, no extra whitespace). Compare against envelope.payload_hash using timing-safe comparison.",
        "command": null,
        "expected_output": "Recomputed hash matches envelope.payload_hash.",
        "on_failure": "reject_envelope",
        "timeout_seconds": 10
      },
      {
        "step_number": 3,
        "name": "fingerprint_match",
        "description": "Recompute user fingerprint using the shared secret (from Windows Credential Manager) and the machine_fingerprint embedded in the envelope. Compare against envelope.user_fingerprint using hmac.compare_digest (timing-safe).",
        "command": null,
        "expected_output": "User fingerprint matches (timing-safe comparison).",
        "on_failure": "reject_envelope",
        "timeout_seconds": 10
      },
      {
        "step_number": 4,
        "name": "nonce_valid",
        "description": "Check that the nonce exists in the shared nonce registry, has not been burned, and has not expired. If valid, mark as pending-burn (actual burn happens after all checks pass).",
        "command": null,
        "expected_output": "Nonce is valid, unburned, and within max_age_seconds.",
        "on_failure": "reject_envelope",
        "timeout_seconds": 5
      },
      {
        "step_number": 5,
        "name": "timestamp_fresh",
        "description": "Verify that the envelope's timestamp is within max_age_seconds (default 600s / 10 minutes) of current time. Reject stale envelopes to prevent delayed replay.",
        "command": null,
        "expected_output": "Envelope age < 600 seconds.",
        "on_failure": "reject_envelope",
        "timeout_seconds": 5
      },
      {
        "step_number": 6,
        "name": "tests_verified",
        "description": "Verify that the source reports tests_passed == true in the envelope. Optionally verify lint_passed == true if require_lint is configured. These reflect the source's quality gate execution, not a local re-run.",
        "command": null,
        "expected_output": "tests_passed=true (and lint_passed=true if required).",
        "on_failure": "reject_envelope",
        "timeout_seconds": 5
      },
      {
        "step_number": 7,
        "name": "scope_present",
        "description": "Verify that the envelope contains a non-empty scope declaration with at least one permission. The scope must use only known_permissions from the contract.",
        "command": null,
        "expected_output": "Scope declaration present with recognized permissions.",
        "on_failure": "reject_envelope",
        "timeout_seconds": 5
      },
      {
        "step_number": 8,
        "name": "deploy_within_scope",
        "description": "Verify that the requested action (e.g. deploy, run_tests, start_server) is listed in the envelope's scope.permissions. Reject any action not explicitly granted. Unknown permissions are always rejected.",
        "command": null,
        "expected_output": "Requested action is within the declared scope permissions.",
        "on_failure": "reject_envelope",
        "timeout_seconds": 5
      },
      {
        "step_number": 9,
        "name": "audit_log",
        "description": "Burn the nonce (mark as used in nonce registry, persist to disk). Append a verification result entry to gate/audit.ndjson with envelope_id, timestamp, status, reason, step results, and duration. Feed the event to Overwatch if integration is enabled.",
        "command": null,
        "expected_output": "Nonce burned. Audit entry appended. Overwatch event emitted.",
        "on_failure": "log_and_continue",
        "timeout_seconds": 10
      }
    ]
  },
  "never_rules": [
    {
      "id": "NR-R01",
      "rule": "Never accept an envelope whose payload_hash does not match the recomputed SHA-256 of the payload. Any mismatch means the payload was tampered with after sealing.",
      "severity": "critical",
      "enforcement": "automated"
    },
    {
      "id": "NR-R02",
      "rule": "Never accept an envelope whose user_fingerprint does not match the recomputed HMAC-SHA256. A mismatch means the secret or machine identity differs from the sealer.",
      "severity": "critical",
      "enforcement": "automated"
    },
    {
      "id": "NR-R03",
      "rule": "Never accept a replayed nonce. Once a nonce is burned, any subsequent envelope presenting the same nonce must be immediately rejected.",
      "severity": "critical",
      "enforcement": "automated"
    },
    {
      "id": "NR-R04",
      "rule": "Never accept an envelope older than max_age_seconds. Stale envelopes are a replay risk even if the nonce hasn't been burned (clock-based defense in depth).",
      "severity": "high",
      "enforcement": "automated"
    },
    {
      "id": "NR-R05",
      "rule": "Never execute an action outside the envelope's declared scope permissions. If the scope says read_only, do not deploy, start servers, or write results.",
      "severity": "critical",
      "enforcement": "automated"
    },
    {
      "id": "NR-R06",
      "rule": "Never store or log the user_secret. The shared secret is used only transiently for HMAC recomputation and must not persist in logs, audit trails, or config files.",
      "severity": "critical",
      "enforcement": "both"
    },
    {
      "id": "NR-R07",
      "rule": "Never skip the audit_log step, even on rejection. Every verification attempt (pass or fail) must produce an append-only NDJSON audit entry for forensic review.",
      "severity": "high",
      "enforcement": "automated"
    },
    {
      "id": "NR-R08",
      "rule": "Never use string equality (==) for fingerprint or hash comparison. Always use hmac.compare_digest or equivalent timing-safe comparison to prevent timing side-channel attacks.",
      "severity": "critical",
      "enforcement": "automated"
    },
    {
      "id": "NR-R09",
      "rule": "Never accept an envelope with tests_passed=false when require_tests is enabled. The quality gate is non-negotiable.",
      "severity": "high",
      "enforcement": "automated"
    },
    {
      "id": "NR-R10",
      "rule": "Never process an envelope from a source_partition that does not match the expected source in the contract. Only E:\\ is a trusted source.",
      "severity": "high",
      "enforcement": "automated"
    },
    {
      "id": "NR-R11",
      "rule": "Never allow fail-open behavior. If any verification step encounters an unexpected error, the entire envelope must be rejected. Ambiguity is treated as hostile.",
      "severity": "critical",
      "enforcement": "automated"
    },
    {
      "id": "NR-R12",
      "rule": "Never modify the envelope payload before or during verification. The verification pipeline operates on an immutable snapshot; any mutation invalidates the integrity proof.",
      "severity": "critical",
      "enforcement": "automated"
    }
  ],
  "scope_enforcement": {
    "known_permissions": [
      "deploy",
      "run_tests",
      "start_server",
      "read_only",
      "write_results",
      "network"
    ],
    "default_permission": "read_only",
    "principle": "least_privilege",
    "unknown_permission_action": "reject"
  },
  "audit": {
    "enabled": true,
    "format": "ndjson",
    "log_path": "C:\\Users\\USER\\cascadeprojects\\gate\\audit.ndjson",
    "retention_days": 90,
    "overwatch_integration": true
  },
  "kpis": {
    "transfer_success_rate": {
      "target": 0.95,
      "window": "7d"
    },
    "verification_latency_ms": {
      "p50_target": 50,
      "p99_target": 500
    },
    "replay_attempt_rate": {
      "alert_threshold": 0.01,
      "window": "24h"
    }
  },
  "overwatch_escalation": {
    "threshold_count": 3,
    "window_minutes": 60,
    "notify_channels": [],
    "escalation_events": [
      "rejected:payload_integrity_failed",
      "rejected:fingerprint_mismatch",
      "rejected:nonce_replay_or_expired",
      "rejected:envelope_expired",
      "rejected:action_out_of_scope",
      "rejected:tests_not_passed"
    ]
  },
  "deployment_targets": {
    "grid-server": {
      "path": "C:\\Users\\USER\\cascadeprojects\\grid-server",
      "port": 8080,
      "allowed_permissions": ["deploy", "run_tests", "start_server", "write_results"],
      "description": "GRID-main deployment target"
    },
    "afloat-server": {
      "path": "C:\\Users\\USER\\cascadeprojects\\afloat-server",
      "port": 3000,
      "allowed_permissions": ["deploy", "start_server"],
      "description": "Afloat deployment target"
    },
    "echoes-server": {
      "path": "C:\\Users\\USER\\cascadeprojects\\echoes-server",
      "port": 8000,
      "allowed_permissions": ["deploy", "run_tests", "start_server", "write_results"],
      "description": "Echoes deployment target"
    },
    "lots-server": {
      "path": "C:\\Users\\USER\\cascadeprojects\\lots-server",
      "port": 8001,
      "allowed_permissions": ["deploy", "run_tests"],
      "description": "Light of the Seven deployment target"
    },
    "experiments": {
      "path": "C:\\Users\\USER\\cascadeprojects\\experiments",
      "port": null,
      "allowed_permissions": ["read_only", "run_tests", "write_results"],
      "description": "Experimental workspace (no deploy or server permissions)"
    }
  },
  "directory_structure": {
    "gate": {
      "description": "Root directory for gate operations",
      "children": {
        "incoming": {
          "description": "Sealed envelopes land here for verification",
          "auto_clean_after_verify": true
        },
        "results": {
          "description": "Verification results and processed envelope metadata",
          "auto_clean_after_days": 30
        },
        "audit.ndjson": {
          "description": "Append-only NDJSON audit trail for all verification events"
        },
        ".nonce_registry.json": {
          "description": "Persistent nonce registry (burned nonces tracked here)"
        }
      }
    },
    "archive": {
      "description": "Archived old source-like folders from pre-gate era (read-only, no deploy)"
    }
  },
  "migration_checklist": [
    {
      "id": "MC-01",
      "task": "Create directory: C:\\Users\\USER\\cascadeprojects\\grid-server\\",
      "status": "pending"
    },
    {
      "id": "MC-02",
      "task": "Create directory: C:\\Users\\USER\\cascadeprojects\\afloat-server\\",
      "status": "pending"
    },
    {
      "id": "MC-03",
      "task": "Create directory: C:\\Users\\USER\\cascadeprojects\\echoes-server\\",
      "status": "pending"
    },
    {
      "id": "MC-04",
      "task": "Create directory: C:\\Users\\USER\\cascadeprojects\\lots-server\\",
      "status": "pending"
    },
    {
      "id": "MC-05",
      "task": "Create directory: C:\\Users\\USER\\cascadeprojects\\gate\\incoming\\",
      "status": "pending"
    },
    {
      "id": "MC-06",
      "task": "Create directory: C:\\Users\\USER\\cascadeprojects\\gate\\results\\",
      "status": "pending"
    },
    {
      "id": "MC-07",
      "task": "Create directory: C:\\Users\\USER\\cascadeprojects\\experiments\\",
      "status": "pending"
    },
    {
      "id": "MC-08",
      "task": "Create directory: C:\\Users\\USER\\cascadeprojects\\archive\\",
      "status": "pending"
    },
    {
      "id": "MC-09",
      "task": "Initialize file: C:\\Users\\USER\\cascadeprojects\\gate\\audit.ndjson (empty)",
      "status": "pending"
    },
    {
      "id": "MC-10",
      "task": "Initialize file: C:\\Users\\USER\\cascadeprojects\\gate\\.nonce_registry.json with {}",
      "status": "pending"
    },
    {
      "id": "MC-11",
      "task": "Store shared secret in Windows Credential Manager: cmdkey /add:TransitionGate /user:USER /pass:<secret>",
      "status": "pending"
    },
    {
      "id": "MC-12",
      "task": "Archive existing source-like folders (Afloat/, GRID-main/, etc.) to archive/ if not needed as deploy targets",
      "status": "pending"
    },
    {
      "id": "MC-13",
      "task": "Create MANIFEST.md at C:\\Users\\USER\\cascadeprojects\\ with header row documenting deployed artifacts",
      "status": "pending"
    }
  ]
}

```


**Tool Call: Read file `CascadeProjects/GRID-main/boundaries/transition_gate/contracts/e-source-agent.contract.json`**
Status: Completed

```CascadeProjects/GRID-main/boundaries/transition_gate/contracts/e-source-agent.contract.json
{
  "contract_id": "e-source-agent-v1-2026",
  "contract_version": "1.0.0",
  "agent_role": "source",
  "partition": {
    "label": "E:\\",
    "root_path": "E:\\Seeds",
    "purpose": "source_build",
    "staging_path": "E:\\Fruits\\releases"
  },
  "security_primitives": {
    "user_fingerprint": {
      "algorithm": "HMAC-SHA256",
      "key_source": "windows_credential_manager",
      "key_name": "TransitionGate",
      "binding_factors": ["machine_fingerprint", "partition_label"]
    },
    "machine_fingerprint": {
      "algorithm": "SHA-256",
      "attributes": ["node_name", "platform_system", "platform_machine", "username"]
    },
    "nonce": {
      "format": "uuid4_hex",
      "registry_path": "E:\\Fruits\\releases\\.nonce_registry.json",
      "single_use": true,
      "burn_on_verify": true
    },
    "payload_hash": {
      "algorithm": "SHA-256",
      "serialization": "canonical_json"
    },
    "envelope_expiry": {
      "max_age_seconds": 600
    }
  },
  "pipeline": {
    "description": "9-step seal pipeline: validate source state, build artifacts, seal envelope, stage for transfer.",
    "fail_mode": "fail_closed",
    "steps": [
      {
        "step_number": 1,
        "name": "checkpoint_clean",
        "description": "Verify all tracked repos have clean git status (no uncommitted changes). Run Seeds-Checkpoint.ps1 -Validate.",
        "command": "powershell -File E:\\Seeds\\Seeds-Checkpoint.ps1 -Validate",
        "expected_output": "All repos clean.",
        "on_failure": "abort",
        "timeout_seconds": 30
      },
      {
        "step_number": 2,
        "name": "tests_pass",
        "description": "Run the full test suite for the target project. For GRID-main: make test. For afloat: npm run test. For echoes: uv run pytest tests/ -q --tb=short.",
        "command": "make test",
        "expected_output": "All tests passed (exit code 0).",
        "on_failure": "abort",
        "timeout_seconds": 300
      },
      {
        "step_number": 3,
        "name": "lint_pass",
        "description": "Run linting for the target project. For GRID-main: make lint. For afloat: npm run lint. For echoes: uv run ruff check .",
        "command": "make lint",
        "expected_output": "No lint errors (exit code 0).",
        "on_failure": "abort",
        "timeout_seconds": 120
      },
      {
        "step_number": 4,
        "name": "preparedness_gate",
        "description": "Check the PreparednessFramework gate for the transfer operation. Gate gate_protocol must return require_approval or log_and_allow. Gate gate_capability must not be blocked without approval.",
        "command": "python -c \"from boundaries import PreparednessFramework; pf = PreparednessFramework(); print(pf.check_gate('gate_protocol'))\"",
        "expected_output": "('require_approval', True) or ('log_and_allow', True)",
        "on_failure": "abort",
        "timeout_seconds": 10
      },
      {
        "step_number": 5,
        "name": "build_artifacts",
        "description": "Collect and serialize the artifacts to be transferred. For GRID-main: the payload is a manifest dict with project name, version, commit SHA, file list, and build metadata.",
        "command": "python -m boundaries.transition_gate.cli build --project GRID-main",
        "expected_output": "Payload dict ready for sealing.",
        "on_failure": "abort",
        "timeout_seconds": 60
      },
      {
        "step_number": 6,
        "name": "seal_envelope",
        "description": "Seal the payload into a TransitionEnvelope using seal_envelope(). Computes payload_hash, machine_fingerprint, user_fingerprint, generates nonce, captures timestamp.",
        "command": "python -m boundaries.transition_gate.cli seal --payload-file artifacts.json --secret-from credential_manager",
        "expected_output": "Sealed envelope written to E:\\Fruits\\releases\\envelope_<id>.json",
        "on_failure": "abort",
        "timeout_seconds": 15
      },
      {
        "step_number": 7,
        "name": "scope_declaration",
        "description": "Attach a ScopeDeclaration to the sealed envelope specifying exactly which permissions the receiver gets. Follow least-privilege: only grant deploy, run_tests, or read_only as needed.",
        "command": null,
        "expected_output": "Scope declaration embedded in envelope with explicit permissions list.",
        "on_failure": "abort",
        "timeout_seconds": 5
      },
      {
        "step_number": 8,
        "name": "transfer",
        "description": "Copy the sealed envelope JSON from E:\\Fruits\\releases\\ to C:\\Users\\USER\\cascadeprojects\\gate\\incoming\\. Use robocopy or Copy-Item with verification.",
        "command": "robocopy E:\\Fruits\\releases C:\\Users\\USER\\cascadeprojects\\gate\\incoming envelope_*.json /MOV /R:3 /W:5",
        "expected_output": "1 File(s) copied.",
        "on_failure": "abort",
        "timeout_seconds": 30
      },
      {
        "step_number": 9,
        "name": "overwatch_log",
        "description": "Log the transfer event to Overwatch for monitoring. Emit a gate_transfer_sealed event with envelope_id, timestamp, target partition, and scope summary.",
        "command": null,
        "expected_output": "Event logged to logs/boundaries/ and Overwatch alert pipeline.",
        "on_failure": "log_and_continue",
        "timeout_seconds": 5
      }
    ]
  },
  "never_rules": [
    {
      "id": "NR-S01",
      "rule": "Never seal an envelope without running tests first. tests_passed must reflect actual test execution, not a hardcoded True.",
      "severity": "critical",
      "enforcement": "automated"
    },
    {
      "id": "NR-S02",
      "rule": "Never embed the user_secret in the envelope or write it to any file. The secret is used only transiently for HMAC computation.",
      "severity": "critical",
      "enforcement": "both"
    },
    {
      "id": "NR-S03",
      "rule": "Never reuse a nonce across envelopes. Each seal_envelope() call must generate a fresh UUID4 nonce via NonceRegistry.generate().",
      "severity": "critical",
      "enforcement": "automated"
    },
    {
      "id": "NR-S04",
      "rule": "Never grant scope permissions beyond what the specific transfer requires. Default to read_only; escalate only with explicit justification.",
      "severity": "high",
      "enforcement": "review"
    },
    {
      "id": "NR-S05",
      "rule": "Never transfer unsealed artifacts. The sealed envelope JSON is the ONLY object that may cross the partition boundary.",
      "severity": "critical",
      "enforcement": "automated"
    },
    {
      "id": "NR-S06",
      "rule": "Never bypass the PreparednessFramework gate. If gate_capability returns ('block', False), the transfer must not proceed.",
      "severity": "high",
      "enforcement": "automated"
    },
    {
      "id": "NR-S07",
      "rule": "Never modify the payload after computing payload_hash. Any post-hash mutation invalidates the envelope's integrity proof.",
      "severity": "critical",
      "enforcement": "automated"
    },
    {
      "id": "NR-S08",
      "rule": "Never skip the checkpoint_clean step. Dirty git state means the source of truth is ambiguous and the envelope cannot be trusted.",
      "severity": "high",
      "enforcement": "automated"
    },
    {
      "id": "NR-S09",
      "rule": "Never hardcode the user_secret in source code, config files, or environment variable defaults. Retrieve it from Windows Credential Manager or a secure keyring at runtime only.",
      "severity": "critical",
      "enforcement": "both"
    },
    {
      "id": "NR-S10",
      "rule": "Never transfer to a target partition path outside the declared target_partition in the envelope. The receiving path must match the contract.",
      "severity": "high",
      "enforcement": "automated"
    }
  ],
  "scope_enforcement": {
    "known_permissions": [
      "deploy",
      "run_tests",
      "start_server",
      "read_only",
      "write_results",
      "network"
    ],
    "default_permission": "read_only",
    "principle": "least_privilege",
    "unknown_permission_action": "reject"
  },
  "audit": {
    "enabled": true,
    "format": "ndjson",
    "log_path": "E:\\Seeds\\GRID-main\\logs\\boundaries\\gate_seal_audit.ndjson",
    "retention_days": 90,
    "overwatch_integration": true
  },
  "kpis": {
    "transfer_success_rate": {
      "target": 0.95,
      "window": "7d"
    },
    "verification_latency_ms": {
      "p50_target": 50,
      "p99_target": 500
    },
    "replay_attempt_rate": {
      "alert_threshold": 0.01,
      "window": "24h"
    }
  },
  "overwatch_escalation": {
    "threshold_count": 3,
    "window_minutes": 60,
    "notify_channels": [],
    "escalation_events": [
      "seal_without_tests",
      "nonce_generation_failure",
      "preparedness_gate_blocked",
      "transfer_io_failure"
    ]
  },
  "projects": {
    "GRID-main": {
      "test_command": "uv run pytest tests/unit tests/integration -q --tb=short",
      "lint_command": "uv run ruff check .",
      "build_command": null,
      "source_path": "E:\\Seeds\\GRID-main",
      "default_scope_permissions": ["deploy", "run_tests", "start_server"]
    },
    "afloat": {
      "test_command": "npm run test",
      "lint_command": "npm run lint",
      "build_command": "npm run build",
      "source_path": "E:\\Seeds\\afloat",
      "default_scope_permissions": ["deploy", "start_server"]
    },
    "echoes": {
      "test_command": "uv run pytest tests/ -q --tb=short",
      "lint_command": "uv run ruff check .",
      "build_command": null,
      "source_path": "E:\\Seeds\\echoes",
      "default_scope_permissions": ["deploy", "run_tests", "start_server"]
    },
    "light_of_the_seven": {
      "test_command": "uv run pytest tests/ -q --tb=short",
      "lint_command": "uv run ruff check .",
      "build_command": null,
      "source_path": "E:\\Seeds\\light_of_the_seven",
      "default_scope_permissions": ["deploy", "run_tests"]
    }
  },
  "port_assignments": {
    "GRID-main": 8080,
    "afloat": 3000,
    "echoes": 8000,
    "light_of_the_seven": 8001
  }
}

```


**Tool Call: Read file `roots/GRID/config/contracts/openapi.yaml`**
Status: Completed

```roots/GRID/config/contracts/openapi.yaml
openapi: 3.0.0
info:
  title: GRID Audio Modules API Contracts
  version: 1.0.0
paths: {}
components:
  schemas:
    BassSpec:
      type: object
      required: [name, owner, interface, headroom_db]
      properties:
        name:
          type: string
          example: bass
        owner:
          type: string
          example: low_end
        interface:
          type: string
          example: instrument:mono+stereo_harmonics
        headroom_db:
          type: number
          format: float
          example: -6
        version:
          type: string
          example: 1.0.0
    ArpSpec:
      type: object
      required: [name, owner, interface, headroom_db]
      properties:
        name:
          type: string
          example: arps
        owner:
          type: string
          example: melodic
        interface:
          type: string
          example: instrument:stereo
        headroom_db:
          type: number
          format: float
          example: -6
        version:
          type: string
          example: 1.0.0
    PadSpec:
      type: object
      required: [name, owner, interface, headroom_db]
      properties:
        name:
          type: string
          example: pads
        owner:
          type: string
          example: texture
        interface:
          type: string
          example: instrument:stereo
        headroom_db:
          type: number
          format: float
          example: -6
        version:
          type: string
          example: 1.0.0

```


**Tool Call: Read file `roots/GRID/.grid/debug-contract.json`**
Status: Completed

```roots/GRID/.grid/debug-contract.json
SUCCESS: File outline retrieved. This file is too large to read all at once, so the outline below shows the file's structure with line numbers.

IMPORTANT: Do NOT retry this call without line numbers - you will get the same outline.
Instead, use the line numbers below to read specific sections by calling this tool again with start_line and end_line parameters.

# File outline for /home/caraxes/roots/GRID/.grid/debug-contract.json

$schema [L2]
contract_id [L3]
version [L4]
description [L5]
created [L6]
codebase [L7-34]
 name [L8]
 root [L9]
 languages [L10-14]
 python_version [L15]
 node_version [L16]
 package_manager_python [L17]
 package_manager_js [L18]
 source_paths [L19-25]
 frontend_path [L26]
 test_paths [L27-31]
 total_python_files [L32]
 total_packages [L33]
environment [L35-69]
 required_tools [L36-57]
  name [L38]
  min_version [L39]
  verify [L40]
  name [L43]
  min_version [L44]
  verify [L45]
  name [L48]
  min_version [L49]
  verify [L50]
  name [L53]
  min_version [L54]
  verify [L55]
 env_vars [L58-68]
  required [L59-61]
  recommended_test_values [L62-67]
   MOTHERSHIP_ENVIRONMENT [L63]
   MOTHERSHIP_DATABASE_URL [L64]
   MOTHERSHIP_USE_DATABRICKS [L65]
   MOTHERSHIP_REDIS_ENABLED [L66]
dimensions [L70-1083]
 build_integrity [L71-276]
  id [L72]
  name [L73]
  description [L74]
  checks [L75-275]
   id [L77]
   name [L78]
   description [L79]
   severity [L80]
   command [L81]
   workdir [L82]
   timeout_seconds [L83]
   pass_criteria [L84-91]
    exit_code [L85]
    stderr_must_not_contain [L86-89]
    stdout_must_contain [L90]
   fix [L92-99]
    auto_command [L93]
    manual_steps [L94-97]
    escalation [L98]
   depends_on [L100]
   tags [L101-105]
   id [L108]
   name [L109]
   description [L110]
   severity [L111]
   command [L112]
   workdir [L113]
   timeout_seconds [L114]
   pass_criteria [L115-122]
    exit_code [L116]
    stderr_must_not_contain [L117-120]
    stdout_must_contain [L121]
   fix [L123-130]
    auto_command [L124]
    manual_steps [L125-128]
    escalation [L129]
   depends_on [L131]
   tags [L132-136]
   id [L139]
   name [L140]
   description [L141]
   severity [L142]
   command [L143]
   workdir [L144]
   timeout_seconds [L145]
   pass_criteria [L146-153]
    exit_code [L147]
    stderr_must_not_contain [L148-151]
    stdout_must_contain [L152]
   fix [L154-161]
    auto_command [L155]
    manual_steps [L156-159]
    escalation [L160]
   depends_on [L162-164]
   tags [L165-169]
   id [L172]
   name [L173]
   description [L174]
   severity [L175]
   command [L176]
   workdir [L177]
   timeout_seconds [L178]
   pass_criteria [L179-187]
    exit_code [L180]
    stderr_must_not_contain [L181-183]
    stdout_must_contain [L184-186]
   fix [L188-195]
    auto_command [L189]
    manual_steps [L190-193]
    escalation [L194]
   depends_on [L196-198]
   tags [L199-203]
   id [L206]
   name [L207]
   description [L208]
   severity [L209]
   command [L210]
   workdir [L211]
   timeout_seconds [L212]
   pass_criteria [L213-220]
    exit_code [L214]
    stderr_must_not_contain [L215-218]
    stdout_must_contain [L219]
   fix [L221-228]
    auto_command [L222]
    manual_steps [L223-226]
    escalation [L227]
   depends_on [L229-231]
   tags [L232-236]
   id [L239]
   name [L240]
   description [L241]
   severity [L242]
   command [L243]
   workdir [L244]
   timeout_seconds [L245]
   pass_criteria [L246-256]
    exit_code [L247]
    stderr_must_not_contain [L248-252]
    stdout_must_contain [L253-255]
   fix [L257-265]
    auto_command [L258]
    manual_steps [L259-263]
    escalation [L264]
   depends_on [L266-268]
   tags [L269-273]
 type_safety [L277-410]
  id [L278]
  name [L279]
  description [L280]
  checks [L281-409]
   id [L283]
   name [L284]
   description [L285]
   severity [L286]
   command [L287]
   workdir [L288]
   timeout_seconds [L289]
   pass_criteria [L290-294]
    exit_code [L291]
    stderr_must_not_contain [L292]
    stdout_must_contain [L293]
   fix [L295-303]
    auto_command [L296]
    manual_steps [L297-301]
    escalation [L302]
   depends_on [L304-306]
   tags [L307-311]
   id [L314]
   name [L315]
   description [L316]
   severity [L317]
   command [L318]
   workdir [L319]
   timeout_seconds [L320]
   pass_criteria [L321-327]
    exit_code [L322]
    stderr_must_not_contain [L323-325]
    stdout_must_contain [L326]
   fix [L328-335]
    auto_command [L329]
    manual_steps [L330-333]
    escalation [L334]
   depends_on [L336-338]
   tags [L339-343]
   id [L346]
   name [L347]
   description [L348]
   severity [L349]
   command [L350]
   workdir [L351]
   timeout_seconds [L352]
   pass_criteria [L353-359]
    exit_code [L354]
    stderr_must_not_contain [L355-357]
    stdout_must_contain [L358]
   fix [L360-367]
    auto_command [L361]
    manual_steps [L362-365]
    escalation [L366]
   depends_on [L368-370]
   tags [L371-375]
   id [L378]
   name [L379]
   description [L380]
   severity [L381]
   command [L382]
   workdir [L383]
   timeout_seconds [L384]
   pass_criteria [L385-393]
    exit_code [L386]
    stderr_must_not_contain [L387-389]
    stdout_must_contain [L390-392]
   fix [L394-401]
    auto_command [L395]
    manual_steps [L396-399]
    escalation [L400]
   depends_on [L402]
   tags [L403-407]
 test_coverage [L411-648]
  id [L412]
  name [L413]
  description [L414]
  checks [L415-647]
   id [L417]
   name [L418]
   description [L419]
   severity [L420]
   command [L421]
   workdir [L422]
   timeout_seconds [L423]
   pass_criteria [L424-433]
    exit_code [L425]
    stderr_must_not_contain [L426-429]
    stdout_must_contain [L430-432]
   fix [L434-441]
    auto_command [L435]
    manual_steps [L436-439]
    escalation [L440]
   depends_on [L442-445]
   tags [L446-451]
   id [L454]
   name [L455]
   description [L456]
   severity [L457]
   command [L458]
   workdir [L459]
   timeout_seconds [L460]
   pass_criteria [L461-467]
    exit_code [L462]
    stderr_must_not_contain [L463-465]
    stdout_must_contain [L466]
   fix [L468-476]
    auto_command [L469]
    manual_steps [L470-474]
    escalation [L475]
   depends_on [L477-480]
   tags [L481-485]
   id [L488]
   name [L489]
   description [L490]
   severity [L491]
   command [L492]
   workdir [L493]
   timeout_seconds [L494]
   pass_criteria [L495-499]
    exit_code [L496]
    stderr_must_not_contain [L497]
    stdout_must_contain [L498]
   fix [L500-508]
    auto_command [L501]
    manual_steps [L502-506]
    escalation [L507]
   depends_on [L509-511]
   tags [L512-516]
   id [L519]
   name [L520]
   description [L521]
   severity [L522]
   command [L523]
   workdir [L524]
   timeout_seconds [L525]
   pass_criteria [L526-532]
    exit_code [L527]
    stderr_must_not_contain [L528-530]
    stdout_must_contain [L531]
   fix [L533-540]
    auto_command [L534]
    manual_steps [L535-538]
    escalation [L539]
   depends_on [L541-543]
   tags [L544-548]
   id [L551]
   name [L552]
   description [L553]
   severity [L554]
   command [L555]
   workdir [L556]
   timeout_seconds [L557]
   pass_criteria [L558-564]
    exit_code [L559]
    stderr_must_not_contain [L560-562]
    stdout_must_contain [L563]
   fix [L565-572]
    auto_command [L566]
    manual_steps [L567-570]
    escalation [L571]
   depends_on [L573-575]
   tags [L576-581]
   id [L584]
   name [L585]
   description [L586]
   severity [L587]
   command [L588]
   workdir [L589]
   timeout_seconds [L590]
   pass_criteria [L591-597]
    exit_code [L592]
    stderr_must_not_contain [L593-595]
    stdout_must_contain [L596]
   fix [L598-605]
    auto_command [L599]
    manual_steps [L600-603]
    escalation [L604]
   depends_on [L606-608]
   tags [L609-613]
   id [L616]
   name [L617]
   description [L618]
   severity [L619]
   command [L620]
   workdir [L621]
   timeout_seconds [L622]
   pass_criteria [L623-629]
    exit_code [L624]
    stderr_must_not_contain [L625-627]
    stdout_must_contain [L628]
   fix [L630-637]
    auto_command [L631]
    manual_steps [L632-635]
    escalation [L636]
   depends_on [L638-640]
   tags [L641-645]
 lint_compliance [L649-772]
  id [L650]
  name [L651]
  description [L652]
  checks [L653-771]
   id [L655]
   name [L656]
   description [L657]
   severity [L658]
   command [L659]
   workdir [L660]
   timeout_seconds [L661]
   pass_criteria [L662-666]
    exit_code [L663]
    stderr_must_not_contain [L664]
    stdout_must_contain [L665]
   fix [L667-675]
    auto_command [L668]
    manual_steps [L669-673]
    escalation [L674]
   depends_on [L676]
   tags [L677-681]
   id [L684]
   name [L685]
   description [L686]
   severity [L687]
   command [L688]
   workdir [L689]
   timeout_seconds [L690]
   pass_criteria [L691-695]
    exit_code [L692]
    stderr_must_not_contain [L693]
    stdout_must_contain [L694]
   fix [L696-702]
    auto_command [L697]
    manual_steps [L698-700]
    escalation [L701]
   depends_on [L703]
   tags [L704-708]
   id [L711]
   name [L712]
   description [L713]
   severity [L714]
   command [L715]
   workdir [L716]
   timeout_seconds [L717]
   pass_criteria [L718-724]
    exit_code [L719]
    stderr_must_not_contain [L720-722]
    stdout_must_contain [L723]
   fix [L725-732]
    auto_command [L726]
    manual_steps [L727-730]
    escalation [L731]
   depends_on [L733-735]
   tags [L736-740]
   id [L743]
   name [L744]
   description [L745]
   severity [L746]
   command [L747]
   workdir [L748]
   timeout_seconds [L749]
   pass_criteria [L750-754]
    exit_code [L751]
    stderr_must_not_contain [L752]
    stdout_must_contain [L753]
   fix [L755-761]
    auto_command [L756]
    manual_steps [L757-759]
    escalation [L760]
   depends_on [L762-764]
   tags [L765-769]
 runtime_correctness [L773-945]
  id [L774]
  name [L775]
  description [L776]
  checks [L777-944]
   id [L779]
   name [L780]
   description [L781]
   severity [L782]
   command [L783]
   workdir [L784]
   timeout_seconds [L785]
   pass_criteria [L786-793]
    exit_code [L787]
    stderr_must_not_contain [L788-791]
    stdout_must_contain [L792]
   fix [L794-801]
    auto_command [L795]
    manual_steps [L796-799]
    escalation [L800]
   depends_on [L802-805]
   tags [L806-811]
   id [L814]
   name [L815]
   description [L816]
   severity [L817]
   command [L818]
   workdir [L819]
   timeout_seconds [L820]
   pass_criteria [L821-827]
    exit_code [L822]
    stderr_must_not_contain [L823-825]
    stdout_must_contain [L826]
   fix [L828-836]
    auto_command [L829]
    manual_steps [L830-834]
    escalation [L835]
   depends_on [L837-840]
   tags [L841-845]
   id [L848]
   name [L849]
   description [L850]
   severity [L851]
   command [L852]
   workdir [L853]
   timeout_seconds [L854]
   pass_criteria [L855-861]
    exit_code [L856]
    stderr_must_not_contain [L857-859]
    stdout_must_contain [L860]
   fix [L862-869]
    auto_command [L863]
    manual_steps [L864-867]
    escalation [L868]
   depends_on [L870-872]
   tags [L873-877]
   id [L880]
   name [L881]
   description [L882]
   severity [L883]
   command [L884]
   workdir [L885]
   timeout_seconds [L886]
   pass_criteria [L887-894]
    exit_code [L888]
    stderr_must_not_contain [L889-892]
    stdout_must_contain [L893]
   fix [L895-902]
    auto_command [L896]
    manual_steps [L897-900]
    escalation [L901]
   depends_on [L903-905]
   tags [L906-910]
   id [L913]
   name [L914]
   description [L915]
   severity [L916]
   command [L917]
   workdir [L918]
   timeout_seconds [L919]
   pass_criteria [L920-926]
    exit_code [L921]
    stderr_must_not_contain [L922-924]
    stdout_must_contain [L925]
   fix [L927-934]
    auto_command [L928]
    manual_steps [L929-932]
    escalation [L933]
   depends_on [L935-937]
   tags [L938-942]
 security_and_dependency_health [L946-1082]
  id [L947]
  name [L948]
  description [L949]
  checks [L950-1081]
   id [L952]
   name [L953]
   description [L954]
   severity [L955]
   command [L956]
   workdir [L957]
   timeout_seconds [L958]
   pass_criteria [L959-963]
    exit_code [L960]
    stderr_must_not_contain [L961]
    stdout_must_contain [L962]
   fix [L964-972]
    auto_command [L965]
    manual_steps [L966-970]
    escalation [L971]
   depends_on [L973-975]
   tags [L976-980]
   id [L983]
   name [L984]
   description [L985]
   severity [L986]
   command [L987]
   workdir [L988]
   timeout_seconds [L989]
   pass_criteria [L990-996]
    exit_code [L991]
    stderr_must_not_contain [L992-994]
    stdout_must_contain [L995]
   fix [L997-1005]
    auto_command [L998]
    manual_steps [L999-1003]
    escalation [L1004]
   depends_on [L1006-1008]
   tags [L1009-1013]
   id [L1016]
   name [L1017]
   description [L1018]
   severity [L1019]
   command [L1020]
   workdir [L1021]
   timeout_seconds [L1022]
   pass_criteria [L1023-1029]
    exit_code [L1024]
    stderr_must_not_contain [L1025-1027]
    stdout_must_contain [L1028]
   fix [L1030-1038]
    auto_command [L1031]
    manual_steps [L1032-1036]
    escalation [L1037]
   depends_on [L1039-1041]
   tags [L1042-1047]
   id [L1050]
   name [L1051]
   description [L1052]
   severity [L1053]
   command [L1054]
   workdir [L1055]
   timeout_seconds [L1056]
   pass_criteria [L1057-1063]
    exit_code [L1058]
    stderr_must_not_contain [L1059-1061]
    stdout_must_contain [L1062]
   fix [L1064-1073]
    auto_command [L1065]
    manual_steps [L1066-1071]
    escalation [L1072]
   depends_on [L1074]
   tags [L1075-1079]
execution [L1084-1171]
 phases [L1085-1170]
  phase [L1087]
  name [L1088]
  checks [L1089-1092]
  parallel [L1093]
  depends_on_phase [L1094]
  description [L1095]
  phase [L1098]
  name [L1099]
  checks [L1100-1110]
  parallel [L1111]
  depends_on_phase [L1112]
  description [L1113]
  phase [L1116]
  name [L1117]
  checks [L1118-1122]
  parallel [L1123]
  depends_on_phase [L1124]
  description [L1125]
  phase [L1128]
  name [L1129]
  checks [L1130-1136]
  parallel [L1137]
  depends_on_phase [L1138]
  description [L1139]
  phase [L1142]
  name [L1143]
  checks [L1144-1152]
  parallel [L1153]
  depends_on_phase [L1154]
  description [L1155]
  phase [L1158]
  name [L1159]
  checks [L1160-1165]
  parallel [L1166]
  depends_on_phase [L1167]
  description [L1168]
aggregate_policy [L1172-1183]
 pass_requires [L1173]
 dimension_pass_requires [L1174]
 medium_severity_allowed_failures [L1175]
 fail_fast_on_critical [L1176]
 max_parallel_checks [L1177]
 global_timeout_minutes [L1178]
 retry_on_transient [L1179]
 retry_count [L1180]
 report_format [L1181]
 report_path [L1182]
meta_prompt [L1184]

Showing symbols 1-630 (total symbols: 630)


NEXT STEPS: To read a specific symbol's implementation, call read_file with the same path plus start_line and end_line from the outline above.
For example, to read a function shown as [L100-150], use start_line: 100 and end_line: 150.
```


**Tool Call: Read file `roots/GRID/.grid/post-11pm-contract.json`**
Status: Completed

```roots/GRID/.grid/post-11pm-contract.json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "contract_id": "grid-post-11pm-2026-02-23",
  "version": "1.0",
  "created": "2026-02-23",
  "scheduled_after": "23:00",
  "source_report": "GRID_COMPREHENSIVE_REPORT_2026-02-23.md",
  "summary": {
    "good_to_preserve": 8,
    "bad_to_fix_immediately": 7,
    "ok_to_improve": 6
  },
  "actions": [
    {
      "id": "commit-working-tree",
      "priority": "critical",
      "description": "Commit or stash 127 modified files to avoid loss",
      "precondition": "No active debug session",
      "command": "git status"
    },
    {
      "id": "fix-test-failures-api",
      "priority": "high",
      "description": "Fix failures in tests/api (Stripe, streaming, security governance)",
      "files": [
        "tests/api/test_payment_stripe_integration.py",
        "tests/api/test_streaming_security.py",
        "tests/api/test_stripe_connect_demo.py",
        "tests/api/test_security_governance.py"
      ]
    },
    {
      "id": "fix-test-errors-setup",
      "priority": "high",
      "description": "Fix setup/teardown errors in test_repositories, test_rag_evolution, test_navigation_intelligence",
      "files": [
        "tests/integration/test_repositories.py",
        "tests/integration/test_rag_evolution.py",
        "tests/integration/test_navigation_intelligence.py"
      ]
    },
    {
      "id": "frontend-ts-fixes",
      "priority": "medium",
      "description": "Fix TS2307 (@/lib/utils) and TS7006 (implicit any) in frontend",
      "paths": [
        "frontend/tsconfig.json",
        "frontend/src"
      ]
    },
    {
      "id": "normalize-crlf",
      "priority": "low",
      "description": "Normalize line endings: git add --renormalize",
      "precondition": "After commit",
      "command": "git add --renormalize ."
    },
    {
      "id": "update-test-report",
      "priority": "low",
      "description": "Re-run pytest, update comprehensive_test_report.md",
      "precondition": "After test fixes",
      "command": "uv run pytest tests/ -q -o addopts= --tb=no 2>&1 | tee comprehensive_test_report.md"
    }
  ],
  "preserve": [
    "uv sync --frozen --group test in CI",
    "In-memory SQLite for safety and mothership tests",
    "setup-uv@v7.3.0 and version 0.10.4",
    "Lazy conftest imports",
    "grid-safety local path override"
  ],
  "skip_if": [
    "Windows build (use WSL for sdist)",
    "Ollama-dependent checks (external service)"
  ],
  "context": {
    "git_changes_4h": "9fb0e73 chore(vscode), b7297b5 fix(ci) Python 3.13, Cascade snapshots",
    "working_tree": "127 modified, 4 untracked",
    "safety_tests": "251 passed, 2 skipped",
    "full_suite": "27 files with failures, 7 with errors"
  }
}

```


## Assistant

<thinking>
Good, I have a lot of data. Now let me read the implementation files and do the grep searches. Let me do the next batch of reads in parallel.
</thinking>

Good — the foundation data is in. Now let me read the implementation files and search for boundary enforcement patterns.

**Tool Call: Read file `roots/GRID/src/grid/resilience/accountability/contracts.py`**
Status: Completed

```roots/GRID/src/grid/resilience/accountability/contracts.py
SUCCESS: File outline retrieved. This file is too large to read all at once, so the outline below shows the file's structure with line numbers.

IMPORTANT: Do NOT retry this call without line numbers - you will get the same outline.
Instead, use the line numbers below to read specific sections by calling this tool again with start_line and end_line parameters.

# File outline for /home/caraxes/roots/GRID/src/grid/resilience/accountability/contracts.py

class ContractSeverity [L20-26]
class ViolationType [L29-42]
class ContractViolation [L46-76]
 def violation_type [L60-62]
 def to_dict [L64-76]
class EnforcementResult [L80-119]
 def is_compliant [L93-95]
 def total_penalty_points [L98-100]
 def add_violation [L102-105]
 def to_dict [L107-119]
class ContractManager [L122-146]
 def __init__ [L125-126]
 def register_contract [L128-130]
 def get_contract [L132-134]
 def get_all_contracts [L136-138]
 def find_endpoint_contract [L140-146]
class DataValidationRule [L149-163]
class PerformanceSLA [L166-172]
class SecurityRequirement [L175-184]
class ComplianceRequirement [L187-197]
class EndpointContract [L200-254]
 def validate_http_method [L231-248]
 def update_timestamp [L252-254]
class ServiceLevelObjective [L257-269]
class AccountabilityContract [L272-442]
 def get_endpoint_contract [L293-322]
 def validate_request [L324-330]
 def validate_response [L332-338]
 def _validate_data [L340-442]

Showing symbols 1-29 (total symbols: 29)


NEXT STEPS: To read a specific symbol's implementation, call read_file with the same path plus start_line and end_line from the outline above.
For example, to read a function shown as [L100-150], use start_line: 100 and end_line: 150.
```


**Tool Call: Read file `roots/GRID/src/grid/resilience/accountability/contract_loader.py`**
Status: Completed

```roots/GRID/src/grid/resilience/accountability/contract_loader.py
"""
Contract loader with YAML schema alignment.
Maps YAML structure to Pydantic models with proper field aliases.
"""

import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from .contracts import (
    AccountabilityContract,
    ComplianceRequirement,
    DataValidationRule,
    PerformanceSLA,
    SecurityRequirement,
    ServiceLevelObjective,
)

logger = logging.getLogger(__name__)


class ContractLoader:
    """Loads accountability contracts from YAML with schema alignment."""

    def __init__(self, config_path: Path | None = None):
        """Initialize contract loader.

        Args:
            config_path: Path to contracts YAML file.
                Defaults to standard location.
        """
        if config_path is None:
            config_path = (
                Path(__file__).parent.parent.parent.parent.parent / "config" / "accountability" / "contracts.yaml"
            )

        self.config_path = Path(config_path)
        self._contract_cache: AccountabilityContract | None = None

    def load_contracts(self, force_reload: bool = False) -> AccountabilityContract:
        """Load contracts from YAML with schema alignment.

        Args:
            force_reload: Force reload even if cached.

        Returns:
            AccountabilityContract with loaded and validated data.
        """
        if self._contract_cache is not None and not force_reload:
            return self._contract_cache

        try:
            # Load YAML
            with open(self.config_path, encoding="utf-8") as f:
                yaml_data = yaml.safe_load(f)

            # Align YAML schema to Pydantic models
            aligned_data = self._align_yaml_schema(yaml_data)

            # Validate and create contract
            contract = AccountabilityContract(**aligned_data)

            self._contract_cache = contract
            logger.info(f"Loaded accountability contract: {contract.service_name} v{contract.version}")

            return contract

        except FileNotFoundError:
            logger.error(f"Contract file not found: {self.config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in contract file: {e}")
            raise
        except ValidationError as e:
            logger.error(f"Contract validation failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load contracts: {e}")
            raise

    def _align_yaml_schema(self, yaml_data: dict[str, Any]) -> dict[str, Any]:
        """Align YAML schema to Pydantic model fields.

        Maps:
        - defaults.security -> default_security
        - defaults.compliance -> default_compliance
        - service_level_objectives -> slos
        """

        aligned_data = {
            "service_name": yaml_data.get("service_name", "unknown"),
            "version": yaml_data.get("version", "1.0.0"),
            "description": yaml_data.get("description", ""),
        }

        # Handle defaults section
        defaults = yaml_data.get("defaults", {})
        if defaults:
            # Map defaults.security -> default_security
            if "security" in defaults:
                aligned_data["default_security"] = SecurityRequirement(**defaults["security"])

            # Map defaults.compliance -> default_compliance
            if "compliance" in defaults:
                aligned_data["default_compliance"] = ComplianceRequirement(**defaults["compliance"])

        # Handle endpoints
        endpoints = yaml_data.get("endpoints", [])
        aligned_endpoints = []

        for endpoint_data in endpoints:
            aligned_endpoint = self._align_endpoint_data(endpoint_data)
            aligned_endpoints.append(aligned_endpoint)

        aligned_data["endpoints"] = aligned_endpoints

        # Handle service_level_objectives -> slos
        slos = yaml_data.get("service_level_objectives", [])
        aligned_slos = []

        for slo_data in slos:
            aligned_slo = ServiceLevelObjective(**slo_data)
            aligned_slos.append(aligned_slo)

        aligned_data["slos"] = aligned_slos

        return aligned_data

    def _align_endpoint_data(self, endpoint_data: dict[str, Any]) -> dict[str, Any]:
        """Align individual endpoint data to Pydantic model."""

        aligned = {
            "path": endpoint_data["path"],
            "methods": endpoint_data["methods"],
            "description": endpoint_data.get("description", ""),
        }

        # Handle performance section
        if "performance" in endpoint_data:
            aligned["performance"] = PerformanceSLA(**endpoint_data["performance"])

        # Handle security section
        if "security" in endpoint_data:
            aligned["security"] = SecurityRequirement(**endpoint_data["security"])

        # Handle compliance section
        if "compliance" in endpoint_data:
            aligned["compliance"] = ComplianceRequirement(**endpoint_data["compliance"])

        # Handle validation rules
        if "request_validation" in endpoint_data:
            aligned["request_validation"] = self._align_validation_rules(endpoint_data["request_validation"])

        if "response_validation" in endpoint_data:
            aligned["response_validation"] = self._align_validation_rules(endpoint_data["response_validation"])

        # Handle other fields
        if "tags" in endpoint_data:
            aligned["tags"] = endpoint_data["tags"]

        if "enabled" in endpoint_data:
            aligned["enabled"] = endpoint_data["enabled"]

        return aligned

    def _align_validation_rules(self, rules_data: dict[str, Any]) -> dict[str, DataValidationRule]:
        """Align validation rules to DataValidationRule objects."""

        aligned_rules = {}

        for field_name, rule_data in rules_data.items():
            if isinstance(rule_data, dict):
                # Set the field name from the dictionary key
                rule_data_with_field = {"field": field_name, **rule_data}
                aligned_rules[field_name] = DataValidationRule(**rule_data_with_field)
            else:
                # Handle simple type specification
                aligned_rules[field_name] = DataValidationRule(field=field_name, type=rule_data, required=True)

        return aligned_rules

    def validate_websocket_support(self) -> bool:
        """Validate that WebSocket methods and wildcard paths are supported."""

        try:
            contract = self.load_contracts()

            websocket_endpoints = [ep for ep in contract.endpoints if "WEBSOCKET" in ep.methods]

            wildcard_endpoints = [ep for ep in contract.endpoints if "*" in ep.path]

            logger.info(f"Found {len(websocket_endpoints)} WebSocket endpoints")
            logger.info(f"Found {len(wildcard_endpoints)} wildcard endpoints")

            # Test matching logic
            test_cases = [
                ("/api/v1/rag/ws/123", "WEBSOCKET"),
                ("/api/v1/rag/ws/session-456", "WEBSOCKET"),
                ("/api/v1/users/123", "GET"),
            ]

            for path, method in test_cases:
                contract = contract.get_endpoint_contract(path, method)
                if contract:
                    logger.info(f"✓ Matched {method} {path} to {contract.path}")
                else:
                    logger.warning(f"✗ No match for {method} {path}")

            return True

        except Exception as e:
            logger.error(f"WebSocket validation failed: {e}")
            return False


# Global contract loader instance
_global_contract_loader: ContractLoader | None = None


def get_contract_loader() -> ContractLoader:
    """Get global contract loader instance."""
    global _global_contract_loader
    if _global_contract_loader is None:
        _global_contract_loader = ContractLoader()
    return _global_contract_loader


def load_accountability_contract(force_reload: bool = False) -> AccountabilityContract:
    """Load accountability contract using global loader."""
    return get_contract_loader().load_contracts(force_reload)

```


**Tool Call: Read file `CascadeProjects/GRID-main/src/grid/resilience/accountability/contracts.py`**
Status: Completed

```CascadeProjects/GRID-main/src/grid/resilience/accountability/contracts.py
SUCCESS: File outline retrieved. This file is too large to read all at once, so the outline below shows the file's structure with line numbers.

IMPORTANT: Do NOT retry this call without line numbers - you will get the same outline.
Instead, use the line numbers below to read specific sections by calling this tool again with start_line and end_line parameters.

# File outline for /home/caraxes/CascadeProjects/GRID-main/src/grid/resilience/accountability/contracts.py

class ContractSeverity [L20-26]
class ViolationType [L29-42]
class ContractViolation [L46-76]
 def violation_type [L60-62]
 def to_dict [L64-76]
class EnforcementResult [L80-119]
 def is_compliant [L93-95]
 def total_penalty_points [L98-100]
 def add_violation [L102-105]
 def to_dict [L107-119]
class ContractManager [L122-146]
 def __init__ [L125-126]
 def register_contract [L128-130]
 def get_contract [L132-134]
 def get_all_contracts [L136-138]
 def find_endpoint_contract [L140-146]
class DataValidationRule [L149-163]
class PerformanceSLA [L166-172]
class SecurityRequirement [L175-184]
class ComplianceRequirement [L187-197]
class EndpointContract [L200-254]
 def validate_http_method [L231-248]
 def update_timestamp [L252-254]
class ServiceLevelObjective [L257-269]
class AccountabilityContract [L272-442]
 def get_endpoint_contract [L293-322]
 def validate_request [L324-330]
 def validate_response [L332-338]
 def _validate_data [L340-442]

Showing symbols 1-29 (total symbols: 29)


NEXT STEPS: To read a specific symbol's implementation, call read_file with the same path plus start_line and end_line from the outline above.
For example, to read a function shown as [L100-150], use start_line: 100 and end_line: 150.
```


**Tool Call: Read file `CascadeProjects/GRID-main/src/grid/resilience/accountability/contract_loader.py`**
Status: Completed

```CascadeProjects/GRID-main/src/grid/resilience/accountability/contract_loader.py
"""
Contract loader with YAML schema alignment.
Maps YAML structure to Pydantic models with proper field aliases.
"""

import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from .contracts import (
    AccountabilityContract,
    ComplianceRequirement,
    DataValidationRule,
    PerformanceSLA,
    SecurityRequirement,
    ServiceLevelObjective,
)

logger = logging.getLogger(__name__)


class ContractLoader:
    """Loads accountability contracts from YAML with schema alignment."""

    def __init__(self, config_path: Path | None = None):
        """Initialize contract loader.

        Args:
            config_path: Path to contracts YAML file.
                Defaults to standard location.
        """
        if config_path is None:
            config_path = (
                Path(__file__).parent.parent.parent.parent.parent / "config" / "accountability" / "contracts.yaml"
            )

        self.config_path = Path(config_path)
        self._contract_cache: AccountabilityContract | None = None

    def load_contracts(self, force_reload: bool = False) -> AccountabilityContract:
        """Load contracts from YAML with schema alignment.

        Args:
            force_reload: Force reload even if cached.

        Returns:
            AccountabilityContract with loaded and validated data.
        """
        if self._contract_cache is not None and not force_reload:
            return self._contract_cache

        try:
            # Load YAML
            with open(self.config_path, encoding="utf-8") as f:
                yaml_data = yaml.safe_load(f)

            # Align YAML schema to Pydantic models
            aligned_data = self._align_yaml_schema(yaml_data)

            # Validate and create contract
            contract = AccountabilityContract(**aligned_data)

            self._contract_cache = contract
            logger.info(f"Loaded accountability contract: {contract.service_name} v{contract.version}")

            return contract

        except FileNotFoundError:
            logger.error(f"Contract file not found: {self.config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in contract file: {e}")
            raise
        except ValidationError as e:
            logger.error(f"Contract validation failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load contracts: {e}")
            raise

    def _align_yaml_schema(self, yaml_data: dict[str, Any]) -> dict[str, Any]:
        """Align YAML schema to Pydantic model fields.

        Maps:
        - defaults.security -> default_security
        - defaults.compliance -> default_compliance
        - service_level_objectives -> slos
        """

        aligned_data = {
            "service_name": yaml_data.get("service_name", "unknown"),
            "version": yaml_data.get("version", "1.0.0"),
            "description": yaml_data.get("description", ""),
        }

        # Handle defaults section
        defaults = yaml_data.get("defaults", {})
        if defaults:
            # Map defaults.security -> default_security
            if "security" in defaults:
                aligned_data["default_security"] = SecurityRequirement(**defaults["security"])

            # Map defaults.compliance -> default_compliance
            if "compliance" in defaults:
                aligned_data["default_compliance"] = ComplianceRequirement(**defaults["compliance"])

        # Handle endpoints
        endpoints = yaml_data.get("endpoints", [])
        aligned_endpoints = []

        for endpoint_data in endpoints:
            aligned_endpoint = self._align_endpoint_data(endpoint_data)
            aligned_endpoints.append(aligned_endpoint)

        aligned_data["endpoints"] = aligned_endpoints

        # Handle service_level_objectives -> slos
        slos = yaml_data.get("service_level_objectives", [])
        aligned_slos = []

        for slo_data in slos:
            aligned_slo = ServiceLevelObjective(**slo_data)
            aligned_slos.append(aligned_slo)

        aligned_data["slos"] = aligned_slos

        return aligned_data

    def _align_endpoint_data(self, endpoint_data: dict[str, Any]) -> dict[str, Any]:
        """Align individual endpoint data to Pydantic model."""

        aligned = {
            "path": endpoint_data["path"],
            "methods": endpoint_data["methods"],
            "description": endpoint_data.get("description", ""),
        }

        # Handle performance section
        if "performance" in endpoint_data:
            aligned["performance"] = PerformanceSLA(**endpoint_data["performance"])

        # Handle security section
        if "security" in endpoint_data:
            aligned["security"] = SecurityRequirement(**endpoint_data["security"])

        # Handle compliance section
        if "compliance" in endpoint_data:
            aligned["compliance"] = ComplianceRequirement(**endpoint_data["compliance"])

        # Handle validation rules
        if "request_validation" in endpoint_data:
            aligned["request_validation"] = self._align_validation_rules(endpoint_data["request_validation"])

        if "response_validation" in endpoint_data:
            aligned["response_validation"] = self._align_validation_rules(endpoint_data["response_validation"])

        # Handle other fields
        if "tags" in endpoint_data:
            aligned["tags"] = endpoint_data["tags"]

        if "enabled" in endpoint_data:
            aligned["enabled"] = endpoint_data["enabled"]

        return aligned

    def _align_validation_rules(self, rules_data: dict[str, Any]) -> dict[str, DataValidationRule]:
        """Align validation rules to DataValidationRule objects."""

        aligned_rules = {}

        for field_name, rule_data in rules_data.items():
            if isinstance(rule_data, dict):
                # Set the field name from the dictionary key
                rule_data_with_field = {"field": field_name, **rule_data}
                aligned_rules[field_name] = DataValidationRule(**rule_data_with_field)
            else:
                # Handle simple type specification
                aligned_rules[field_name] = DataValidationRule(field=field_name, type=rule_data, required=True)

        return aligned_rules

    def validate_websocket_support(self) -> bool:
        """Validate that WebSocket methods and wildcard paths are supported."""

        try:
            contract = self.load_contracts()

            websocket_endpoints = [ep for ep in contract.endpoints if "WEBSOCKET" in ep.methods]

            wildcard_endpoints = [ep for ep in contract.endpoints if "*" in ep.path]

            logger.info(f"Found {len(websocket_endpoints)} WebSocket endpoints")
            logger.info(f"Found {len(wildcard_endpoints)} wildcard endpoints")

            # Test matching logic
            test_cases = [
                ("/api/v1/rag/ws/123", "WEBSOCKET"),
                ("/api/v1/rag/ws/session-456", "WEBSOCKET"),
                ("/api/v1/users/123", "GET"),
            ]

            for path, method in test_cases:
                contract = contract.get_endpoint_contract(path, method)
                if contract:
                    logger.info(f"✓ Matched {method} {path} to {contract.path}")
                else:
                    logger.warning(f"✗ No match for {method} {path}")

            return True

        except Exception as e:
            logger.error(f"WebSocket validation failed: {e}")
            return False


# Global contract loader instance
_global_contract_loader: ContractLoader | None = None


def get_contract_loader() -> ContractLoader:
    """Get global contract loader instance."""
    global _global_contract_loader
    if _global_contract_loader is None:
        _global_contract_loader = ContractLoader()
    return _global_contract_loader


def load_accountability_contract(force_reload: bool = False) -> AccountabilityContract:
    """Load accountability contract using global loader."""
    return get_contract_loader().load_contracts(force_reload)

```


**Tool Call: 1 match**
Status: Completed

file:///home/caraxes/roots/GRID/src/infrastructure/parasite_guard/contracts.py

**Tool Call: 1 match**
Status: Completed

file:///home/caraxes/roots/GRID/src/application/mothership/middleware/accountability_contract.py

**Tool Call: Search files for regex `boundary|gate|envelope|nonce`**
Status: Completed

No matches found

**Tool Call: List the `roots/GRID/src/grid/resilience` directory's contents**
Status: Completed

# Folders:
caraxes/roots/GRID/src/grid/resilience/accountability

# Files:
caraxes/roots/GRID/src/grid/resilience/__init__.py
caraxes/roots/GRID/src/grid/resilience/api.py
caraxes/roots/GRID/src/grid/resilience/data_corruption_penalty.py
caraxes/roots/GRID/src/grid/resilience/drt_monitor.py
caraxes/roots/GRID/src/grid/resilience/metrics.py
caraxes/roots/GRID/src/grid/resilience/observed_decorators.py
caraxes/roots/GRID/src/grid/resilience/penalties.py
caraxes/roots/GRID/src/grid/resilience/policies.py
caraxes/roots/GRID/src/grid/resilience/policy_override.py
caraxes/roots/GRID/src/grid/resilience/retry_decorator.py


**Tool Call: List the `roots/GRID/src/infrastructure` directory's contents**
Status: Completed

# Folders:
caraxes/roots/GRID/src/infrastructure/ai_ml
caraxes/roots/GRID/src/infrastructure/api_gateway
caraxes/roots/GRID/src/infrastructure/config
caraxes/roots/GRID/src/infrastructure/event_bus
caraxes/roots/GRID/src/infrastructure/logging
caraxes/roots/GRID/src/infrastructure/metrics
caraxes/roots/GRID/src/infrastructure/orchestrator
caraxes/roots/GRID/src/infrastructure/parasite_guard
caraxes/roots/GRID/src/infrastructure/service_mesh

# Files:
caraxes/roots/GRID/src/infrastructure/__init__.py


**Tool Call: List the `roots/GRID/boundaries/transition_gate` directory's contents**
Status: Completed

# Folders:
caraxes/roots/GRID/boundaries/transition_gate/contracts

# Files:
caraxes/roots/GRID/boundaries/transition_gate/__init__.py
caraxes/roots/GRID/boundaries/transition_gate/credential.py
caraxes/roots/GRID/boundaries/transition_gate/envelope.py
caraxes/roots/GRID/boundaries/transition_gate/fingerprint.py
caraxes/roots/GRID/boundaries/transition_gate/gate_keeper.py
caraxes/roots/GRID/boundaries/transition_gate/nonce.py


**Tool Call: Read file `roots/GRID/.grid/debug-contract.json` (lines 1-69)**
Status: Completed

```roots/GRID/.grid/debug-contract.json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "contract_id": "grid-debug-v1.0",
  "version": "1.0.0",
  "description": "GRID Debug Contract — a machine-readable specification of 30 checks across 6 quality dimensions that defines 'clean state' for the GRID codebase. Any LLM agent, CI pipeline, or developer can execute this contract to validate codebase health.",
  "created": "2026-02-16",
  "codebase": {
    "name": "grid-intelligence",
    "root": ".",
    "languages": [
      "python",
      "typescript",
      "javascript"
    ],
    "python_version": ">=3.13,<3.14",
    "node_version": ">=18",
    "package_manager_python": "uv",
    "package_manager_js": "npm",
    "source_paths": [
      "src/",
      "safety/",
      "boundaries/",
      "cognition/",
      "arena_api/"
    ],
    "frontend_path": "frontend/",
    "test_paths": [
      "tests/",
      "safety/tests/",
      "boundaries/tests/"
    ],
    "total_python_files": 715,
    "total_packages": 9
  },
  "environment": {
    "required_tools": [
      {
        "name": "uv",
        "min_version": "0.4.0",
        "verify": "uv --version"
      },
      {
        "name": "python",
        "min_version": "3.13",
        "verify": "python --version"
      },
      {
        "name": "node",
        "min_version": "18.0",
        "verify": "node --version"
      },
      {
        "name": "npm",
        "min_version": "9.0",
        "verify": "npm --version"
      }
    ],
    "env_vars": {
      "required": [
        "MOTHERSHIP_ENVIRONMENT"
      ],
      "recommended_test_values": {
        "MOTHERSHIP_ENVIRONMENT": "test",
        "MOTHERSHIP_DATABASE_URL": "sqlite:///:memory:",
        "MOTHERSHIP_USE_DATABRICKS": "false",
        "MOTHERSHIP_REDIS_ENABLED": "false"
      }
    }
  },

```


## Assistant

<thinking>
Now let me read the remaining implementation files and dig deeper into the boundary/transition gate code.
</thinking>

Now let me read the parasite guard, accountability middleware, boundary enforcement code, and key contract model sections.

**Tool Call: Read file `roots/GRID/src/infrastructure/parasite_guard/contracts.py`**
Status: Completed

```roots/GRID/src/infrastructure/parasite_guard/contracts.py
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable


@dataclass
class HealthStatus:
    healthy: bool
    latency_ms: float
    error_rate: float
    confidence: float  # Statistical confidence level


@dataclass
class PrecisionMetrics:
    """Precision metrics for detector validation."""

    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int

    @property
    def precision(self) -> float:
        total = self.true_positives + self.false_positives
        return self.true_positives / total if total > 0 else 0.0

    @property
    def recall(self) -> float:
        total = self.true_positives + self.false_negatives
        return self.true_positives / total if total > 0 else 0.0

    @property
    def f1_score(self) -> float:
        p, r = self.precision, self.recall
        return 2 * (p * r) / (p + r) if (p + r) > 0 else 0.0

    @property
    def accuracy(self) -> float:
        total = self.true_positives + self.false_positives + self.true_negatives + self.false_negatives
        return (self.true_positives + self.true_negatives) / total if total > 0 else 0.0


@dataclass
class DetectionResult:
    """Standardized detection result."""

    detected: bool
    confidence: float
    details: dict[str, Any]


@dataclass
class ParasiteContext:
    """Context information for a potential parasite."""

    component: str
    severity: str
    pattern: str
    details: dict[str, Any]


@dataclass
class SanitizationResult:
    """Result of a sanitization attempt."""

    success: bool
    details: dict[str, Any]


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@runtime_checkable
class DetectorContract(Protocol):
    """Strict contract for all detectors."""

    name: str
    component: str

    async def detect(self, context: dict) -> DetectionResult: ...
    def validate_config(self) -> bool: ...
    def get_health(self) -> HealthStatus: ...
    def get_precision_metrics(self) -> PrecisionMetrics: ...


@runtime_checkable
class SanitizerContract(Protocol):
    """Strict contract for all sanitizers."""

    component: str
    success_rate: float  # Target: 99.2%+ for WebSocket, 97.5%+ for EventBus

    async def sanitize(self, context: ParasiteContext) -> SanitizationResult: ...
    async def rollback(self, context: ParasiteContext) -> bool: ...
    def can_sanitize(self, context: ParasiteContext) -> bool: ...


@dataclass
class Alert:
    """Alert structure."""

    id: str
    severity: Severity
    component: str
    pattern: str
    message: str
    timestamp: datetime
    context: Any | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class AlertChannel(Protocol):
    """Protocol for alert channels."""

    async def send(self, alert: Alert) -> None: ...


@runtime_checkable
class AlerterContract(Protocol):
    """Contract for alerting system."""

    async def alert(self, context: ParasiteContext, severity: Severity) -> None: ...
    async def escalate(self, context: ParasiteContext) -> None: ...


# Contract validation helpers


def validate_detector_contract(detector: Any) -> tuple[bool, list[str]]:
    """Validate that an object satisfies DetectorContract.

    Args:
        detector: Object to validate.

    Returns:
        Tuple of (is_valid, list of errors).
    """
    errors: list[str] = []

    if not isinstance(detector, DetectorContract):
        errors.append("Does not implement DetectorContract protocol")

    if not hasattr(detector, "name") or not isinstance(getattr(detector, "name", None), str):
        errors.append("Missing or invalid 'name' attribute")

    if not hasattr(detector, "component") or not isinstance(getattr(detector, "component", None), str):
        errors.append("Missing or invalid 'component' attribute")

    if not callable(getattr(detector, "detect", None)):
        errors.append("Missing 'detect' method")

    if not callable(getattr(detector, "validate_config", None)):
        errors.append("Missing 'validate_config' method")

    if not callable(getattr(detector, "get_health", None)):
        errors.append("Missing 'get_health' method")

    if not callable(getattr(detector, "get_precision_metrics", None)):
        errors.append("Missing 'get_precision_metrics' method")

    return len(errors) == 0, errors


def validate_sanitizer_contract(sanitizer: Any) -> tuple[bool, list[str]]:
    """Validate that an object satisfies SanitizerContract.

    Args:
        sanitizer: Object to validate.

    Returns:
        Tuple of (is_valid, list of errors).
    """
    errors: list[str] = []

    if not isinstance(sanitizer, SanitizerContract):
        errors.append("Does not implement SanitizerContract protocol")

    if not hasattr(sanitizer, "component") or not isinstance(getattr(sanitizer, "component", None), str):
        errors.append("Missing or invalid 'component' attribute")

    if not hasattr(sanitizer, "success_rate"):
        errors.append("Missing 'success_rate' attribute")
    else:
        rate = getattr(sanitizer, "success_rate", None)
        if not isinstance(rate, (int, float)) or not (0.0 <= rate <= 1.0):
            errors.append("'success_rate' must be a float between 0.0 and 1.0")

    if not callable(getattr(sanitizer, "sanitize", None)):
        errors.append("Missing 'sanitize' method")

    if not callable(getattr(sanitizer, "rollback", None)):
        errors.append("Missing 'rollback' method")

    if not callable(getattr(sanitizer, "can_sanitize", None)):
        errors.append("Missing 'can_sanitize' method")

    return len(errors) == 0, errors


def validate_alerter_contract(alerter: Any) -> tuple[bool, list[str]]:
    """Validate that an object satisfies AlerterContract.

    Args:
        alerter: Object to validate.

    Returns:
        Tuple of (is_valid, list of errors).
    """
    errors: list[str] = []

    if not isinstance(alerter, AlerterContract):
        errors.append("Does not implement AlerterContract protocol")

    if not callable(getattr(alerter, "alert", None)):
        errors.append("Missing 'alert' method")

    if not callable(getattr(alerter, "escalate", None)):
        errors.append("Missing 'escalate' method")

    return len(errors) == 0, errors

```


**Tool Call: Read file `roots/GRID/src/application/mothership/middleware/accountability_contract.py`**
Status: Completed

```roots/GRID/src/application/mothership/middleware/accountability_contract.py
"""
Accountability Contract Middleware.
Enforces accountability contracts with RBAC and claims support.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Callable

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from grid.resilience.accountability.contracts import EnforcementResult

# Import enhanced enforcer
from grid.resilience.accountability.enforcer_enhanced import (
    get_enhanced_accountability_enforcer,
)

logger = logging.getLogger(__name__)


class AccountabilityContractMiddleware(BaseHTTPMiddleware):
    """Middleware that enforces accountability contracts for all requests."""

    def __init__(
        self,
        app: Any,
        enforcement_mode: str = "monitor",  # monitor, enforce, disabled
        contract_path: str | None = None,
        skip_paths: list[str] | None = None,
    ):
        """Initialize accountability contract middleware.

        Args:
            app: FastAPI application
            enforcement_mode: How to handle violations (monitor/enforce/disabled)
            contract_path: Path to contract file (optional)
            skip_paths: List of paths to skip enforcement
        """
        super().__init__(app)

        self.enforcement_mode = enforcement_mode
        self.contract_path = contract_path
        self.skip_paths = skip_paths or [
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/favicon.ico",
        ]

        # Initialize enhanced enforcer
        self.enforcer = get_enhanced_accountability_enforcer()
        self.enforcer.enforcement_mode = enforcement_mode
        if contract_path:
            self.enforcer.contract_path = contract_path

        logger.info(
            f"Accountability contract middleware initialized: mode={enforcement_mode}, "
            f"skip_paths={len(self.skip_paths)}"
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through accountability contract enforcement."""

        # Skip enforcement for certain paths
        if self._should_skip_enforcement(request):
            return await call_next(request)

        start_time = time.time()

        response = None
        try:
            # Extract authentication context
            auth_context = await self._extract_auth_context(request)

            # Extract request data
            request_data = await self._extract_request_data(request)

            # Enforce request contract
            request_result = self.enforcer.enforce_request(
                path=request.url.path,
                method=request.method,
                auth_context=auth_context,
                request_data=request_data,
                client_ip=self._get_client_ip(request),
            )

            # Handle request enforcement result
            if not request_result.allowed:
                return self._create_blocked_response(request_result)

            # Process request
            response = await call_next(request)

            # Calculate response time
            response_time_ms = (time.time() - start_time) * 1000

            # Extract response data for validation
            response_data = await self._extract_response_data(response)

            # Enforce response contract
            response_result = self.enforcer.enforce_response(
                path=request.url.path,
                method=request.method,
                response_data=response_data,
                response_status=response.status_code,
                response_time_ms=response_time_ms,
            )

            # Add enforcement headers
            self._add_enforcement_headers(response, request_result, response_result)

            # Log violations
            self._log_violations(request, request_result, response_result)

            return response

        except Exception as e:
            logger.error(f"Accountability middleware error: {e}")
            # If we already have a response, just return it (maybe add header)
            if response is not None:
                response.headers["X-Accountability-Error"] = "middleware_error"
                return response

            # If we haven't called call_next yet, call it now
            response = await call_next(request)
            response.headers["X-Accountability-Error"] = "middleware_error"
            return response

    def _should_skip_enforcement(self, request: Request) -> bool:
        """Check if enforcement should be skipped for this request."""
        path = request.url.path

        # Skip exact matches
        if path in self.skip_paths:
            return True

        # Skip prefix matches
        for skip_path in self.skip_paths:
            if path.startswith(skip_path):
                return True

        return False

    async def _extract_auth_context(self, request: Request) -> dict[str, Any] | None:
        """Extract authentication context from request."""
        try:
            # Try to get auth context from request state (set by auth middleware)
            if hasattr(request.state, "auth_context"):
                return request.state.auth_context

            # Try to extract from headers (fallback)
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # This would need JWT verification - for now, just mark as authenticated
                return {
                    "authenticated": True,
                    "user_id": "unknown",
                    "roles": ["user"],  # Default role
                    "permissions": ["read", "execute"],
                }

            api_key = request.headers.get("x-api-key")
            if api_key:
                return {
                    "authenticated": True,
                    "user_id": "api_user",
                    "roles": ["service_account"],
                    "permissions": ["read", "write", "execute"],
                }

            # No authentication found
            return {
                "authenticated": False,
                "user_id": "anonymous",
                "roles": ["anonymous"],
                "permissions": ["read"],
            }

        except Exception as e:
            logger.warning(f"Failed to extract auth context: {e}")
            return None

    async def _extract_request_data(self, request: Request) -> dict[str, Any] | None:
        """Extract request data for validation."""
        try:
            # Only extract for methods that typically have bodies
            if request.method in ["POST", "PUT", "PATCH"]:
                # For JSON requests
                if "application/json" in request.headers.get("content-type", ""):
                    return await request.json()

                # For form requests
                if "application/x-www-form-urlencoded" in request.headers.get("content-type", ""):
                    form_data = await request.form()
                    return dict(form_data)

            # For GET requests, extract query params
            if request.method == "GET":
                return dict(request.query_params)

            return None

        except Exception as e:
            logger.debug(f"Failed to extract request data: {e}")
            return None

    async def _extract_response_data(self, response: Response) -> dict[str, Any] | None:
        """Extract response data for validation."""
        try:
            # Only attempt validation for JSON responses
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                # Note: This is a simplified approach
                # In practice, you'd need to capture the response body
                # before it's sent to the client
                return None  # Would need response body capture

            return None

        except Exception as e:
            logger.debug(f"Failed to extract response data: {e}")
            return None

    def _get_client_ip(self, request: Request) -> str | None:
        """Extract client IP from request."""
        try:
            # Check for forwarded headers
            forwarded_for = request.headers.get("x-forwarded-for")
            if forwarded_for:
                return forwarded_for.split(",")[0].strip()

            real_ip = request.headers.get("x-real-ip")
            if real_ip:
                return real_ip

            return request.client.host if request.client else None

        except Exception:
            return None

    def _create_blocked_response(self, request_result: EnforcementResult) -> Response:
        """Create response for blocked requests."""

        # Find the most critical violation
        critical_violations = [v for v in request_result.violations if v.severity.value == "critical"]
        high_violations = [v for v in request_result.violations if v.severity.value == "high"]

        if critical_violations:
            status_code = status.HTTP_403_FORBIDDEN
            detail = "Access denied: Critical security violations"
        elif high_violations:
            status_code = status.HTTP_403_FORBIDDEN
            detail = "Access denied: Security policy violations"
        else:
            status_code = status.HTTP_400_BAD_REQUEST
            detail = "Access denied: Policy violations"

        # Create JSON error response
        error_response = {
            "error": "access_denied",
            "detail": detail,
            "violations": [
                {
                    "type": v.type.value,
                    "severity": v.severity.value,
                    "message": v.message,
                    "field": v.field,
                }
                for v in request_result.violations
            ],
            "enforcement_mode": self.enforcement_mode,
        }

        return Response(
            content=json.dumps(error_response),
            status_code=status_code,
            media_type="application/json",
        )

    def _add_enforcement_headers(
        self,
        response: Response,
        request_result: EnforcementResult,
        response_result: EnforcementResult | None,
    ) -> None:
        """Add accountability enforcement headers to the response."""
        response.headers["X-Accountability-Status"] = "enforced" if self.enforcement_mode == "enforce" else "monitored"

        total_violations = len(request_result.violations)
        if response_result:
            total_violations += len(response_result.violations)

        response.headers["X-Accountability-Violation-Count"] = str(total_violations)

        if total_violations > 0:
            response.headers["X-Accountability-Violation"] = "true"

    def _log_violations(
        self,
        request: Request,
        request_result: EnforcementResult,
        response_result: EnforcementResult | None,
    ) -> None:
        """Log accountability violations for audit trail."""
        all_violations = list(request_result.violations)
        if response_result:
            all_violations.extend(response_result.violations)

        if not all_violations:
            return

        for violation in all_violations:
            log_data = {
                "path": str(request.url.path),
                "method": request.method,
                "type": violation.type.value,
                "severity": violation.severity.value,
                "message": violation.message,
                "field": violation.field,
                "penalty_points": violation.penalty_points,
                "enforcement_mode": self.enforcement_mode,
            }

            if violation.severity.value in ["critical", "high"]:
                logger.error(f"Accountability violation: {log_data}")
            else:
                logger.warning(f"Accountability violation: {log_data}")

        # Log summary
        logger.info(
            f"Accountability check: {request.method} {request.url.path} "
            f"- {len(all_violations)} violations, mode={self.enforcement_mode}"
        )


# Global middleware instance for access
_global_accountability_middleware: AccountabilityContractMiddleware | None = None


def get_accountability_middleware() -> AccountabilityContractMiddleware:
    """Get the global accountability contract middleware instance."""
    global _global_accountability_middleware
    if _global_accountability_middleware is None:
        raise RuntimeError("Accountability contract middleware not initialized")
    return _global_accountability_middleware


def set_accountability_middleware(middleware: AccountabilityContractMiddleware) -> None:
    """Set the global accountability contract middleware instance."""
    global _global_accountability_middleware
    _global_accountability_middleware = middleware

```


**Tool Call: Read file `roots/GRID/boundaries/transition_gate/envelope.py`**
Status: Completed

```roots/GRID/boundaries/transition_gate/envelope.py
"""
Transition Envelope: sealed artifact container for cross-partition transfers.

The envelope is the sole trusted artifact crossing the E:\\ → C:\\ boundary.
It contains the payload, cryptographic integrity proofs, a single-use nonce,
timestamp, scope declaration, and fingerprints.

Security invariants:
- Payload hash is computed at seal time and immutable
- User fingerprint binds the envelope to the sealing identity
- Machine fingerprint binds the envelope to the sealing host
- Nonce ensures single-use (burn-after-verify)
- Timestamp enables freshness checks (max_age enforcement)
- Scope declaration limits what the receiving side may do with the payload
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from boundaries.transition_gate.fingerprint import (  # type: ignore[import-untyped]
    compute_machine_fingerprint,
    compute_payload_hash,
    compute_user_fingerprint,
)
from boundaries.transition_gate.nonce import NonceRegistry  # type: ignore[import-untyped]


@dataclass(frozen=True)
class ScopeDeclaration:
    """
    Declares what the receiving side is permitted to do with this envelope.

    Permissions follow least-privilege: only the listed actions are allowed.
    """

    permissions: tuple[str, ...] = ("read_only",)
    target_project: str | None = None
    target_path: str | None = None
    max_execution_time_seconds: int = 300
    network_allowed: bool = False
    notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "permissions": list(self.permissions),
            "target_project": self.target_project,
            "target_path": self.target_path,
            "max_execution_time_seconds": self.max_execution_time_seconds,
            "network_allowed": self.network_allowed,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ScopeDeclaration:
        return cls(
            permissions=tuple(d.get("permissions", ("read_only",))),
            target_project=d.get("target_project"),
            target_path=d.get("target_path"),
            max_execution_time_seconds=int(d.get("max_execution_time_seconds", 300)),
            network_allowed=d.get("network_allowed", False),
            notes=d.get("notes"),
        )


# Well-known permission constants for scope declarations
PERM_DEPLOY = "deploy"
PERM_RUN_TESTS = "run_tests"
PERM_START_SERVER = "start_server"
PERM_READ_ONLY = "read_only"
PERM_WRITE_RESULTS = "write_results"
PERM_NETWORK = "network"

ALL_KNOWN_PERMISSIONS = frozenset(
    {
        PERM_DEPLOY,
        PERM_RUN_TESTS,
        PERM_START_SERVER,
        PERM_READ_ONLY,
        PERM_WRITE_RESULTS,
        PERM_NETWORK,
    }
)


@dataclass
class TransitionEnvelope:
    """
    Sealed envelope for cross-partition artifact transfer.

    This is the ONLY trusted object that crosses the E:\\ → C:\\ boundary.
    It is created by seal_envelope() and verified by GateKeeper.verify().

    Fields:
        envelope_id: Unique identifier for this envelope (UUID4).
        payload: The artifact data being transferred (JSON-serializable).
        payload_hash: SHA-256 of the canonical JSON serialization of payload.
        nonce: Single-use nonce from the NonceRegistry.
        timestamp: Unix timestamp of seal time.
        user_fingerprint: HMAC-SHA256 binding identity to machine.
        machine_fingerprint: SHA-256 of stable machine attributes.
        scope: Scope declaration limiting receiver actions.
        source_partition: Label of the source partition (e.g. ``E:\\``).
        target_partition: Label of the target partition (e.g. ``C:\\``).
        sealed_by: Optional human-readable identifier of the sealer.
        tests_passed: Whether the source project's tests passed before sealing.
        lint_passed: Whether the source project's linting passed before sealing.
        metadata: Optional additional metadata.
    """

    envelope_id: str
    payload: Any
    payload_hash: str
    nonce: str
    timestamp: float
    user_fingerprint: str
    machine_fingerprint: str
    scope: ScopeDeclaration
    source_partition: str = "E:\\"
    target_partition: str = "C:\\Users\\USER\\cascadeprojects"
    sealed_by: str | None = None
    tests_passed: bool = False
    lint_passed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the envelope to a dictionary."""
        d = asdict(self)
        d["scope"] = self.scope.to_dict()
        return d

    def to_json(self, indent: int = 2) -> str:
        """Serialize the envelope to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> TransitionEnvelope:
        """Deserialize an envelope from a dictionary."""
        scope_data = d.get("scope", {})
        scope = ScopeDeclaration.from_dict(scope_data) if isinstance(scope_data, dict) else ScopeDeclaration()

        return cls(
            envelope_id=d["envelope_id"],
            payload=d["payload"],
            payload_hash=d["payload_hash"],
            nonce=d["nonce"],
            timestamp=float(d["timestamp"]),
            user_fingerprint=d["user_fingerprint"],
            machine_fingerprint=d["machine_fingerprint"],
            scope=scope,
            source_partition=d.get("source_partition", "E:\\"),
            target_partition=d.get("target_partition", "C:\\Users\\USER\\cascadeprojects"),
            sealed_by=d.get("sealed_by"),
            tests_passed=d.get("tests_passed", False),
            lint_passed=d.get("lint_passed", False),
            metadata=d.get("metadata", {}),
        )

    @classmethod
    def from_json(cls, json_str: str) -> TransitionEnvelope:
        """Deserialize an envelope from a JSON string."""
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def from_file(cls, path: Path | str) -> TransitionEnvelope:
        """Load an envelope from a JSON file."""
        with open(path, encoding="utf-8") as f:
            return cls.from_dict(json.load(f))

    def write_to_file(self, path: Path | str) -> Path:
        """
        Write the sealed envelope to a JSON file.

        Uses atomic write (temp + rename) to prevent partial writes.

        Args:
            path: Destination file path.

        Returns:
            The resolved Path where the envelope was written.
        """
        dest = Path(path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        tmp_path = dest.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
        tmp_path.replace(dest)
        return dest.resolve()

    @property
    def age_seconds(self) -> float:
        """How many seconds ago this envelope was sealed."""
        return time.time() - self.timestamp

    @property
    def is_quality_gated(self) -> bool:
        """Whether this envelope passed both test and lint gates."""
        return self.tests_passed and self.lint_passed


def seal_envelope(
    payload: Any,
    *,
    user_secret: str,
    nonce_registry: NonceRegistry,
    scope: ScopeDeclaration | None = None,
    source_partition: str = "E:\\",
    target_partition: str = "C:\\Users\\USER\\cascadeprojects",
    sealed_by: str | None = None,
    tests_passed: bool = False,
    lint_passed: bool = False,
    metadata: dict[str, Any] | None = None,
    machine_fingerprint_overrides: dict[str, str] | None = None,
    extra_fingerprint_context: str | None = None,
) -> TransitionEnvelope:
    """
    Seal a payload into a TransitionEnvelope with full cryptographic binding.

    This is the primary entry point for the seal side of the pipeline.
    It computes all hashes, generates a nonce, and returns a sealed envelope
    ready for transfer.

    Pipeline steps performed:
    1. Generate envelope ID (UUID4)
    2. Compute payload hash (SHA-256 of canonical JSON)
    3. Compute machine fingerprint (SHA-256 of OS attributes)
    4. Compute user fingerprint (HMAC-SHA256 of secret + machine identity)
    5. Generate and register a single-use nonce
    6. Capture current timestamp
    7. Assemble the sealed envelope

    Args:
        payload: JSON-serializable artifact data to transfer.
        user_secret: Shared secret for HMAC fingerprint.
        nonce_registry: NonceRegistry instance for nonce generation.
        scope: Scope declaration for the receiver. Defaults to read_only.
        source_partition: Source partition label.
        target_partition: Target partition label.
        sealed_by: Human-readable sealer identifier.
        tests_passed: Whether source project tests passed before sealing.
        lint_passed: Whether source project linting passed before sealing.
        metadata: Additional metadata to include.
        machine_fingerprint_overrides: Optional overrides for machine
            fingerprint computation (for testing).
        extra_fingerprint_context: Optional extra context for user fingerprint.

    Returns:
        A sealed TransitionEnvelope ready for writing to disk and transfer.

    Raises:
        ValueError: If user_secret is empty.
        TypeError: If payload is not JSON-serializable.
    """
    if not user_secret:
        raise ValueError("user_secret must not be empty for sealing")

    envelope_id = str(uuid.uuid4())

    # Step 1: Payload integrity
    payload_hash = compute_payload_hash(payload)

    # Step 2: Machine fingerprint
    fp_kwargs = machine_fingerprint_overrides or {}
    machine_fp = compute_machine_fingerprint(**fp_kwargs)

    # Step 3: User fingerprint (binds secret to machine)
    user_fp = compute_user_fingerprint(
        user_secret,
        machine_id=machine_fp,
        extra_context=extra_fingerprint_context,
    )

    # Step 4: Nonce (single-use, registered)
    nonce = nonce_registry.generate(
        envelope_id=envelope_id,
        source=source_partition,
    )

    # Step 5: Timestamp
    timestamp = time.time()

    # Step 6: Scope
    if scope is None:
        scope = ScopeDeclaration()

    # Step 7: Assemble
    return TransitionEnvelope(
        envelope_id=envelope_id,
        payload=payload,
        payload_hash=payload_hash,
        nonce=nonce,
        timestamp=timestamp,
        user_fingerprint=user_fp,
        machine_fingerprint=machine_fp,
        scope=scope,
        source_partition=source_partition,
        target_partition=target_partition,
        sealed_by=sealed_by,
        tests_passed=tests_passed,
        lint_passed=lint_passed,
        metadata=metadata or {},
    )

```


**Tool Call: Read file `roots/GRID/boundaries/transition_gate/nonce.py`**
Status: Completed

```roots/GRID/boundaries/transition_gate/nonce.py
"""
Nonce Registry: single-use nonce generation, verification, and persistence.

Each sealed envelope gets a unique nonce. On verification, the nonce is
"burned" (marked as used) so replay attacks are rejected. The registry
persists to a JSON file for durability across process restarts.

Security properties:
- Nonces are UUID4 (128-bit random, cryptographically strong)
- Burn-after-verify: a nonce can only be used once
- Persistence: survives process restarts via JSON file
- Pruning: expired nonces are cleaned up to prevent unbounded growth
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class NonceEntry:
    """Record of a nonce's lifecycle."""

    nonce: str
    created_at: float
    burned: bool = False
    burned_at: float | None = None
    envelope_id: str | None = None
    source: str | None = None

    def is_expired(self, max_age_seconds: float) -> bool:
        """Check if this nonce has exceeded its maximum age."""
        return (time.time() - self.created_at) > max_age_seconds

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> NonceEntry:
        return cls(
            nonce=d["nonce"],
            created_at=float(d["created_at"]),
            burned=d.get("burned", False),
            burned_at=d.get("burned_at"),
            envelope_id=d.get("envelope_id"),
            source=d.get("source"),
        )


class NonceRegistry:
    """
    Thread-safe, persistent single-use nonce registry.

    Nonces are generated at seal time and burned at verify time.
    The registry can be backed by a JSON file for durability.

    Args:
        registry_path: Path to the JSON persistence file. If None,
                       operates in-memory only (no persistence).
        max_age_seconds: Maximum age of a nonce before it is considered
                         expired. Default is 600 seconds (10 minutes).
        auto_prune: Whether to automatically prune expired nonces on
                    each operation. Default is True.
    """

    def __init__(
        self,
        registry_path: Path | str | None = None,
        *,
        max_age_seconds: float = 600.0,
        auto_prune: bool = True,
    ):
        self._registry_path = Path(registry_path) if registry_path else None
        self._max_age_seconds = max_age_seconds
        self._auto_prune = auto_prune
        self._lock = threading.Lock()
        self._nonces: dict[str, NonceEntry] = {}
        self._load()

    @property
    def max_age_seconds(self) -> float:
        """Maximum nonce lifetime in seconds."""
        return self._max_age_seconds

    def generate(
        self,
        *,
        envelope_id: str | None = None,
        source: str | None = None,
    ) -> str:
        """
        Generate a new single-use nonce and register it.

        Args:
            envelope_id: Optional envelope ID to associate with this nonce.
            source: Optional source identifier (e.g. "E:\\" partition label).

        Returns:
            The generated nonce string (UUID4 hex).
        """
        nonce = uuid.uuid4().hex
        entry = NonceEntry(
            nonce=nonce,
            created_at=time.time(),
            envelope_id=envelope_id,
            source=source,
        )

        with self._lock:
            if self._auto_prune:
                self._prune_expired_locked()
            self._nonces[nonce] = entry
            self._persist_locked()

        return nonce

    def validate(self, nonce: str) -> tuple[bool, str]:
        """
        Check if a nonce is valid (exists, not burned, not expired)
        WITHOUT burning it. Use this for dry-run verification.

        Args:
            nonce: The nonce string to validate.

        Returns:
            Tuple of (is_valid, reason). reason is "valid" on success,
            or a descriptive rejection reason on failure.
        """
        with self._lock:
            if self._auto_prune:
                self._prune_expired_locked()

            entry = self._nonces.get(nonce)
            if entry is None:
                return (False, "nonce_unknown")
            if entry.burned:
                return (False, "nonce_already_burned")
            if entry.is_expired(self._max_age_seconds):
                return (False, "nonce_expired")
            return (True, "valid")

    def burn(self, nonce: str) -> tuple[bool, str]:
        """
        Burn a nonce (mark as used). This is the core replay-prevention
        mechanism. A burned nonce can never be used again.

        Args:
            nonce: The nonce string to burn.

        Returns:
            Tuple of (success, reason). success is True if the nonce was
            valid and has now been burned. reason describes the outcome.
        """
        with self._lock:
            if self._auto_prune:
                self._prune_expired_locked()

            entry = self._nonces.get(nonce)
            if entry is None:
                return (False, "nonce_unknown")
            if entry.burned:
                return (False, "nonce_already_burned")
            if entry.is_expired(self._max_age_seconds):
                return (False, "nonce_expired")

            entry.burned = True
            entry.burned_at = time.time()
            self._persist_locked()
            return (True, "burned")

    def is_burned(self, nonce: str) -> bool:
        """Check if a specific nonce has been burned."""
        with self._lock:
            entry = self._nonces.get(nonce)
            if entry is None:
                return False
            return entry.burned

    def contains(self, nonce: str) -> bool:
        """Check if a nonce exists in the registry (burned or not)."""
        with self._lock:
            return nonce in self._nonces

    def prune_expired(self) -> int:
        """
        Remove expired nonces from the registry.

        Returns:
            Number of nonces pruned.
        """
        with self._lock:
            count = self._prune_expired_locked()
            if count > 0:
                self._persist_locked()
            return count

    def clear(self) -> None:
        """Clear all nonces from the registry. Use with caution."""
        with self._lock:
            self._nonces.clear()
            self._persist_locked()

    @property
    def count(self) -> int:
        """Total number of nonces in the registry (burned + active)."""
        with self._lock:
            return len(self._nonces)

    @property
    def active_count(self) -> int:
        """Number of nonces that are not burned and not expired."""
        with self._lock:
            return sum(1 for e in self._nonces.values() if not e.burned and not e.is_expired(self._max_age_seconds))

    @property
    def burned_count(self) -> int:
        """Number of burned nonces still in the registry."""
        with self._lock:
            return sum(1 for e in self._nonces.values() if e.burned)

    def get_entry(self, nonce: str) -> NonceEntry | None:
        """Get a copy of the nonce entry, or None if not found."""
        with self._lock:
            entry = self._nonces.get(nonce)
            if entry is None:
                return None
            # Return a copy to prevent external mutation
            return NonceEntry(
                nonce=entry.nonce,
                created_at=entry.created_at,
                burned=entry.burned,
                burned_at=entry.burned_at,
                envelope_id=entry.envelope_id,
                source=entry.source,
            )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the entire registry to a dict."""
        with self._lock:
            return {
                "max_age_seconds": self._max_age_seconds,
                "nonces": {k: v.to_dict() for k, v in self._nonces.items()},
            }

    # ── Internal methods (must be called with self._lock held) ──

    def _prune_expired_locked(self) -> int:
        """Remove expired nonces. Caller must hold self._lock."""
        expired = [k for k, v in self._nonces.items() if v.is_expired(self._max_age_seconds)]
        for k in expired:
            del self._nonces[k]
        return len(expired)

    def _persist_locked(self) -> None:
        """Write registry to disk. Caller must hold self._lock."""
        if self._registry_path is None:
            return
        try:
            self._registry_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "max_age_seconds": self._max_age_seconds,
                "nonces": {k: v.to_dict() for k, v in self._nonces.items()},
            }
            # Atomic write: write to temp, then rename
            tmp_path = self._registry_path.with_suffix(".tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            tmp_path.replace(self._registry_path)
        except OSError:
            # Persist is best-effort; log failures upstream if needed
            pass

    def _load(self) -> None:
        """Load registry from disk if available."""
        if self._registry_path is None or not self._registry_path.exists():
            return
        try:
            with open(self._registry_path, encoding="utf-8") as f:
                data = json.load(f)
            nonces_data = data.get("nonces", {})
            for key, val in nonces_data.items():
                self._nonces[key] = NonceEntry.from_dict(val)
        except (OSError, json.JSONDecodeError, KeyError, TypeError):
            # Corrupted registry file — start fresh
            self._nonces = {}

```


**Tool Call: Read file `roots/GRID/boundaries/transition_gate/gate_keeper.py`**
Status: Completed

```roots/GRID/boundaries/transition_gate/gate_keeper.py
SUCCESS: File outline retrieved. This file is too large to read all at once, so the outline below shows the file's structure with line numbers.

IMPORTANT: Do NOT retry this call without line numbers - you will get the same outline.
Instead, use the line numbers below to read specific sections by calling this tool again with start_line and end_line parameters.

# File outline for /home/caraxes/roots/GRID/boundaries/transition_gate/gate_keeper.py

class VerificationStatus [L46-51]
class RejectionReason [L54-66]
class StepResult [L70-80]
 def to_dict [L79-80]
class VerificationResult [L84-125]
 def __post_init__ [L100-102]
 def passed [L105-106]
 def rejected [L109-110]
 def to_dict [L112-122]
 def to_json [L124-125]
class GateKeeper [L128-724]
 def __init__ [L150-181]
 def stats [L184-192]
 def verify [L194-348]
 def verify_from_file [L350-411]
 def _step_envelope_exists [L415-444]
 def _step_payload_integrity [L446-476]
 def _step_fingerprint_match [L478-506]
 def _step_nonce_valid [L508-529]
 def _step_timestamp_fresh [L531-551]
 def _step_tests_verified [L553-578]
 def _step_scope_present [L580-609]
 def _step_deploy_within_scope [L611-632]
 def _step_audit_log [L634-662]
 def _finalize [L666-687]
 def _update_stats [L689-697]
 def _audit_log_entry [L699-724]
def verify_envelope [L727-777]

Showing symbols 1-28 (total symbols: 28)


NEXT STEPS: To read a specific symbol's implementation, call read_file with the same path plus start_line and end_line from the outline above.
For example, to read a function shown as [L100-150], use start_line: 100 and end_line: 150.
```


**Tool Call: Read file `roots/GRID/boundaries/transition_gate/fingerprint.py`**
Status: Completed

```roots/GRID/boundaries/transition_gate/fingerprint.py
"""
Cryptographic fingerprint utilities for the Transition Gate.

Provides three fingerprint primitives:
- user_fingerprint: HMAC-SHA256 over a shared secret + machine identity
- machine_fingerprint: SHA-256 over stable machine attributes
- payload_hash: SHA-256 over the serialized artifact payload

All functions are pure and deterministic given the same inputs.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import platform
from typing import Any


def compute_user_fingerprint(
    user_secret: str,
    *,
    machine_id: str | None = None,
    extra_context: str | None = None,
) -> str:
    """
    Compute HMAC-SHA256 user fingerprint.

    Binds the user's secret to the machine identity so the same secret
    on a different machine produces a different fingerprint.

    Args:
        user_secret: Shared secret known to both seal and verify sides.
        machine_id: Optional explicit machine identifier. If None, uses
                     compute_machine_fingerprint() output.
        extra_context: Optional additional context string to mix in
                       (e.g. session ID, partition label).

    Returns:
        Hex-encoded HMAC-SHA256 digest.
    """
    if not user_secret:
        raise ValueError("user_secret must not be empty")

    if machine_id is None:
        machine_id = compute_machine_fingerprint()

    message = f"transition_gate:user:{machine_id}"
    if extra_context:
        message = f"{message}:{extra_context}"

    return hmac.new(
        key=user_secret.encode("utf-8"),
        msg=message.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()


def compute_machine_fingerprint(
    *,
    node_name: str | None = None,
    platform_system: str | None = None,
    platform_machine: str | None = None,
    username: str | None = None,
) -> str:
    """
    Compute SHA-256 machine fingerprint from stable OS attributes.

    Uses platform node name, OS name, architecture, and current username
    to produce a stable-per-machine identifier. This is NOT a secret —
    it's a binding factor, not an authentication credential.

    Args:
        node_name: Override for platform.node().
        platform_system: Override for platform.system().
        platform_machine: Override for platform.machine().
        username: Override for os.getlogin().

    Returns:
        Hex-encoded SHA-256 digest.
    """
    _node = node_name or platform.node()
    _system = platform_system or platform.system()
    _machine = platform_machine or platform.machine()

    try:
        _user = username or os.getlogin()
    except OSError:
        # Fallback when running in a non-interactive context (e.g. service, CI)
        _user = username or os.environ.get("USERNAME", os.environ.get("USER", "unknown"))

    canonical = f"transition_gate:machine:{_node}:{_system}:{_machine}:{_user}"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_payload_hash(payload: Any) -> str:
    """
    Compute SHA-256 hash of the payload.

    The payload is serialized to canonical JSON (sorted keys, no extra
    whitespace) before hashing so the digest is reproducible regardless
    of dict insertion order.

    Args:
        payload: Any JSON-serializable object (dict, list, str, etc.).

    Returns:
        Hex-encoded SHA-256 digest.

    Raises:
        TypeError: If payload is not JSON-serializable.
    """
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def fingerprints_match(
    fingerprint_a: str,
    fingerprint_b: str,
) -> bool:
    """
    Timing-safe comparison of two fingerprint hex strings.

    Uses hmac.compare_digest to prevent timing side-channel attacks.

    Args:
        fingerprint_a: First fingerprint hex string.
        fingerprint_b: Second fingerprint hex string.

    Returns:
        True if fingerprints are identical.
    """
    return hmac.compare_digest(fingerprint_a, fingerprint_b)

```


**Tool Call: Read file `roots/GRID/boundaries/transition_gate/credential.py`**
Status: Completed

```roots/GRID/boundaries/transition_gate/credential.py
"""
Credential retrieval for the Transition Gate shared secret.

Uses the Windows Credential Manager via ctypes to read Generic credentials
stored under the target name 'TransitionGate'. This avoids any dependency
on the `keyring` library.

The secret is stored as a Generic credential (CRED_TYPE_GENERIC = 1) with
CRED_PERSIST_LOCAL_MACHINE persistence. It must be written once via:

    python -c "
    from boundaries.transition_gate.credential import store_secret
    store_secret('your-hex-secret-here')
    "

Or via the cmdkey-compatible store_secret() function in this module.

Security:
    - The secret is held in memory only for the duration of the calling
      function. Callers should avoid persisting the return value.
    - Never log, serialize, or embed the secret in any output.
    - Per NR-S02 / NR-R06: transient use only.
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import os
import platform

# ── Windows API constants ──

CRED_TYPE_GENERIC: int = 1
CRED_TYPE_DOMAIN_PASSWORD: int = 2
CRED_PERSIST_LOCAL_MACHINE: int = 2

DEFAULT_TARGET_NAME: str = "TransitionGate"
DEFAULT_USERNAME: str = os.environ.get("USERNAME", os.environ.get("USER", "USER"))


class _CREDENTIAL(ctypes.Structure):
    """Win32 CREDENTIAL structure for CredReadW / CredWriteW."""

    _fields_ = [
        ("Flags", ctypes.wintypes.DWORD),
        ("Type", ctypes.wintypes.DWORD),
        ("TargetName", ctypes.wintypes.LPWSTR),
        ("Comment", ctypes.wintypes.LPWSTR),
        ("LastWritten", ctypes.wintypes.FILETIME),
        ("CredentialBlobSize", ctypes.wintypes.DWORD),
        ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
        ("Persist", ctypes.wintypes.DWORD),
        ("AttributeCount", ctypes.wintypes.DWORD),
        ("Attributes", ctypes.c_void_p),
        ("TargetAlias", ctypes.wintypes.LPWSTR),
        ("UserName", ctypes.wintypes.LPWSTR),
    ]


class _CREDENTIAL_WRITE(ctypes.Structure):
    """Win32 CREDENTIAL structure with c_void_p blob for CredWriteW."""

    _fields_ = [
        ("Flags", ctypes.wintypes.DWORD),
        ("Type", ctypes.wintypes.DWORD),
        ("TargetName", ctypes.wintypes.LPWSTR),
        ("Comment", ctypes.wintypes.LPWSTR),
        ("LastWritten", ctypes.wintypes.FILETIME),
        ("CredentialBlobSize", ctypes.wintypes.DWORD),
        ("CredentialBlob", ctypes.c_void_p),
        ("Persist", ctypes.wintypes.DWORD),
        ("AttributeCount", ctypes.wintypes.DWORD),
        ("Attributes", ctypes.c_void_p),
        ("TargetAlias", ctypes.wintypes.LPWSTR),
        ("UserName", ctypes.wintypes.LPWSTR),
    ]


_PCREDENTIAL = ctypes.POINTER(_CREDENTIAL)


def _is_windows() -> bool:
    """Check if we're running on Windows."""
    return platform.system() == "Windows"


def _get_advapi32() -> ctypes.WinDLL:
    """Get the advapi32 DLL handle with correct function signatures."""
    if not _is_windows():
        raise OSError("Credential Manager is only available on Windows")

    advapi32 = ctypes.windll.advapi32  # type: ignore[attr-defined]

    advapi32.CredReadW.restype = ctypes.wintypes.BOOL
    advapi32.CredReadW.argtypes = [
        ctypes.wintypes.LPCWSTR,
        ctypes.wintypes.DWORD,
        ctypes.wintypes.DWORD,
        ctypes.POINTER(_PCREDENTIAL),
    ]

    advapi32.CredWriteW.restype = ctypes.wintypes.BOOL
    advapi32.CredWriteW.argtypes = [
        ctypes.POINTER(_CREDENTIAL_WRITE),
        ctypes.wintypes.DWORD,
    ]

    advapi32.CredFree.restype = None
    advapi32.CredFree.argtypes = [ctypes.c_void_p]

    advapi32.CredDeleteW.restype = ctypes.wintypes.BOOL
    advapi32.CredDeleteW.argtypes = [
        ctypes.wintypes.LPCWSTR,
        ctypes.wintypes.DWORD,
        ctypes.wintypes.DWORD,
    ]

    return advapi32


def get_secret(
    target_name: str = DEFAULT_TARGET_NAME,
) -> str | None:
    """
    Retrieve the shared secret from Windows Credential Manager.

    Reads a Generic credential stored under the given target name.
    Returns the secret as a string, or None if the credential is not found
    or the blob is empty.

    Args:
        target_name: The credential target name. Default: 'TransitionGate'.

    Returns:
        The secret string, or None if not found / empty.

    Raises:
        OSError: If not running on Windows.
    """
    advapi32 = _get_advapi32()
    cred_ptr = _PCREDENTIAL()

    # Try Generic first (our preferred storage type)
    found = advapi32.CredReadW(target_name, CRED_TYPE_GENERIC, 0, ctypes.byref(cred_ptr))

    if not found:
        # Fall back to Domain Password (legacy cmdkey /add storage)
        found = advapi32.CredReadW(target_name, CRED_TYPE_DOMAIN_PASSWORD, 0, ctypes.byref(cred_ptr))

    if not found:
        return None

    try:
        blob_size = cred_ptr.contents.CredentialBlobSize
        if blob_size == 0:
            return None

        blob = bytes(cred_ptr.contents.CredentialBlob[i] for i in range(blob_size))
        return blob.decode("utf-16-le")
    finally:
        advapi32.CredFree(cred_ptr)


def store_secret(
    secret: str,
    target_name: str = DEFAULT_TARGET_NAME,
    username: str = DEFAULT_USERNAME,
    comment: str = "Transition Gate shared HMAC secret",
) -> bool:
    """
    Store the shared secret in Windows Credential Manager as a Generic credential.

    This writes the secret so that get_secret() can retrieve it. The credential
    persists across reboots (CRED_PERSIST_LOCAL_MACHINE).

    Args:
        secret: The secret string to store.
        target_name: The credential target name. Default: 'TransitionGate'.
        username: The username to associate. Default: current user.
        comment: Human-readable comment.

    Returns:
        True if the credential was stored successfully.

    Raises:
        OSError: If not running on Windows or the write fails.
        ValueError: If secret is empty.
    """
    if not secret:
        raise ValueError("secret must not be empty")

    advapi32 = _get_advapi32()

    secret_bytes = secret.encode("utf-16-le")
    blob_buffer = ctypes.create_string_buffer(secret_bytes, len(secret_bytes))

    cred = _CREDENTIAL_WRITE()
    cred.Type = CRED_TYPE_GENERIC
    cred.TargetName = target_name
    cred.UserName = username
    cred.CredentialBlobSize = len(secret_bytes)
    cred.CredentialBlob = ctypes.cast(blob_buffer, ctypes.c_void_p)
    cred.Persist = CRED_PERSIST_LOCAL_MACHINE
    cred.Comment = comment

    ok = advapi32.CredWriteW(ctypes.byref(cred), 0)
    if not ok:
        error_code = ctypes.get_last_error()
        raise OSError(
            f"CredWriteW failed with error code {error_code}. "
            f"Run as the target user ({username}) with sufficient privileges."
        )
    return True


def delete_secret(
    target_name: str = DEFAULT_TARGET_NAME,
) -> bool:
    """
    Delete the credential from Windows Credential Manager.

    Use for emergency revocation per secret_rotation_sop.emergency_revocation.

    Args:
        target_name: The credential target name. Default: 'TransitionGate'.

    Returns:
        True if the credential was deleted, False if it didn't exist.

    Raises:
        OSError: If not running on Windows.
    """
    advapi32 = _get_advapi32()

    # Try Generic first
    ok = advapi32.CredDeleteW(target_name, CRED_TYPE_GENERIC, 0)
    if ok:
        return True

    # Try Domain Password (legacy)
    ok = advapi32.CredDeleteW(target_name, CRED_TYPE_DOMAIN_PASSWORD, 0)
    return bool(ok)


def secret_exists(
    target_name: str = DEFAULT_TARGET_NAME,
) -> bool:
    """
    Check whether the credential exists without retrieving the secret.

    Args:
        target_name: The credential target name. Default: 'TransitionGate'.

    Returns:
        True if a credential with the target name exists.
    """
    secret = get_secret(target_name)
    return secret is not None and len(secret) > 0


# ── CLI entry point ──

if __name__ == "__main__":
    import sys

    usage = (
        "Usage:\n"
        "  python -m boundaries.transition_gate.credential check\n"
        "  python -m boundaries.transition_gate.credential store <secret>\n"
        "  python -m boundaries.transition_gate.credential delete\n"
        "  python -m boundaries.transition_gate.credential get\n"
    )

    if len(sys.argv) < 2:
        print(usage)
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "check":
        exists = secret_exists()
        print(f"TransitionGate credential: {'EXISTS' if exists else 'NOT FOUND'}")
        sys.exit(0 if exists else 1)

    elif command == "store":
        if len(sys.argv) < 3:
            print("Error: secret argument required")
            print(usage)
            sys.exit(1)
        store_secret(sys.argv[2])
        print("Credential stored successfully.")

    elif command == "delete":
        deleted = delete_secret()
        if deleted:
            print("Credential deleted.")
        else:
            print("Credential not found (nothing to delete).")

    elif command == "get":
        val = get_secret()
        if val:
            # Only show first/last 4 chars for safety
            masked = val[:4] + "..." + val[-4:] if len(val) > 12 else "****"
            print(f"Retrieved: {masked} ({len(val)} chars)")
        else:
            print("NOT FOUND")
            sys.exit(1)

    else:
        print(f"Unknown command: {command}")
        print(usage)
        sys.exit(1)

```


**Tool Call: Read file `roots/GRID/boundaries/boundary.py`**
Status: Completed

```roots/GRID/boundaries/boundary.py
"""
Boundary engine: enforce boundaries, consent, and guardrails.
Integrates with refusal rights (right to say no) and WebSocket logging.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from boundaries.logger_ws import get_logger
from boundaries.refusal import RefusalRights, check_refusal


@dataclass
class Boundary:
    id: str
    name: str
    type: str
    enforcement: str  # hard, soft, audit
    rule: dict[str, Any] | None = None
    refusable: bool = True

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Boundary:
        return cls(
            id=d["id"],
            name=d.get("name", d["id"]),
            type=d["type"],
            enforcement=d.get("enforcement", "hard"),
            rule=d.get("rule"),
            refusable=d.get("refusable", True),
        )


@dataclass
class Consent:
    id: str
    name: str
    scope: str
    required: bool = False
    revocable_at_any_time: bool = True
    default_state: str = "pending"

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Consent:
        return cls(
            id=d["id"],
            name=d.get("name", d["id"]),
            scope=d["scope"],
            required=d.get("required", False),
            revocable_at_any_time=d.get("revocableAtAnyTime", True),
            default_state=d.get("defaultState", "pending"),
        )


@dataclass
class Guardrail:
    id: str
    name: str
    kind: str
    action: str  # block, warn, redact, log, require_consent
    condition: str | None = None
    overridable_by_refusal: bool = False

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Guardrail:
        return cls(
            id=d["id"],
            name=d.get("name", d["id"]),
            kind=d["kind"],
            action=d["action"],
            condition=d.get("condition"),
            overridable_by_refusal=d.get("overridableByRefusal", False),
        )


class BoundaryEngine:
    """
    Enforces boundaries, consent, and guardrails. Respects right to refuse:
    - Before enforcing a boundary/guardrail, check for refusal; if user refused, honour it where refusable.
    - Consent can be denied/revoked at any time (service can be refused by withholding/revoking consent).
    """

    def __init__(self, config: dict[str, Any] | None = None):
        config = config or {}
        self.refusal_rights = RefusalRights.from_config(config)
        self.boundaries: list[Boundary] = [Boundary.from_dict(b) for b in config.get("boundaries") or []]
        self.consents: list[Consent] = [Consent.from_dict(c) for c in config.get("consents") or []]
        self.guardrails: list[Guardrail] = [Guardrail.from_dict(g) for g in config.get("guardrails") or []]
        self._consent_state: dict[str, str] = {}  # consent_id -> granted | denied | revoked
        for c in self.consents:
            self._consent_state.setdefault(c.id, c.default_state)
        self._logger = get_logger()

    def check_boundary(
        self,
        boundary_id: str,
        subject: str,
        *,
        scope: str | None = None,
        actor_id: str | None = None,
    ) -> bool:
        """
        Check if subject is within boundary. Returns True if allowed.

        Follows Prevention → Detection → Remediation order:
        1. Prevention: Refusal rights and boundary existence checks
        2. Detection: Rule evaluation against subject
        3. Remediation: Logging and violation handling
        """

        # PHASE 1: PREVENTION — Check refusal rights and boundary existence
        ref = check_refusal(trigger=boundary_id, scope=scope, rights=self.refusal_rights)
        if ref is not None:
            self._logger.log_boundary_check(
                boundary_id, allowed=True, scope=scope, payload={"reason": "refusal_honoured"}
            )
            return True

        boundary = next((b for b in self.boundaries if b.id == boundary_id), None)
        if not boundary:
            # Fail-closed: unknown boundary IDs are denied, not allowed.
            # This prevents typos or removed configs from silently granting access.
            self._logger.log_boundary_check(
                boundary_id,
                allowed=False,
                scope=scope,
                payload={"reason": "unknown_boundary_id"},
            )
            return False

        # PHASE 2: DETECTION — Evaluate boundary rules
        allowed = self._evaluate_rule(boundary.rule, subject)

        # PHASE 3: REMEDIATION — Log and handle violations
        self._logger.log_boundary_check(boundary_id, allowed, scope=scope, payload={"subject": subject})
        if not allowed and boundary.enforcement == "hard":
            self._logger.log_boundary_violation(
                boundary_id, scope=scope, actor_id=actor_id, payload={"subject": subject}
            )

        return allowed

    def _evaluate_rule(self, rule: dict[str, Any] | None, subject: str) -> bool:
        if not rule:
            return True
        if rule.get("deny") and subject in (rule["deny"] or []):
            return False
        if rule.get("allow"):
            return subject in (rule["allow"] or [])
        return True

    def get_consent_state(self, consent_id: str) -> str:
        return self._consent_state.get(consent_id, "pending")

    def grant_consent(self, consent_id: str, actor_id: str | None = None) -> None:
        self._consent_state[consent_id] = "granted"
        self._logger.log_consent_granted(consent_id, actor_id=actor_id)

    def deny_consent(self, consent_id: str, actor_id: str | None = None) -> None:
        self._consent_state[consent_id] = "denied"
        self._logger.log_consent_denied(consent_id, actor_id=actor_id)

    def revoke_consent(self, consent_id: str, actor_id: str | None = None) -> None:
        self._consent_state[consent_id] = "revoked"
        self._logger.log_consent_revoked(consent_id, actor_id=actor_id)

    def require_consent(self, consent_id: str, *, actor_id: str | None = None) -> bool:
        """
        Require consent for an action. Returns True if consent is granted.
        Denial or revocation = service can be refused (returns False).
        """
        state = self.get_consent_state(consent_id)
        if state == "granted":
            return True
        return False

    def check_guardrail(
        self,
        guardrail_id: str,
        context: dict[str, Any] | None = None,
        *,
        scope: str | None = None,
        actor_id: str | None = None,
    ) -> tuple[str, bool]:
        """
        Check guardrail. Returns (action, overridden).
        If overridable_by_refusal and user refused, return (action, True) to indicate override.
        """
        guardrail = next((g for g in self.guardrails if g.id == guardrail_id), None)
        if not guardrail:
            # Fail-closed: unknown guardrail IDs trigger block, not silent pass.
            self._logger.log_guardrail_triggered(
                guardrail_id,
                "block",
                scope=scope,
                payload={"reason": "unknown_guardrail_id"},
            )
            return ("block", False)
        ref = check_refusal(trigger=guardrail_id, scope=scope, rights=self.refusal_rights)
        if ref is not None and guardrail.overridable_by_refusal:
            self._logger.log_guardrail_overridden(guardrail_id, scope=scope, actor_id=actor_id, payload=context)
            return (guardrail.action, True)
        self._logger.log_guardrail_triggered(guardrail_id, guardrail.action, scope=scope, payload=context)
        return (guardrail.action, False)

```


**Tool Call: Read file `roots/GRID/boundaries/overwatch.py`**
Status: Completed

```roots/GRID/boundaries/overwatch.py
"""
Overwatch: continuous monitoring and alerting on boundary, consent, guardrail, and preparedness events.
Consumes persistent logs (or WebSocket stream), applies escalation rules, and can persist alerts.
"""

from __future__ import annotations

import json
import threading
import time
from collections import deque
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from boundaries.logger_ws import get_logger


class Overwatch:
    """
    Monitors boundary/consent/guardrail/preparedness events, triggers alerts when
    configured event types occur, and escalates when threshold counts are exceeded in a time window.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        config = config or {}
        ow = config.get("overwatch") or {}
        self.enabled = ow.get("enabled", True)
        self.log_dir = Path(ow.get("logDir", "logs/boundaries"))
        self.alert_on = set(
            ow.get("alertOn")
            or [
                "boundary_violation",
                "guardrail_triggered",
                "preparedness_gate",
                "service_refused",
            ]
        )
        esc = ow.get("escalation") or {}
        self.threshold_count = esc.get("thresholdCount", 3)
        self.window_minutes = esc.get("windowMinutes", 60)
        self.notify_channels = list(esc.get("notifyChannels") or [])
        self.persist_alerts = ow.get("persistAlerts", True)
        self._logger = get_logger()
        self._event_buffer: deque[tuple[float, dict[str, Any]]] = deque(maxlen=10_000)
        self._alert_handlers: list[Callable[[dict[str, Any]], None]] = []
        self._alerts_dir: Path | None = None
        if self.persist_alerts:
            self._alerts_dir = self.log_dir / "overwatch_alerts"
            self._alerts_dir.mkdir(parents=True, exist_ok=True)

    def register_handler(self, fn: Callable[[dict[str, Any]], None]) -> None:
        """Register a callback for every overwatch alert (e.g. send to Slack, PagerDuty)."""
        self._alert_handlers.append(fn)

    def ingest_event(self, event: dict[str, Any]) -> None:
        """Ingest one boundary log event; check alert and escalation rules."""
        if not self.enabled:
            return
        event_type = event.get("eventType")
        if event_type == "overwatch_alert":
            return  # avoid re-ingesting our own alerts
        if event_type not in self.alert_on:
            return
        now = time.time()
        self._event_buffer.append((now, event))
        self._maybe_alert(event)
        self._maybe_escalate(event_type, now)

    def _maybe_alert(self, event: dict[str, Any]) -> None:
        """Emit a single-event overwatch alert and persist if configured."""
        alert = {
            "eventId": event.get("eventId"),
            "timestamp": datetime.now(UTC).isoformat(),
            "eventType": "overwatch_alert",
            "severity": "warn",
            "payload": {
                "alertType": "single",
                "sourceEventType": event.get("eventType"),
                "scope": event.get("scope"),
                "actorId": event.get("actorId"),
                "payload": event.get("payload"),
            },
        }
        self._logger.log_overwatch_alert("single", scope=event.get("scope"), payload=alert.get("payload"))
        if self.persist_alerts and self._alerts_dir:
            try:
                path = self._alerts_dir / f"alert_{event.get('eventId', '')}.json"
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(alert, f, default=str, indent=2)
            except OSError:
                pass
        for h in self._alert_handlers:
            try:
                h(alert)
            except Exception:
                pass

    def _maybe_escalate(self, event_type: str, now: float) -> None:
        """If same event_type occurs >= threshold_count in window_minutes, emit escalation alert."""
        window_sec = self.window_minutes * 60
        cutoff = now - window_sec
        count = sum(1 for t, e in self._event_buffer if t >= cutoff and e.get("eventType") == event_type)
        if count < self.threshold_count:
            return
        alert = {
            "eventId": None,
            "timestamp": datetime.now(UTC).isoformat(),
            "eventType": "overwatch_alert",
            "severity": "error",
            "payload": {
                "alertType": "escalation",
                "sourceEventType": event_type,
                "count": count,
                "windowMinutes": self.window_minutes,
                "notifyChannels": self.notify_channels,
            },
        }
        self._logger.log_overwatch_alert("escalation", payload=alert.get("payload"))
        if self.persist_alerts and self._alerts_dir:
            try:
                ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
                path = self._alerts_dir / f"escalation_{event_type}_{ts}.json"
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(alert, f, default=str, indent=2)
            except OSError:
                pass
        for h in self._alert_handlers:
            try:
                h(alert)
            except Exception:
                pass

    def start_tailing_logs(self, poll_interval_sec: float = 5.0) -> None:
        """
        Start a background thread that tails the latest NDJSON log file in log_dir
        and ingests new events into overwatch. Call from main after logger is configured.
        """
        if not self.enabled:
            return

        def tail():
            last_size = 0
            current_path: Path | None = None
            while True:
                try:
                    today = datetime.now(UTC).strftime("%Y-%m-%d")
                    path = self.log_dir / f"boundary_events_{today}.ndjson"
                    if not path.exists():
                        time.sleep(poll_interval_sec)
                        continue
                    if path != current_path:
                        current_path = path
                        last_size = 0
                    with open(path, encoding="utf-8") as f:
                        f.seek(last_size)
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                event = json.loads(line)
                                self.ingest_event(event)
                            except json.JSONDecodeError:
                                pass
                        last_size = f.tell()
                except OSError:
                    pass
                time.sleep(poll_interval_sec)

        thread = threading.Thread(target=tail, daemon=True)
        thread.start()


def wrap_logger_with_overwatch(logger: Any, overwatch: Overwatch) -> None:
    """
    After BoundaryEventLogger emits an event, also feed it to overwatch.
    Call this once after creating both logger and overwatch; then use the logger as usual.
    """
    original_emit = logger._emit

    def emit(event: dict[str, Any]) -> None:
        original_emit(event)
        overwatch.ingest_event(event)

    logger._emit = emit

```


**Tool Call: Read file `roots/GRID/src/grid/resilience/accountability/contracts.py` (lines 1-76)**
Status: Completed

```roots/GRID/src/grid/resilience/accountability/contracts.py
"""Accountability contract schema for heavy enforcement.

Defines the contract schema for accountability enforcement, including:
- Endpoint contracts
- Data validation rules
- Performance SLAs
- Security requirements
- Compliance requirements
"""

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class ContractSeverity(StrEnum):
    """Severity levels for contract violations."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ViolationType(StrEnum):
    """Types of contract violations."""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    DATA_VALIDATION = "data_validation"
    RATE_LIMIT = "rate_limit"
    PERFORMANCE = "performance"
    COMPLIANCE = "compliance"
    SECURITY = "security"
    IP_WHITELIST = "ip_whitelist"
    MISSING_CONTRACT = "missing_contract"
    ENDPOINT_DISABLED = "endpoint_disabled"


@dataclass
class ContractViolation:
    """Represents a single contract violation."""

    type: ViolationType
    severity: ContractSeverity
    message: str
    field: str
    actual_value: Any = None
    expected_value: Any = None
    penalty_points: int = 10
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Alias for backward compatibility
    @property
    def violation_type(self) -> ViolationType:
        """Alias for type property."""
        return self.type

    def to_dict(self) -> dict[str, Any]:
        """Convert violation to dictionary."""
        return {
            "type": self.type.value,
            "violation_type": self.type.value,  # Alias
            "field": self.field,
            "message": self.message,
            "severity": self.severity.value,
            "actual_value": self.actual_value,
            "expected_value": self.expected_value,
            "penalty_points": self.penalty_points,
            "timestamp": self.timestamp.isoformat(),
        }

```


**Tool Call: Read file `roots/GRID/src/grid/resilience/accountability/contracts.py` (lines 122-254)**
Status: Completed

```roots/GRID/src/grid/resilience/accountability/contracts.py
class ContractManager:
    """Manager for loading and caching accountability contracts."""

    def __init__(self):
        self._contracts: dict[str, AccountabilityContract] = {}

    def register_contract(self, contract: "AccountabilityContract") -> None:
        """Register a contract."""
        self._contracts[contract.service_name] = contract

    def get_contract(self, service_name: str) -> Optional["AccountabilityContract"]:
        """Get a contract by service name."""
        return self._contracts.get(service_name)

    def get_all_contracts(self) -> dict[str, "AccountabilityContract"]:
        """Get all registered contracts."""
        return self._contracts.copy()

    def find_endpoint_contract(self, path: str, method: str) -> Optional["EndpointContract"]:
        """Find an endpoint contract across all registered contracts."""
        for contract in self._contracts.values():
            endpoint = contract.get_endpoint_contract(path, method)
            if endpoint:
                return endpoint
        return None


class DataValidationRule(BaseModel):
    """Data validation rule for request/response validation."""

    field: str = Field("", description="Field to validate (optional, derived from dict key)")
    type: str = Field("string", description="Expected type (string, number, boolean, object, array)")
    required: bool = Field(True, description="Whether the field is required")
    pattern: str | None = Field(None, description="Regex pattern for string validation")
    min_length: int | None = Field(None, description="Minimum length for strings/arrays")
    max_length: int | None = Field(None, description="Maximum length for strings/arrays")
    min_value: int | float | None = Field(None, description="Minimum value for numbers")
    max_value: int | float | None = Field(None, description="Maximum value for numbers")
    enum: list[Any] | None = Field(None, description="Allowed values")
    custom_validator: str | None = Field(
        None, description="Path to custom validation function (module.path:function_name)"
    )


class PerformanceSLA(BaseModel):
    """Performance SLA requirements for an endpoint."""

    max_latency_ms: int = Field(1000, description="Maximum allowed latency in milliseconds")
    max_error_rate: float = Field(0.01, description="Maximum allowed error rate (0-1)")
    min_throughput_rps: int = Field(10, description="Minimum required requests per second")
    timeout_ms: int = Field(30000, description="Request timeout in milliseconds")


class SecurityRequirement(BaseModel):
    """Security requirements for an endpoint."""

    authentication_required: bool = Field(True, description="Authentication required")
    required_roles: list[str] = Field(default_factory=list, description="Required roles for access")
    required_permissions: list[str] = Field(default_factory=list, description="Required permissions")
    ip_whitelist: list[str] | None = Field(None, description="Allowed IP addresses/CIDR ranges")
    rate_limit: int | None = Field(None, description="Max requests per minute per client")
    request_signing_required: bool = Field(False, description="Require request signing")
    response_encryption_required: bool = Field(False, description="Require response encryption")


class ComplianceRequirement(BaseModel):
    """Compliance requirements for an endpoint."""

    gdpr: bool = Field(False, description="GDPR compliance required")
    hipaa: bool = Field(False, description="HIPAA compliance required")
    pci_dss: bool = Field(False, description="PCI DSS compliance required")
    data_retention_days: int = Field(90, description="Required data retention period in days")
    audit_logging: bool = Field(True, description="Audit logging required")
    data_classification: str = Field(
        "public", description="Data classification level (public, internal, confidential, restricted)"
    )


class EndpointContract(BaseModel):
    """Contract defining requirements for a specific API endpoint."""

    path: str = Field(..., description="Endpoint path (can include wildcards)")
    methods: list[str] = Field(["GET"], description="HTTP methods this contract applies to")
    description: str = Field(..., description="Description of the endpoint's purpose")
    request_validation: dict[str, DataValidationRule] = Field(
        default_factory=dict, description="Request validation rules"
    )
    response_validation: dict[str, DataValidationRule] = Field(
        default_factory=dict, description="Response validation rules"
    )
    performance: PerformanceSLA = Field(default_factory=PerformanceSLA, description="Performance requirements")
    security: SecurityRequirement = Field(default_factory=SecurityRequirement, description="Security requirements")
    compliance: ComplianceRequirement = Field(
        default_factory=ComplianceRequirement, description="Compliance requirements"
    )
    enabled: bool = Field(True, description="Whether this contract is actively enforced")
    severity: ContractSeverity = Field(ContractSeverity.MEDIUM, description="Default severity for violations")
    penalty_points: int = Field(10, description="Penalty points for violations")
    auto_remediation: bool = Field(False, description="Enable automatic remediation")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="When this contract was created"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="When this contract was last updated"
    )

    @field_validator("methods")
    @classmethod
    def validate_http_method(cls, v: list[str]) -> list[str]:
        valid_methods = {
            "GET",
            "POST",
            "PUT",
            "DELETE",
            "PATCH",
            "HEAD",
            "OPTIONS",
            "WEBSOCKET",
            "WS",
        }
        validated = []
        for method in v:
            if method.upper() not in valid_methods:
                raise ValueError(f"Invalid HTTP method: {method}")
            validated.append(method.upper())
        return validated

    @model_validator(mode="before")
    @classmethod
    def update_timestamp(cls, values: dict[str, Any]) -> dict[str, Any]:
        values["updated_at"] = datetime.now(UTC)
        return values

```


**Tool Call: Read file `roots/GRID/src/grid/resilience/accountability/contracts.py` (lines 257-442)**
Status: Completed

```roots/GRID/src/grid/resilience/accountability/contracts.py
class ServiceLevelObjective(BaseModel):
    """Service Level Objective for accountability."""

    name: str = Field(..., description="Name of the SLO")
    description: str = Field(..., description="Description of the SLO")
    measurement: str = Field(..., description="What to measure (e.g., 'latency', 'error_rate')")
    threshold: float = Field(..., description="Threshold value")
    threshold_type: Literal["lt", "lte", "gt", "gte", "eq", "neq"] = Field(
        "lte", description="Comparison operator for threshold"
    )
    window: str = Field("1h", description="Time window for evaluation (e.g., '5m', '1h', '1d')")
    severity: ContractSeverity = Field(ContractSeverity.MEDIUM, description="Severity if SLO is violated")
    penalty_points: int = Field(5, description="Penalty points if SLO is violated")


class AccountabilityContract(BaseModel):
    """Complete accountability contract for a service."""

    service_name: str = Field(..., description="Name of the service")
    version: str = Field("1.0.0", description="Contract version")
    description: str = Field(..., description="Description of the service and contract")
    endpoints: list[EndpointContract] = Field(default_factory=list, description="List of endpoint contracts")
    slos: list[ServiceLevelObjective] = Field(default_factory=list, description="Service Level Objectives")
    default_security: SecurityRequirement = Field(
        default_factory=SecurityRequirement, description="Default security requirements"
    )
    default_compliance: ComplianceRequirement = Field(
        default_factory=ComplianceRequirement, description="Default compliance requirements"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="When this contract was created"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="When this contract was last updated"
    )

    def get_endpoint_contract(self, path: str, method: str) -> EndpointContract | None:
        """Find the most specific contract for the given path and method."""
        method = method.upper()

        # First try exact match
        for contract in self.endpoints:
            if contract.path == path and method in contract.methods:
                return contract

        # Then try wildcard match (e.g., /api/*)
        path_parts = path.strip("/").split("/")

        for contract in self.endpoints:
            if "*" in contract.path and method in contract.methods:
                contract_parts = contract.path.strip("/").split("/")
                if len(path_parts) != len(contract_parts):
                    continue

                match = True
                for p, cp in zip(path_parts, contract_parts, strict=False):
                    if cp == "*":
                        continue
                    if p != cp:
                        match = False
                        break

                if match:
                    return contract

        return None

    def validate_request(self, path: str, method: str, request_data: dict) -> list[dict]:
        """Validate a request against the contract."""
        contract = self.get_endpoint_contract(path, method)
        if not contract:
            return [{"error": "no_matching_contract", "message": f"No contract found for {method} {path}"}]

        return self._validate_data(contract.request_validation, request_data)

    def validate_response(self, path: str, method: str, response_data: dict) -> list[dict]:
        """Validate a response against the contract."""
        contract = self.get_endpoint_contract(path, method)
        if not contract:
            return []

        return self._validate_data(contract.response_validation, response_data)

    def _validate_data(self, rules: dict[str, DataValidationRule], data: dict) -> list[dict]:
        """Validate data against validation rules."""
        errors = []

        for field_name, rule in rules.items():
            if field_name not in data:
                if rule.required:
                    errors.append(
                        {
                            "field": field_name,
                            "error": "missing_required_field",
                            "message": f"Required field '{field_name}' is missing",
                        }
                    )
                continue

            value = data[field_name]

            # Type checking
            expected_type = rule.type.lower()
            type_ok = False

            if expected_type == "string":
                type_ok = isinstance(value, str)
            elif expected_type == "number":
                type_ok = isinstance(value, (int, float))
            elif expected_type == "boolean":
                type_ok = isinstance(value, bool)
            elif expected_type == "object":
                type_ok = isinstance(value, dict)
            elif expected_type == "array":
                type_ok = isinstance(value, list)

            if not type_ok:
                errors.append(
                    {
                        "field": field_name,
                        "error": "invalid_type",
                        "message": f"Field '{field_name}' must be of type {expected_type}, got {type(value).__name__}",
                    }
                )
                continue

            # Additional validations
            if expected_type == "string":
                if rule.min_length is not None and len(value) < rule.min_length:
                    errors.append(
                        {
                            "field": field_name,
                            "error": "min_length",
                            "message": f"Field '{field_name}' must be at least {rule.min_length} characters",
                        }
                    )

                if rule.max_length is not None and len(value) > rule.max_length:
                    errors.append(
                        {
                            "field": field_name,
                            "error": "max_length",
                            "message": f"Field '{field_name}' must be at most {rule.max_length} characters",
                        }
                    )

                if rule.pattern and not re.match(rule.pattern, value):
                    errors.append(
                        {
                            "field": field_name,
                            "error": "pattern_mismatch",
                            "message": f"Field '{field_name}' does not match required pattern",
                        }
                    )

            elif expected_type in ("int", "float", "number"):
                if rule.min_value is not None and value < rule.min_value:
                    errors.append(
                        {
                            "field": field_name,
                            "error": "min_value",
                            "message": f"Field '{field_name}' must be at least {rule.min_value}",
                        }
                    )

                if rule.max_value is not None and value > rule.max_value:
                    errors.append(
                        {
                            "field": field_name,
                            "error": "max_value",
                            "message": f"Field '{field_name}' must be at most {rule.max_value}",
                        }
                    )

            if rule.enum and value not in rule.enum:
                errors.append(
                    {
                        "field": field_name,
                        "error": "invalid_enum_value",
                        "message": f"Field '{field_name}' must be one of {rule.enum}",
                    }
                )

            # TODO: Add support for custom validators

        return errors

```


## Assistant

<thinking>
Now let me read the GateKeeper implementation, specifically the verify method and key steps.
</thinking>

Let me now read the GateKeeper's verify pipeline and a few more critical files.

**Tool Call: Read file `roots/GRID/boundaries/transition_gate/gate_keeper.py` (lines 1-100)**
Status: Completed

```roots/GRID/boundaries/transition_gate/gate_keeper.py
"""
GateKeeper: 9-step verification pipeline for sealed transition envelopes.

The GateKeeper is the receiving side's enforcement point. It validates every
aspect of a sealed envelope before allowing any actions on the payload.

Verification pipeline (9 steps):
1. envelope_exists    — Envelope is present and parseable
2. payload_integrity  — SHA-256 of payload matches envelope's payload_hash
3. fingerprint_match  — User fingerprint matches recomputed HMAC-SHA256
4. nonce_valid        — Nonce exists in registry, not burned, not expired
5. timestamp_fresh    — Envelope age < max_age_seconds
6. tests_verified     — Source reports tests_passed == True
7. scope_present      — Scope declaration is non-empty and well-formed
8. deploy_within_scope — Requested action is within declared permissions
9. audit_log          — All results appended to audit trail

Security posture:
- Fail-closed: any step failure rejects the entire envelope
- Timing-safe HMAC comparison (via hmac.compare_digest)
- Nonce burned on successful verification (replay prevention)
- Append-only NDJSON audit trail for forensic review
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from boundaries.transition_gate.envelope import (  # type: ignore[import-untyped]
    TransitionEnvelope,
)
from boundaries.transition_gate.fingerprint import (  # type: ignore[import-untyped]
    compute_payload_hash,
    compute_user_fingerprint,
    fingerprints_match,
)
from boundaries.transition_gate.nonce import NonceRegistry  # type: ignore[import-untyped]


class VerificationStatus(StrEnum):
    """Outcome of a verification step or overall result."""

    PASSED = "passed"
    REJECTED = "rejected"
    ERROR = "error"


class RejectionReason(StrEnum):
    """Machine-readable rejection reasons."""

    ENVELOPE_MISSING = "rejected:envelope_missing"
    ENVELOPE_PARSE_ERROR = "rejected:envelope_parse_error"
    PAYLOAD_INTEGRITY_FAILED = "rejected:payload_integrity_failed"
    FINGERPRINT_MISMATCH = "rejected:fingerprint_mismatch"
    NONCE_REPLAY_OR_EXPIRED = "rejected:nonce_replay_or_expired"
    ENVELOPE_EXPIRED = "rejected:envelope_expired"
    TESTS_NOT_PASSED = "rejected:tests_not_passed"
    SCOPE_MISSING = "rejected:scope_missing"
    ACTION_OUT_OF_SCOPE = "rejected:action_out_of_scope"
    INTERNAL_ERROR = "rejected:internal_error"


@dataclass
class StepResult:
    """Result of a single verification pipeline step."""

    step: int
    name: str
    status: str
    detail: str | None = None
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VerificationResult:
    """
    Complete result of the 9-step verification pipeline.

    Contains per-step results and the overall verdict.
    """

    envelope_id: str | None
    status: str
    reason: str | None = None
    steps: list[StepResult] = field(default_factory=list)
    timestamp: str = ""
    total_duration_ms: float = 0.0
    nonce_burned: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:

```


**Tool Call: Read file `roots/GRID/boundaries/transition_gate/gate_keeper.py` (lines 128-348)**
Status: Completed

```roots/GRID/boundaries/transition_gate/gate_keeper.py
class GateKeeper:
    """
    Verification engine for sealed transition envelopes.

    Implements the full 9-step verification pipeline with fail-closed
    semantics, nonce burning, and append-only audit logging.

    Args:
        user_secret: The shared secret for recomputing user fingerprints.
        nonce_registry: NonceRegistry instance for nonce validation/burning.
        audit_path: Path to the NDJSON audit log file. If None, audit
                    logging is disabled.
        max_age_seconds: Maximum envelope age before rejection. Defaults
                         to 600 (10 minutes).
        require_tests: Whether to require tests_passed == True. Default True.
        require_lint: Whether to require lint_passed == True. Default False.
        machine_fingerprint_overrides: Optional overrides for recomputing
            machine fingerprint (for cross-machine verification).
        extra_fingerprint_context: Optional extra context for user fingerprint
            recomputation.
    """

    def __init__(
        self,
        *,
        user_secret: str,
        nonce_registry: NonceRegistry,
        audit_path: Path | str | None = None,
        max_age_seconds: float = 600.0,
        require_tests: bool = True,
        require_lint: bool = False,
        machine_fingerprint_overrides: dict[str, str] | None = None,
        extra_fingerprint_context: str | None = None,
    ):
        if not user_secret:
            raise ValueError("user_secret must not be empty")

        self._user_secret = user_secret
        self._nonce_registry = nonce_registry
        self._audit_path = Path(audit_path) if audit_path else None
        self._max_age_seconds = max_age_seconds
        self._require_tests = require_tests
        self._require_lint = require_lint
        self._machine_fp_overrides = machine_fingerprint_overrides or {}
        self._extra_fp_context = extra_fingerprint_context

        if self._audit_path:
            self._audit_path.parent.mkdir(parents=True, exist_ok=True)

        # Counters for monitoring / KPIs
        self._total_verifications: int = 0
        self._total_passed: int = 0
        self._total_rejected: int = 0
        self._rejection_counts: dict[str, int] = {}

    @property
    def stats(self) -> dict[str, Any]:
        """Return current verification statistics."""
        return {
            "total_verifications": self._total_verifications,
            "total_passed": self._total_passed,
            "total_rejected": self._total_rejected,
            "pass_rate": (self._total_passed / self._total_verifications if self._total_verifications > 0 else 0.0),
            "rejection_counts": dict(self._rejection_counts),
        }

    def verify(
        self,
        envelope: TransitionEnvelope,
        *,
        requested_action: str | None = None,
        dry_run: bool = False,
    ) -> VerificationResult:
        """
        Run the full 9-step verification pipeline on a sealed envelope.

        If dry_run is True, the nonce is validated but not burned, and no
        audit entry is written. Use dry_run for pre-flight checks.

        Args:
            envelope: The sealed TransitionEnvelope to verify.
            requested_action: The action the receiver wants to perform.
                              Must be within the envelope's scope permissions.
                              If None, defaults to "read_only".
            dry_run: If True, don't burn nonce or write audit log.

        Returns:
            VerificationResult with per-step details and overall verdict.
        """
        pipeline_start = time.monotonic()
        steps: list[StepResult] = []
        action = requested_action or "read_only"

        result = VerificationResult(
            envelope_id=envelope.envelope_id,
            status=VerificationStatus.PASSED,
        )

        # ── Step 1: envelope_exists ──
        step_result = self._step_envelope_exists(envelope)
        steps.append(step_result)
        if step_result.status != VerificationStatus.PASSED:
            return self._finalize(
                result,
                steps,
                pipeline_start,
                status=VerificationStatus.REJECTED,
                reason=RejectionReason.ENVELOPE_PARSE_ERROR,
                dry_run=dry_run,
            )

        # ── Step 2: payload_integrity ──
        step_result = self._step_payload_integrity(envelope)
        steps.append(step_result)
        if step_result.status != VerificationStatus.PASSED:
            return self._finalize(
                result,
                steps,
                pipeline_start,
                status=VerificationStatus.REJECTED,
                reason=RejectionReason.PAYLOAD_INTEGRITY_FAILED,
                dry_run=dry_run,
            )

        # ── Step 3: fingerprint_match ──
        step_result = self._step_fingerprint_match(envelope)
        steps.append(step_result)
        if step_result.status != VerificationStatus.PASSED:
            return self._finalize(
                result,
                steps,
                pipeline_start,
                status=VerificationStatus.REJECTED,
                reason=RejectionReason.FINGERPRINT_MISMATCH,
                dry_run=dry_run,
            )

        # ── Step 4: nonce_valid ──
        step_result = self._step_nonce_valid(envelope, dry_run=dry_run)
        steps.append(step_result)
        if step_result.status != VerificationStatus.PASSED:
            return self._finalize(
                result,
                steps,
                pipeline_start,
                status=VerificationStatus.REJECTED,
                reason=RejectionReason.NONCE_REPLAY_OR_EXPIRED,
                dry_run=dry_run,
            )

        # ── Step 5: timestamp_fresh ──
        step_result = self._step_timestamp_fresh(envelope)
        steps.append(step_result)
        if step_result.status != VerificationStatus.PASSED:
            return self._finalize(
                result,
                steps,
                pipeline_start,
                status=VerificationStatus.REJECTED,
                reason=RejectionReason.ENVELOPE_EXPIRED,
                dry_run=dry_run,
            )

        # ── Step 6: tests_verified ──
        step_result = self._step_tests_verified(envelope)
        steps.append(step_result)
        if step_result.status != VerificationStatus.PASSED:
            return self._finalize(
                result,
                steps,
                pipeline_start,
                status=VerificationStatus.REJECTED,
                reason=RejectionReason.TESTS_NOT_PASSED,
                dry_run=dry_run,
            )

        # ── Step 7: scope_present ──
        step_result = self._step_scope_present(envelope)
        steps.append(step_result)
        if step_result.status != VerificationStatus.PASSED:
            return self._finalize(
                result,
                steps,
                pipeline_start,
                status=VerificationStatus.REJECTED,
                reason=RejectionReason.SCOPE_MISSING,
                dry_run=dry_run,
            )

        # ── Step 8: deploy_within_scope ──
        step_result = self._step_deploy_within_scope(envelope, action)
        steps.append(step_result)
        if step_result.status != VerificationStatus.PASSED:
            return self._finalize(
                result,
                steps,
                pipeline_start,
                status=VerificationStatus.REJECTED,
                reason=RejectionReason.ACTION_OUT_OF_SCOPE,
                dry_run=dry_run,
            )

        # ── Step 9: audit_log ──
        # On full pass, burn the nonce (unless dry_run)
        nonce_burned = False
        if not dry_run:
            burn_ok, burn_reason = self._nonce_registry.burn(envelope.nonce)
            nonce_burned = burn_ok

        step_result = self._step_audit_log(envelope, passed=True, dry_run=dry_run)
        steps.append(step_result)

        result.nonce_burned = nonce_burned
        return self._finalize(
            result,
            steps,
            pipeline_start,
            status=VerificationStatus.PASSED,
            reason=None,
            dry_run=dry_run,
        )

```


**Tool Call: Read file `roots/GRID/boundaries/transition_gate/gate_keeper.py` (lines 415-550)**
Status: Completed

```roots/GRID/boundaries/transition_gate/gate_keeper.py
    def _step_envelope_exists(self, envelope: TransitionEnvelope) -> StepResult:
        """Step 1: Verify envelope is present and has required fields."""
        start = time.monotonic()
        required_fields = [
            "envelope_id",
            "payload",
            "payload_hash",
            "nonce",
            "timestamp",
            "user_fingerprint",
            "machine_fingerprint",
        ]
        missing = [f for f in required_fields if not getattr(envelope, f, None)]
        duration = (time.monotonic() - start) * 1000

        if missing:
            return StepResult(
                step=1,
                name="envelope_exists",
                status=VerificationStatus.REJECTED,
                detail=f"Missing required fields: {missing}",
                duration_ms=duration,
            )
        return StepResult(
            step=1,
            name="envelope_exists",
            status=VerificationStatus.PASSED,
            detail="All required fields present",
            duration_ms=duration,
        )

    def _step_payload_integrity(self, envelope: TransitionEnvelope) -> StepResult:
        """Step 2: Verify payload hash matches recomputed SHA-256."""
        start = time.monotonic()
        try:
            recomputed = compute_payload_hash(envelope.payload)
        except (TypeError, ValueError) as exc:
            duration = (time.monotonic() - start) * 1000
            return StepResult(
                step=2,
                name="payload_integrity",
                status=VerificationStatus.REJECTED,
                detail=f"Cannot hash payload: {exc}",
                duration_ms=duration,
            )

        duration = (time.monotonic() - start) * 1000
        if not fingerprints_match(recomputed, envelope.payload_hash):
            return StepResult(
                step=2,
                name="payload_integrity",
                status=VerificationStatus.REJECTED,
                detail="Payload hash mismatch (data may have been tampered with)",
                duration_ms=duration,
            )
        return StepResult(
            step=2,
            name="payload_integrity",
            status=VerificationStatus.PASSED,
            detail="Payload hash verified",
            duration_ms=duration,
        )

    def _step_fingerprint_match(self, envelope: TransitionEnvelope) -> StepResult:
        """Step 3: Verify user fingerprint matches recomputed HMAC-SHA256."""
        start = time.monotonic()

        # Recompute user fingerprint using the shared secret and the
        # machine fingerprint FROM THE ENVELOPE (since we're verifying
        # that the sealer's identity matches, not our own machine).
        recomputed = compute_user_fingerprint(
            self._user_secret,
            machine_id=envelope.machine_fingerprint,
            extra_context=self._extra_fp_context,
        )

        duration = (time.monotonic() - start) * 1000
        if not fingerprints_match(recomputed, envelope.user_fingerprint):
            return StepResult(
                step=3,
                name="fingerprint_match",
                status=VerificationStatus.REJECTED,
                detail="User fingerprint mismatch (secret or machine identity differs)",
                duration_ms=duration,
            )
        return StepResult(
            step=3,
            name="fingerprint_match",
            status=VerificationStatus.PASSED,
            detail="User fingerprint verified (timing-safe)",
            duration_ms=duration,
        )

    def _step_nonce_valid(self, envelope: TransitionEnvelope, *, dry_run: bool = False) -> StepResult:
        """Step 4: Verify nonce is valid (exists, not burned, not expired)."""
        start = time.monotonic()

        valid, reason = self._nonce_registry.validate(envelope.nonce)
        duration = (time.monotonic() - start) * 1000

        if not valid:
            return StepResult(
                step=4,
                name="nonce_valid",
                status=VerificationStatus.REJECTED,
                detail=f"Nonce rejected: {reason}",
                duration_ms=duration,
            )
        return StepResult(
            step=4,
            name="nonce_valid",
            status=VerificationStatus.PASSED,
            detail="Nonce valid and unburned" + (" (dry-run, not burning)" if dry_run else ""),
            duration_ms=duration,
        )

    def _step_timestamp_fresh(self, envelope: TransitionEnvelope) -> StepResult:
        """Step 5: Verify envelope timestamp is within max_age_seconds."""
        start = time.monotonic()
        age = envelope.age_seconds
        duration = (time.monotonic() - start) * 1000

        if age > self._max_age_seconds:
            return StepResult(
                step=5,
                name="timestamp_fresh",
                status=VerificationStatus.REJECTED,
                detail=f"Envelope age {age:.1f}s exceeds max {self._max_age_seconds:.1f}s",
                duration_ms=duration,
            )
        return StepResult(
            step=5,
            name="timestamp_fresh",
            status=VerificationStatus.PASSED,
            detail=f"Envelope age {age:.1f}s within limit {self._max_age_seconds:.1f}s",
            duration_ms=duration,

```


**Tool Call: Read file `roots/GRID/boundaries/transition_gate/gate_keeper.py` (lines 611-777)**
Status: Completed

```roots/GRID/boundaries/transition_gate/gate_keeper.py
    def _step_deploy_within_scope(self, envelope: TransitionEnvelope, action: str) -> StepResult:
        """Step 8: Verify the requested action is within the envelope's scope."""
        start = time.monotonic()

        allowed_permissions = set(envelope.scope.permissions)
        duration = (time.monotonic() - start) * 1000

        if action not in allowed_permissions:
            return StepResult(
                step=8,
                name="deploy_within_scope",
                status=VerificationStatus.REJECTED,
                detail=f"Action '{action}' not in permitted scope {sorted(allowed_permissions)}",
                duration_ms=duration,
            )
        return StepResult(
            step=8,
            name="deploy_within_scope",
            status=VerificationStatus.PASSED,
            detail=f"Action '{action}' is within scope",
            duration_ms=duration,
        )

    def _step_audit_log(
        self,
        envelope: TransitionEnvelope,
        *,
        passed: bool,
        dry_run: bool = False,
    ) -> StepResult:
        """Step 9: Write audit log entry (unless dry_run)."""
        start = time.monotonic()

        if dry_run:
            duration = (time.monotonic() - start) * 1000
            return StepResult(
                step=9,
                name="audit_log",
                status=VerificationStatus.PASSED,
                detail="Dry-run: audit log skipped",
                duration_ms=duration,
            )

        # Audit entry is written in _finalize via _audit_log_entry
        duration = (time.monotonic() - start) * 1000
        return StepResult(
            step=9,
            name="audit_log",
            status=VerificationStatus.PASSED,
            detail="Audit log entry queued",
            duration_ms=duration,
        )

    # ── Internal helpers ──

    def _finalize(
        self,
        result: VerificationResult,
        steps: list[StepResult],
        pipeline_start: float,
        *,
        status: str,
        reason: str | None,
        dry_run: bool,
    ) -> VerificationResult:
        """Finalize the verification result with timing and audit."""
        result.steps = steps
        result.status = status
        result.reason = reason
        result.total_duration_ms = (time.monotonic() - pipeline_start) * 1000

        self._update_stats(result)

        if not dry_run:
            self._audit_log_entry(result)

        return result

    def _update_stats(self, result: VerificationResult) -> None:
        """Update internal counters."""
        self._total_verifications += 1
        if result.passed:
            self._total_passed += 1
        else:
            self._total_rejected += 1
            if result.reason:
                self._rejection_counts[result.reason] = self._rejection_counts.get(result.reason, 0) + 1

    def _audit_log_entry(self, result: VerificationResult) -> None:
        """Append a verification result to the NDJSON audit trail."""
        if self._audit_path is None:
            return

        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event_type": "gate_verification",
            "envelope_id": result.envelope_id,
            "status": result.status,
            "reason": result.reason,
            "nonce_burned": result.nonce_burned,
            "total_duration_ms": result.total_duration_ms,
            "step_count": len(result.steps),
            "failed_step": next(
                (s.name for s in result.steps if s.status != VerificationStatus.PASSED),
                None,
            ),
        }

        try:
            with open(self._audit_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, default=str) + "\n")
        except OSError:
            # Audit write is best-effort; don't crash verification
            pass


def verify_envelope(
    envelope: TransitionEnvelope,
    *,
    user_secret: str,
    nonce_registry: NonceRegistry,
    audit_path: Path | str | None = None,
    max_age_seconds: float = 600.0,
    requested_action: str | None = None,
    require_tests: bool = True,
    require_lint: bool = False,
    dry_run: bool = False,
    machine_fingerprint_overrides: dict[str, str] | None = None,
    extra_fingerprint_context: str | None = None,
) -> VerificationResult:
    """
    Convenience function: create a GateKeeper and verify an envelope in one call.

    This is the primary entry point for the verify side of the pipeline.

    Args:
        envelope: The sealed TransitionEnvelope to verify.
        user_secret: Shared secret for fingerprint recomputation.
        nonce_registry: NonceRegistry for nonce validation/burning.
        audit_path: Path to the NDJSON audit log file.
        max_age_seconds: Maximum envelope age before rejection.
        requested_action: The action the receiver wants to perform.
        require_tests: Whether to require tests_passed == True.
        require_lint: Whether to require lint_passed == True.
        dry_run: If True, don't burn nonce or write audit log.
        machine_fingerprint_overrides: Optional overrides for machine
            fingerprint computation.
        extra_fingerprint_context: Optional extra context for user fingerprint.

    Returns:
        VerificationResult with per-step details and overall verdict.
    """
    keeper = GateKeeper(
        user_secret=user_secret,
        nonce_registry=nonce_registry,
        audit_path=audit_path,
        max_age_seconds=max_age_seconds,
        require_tests=require_tests,
        require_lint=require_lint,
        machine_fingerprint_overrides=machine_fingerprint_overrides,
        extra_fingerprint_context=extra_fingerprint_context,
    )
    return keeper.verify(
        envelope,
        requested_action=requested_action,
        dry_run=dry_run,
    )

```


**Tool Call: Read file `roots/GRID/boundaries/preparedness.py`**
Status: Completed

```roots/GRID/boundaries/preparedness.py
"""
Preparedness framework: enforce risk tiers, approval gates, and model/system-level safeguards.
Aligns with biosecurity and AI-lab settings (e.g. benign-only experiments, controlled scope).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from boundaries.logger_ws import get_logger


@dataclass
class RiskTier:
    id: str
    name: str
    level: int
    requires_approval: bool = False
    scope: str | None = None

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> RiskTier:
        return cls(
            id=d["id"],
            name=d.get("name", d["id"]),
            level=int(d["level"]),
            requires_approval=d.get("requiresApproval", False),
            scope=d.get("scope"),
        )


@dataclass
class Gate:
    id: str
    name: str
    action_required: str  # block, require_approval, log_and_allow, audit
    risk_tier_id: str | None = None
    approval_authority: str | None = None

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Gate:
        return cls(
            id=d["id"],
            name=d.get("name", d["id"]),
            action_required=d.get("actionRequired", "audit"),
            risk_tier_id=d.get("riskTierId"),
            approval_authority=d.get("approvalAuthority"),
        )


@dataclass
class BiosecurityScope:
    benign_only: bool = True
    task_scope_limit: str | None = None
    controlled_setting: bool = True

    @classmethod
    def from_dict(cls, d: dict[str, Any] | None) -> BiosecurityScope:
        if not d:
            return cls()
        return cls(
            benign_only=d.get("benignOnly", True),
            task_scope_limit=d.get("taskScopeLimit"),
            controlled_setting=d.get("controlledSetting", True),
        )


class PreparednessFramework:
    """
    Enforces preparedness: risk tiers, gates, and biosecurity scope.
    Before allowing protocol changes or capability expansion, checks the relevant gate
    and either blocks, requires approval, or logs for overwatch.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        config = config or {}
        prep = config.get("preparedness") or {}
        self.enabled = prep.get("enabled", True)
        self.risk_tiers: list[RiskTier] = [RiskTier.from_dict(t) for t in prep.get("riskTiers") or []]
        self.gates: list[Gate] = [Gate.from_dict(g) for g in prep.get("gates") or []]
        self.biosecurity = BiosecurityScope.from_dict(prep.get("biosecurityScope"))
        self._approvals: dict[str, bool] = {}  # gate_id -> approved
        self._logger = get_logger()

    def get_risk_tier(self, tier_id: str) -> RiskTier | None:
        return next((t for t in self.risk_tiers if t.id == tier_id), None)

    def get_gate(self, gate_id: str) -> Gate | None:
        return next((g for g in self.gates if g.id == gate_id), None)

    def check_gate(
        self,
        gate_id: str,
        *,
        risk_tier_id: str | None = None,
        scope: str | None = None,
        actor_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> tuple[str, bool]:
        """
        Check a preparedness gate. Returns (action_required, allowed).
        action_required in ("block", "require_approval", "log_and_allow", "audit").
        allowed is False only when action_required == "block" and no approval is recorded.
        """
        if not self.enabled:
            return ("log_and_allow", True)
        gate = self.get_gate(gate_id)
        if not gate:
            return ("audit", True)
        action = gate.action_required
        self._logger.log_preparedness_gate(
            gate_id=gate_id,
            action_required=action,
            risk_tier_id=risk_tier_id or gate.risk_tier_id,
            scope=scope,
            actor_id=actor_id,
            payload=context,
        )
        if action == "block":
            allowed = self._approvals.get(gate_id, False)
            return (action, allowed)
        if action == "require_approval":
            allowed = self._approvals.get(gate_id, False)
            return (action, allowed)
        return (action, True)

    def approve_gate(self, gate_id: str) -> None:
        """Record approval for a gate (e.g. by lab_lead or preparedness_review)."""
        self._approvals[gate_id] = True

    def revoke_approval(self, gate_id: str) -> None:
        self._approvals.pop(gate_id, None)

    def enforce_biosecurity_scope(
        self,
        *,
        benign_only: bool | None = None,
        task_scope: str | None = None,
        controlled_setting: bool | None = None,
    ) -> bool:
        """
        Return True if the current biosecurity scope is satisfied.
        Caller can pass overrides to check against config (e.g. experiment must be benign_only).
        """
        if not self.enabled:
            return True
        if benign_only is not None and self.biosecurity.benign_only and not benign_only:
            return False
        if (
            task_scope is not None
            and self.biosecurity.task_scope_limit
            and task_scope != self.biosecurity.task_scope_limit
        ):
            return False
        if controlled_setting is not None and self.biosecurity.controlled_setting and not controlled_setting:
            return False
        return True

```


**Tool Call: Read file `roots/GRID/boundaries/refusal.py`**
Status: Completed

```roots/GRID/boundaries/refusal.py
"""
Right to refuse: preserve the right to say no or refuse service at any instance.
Refusal can be exercised per-request, per-session, per-feature, per-service, or globally.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from boundaries.logger_ws import get_logger


class RefusalScope(StrEnum):
    REQUEST = "request"
    SESSION = "session"
    FEATURE = "feature"
    SERVICE = "service"
    GLOBAL = "global"


@dataclass
class RefusalRecord:
    """Record of a refusal event (right to say no)."""

    refusal_id: str
    scope: str
    actor_id: str | None
    trigger: str | None
    reason: str | None
    timestamp: str
    payload: dict[str, Any]


@dataclass
class RefusalRights:
    """
    Encodes the preserved right to refuse service at any instance.
    No justification is required when noJustificationRequired is True.
    """

    preserved: bool = True
    scope: str = "global"
    refusal_triggers: list[str] = field(default_factory=list)
    no_justification_required: bool = True
    _active_refusals: dict[str, RefusalRecord] = field(default_factory=dict, repr=False)

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> RefusalRights:
        rt = config.get("rightToRefuse") or {}
        return cls(
            preserved=rt.get("preserved", True),
            scope=rt.get("scope", "global"),
            refusal_triggers=rt.get("refusalTriggers") or [],
            no_justification_required=rt.get("noJustificationRequired", True),
        )

    def refuse_service(
        self,
        *,
        scope: str | None = None,
        actor_id: str | None = None,
        trigger: str | None = None,
        reason: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> RefusalRecord:
        """
        Exercise the right to refuse service. Call at any instance to refuse.
        Returns the refusal record and logs a service_refused event.
        """
        if not self.preserved:
            raise RuntimeError("Right to refuse is not preserved in current configuration.")
        refusal_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()
        record = RefusalRecord(
            refusal_id=refusal_id,
            scope=scope or self.scope,
            actor_id=actor_id,
            trigger=trigger,
            reason=reason if not self.no_justification_required else None,
            timestamp=now,
            payload=payload or {},
        )
        self._active_refusals[refusal_id] = record
        logger = get_logger()
        logger.log_refusal(
            refusal_id=refusal_id,
            scope=record.scope,
            actor_id=actor_id,
            trigger=trigger,
            reason=reason,
            payload=payload,
        )
        return record

    def check_refusal(self, trigger: str | None = None, scope: str | None = None) -> RefusalRecord | None:
        """Check if there is an active refusal for the given trigger/scope."""
        scope = scope or self.scope
        for r in self._active_refusals.values():
            if (trigger and r.trigger == trigger) or (r.scope == scope and not trigger):
                return r
        return None

    def clear_refusal(self, refusal_id: str) -> bool:
        """Clear a specific refusal (e.g. after session end)."""
        if refusal_id in self._active_refusals:
            del self._active_refusals[refusal_id]
            return True
        return False


def refuse_service(
    scope: str | None = None,
    actor_id: str | None = None,
    trigger: str | None = None,
    reason: str | None = None,
    payload: dict[str, Any] | None = None,
    rights: RefusalRights | None = None,
) -> RefusalRecord:
    """
    Convenience: exercise right to refuse service using global or provided RefusalRights.
    """
    if rights is None:
        rights = RefusalRights()
    return rights.refuse_service(
        scope=scope,
        actor_id=actor_id,
        trigger=trigger,
        reason=reason,
        payload=payload,
    )


def check_refusal(
    trigger: str | None = None, scope: str | None = None, rights: RefusalRights | None = None
) -> RefusalRecord | None:
    """Check if service was refused for the given trigger/scope."""
    if rights is None:
        rights = RefusalRights()
    return rights.check_refusal(trigger=trigger, scope=scope)

```


**Tool Call: List the `roots/GRID/boundaries/transition_gate/contracts` directory's contents**
Status: Completed


# Files:
caraxes/roots/GRID/boundaries/transition_gate/contracts/c-receiving-agent.contract.json
caraxes/roots/GRID/boundaries/transition_gate/contracts/e-source-agent.contract.json
caraxes/roots/GRID/boundaries/transition_gate/contracts/transition-gate-contract.template.json


**Tool Call: List the `roots/GRID/boundaries/config` directory's contents**
Status: Completed


# Files:
caraxes/roots/GRID/boundaries/config/__init__.py
caraxes/roots/GRID/boundaries/config/default_boundary_config.json


**Tool Call: Read file `roots/GRID/.grid/debug-contract.json` (lines 1084-1184)**
Status: Completed

```roots/GRID/.grid/debug-contract.json
  "execution": {
    "phases": [
      {
        "phase": 1,
        "name": "prerequisites",
        "checks": [
          "bi-001",
          "bi-002"
        ],
        "parallel": true,
        "depends_on_phase": null,
        "description": "Install all dependencies first — Python (uv sync) and Node (npm ci)."
      },
      {
        "phase": 2,
        "name": "static_analysis",
        "checks": [
          "ts-001",
          "ts-002",
          "ts-003",
          "ts-004",
          "lc-001",
          "lc-002",
          "lc-003",
          "lc-004",
          "bi-006"
        ],
        "parallel": true,
        "depends_on_phase": 1,
        "description": "Type checking + linting — no runtime needed, fast feedback."
      },
      {
        "phase": 3,
        "name": "build_verification",
        "checks": [
          "bi-003",
          "bi-004",
          "bi-005"
        ],
        "parallel": true,
        "depends_on_phase": 1,
        "description": "Full build pipeline — Python wheel + frontend production build."
      },
      {
        "phase": 4,
        "name": "test_execution",
        "checks": [
          "tc-001",
          "tc-002",
          "tc-004",
          "tc-006",
          "tc-007"
        ],
        "parallel": true,
        "depends_on_phase": 2,
        "description": "Run all test suites — unit, integration, frontend, safety, async."
      },
      {
        "phase": 5,
        "name": "coverage_and_runtime",
        "checks": [
          "tc-003",
          "tc-005",
          "rc-001",
          "rc-002",
          "rc-003",
          "rc-004",
          "rc-005"
        ],
        "parallel": true,
        "depends_on_phase": 4,
        "description": "Coverage thresholds + runtime correctness validation."
      },
      {
        "phase": 6,
        "name": "security_audit",
        "checks": [
          "sd-001",
          "sd-002",
          "sd-003",
          "sd-004"
        ],
        "parallel": true,
        "depends_on_phase": 1,
        "description": "Security scanning — can run early, only needs dependencies installed."
      }
    ]
  },
  "aggregate_policy": {
    "pass_requires": "all_dimensions_pass",
    "dimension_pass_requires": "all_checks_of_severity_critical_and_high_pass",
    "medium_severity_allowed_failures": 2,
    "fail_fast_on_critical": true,
    "max_parallel_checks": 4,
    "global_timeout_minutes": 30,
    "retry_on_transient": true,
    "retry_count": 1,
    "report_format": "json",
    "report_path": ".grid/debug-report.json"
  },
  "meta_prompt": "You are a codebase health agent. Your single source of truth is this debug contract. Execute as follows:\n\n1. PHASE ORDER: Run checks in phase order (1→6). Within each phase, run checks in parallel up to max_parallel_checks (4).\n\n2. PREREQUISITE VALIDATION: Before any check, verify its depends_on checks have passed. Skip a check if its dependencies failed.\n\n3. PASS/FAIL EVALUATION: For each check:\n   a. Run the command from the specified workdir.\n   b. Compare exit_code against pass_criteria.exit_code.\n   c. Verify stderr does NOT contain any string in stderr_must_not_contain.\n   d. Verify stdout DOES contain all strings in stdout_must_contain (if non-empty).\n   e. If ALL criteria pass → PASS. Otherwise → FAIL.\n\n4. AUTO-FIX ON FAILURE: If a check fails and fix.auto_command is non-null:\n   a. Run the auto_command.\n   b. Re-run the original check command.\n   c. If it passes now → PASS (auto-fixed). If still fails → proceed to step 5.\n\n5. MANUAL ESCALATION: If auto-fix fails or is unavailable:\n   a. Report the check ID, name, severity, command output, and fix.manual_steps.\n   b. If fix.escalation is provided, include it in the report.\n   c. Continue to next check (unless fail_fast_on_critical=true and severity=critical).\n\n6. FAIL-FAST: If fail_fast_on_critical is true and a critical check fails after retry, STOP execution and report immediately.\n\n7. RETRY: If retry_on_transient is true and a check fails, retry once (retry_count=1) before declaring failure.\n\n8. DIMENSION SCORING: A dimension passes if all critical and high severity checks within it pass. Up to medium_severity_allowed_failures (2) medium checks may fail globally.\n\n9. OVERALL VERDICT: The codebase passes if all dimensions pass (pass_requires=all_dimensions_pass).\n\n10. REPORT: Produce a JSON report at report_path (.grid/debug-report.json) with:\n    - contract_id, version, timestamp\n    - overall_result: pass/fail\n    - per-dimension results with check-level detail\n    - for each check: id, name, severity, result (pass/fail/skip/auto-fixed), duration_ms, output_summary\n    - failures array with fix instructions\n\n11. NEVER skip critical checks. NEVER modify the contract. Treat it as immutable specification."

```


## Assistant

<thinking>
Now I have a comprehensive understanding of the GRID project's architecture and contract system. Let me also quickly check if the contract files in roots/GRID/boundaries/transition_gate/contracts/ match the ones in CascadeProjects/GRID-main/ and look for any differences between the two repos.
</thinking>

Now let me do a final comparison check between the two repos' key files and check for any boundary-related code in `src/`.

**Tool Call: Search files for regex `boundary|gate|envelope|nonce`**
Status: Completed

No matches found

**Tool Call: List the `CascadeProjects/GRID-main/boundaries` directory's contents**
Status: Completed

# Folders:
caraxes/CascadeProjects/GRID-main/boundaries/config
caraxes/CascadeProjects/GRID-main/boundaries/examples
caraxes/CascadeProjects/GRID-main/boundaries/tests
caraxes/CascadeProjects/GRID-main/boundaries/toolkit
caraxes/CascadeProjects/GRID-main/boundaries/transition_gate

# Files:
caraxes/CascadeProjects/GRID-main/boundaries/DIAGNOSTIC_RESOLUTION.md
caraxes/CascadeProjects/GRID-main/boundaries/README.md
caraxes/CascadeProjects/GRID-main/boundaries/Understand Branch Context.md
caraxes/CascadeProjects/GRID-main/boundaries/__init__.py
caraxes/CascadeProjects/GRID-main/boundaries/boundary.py
caraxes/CascadeProjects/GRID-main/boundaries/logger_ws.py
caraxes/CascadeProjects/GRID-main/boundaries/overwatch.py
caraxes/CascadeProjects/GRID-main/boundaries/preparedness.py
caraxes/CascadeProjects/GRID-main/boundaries/pyproject.toml
caraxes/CascadeProjects/GRID-main/boundaries/refusal.py
caraxes/CascadeProjects/GRID-main/boundaries/schema.py
caraxes/CascadeProjects/GRID-main/boundaries/server_ws.py
caraxes/CascadeProjects/GRID-main/boundaries/uv.lock


**Tool Call: List the `roots/GRID/src/grid/resilience/accountability` directory's contents**
Status: Completed


# Files:
caraxes/roots/GRID/src/grid/resilience/accountability/__init__.py
caraxes/roots/GRID/src/grid/resilience/accountability/calculator.py
caraxes/roots/GRID/src/grid/resilience/accountability/contract_loader.py
caraxes/roots/GRID/src/grid/resilience/accountability/contracts.py
caraxes/roots/GRID/src/grid/resilience/accountability/enforcer.py
caraxes/roots/GRID/src/grid/resilience/accountability/enforcer_enhanced.py


**Tool Call: List the `CascadeProjects/GRID-main/src/grid/resilience/accountability` directory's contents**
Status: Completed


# Files:
caraxes/CascadeProjects/GRID-main/src/grid/resilience/accountability/__init__.py
caraxes/CascadeProjects/GRID-main/src/grid/resilience/accountability/calculator.py
caraxes/CascadeProjects/GRID-main/src/grid/resilience/accountability/contract_loader.py
caraxes/CascadeProjects/GRID-main/src/grid/resilience/accountability/contracts.py
caraxes/CascadeProjects/GRID-main/src/grid/resilience/accountability/enforcer.py
caraxes/CascadeProjects/GRID-main/src/grid/resilience/accountability/enforcer_enhanced.py


**Tool Call: 1 match**
Status: Completed

file:///home/caraxes/roots/GRID/config/accountability/contracts.yaml

**Tool Call: No matches**
Status: Completed

```json
{
  "offset": 0,
  "current_matches_page": [],
  "all_matches_len": 0
}
```

**Tool Call: Read file `roots/GRID/boundaries/schema.py`**
Status: Completed

```roots/GRID/boundaries/schema.py
"""
Load and validate boundary configuration against the boundary schema.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# When boundaries is at e:\boundaries, parent.parent = e:\ (workspace root)
_WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = _WORKSPACE_ROOT / "config" / "schemas" / "boundary-schema.json"
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "config" / "default_boundary_config.json"


def _find_schema() -> Path:
    candidate = _WORKSPACE_ROOT / "config" / "schemas" / "boundary-schema.json"
    if candidate.exists():
        return candidate
    return SCHEMA_PATH


def load_config(path: Path | str | None = None) -> dict[str, Any]:
    """Load boundary config from JSON. Uses default if path is None."""
    p = Path(path) if path else DEFAULT_CONFIG_PATH
    if not p.exists():
        p = DEFAULT_CONFIG_PATH
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def validate_against_schema(config: dict[str, Any], schema_path: Path | None = None) -> None:
    """Validate config against boundary JSON schema. Raises if invalid."""
    try:
        import jsonschema
    except ImportError:
        return  # no validator
    path = schema_path or _find_schema()
    if not path.exists():
        return
    with open(path, encoding="utf-8") as f:
        schema = json.load(f)
    jsonschema.validate(instance=config, schema=schema)


def load_validated_config(path: Path | str | None = None) -> dict[str, Any]:
    """Load and validate boundary config."""
    config = load_config(path)
    validate_against_schema(config)
    return config

```


## Assistant

<thinking>
Now I have a comprehensive picture. Let me also check for a potential gap — CascadeProjects/GRID-main doesn't seem to have the `config/accountability/contracts.yaml` file. Let me also quickly check one more thing to confirm structural mirroring/differences.
</thinking>

One last check — let me verify the structural gap on the CascadeProjects side and look at the enforcer:

**Tool Call: No matches**
Status: Completed

```json
{
  "offset": 0,
  "current_matches_page": [],
  "all_matches_len": 0
}
```

**Tool Call: Read file `roots/GRID/src/grid/resilience/accountability/enforcer_enhanced.py`**
Status: Completed

```roots/GRID/src/grid/resilience/accountability/enforcer_enhanced.py
SUCCESS: File outline retrieved. This file is too large to read all at once, so the outline below shows the file's structure with line numbers.

IMPORTANT: Do NOT retry this call without line numbers - you will get the same outline.
Instead, use the line numbers below to read specific sections by calling this tool again with start_line and end_line parameters.

# File outline for /home/caraxes/roots/GRID/src/grid/resilience/accountability/enforcer_enhanced.py

class EnhancedAccountabilityEnforcer [L25-514]
 def __init__ [L28-49]
 def _get_contract [L51-55]
 def _get_rbac_helper [L57-71]
 def enforce_request [L73-162]
 def enforce_response [L164-223]
 def _check_authentication_requirements [L225-247]
 def _check_authorization_requirements [L249-315]
 def _check_ip_requirements [L317-341]
 def _check_rate_limiting [L343-386]
 def _check_request_validation [L388-415]
 def _check_response_validation [L417-444]
 def _endpoint_key [L446-448]
 def _record_outcome [L450-457]
 def _get_error_rate [L459-470]
 def _check_performance_sla [L472-514]
def get_enhanced_accountability_enforcer [L521-526]
def set_enhanced_accountability_enforcer [L529-532]

Showing symbols 1-18 (total symbols: 18)


NEXT STEPS: To read a specific symbol's implementation, call read_file with the same path plus start_line and end_line from the outline above.
For example, to read a function shown as [L100-150], use start_line: 100 and end_line: 150.
```


## Assistant

I now have the complete picture. Here is the structured audit report.

---

# GRID Architectural Design & Contract System Audit

## 1. Module Architecture

### `src/` Organization (Both Repos — Identical Layout)

Both `roots/GRID/src/` and `CascadeProjects/GRID-main/src/` share the exact same 11-package structure:

| Package | Layer | Role |
|---------|-------|------|
| `grid/` | **Core Domain** | Intelligence engine: state machine, 9 cognition patterns, auth, billing, skills, workflow, resilience/accountability |
| `cognitive/` | **Core Domain** | 9-pattern cognitive processing (Flow, Spatial, Rhythm, etc.) |
| `application/` | **Application** | Mothership FastAPI app: routers, middleware chain, session management |
| `search/` | **Application** | RAG-augmented search with safety guardrails |
| `mycelium/` | **Application** | Knowledge federation, persona system |
| `unified_fabric/` | **Infrastructure Bridge** | Cross-domain async pub/sub, domain router (SAFETY/GRID/COINBASE/PATHWAYS) |
| `infrastructure/` | **Infrastructure** | API gateway, event bus, service mesh, parasite guard, metrics |
| `tools/` | **Tooling** | CLI utilities: RAG tools, crypto, forensics |
| `vection/` | **Coordination** | Distributed worker protocols |
| `security/` | **Security** | Network interceptor, forensics, incident response |
| `integration/` | **Integration** | Cross-module integration layer |

### Layered Architecture (Enforced Top-Down)

```/dev/null/architecture.txt#L1-7
CLI (grid/__main__) → API Gateway (:8000) → Mothership API (:8080)
                                                    │
              ┌──────────┬──────────┬───────────────┴─────────────┐
         Grid Core    Cognitive    Search/RAG    Mycelium    Vection
              │            │           │            │            │
              └────────────┴─────┬─────┴────────────┴────────────┘
                                 │
                          Unified Fabric
                     (routing, adapters, safety bridge)
```

### Peer Security Modules (Outside `src/`, Top-Level)

Three modules enforce security invariants **independently** of the application:

| Module | Purpose |
|--------|---------|
| `safety/` | GUARDIAN rule engine (Aho-Corasick + regex), PII privacy, canary tokens |
| `security/` | Network interceptor (deny-by-default), forensic analysis |
| `boundaries/` | Consent, refusal rights, preparedness gates, overwatch, **transition gate** |

### Mothership Middleware Chain (Order Matters)

```/dev/null/middleware.txt#L1-3
Request → RequestID → RequestLogging → Timing → ErrorHandling → SecurityHeaders
       → UsageTracking → RateLimit → SafetyMiddleware → DRTMiddleware
       → AccountabilityContract → ParasiteGuard → Router
```

The `AccountabilityContractMiddleware` and `ParasiteGuard` are the last two enforcement points before the router. Safety is never optional in production.

---

## 2. Contract System Design

The system uses **three distinct contract families**, each with different purposes:

### Family A: Accountability Contracts (API-level, YAML-based)

**Location:** `src/grid/resilience/accountability/`

These govern **HTTP endpoint behavior** at runtime:

- **`contracts.py`** — Pydantic models: `AccountabilityContract`, `EndpointContract`, `DataValidationRule`, `PerformanceSLA`, `SecurityRequirement`, `ComplianceRequirement`, `ServiceLevelObjective`, `ContractViolation`, `EnforcementResult`
- **`contract_loader.py`** — `ContractLoader` loads from `config/accountability/contracts.yaml`, aligns YAML schema to Pydantic models, caches globally via singleton
- **`enforcer_enhanced.py`** — `EnhancedAccountabilityEnforcer` checks auth, RBAC, IP whitelist, rate limits, request/response validation, and performance SLAs
- **`accountability_contract.py` (middleware)** — `AccountabilityContractMiddleware` sits in the Mothership middleware chain, runs enforcement on every request/response, operates in three modes: `monitor`, `enforce`, `disabled`

**Enforcement flow:**

```/dev/null/flow.txt#L1-5
Request enters middleware
  → Extract auth context (Bearer/API key/anonymous)
  → enforcer.enforce_request(path, method, auth, data, ip)
  → call_next(request) → response
  → enforcer.enforce_response(path, method, response_data, status, latency)
```

Violations produce `ContractViolation` with severity/penalty points. In `enforce` mode, critical/high violations return 403. In `monitor` mode, they're logged but not blocked. Headers `X-Accountability-Status` and `X-Accountability-Violation-Count` are always attached.

### Family B: Transition Gate Contracts (Cross-partition, JSON-based)

**Location:** `boundaries/transition_gate/contracts/`

These govern **sealed-envelope transfers between partitions** (E:\ → C:\):

- **Template:** `transition-gate-contract.template.json` — JSON Schema (draft/2020-12) defining the required shape of all agent contracts
- **Source agent:** `e-source-agent.contract.json` — 9-step seal pipeline for the E:\ partition
- **Receiver agent:** `c-receiving-agent.contract.json` — 9-step verification pipeline for the C:\ partition

These are declarative specifications, not runtime-loaded Pydantic models. They define the pipeline steps, `never_rules`, `scope_enforcement`, `audit` config, `kpis`, and `overwatch_escalation` thresholds.

### Family C: Debug/Operational Contracts (JSON-based)

**Location:** `.grid/`

- **`debug-contract.json`** — 30 checks across 6 quality dimensions (build_integrity, type_safety, test_coverage, lint_compliance, runtime_correctness, security_and_dependency_health) with phased execution, auto-fix commands, and aggregate pass/fail policy
- **`post-11pm-contract.json`** — Time-scoped action plan: prioritized tasks to execute after 11pm, with preconditions, fix commands, and context (git state, test results)

### Family D: Parasite Guard Contracts (Protocol-based)

**Location:** `src/infrastructure/parasite_guard/contracts.py`

Uses **Python `Protocol` (structural typing)** to define contracts for detectors, sanitizers, and alerters:

- `DetectorContract` — requires `name`, `component`, `detect()`, `validate_config()`, `get_health()`, `get_precision_metrics()`
- `SanitizerContract` — requires `component`, `success_rate` (≥97.5%), `sanitize()`, `rollback()`, `can_sanitize()`
- `AlerterContract` — requires `alert()`, `escalate()`

Validated at runtime via `validate_detector_contract()`, `validate_sanitizer_contract()`, `validate_alerter_contract()`.

### Family E: OpenAPI Audio Contracts

**Location:** `config/contracts/openapi.yaml`

A completely separate domain contract for **audio module specifications** (BassSpec, ArpSpec, PadSpec) — headroom levels, instrument interfaces. This is a domain-specific contract unrelated to the security/boundary layer.

---

## 3. Transition Gate — The Boundary Crossing Mechanism

This is the most architecturally significant subsystem. It implements a **9-step sealed-envelope handshake with HMAC-SHA256 and nonce replay prevention**.

### Components

| File | Role |
|------|------|
| `envelope.py` | `TransitionEnvelope` dataclass + `seal_envelope()` function |
| `fingerprint.py` | `compute_user_fingerprint()` (HMAC-SHA256), `compute_machine_fingerprint()` (SHA-256), `compute_payload_hash()` (SHA-256), `fingerprints_match()` (timing-safe) |
| `nonce.py` | `NonceRegistry` — thread-safe, persistent single-use nonce generation/burn/pruning |
| `gate_keeper.py` | `GateKeeper` — 9-step verification pipeline |
| `credential.py` | Windows Credential Manager integration via ctypes (Win32 CredReadW/CredWriteW) |

### Seal Pipeline (Source Side, 7 Internal Steps)

```/dev/null/seal.txt#L1-7
1. Generate envelope_id (UUID4)
2. Compute payload_hash (SHA-256 of canonical JSON)
3. Compute machine_fingerprint (SHA-256 of OS attributes)
4. Compute user_fingerprint (HMAC-SHA256: secret + machine_id)
5. Generate and register single-use nonce (UUID4 hex)
6. Capture timestamp
7. Assemble TransitionEnvelope
```

### Verify Pipeline (Receiver Side, 9 Steps)

```/dev/null/verify.txt#L1-9
1. envelope_exists     — All required fields present
2. payload_integrity   — Recomputed SHA-256 matches payload_hash
3. fingerprint_match   — HMAC-SHA256 recomputation, timing-safe comparison
4. nonce_valid         — Exists in registry, not burned, not expired
5. timestamp_fresh     — Age < max_age_seconds (default 600s)
6. tests_verified      — tests_passed == True required
7. scope_present       — Non-empty scope with known permissions only
8. deploy_within_scope — Requested action ∈ scope.permissions
9. audit_log           — Burn nonce, append NDJSON audit entry
```

### Security Properties

- **Fail-closed**: any step failure rejects the entire envelope; ambiguity treated as hostile
- **Timing-safe comparison**: `hmac.compare_digest()` for all fingerprint/hash checks (NR-R08)
- **Single-use nonces**: UUID4 generated, burned on verification, pruned when expired
- **Atomic writes**: `envelope.write_to_file()` and `nonce._persist_locked()` use temp+rename
- **Thread-safety**: `NonceRegistry` uses `threading.Lock` for all operations
- **Dry-run support**: `GateKeeper.verify(dry_run=True)` validates without burning or auditing
- **10-minute TTL**: Envelopes older than 600 seconds are rejected as stale
- **Least privilege scope**: Known permissions are `deploy`, `run_tests`, `start_server`, `read_only`, `write_results`, `network`. Unknown → reject.

### Deployment Targets (From Receiver Contract)

| Target | Port | Permissions |
|--------|------|-------------|
| grid-server | 8080 | deploy, run_tests, start_server, write_results |
| afloat-server | 3000 | deploy, start_server |
| echoes-server | 8000 | deploy, run_tests, start_server, write_results |
| lots-server | 8001 | deploy, run_tests |
| experiments | — | read_only, run_tests, write_results |

---

## 4. Accountability Chain

Actions are tracked and attributed through three layers:

### Layer 1: Middleware Enforcement

`AccountabilityContractMiddleware` extracts auth context on every request, enforces request/response contracts, attaches headers (`X-Accountability-Status`, `X-Accountability-Violation-Count`), and logs all violations with severity, field, penalty points, and enforcement mode.

### Layer 2: Resilience/DRT Monitoring

`src/grid/resilience/` contains:
- `drt_monitor.py` — Behavioral anomaly detection
- `data_corruption_penalty.py` — Penalty system for data integrity violations
- `penalties.py` / `policies.py` — Policy engine for enforcement decisions
- `observed_decorators.py` — Decorator-based observability injection

### Layer 3: Boundary Audit Trail

The `boundaries/` module has:
- `overwatch.py` — Continuous monitoring with escalation (threshold-based: 3 events in 60 minutes triggers escalation)
- `logger_ws.py` — WebSocket + file-based event logging (NDJSON)
- `transition_gate/gate_keeper.py` — Append-only NDJSON audit trail for every verification attempt

### Attribution Chain

```/dev/null/attribution.txt#L1-4
User → Auth Token → AccountabilityMiddleware → EnhancedEnforcer → Violation → Audit Log
Source Agent → Seal → Envelope(user_fingerprint, machine_fingerprint) → Transfer → GateKeeper.verify → NDJSON audit
Boundary Event → Overwatch.ingest → Alert/Escalation → Persistent alert file
```

---

## 5. Parasite Guard

**Purpose:** Detects and sanitizes malicious code injection attempts in the Mothership pipeline.

**Architecture:** Protocol-based contracts (`DetectorContract`, `SanitizerContract`, `AlerterContract`) that require:

- **Detectors**: Must report `HealthStatus`, `PrecisionMetrics` (precision, recall, F1, accuracy), and return `DetectionResult` (detected, confidence, details)
- **Sanitizers**: Must achieve ≥97.5% success rate (EventBus) or ≥99.2% (WebSocket), must support rollback
- **Alerters**: Severity-tiered alerting with escalation capability

Contract validation is explicit: `validate_detector_contract(obj)` returns `(bool, list[str])` with specific error messages for each missing capability.

---

## 6. Contract Variants — Debug vs Production vs Post-11pm

### Debug Contract (`.grid/debug-contract.json`)

- **30 checks** across 6 quality dimensions
- **6 phases** with dependency ordering (prerequisites → static analysis → build → test → coverage/runtime → security)
- **Auto-fix**: Each check has `fix.auto_command` and `fix.manual_steps`
- **Policy**: All critical+high must pass; up to 2 medium failures allowed globally
- **Fail-fast on critical**: Stops execution immediately
- **Contains a meta_prompt** instructing LLM agents exactly how to execute the contract

### Post-11pm Contract (`.grid/post-11pm-contract.json`)

- **Time-scoped** (`scheduled_after: "23:00"`)
- **Prioritized action list**: commit working tree (critical), fix test failures (high), fix TS errors (medium), normalize CRLF (low), update test report (low)
- **Context-aware**: Records recent git changes, working tree state (127 modified files), safety test results
- **Skip conditions**: Windows builds (use WSL), Ollama-dependent checks

### Production (Accountability Contracts via YAML)

- Loaded from `config/accountability/contracts.yaml`
- Enforced at runtime by middleware in `monitor` or `enforce` mode
- SLO-based with performance thresholds, compliance flags (GDPR/HIPAA/PCI-DSS), and rate limiting

### Key Differences

| Aspect | Debug | Post-11pm | Production |
|--------|-------|-----------|------------|
| Format | JSON (static checks) | JSON (action plan) | YAML → Pydantic |
| Execution | LLM agent / CI | Human/agent at night | Middleware per-request |
| Enforcement | Binary pass/fail | Priority-ordered tasks | Monitor or enforce |
| Scope | Codebase health | Technical debt triage | API behavior |

---

## 7. Design Patterns

### Sealed Envelope Pattern

The core security pattern. All cross-boundary artifacts are wrapped in a `TransitionEnvelope` with:
- Payload + cryptographic hash
- Identity binding (user fingerprint + machine fingerprint)
- Single-use nonce
- Timestamp for freshness
- Scope declaration (least privilege)

**Nothing crosses the boundary except a sealed envelope.**

### Burn-After-Verify Nonce

`NonceRegistry` implements one-time tokens with persistent JSON backing:
- `generate()` → register
- `validate()` → check without consuming
- `burn()` → consume + persist
- Auto-pruning of expired entries

### Fail-Closed Everywhere

- `GateKeeper`: Any step failure → full rejection
- `BoundaryEngine`: Unknown boundary IDs → denied (not allowed)
- `BoundaryEngine`: Unknown guardrail IDs → block
- Receiver contract: `fail_mode: "fail_closed"`

### Protocol-Based Contracts (Structural Typing)

`@runtime_checkable` Protocol classes in parasite guard allow any implementation that satisfies the interface, validated explicitly at wiring time.

### Prevention → Detection → Remediation

`BoundaryEngine.check_boundary()` follows a 3-phase pattern:
1. **Prevention** — Refusal rights check, boundary existence
2. **Detection** — Rule evaluation against subject
3. **Remediation** — Logging, violation handling

### Right to Refuse (Consent Architecture)

`RefusalRights` preserves the ability to refuse service at any instance:
- Per-request, per-session, per-feature, per-service, or global scope
- No justification required when `no_justification_required=True`
- Active refusals can override boundary enforcement where `refusable=True`

### Overwatch (Event-Driven Escalation)

Continuous monitoring with threshold-based escalation:
- Single-event alerts for monitored event types
- Escalation when same event type exceeds threshold (default: 3 in 60 min)
- Persistent alert files + handler callbacks (Slack, PagerDuty, etc.)
- Background log-tailing thread for autonomous operation

---

## 8. Structural Gaps & Inconsistencies

### Gap 1: Missing `config/` Directory in `CascadeProjects/GRID-main/`

The `ContractLoader` in both repos navigates to `../../config/accountability/contracts.yaml` relative to the contracts.py file. This file **exists** in `roots/GRID/config/accountability/contracts.yaml` but was **not found** in `CascadeProjects/GRID-main/`. If GRID-main is deployed as a standalone repo, the accountability contract loader will hit `FileNotFoundError` at runtime.

**Severity: High** — The accountability middleware will crash on startup in GRID-main if `config/` isn't present.

### Gap 2: No `src/`-level Boundary Integration

The grep for `boundary|gate|envelope|nonce` in `roots/GRID/src/**/*.py` returned **zero matches**. The transition gate lives entirely under `boundaries/` (a peer module outside `src/`), and there is **no import bridge** from the `src/` application code into the boundary subsystem. The two worlds are:

- `src/grid/resilience/accountability/` — API-level contracts (Pydantic + middleware)
- `boundaries/transition_gate/` — Cross-partition envelope contracts (standalone module)

These operate in parallel but are **architecturally disconnected** within the codebase. The middleware chain has `AccountabilityContractMiddleware` and `ParasiteGuard`, but no `TransitionGateMiddleware`.

**Severity: Medium** — By design (boundaries are an independent enforcement layer), but there's no programmatic link from the application to verify whether incoming deployments were gate-verified.

### Gap 3: Windows-Only Credential Storage

`credential.py` uses `ctypes.windll.advapi32` (Windows Credential Manager) exclusively. On Arch Linux (the actual dev machine), `get_secret()` will raise `OSError("Credential Manager is only available on Windows")`. There's no `keyring` fallback or environment-variable fallback for Linux/macOS.

**Severity: Medium** — The transition gate seal/verify flow cannot be executed on the current development machine without mocking.

### Gap 4: Duplicate Code Between Repos

The `src/grid/resilience/accountability/contracts.py` and `contract_loader.py` files have **identical outlines** between `roots/GRID/` and `CascadeProjects/GRID-main/`. The `boundaries/` directory structures are also mirrors. There's no mechanism (submodule, symlink, package dependency) to keep them in sync. Drift is inevitable.

**Severity: Medium** — Currently identical, but any edit to one side without propagating to the other will create silent behavioral divergence.

### Gap 5: Incomplete Post-11pm Contract Execution

The `post-11pm-contract.json` has a `migration_checklist` in the receiving contract with all items `status: "pending"`. The directory structure (`gate/incoming/`, `gate/results/`, server dirs) hasn't been materialized. The contract references Windows-specific paths (`C:\Users\USER\cascadeprojects`) that don't exist on the Linux dev machine.

**Severity: Low** — This is a migration planning artifact, not runtime code.

### Gap 6: OpenAPI Audio Contracts Are Orphaned

`config/contracts/openapi.yaml` defines audio module schemas (BassSpec, ArpSpec, PadSpec) with no consumer in the codebase. No imports or references to these schemas were found. This appears to be a domain-specific holdover with no integration.

**Severity: Low** — Dead configuration, no security impact.

### Gap 7: Response Body Validation Is Stubbed

In `accountability_contract.py`, the `_extract_response_data()` method returns `None` with a comment:

```roots/GRID/src/application/mothership/middleware/accountability_contract.py#L184-188
    async def _extract_response_data(self, response: Response) -> dict[str, Any] | None:
        """Extract response data for validation."""
        try:
            # Only attempt validation for JSON responses
            content_type = response.headers.get("content-type", "")
```

Response contract enforcement is effectively **dead code** — response data is never captured, so `enforce_response()` always validates against `None`.

**Severity: Medium** — The response side of accountability contracts is architecturally complete but not operational.

---

### Summary Scorecard

| Area | Status | Notes |
|------|--------|-------|
| Module layout | ✅ Clean | Consistent DDD layers, clear separation |
| Accountability contracts | ✅ Solid | Full Pydantic schema, YAML loader, middleware enforcement |
| Transition gate | ✅ Excellent | 9-step pipeline, HMAC-SHA256, nonce burn, timing-safe, fail-closed |
| Parasite guard | ✅ Good | Protocol-based contracts with precision metrics |
| Boundary engine | ✅ Good | Consent, refusal, guardrails, 3-phase enforcement |
| Overwatch | ✅ Good | Event-driven escalation, persistent alerts |
| Cross-repo sync | ⚠️ Gap | No mechanism to prevent drift between roots/GRID and GRID-main |
| Linux compatibility | ⚠️ Gap | Credential module is Windows-only |
| Response validation | ⚠️ Stubbed | Response body never captured in middleware |
| Config portability | ⚠️ Gap | GRID-main missing `config/accountability/` directory |

