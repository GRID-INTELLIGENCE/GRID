# GRID — Geometric Resonance Intelligence Driver

<div align="center">

[![CI](https://github.com/GRID-INTELLIGENCE/GRID/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/GRID-INTELLIGENCE/GRID/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/grid-intelligence.svg)](https://pypi.org/project/grid-intelligence/)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/badge/linter-ruff-261230.svg)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Local-First AI · Privacy-First · Production-Ready**

</div>

## Engineering at a Glance

Built primarily by a solo engineer over 6 months — from blank templates to a production-hardened framework with CI, security layers, and full test infrastructure.

| What | Evidence |
|------|----------|
| **Codebase scale** | 1,490+ Python files, 200K+ lines, 9 distributable wheel packages |
| **Test discipline** | 4,490+ test functions, ≥75% coverage, 30s performance budget |
| **CI rigor** | 7-stage GitHub Actions pipeline: secrets scan → lint → smoke → security → test → integration → build |
| **Security depth** | 3 independent security modules (safety, security, boundaries), sealed-envelope HMAC-SHA256 transfer gate, admission gate with ethical enforcement, zero-trust boundary contracts |
| **API architecture** | FastAPI + 14-layer middleware chain, dual event bus (Redis + in-memory fallback), circuit breaking, rate limiting |
| **Code quality** | 0 ruff lint errors across 1,490+ files, strict type hints, conventional commits |
| **Resilience patterns** | Published separately as [GRID-APIGUARD](https://pypi.org/project/GRID-APIGUARD/) — circuit breaking + rate limiting + retry with 100% test coverage |

The architecture is domain-driven with event-driven agentic workflows — not a monolith, not a microservice explosion. Each package has clear boundaries, its own tests, and ships as an independent wheel.

For clients: If you're evaluating this repo as part of a proposal, the CI pipeline, CHANGELOG, and test structure tell the story better than any portfolio page. The code is the portfolio.
---

GRID is a **privacy-first code intelligence framework** that helps you understand complex codebases using local AI models. Your code never leaves your machine.

```bash
pip install grid-intelligence
grid --help
```

Or install from source for development:

```bash
git clone https://github.com/GRID-INTELLIGENCE/GRID.git
cd GRID
uv sync --group dev --group test
uv run grid --help
```

> For contributor setup see [docs/INSTALLATION.md](docs/INSTALLATION.md).
> Environment template: `config/environment/.env.example`.

---

## Why GRID?

| Problem | GRID's Answer |
|---------|---------------|
| Developers spend **40 %** of time *reading* code | Semantic analysis reduces onboarding to minutes |
| Cloud AI tools require sending source code off-machine | **Everything runs locally** — Ollama + ChromaDB |
| Text search can't answer *"why"* or *"how"* | 9 Cognition Patterns map structure, flow, and intent |
| Enterprise tools are expensive | Free tier with MIT license |

---

## At a Glance

| Metric | Value |
|--------|-------|
| **Python** | 3.13+ |
| **Source files** | 1,490+ |
| **Tests** | 4,490+ test functions |
| **Lint errors** | 0 (ruff clean) |
| **Coverage** | ≥ 75 % |
| **RAG precision lift** | +33–40 % |
| **Architecture** | DDD + Event-Driven |
| **Package manager** | [uv](https://docs.astral.sh/uv/) |

---

## Core Capabilities

- **9 Cognition Patterns** — Flow · Spatial · Rhythm · Color · Repetition · Deviation · Cause · Time · Combination
- **Local-First RAG** — ChromaDB + Ollama. Optional cloud hybrid (OpenAI / Anthropic / Gemini) via `RAG_LLM_MODE=external`
- **Cognitive Decision Support** — *Light of the Seven* architecture for bounded rationality
- **Agentic System** — Event-driven case management (receptionist → lawyer → executor)
- **Transition Gate** — Sealed-envelope HMAC-SHA256 handshake for cross-partition artifact transfers
- **Search with Guardrails** — Auth, rate limiting, input sanitization, admin-gated schema routes
- **Unified Fabric** — Async event bus and distributed AI Safety bridge
- **Authentication & Billing** — JWT + bcrypt, token revocation, tier-based usage tracking

---

## Quick Start (Contributors)

```bash
uv sync --group dev --group test   # Creates .venv, installs everything
uv run pytest                      # Run tests
uv run ruff check .                # Lint
uv run python -m grid --help       # CLI
```

> [!IMPORTANT]
> Use `uv add` to manage packages — not `pip install`. See `pyproject.toml` and `uv.lock`.

<details>
<summary>Managing dependencies</summary>

```bash
uv add <package>                   # Runtime dependency
uv add --group dev <package>       # Dev-only
uv lock                            # Regenerate lockfile
uv sync                            # Sync .venv to lockfile
```

The `.venv/` folder is disposable — delete it and `uv sync` recreates it.

</details>

---

## Project Structure

```
GRID/
├── src/                       # Source code (9 wheel packages)
│   ├── grid/                  #   Core intelligence engine
│   ├── application/           #   FastAPI (Mothership API)
│   ├── cognitive/             #   Cognitive architecture
│   ├── tools/                 #   RAG, utilities
│   ├── search/                #   Search service + guardrails
│   ├── mycelium/              #   Comprehension frontend
│   ├── infrastructure/        #   Infra adapters
│   ├── unified_fabric/        #   Async event bus + safety bridge
│   └── vection/               #   Motion & perception
├── tests/                     # Test suite (4490+ test functions)
├── safety/                    # GUARDIAN rule engine, PII privacy
├── security/                  # Network interceptor, forensics
├── boundaries/                # Boundary engine, transition gate
├── config/                    # All configuration & structured data
│   ├── deploy/                #   Railway, Render deployment configs
│   ├── contracts/             #   OpenAPI specs
│   └── prompts/               #   Prompt templates
├── schemas/                   # JSON schemas (OpenAPI, telemetry, …)
├── scripts/                   # Build, CI, and demo scripts
├── docs/                      # Documentation (architecture, guides, ADRs)
│   ├── reports/               #   Audit & analysis reports
│   └── checkpoints/           #   Session checkpoints
├── landing/                   # Marketing site (Netlify)
├── frontend/                  # Web client
└── pyproject.toml             # Project config (uv)
```

---

## What's New

### v2.8.0 — Admission Gate & Entity Persistence (March 2026)

- **Admission Gate** — Top-of-stack ethical participation enforcement with 6 sequential gates, 3-tier penalty escalation, and entity attribution
- **Entity Persistence** — SQLite-backed entity state with async CRUD and startup hydration
- **Frontend Dashboard** — Admission page with live stats, policy billboard, bannered entities table
- **REST API** — 7 endpoints under `/admission/*` with admin-protected penalty management

<details>
<summary><b>Earlier releases</b></summary>

**v2.7.0** — Security Hardening & CI Hygiene: search guardrails, transition gate, API attack surface guardrails, CI audit gates, cross-platform path traversal protection

**v2.6.x** — Mycelium Frontend, wheel packaging, version/changelog CI gate

**v2.5.0** — Environmental Intelligence (Le Chatelier homeostatic middleware), Round Table multi-agent facilitator

**v2.4.0** — 664 → 0 lint errors, StrEnum modernization (122 classes)

**v2.3.0** — Ruff formatter consolidation, GUARDIAN engine hardening

**January 2026** — Auth & billing, advanced RAG (+33-40 % precision), Unified Fabric, Databricks scaffold

</details>

---

## Development Workflow

### CI Pipeline (GitHub Actions)

| Job | Purpose |
|-----|---------|
| **Secrets Scan** | Version/changelog gate, no-debug gate, secret detection |
| **Lint** | `ruff check` + `ruff format --check` |
| **Smoke Test** | Fast sanity checks |
| **Security Scan** | Attack surface & guardrail tests |
| **Test** | Unit + integration + API tests with coverage |
| **Build Package** | Validates all 9 wheel packages build cleanly |
| **Integration Tests** | Cross-module integration |

### Quality Gates

Before merging to `main`:

1. `uv run ruff check .` — zero errors
2. `uv run pytest tests/ -q --tb=short` — all passing
3. `pyproject.toml` version matches top `CHANGELOG.md` entry
4. No `DEBUG=true` or `ENABLE_DEV_TOKEN` in production paths
5. No untracked files in `src/` or `tests/`

### Tooling

| Tool | Command |
|------|---------|
| **Ruff** (lint + format) | `uv run ruff check .` / `uv run ruff format .` |
| **Mypy** (types) | `uv run mypy src/grid/ src/application/` |
| **Pytest** (tests) | `uv run pytest tests/` |

---

## Privacy & External LLM

GRID is **local-first by default**. No data leaves your machine unless you explicitly opt in.

| Variable | Purpose |
|----------|---------|
| `RAG_LLM_MODE=external` | Switch RAG to external API |
| `RAG_LLM_PROVIDER` | `openai`, `anthropic`, or `gemini` |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GEMINI_API_KEY` | Provider key |

> When using external providers, prompts and responses are sent to the chosen provider.

---

## The Story

GRID began in **November 2025** as blank templates and empty journals. By December it became a *system* — domain-driven architecture, security foundations, and a core principle:

> *When the environment is noisy, separate signal from noise, compress it into a structured core, and keep moving.*

There's a state in the pattern engine called **MIST** — *"high confidence that we don't know."* That epistemic humility, inspired by Carl Jung, shapes everything we build.

```
Nov 2025 → First commit. Blank templates.
Dec 2025 → Architecture cleanup. Security foundation. DDD.
Jan 2026 → Cognitive layer. RAG optimization. Production hardening.
Feb 2026 → 540+ files. Environmental Intelligence. Mycelium. v2.6+.
Mar 2026 → 1270+ files. Admission gate. Entity persistence. v2.8.0.
Apr 2026 → 1490+ files. 4490+ tests. TS 6.0, strict asyncio, CI green.
```

**GRID is built by someone who cares about doing things right — principled, not perfect.**

---

## Documentation

| Area | Link |
|------|------|
| **What Can I Do?** | [`docs/WHAT_CAN_I_DO.md`](docs/WHAT_CAN_I_DO.md) |
| **Architecture** | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) |
| **Security** | [`docs/security/SECURITY_ARCHITECTURE.md`](docs/security/SECURITY_ARCHITECTURE.md) |
| **Skills & RAG** | [`docs/SKILLS_RAG_QUICKSTART.md`](docs/SKILLS_RAG_QUICKSTART.md) |
| **Agentic System** | [`docs/AGENTIC_SYSTEM_USAGE.md`](docs/AGENTIC_SYSTEM_USAGE.md) |
| **Event Architecture** | [`docs/EVENT_DRIVEN_ARCHITECTURE.md`](docs/EVENT_DRIVEN_ARCHITECTURE.md) |
| **Pipeline Runbook** | [`docs/release/pipeline-runbook.md`](docs/release/pipeline-runbook.md) |
| **Contributing** | [`CONTRIBUTING.md`](CONTRIBUTING.md) |

---

<details>
<summary><b>FAQ</b></summary>

**What is GRID?** — A privacy-first, local-first tool that helps you understand any codebase using local AI models.

**How is this different from Copilot?** — Copilot helps you *write* code. GRID helps you *understand* code.

**Does my code stay local?** — Yes. Zero network requests, no API keys needed, works offline.

**Languages supported?** — Python, JS/TS, Java, Go, Rust, C/C++, Ruby, PHP, C#.

**System requirements?** — 8 GB RAM minimum (16 GB recommended), Python 3.13+, Windows / Mac / Linux.

**What are the 9 Cognition Patterns?** — Flow, Spatial, Rhythm, Color, Repetition, Deviation, Cause, Time, Combination — a unique framework for understanding complex systems.

**Is the architecture original?** — Yes. While inspired by seL4, Fuchsia, and cognitive science, the 9 Cognition Patterns and Geometric Resonance metaphor are proprietary innovations.

</details>

## License

MIT — see [LICENSE](LICENSE).
