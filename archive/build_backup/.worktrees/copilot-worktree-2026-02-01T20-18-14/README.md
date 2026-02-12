# E:\ Development Root

E:\ is the single development parent directory. All projects are organized under this root.

## Layout

- **grid/** - GRID Intelligence Framework (core Python/FastAPI project)
- **Coinbase/** - Crypto-focused project with GRID integration
- **config/** - Workspace-wide configuration files
- **docs/** - Guides, summaries, architecture documentation
- **shared/** - Shared utilities (workspace_utils, context_bridge)
- **analysis_outputs/** - Analysis artifacts repository
- **archive/** - Retired outputs, old artifacts

## Quick Start

### GRID Framework
```bash
cd e:\grid
uv venv --python 3.13 --clear
.\.venv\Scripts\Activate.ps1
uv sync --group dev --group test

# Run API server
python -m application.mothership.main

# Query RAG system
python -m tools.rag.cli query "your question"

# Run tests
pytest
```

### Coinbase Project
```bash
cd e:\Coinbase
pip install -e .[dev,test]
pytest
```

## Python Version

Python 3.13.11 is enforced across all projects via `.python-version` files.

## Commands

- **Cleanup**: `python scripts/cleanup_temp.py --workspace-root E:\ [--dry-run]`
- **Analysis**: `python scripts/run_comprehensive_analysis.py`
- **Install**: `pip install -r requirements.txt` (root master requirements)

## Python Path

Ensure `E:\` or `E:\shared` is in PYTHONPATH when using workspace_utils or running tests.

## See Also

- [AGENTS.md](AGENTS.md) - AI agent development guide
- [grid/README.md](grid/README.md) - GRID framework documentation
- [docs/ARCHITECTURE_EXECUTIVE_SUMMARY.md](docs/ARCHITECTURE_EXECUTIVE_SUMMARY.md) - Architecture overview
