# E:\ Drive Layout - GRID Ecosystem

## Overview
This is the primary development drive containing the GRID (Generalized Reasoning Intelligence Domain) ecosystem and related projects.

## Directory Structure

```
E:\
├── grid/                    # Primary GRID repository (caraxesthebloodwyrm02/GRID)
│   ├── src/                 # Core GRID source code
│   ├── tests/               # Test suites (1400+ tests)
│   ├── docs/                # Documentation
│   ├── Arena/               # AI Arena components
│   ├── EUFLE/               # EUFLE (Edge Unified Fabric Layer)
│   └── ...
│
├── Coinbase/                # Coinbase trading/analysis tools
├── wellness_studio/         # Wellness/health data analysis
├── SSL/                     # SSL certificates and security tools
├── mothership/              # Core application components
├──
├── analysis_outputs/        # Analysis reports and outputs
├── tests/                   # Additional test suites
├── docs/                    # Cross-project documentation
│
├── _projects/               # Sub-projects and worktrees
├── data/                    # Shared data storage
├── shared/                  # Shared utilities and resources
├── tmp/                     # Temporary working directory
│
├── .env.editor              # Editor environment configuration
└── README.md                # This file
```

## Git Remotes (GRID Repo)

- **origin**: `https://github.com/caraxesthebloodwyrm02/GRID.git` (primary)
- **origin_irfan**: `https://github.com/irfankabir02/GRID.git` (mirror)

## Environment Variables

Key paths configured in `.env.editor`:
- `PROJECT_GRID=E:\grid`
- `PROJECT_COINBASE=E:\Coinbase`
- `PROJECT_WELLNESS=E:\wellness_studio`
- `WORKSPACE_ROOT=E:\`

## Quick Start

```powershell
# Navigate to GRID
cd E:\grid

# Check git status
& 'C:\Program Files\Git\bin\git.exe' status

# Run tests
python -m pytest tests/ -x
```
