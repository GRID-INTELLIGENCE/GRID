# GRID-main Workspace Overload Runbook

## Live Baseline

Last checked from the local workspace on 2026-04-06:

- RAM: 31 GB total, 8 GB free, about 72% used
- Swap: 0 GB
- Disk: about 83% free on `/`
- Overall diagnostic: healthy

This means the active risk is memory pressure, not disk pressure.

## Primary Overload Signals

Treat these as the main warning signs:

- RAM climbs past about 80%
- Python tests, frontend tests, Electron, and Ollama are active at the same time
- Editor and language-server processes begin to dominate memory

Do not start another heavy job once RAM is already near 80%.

## Highest-Value RAM Relief

Close or stop work in this order:

1. Unused `code` or `windsurf-next` windows
2. Duplicate `language_server` processes tied to idle workspaces
3. Extra `claude` sessions not involved in the current task
4. `ollama` when local-model inference is not needed
5. Extra Electron windows when desktop-shell testing is not active

Keep only one active editor surface and one active language-server set for the current workspace.

## What Not To Prioritize

These are not current overload drivers:

- `/tmp` cleanup
- general disk cleanup
- deleting `frontend/node_modules`
- deleting `.venv`

Those are storage-heavy, not the primary live performance bottleneck.

## GRID-main Execution Order

Use this sequence to minimize contention:

1. Run targeted backend work first:
   - `uv run pytest tests/<domain> -q --tb=short`
2. Run frontend renderer checks next:
   - `make frontend-typecheck`
   - `make test-frontend`
3. Run Electron build only when needed:
   - `make electron-build`
4. Keep landing work isolated:
   - `make landing-validate`

Do not run backend tests, frontend tests, Electron builds, and Ollama-backed work in parallel.

## Scope Windows

Debug and refactor inside one window at a time:

- Python service: `src/<domain>` plus matching `tests/<domain>`
- Frontend renderer: `frontend/src`
- Electron shell: `frontend/electron`
- Landing/branding: `landing/`

Only widen beyond one window if a shared contract forces it.

## Fast Triage Checklist

When the machine feels overloaded:

1. Check whether RAM is already near or above 80%.
2. Close one unused editor surface.
3. Close one idle language-server-heavy workspace.
4. Stop `ollama` if it is not part of the current task.
5. Resume work with one `GRID-main` window only.

## Current Storage Hot Spots

These are useful for context, not emergency cleanup:

- `GRID-main/.venv`: about 1.8 GB
- `GRID-main/frontend`: about 893 MB
- `GRID-main/research`: about 249 MB
- `GRID-main/frontend/node_modules`: about 891 MB

They explain footprint, but not the main live slowdown.
