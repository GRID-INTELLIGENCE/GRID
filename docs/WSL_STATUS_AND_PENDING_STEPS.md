# WSL Status & Pending Steps for Full Installation

Command-line check results and what’s left to do for a full GRID-from-WSL setup.

---

## 1. Current status (as checked)

| Check | Result | Notes |
|-------|--------|--------|
| **WSL installed** | ✅ Yes | WSL 2.6.3.0 |
| **Default distro** | ✅ Ubuntu | WSL 2, Running |
| **Windows E: drive** | ✅ Exists | `E:\` and `E:\Seeds\GRID-main` present from PowerShell |
| **WSL /mnt/e** | ⚠️ Empty | Directory exists; **E: is not mounted** — only `C:\` appears in `mount` |
| **WSL /mnt/e/Seeds/GRID-main** | ❌ Not accessible | No such file or directory (E: not mounted) |
| **WSL Python** | ⚠️ 3.12.3 | GRID expects 3.13; use Windows venv or install 3.13 in WSL |
| **WSL uv** | ❓ Not confirmed | `which uv` not in scope; install in WSL if using WSL for GRID |
| **wsl.conf** | ⚠️ No [automount] | Has `[boot] systemd=true` only |

**Conclusion:** WSL and Ubuntu are fine. The blocker for “full installation” from WSL is that **E: is not mounted in WSL**, so `/mnt/e/Seeds/GRID-main` is not available. Fix the E: mount, then optionally align Python/uv in WSL.

---

## 2. Steps pending for full installation

### Step A: Fix E: drive mount in WSL (required to use GRID from WSL)

**Option 1 — Automount (recommended, persistent):**

1. In WSL:
   ```bash
   sudo nano /etc/wsl.conf
   ```
2. Ensure this block exists (add if missing):
   ```ini
   [automount]
   enabled = true
   options = "metadata"
   ```
3. Save (`Ctrl+O`, Enter, `Ctrl+X`), exit WSL, then from **PowerShell**:
   ```powershell
   wsl --shutdown
   ```
4. Start WSL again and verify:
   ```bash
   ls -la /mnt/e/Seeds/GRID-main
   ```
   You should see repo contents (e.g. `src/`, `pyproject.toml`).

**Option 2 — Manual mount (current session only):**

From WSL:

```bash
sudo mount -t drvfs E: /mnt/e -o metadata
ls /mnt/e/Seeds/GRID-main
```

You must repeat this after each WSL restart unless you add the automount config above.

---

### Step B: Python 3.13 & uv in WSL (optional, for running GRID inside WSL)

- GRID expects **Python 3.13**. WSL Ubuntu may have 3.12.
- Install 3.13 and uv in WSL, then create venv and sync:
  ```bash
  sudo apt update && sudo apt install -y python3.13 python3.13-venv
  curl -LsSf https://astral.sh/uv/install.sh | sh
  cd /mnt/e/Seeds/GRID-main
  uv venv --python 3.13 --clear
  source .venv/bin/activate
  uv sync --group dev --group test
  ```
- If you only need bash scripts and keep using Windows for Python, Step A is enough.

---

### Step C: Verify full installation from WSL

After Step A (and optionally B):

```bash
cd /mnt/e/Seeds/GRID-main
ls scripts/*.sh   # bash scripts
source .venv/bin/activate   # if you did Step B
uv run pytest tests/unit/ -q --tb=short
make test   # if make is installed in WSL
```

---

## 3. Quick reference commands

| Purpose | Command (PowerShell) | Command (WSL bash) |
|--------|----------------------|---------------------|
| WSL distros & state | `wsl --list --verbose` | — |
| WSL status | `wsl --status` | — |
| E: and GRID from Windows | `Test-Path E:\Seeds\GRID-main` | — |
| E: visible in WSL | — | `ls /mnt/e/Seeds/GRID-main` |
| Mount table in WSL | — | `mount \| grep /mnt` |
| Run repo diagnostic | `.\scripts\quick_diagnostic.ps1` | — |

---

## 4. Repo references

- **Mount fix (EUFLE path):** `docs/guides/WSL_MOUNT_FIX.md`
- **Full WSL runbook:** `docs/guides/WSL_SETUP_COMPLETE_RUNBOOK.md`
- **Linux/Bash scope:** `docs/LINUX_BASH_SCOPE.md`
- **Quick diagnostic (PowerShell):** `scripts/quick_diagnostic.ps1` (checks `/mnt/e/EUFLE`; same fix applies for `/mnt/e/Seeds/GRID-main`)

---

*Generated from command-line WSL checks. Re-run the verification commands above after applying Step A to confirm full installation.*
