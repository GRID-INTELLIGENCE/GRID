# Restore and Tracking Reference (Grid Directory)

This document records how to restore the Grid directory to its most recent change and which sources are used for tracking.

## Grid directory path

- **Primary:** `d:\Build\GRID-main` (restored from `d:\Build\GRID.zip`; previous folder backed up as `d:\Build\GRID-main.old`).

## Restore steps performed

1. **Backup:** `GRID-main` was renamed to `GRID-main.old`.
2. **Extract:** `GRID.zip` was extracted to `d:\Build`; the extracted folder was renamed to `GRID-main`.
3. **Git:** The restored `GRID-main` already contains a `.git` directory with remote `origin` → `https://github.com/caraxesthebloodwyrm02/GRID.git`. To align with the remote's most recent state, run (with network and Git in PATH):

   ```powershell
   cd d:\Build\GRID-main
   git fetch origin
   git reset --hard origin/main
   ```

   If Git is not in PATH, use the full path: `& "C:\Program Files\Git\bin\git.exe" fetch origin`, etc.

## Tracking sources ("all others")

| Source | Role |
|--------|------|
| **Git** | Primary version history; use for "most recent change" and ongoing tracking. Remote: `origin` → GitHub GRID repo. |
| **GRID.zip** | Snapshot backup at `d:\Build\GRID.zip`; use to restore if the folder was overwritten or not a repo. |
| **GRID-main.old** | Backup of the folder before this restore; keep or delete after confirming the restored tree. |
| **Cursor / VSCode Local History** | Per-file history; use "Local History" in the editor to recover individual file versions. |
| **Windows File History / Backup** | System-level restores if the whole folder was deleted or moved. |
| **Cloud sync (e.g. OneDrive)** | Version history on synced folders; use to restore previous versions of files/folders. |
| **Windows built-in restore** | For all Windows options (Recycle Bin, File History, Previous Versions, OneDrive, Backup and Restore, shadow copies, System Restore, etc.), see [WINDOWS_RESTORE_OPTIONS.md](WINDOWS_RESTORE_OPTIONS.md). |

## Future restores

- If `GRID-main` has a working `.git`: use `git status`, `git log -1`, `git reflog`, then `git restore .` or `git reset --hard <commit>` as needed.
- If there is no `.git`: use `GRID.zip` (or a fresh clone), then run `git init`, `git remote add origin https://github.com/caraxesthebloodwyrm02/GRID.git`, `git fetch origin`, `git checkout -b main origin/main` (or `git reset --hard origin/main`).
- **Commit restoration:** For Grid commit or branch recovery (reflog, lost commits, reset to a specific commit), see `d:\Build\GRID-main\COMMIT_RESTORATION.md`.

Last updated: 2026-02-07 (after restore from GRID.zip and establishment of Git tracking reference).
