# THE GRID — Geometric Resonance Intelligence Driver

> Named after Daft Punk's "The Grid" (Tron Legacy OST, remixed by Pyrotechnique).
> Local-first, privacy-first AI codebase analysis framework.
> Built by Irfan Kabir. Principled, not perfect.

## What This Project Is

THE GRID explores complex systems through 9 cognition patterns (Flow, Spatial, Rhythm, Color, Repetition, Deviation, Cause, Time, Combination). It uses local AI (Ollama + ChromaDB) with zero external API calls. Your code never leaves your machine.

**Core mission**: Serve people who cannot communicate with their loved ones.

## Monorepo Structure

```
e:\grid/                        ← Workspace root (uv workspace)
├── work/GRID/                  ← Main GRID application (Python backend)
│   ├── src/grid/               ← Core intelligence (cognition, agentic, RAG)
│   ├── src/application/        ← FastAPI applications (mothership API)
│   ├── src/cognitive/          ← Cognitive architecture (Light of the Seven)
│   ├── src/tools/              ← Dev tools (RAG CLI, utilities)
│   ├── src/unified_fabric/     ← Event bus + AI Safety bridge
│   ├── tests/                  ← 283+ tests
│   └── landing/                ← Netlify landing page
├── frontend/                   ← Electron + Vite + React 19 + TypeScript
├── safety/                     ← AI safety: detectors, escalation, guardian, audit
├── security/                   ← Network monitoring, forensics, incident response
├── boundaries/                 ← Boundary contracts, overwatch, refusal logic
├── config/                     ← Denylists, schemas, env configs
├── scripts/                    ← PowerShell/Python automation scripts
├── docs/                       ← Guides, reports, reference docs
└── archive/                    ← Historical files (do not modify)
```

## Tech Stack

| Layer | Stack |
|-------|-------|
| **Backend** | Python 3.13, FastAPI, Pydantic v2, SQLAlchemy (async), Celery, Redis |
| **AI/ML** | Ollama (local LLM), ChromaDB, sentence-transformers, scikit-learn, networkx |
| **Frontend** | React 19, TypeScript, Vite 7, Electron 40, TailwindCSS 4, Storybook 10 |
| **Testing** | pytest (backend), Vitest (frontend), pytest-asyncio, pytest-cov |
| **Quality** | ruff (linter), black (formatter), mypy (type checker), ESLint + Prettier |
| **Package Mgmt** | `uv` for Python (NOT pip), npm for frontend |
| **Infra** | MCP servers, OpenTelemetry, Prometheus, structlog |

## Essential Commands

```bash
# Python environment (ALWAYS use uv, never pip)
uv sync --all-groups              # Install/sync all deps
uv run pytest -q --tb=short       # Run all tests
uv run pytest work/GRID/tests -q  # GRID tests only
uv run ruff check work/ safety/   # Lint
uv run black work/ safety/        # Format
uv run mypy work/GRID/src/grid    # Type check

# Frontend
cd frontend && npm run dev        # Dev server (Vite + Electron)
cd frontend && npm run lint       # ESLint + typecheck
cd frontend && npm test           # Vitest

# API server
uv run python -m application.mothership.main

# Makefile shortcuts (from root)
make test          # All tests
make lint          # ruff + mypy
make format        # black + ruff fix
make audit         # pip-audit + bandit
make clean         # Remove caches
```

## Core Principles (NON-NEGOTIABLE)

1. **No `eval()`, `exec()`, or `pickle`** — ever, anywhere, for any reason
2. **No authentication bypass** — every request must be authenticated, no dev-mode exceptions
3. **All actions are attributable** — complete audit trails, every operation logged with user_id
4. **Fair resource allocation** — logged, auditable, no favoritism
5. **Staff protection** — burnout detection, workload visibility

## Coding Conventions

- **Python**: Line length 120, type hints required (`disallow_untyped_defs = true`), ruff rules `E,F,B,I,W,UP`
- **Imports**: isort with known-first-party `grid, application, cognitive, tools, boundaries, safety, security`
- **Frontend**: Strict TypeScript, CVA + clsx + tailwind-merge for component variants
- **Commits**: Descriptive messages, reference related modules
- **Tests**: Mark with `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.safety`, etc.

## Anti-Patterns (DO NOT)

- ❌ Use `pip install` — use `uv sync` or `uv add`
- ❌ Create auth bypass or "dev mode" shortcuts
- ❌ Use `eval()`, `exec()`, `pickle`, or string-based code execution
- ❌ Modify files in `archive/` — that's historical record
- ❌ Weaken safety checks in `safety/`, `security/`, or `boundaries/`
- ❌ Use external AI APIs — everything runs locally via Ollama
- ❌ Hardcode secrets or use realistic-looking dummy keys in tests

## Discipline Routines

```bash
# Daily — before any new work
make wall              # Tests + lint must pass

# Weekly — Friday
make weekly            # Dep audit + bandit + perf budget + invariant scan

# Per-decision
# Append to docs/decisions/DECISIONS.md (see TEMPLATE.md)
```

## Where to Find Things

- Architecture docs → `work/GRID/docs/ARCHITECTURE.md`
- Decision log → `docs/decisions/DECISIONS.md`
- Security audit → `work/GRID/SECURITY_AUDIT_REPORT.md`
- Security review → `safety/SECURITY_REVIEW_2026_02.md`
- Core principles → `work/GRID/CORE_PRINCIPLES.md`
- Safety deployment → `safety/DEPLOYMENT_GUIDE.md`
- Frontend components → `frontend/src/`
- Config schemas → `config/schemas/`
- Claude rules → `.claude/rules/` (backend, frontend, safety, discipline)
- VSCode tasks → `.vscode/tasks.json` (daily/weekly routines as runnable tasks)

## Developer Context

For comprehensive structured context about the developer, their projects, environment, philosophy, and working style, see `.claude/user-profile.json`.
