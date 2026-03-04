# Bash Conducts: Simplifying and Applying Best Practices (Risk & Elevation)

Approach for simplifying bash scripts and documented “conducts” that currently impose risk or require elevation (sudo/root). Goal: **user-space by default**, **elevation explicit and minimal**, **single source of truth**.

---

## 1. Principles

| Principle | Meaning |
|-----------|--------|
| **User-space first** | Scripts run as the current user. No `sudo` inside “daily” scripts. |
| **Elevation explicit** | Any need for root/sudo is documented once, in a setup/install section, not embedded in launchers. |
| **Fail safe** | If elevation is required, script exits with a clear message and the exact command to run (user runs it). |
| **Single source of truth** | One doc (e.g. LINUX_BASH_SCOPE.md) lists scripts and whether they need elevation; scripts don’t duplicate policy. |
| **Smallest scope** | Elevation only for operations that truly need it (e.g. mount, systemd, /opt), not for project venv or app code. |

---

## 2. Current Risk / Elevation Map

| Script / Doc | Elevation / Risk | Change |
|--------------|------------------|--------|
| **eufle.sh** / **eufle_launcher.sh** | `sudo mount` inside script; runs whenever E: not mounted | **Remove** inline sudo; require pre-mounted drive or document one-time mount step. |
| **deploy.sh** | Requires root; writes /opt, /etc/systemd, /var/log | Keep as **explicit admin script**; document “run with sudo” once; don’t call from automation without consent. |
| **LINUX_BASH_SCOPE.md** / **INSTALLATION.md** | `sudo apt`, `sudo nano /etc/wsl.conf` in docs | Keep as **one-time setup**; add short “elevation boundary” note. |
| **migrate_to_wsl.sh** | Suggests `sudo apt install` for missing deps | Keep as **suggestion** (print only); user runs in their own shell. |
| **security/install.sh** | TBD (network/config) | Audit; any sudo must be explicit and documented. |

---

## 3. Simplification Patterns

### 3.1 No sudo inside “runner” scripts

- **Pattern:** Launchers (eufle, opencode_wrapper, etc.) assume environment is already set up (mount done, deps installed).
- **If something is missing:** Exit with a clear message and the **exact** command the user must run (e.g. “Run once: sudo mount -t drvfs E: /mnt/e” or “Run: sudo apt install …”).

Example (eufle-style launcher):

```bash
#!/bin/bash
set -e
if [ ! -d /mnt/e ]; then
  echo "E: not mounted. Run once (WSL): sudo mount -t drvfs E: /mnt/e"
  exit 1
fi
if [ ! -d /mnt/e/EUFLE ]; then
  echo "EUFLE directory not found at /mnt/e/EUFLE. Ensure E: is mounted and EUFLE exists at E:\\EUFLE."
  exit 1
fi
export PYTHONPATH=/mnt/e/EUFLE:$PYTHONPATH
cd /mnt/e/EUFLE
exec python3 eufle.py "$@"
```
(Production scripts should distinguish “mount missing” vs “project dir missing” and avoid a single “E: not mounted” message when only `/mnt/e/EUFLE` is checked.)

### 3.2 Elevation only in “setup” or “admin” scripts

- **Setup:** One-time (or rare) install: e.g. `sudo apt install`, `sudo nano /etc/wsl.conf`, optional `sudo mount` in a dedicated **setup** doc or script.
- **Admin:** deploy.sh, systemd install, logrotate: documented as “run with sudo” or “run as root” from a single place (e.g. LINUX_BASH_SCOPE.md or DEPLOYMENT.md).

### 3.3 Document elevation in one place

- In **LINUX_BASH_SCOPE.md** (or a short “Bash scripts” section in INSTALLATION.md):
  - Table: Script name | Purpose | Elevation? | When
  - “Elevation?”: **None** | **One-time setup** (user runs documented sudo) | **Admin** (script expects root/sudo).

