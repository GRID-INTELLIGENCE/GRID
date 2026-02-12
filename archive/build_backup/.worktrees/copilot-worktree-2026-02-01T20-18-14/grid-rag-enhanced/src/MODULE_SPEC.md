# GRID Module Spec: src (Windows)

> **Purpose:** Core source code module containing application logic, services, and tools.

## 1) Module Metadata
- **Module name:** `src`
- **Root path (absolute):** `E:\grid\src`
- **Owner:** `grid-core-team`
- **Primary runtime:** `python`
- **OS targets:** `Windows` (primary), `WSL` (optional)

## 2) Path Normalization Rules (Windows)
Based on Microsoft documentation:
- Windows normalizes paths by **canonicalizing separators**, **applying current directory** to relative paths, **evaluating `.` and `..`**, and **trimming trailing spaces/periods**.
  Source: https://learn.microsoft.com/en-us/dotnet/standard/io/file-path-formats
- **Relative paths are risky in multithreaded apps** (current directory is process‑wide). Resolve against a known base.
- Long paths require **opt‑in**: set `LongPathsEnabled=1` and ensure apps are long‑path‑aware.

### Required conventions
- **Always store/emit absolute paths** in configs and scripts.
- **Windows separator:** use `\` for paths intended for Windows tooling.
- **Avoid trailing spaces/periods** in names.
- **Avoid drive‑relative paths** like `D:folder` (ambiguous).
- **Do not rely on CWD** in any threaded process; resolve against explicit base.

## 3) Module Structure
```
E:\grid\src\
├── application/   (125 items) - Application layer logic
├── cognitive/     (2 items)   - AI/cognitive processing
├── grid/          (180 items) - Core GRID framework
├── tools/         (156 items) - CLI and utility tools
├── api/           - API endpoints
├── bridge/        - Integration bridges
├── cli/           - Command-line interface
├── core/          - Core abstractions
├── data/          - Data models
├── database/      - Database layer
├── kernel/        - Kernel operations
├── services/      - Service layer
└── utils/         - Shared utilities
```

## 4) Module‑specific routing rules
- **Base path:** `E:\grid\src`
- **Config path:** `E:\grid\config`
- **Data path:** `E:\grid\data`
- **Logs path:** `E:\grid\logs`

## 5) Audit Checklist
- [x] All paths resolved against explicit base
- [x] No `D:folder` drive‑relative usage
- [x] No trailing spaces/periods in file/dir names
- [x] No path lengths > 260 unless long‑paths enabled
- [x] No relative paths in multithreaded sections

---
**Last audit:** 2026-01-17
