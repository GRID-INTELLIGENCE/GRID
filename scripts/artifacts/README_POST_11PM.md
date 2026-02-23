# Post-11pm contract runner

Runs the GRID post-11pm contract via **Claude Code** (Anthropic CLI), using the workflow described in [Anthropic’s common workflows](https://docs.anthropic.com/en/docs/claude-code/common-workflows) and [CLI reference](https://docs.anthropic.com/en/docs/claude-code/cli-reference).

## Prerequisites

- **Claude Code CLI** installed and on `PATH`  
  - Install: https://docs.anthropic.com/en/docs/claude-code/getting-started  
  - Verify: `claude -v`
- Repo root contains:
  - `GRID_COMPREHENSIVE_REPORT_2026-02-23.md`
  - `.grid/post-11pm-contract.json`
  - `scripts/post_11pm_context.txt`
  - `scripts/artifacts/session-terminal-outputs-2026-02-23.txt`

## Usage

### Windows (PowerShell)

```powershell
cd E:\GRID-main
.\scripts\run_post_11pm_contract.ps1
```

- **Dry run (no Claude call):** `.\scripts\run_post_11pm_contract.ps1 -DryRun`
- **No worktree (run in current dir):** `.\scripts\run_post_11pm_contract.ps1 -NoWorktree`
- **Custom model:** `.\scripts\run_post_11pm_contract.ps1 -Model sonnet`

### WSL / Linux / macOS

```bash
cd /path/to/GRID-main
chmod +x scripts/run_post_11pm_contract.sh
./scripts/run_post_11pm_contract.sh
```

- **Dry run:** `./scripts/run_post_11pm_contract.sh --dry-run`
- **No worktree:** `./scripts/run_post_11pm_contract.sh --no-worktree`
- **Custom model:** `CLAUDE_MODEL=sonnet ./scripts/run_post_11pm_contract.sh`

## What the script does

1. Resolves GRID root and checks that report, contract, context file, and terminal-outputs artifact exist.
2. Writes a run log under `scripts/artifacts/post_11pm_run_YYYYMMDD_HHMMSS.log` with paths and the exact command.
3. Invokes Claude Code with:
   - **Worktree:** `--worktree post-11pm-20260223` (isolated git worktree per [Run parallel Claude Code sessions with Git worktrees](https://docs.anthropic.com/en/docs/claude-code/common-workflows#run-parallel-claude-code-sessions-with-git-worktrees)).
   - **Model:** `--model opus` (override with `-Model` / `CLAUDE_MODEL`).
   - **Context:** `--append-system-prompt-file scripts/post_11pm_context.txt` (paths and rules for the contract).
   - **Task:** `-p "Execute the post-11pm contract..."` (print mode; single non-interactive run).

Claude is instructed to read the report and contract, use the terminal outputs for reference, run actions in priority order, preserve the “preserve” list, and output a short summary.

## Scheduled run (once, after 11 PM — when token rate limit resets)

- **One-time setup:** Run the scheduled-task setup script. It creates a **one-time** task at **11:02 PM** (a little past 11 so your token rate limit has reset):
  ```powershell
  cd E:\GRID-main
  .\scripts\setup_scheduled_task_post_11pm.ps1
  ```
- **Task name:** `GRID_Post_11pm_Claude_Contract`
- **Trigger:** **Once** at 11:02 PM (edit `$RunAt = "23:02"` in `setup_scheduled_task_post_11pm.ps1` to use 23:05 for 11:05 PM, etc.).
- **What it does:** At 11:02 PM, opens a console window and runs the contract with:
  - **Worktree** isolation (`post-11pm-20260223`)
  - **Opus** model with **fallback to Sonnet** if Opus is overloaded
  - **Verbose** output (turn-by-turn) so you see progress
  - Report + contract + terminal outputs as context
  - **Extended thinking** encouraged for complex, multi-step fixes
- **Verify:** `taskschd.msc` → Task Scheduler Library → `GRID_Post_11pm_Claude_Contract`
- **Run now:** `Start-ScheduledTask -TaskName "GRID_Post_11pm_Claude_Contract"`
- **Remove task:** `Unregister-ScheduledTask -TaskName "GRID_Post_11pm_Claude_Contract"`
- **Quiet run (no --verbose):** `.\scripts\run_post_11pm_contract.ps1 -Quiet`

### Removing duplicate / redundant tasks around 11 PM

To remove any other scheduled tasks in the 11 PM hour that look like the GRID post-11pm contract (and leave only the canonical one):

```powershell
.\scripts\remove_duplicate_post_11pm_tasks.ps1
```

Then re-create the single task:

```powershell
.\scripts\setup_scheduled_task_post_11pm.ps1
```

To only list what would be removed (no changes): `.\scripts\remove_duplicate_post_11pm_tasks.ps1 -WhatIf`

**Note:** Each time you run `setup_scheduled_task_post_11pm.ps1`, it runs this cleanup first, then registers the single task — so you always end up with exactly one task at 11:02 PM.

### Administrator required for task creation

Creating or updating the GRID post-11pm scheduled task **requires running PowerShell as Administrator** (elevation). This ensures only an approved admin can add or change scheduled tasks.

- Run: Right-click PowerShell → "Run as administrator", then `cd E:\GRID-main` and `.\scripts\setup_scheduled_task_post_11pm.ps1`.
- If you run without elevation, the script will exit with an error asking for admin.

### Stopping security/certificate/OneDrive/system tasks (normalize by attributes)

To **stop, disable, and optionally delete** tasks that match security-related attributes (certificate enrollment, key pre-gen, OneDrive, consent sync, time-scheduled updaters, etc.):

```powershell
# Run PowerShell as Administrator, then:
cd E:\GRID-main
.\scripts\stop_and_normalize_system_tasks.ps1
```

- **WhatIf (list only):** `.\scripts\stop_and_normalize_system_tasks.ps1 -WhatIf`
- **Disable and stop only (default):** `.\scripts\stop_and_normalize_system_tasks.ps1`
- **Disable and delete (remove task):** `.\scripts\stop_and_normalize_system_tasks.ps1 -Delete`

Tasks matched by name/description/attributes include: AikCertEnrollTask, KeyPreGenTask, UnifiedConsentSyncTask, GoogleUpdaterTaskSystem*, appuriverifierinstall, OneDrive*, and similar. **GRID_Post_11pm_Claude_Contract is never modified** by this script.

## Referenced paths (for prompts and logs)

| Purpose              | Path |
|----------------------|------|
| Full report          | `GRID_COMPREHENSIVE_REPORT_2026-02-23.md` |
| Contract JSON        | `.grid/post-11pm-contract.json` |
| Terminal outputs     | `scripts/artifacts/session-terminal-outputs-2026-02-23.txt` |
| Context (system)     | `scripts/post_11pm_context.txt` |
| Run logs             | `scripts/artifacts/post_11pm_run_*.log` |

These paths are highlighted in the context file and in the runner so Claude and humans can open the same files.
