# Keybindings audit and scripts 🔧

## Purpose
Short guide for validating user and workspace keybindings and detecting conflicts with installed extensions.

## Paths
- User keybindings: `%APPDATA%\Code\User\keybindings.json`
- Workspace manifest (overrides): `E:\grid\.code-workspace` ("settings" section)
- Extensions folder: `%USERPROFILE%\\.vscode\\extensions`
- Export/report directory (suggested): `%USERPROFILE%\\Documents\\vscode-audit-exports`

## Files added
- `E:\grid\scripts\check-keybindings.ps1` — scans `keybindings.json` for duplicates and conflicts with `contributes.keybindings` from installed extensions, writes JSON/CSV report.

## Quick run
Open PowerShell (as appropriate) and run:

```powershell
cd E:\grid\scripts
.\check-keybindings.ps1 -ReportDir "$env:USERPROFILE\Documents\vscode-audit-exports"
```

Reports will appear in the specified `ReportDir`.

## Notes
- The script only detects duplicate key combos and extension-declared bindings that match user keys; it cannot fully resolve runtime "when" clause semantics — for that, use VS Code Keybinding Resolver UI (`Developer: Toggle Keyboard Shortcuts Troubleshooting`).
- Keep exports for audits and share the JSON if you want me to interpret results.
