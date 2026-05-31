# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

GRID (Geometric Resonance Intelligence Driver) v2.8.0 — local-first, privacy-first AI safety and code-intelligence framework. Python 3.13, FastAPI, SQLAlchemy, ChromaDB + Ollama. DDD + event-driven agentic workflows. Solo-authored. Authoritative agent rules also live in `.agent/rules/grid-rules.md`, `AGENTS.md`, and `.github/copilot-instructions.md`.

## Commands

```bash
# Environment (uv only — never bare pip / python / venv)
uv sync --group dev --group test          # standard setup
uv sync --group finetuning                # optional: torch/transformers for RAG intent classifier
                                          # (without it, intent classification falls back to rules)

# Session start — run before writing any new code ("The Wall")
uv run pytest -q --tb=short && uv run ruff check src/ safety/ security/ boundaries/

# Tests (CI runs these slices, not the whole tree)
make test                                 # core: tests/unit tests/integration tests/security tests/api
uv run pytest tests/unit/ tests/security/ tests/api/ -v --tb=short -x   # CI unit stage
uv run pytest safety/tests -q --tb=short
uv run pytest boundaries/tests -q --tb=short
uv run pytest tests/unit/test_x.py::test_fn -v                          # single test

# Lint / format / type-check
uv run ruff check .            # or: make lint  (ruff + mypy)
uv run ruff format . && uv run ruff check . --fix
uv run mypy src/grid/ src/application/ src/tools/ src/search/ src/cognitive/ src/mycelium/

# Run services
uv run python -m application.mothership.main   # Mothership API, port 8080
uv run python -m src.main                       # API Gateway, port 8000
uv run python -m grid --help                    # CLI (serve/analyze/chat/skills/process/run)

# Frontend (Vitest — never Jest flags like --runInBand)
make frontend-typecheck && make test-frontend
cd frontend && npm run dev

# Production guard (CI gate)
make guard-no-debug    # asserts no DEBUG / ENABLE_DEV_TOKEN in production
```

## Pytest configuration (non-obvious)

- `pythonpath = ["src"]`, `--import-mode=importlib`, `testpaths = tests safety/tests boundaries/tests`.
- `asyncio_mode = "strict"` — every async test needs explicit `@pytest.mark.asyncio`.
- `strict_markers = true`. Default addopts exclude `scratch`, `flaky`, `slow`: `-m "not scratch and not flaky and not slow"`, plus `--maxfail=5`, `--durations=10`.
- Markers: `unit`, `integration`, `safety`, `security`, `api`, `critical`, `redteam`, `smoke`, `database`, `slow`, `flaky`, `scratch`.
- Coverage floor 75%. Full suite performance budget < 30s — profile with `--durations=10` before adding tests.

## Architecture

Strict layer boundaries — Core has no dependency on upper layers; Services depend on Core but not Application; API orchestrates Services and never touches the DB directly.

```
CLI (grid) → API Gateway (:8000) → Mothership API (:8080)
                                         │
        grid/ ─ cognitive/ ─ search/ ─ mycelium/ ─ unified_fabric/
```

Source packages (`src/`, the 9 shipped wheel packages):

| Package | Role |
|---------|------|
| `grid/` | Core: 9 cognition patterns, agentic case system, auth, billing, skills, persistence |
| `application/` | Mothership FastAPI app (versioned routers), resonance, canvas |
| `cognitive/` | 9-pattern analysis: Flow, Spatial, Rhythm, Color, Repetition, Deviation, Cause, Time, Combination |
| `search/` | Local RAG: chunking, hybrid BM25+vector retrieval, reranking, guardrails |
| `tools/` | RAG CLI/pipeline, MCP servers, forensics, dashboards |
| `mycelium/` | Knowledge federation, persona/lens synthesis |
| `unified_fabric/` | Cross-domain async event bus + AI safety bridge (SAFETY, GRID, COINBASE, PATHWAYS) |
| `infrastructure/` | API gateway (circuit breaker, routing), event bus, parasite guard, metrics |
| `vection/` | Distributed worker protocols |

**Peer security modules (outside `src/`, enforce invariants independently):** `safety/` (GUARDIAN rule engine, detectors, escalation, PII engine, audit log), `security/` (network interceptor, forensics), `boundaries/` (consent/refusal contracts, overwatch, sealed-envelope HMAC-SHA256 transfer gate).

**Dual event bus:** infrastructure `EventBus` (priority + correlation/causation, Redis with in-memory fallback) and unified-fabric `DynamicEventBus` (domain-aware routing). Mothership runs a 14-layer middleware chain (RequestID → Logging → Timing → ErrorHandling → SecurityHeaders → UsageTracking → RateLimit → Safety → DRT → Accountability → ParasiteGuard → Router); order matters, SafetyMiddleware mandatory in production.

## Local-first (non-negotiable)

Never suggest external APIs (OpenAI, Anthropic, etc.) unless explicitly requested. Default to local Ollama (`nomic-embed-text-v2-moe` embeddings, `ministral`/`gpt-oss-safeguard` LLM); RAG context stays in `.rag_db/` (ChromaDB).

## Safety-critical rules

`safety/`, `security/`, `boundaries/` are deployed safety contracts. Never use `eval()`/`exec()`/`pickle`; never bypass auth or weaken existing validation; never add bypass paths or "dev mode" shortcuts. Any change here needs tests plus a rollback plan, and must preserve audit-trail integrity and backward compatibility.

Attack-surface controls (see `docs/API_ATTACK_SURFACE_GUARDRAILS_AND_TODOS.md`): agentic routes require `RequiredAuth`, admin routes `AdminAuth`. Body limits — Mothership 10MB, Safety 50KB, KB 5MB, RAG Chat 1MB. Production returns generic 500 (no `str(e)` to client). Outbound HTTP to user/config-supplied URLs must pass `application.mothership.utils.validate_url_allowlist` (SSRF).

## Debugging windows (do not widen scope unless a contract forces it)

Treat the repo as four surfaces: **Python service** (`src/<domain>` + matching `tests/<domain>`), **Frontend renderer** (`frontend/src`, start `make frontend-typecheck`), **Electron** (`frontend/electron`, `make electron-build`), **Landing** (`landing/`, `make landing-validate`). Reproduce in one window, run its smallest gate, fix the failing layer, then widen.

## CI pipeline (`.github/workflows/ci.yml`)

secrets-scan → lint (ruff + mypy) → security (bandit, pip-audit, npm audit) → smoke-test → test → integration → build → schema-validation → mcp-security. Includes a git-hygiene gate (no untracked files in `src/` or `tests/`) and a no-DEBUG-in-production gate.

## Conventions

- Conventional commits, one concern each: `feat(scope):`, `fix(scope):`, `test(scope):`, `docs(scope):`.
- Type hints required on all signatures; line length 120; ruff only; `structlog` (no `print()` in runtime paths); Pydantic v2 (`model_validator`).
- Architectural decisions → `docs/decisions/DECISIONS.md`.
- `.claude/` and `data/` are gitignored but contain tracked files — staging them needs `git add -f` (or `git add -u` for already-tracked modifications).
