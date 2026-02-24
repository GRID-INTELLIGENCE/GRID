# Installation Guide

Complete installation instructions for GRID across different platforms and use cases.

---

## System Requirements

### Minimum Requirements

- **Python**: 3.13 (required — GRID uses PEP 695 syntax)
- **RAM**: 2GB minimum, 4GB recommended
- **Disk Space**: 500MB for installation
- **OS**: Windows 10+, macOS 12+, or Linux (Ubuntu 22.04+)

### Required Tools

- **uv** — Python package manager ([install guide](https://docs.astral.sh/uv/getting-started/installation/))
- **Git**: 2.30+

---

## Quick Installation

### For End Users

```bash
pip install grid-intelligence
grid --help
```

### For Developers

```bash
git clone https://github.com/GRID-INTELLIGENCE/GRID.git
cd GRID
uv sync --group dev --group test
uv run pytest -q --tb=short
```

---

## Detailed Installation

### Step 1: Install Python 3.13

#### Windows
1. Download Python 3.13 from [python.org](https://www.python.org/downloads/)
2. Run installer, **check "Add Python to PATH"**
3. Verify: `python --version`

#### macOS
```bash
brew install python@3.13
python3 --version
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install -y python3.13 python3.13-venv
python3.13 --version
```

### Step 2: Install uv

```bash
# All platforms
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv

# Verify
uv --version
```

### Step 3: Clone and Install

```bash
git clone https://github.com/GRID-INTELLIGENCE/GRID.git
cd GRID

# Install all dependencies (creates .venv from uv.lock)
uv sync --group dev --group test
```

Do not use `python -m venv` or bare `pip install` for this repo. Use uv so the environment matches the lockfile.

### Step 4: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
ENVIRONMENT=development
DATABASE_URL=sqlite:///./app.db
SECRET_KEY=change-this-to-random-string
API_HOST=0.0.0.0
API_PORT=8000
```

### Step 5: Verify Installation

```bash
uv run python -c "import grid; print(grid.__version__)"
uv run grid --help
uv run pytest -q --tb=short
```

---

## IDE Setup

### Visual Studio Code (Recommended)

Install extensions:
- **charliermarsh.ruff** — Python formatter and linter (replaces Black + isort)
- **ms-python.python** — Python language support
- **ms-python.vscode-pylance** — Type checking

Settings are pre-configured in `.vscode/settings.json`. Key points:
- Formatter: **Ruff** (not Black, not isort)
- Line length: 120 characters
- Line endings: LF (not CRLF)
- Python path: `.venv/Scripts/python` (Windows) or `.venv/bin/python` (Unix)

See [IDE_SETUP_VERIFICATION.md](guides/IDE_SETUP_VERIFICATION.md) for the full checklist.

---

## Troubleshooting

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'grid'`

```bash
# Re-sync environment
uv sync --group dev --group test

# Verify Python path
uv run python -c "import sys; print(sys.path)"
```

### Port Already in Use

```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Unix/macOS
lsof -ti:8000 | xargs kill -9

# Or use different port
uv run uvicorn grid.api.main:app --port 8001
```

### Getting Help

1. Check [GitHub Issues](https://github.com/GRID-INTELLIGENCE/GRID/issues)
2. Review the [getting-started guide](getting-started.md)

---

## Verification Checklist

- [ ] Python 3.13: `python --version`
- [ ] uv installed: `uv --version`
- [ ] Dependencies synced: `uv sync --group dev --group test`
- [ ] Package imports: `uv run python -c "import grid"`
- [ ] CLI works: `uv run grid --help`
- [ ] Tests pass: `uv run pytest -q --tb=short`
- [ ] Linter clean: `uv run ruff check work/ safety/ security/ boundaries/`
