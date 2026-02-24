# Getting Started with GRID

This guide will help you get up and running with GRID (Geometric Resonance Intelligence Driver).

## Prerequisites

- **Python 3.13** (required — GRID uses PEP 695 syntax)
- **Git** 2.30+
- **uv** (recommended) — install from [docs.astral.sh/uv](https://docs.astral.sh/uv/)

## Installation

### For End Users (PyPI)

```bash
pip install grid-intelligence
grid --help
```

### For Contributors

```bash
# Clone the repository
git clone https://github.com/GRID-INTELLIGENCE/GRID.git
cd GRID

# Install with uv (creates .venv, installs all deps from lockfile)
uv sync --group dev --group test

# Verify
uv run pytest -q --tb=short
uv run grid --help
```

## Configuration

### Environment Variables

Copy the example environment file and edit it:

```bash
cp .env.example .env
```

Key settings:

```env
ENVIRONMENT=development
DATABASE_URL=sqlite:///./app.db
SECRET_KEY=change-this-to-random-string
API_HOST=0.0.0.0
API_PORT=8000
```

### Database Setup

GRID supports SQLite (default), PostgreSQL, and MySQL:

```bash
# Run migrations
uv run alembic upgrade head
```

## Development Workflow

### Common Commands

```bash
# Start the API server
uv run grid serve

# Run tests
uv run pytest -q --tb=short

# Run linter
uv run ruff check work/ safety/ security/ boundaries/

# Interactive RAG chat (requires Ollama)
uv run grid chat
```

### Session Start Protocol

Before writing any new code, always verify the wall holds:

```bash
uv run pytest -q --tb=short && uv run ruff check work/ safety/ security/ boundaries/
```

## Project Structure

```
GRID/
├── src/
│   ├── grid/              # Core runtime (API, CLI, config, agentic)
│   ├── application/       # Mothership layer (middleware, skills, resonance)
│   ├── cognitive/         # Cognitive engine (patterns, temporal, XAI)
│   └── tools/             # RAG, cognitive tooling
├── safety/                # AI safety: detectors, escalation, audit
├── security/              # Network monitoring, forensics
├── boundaries/            # Boundary contracts, overwatch, refusal
├── frontend/              # React + TypeScript + Electron
├── tests/                 # Test suite
├── docs/                  # Documentation
└── .github/               # CI/CD workflows
```

## Next Steps

1. Read the [INSTALLATION.md](INSTALLATION.md) for platform-specific details
2. Check [CONTRIBUTING.md](../CONTRIBUTING.md) for contribution guidelines
3. Explore the `examples/` directory for usage samples
4. Visit the [live demo](https://grid-intelligence.netlify.app)
