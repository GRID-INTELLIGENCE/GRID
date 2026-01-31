# GRID - Geometric Resonance Intelligence Driver

[![Tests](https://github.com/irfankabir02/GRID/actions/workflows/ci-test.yml/badge.svg?branch=main)](https://github.com/irfankabir02/GRID/actions/workflows/ci-test.yml)
[![Quality](https://github.com/irfankabir02/GRID/actions/workflows/ci-quality.yml/badge.svg?branch=main)](https://github.com/irfankabir02/GRID/actions/workflows/ci-quality.yml)
[![Codecov](https://codecov.io/gh/irfankabir02/GRID/branch/main/graph/badge.svg)](https://codecov.io/gh/irfankabir02/GRID)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Overview

GRID (Geometric Resonance Intelligence Driver) is a comprehensive framework for exploring and understanding complex systems through:

- **Geometric Resonance Patterns**: Core intelligence engine with 9 cognition patterns (Flow, Spatial, Rhythm, Color, Repetition, Deviation, Cause, Time, Combination)
- **Cognitive Decision Support**: Light of the Seven cognitive architecture for bounded rationality and human-centered AI
- **Local-First RAG**: Retrieval-Augmented Generation with ChromaDB + Ollama (no external APIs)
- **Intelligent Skills Ecosystem**: Self-organizing framework with automated discovery, persistent intelligence, and performance guarding (Phases 1-4)
- **Event-Driven Agentic System**: Complete case management workflow with continuous learning
- **Domain-Driven Design**: Professional architectural patterns with service layer decoupling

## 🚀 What's New (January 2026)

### Major Enhancements:

- ✅ **Security Hardening** - Comprehensive path traversal protection and validation
- ✅ **Advanced RAG System** - 4-phase optimization with semantic chunking, hybrid search, cross-encoder reranking
- ✅ **Enhanced Testing** - 137+ tests passing with 15/15 Unified Fabric cases
- ✅ **Windows Compatibility** - Fixed pre-commit hooks and cross-platform path handling
- ✅ **Performance Monitoring** - Real-time system metrics and optimization
- ✅ **Dynamic Unified Fabric** - Event-driven architecture with distributed AI Safety across E:/
- ✅ **Databricks Scaffold** - Native Coinbase analytics pipeline architecture

### New Capabilities:

- **Path Traversal Protection**: Robust security validation for all file operations
- **Semantic Chunking**: Context-aware document splitting for better RAG coherence
- **Hybrid Search**: BM25 + Vector fusion for improved recall and precision
- **Cross-Encoder Reranking**: 33-40% precision improvement with ms-marco-MiniLM-L6-v2
- **Evaluation Metrics**: Automated Context Relevance scoring and quality tracking
- **Distributed AI Safety**: `AISafetyBridge` for cross-project safety validation (wellness_studio → E:/)
- **Automatic Revenue Pipeline**: End-to-end signal-to-execution flow with multi-system auditing

## Installation

**This repo uses UV as the Python venv/package manager.** Do not use `python -m venv` or `pip` directly—use UV for all venv and package operations.

### Quick setup with UV (recommended)

```powershell
Set-Location e:\grid
uv venv --python 3.13 --clear
.\.venv\Scripts\Activate.ps1
uv sync --group dev --group test
```

> [!NOTE]
> When running `python -m grid` manually from the root, ensure the `src` directory is in your `PYTHONPATH`:
> `$env:PYTHONPATH="src"; python -m grid --help`

### Legacy setup (not recommended)

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\Activate.ps1
pip install -e .
```

## UV usage (per-repo)

See `docs/UV_USAGE.md` for full copy-paste commands. Quick root setup with uv:

```powershell
Set-Location e:\grid
uv venv --python 3.13 --clear
.\.venv\Scripts\Activate.ps1
uv sync --group dev --group test
```

## Key Components

### Core Intelligence

- **Circuits**: Constraint-based pathway lighting system
- **Physics**: Spacetime geometry framework for non-Euclidean grids
- **RAG**: Retrieval-Augmented Generation system (ChromaDB + Ollama)
- **Cognitive Layer**: Decision support, mental models, and navigation (Light of the Seven)
- **Resonance API**: Real-time activity processing with adaptive feedback

### New Systems (2026)

- **🤖 Agentic System**: Event-driven case management with continuous learning
- **🏗️ DDD Architecture**: Domain-driven design with service layer decoupling
- **📁 Organized Structure**: Clean root directory with logical organization
- **🏗️ Unified Fabric**: High-performance async event bus and distributed safety layer
- **🐳 Docker Stack**: Health checks and Windows compatibility

### Visualization & Tools

- **Visualization**: Interactive data visualization tools
- **Arena (The Chase)**: Simulation + referee lab with diagnostics CLI
- **Workspace**: MCP servers and development tools

## Project Structure (2026)

The project has been reorganized with a clean, maintainable structure:

### 📁 Root Directory (Essential Files Only)

```
e:\grid/
├── src/                    # All source code
├── tests/                  # Test suite
├── docs/                   # Core documentation
├── config/                 # Configuration files
├── scripts/                # Build and development scripts
├── docker/                 # Docker configurations
├── tools/                  # Development tools
├── workspace/              # MCP workspace
└── pyproject.toml         # Project configuration
```

### 📁 New Organized Directories

```
├── dev/                    # Development files
│   ├── debug/             # Debug scripts
│   ├── patches/           # Patch files
│   ├── logs/              # Development logs
│   └── temp/              # Temporary files
├── reports/                # Reports and analysis
│   ├── analysis/          # Analysis reports
│   ├── integration/       # Integration test failures
│   ├── checkpoints/       # Project checkpoints
│   └── daily/             # Daily reports
└── docs-ext/              # Extended documentation
    ├── guides/            # Implementation guides
    └── workflows/         # Workflow documentation
```

### 📦 Source Code Structure

```
src/
├── grid/                   # Core intelligence package
│   ├── agentic/           # Event-driven agentic system
│   ├── context/           # User context management
│   ├── workflow/          # Workflow orchestration
│   └── io/                # Input/output handling
├── application/           # FastAPI applications
├── tools/                  # Development tools (RAG, utilities)
├── cognitive/              # Cognitive architecture
└── unified_fabric/         # Event-driven core & AI Safety bridge
```

## Skills + RAG (Quickstart)

**Local-First RAG System** (ChromaDB + Ollama - no external APIs):

```bash
# Query knowledge base
python -m tools.rag.cli query "How does pattern recognition work?"

# Index/rebuild documentation
python -m tools.rag.cli index docs/ --rebuild --curate

# List available skills (Auto-discovered)
python -m grid skills list

# Run a skill with JSON args (Performance-tracked)
python -m grid skills run transform.schema_map --args-json '{"text":"...", "target_schema":"resonance"}'
```

See [`docs/INTELLIGENT_SKILLS_SYSTEM.md`](docs/INTELLIGENT_SKILLS_SYSTEM.md) for details on the automated discovery and management layer.

### Resonance API

The Resonance API provides a "canvas flip" checkpoint for mid-process alignment:

```bash
# Start the server
python -m application.mothership.main

# Call the definitive endpoint
curl -X POST http://localhost:8080/api/v1/resonance/definitive \
  -H "Content-Type: application/json" \
  -d '{"query": "Where do these features connect?", "progress": 0.65}'

# Process activity with cognitive support
curl -X POST http://localhost:8080/api/v1/resonance/process \
  -H "Content-Type: application/json" \
  -d '{"query": "create a new service", "activity_type": "code"}'
```

### 🤖 Agentic System (NEW)

The Event-Driven Agentic System implements a receptionist-lawyer-client workflow for structured case processing:

```bash
# Create a case (receptionist intake)
curl -X POST http://localhost:8080/api/v1/agentic/cases \
  -H "Content-Type: application/json" \
  -d '{"raw_input": "Add contract testing to CI pipeline"}'

# Execute case (lawyer processes case)
curl -X POST http://localhost:8080/api/v1/agentic/cases/{case_id}/execute \
  -H "Content-Type: application/json" \
  -d '{"agent_role": "Executor", "task": "/execute"}'

# Get agent experience summary
curl http://localhost:8080/api/v1/agentic/experience
```

**Event Flow:**

1. **CaseCreated** → Receptionist receives and categorizes input
2. **CaseCategorized** → Case is filed with priority and metadata
3. **CaseReferenceGenerated** → Reference documents and workflow created
4. **CaseExecuted** → Agent processes the case with role-based execution
5. **CaseCompleted** → Case is completed with outcome and experience data

See [`docs/AGENTIC_SYSTEM_USAGE.md`](docs/AGENTIC_SYSTEM_USAGE.md) for complete usage instructions and [`docs/AGENTIC_SYSTEM.md`](docs/AGENTIC_SYSTEM.md) for system documentation.

### 🕸️ Unified Fabric & Watchmaker Mechanism (NEW)

The Unified Fabric provides a high-performance, asynchronous event bus and a distributed AI Safety bridge that connects GRID cognitive analysis with Coinbase financial execution.

**Key Features:**
- **AISafetyBridge**: Distributes safety validation from `wellness_studio` to all `E:/` projects.
- **Async Router Hooks**: De-blocks synchronous GRID routers with non-blocking safety checks.
- **Revenue Pipeline**: Automated flow from trading signals to portfolio execution with multi-system auditing.

**Run the Watchmaker Scenario:**
```powershell
# Demonstrates the full dynamic flow (Analysis -> Safety -> Trading -> Revenue)
python example_scenario.py
```

See `src/unified_fabric/` for implementation details.

## 🐳 Docker Stack (NEW)

### Health Check System

All MCP servers now include HTTP health endpoints for Docker monitoring:

```bash
# Check all MCP server health
curl http://localhost:8080/health

# Individual server health
curl http://localhost:8081/health  # Database MCP
curl http://localhost:8082/health  # Filesystem MCP
curl http://localhost:8083/health  # Memory MCP
```

### Docker Compose

```bash
# Development stack
docker-compose -f docker/compose/docker-compose.yml up -d

# Production stack with security
docker-compose -f docker/compose/docker-compose-secure.yml up -d

# Override configuration
docker-compose -f docker/compose/docker-compose.override.yml up -d
```

## Development Workflow

### CI/CD & Monitoring

We use GitHub Actions for CI/CD with comprehensive validation:

```bash
# Watch the latest CI run
make watch-ci

# Watch the latest Docker build
make watch-docker
```

### Pre-Push Validation

Optimized pre-push hook ensures:

1. **Brain Integrity**: Validates `seed/topics_seed.json` structure
2. **Core Logic**: Runs fast unit tests (122+ passing)
3. **Hygiene**: Checks for large artifacts

### Tooling

- **Ruff**: Fast Python linter (`uv run ruff check .`)
- **Black**: Code formatter (`uv run black .`)
- **Pyright**: Type checker (`uv run pyright .`)
- **Pytest**: Test runner (`uv run pytest tests/`)

**VS Code Tasks** (Ctrl+Shift+P → "Run Task"):

- `🧪 Tests · Run All` - Full test suite with coverage
- `✅ IDE · Validate Context` - Environment validation
- `🔍 RAG · Query` - Query knowledge base
- `📊 RAG · Index Docs` - Rebuild documentation index
- `🛰️ PULSAR · Dashboard` - System vitals dashboard

## Performance & Quality

### Test Coverage

- **137+ tests passing** across unit, integration, and agentic systems
- **100% pass rate** for new Unified Fabric core modules
- **Comprehensive coverage** for core intelligence, agentic system, and DDD patterns
- **CI/CD pipeline** with automated validation and deployment

### Performance Benchmarks

| Metric        | Before        | After         | Improvement |
| :------------ | :------------ | :------------ | :---------- |
| `cache_ops`   | 1,446 ops/sec | 7,281 ops/sec | **5x**      |
| `eviction`    | 36 ops/sec    | 6,336 ops/sec | **175x**    |
| `honor_decay` | 5,628 ops/sec | 3.1M ops/sec  | **550x**    |

## Documentation

### Core Documentation

- [`docs/WHAT_CAN_I_DO.md`](docs/WHAT_CAN_I_DO.md) - Complete capability overview
- [`docs/USER_ENGAGEMENT_GUIDE.md`](docs/USER_ENGAGEMENT_GUIDE.md) - User engagement & tailored experience
- [`docs/SKILLS_RAG_QUICKSTART.md`](docs/SKILLS_RAG_QUICKSTART.md) - Skills and RAG system guide
- [`docs/AGENTIC_SYSTEM.md`](docs/AGENTIC_SYSTEM.md) - Agentic system documentation
- [`docs/AGENTIC_SYSTEM_USAGE.md`](docs/AGENTIC_SYSTEM_USAGE.md) - Agentic system usage guide

### Architecture & Security

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) - **Complete architecture documentation with detailed Mermaid diagrams**
- [`docs/ARCHITECTURE_VISUAL_GUIDE.md`](docs/ARCHITECTURE_VISUAL_GUIDE.md) - **Visual quick reference guide for rapid understanding**
- [`docs/security/SECURITY_ARCHITECTURE.md`](docs/security/SECURITY_ARCHITECTURE.md) - Security architecture
- [`docs/EVENT_DRIVEN_ARCHITECTURE.md`](docs/EVENT_DRIVEN_ARCHITECTURE.md) - Event-driven design patterns
- [`docs/PERFORMANCE_OPTIMIZATION.md`](docs/PERFORMANCE_OPTIMIZATION.md) - Performance optimization guide

### Development Guides

- [`docs/structure/README.md`](docs/structure/README.md) - Repository structure guide
- [`docs/CLEANUP_SUMMARY.md`](docs/CLEANUP_SUMMARY.md) - Recent cleanup and reorganization
- [`SAFE_MERGES_COMPLETED.md`](SAFE_MERGES_COMPLETED.md) - Merge strategy and completion report

## License

MIT License - See [LICENSE](LICENSE) for details.

---

**GRID is now more organized, capable, and production-ready than ever! 🚀**
