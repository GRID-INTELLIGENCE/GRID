# GRID Discovery Checklist

**Context:** Microsoft account synced. Recovery drive can be created per Microsoft steps (Create a recovery drive, back up system files, Safety Remove Hardware to eject). This document records where GRID was searched and what was found.

---

## 1. Known backup and source locations

| Location | Found | Type | In restore plan? |
|----------|--------|------|------------------|
| **F:\FileHistory** | Yes | Directory | — |
| **F:\FileHistory\GRID** | Yes | Directory | Yes |
| **F:\FileHistory\GRID\DELOREAN** | Yes (contents: Configuration, Data) | File History backup | Yes (primary GRID source) |
| **F:\.pytest_cache.zip** | Yes — 740,000,368 bytes; modified 2026-02-07 08:50 | Zip backup | Yes |
| **E:\grid** | Yes | Junction → E:\_projects\grid-rag-enhanced | Yes (canonical path) |
| **E:\_projects\grid-rag-enhanced** | Yes (data, src, tests, GRID_JUNCTION_NOTE.txt) | Live GRID repo | Yes |
| **E:\Build\GRID-main.old** | Yes | Full snapshot | Yes (fallback) |
| **E:\Build\GRID.zip** | Yes | Zip archive | Yes (fallback) |

---

## 2. File History (F: drive)

- **F:\FileHistory** — Exists; top-level folders: Configuration, Data, GRID.
- **F:\FileHistory\GRID\DELOREAN** — Exists; contains Configuration and Data (File History versioning structure). Treat as GRID backup root for restore.
- File History UI: Check Settings > Update & Security > Backup to confirm included folders (e.g. E:\ or user libraries).

---

## 3. OneDrive (Microsoft account synced)

- **OneDrive root:** C:\Users\irfan\OneDrive (folders: Apps, Attachments, Desktop, Documents, Music, Pictures, Videos).
- **Folder search:** No folders named `grid`, `GRID`, `grid-rag-enhanced`, `pytest_cache`, or `DELOREAN` found in quick scan.
- **File content search:** Run [e:\scripts\search_onedrive_grid_paths.ps1](e:\scripts\search_onedrive_grid_paths.ps1) manually; automated run timed out over full OneDrive tree. Re-run for deeper content search if needed.

---

## 4. User profile (Documents, Desktop, Downloads, AppData)

| Location | Found | Notes |
|----------|--------|--------|
| **Downloads** | Yes | **GRID-main.zip**, **GRID-main (1).zip** — GRID repo zips (new finds for restore) |
| **Documents** | No GRID folders/files | — |
| **Desktop** | No GRID shortcuts/folders | — |
| **AppData (Cursor/Code/Windsurf)** | No GRID-named files in quick scan | Workspace/recent list may still reference E:\grid; not enumerated here. |

---

## 5. E:\ drive scan

| Path | Found | Notes |
|------|--------|--------|
| **E:\** (root) | grid (junction), grid.worktrees | As expected. |
| **E:\Build** | Yes | **GRID**, **GRID-main**, **GRID-main.old**, **GRID-INTELLIGENCE-GRID-c9d13087f0ccd76595e0db5891cad817f0545f06**, **grid.worktrees**, **GRID.zip** — multiple GRID sources (some new vs restore plan) |
| **E:\Storage\E-Drive-Backup-20260206-174528** | Yes | **scripts\disable_grid_servers.ps1** — reference/script only. |
| **E:\Storage\Selected-Dirs-Backup-20260206-175159** | Yes | **analysis_outputs\grid** (folder); eufle file_metrics with "grid" in filename (e.g. onboarding_gridstral, grid_bridge); venv libs (scipy/sympy/torch *grid* — not GRID project). |
| **E:\.worktrees** | Yes | **copilot-worktree-2026-02-01T20-18-14**, **copilot-worktree-2026-02-07T01-40-39** — each has .env.editor.template with PROJECT_GRID ref. |

---

## 6. Config and workspace files (references)

| File | GRID reference |
|------|-----------------|
| **E:\.env.editor.template** | PROJECT_GRID=E:\\grid (line 62) |
| **E:\.env.editor** | Same (template copy) |
| **E:\OrganizedWorkspace.code-workspace** | "path":"E:/grid" for GRID (AI/ML Platform) folder |
| **E:\config\unified-server-configuration.json** | description: E:\\grid; working_directory: E:\\grid, E:\\grid\\mcp-setup\\server (grid-rag-server, grid-enhanced-tools-server, grid-agentic-server) |
| **E:\.worktrees\*\\.env.editor.template** | PROJECT_GRID=E:\\grid in listed worktrees |

---

## 7. Environment variables and shortcuts

- **PROJECT_GRID:** Not set in User or Machine environment.
- **Other env:** COMPUTERNAME=GRID, LOGONSERVER=\\GRID, USERDOMAIN=GRID (machine/domain names, not project path).
- **Shortcuts:** No .lnk found on Desktop or in Documents (first 20) with target path containing "grid".

---

## 8. WSL

- Not run. If E: is mounted (e.g. /mnt/e), E:\grid is visible as /mnt/e/grid.

---

## 9. Recovery drive

- Recovery drive (USB) holds system recovery tools and optionally system files; it does **not** typically contain E:\ or user projects. GRID repo is not on the recovery drive unless a full system image (Backup and Restore or third-party) that includes E:\ was created — document that image location if used.

---

## 10. Remote / cloud

- **GitHub:** GRID-INTELLIGENCE/GRID — canonical repo (clone/compare).
- **Other clouds:** Not scanned; add Dropbox/Google Drive if used.

---

## Summary

- **Full repo / backup:** F:\FileHistory\GRID\DELOREAN, F:\.pytest_cache.zip, E:\_projects\grid-rag-enhanced (via E:\grid), E:\Build\GRID-main.old, E:\Build\GRID.zip, E:\Build\GRID, E:\Build\GRID-main, E:\Build\GRID-INTELLIGENCE-GRID-..., and user Downloads (GRID-main.zip, GRID-main (1).zip).
- **References only:** E:\.env.editor.template, E:\OrganizedWorkspace.code-workspace, E:\config\unified-server-configuration.json, E:\.worktrees\*\.env.editor.template, E:\Storage\...\disable_grid_servers.ps1, E:\Storage\...\analysis_outputs\grid and eufle file_metrics.
- **OneDrive:** No GRID folder names in quick scan; content search script available for manual run.
- **Recovery drive:** Created per Microsoft steps; does not contain GRID unless a full image including E:\ exists elsewhere.
