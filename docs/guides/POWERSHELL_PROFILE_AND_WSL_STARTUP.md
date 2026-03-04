# PowerShell Profile and WSL Startup

How to **activate** terminal shortcuts (eg, ee, ea, exr, proj, pst) and optional WSL startup for the GRID workspace.

---

## 1. PowerShell profile (Windows)

Shortcuts **eg**, **ee**, **ea**, **exr**, **proj**, **pst**, **Show-Ports**, **Test-All** come from the workspace PowerShell profile. Install or update it so every new PowerShell session loads them.

### Install / update from GRID repo

From PowerShell (from any directory):

```powershell
# Default: uses E:\Emergence\Canopy\Workspaces\VSCode-Workspace-BestPractices\PowerShellProfileBackup.ps1
& "E:\Seeds\GRID-main\scripts\Install-PowerShellProfile.ps1"
```

This copies the backup profile to `$PROFILE` and backs up your existing profile. Reload with `. $PROFILE` or open a new terminal.

### Custom profile path

If the backup lives elsewhere:

```powershell
& "E:\Seeds\GRID-main\scripts\Install-PowerShellProfile.ps1" -SourcePath "D:\path\to\PowerShellProfileBackup.ps1"
```

### Manual one-liner (if script not used)

```powershell
Copy-Item -Path "E:\Emergence\Canopy\Workspaces\VSCode-Workspace-BestPractices\PowerShellProfileBackup.ps1" -Destination $PROFILE -Force
. $PROFILE
```

### Verify

In a new PowerShell window: run `proj` — you should see the project list. Then `eg` to enter GRID (cwd + venv).

---

## 2. WSL startup script

Optional: run GRID-related env (e.g. `GRID_HOME`, venv on `PATH`) when you start a WSL bash session.

### Use the script (source from ~/.bashrc)

In WSL:

```bash
# Add once to ~/.bashrc
if [ -f /mnt/e/Seeds/GRID-main/scripts/wsl_startup.sh ]; then
  . /mnt/e/Seeds/GRID-main/scripts/wsl_startup.sh
fi
```

Then `source ~/.bashrc` or open a new WSL terminal. The script:

- Does nothing if `/mnt/e` is missing (e.g. not WSL or mount not done).
- Sets `GRID_HOME` and adds GRID `.venv/bin` to `PATH` when `/mnt/e/Seeds/GRID-main` exists.
- No sudo; user-space only.

### If /mnt/e is not mounted

Run once (in WSL): `sudo mount -t drvfs E: /mnt/e`. See **docs/guides/WSL_SETUP_COMPLETE_RUNBOOK.md** and **docs/LINUX_BASH_SCOPE.md** for full WSL setup.

---

## 3. Quick reference

| Goal | Command / action |
|------|------------------|
| Activate PowerShell shortcuts | Run `Install-PowerShellProfile.ps1` once; then `. $PROFILE` or new terminal |
| WSL: load GRID env on login | Add the `if [ -f ... wsl_startup.sh ]; then . ... fi` block to `~/.bashrc` |
| Full shortcut table | **E:\.vscode\cli-shortcuts.md** or **E:\AGENTS.md** (CLI shortcuts section) |
