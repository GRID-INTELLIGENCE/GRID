---
trigger: always_on
glob:
description: GRID project rules — architecture, standards, safety invariants, and development discipline
---

# THE GRID — Workspace Rules

## Project Identity

**GRID** (Geometric Resonance Intelligence Driver) v2.4.0 — a local-first, privacy-first AI safety and cognitive analysis platform.

- **Author**: Irfan Kabir
- **Repo**: `github.com/caraxesthebloodwyrm02/GRID` (private)
- **Architecture**: Domain-Driven Design + Event-Driven Architecture
- **Python**: 3.13 (strict typing, async-first)
- **Package manager**: `uv` (never bare `pip` or `python`)

## Project Structure

```
src/
  grid/           # Core domain — cognition patterns, agentic system, persistence
  application/    # Application layer — Mothership API, resonance, routers
  cognitive/      # Cognitive processing — pattern analysis
  tools/          # RAG pipeline, MCP servers, CLI utilities
  infrastructure/ # API gateway, service mesh
  vection/        # Worker pool, context interfaces
  unified_fabric/ # Cross-project event bus + AI safety bridge
safety/           # AI safety — detectors, middleware, escalation, audit logging
security/         # Network monitoring, forensic analysis, incident response
boundaries/       # Boundary contracts, overwatch, refusal logic
frontend/         # React 19 + TypeScript + Electron 40 + TailwindCSS 4
tests/            # Pytest test suite (unit, integration, API)
config/           # Configuration management
scripts/          # Development and debugging scripts
```

## Backend Standards

- Python 3.13 — use modern syntax (`match/case`, `type X = ...`, `|` unions)
- Type hints required on all function signatures
- `uv run` prefix for ALL Python CLI commands
- Pydantic v2 for data models (`model_validator`, not `@validator`)
- FastAPI with dependency injection (`Depends()`)
- Async-first: prefer `async def` for I/O operations
- Structured logging with `structlog` — no bare `print()` in production
- Line length: 120 characters (ruff configured)
- Imports: `known-first-party = ["grid", "application", "cognitive", "tools"]`

## Frontend Standards

- React 19 with functional components and hooks only
- TypeScript strict mode — no `any` types, explicit return types on exports
- TailwindCSS 4 for styling (no inline styles, no CSS modules)
- Component variants: CVA + clsx + tailwind-merge
- Icons: `lucide-react` only
- Data fetching: `@tanstack/react-query`
- Routing: `react-router-dom` v7
- Validation: `zod` schemas
- File naming: PascalCase for components, camelCase for utils
- Named exports preferred over default exports

## Safety-Critical Code Rules

> ⚠️ `safety/`, `security/`, `boundaries/` enforce THE GRID's security invariants.

1. **Never** use `eval()`, `exec()`, or `pickle` in production code
2. **Never** bypass authentication checks
3. **Never** remove or weaken existing validation logic
4. **Never** add bypass paths or "dev mode" shortcuts
5. **Always** maintain backward compatibility — these are deployed safety contracts
6. **Always** add tests for changes in safety modules
7. **Always** preserve audit trail integrity
8. **No shared mutable global state** for concurrent users — use per-user/per-session instances
9. **Temporal logic consistency** — one time reference per decision
10. **Sensitive data** (user age, PII) must not leak into logs or responses

## Development Discipline

### The Wall (Session Start Protocol)
Before writing ANY new code, run:
```
uv run pytest -q --tb=short && uv run ruff check src/ safety/ security/ boundaries/
```
If tests fail, fix them before doing anything else.

### Commit Conventions
- One commit, one concern
- Conventional commits: `fix(security):`, `feat(cognition):`, `refactor(rag):`, `test(safety):`, `docs(adr):`
- Always verify tests pass before committing

### Performance Budget
- Full test suite must complete in < 30 seconds
- If exceeded, profile with `--durations=10` and fix before adding more tests

### Complexity Check
Before adding a new abstraction:
1. Does a similar abstraction already exist in the codebase?
2. Can this be done with existing patterns instead?
3. Will this be tested? If not testable, it shouldn't exist.

## Testing Standards

- Markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.safety`
- `asyncio_mode = "auto"` — no need for explicit `@pytest.mark.asyncio`
- Test paths: `tests/` (main), `safety/tests/`, `boundaries/tests/`
- Commands:
  - Full suite: `uv run pytest -q --tb=short`
  - Safety only: `uv run pytest safety/tests -q --tb=short`
  - Boundaries: `uv run pytest boundaries/tests -q --tb=short`
  - Current file: `uv run pytest <file> -q --tb=short -v`

## Key Subsystems

| Subsystem | Path | Purpose |
|:----------|:-----|:--------|
| Safety Pipeline | `safety/` | AI safety enforcement — fail-closed, <50ms pre-check |
| Security | `security/` | Network monitoring, forensics, incident response |
| Boundaries | `boundaries/` | Boundary contracts, overwatch, refusal logic |
| RAG System | `src/tools/rag/` | Local-first hybrid BM25+Vector search with reranking |
| Mothership API | `src/application/mothership/` | FastAPI main application (port 8080) |
| Agentic System | `src/grid/agentic/` | Event-driven case management |
| Cognitive Engine | `src/cognitive/` | 9 cognition patterns analysis |
| Unified Fabric | `src/unified_fabric/` | Cross-project event bus + AI safety bridge |

## Trust Layer Standards (2026)

- **Active Refusal**: Immediate refusal of harmful requests at inference layer
- **Content Provenance**: Watermarking and metadata for safety reports
- **Triadic Safeguarding**: Safety boundaries over autonomy in critical discovery
- **Safety Pact Headers**: `X-Safety-Pact-Awaiting`, `X-Safety-Pact-Concurrency`, `X-Safety-Pact-Sovereignty`
- **Fair Play Rules**: Input-locked stamina, deterministic heat, efficiency-based flow
