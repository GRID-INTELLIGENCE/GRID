# Trace Recent Files (Trace to Recover)

**Purpose:** Produce a report of the **most recently modified files** (by filesystem mtime) across all (or selected) drives so you can see what was last touched and use it for **recovery** — e.g. correlate with File History, backup timestamps, or prioritize what to restore.

## How to run

From PowerShell (run from `E:\` or use full path):

```powershell
E:\scripts\track_recent_files.ps1
```

Optional parameters:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `-ReportDir` | `E:\docs` | Directory where report files are written |
| `-TopN` | `500` | Number of most-recent files to include |
| `-Drives` | (all from config or all FileSystem) | Comma-separated drive letters, e.g. `E,F` |
| `-ConfigPath` | `E:\config\recent_files_trace.json` | Path to JSON config (drive roots, exclusions, maxFiles) |
| `-NoMarkdown` | — | Do not write the `.md` summary file |

Examples:

```powershell
# Scan only E: and F: (faster)
.\scripts\track_recent_files.ps1 -Drives "E,F"

# Top 1000 files, reports to E:\config\reports
.\scripts\track_recent_files.ps1 -ReportDir E:\config\reports -TopN 1000
```

## Where reports go

- **Default:** `E:\docs\`
- Each run creates **timestamped** files (no overwrite):
  - `recent_files_trace_YYYYMMDD-HHMMSS.json` — machine-readable list
  - `recent_files_trace_YYYYMMDD-HHMMSS.md` — table for quick human scan

## Output format

**JSON** contains:

- `generatedUtc` — when the report was generated
- `drivesScanned` — drive letters scanned
- `rootsScanned` — full roots (e.g. `C:\Users\irfan`, `E:\`, `F:\`)
- `totalFilesCollected` — count before taking top N
- `topN` — limit applied
- `topFiles` — array of `{ "path", "lastWriteTimeUtc", "lastWriteTimeLocal", "length" }`

**Markdown** is a table: Path | Last modified (local) | Size.

## Using the list for recovery

1. **Correlate with backup time:** Compare `lastWriteTimeUtc` with your backup or File History snapshot time to see which files were changed before/after.
2. **Prioritize restore:** Restore or re-check the top entries first (most recently modified).
3. **Trace after an incident:** Run the script after an event; keep the report as evidence of what was last touched on each drive.
4. **Run periodically:** Run on a schedule (e.g. daily or before major changes) so you have a history of timestamped reports in `ReportDir`.

## Configuration

Optional config file: **E:\config\recent_files_trace.json**

- **driveRoots** — which roots to scan per drive (e.g. limit C: to `C:\Users\irfan`, full E:\ and F:\).
- **excludeDirNames** — directory names that are skipped (e.g. `.git`, `node_modules`, `.venv`).
- **excludePathContains** — path substrings that skip a directory (e.g. `WinSxS`, `Program Files`).
- **maxFiles** — default top N when not overridden by `-TopN`.

If the config file is missing, the script uses built-in defaults (all FileSystem drives with C: limited to your user profile, common exclusions, top 500).

## See also

- [GRID_DISCOVERY_CHECKLIST.md](GRID_DISCOVERY_CHECKLIST.md) — where GRID and backups were found (File History, E:\, F:\, Storage)
- [BACKUP_VERIFICATION_REPORT.md](BACKUP_VERIFICATION_REPORT.md) — backup verification (if present in your docs)
