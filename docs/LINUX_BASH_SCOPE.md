# Linux & Bash Scope: Installation, Recommendations, Guidance

Single reference for **bash-specific** and **Linux-scope** documentation in GRID: installation, recommendations, and guidance. Covers native Linux, WSL2, and bash scripts.

---

## 1. Installation (Linux / Bash)

### 1.1 System requirements (Linux)

- **OS**: Linux (Ubuntu 22.04+ or equivalent)
- **Python**: 3.13 (required)
- **uv**: Package manager (use uv, not pip for this repo)
- **RAM**: 2GB min, 4GB recommended
- **Disk**: ~500MB for install

### 1.2 Install Python 3.13 (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install -y python3.13 python3.13-venv
python3.13 --version
```

### 1.3 Install uv (all platforms, bash)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# Or: pip install uv
uv --version
```

### 1.4 Clone and sync (developer install)

```bash
git clone https://github.com/GRID-INTELLIGENCE/GRID.git
cd GRID

# Venv + activate (Linux/Mac)
uv venv --python 3.13 --clear
source .venv/bin/activate

# Sync deps (base + dev + test)
uv sync --group dev --group test

# Verify
uv run pytest tests/unit/ -q --tb=short
```

### 1.5 Makefile (bash-friendly)

From repo root on Linux/Mac:

```bash
make install    # uv sync
make run       # Start Mothership API
make test      # Unit + integration tests
make lint      # Ruff + mypy
make format    # Ruff format + fix
make clean     # Remove build/cache artifacts
```

### 1.6 Security install (Linux/Mac)

```bash
cd /path/to/GRID
bash security/install.sh
# Or quick mode (no prompts):
bash security/install.sh --quick
```

See `security/QUICK_START.md` for Linux/Mac one-liner and next steps.

---

## 2. WSL2 scope (Linux environment on Windows)

### 2.1 When to use WSL

- Run bash scripts and Linux tooling from Windows.
- Use llama-cli or other Linux-only builds.
- Match CI (Linux) locally.

### 2.2 WSL mount and path

- **Windows drive in WSL**: `E:\` → `/mnt/e/`
- **GRID repo in WSL**: e.g. `/mnt/e/Seeds/GRID-main` or `$HOME/projects/GRID` after migration.
- If `/mnt/e` is missing, fix mount first (see **WSL_SETUP_COMPLETE_RUNBOOK.md**).

### 2.3 Fix /mnt/e mount (bash)

```bash
# In WSL
sudo nano /etc/wsl.conf
```

Add or ensure:

```ini
[automount]
enabled = true
options = "metadata"
```

Then:

```bash
exit
# From Windows PowerShell: wsl --shutdown
# Then open WSL again: wsl
ls -la /mnt/e/Seeds/GRID-main   # verify
```

### 2.4 Run GRID from WSL (bash)

```bash
cd /mnt/e/Seeds/GRID-main
source .venv/bin/activate   # if venv exists
uv sync --group dev --group test
uv run grid --help
```

Or use **migrate_to_wsl.sh** to copy project into WSL filesystem for better I/O (see **Scripts** below).

### 2.5 Path conversion (Windows ↔ WSL)

- **Windows → WSL**: `E:\Seeds\GRID-main` → `/mnt/e/Seeds/GRID-main`
- **WSL → Windows**: Use from Windows as `\\wsl$\Ubuntu\home\user\...` or run commands inside WSL.
- OpenCode/wrapper: use absolute WSL paths in bash, e.g. `wsl bash /mnt/e/Seeds/GRID-main/scripts/opencode_wrapper.sh`.

---

## 3. Bash scripts reference

| Script | Purpose | Usage (bash) |
|--------|---------|---------------|
| **security/install.sh** | Network security install & config | `bash security/install.sh` |
| **scripts/migrate_to_wsl.sh** | Migrate repo into WSL fs, benchmark | `bash scripts/migrate_to_wsl.sh` [--dry-run \| --skip-benchmark \| --force] |
| **scripts/eufle.sh** | EUFLE launcher (mounts E:, sets PYTHONPATH) | `bash scripts/eufle.sh` |
| **scripts/eufle_launcher.sh** | EUFLE launcher wrapper | `bash scripts/eufle_launcher.sh` |
| **scripts/opencode_wrapper.sh** | OpenCode CLI via WSL | `wsl bash scripts/opencode_wrapper.sh --version` |
| **scripts/quick_health_check.sh** | Quick health check | `bash scripts/quick_health_check.sh` |
| **scripts/deploy.sh** | Deployment | `bash scripts/deploy.sh` |
| **scripts/monitor_wsl_performance.sh** | WSL performance monitoring | `bash scripts/monitor_wsl_performance.sh` |
| **scripts/run_post_11pm_contract.sh** | Post-11pm contract run | `bash scripts/run_post_11pm_contract.sh` |
| **scripts/woven_seed_tracing.sh** | Seed tracing | `bash scripts/woven_seed_tracing.sh` |
| **infrastructure/docker/docker-entrypoint.sh** | Docker entrypoint | Used by Docker; not for direct bash run |
| **docker/docker-entrypoint.sh** | Docker entrypoint | Same |

### 3.1 Script conventions

- Shebang: `#!/bin/bash`
- Fail fast: `set -e` or `set -euo pipefail`
- Paths: prefer `$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)` for script dir
- No `pip` in scripts: use `uv` or `python3 -m pip` only where project allows

