# Settings diff & workspace mapping 📋

## Purpose
Explain how to compare user-level settings to workspace-level settings in `E:\grid\.code-workspace` and export a brief overrides report.

## Paths
- User settings: `%APPDATA%\Code\User\settings.json`
- Workspace settings: `E:\grid\.code-workspace` (the `"settings"` object)

## Files added
- `E:\grid\scripts\diff-settings.ps1` — pulls both files, performs a shallow diff of keys and exports `overrides.json` & `overrides.csv`.

## Quick run
Open PowerShell and run:

```powershell
cd E:\grid\scripts
.\diff-settings.ps1 -ReportDir "$env:USERPROFILE\Documents\vscode-audit-exports"
```

Results will include keys that workspace overrides and the effective values.

## Notes
- Keep workspace settings authoritative for project-specific overrides.
- Script is conservative (shallow key diff); for deeper inspection, open both files and inspect nested objects manually or extend the script.