### 3.4 Shared conventions (already in LINUX_BASH_SCOPE.md; reinforce)

- Shebang: `#!/bin/bash`
- Fail fast: `set -e` or `set -euo pipefail`
- Script dir: `$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)`; no `pip` in scripts for GRID — use `uv` or documented `python3 -m pip` only where allowed.

---

## 4. Concrete Changes (Checklist)

1. **eufle.sh / eufle_launcher.sh**  
   - Remove `sudo mount`.  
   - If `/mnt/e` (or target) missing: print message + exact mount command, `exit 1`.  
   - Optionally: one-line “setup” in a doc: “To use EUFLE from WSL, run once: sudo mount -t drvfs E: /mnt/e”.

2. **deploy.sh**  
   - Keep “must run as root/sudo” at top; add one-line comment pointing to DEPLOYMENT or LINUX_BASH_SCOPE for when/why.  
   - Do not invoke from CI or automation unless explicitly intended (and documented).

3. **LINUX_BASH_SCOPE.md**  
   - Add **§ 3.1 Elevation boundary**: short table (script | elevation | when).  
   - Clarify that `sudo apt` / `sudo nano /etc/wsl.conf` are **one-time setup**, not part of daily scripts.

4. **migrate_to_wsl.sh**  
   - Keep current behavior: only **print** “Install with: sudo apt install …”. No automatic sudo.

5. **security/install.sh**  
   - Audit for any sudo/root; if present, document in the same elevation table and limit to setup/admin use.

---

## 5. Activation (launcher scripts)

- **EUFLE launchers:** No venv activation inside the script; they set `PYTHONPATH`, `EUFLE_HOME`, and `LLAMACPP_PATH`. If EUFLE uses a venv, activate it before running, or rely on system `python3`.
- **LLAMACPP_PATH:** Scripts use `"${LLAMACPP_PATH:-/home/irfan/eufle_work/llama.cpp/build/bin}"`. Override by exporting before run: `export LLAMACPP_PATH=/path/to/llama.cpp/build/bin; bash scripts/eufle.sh`. Document default in LINUX_BASH_SCOPE or README for EUFLE.

---

## 6. Post-debug / verification sequence (best practices)

After applying bash-conduct changes (or any script/doc fix), follow a short **Reconcile → Report** sequence aligned with the 6-stage workflow (VSCode-Workspace-BestPractices):

1. **Reconcile**
   - Update any state or docs that record “last change” (e.g. checklist in this file, or session state if used).
   - Confirm elevation table in LINUX_BASH_SCOPE.md matches current scripts (no “mounts E:” for eufle; deploy.sh documented as admin).

2. **Report**
   - What changed: list files and one-line summary per file.
   - Verification commands (run to confirm behavior):
     - **EUFLE (WSL):** `bash scripts/eufle.sh --help` or run with no args after mount; expect clear exit message if `/mnt/e` or `/mnt/e/EUFLE` missing.
     - **GRID:** `make test` and `make lint` from repo root (no bash script change required for those).
   - Remaining: note any follow-up (e.g. security/install.sh audit, or LLAMACPP_PATH in EUFLE README).

3. **Optional: one-shot verify**
   - From GRID repo root: `make test && make lint` (confirms no regressions from doc-only or script-only edits).

---

## 7. Outcome

- **Conducts** = what we document (when to use which script, what’s user vs admin).  
- **Simpler:** Runners never elevate; setup and admin are explicit and documented in one place.  
- **Less risk:** No hidden sudo in launchers; user runs elevated commands consciously.  
- **Aligned with VSCode-Workspace-BestPractices:** Explicit, minimal, file-based evidence (one doc for elevation and scripts).

---

*Ref: LINUX_BASH_SCOPE.md, AGENTS.md, VSCode-Workspace-BestPractices AGENTS.md (6-stage workflow: Orient → Route → Gate → Implement → Reconcile → Report).*
