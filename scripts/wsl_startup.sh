#!/bin/bash
# WSL startup script for GRID workspace
# Source from ~/.bashrc: [ -f /mnt/e/Seeds/GRID-main/scripts/wsl_startup.sh ] && . /mnt/e/Seeds/GRID-main/scripts/wsl_startup.sh
# No sudo; user-space only.

# Only run if /mnt/e exists (avoid noise when not in WSL or mount missing)
if [ ! -d /mnt/e ]; then
    return 0 2>/dev/null || true
    exit 0
fi

# Optional: set GRID env when GRID-main is present
GRID_ROOT="/mnt/e/Seeds/GRID-main"
if [ -d "$GRID_ROOT" ]; then
    export GRID_HOME="${GRID_HOME:-$GRID_ROOT}"
    [ -d "$GRID_ROOT/.venv/bin" ] && export PATH="$GRID_ROOT/.venv/bin:$PATH"
fi

# Optional: hint if E: exists but a common path is missing (e.g. for EUFLE)
if [ -d /mnt/e ] && [ ! -d /mnt/e/Seeds/GRID-main ] && [ ! -d /mnt/e/EUFLE ]; then
    :  # Silent; user may use other layouts
fi

return 0 2>/dev/null || true