---

## 4. Recommendations

### 4.1 Package manager

- **Use uv** for install/sync (matches lockfile). Do not use raw `pip` for GRID deps.
- **Linux**: `uv sync --group dev --group test` for development; add `--group finetuning` only if needed.

### 4.2 Venv activation (Linux/Mac)

```bash
source .venv/bin/activate
```

Windows (PowerShell): `.venv\Scripts\Activate.ps1`. For bash on Windows use WSL.

### 4.3 RAG / environment (bash)

```bash
export RAG_USE_HYBRID=true
export RAG_USE_RERANKER=true
```

Optional; see **docs/project/CLAUDE.md** for RAG env vars.

### 4.4 Session start protocol (before coding)

From **CLAUDE.md**:

```bash
uv run python -m pytest -q --tb=short && uv run ruff check work/ safety/ security/ boundaries/
```

Fix failing tests before making changes.

### 4.5 WSL recommendation

- **Development on Windows**: Prefer WSL2 + bash for scripts, Makefile, and Linux-style paths.
- **Ollama**: Can run on Windows or in WSL; ensure `ollama serve` is reachable from where you run GRID (same host or correct URL).
- **Performance**: If I/O is slow on `/mnt/e`, use **migrate_to_wsl.sh** to work from `$HOME` in WSL.

---

## 5. Guidance summary

| Topic | Guidance |
|-------|----------|
| **Install (Linux)** | `apt install python3.13`, install uv, clone repo, `uv venv` + `source .venv/bin/activate`, `uv sync --group dev --group test`. |
| **Install (WSL)** | Ensure `/mnt/e` (or your drive) is mounted; same as Linux; or run **migrate_to_wsl.sh** to work inside WSL fs. |
| **Bash scripts** | Run from repo root; use `bash path/to/script.sh`; optional args as in table above. |
| **Makefile** | Use `make install`, `make test`, `make lint`, `make run` on Linux/Mac (bash). |
| **Paths** | In bash/WSL use `/mnt/e/...` for Windows E:; in scripts use script-relative or `$ROOT_DIR`. |
| **Security** | `bash security/install.sh`; then use `security/monitor.sh`, `enable_network.sh`, `disable_network.sh` from security dir. |
| **Docs to read next** | **docs/project/CLAUDE.md** (commands, Makefile, RAG), **docs/guides/WSL_SETUP_COMPLETE_RUNBOOK.md** (WSL + llama-cli), **docs/INSTALLATION.md** (full install), **security/QUICK_START.md** (security quick start). |

---

## 6. Source document index

| Document | Content (Linux/Bash relevance) |
|----------|---------------------------------|
| **docs/project/CLAUDE.md** | Bash blocks: venv activate (Linux/Mac), uv sync, pytest, ruff, make, RAG env. |
| **docs/INSTALLATION.md** | Python 3.13 install (Ubuntu/Debian), uv, clone, uv sync; no pip for repo. |
| **docs/guides/WSL_SETUP_COMPLETE_RUNBOOK.md** | WSL mount, setup_llamacpp.sh, diagnostics, Path B (WSL + llama-cli). |
| **docs/guides/opencode_usage.md** | WSL2 install (bash), path issues, API keys in `~/.bashrc` / `~/.zshrc`. |
| **docs/guides/USAGE_INSTRUCTIONS.md** | `source venv/bin/activate` (Linux/Mac). |
| **security/install.sh** | Bash install script: Python check, deps, config, security init, helper scripts. |
| **security/QUICK_START.md** | Linux/Mac: `bash security/install.sh`; commands for monitor, whitelist, enable/disable. |
| **scripts/migrate_to_wsl.sh** | Bash: migrate GRID to WSL fs, benchmark, --dry-run, --force. |
| **scripts/eufle.sh** | Bash: mount E:, set PYTHONPATH/EUFLE_HOME, run eufle.py. |
| **Makefile** | make install, run, test, lint, format, clean (bash/make on Linux/Mac). |
| **README.md** | Pip install (end-user); Platforms: Windows, Mac, Linux. |

---

*This doc synthesizes bash and Linux scope only. For full project setup, see **docs/INSTALLATION.md** and **docs/project/CLAUDE.md**.*
