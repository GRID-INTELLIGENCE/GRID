# Disabling JavaScript, TypeScript and Node.js features in this workspace

This repository is Python-first. To prevent VS Code from activating JavaScript, TypeScript
and Node.js language features in this workspace, we've configured workspace settings
in `.vscode/settings.json`.

What the settings do:
- Turn off JS/TS suggestion, validation and formatting.
- Disable npm script explorer and npm autoscanning.
- Treat common JS/TS file extensions as `plaintext` so language service features are not activated.
- Ignore extension recommendations so the editor won't prompt to install JS/TS tooling.

Why not a blocklist? Treating files as `plaintext` and disabling features avoids any file-level
blocklists or exclusion rules — it simply avoids enabling language services.

How to revert locally:
1. In VS Code, open Settings (Workspace) and remove or flip the flags in `.vscode/settings.json`.
2. Or delete `.vscode/settings.json` to restore normal JS/TS/Node behaviour in the workspace.

If you'd like a different approach (e.g. disabling only specific features instead of treating files as plaintext),
tell me which features to keep and I'll adjust the workspace settings accordingly.
