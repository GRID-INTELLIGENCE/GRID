# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GRID (Geometric Resonance Intelligence Driver) is a local-first AI framework built on Python 3.13, FastAPI, SQLAlchemy, and ChromaDB+Ollama for RAG. It uses domain-driven design with event-driven agentic workflows, a 9-pattern cognitive intelligence engine, and layered security/safety enforcement. Version 2.7.0, MIT license, repo at `github.com/GRID-INTELLIGENCE/GRID`.

## Commands

```bash
# Install / sync environment
uv sync --group dev --group test

# Run the core backend test slice
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

# Frontend renderer checks
cd frontend && npm run typecheck
cd frontend && npm test

# Frontend/Electron build checks
cd frontend && npm run build:renderer
cd frontend && npm run build:electron

# Landing brand validation
cd landing && npm run validate:brand

# Backend coverage refresh (diagnostic, non-gating)
make coverage-backend

# Focused module coverage (used to validate disputed module gaps)
make coverage-mycelium

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
make test               # Core backend tests
make test-frontend      # Frontend Vitest suite
make frontend-typecheck # Frontend typecheck
make electron-build     # Electron build
make landing-validate   # Landing brand validation
make lint               # Ruff + Mypy
make format             # Auto-format
make clean              # Remove caches
```

## Recommended Debugging Windows

Treat `GRID-main` as four separate execution surfaces:

1. **Python service**: `src/<domain>` and matching `tests/<domain>`.
2. **Frontend renderer**: `frontend/src` only.
3. **Electron shell**: `frontend/electron` and Electron config.
4. **Landing/branding**: `landing/` only.

Default workflow:

1. Reproduce in one window only.
2. Run that window's smallest real gate.
3. Fix the failing layer before widening scope.
4. Re-run the narrow gate, then the full window gate.

Notes:

- `npm test` in `frontend/` uses Vitest. Do not pass Jest-only flags such as `--runInBand`.
- `make test` is a backend confidence slice, not a full-repo verification command.
- `make coverage-backend` is the canonical backend coverage refresh command.
- If a module appears unexpectedly low/zero, run focused coverage (for example `make coverage-mycelium`) before planning large test-count expansions.
- Avoid running heavy Python tests, Electron, and large frontend builds in parallel when RAM pressure is already high.

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

- `asyncio_mode = "strict"` — all async tests require explicit `@pytest.mark.asyncio`
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

## Git hygiene and source protection

- Respect **`.gitignore`** and **`core.excludesfile`** when set (`~/.config/git/ignore` — see `~/scripts/global-git-excludes-README.md`). Do not stage generated output (`dist/`, `build/`, `.next/`, coverage, `.venv/`, `node_modules/`, `*.tsbuildinfo`), caches, local `.env*`, or IDE-only dirs unless the operator explicitly requests it.
- Prefer **`git status`** and **`git diff`** before **`git add`**. Avoid repository-wide **`git add .`**. Do not **force-push** or rewrite **history** without explicit instruction.
- Change **generators and source**, not hand-edited **`dist/`** or lockfiles, unless the task is explicitly to update those files.
- **Secrets:** Never commit credentials. If found tracked or staged, stop and escalate: **`.gitignore`**, **`git rm --cached`**, and rotation / history scrub are **human-gated** when pushes occurred.
- **New repos:** `~/seed/templates/gitignore-node-strict.template` or `gitignore-python-uv.template`. **Audit:** `~/scripts/gitignore-audit.sh`.

