# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GRID (Geometric Resonance Intelligence Driver) is a local-first AI framework built on Python 3.13, FastAPI, SQLAlchemy, and ChromaDB+Ollama for RAG. It uses domain-driven design with event-driven agentic workflows, a 9-pattern cognitive intelligence engine, and layered security/safety enforcement.

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
| `grid/` | Core intelligence: state machine (essence), 9 cognition patterns, awareness, evolution, quantum architecture, multi-tenant organization |
| `application/` | Mothership Cockpit FastAPI app: versioned routers (v1, v2), session management, alerts, component registry |
| `cognitive/` | Cognitive processing: interaction tracking, temporal reasoning, flow management, resonance bridging |
| `search/` | RAG-augmented search: query parsing, retrieval, ranking, indexing, chunking, embedding, safety guardrails |
| `mycelium/` | Knowledge federation: persona system, lens discovery, multi-perspective synthesis |
| `unified_fabric/` | Cross-project routing: domain router, Coinbase/Pathways adapters, AI safety bridge, audit |
| `tools/` | CLI utilities: RAG tools, crypto, forensics, dashboards, skill store |
| `infrastructure/` | API gateway, event bus, service mesh, parasite guard, logging/metrics |
| `vection/` | Distributed worker protocols and concurrency coordination |

### Peer Security Modules (outside `src/`)

| Module | Purpose |
|--------|---------|
| `safety/` | AI safety: content detectors, escalation, guardian engine, audit logging, observability |
| `security/` | Network monitoring, forensic analysis, incident response, hardening |
| `boundaries/` | Boundary contracts (ownership transfer), overwatch, refusal logic, transition gate |

These three modules enforce security invariants independently. Never weaken validation, add bypass paths, or remove existing checks. See `.claude/rules/safety.md` and `.claude/rules/behavioral-shield.md`.

### Key Entry Points

- **CLI**: `src/grid/__main__.py` — commands: `serve`, `analyze`, `chat`, `skills`, `process`
- **Mothership API**: `src/application/mothership/main.py` — port 8080
- **API Gateway**: `src/infrastructure/api_gateway/` → `src/main.py` — port 8000
- **RAG Chat**: `grid chat` or `grid run rag` — uses Ollama (default model: ministral-3:3b)

### Test Structure

Tests live in `tests/` with subdirectories per concern: `unit/`, `integration/`, `e2e/`, `api/`, `security/`, `safety/`, `agentic/`, `auth/`, `billing/`, `cognitive/`, `mycelium/`, `resilience/`, `chaos/`, `load/`, `performance/`, `unified_fabric/`. Safety module has its own tests at `safety/tests/`. Boundary tests at `boundaries/tests/`.

### Pytest Configuration

- `asyncio_mode = "auto"` — no need for `@pytest.mark.asyncio`
- Default timeout: 30s per test
- Markers: `unit`, `integration`, `safety`, `security`, `api`, `critical`, `slow`, `flaky`, `redteam`, `smoke`
- `--maxfail=5` and `-m "not scratch and not flaky and not slow"` by default
- `pythonpath = ["src"]` — imports resolve from `src/`

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

## Decision Logging

Architectural decisions go in `docs/decisions/DECISIONS.md` with date, decision, rationale, and alternatives considered.
