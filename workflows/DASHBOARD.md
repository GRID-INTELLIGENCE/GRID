# Workflows Dashboard

## Today

Open `workflows/TODAY.md`.

## Update

Run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File e:\grid\workflows\update.ps1
```

This will create/update:

- `workflows/daily/YYYY-MM-DD.md`
- `workflows/TODAY.md`

## Config

Edit:

- `workflows/config.json`

## Principles

- Live tasks live in `workflows/TODAY.md`.
- Long-running project tasks belong in the repo’s `TODO.md` and/or your project trackers.
- Every AI-assisted action should be traceable to:
  - what command ran
  - what file changed
  - what evidence/logs were collected
